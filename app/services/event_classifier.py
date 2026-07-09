"""
Event classification service.
Classifies Statsbomb events as attacks, defenses, or fouls based on user-selected definitions.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models import Event


logger = logging.getLogger(__name__)


# ===== ATTACK DEFINITIONS =====

ATTACK_DEFINITIONS = {
    "all_combined": {
        "description": "Shots + Shot Assists + Passes in final 3rd + Dribbles + Carries",
        "event_types": ["Shot", "Pass", "Dribble", "Carry"],
        "filters": {
            "Pass": {"min_x": 80},  # Final third (x > 80 out of 120)
            "Dribble": {"min_x": 60},  # Attacking zones
            "Carry": {"min_x": 60},
        }
    },
    "shots_only": {
        "description": "Shots and Shot Assists",
        "event_types": ["Shot"],
        "filters": {}
    },
    "passes_only": {
        "description": "Passes in final third",
        "event_types": ["Pass"],
        "filters": {
            "Pass": {"min_x": 80},
        }
    },
    "dribbles_only": {
        "description": "Dribbles and Carries",
        "event_types": ["Dribble", "Carry"],
        "filters": {
            "Dribble": {"min_x": 60},
            "Carry": {"min_x": 60},
        }
    }
}


# ===== DEFENSE DEFINITIONS =====

DEFENSE_DEFINITIONS = {
    "all_combined": {
        "description": "Tackles + Interceptions + Blocks + Clearances + Duels (won)",
        "event_types": ["Tackle", "Interception", "Block", "Clearance", "Duel"],
        "filters": {
            "Duel": {"outcome": "Won"},
        }
    },
    "tackles_only": {
        "description": "Tackles",
        "event_types": ["Tackle"],
        "filters": {}
    },
    "blocks_only": {
        "description": "Blocks and Clearances",
        "event_types": ["Block", "Clearance"],
        "filters": {}
    },
    "duels_only": {
        "description": "Duels (won)",
        "event_types": ["Duel"],
        "filters": {
            "Duel": {"outcome": "Won"},
        }
    }
}


# ===== COUNT ATTACK EVENTS =====

def count_attacks(
    team_id: int,
    match_ids: list,
    definition: str = "all_combined",
    db: Session = None,
) -> int:
    """
    Count attack events for a team across multiple matches.
    
    Args:
        team_id: Team ID
        match_ids: List of match IDs to search
        definition: Attack definition to use
        db: Database session
    
    Returns:
        Count of attack events
    """
    if not db or not match_ids:
        return 0
    
    if definition not in ATTACK_DEFINITIONS:
        logger.warning(f"Unknown attack definition: {definition}, using all_combined")
        definition = "all_combined"
    
    attack_def = ATTACK_DEFINITIONS[definition]
    event_types = attack_def["event_types"]
    filters = attack_def["filters"]
    
    try:
        query = db.query(Event).filter(
            and_(
                Event.match_id.in_(match_ids),
                Event.team_id == team_id,
                Event.event_type.in_(event_types),
            )
        )
        
        # Apply location filters
        for event_type, filter_rules in filters.items():
            if event_type in event_types:
                if "min_x" in filter_rules:
                    query = query.filter(
                        (Event.event_type != event_type) |
                        (Event.x >= filter_rules["min_x"])
                    )
                
                if "outcome" in filter_rules:
                    query = query.filter(
                        (Event.event_type != event_type) |
                        (Event.outcome == filter_rules["outcome"])
                    )
        
        count = query.count()
        logger.debug(
            f"Counted {count} attacks for team {team_id} "
            f"using definition '{definition}'"
        )
        return count
    
    except Exception as e:
        logger.error(f"Error counting attacks: {e}", exc_info=True)
        return 0


# ===== COUNT DEFENSE EVENTS =====

def count_defenses(
    team_id: int,
    match_ids: list,
    definition: str = "all_combined",
    db: Session = None,
) -> int:
    """
    Count defense events for a team across multiple matches.
    
    Args:
        team_id: Team ID
        match_ids: List of match IDs to search
        definition: Defense definition to use
        db: Database session
    
    Returns:
        Count of defense events
    """
    if not db or not match_ids:
        return 0
    
    if definition not in DEFENSE_DEFINITIONS:
        logger.warning(f"Unknown defense definition: {definition}, using all_combined")
        definition = "all_combined"
    
    defense_def = DEFENSE_DEFINITIONS[definition]
    event_types = defense_def["event_types"]
    filters = defense_def["filters"]
    
    try:
        query = db.query(Event).filter(
            and_(
                Event.match_id.in_(match_ids),
                Event.team_id == team_id,
                Event.event_type.in_(event_types),
            )
        )
        
        # Apply filters
        for event_type, filter_rules in filters.items():
            if event_type in event_types:
                if "outcome" in filter_rules:
                    query = query.filter(
                        (Event.event_type != event_type) |
                        (Event.outcome == filter_rules["outcome"])
                    )
        
        count = query.count()
        logger.debug(
            f"Counted {count} defenses for team {team_id} "
            f"using definition '{definition}'"
        )
        return count
    
    except Exception as e:
        logger.error(f"Error counting defenses: {e}", exc_info=True)
        return 0


# ===== VALIDATION FUNCTIONS =====

def is_valid_attack_definition(definition: str) -> bool:
    """Check if attack definition is valid"""
    return definition in ATTACK_DEFINITIONS


def is_valid_defense_definition(definition: str) -> bool:
    """Check if defense definition is valid"""
    return definition in DEFENSE_DEFINITIONS


def get_attack_definitions() -> dict:
    """Get all available attack definitions with descriptions"""
    return {
        key: value["description"]
        for key, value in ATTACK_DEFINITIONS.items()
    }


def get_defense_definitions() -> dict:
    """Get all available defense definitions with descriptions"""
    return {
        key: value["description"]
        for key, value in DEFENSE_DEFINITIONS.items()
    }
