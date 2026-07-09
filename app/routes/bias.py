"""
Bias Analysis API routes.
Calculate and return bias metrics, chi-square tests, and foul ratios.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models import Competition, Team, BiasMetrics
from app.schemas import BiasAnalysisResponse, BiasMetricsResponse
from app.services.bias_calculator import calculate_competition_bias


logger = logging.getLogger(__name__)
router = APIRouter()


# ===== GET BIAS ANALYSIS FOR COMPETITION =====

@router.get("/competitions/{competition_id}/bias-analysis", response_model=BiasAnalysisResponse)
async def get_bias_analysis(
    competition_id: int,
    attack_definition: str = Query("all_combined", description="Attack definition type"),
    defense_definition: str = Query("all_combined", description="Defense definition type"),
    recalculate: bool = Query(False, description="Force recalculation of metrics"),
    db: Session = Depends(get_db),
):
    """
    Get bias analysis for all teams in a competition.
    
    Args:
        competition_id: Competition ID
        attack_definition: Type of attack events to count
            - "all_combined": Shots + Passes in final 3rd + Dribbles + Carries
            - "shots_only": Shots and shot assists
            - "passes_only": Passes in final third
            - "dribbles_only": Dribbles and carries
        defense_definition: Type of defense events to count
            - "all_combined": Tackles + Interceptions + Blocks + Clearances + Duels won
            - "tackles_only": Tackles
            - "blocks_only": Blocks and clearances
            - "duels_only": Duels won
        recalculate: Force recalculation even if cached
        db: Database session
    
    Returns:
        BiasAnalysisResponse with metrics for all teams
    
    Example Response:
        {
            "competition_id": 1,
            "analysis_date": "2024-01-15T00:00:00",
            "teams": [
                {
                    "id": 1,
                    "competition_id": 1,
                    "team_id": 1,
                    "fouls_committed_count": 45,
                    "fouls_conceded_count": 32,
                    "total_attacks": 180,
                    "total_defenses": 220,
                    "fouls_per_attack": 0.25,
                    "fouls_per_defense": 0.145,
                    "chi_square_stat": 3.47,
                    "p_value": 0.062,
                    "is_significant": false,
                    "calculated_at": "2024-01-15T00:00:00"
                }
            ]
        }
    """
    try:
        # Verify competition exists
        competition = db.query(Competition).filter(
            Competition.id == competition_id
        ).first()
        
        if not competition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Competition {competition_id} not found",
            )
        
        logger.info(
            f"Bias analysis for {competition.name} "
            f"(attack={attack_definition}, defense={defense_definition})"
        )
        
        # Calculate or retrieve bias metrics
        metrics = calculate_competition_bias(
            competition_id=competition_id,
            attack_definition=attack_definition,
            defense_definition=defense_definition,
            recalculate=recalculate,
            db=db,
        )
        
        return BiasAnalysisResponse(
            competition_id=competition_id,
            analysis_date=competition.updated_at,
            teams=metrics,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating bias analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate bias analysis",
        )


# ===== GET BIAS FOR SPECIFIC TEAM =====

@router.get("/teams/{team_id}/bias")
async def get_team_bias(
    team_id: int,
    competition_id: int = Query(..., description="Competition ID"),
    attack_definition: str = Query("all_combined"),
    defense_definition: str = Query("all_combined"),
    db: Session = Depends(get_db),
):
    """
    Get bias metrics for a specific team in a competition.
    
    Args:
        team_id: Team ID
        competition_id: Competition ID
        attack_definition: Attack definition type
        defense_definition: Defense definition type
        db: Database session
    
    Returns:
        Dictionary with team bias metrics and match breakdown
    
    Example Response:
        {
            "team_id": 1,
            "team_name": "Argentina",
            "competition_id": 1,
            "aggregate": {
                "total_fouls_committed": 45,
                "total_fouls_conceded": 32,
                "avg_fouls_per_attack": 0.25,
                "avg_fouls_per_defense": 0.145,
                "chi_square": 3.47,
                "p_value": 0.062,
                "is_significant": false
            },
            "matches": [
                {
                    "match_id": 1,
                    "opponent": "Saudi Arabia",
                    "fouls_committed": 8,
                    "fouls_conceded": 6,
                    "attacks": 28,
                    "defenses": 35,
                    "fouls_per_attack": 0.286,
                    "fouls_per_defense": 0.171
                }
            ]
        }
    """
    try:
        # Verify team and competition exist
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team {team_id} not found",
            )
        
        competition = db.query(Competition).filter(
            Competition.id == competition_id
        ).first()
        if not competition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Competition {competition_id} not found",
            )
        
        # Get cached bias metrics
        bias_metrics = db.query(BiasMetrics).filter(
            (BiasMetrics.team_id == team_id) &
            (BiasMetrics.competition_id == competition_id)
        ).first()
        
        if not bias_metrics:
            logger.warning(
                f"No bias metrics found for team {team_id} "
                f"in competition {competition_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bias metrics not calculated yet. Run /bias-analysis first.",
            )
        
        logger.info(f"Retrieved bias for {team.name} in {competition.name}")
        
        return {
            "team_id": team_id,
            "team_name": team.name,
            "competition_id": competition_id,
            "competition_name": competition.name,
            "aggregate": {
                "total_fouls_committed": bias_metrics.fouls_committed_count,
                "total_fouls_conceded": bias_metrics.fouls_conceded_count,
                "total_attacks": bias_metrics.total_attacks,
                "total_defenses": bias_metrics.total_defenses,
                "avg_fouls_per_attack": round(bias_metrics.fouls_per_attack, 4),
                "avg_fouls_per_defense": round(bias_metrics.fouls_per_defense, 4),
                "chi_square": round(bias_metrics.chi_square_stat, 4) if bias_metrics.chi_square_stat else None,
                "p_value": round(bias_metrics.p_value, 4) if bias_metrics.p_value else None,
                "is_significant": bias_metrics.is_significant,
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team bias: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch team bias metrics",
        )


# ===== DEFINITION OPTIONS ENDPOINT =====

@router.get("/definitions")
async def get_definitions():
    """
    Get available attack and defense definitions.
    
    Returns:
        Dictionary with all available definition options
    """
    return {
        "attack_definitions": {
            "all_combined": "Shots + Shot Assists + Passes in final 3rd + Dribbles + Carries in attacking zones",
            "shots_only": "Shots and Shot Assists only",
            "passes_only": "Passes in final third only",
            "dribbles_only": "Dribbles and Carries only",
        },
        "defense_definitions": {
            "all_combined": "Tackles + Interceptions + Blocks + Clearances + Duels (won)",
            "tackles_only": "Tackles only",
            "blocks_only": "Blocks and Clearances only",
            "duels_only": "Duels (won) only",
        }
    }
