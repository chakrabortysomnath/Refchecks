"""
Matches API routes.
Get matches, match details, and foul information.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models import Match, Foul, Competition
from app.schemas import MatchResponse, FoulResponse, MatchDetailResponse


logger = logging.getLogger(__name__)
router = APIRouter()


# ===== GET ALL MATCHES IN COMPETITION =====

@router.get("/competitions/{competition_id}/matches", response_model=list[MatchResponse])
async def get_matches_by_competition(
    competition_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all matches in a specific competition.
    
    Args:
        competition_id: Competition ID
    
    Returns:
        List of matches in the competition
    
    Raises:
        404: Competition not found
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
        
        # Get matches
        matches = db.query(Match).filter(
            Match.competition_id == competition_id
        ).order_by(Match.match_date).all()
        
        logger.info(f"Retrieved {len(matches)} matches for {competition.name}")
        return matches
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching matches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch matches",
        )


# ===== GET SINGLE MATCH =====

@router.get("/matches/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific match by ID.
    
    Args:
        match_id: Match ID
    
    Returns:
        Match details
    
    Raises:
        404: Match not found
    """
    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match {match_id} not found",
            )
        
        logger.info(f"Retrieved match: {match.home_team_name} vs {match.away_team_name}")
        return match
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching match: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch match",
        )


# ===== GET MATCH FOULS =====

@router.get("/matches/{match_id}/fouls", response_model=dict)
async def get_match_fouls(
    match_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all fouls in a match, separated by team.
    
    Args:
        match_id: Match ID
    
    Returns:
        Dictionary with fouls by team
    
    Example Response:
        {
            "match_id": 1,
            "home_team": "Argentina",
            "away_team": "Saudi Arabia",
            "home_team_fouls_committed": [
                {
                    "id": 1,
                    "foul_type": "Tackle",
                    "timestamp": 120,
                    "x": 50.0,
                    "y": 40.0,
                    ...
                }
            ],
            "away_team_fouls_committed": [...]
        }
    """
    try:
        # Get match
        match = db.query(Match).filter(Match.id == match_id).first()
        
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match {match_id} not found",
            )
        
        # Get fouls by home team
        home_fouls = db.query(Foul).filter(
            (Foul.match_id == match_id) &
            (Foul.team_fouls_id == match.home_team_id)
        ).all()
        
        # Get fouls by away team
        away_fouls = db.query(Foul).filter(
            (Foul.match_id == match_id) &
            (Foul.team_fouls_id == match.away_team_id)
        ).all()
        
        logger.info(
            f"Retrieved {len(home_fouls)} + {len(away_fouls)} fouls for match {match_id}"
        )
        
        return {
            "match_id": match_id,
            "home_team": match.home_team_name,
            "away_team": match.away_team_name,
            "match_date": match.match_date,
            "home_team_fouls_committed": [
                {
                    "id": f.id,
                    "foul_type": f.foul_type,
                    "card_type": f.card_type,
                    "timestamp": f.timestamp,
                    "x": f.x,
                    "y": f.y,
                    "period": f.period,
                }
                for f in home_fouls
            ],
            "away_team_fouls_committed": [
                {
                    "id": f.id,
                    "foul_type": f.foul_type,
                    "card_type": f.card_type,
                    "timestamp": f.timestamp,
                    "x": f.x,
                    "y": f.y,
                    "period": f.period,
                }
                for f in away_fouls
            ],
            "total_home_fouls": len(home_fouls),
            "total_away_fouls": len(away_fouls),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fouls: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch fouls",
        )
