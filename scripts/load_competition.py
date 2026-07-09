#!/usr/bin/env python
"""
CLI script to load Statsbomb competition data into the database.

Usage:
    python scripts/load_competition.py --competition "FIFA World Cup - 2022"
    python scripts/load_competition.py --list-competitions
    python scripts/load_competition.py --competition "UEFA Euro - 2024" --recalculate
"""

import argparse
import sys
import logging
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, '/home/claude/refchecks-backend')

from app.database import SessionLocal, create_all_tables
from app.services.statsbomb_ingester import (
    fetch_competitions,
    load_competition_data,
)
from app.services.bias_calculator import calculate_competition_bias


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def list_competitions():
    """List all available competitions"""
    try:
        comps = fetch_competitions()
        print("\n=== Available Competitions ===\n")
        for i, name in enumerate(sorted(comps.keys()), 1):
            print(f"{i}. {name}")
        print(f"\nTotal: {len(comps)} competitions\n")
    except Exception as e:
        logger.error(f"Failed to fetch competitions: {e}")
        sys.exit(1)


def load_competition(competition_name: str, recalculate: bool = False):
    """Load competition data"""
    try:
        db = SessionLocal()
        
        logger.info(f"Loading competition: {competition_name}")
        
        # Load all data
        competition = load_competition_data(competition_name, db)
        
        logger.info(f"✅ Successfully loaded {competition.name}")
        logger.info(f"   Matches: {len(competition.matches)}")
        
        # Calculate bias metrics
        if recalculate or True:  # Always calculate on load
            logger.info("Calculating bias metrics...")
            metrics = calculate_competition_bias(
                competition_id=competition.id,
                db=db,
            )
            logger.info(f"✅ Calculated metrics for {len(metrics)} teams")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Failed to load competition: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Load Statsbomb competition data into RefChecks database"
    )
    
    parser.add_argument(
        "--list-competitions",
        action="store_true",
        help="List all available competitions",
    )
    
    parser.add_argument(
        "--competition",
        type=str,
        help="Competition name to load (e.g., 'FIFA World Cup - 2022')",
    )
    
    parser.add_argument(
        "--recalculate",
        action="store_true",
        help="Force recalculation of bias metrics",
    )
    
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database tables",
    )
    
    args = parser.parse_args()
    
    # Initialize database tables if requested
    if args.init_db:
        logger.info("Initializing database tables...")
        try:
            create_all_tables()
            logger.info("✅ Database tables created")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            sys.exit(1)
    
    # List competitions
    if args.list_competitions:
        list_competitions()
        return
    
    # Load competition
    if args.competition:
        load_competition(args.competition, args.recalculate)
        return
    
    # Show help if no arguments
    parser.print_help()


if __name__ == "__main__":
    main()
