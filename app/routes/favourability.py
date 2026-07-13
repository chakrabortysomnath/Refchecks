"""
Favourability analysis API route.

The rebuilt "referee bias in a team's favour" endpoint: a severity-weighted,
expected-vs-actual residual model. See services/favourability_calculator.py for
the methodology.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models import Competition
from app.services.favourability_calculator import calculate_favourability


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/competitions/{competition_id}/favourability")
async def get_favourability(
    competition_id: int,
    attack_definition: str = Query("all_combined"),
    defense_definition: str = Query("all_combined"),
    w_penalty: float = Query(5.0, ge=0, description="Weight for a penalty awarded"),
    w_red: float = Query(4.0, ge=0, description="Weight for a red / second-yellow"),
    w_yellow: float = Query(2.0, ge=0, description="Weight for a yellow card"),
    w_foul: float = Query(1.0, ge=0, description="Weight for an ordinary foul"),
    w_advantage: float = Query(0.5, ge=0, description="Weight for advantage played"),
    db: Session = Depends(get_db),
):
    """
    Severity-weighted refereeing favourability per team.

    Each foul is weighted by decision severity (penalty / red / yellow /
    ordinary / advantage-played; every weight configurable via query params).
    For each team we compare weighted fouls committed and awarded against what a
    neutral referee would be expected to give for that team's own attack /
    defense volume, and express the gap as a standardized residual:

      * z_leniency   - let off when defending (fewer fouls called against them)
      * z_protection - protected when attacking (more fouls awarded to them)
      * favourability = z_leniency + z_protection  (positive = net favoured)

    Teams are returned sorted most-favoured first.
    """
    competition = db.query(Competition).filter(
        Competition.id == competition_id
    ).first()
    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competition {competition_id} not found",
        )

    try:
        return calculate_favourability(
            competition_id=competition_id,
            attack_definition=attack_definition,
            defense_definition=defense_definition,
            weights={
                "penalty": w_penalty,
                "red": w_red,
                "yellow": w_yellow,
                "foul": w_foul,
                "advantage": w_advantage,
            },
            db=db,
        )
    except Exception as e:
        logger.error(f"Error calculating favourability: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate favourability",
        )
