"""
Competitions API routes.
Get competitions, load their data, and manage competition-level operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models import Competition, Match
from app.schemas import CompetitionResponse


logger = logging.getLogger(__name__)
router = APIRouter()


# ===== GET ALL COMPETITIONS =====

@router.get("/competitions", response_model=list[CompetitionResponse])
async def get_competitions(db: Session = Depends(get_db)):
    """
    Get all available competitions.
    
    Returns:
        List of competitions with metadata
    
    Example Response:
        [
            {
                "id": 1,
                "name": "FIFA World Cup",
                "season": 2022,
                "country": "Qatar",
                "statsbomb_id": "43",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        ]
    """
    try:
        competitions = db.query(Competition).all()
        
        if not competitions:
            logger.warning("No competitions found in database")
            return []
        
        logger.info(f"Retrieved {len(competitions)} competitions")
        return competitions
    
    except Exception as e:
        logger.error(f"Error fetching competitions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch competitions",
        )


# ===== GET SINGLE COMPETITION =====

@router.get("/competitions/{competition_id}", response_model=CompetitionResponse)
async def get_competition(
    competition_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific competition by ID.
    
    Args:
        competition_id: Competition ID
    
    Returns:
        Competition details
    
    Raises:
        404: Competition not found
    """
    try:
        competition = db.query(Competition).filter(
            Competition.id == competition_id
        ).first()
        
        if not competition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Competition {competition_id} not found",
            )
        
        logger.info(f"Retrieved competition: {competition.name}")
        return competition
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching competition: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch competition",
        )


# ===== GET COMPETITION MATCH COUNT =====

@router.get("/competitions/{competition_id}/match-count")
async def get_competition_match_count(
    competition_id: int,
    db: Session = Depends(get_db),
):
    """
    Get number of matches in a competition.
    
    Args:
        competition_id: Competition ID
    
    Returns:
        Dictionary with match count
    """
    try:
        competition = db.query(Competition).filter(
            Competition.id == competition_id
        ).first()
        
        if not competition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Competition {competition_id} not found",
            )
        
        match_count = db.query(Match).filter(
            Match.competition_id == competition_id
        ).count()
        
        return {
            "competition_id": competition_id,
            "competition_name": competition.name,
            "match_count": match_count,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error counting matches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to count matches",
        )


# ===== CREATE COMPETITION (for data loading) =====

@router.post("/competitions", response_model=CompetitionResponse)
async def create_competition(
    competition: CompetitionResponse,
    db: Session = Depends(get_db),
):
    """
    Create a new competition (admin only).
    Called during Statsbomb data ingestion.
    
    Args:
        competition: Competition data
        db: Database session
    
    Returns:
        Created competition
    """
    try:
        # Check if competition already exists
        existing = db.query(Competition).filter(
            Competition.statsbomb_id == competition.statsbomb_id
        ).first()
        
        if existing:
            logger.warning(f"Competition {competition.name} already exists")
            return existing
        
        new_competition = Competition(
            statsbomb_id=competition.statsbomb_id,
            name=competition.name,
            season=competition.season,
            country=competition.country,
        )
        
        db.add(new_competition)
        db.commit()
        db.refresh(new_competition)
        
        logger.info(f"Created competition: {new_competition.name}")
        return new_competition
    
    except Exception as e:
        logger.error(f"Error creating competition: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create competition",
        )
