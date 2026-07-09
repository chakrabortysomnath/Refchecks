"""
Statistics and Visualization API routes.
Provide data formatted for charts, heatmaps, and scatter plots.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models import Competition, Match, Foul, BiasMetrics, Team
from app.schemas import StatisticsResponse, HeatmapDataPoint, ScatterDataPoint


logger = logging.getLogger(__name__)
router = APIRouter()


# ===== GET VISUALIZATION DATA =====

@router.get("/competitions/{competition_id}/statistics", response_model=StatisticsResponse)
async def get_statistics(
    competition_id: int,
    db: Session = Depends(get_db),
):
    """
    Get data formatted for visualization (heatmaps and scatter plots).
    
    Args:
        competition_id: Competition ID
    
    Returns:
        StatisticsResponse with heatmap and scatter data
    
    Example Response:
        {
            "competition_id": 1,
            "heatmap_data": [
                {
                    "team": "Argentina",
                    "match_id": 1,
                    "match_description": "vs Saudi Arabia",
                    "foul_ratio": 0.286,
                    "fouls_committed": 8,
                    "attacks": 28
                }
            ],
            "scatter_data": [
                {
                    "team": "Argentina",
                    "team_id": 1,
                    "attacks": 180,
                    "defenses": 220,
                    "fouls_committed": 45,
                    "match_importance": "Group Stage"
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
        
        # ===== HEATMAP DATA: Team × Match with foul ratios =====
        heatmap_data = []
        
        matches = db.query(Match).filter(
            Match.competition_id == competition_id
        ).order_by(Match.match_date).all()
        
        for match in matches:
            # Home team heatmap point
            home_fouls = db.query(Foul).filter(
                (Foul.match_id == match.id) &
                (Foul.team_fouls_id == match.home_team_id)
            ).count()
            
            home_bias = db.query(BiasMetrics).filter(
                (BiasMetrics.competition_id == competition_id) &
                (BiasMetrics.team_id == match.home_team_id)
            ).first()
            
            if home_bias and home_bias.total_attacks > 0:
                foul_ratio = home_fouls / home_bias.total_attacks if home_bias.total_attacks > 0 else 0
                heatmap_data.append(HeatmapDataPoint(
                    team=match.home_team_name,
                    match_id=match.id,
                    match_description=f"vs {match.away_team_name}",
                    foul_ratio=round(foul_ratio, 4),
                    fouls_committed=home_fouls,
                    attacks=home_bias.total_attacks,
                ))
            
            # Away team heatmap point
            away_fouls = db.query(Foul).filter(
                (Foul.match_id == match.id) &
                (Foul.team_fouls_id == match.away_team_id)
            ).count()
            
            away_bias = db.query(BiasMetrics).filter(
                (BiasMetrics.competition_id == competition_id) &
                (BiasMetrics.team_id == match.away_team_id)
            ).first()
            
            if away_bias and away_bias.total_attacks > 0:
                foul_ratio = away_fouls / away_bias.total_attacks if away_bias.total_attacks > 0 else 0
                heatmap_data.append(HeatmapDataPoint(
                    team=match.away_team_name,
                    match_id=match.id,
                    match_description=f"vs {match.home_team_name}",
                    foul_ratio=round(foul_ratio, 4),
                    fouls_committed=away_fouls,
                    attacks=away_bias.total_attacks,
                ))
        
        # ===== SCATTER DATA: Attacks vs Fouls by Team =====
        scatter_data = []
        
        bias_metrics_all = db.query(BiasMetrics).filter(
            BiasMetrics.competition_id == competition_id
        ).all()
        
        for bias in bias_metrics_all:
            team = db.query(Team).filter(Team.id == bias.team_id).first()
            if team:
                scatter_data.append(ScatterDataPoint(
                    team=team.name,
                    team_id=team.id,
                    attacks=bias.total_attacks,
                    defenses=bias.total_defenses,
                    fouls_committed=bias.fouls_committed_count,
                    match_importance="Group Stage",  # TODO: Implement tournament phase detection
                ))
        
        logger.info(
            f"Retrieved statistics for {competition.name}: "
            f"{len(heatmap_data)} heatmap points, {len(scatter_data)} scatter points"
        )
        
        return StatisticsResponse(
            competition_id=competition_id,
            heatmap_data=heatmap_data,
            scatter_data=scatter_data,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch statistics",
        )


# ===== GET HEATMAP DATA ONLY =====

@router.get("/competitions/{competition_id}/heatmap")
async def get_heatmap_data(
    competition_id: int,
    db: Session = Depends(get_db),
):
    """
    Get heatmap data (Team × Match with foul ratios).
    
    Args:
        competition_id: Competition ID
    
    Returns:
        List of heatmap data points
    """
    try:
        stats = await get_statistics(competition_id, db)
        return {
            "competition_id": competition_id,
            "data": stats.heatmap_data,
        }
    except Exception as e:
        logger.error(f"Error fetching heatmap: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch heatmap data",
        )


# ===== GET SCATTER DATA ONLY =====

@router.get("/competitions/{competition_id}/scatter")
async def get_scatter_data(
    competition_id: int,
    db: Session = Depends(get_db),
):
    """
    Get scatter plot data (Attacks vs Fouls by Team).
    
    Args:
        competition_id: Competition ID
    
    Returns:
        List of scatter data points
    """
    try:
        stats = await get_statistics(competition_id, db)
        return {
            "competition_id": competition_id,
            "data": stats.scatter_data,
        }
    except Exception as e:
        logger.error(f"Error fetching scatter: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch scatter data",
        )
