"""
Bias calculation service.
Calculates chi-square tests, foul metrics, and stores results in cache.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
import numpy as np
from scipy.stats import chisquare

from app.models import (
    BiasMetrics, Match, Foul, Team, AttackEvent, DefenseEvent
)
from app.services.event_classifier import (
    count_attacks, count_defenses
)


logger = logging.getLogger(__name__)


def calculate_competition_bias(
    competition_id: int,
    attack_definition: str = "all_combined",
    defense_definition: str = "all_combined",
    recalculate: bool = False,
    db: Session = None,
) -> list:
    """
    Calculate bias metrics for all teams in a competition.
    
    Args:
        competition_id: Competition ID
        attack_definition: Type of attacks to count
        defense_definition: Type of defenses to count
        recalculate: Force recalculation even if cached
        db: Database session
    
    Returns:
        List of BiasMetrics objects
    """
    if not db:
        raise ValueError("Database session required")
    
    logger.info(
        f"Calculating bias for competition {competition_id} "
        f"(attack={attack_definition}, defense={defense_definition})"
    )
    
    try:
        # Get all teams in competition
        matches = db.query(Match).filter(
            Match.competition_id == competition_id
        ).all()
        
        if not matches:
            logger.warning(f"No matches found for competition {competition_id}")
            return []
        
        # Get unique teams
        team_ids = set()
        for match in matches:
            team_ids.add(match.home_team_id)
            team_ids.add(match.away_team_id)
        
        # Calculate metrics for each team
        bias_metrics_list = []
        all_fouls_committed = []
        
        for team_id in team_ids:
            metrics = calculate_team_bias(
                competition_id=competition_id,
                team_id=team_id,
                attack_definition=attack_definition,
                defense_definition=defense_definition,
                recalculate=recalculate,
                db=db,
            )
            
            if metrics:
                bias_metrics_list.append(metrics)
                all_fouls_committed.append(metrics.fouls_committed_count)
        
        # Calculate chi-square test for the entire competition.
        # NOTE: This is a single COMPETITION-WIDE test (are fouls evenly
        # distributed across all teams?), not a per-team test - the same
        # result is stored on every team's row to represent "how significant
        # is the overall bias pattern in this competition."
        if len(all_fouls_committed) > 1:
            chi_square_stat, p_value = perform_chi_square_test(all_fouls_committed)
            
            if chi_square_stat is not None and p_value is not None:
                logger.info(
                    f"Competition-level chi-square: {chi_square_stat:.4f}, "
                    f"p-value: {p_value:.4f}"
                )
                is_significant = p_value < 0.05
                
                for metrics in bias_metrics_list:
                    metrics.chi_square_stat = chi_square_stat
                    metrics.p_value = p_value
                    metrics.is_significant = is_significant
                
                db.commit()
                logger.info(f"Persisted chi-square results to {len(bias_metrics_list)} team records")
        
        return bias_metrics_list
    
    except Exception as e:
        logger.error(f"Error calculating competition bias: {e}", exc_info=True)
        raise


def calculate_team_bias(
    competition_id: int,
    team_id: int,
    attack_definition: str = "all_combined",
    defense_definition: str = "all_combined",
    recalculate: bool = False,
    db: Session = None,
) -> BiasMetrics:
    """
    Calculate bias metrics for a specific team in a competition.
    
    Args:
        competition_id: Competition ID
        team_id: Team ID
        attack_definition: Type of attacks to count
        defense_definition: Type of defenses to count
        recalculate: Force recalculation
        db: Database session
    
    Returns:
        BiasMetrics object with calculated metrics
    """
    if not db:
        raise ValueError("Database session required")
    
    logger.debug(f"Calculating bias for team {team_id} in competition {competition_id}")
    
    try:
        # Look up any existing row for this (competition, team) pair up front -
        # we need this reference either way: to return early (cache hit) or to
        # update in place later (recalculation), since constructing a brand-new
        # BiasMetrics() and merging it would try to INSERT a duplicate and
        # silently fail against the unique constraint on (competition_id, team_id).
        existing = db.query(BiasMetrics).filter(
            and_(
                BiasMetrics.competition_id == competition_id,
                BiasMetrics.team_id == team_id,
            )
        ).first()
        
        if existing and not recalculate:
            logger.debug(f"Using cached metrics for team {team_id}")
            return existing
        
        # Get all matches where this team played
        matches = db.query(Match).filter(
            and_(
                Match.competition_id == competition_id,
                ((Match.home_team_id == team_id) | (Match.away_team_id == team_id))
            )
        ).all()
        
        # Count fouls committed and conceded
        fouls_committed = db.query(Foul).filter(
            and_(
                Foul.match_id.in_([m.id for m in matches]),
                Foul.team_fouls_id == team_id,
            )
        ).count()
        
        fouls_conceded = db.query(Foul).filter(
            and_(
                Foul.match_id.in_([m.id for m in matches]),
                Foul.team_fouls_against_id == team_id,
            )
        ).count()
        
        # Count attacks and defenses
        total_attacks = count_attacks(
            team_id=team_id,
            match_ids=[m.id for m in matches],
            definition=attack_definition,
            db=db,
        )
        
        total_defenses = count_defenses(
            team_id=team_id,
            match_ids=[m.id for m in matches],
            definition=defense_definition,
            db=db,
        )
        
        # Calculate ratios
        fouls_per_attack = (
            fouls_committed / total_attacks
            if total_attacks > 0 else 0
        )
        
        fouls_per_defense = (
            fouls_committed / total_defenses
            if total_defenses > 0 else 0
        )
        
        # Update the existing row in place if one exists, otherwise create new.
        # This avoids the merge()-tries-to-INSERT-a-duplicate bug: mutating an
        # already-persistent, session-tracked object and committing is a plain
        # UPDATE, which works reliably regardless of how the row was first created.
        if existing:
            existing.fouls_committed_count = fouls_committed
            existing.fouls_conceded_count = fouls_conceded
            existing.total_attacks = total_attacks
            existing.total_defenses = total_defenses
            existing.fouls_per_attack = fouls_per_attack
            existing.fouls_per_defense = fouls_per_defense
            bias_metric = existing
        else:
            bias_metric = BiasMetrics(
                competition_id=competition_id,
                team_id=team_id,
                fouls_committed_count=fouls_committed,
                fouls_conceded_count=fouls_conceded,
                total_attacks=total_attacks,
                total_defenses=total_defenses,
                fouls_per_attack=fouls_per_attack,
                fouls_per_defense=fouls_per_defense,
                chi_square_stat=None,
                p_value=None,
                is_significant=False,
            )
            db.add(bias_metric)
        
        try:
            db.commit()
            logger.debug(
                f"Saved metrics for team {team_id}: "
                f"{fouls_committed} fouls committed, {fouls_conceded} conceded, "
                f"{total_attacks} attacks, {total_defenses} defenses"
            )
        except Exception as e:
            logger.warning(f"Failed to save metrics: {e}")
            db.rollback()
        
        return bias_metric
    
    except Exception as e:
        logger.error(f"Error calculating team bias: {e}", exc_info=True)
        raise


def perform_chi_square_test(foul_counts: list) -> tuple:
    """
    Perform chi-square goodness-of-fit test.
    
    Tests if foul distribution across teams differs significantly from uniform.
    H0: Fouls are uniformly distributed
    H1: Fouls are not uniformly distributed (bias exists)
    
    Args:
        foul_counts: List of foul counts per team
    
    Returns:
        Tuple of (chi_square_statistic, p_value)
    
    Interpretation:
        p < 0.05: Reject H0 → Evidence of bias
        p >= 0.05: Fail to reject H0 → No significant bias
    """
    try:
        foul_array = np.array(foul_counts)
        
        # Expected value: uniform distribution
        expected = np.full_like(foul_array, foul_array.mean(), dtype=float)
        
        # Perform chi-square test
        chi_stat, p_val = chisquare(foul_array, expected)
        
        logger.info(
            f"Chi-square test: χ² = {chi_stat:.4f}, p = {p_val:.4f}"
        )
        
        return chi_stat, p_val
    
    except Exception as e:
        logger.error(f"Chi-square test failed: {e}")
        return None, None


def get_significance_interpretation(p_value: float) -> str:
    """
    Get human-readable interpretation of p-value.
    
    Args:
        p_value: Statistical p-value
    
    Returns:
        String interpretation
    """
    if p_value is None:
        return "Insufficient data"
    
    if p_value < 0.001:
        return "Highly significant bias (p < 0.001)"
    elif p_value < 0.01:
        return "Very significant bias (p < 0.01)"
    elif p_value < 0.05:
        return "Significant bias (p < 0.05)"
    elif p_value < 0.10:
        return "Marginally significant bias (p < 0.10)"
    else:
        return "No significant bias (p >= 0.05)"