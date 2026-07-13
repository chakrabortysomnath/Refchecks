"""
Favourability analysis service.

Measures refereeing bias *in a team's favour* using a severity-weighted,
expected-vs-actual residual model. This is the rebuilt core of the dashboard;
the older per-team ratio table + competition-wide chi-square (see
bias_calculator.py) is left intact but is superseded for insight purposes.

Concept
-------
A team refereed favourably is:
  (a) LET OFF when defending   - fewer fouls called against it than its
      defensive workload warrants, and
  (b) PROTECTED when attacking - more fouls awarded to it than its attacking
      workload warrants.

Each foul is weighted by how consequential the referee's *decision* was: a
penalty is a far bigger call than a midfield free kick. For every team we
compare its weighted fouls (committed / awarded) against what a NEUTRAL referee
would be expected to give for that team's own attack/defense volume, then
express the gap as a standardized (Poisson) residual so genuine outliers stand
out. The two residuals combine into a single signed Favourability Index F:
positive = net favoured, negative = net disadvantaged.

Volume denominators reuse count_attacks / count_defenses from event_classifier,
exactly as bias_calculator does, so the attack/defense definition selectors keep
driving the analysis.
"""

import logging
import math

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Match, Foul, Team
from app.services.event_classifier import count_attacks, count_defenses


logger = logging.getLogger(__name__)


# Default decision-severity weights (all configurable per request). A foul that
# is both a penalty and a card counts ONCE, at the highest applicable weight
# (max, not sum) - the precedence below encodes that.
DEFAULT_WEIGHTS = {
    "penalty": 5.0,    # spot-kick awarded - the biggest single decision
    "red": 4.0,        # red card / second yellow
    "yellow": 2.0,     # yellow card
    "foul": 1.0,       # ordinary whistled free kick, no card
    "advantage": 0.5,  # advantage played - infringement seen, play not stopped
}

TIERS = ("penalty", "red", "yellow", "foul", "advantage")

# |z| at or beyond this flags a team as a genuine outlier on that side.
OUTLIER_Z = 2.0


def _card_tier(card_type):
    """Map a Statsbomb card name ('Yellow Card', 'Red Card', 'Second Yellow')
    to 'red' / 'yellow' / None."""
    if not card_type:
        return None
    c = card_type.lower()
    if "red" in c or "second yellow" in c:
        return "red"
    if "yellow" in c:
        return "yellow"
    return None


def classify_foul(foul, weights):
    """
    Return (tier, weight) for a single foul.

    Precedence (highest-consequence decision wins):
        penalty > red/second-yellow > yellow > ordinary foul > advantage-only

    penalty/advantage come from the retained raw Statsbomb JSON
    (foul_committed.penalty / .advantage); the card comes from the stored
    card_type column.
    """
    raw = foul.raw_data or {}
    fc = raw.get("foul_committed") or {}
    is_penalty = bool(fc.get("penalty"))
    is_advantage = bool(fc.get("advantage"))
    card = _card_tier(foul.card_type)

    if is_penalty:
        tier = "penalty"
    elif card == "red":
        tier = "red"
    elif card == "yellow":
        tier = "yellow"
    elif is_advantage:
        tier = "advantage"
    else:
        tier = "foul"
    return tier, weights[tier]


def _empty_breakdown():
    return {t: 0 for t in TIERS}


def _resolve_weights(weights):
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        for k, v in weights.items():
            if k in w and v is not None:
                w[k] = float(v)
    return w


