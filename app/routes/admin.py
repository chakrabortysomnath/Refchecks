"""
Temporary admin routes for setup tasks.
These let you initialize the database and load Statsbomb data via HTTP,
since Render's free tier doesn't include Shell access.

SECURITY NOTE: Protected by a simple secret key query param.
Remove this file (or at least tighten security) once initial setup is done.
"""

from fastapi import APIRouter, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from app.database import get_db, create_all_tables, SessionLocal
from app.config import settings
from app.services.statsbomb_ingester import fetch_competitions, load_competition_data
from app.services.bias_calculator import calculate_competition_bias


logger = logging.getLogger(__name__)
router = APIRouter()

# Simple shared-secret check so random internet visitors can't trigger this.
# Set ADMIN_SETUP_KEY as an environment variable in Render.
ADMIN_SETUP_KEY = getattr(settings, "admin_setup_key", "changeme-setup-key")


def _check_key(key: str):
    if key != ADMIN_SETUP_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid setup key",
        )


# ===== INIT DATABASE TABLES =====

@router.post("/admin/init-db")
async def init_db(key: str = Query(..., description="Admin setup key")):
    """
    Create all database tables.
    Call once after first deployment.

    Example:
        POST /admin/init-db?key=YOUR_SETUP_KEY
    """
    _check_key(key)
    try:
        create_all_tables()
        logger.info("Database tables created via admin endpoint")
        return {"status": "success", "message": "Database tables created"}
    except Exception as e:
        logger.error(f"init_db failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===== LIST AVAILABLE STATSBOMB COMPETITIONS =====

@router.get("/admin/list-competitions")
async def list_available_competitions(key: str = Query(...)):
    """
    List all competitions available from Statsbomb Open Data.
    Use this to find the exact name string to pass to /admin/load-competition.

    Example:
        GET /admin/list-competitions?key=YOUR_SETUP_KEY
    """
    _check_key(key)
    try:
        comps = fetch_competitions()
        return {"count": len(comps), "competitions": sorted(comps.keys())}
    except Exception as e:
        logger.error(f"list_competitions failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===== LOAD A COMPETITION (runs in background, returns immediately) =====

@router.post("/admin/load-competition")
async def load_competition(
    background_tasks: BackgroundTasks,
    competition_name: str = Query(..., description="Exact competition name from /admin/list-competitions"),
    key: str = Query(...),
):
    """
    Load a competition's matches and events from Statsbomb, then calculate
    bias metrics. Runs in the background since it can take a few minutes.

    Example:
        POST /admin/load-competition?competition_name=FIFA%20World%20Cup%20-%202022&key=YOUR_SETUP_KEY

    Check progress via logs, or poll GET /api/competitions afterwards.
    """
    _check_key(key)

    def _run():
        db = SessionLocal()
        try:
            logger.info(f"[admin] Starting load for: {competition_name}")
            competition = load_competition_data(competition_name, db)
            logger.info(f"[admin] Loaded {competition.name}, calculating bias metrics...")
            calculate_competition_bias(competition_id=competition.id, db=db)
            logger.info(f"[admin] Finished loading {competition.name}")
        except Exception as e:
            logger.error(f"[admin] Background load failed: {e}", exc_info=True)
        finally:
            db.close()

    background_tasks.add_task(_run)

    return {
        "status": "started",
        "message": f"Loading '{competition_name}' in the background. This can take several minutes.",
        "check_progress": "GET /api/competitions (once it appears, loading succeeded)",
    }