def calculate_favourability(
    competition_id: int,
    attack_definition: str = "all_combined",
    defense_definition: str = "all_combined",
    weights: dict = None,
    db: Session = None,
) -> dict:
    """
    Compute the severity-weighted favourability model for every team in a
    competition. Returns a plain dict ready to serialize (see the route).
    """
    if not db:
        raise ValueError("Database session required")

    w = _resolve_weights(weights)

    matches = db.query(Match).filter(
        Match.competition_id == competition_id
    ).all()

    empty_rates = {"weighted_fouls_per_defense": 0.0, "weighted_fouls_per_attack": 0.0}
    if not matches:
        return {
            "competition_id": competition_id,
            "attack_definition": attack_definition,
            "defense_definition": defense_definition,
            "weights": w,
            "rates": empty_rates,
            "teams": [],
        }

    team_ids = set()
    for m in matches:
        team_ids.add(m.home_team_id)
        team_ids.add(m.away_team_id)

    # --- Pass 1: per-team volumes, weighted foul sums, severity breakdowns ---
    teams = {}
    for team_id in team_ids:
        match_ids = [
            m.id for m in matches
            if m.home_team_id == team_id or m.away_team_id == team_id
        ]

        defenses = count_defenses(team_id, match_ids, defense_definition, db)
        attacks = count_attacks(team_id, match_ids, attack_definition, db)

        committed = db.query(Foul).filter(
            and_(Foul.match_id.in_(match_ids), Foul.team_fouls_id == team_id)
        ).all()
        awarded = db.query(Foul).filter(
            and_(
                Foul.match_id.in_(match_ids),
                Foul.team_fouls_against_id == team_id,
            )
        ).all()

        wfc = 0.0
        cb = _empty_breakdown()
        for f in committed:
            tier, weight = classify_foul(f, w)
            wfc += weight
            cb[tier] += 1

        wfa = 0.0
        ab = _empty_breakdown()
        for f in awarded:
            tier, weight = classify_foul(f, w)
            wfa += weight
            ab[tier] += 1

        team = db.query(Team).filter(Team.id == team_id).first()
        teams[team_id] = {
            "team_id": team_id,
            "team_name": team.name if team else f"Team {team_id}",
            "defenses": defenses,
            "attacks": attacks,
            "weighted_fouls_committed": round(wfc, 2),
            "weighted_fouls_awarded": round(wfa, 2),
            "committed_breakdown": cb,
            "awarded_breakdown": ab,
        }

    # --- Competition-wide neutral-referee rates ---
    total_wfc = sum(t["weighted_fouls_committed"] for t in teams.values())
    total_wfa = sum(t["weighted_fouls_awarded"] for t in teams.values())
    total_def = sum(t["defenses"] for t in teams.values())
    total_att = sum(t["attacks"] for t in teams.values())
    r_def = total_wfc / total_def if total_def > 0 else 0.0
    r_att = total_wfa / total_att if total_att > 0 else 0.0

    # --- Pass 2: expected, standardized residuals, favourability index ---
    result_teams = []
    for t in teams.values():
        e_committed = r_def * t["defenses"]
        e_awarded = r_att * t["attacks"]

        # Standardized (Poisson) residuals, signed so + = favoured.
        # Leniency: fewer weighted fouls called AGAINST them than expected.
        z_leniency = (
            (e_committed - t["weighted_fouls_committed"]) / math.sqrt(e_committed)
            if e_committed > 0 else 0.0
        )
        # Protection: more weighted fouls awarded TO them than expected.
        z_protection = (
            (t["weighted_fouls_awarded"] - e_awarded) / math.sqrt(e_awarded)
            if e_awarded > 0 else 0.0
        )
        favourability = z_leniency + z_protection

        t.update({
            "expected_committed": round(e_committed, 2),
            "expected_awarded": round(e_awarded, 2),
            "z_leniency": round(z_leniency, 3),
            "z_protection": round(z_protection, 3),
            "favourability": round(favourability, 3),
            "leniency_outlier": abs(z_leniency) >= OUTLIER_Z,
            "protection_outlier": abs(z_protection) >= OUTLIER_Z,
        })
        result_teams.append(t)

    # Most favoured first.
    result_teams.sort(key=lambda x: x["favourability"], reverse=True)

    logger.info(
        f"Favourability for competition {competition_id}: "
        f"{len(result_teams)} teams, r_def={r_def:.5f}, r_att={r_att:.5f}"
    )

    return {
        "competition_id": competition_id,
        "attack_definition": attack_definition,
        "defense_definition": defense_definition,
        "weights": w,
        "rates": {
            "weighted_fouls_per_defense": round(r_def, 5),
            "weighted_fouls_per_attack": round(r_att, 5),
        },
        "teams": result_teams,
    }
