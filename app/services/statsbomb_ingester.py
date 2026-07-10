"""
Statsbomb data ingestion service.
Fetches competition, match, and event data from Statsbomb Open Data GitHub repository.
Parses and loads into database.
"""

import requests
import json
import logging
from sqlalchemy.orm import Session
from datetime import datetime
import tempfile
import zipfile
import os

from app.models import (
    Competition, Team, Match, Event, Foul
)
from app.config import settings


logger = logging.getLogger(__name__)

BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"


# ===== FETCH COMPETITIONS =====

def fetch_competitions() -> dict:
    """
    Fetch all competitions metadata from Statsbomb.
    
    Returns:
        Dictionary mapping competition names to their Statsbomb IDs
    """
    try:
        url = f"{BASE_URL}/competitions.json"
        logger.info(f"Fetching competitions from {url}")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        competitions = response.json()
        comp_map = {}
        
        for comp in competitions:
            comp_id = str(comp.get("competition_id"))
            season_id = str(comp.get("season_id"))
            name = comp.get("competition_name", "Unknown")
            season = comp.get("season_name", "")
            
            key = f"{name} - {season}"
            comp_map[key] = {
                "statsbomb_id": comp_id,
                "season_id": season_id,
                "country": comp.get("country_name"),
                "season": int(season.split("/")[0]) if season else None,
            }
        
        logger.info(f"Found {len(comp_map)} competitions")
        return comp_map
    
    except Exception as e:
        logger.error(f"Failed to fetch competitions: {e}")
        raise


# ===== FETCH MATCHES =====

def fetch_matches(competition_id: str, season_id: str) -> list:
    """
    Fetch all matches for a specific competition and season.
    
    Args:
        competition_id: Statsbomb competition ID
        season_id: Statsbomb season ID
    
    Returns:
        List of match dictionaries
    """
    try:
        url = f"{BASE_URL}/matches/{competition_id}/{season_id}.json"
        logger.info(f"Fetching matches from {url}")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        matches = response.json()
        logger.info(f"Found {len(matches)} matches")
        return matches
    
    except Exception as e:
        logger.error(f"Failed to fetch matches: {e}")
        raise


# ===== FETCH EVENTS =====

def fetch_events(match_id: str) -> list:
    """
    Fetch all events for a specific match.
    
    Args:
        match_id: Statsbomb match ID
    
    Returns:
        List of event dictionaries
    """
    try:
        url = f"{BASE_URL}/events/{match_id}.json"
        logger.debug(f"Fetching events from {url}")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        events = response.json()
        logger.debug(f"Found {len(events)} events in match {match_id}")
        return events
    
    except Exception as e:
        logger.error(f"Failed to fetch events for match {match_id}: {e}")
        return []


# ===== LOAD COMPETITION DATA =====

def load_competition_data(
    competition_name: str,
    db: Session,
) -> Competition:
    """
    Load complete competition data (metadata, matches, events).
    
    Args:
        competition_name: Name of competition (e.g., "FIFA World Cup - 2022")
        db: Database session
    
    Returns:
        Competition object
    """
    try:
        # Fetch competitions metadata
        comps = fetch_competitions()
        
        if competition_name not in comps:
            raise ValueError(f"Competition '{competition_name}' not found")
        
        comp_info = comps[competition_name]
        competition_id = comp_info["statsbomb_id"]
        season_id = comp_info["season_id"]
        
        logger.info(f"Loading {competition_name}")
        
        # Check if competition already exists (idempotent - won't create a duplicate)
        comp = db.query(Competition).filter(
            Competition.statsbomb_id == competition_id
        ).first()
        
        if comp:
            logger.info(f"Competition {competition_name} already exists (id={comp.id}) - will still check/load matches")
        else:
            # Create competition
            comp = Competition(
                statsbomb_id=competition_id,
                name=comp_info.get("competition_name", competition_name.split(" - ")[0]),
                season=comp_info["season"],
                country=comp_info["country"],
            )
            db.add(comp)
            db.commit()
            db.refresh(comp)
            logger.info(f"Created competition: {comp.name}")
        
        # Fetch and load matches.
        # NOTE: This always runs, even if the competition record already existed -
        # load_match_data() checks each match individually by statsbomb_id, so
        # already-loaded matches are skipped and only missing/failed ones are (re)loaded.
        matches_data = fetch_matches(competition_id, season_id)
        
        for match_data in matches_data:
            load_match_data(match_data, comp.id, db)
        
        logger.info(f"Processed {len(matches_data)} matches for {comp.name}")
        return comp
    
    except Exception as e:
        logger.error(f"Failed to load competition: {e}", exc_info=True)
        db.rollback()
        raise


# ===== LOAD MATCH DATA =====

def load_match_data(match_data: dict, competition_id: int, db: Session):
    """
    Load a single match and its events.
    
    Args:
        match_data: Match dictionary from Statsbomb API
        competition_id: Competition ID in database
        db: Database session
    """
    try:
        match_id = str(match_data.get("match_id"))
        
        # Check if match already loaded
        existing = db.query(Match).filter(
            Match.statsbomb_id == match_id
        ).first()
        
        if existing:
            logger.debug(f"Match {match_id} already loaded")
            return
        
        # Get or create teams.
        # NOTE: Statsbomb's matches.json uses PREFIXED keys for team info
        # ("home_team_id", "home_team_name", "country") - not the plain
        # "id"/"name" shape used in events.json. Normalize here before
        # passing to get_or_create_team(), which expects the plain shape.
        home_team_raw = match_data.get("home_team", {})
        away_team_raw = match_data.get("away_team", {})

        home_team_data = {
            "id": home_team_raw.get("home_team_id"),
            "name": home_team_raw.get("home_team_name"),
            "country": home_team_raw.get("country", {}),
        }
        away_team_data = {
            "id": away_team_raw.get("away_team_id"),
            "name": away_team_raw.get("away_team_name"),
            "country": away_team_raw.get("country", {}),
        }
        
        home_team = get_or_create_team(home_team_data, db)
        away_team = get_or_create_team(away_team_data, db)
        
        # Statsbomb match_date is usually date-only ("2022-11-20"), sometimes with time.
        raw_date = match_data.get("match_date", "2020-01-01")
        try:
            match_date_parsed = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            match_date_parsed = datetime(2020, 1, 1)

        # Create match
        match = Match(
            statsbomb_id=match_id,
            competition_id=competition_id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            home_team_name=home_team_data.get("name"),
            away_team_name=away_team_data.get("name"),
            match_date=match_date_parsed,
            home_score=match_data.get("home_score"),
            away_score=match_data.get("away_score"),
            status=match_data.get("match_status", match_data.get("status", "completed")),
        )
        db.add(match)
        db.flush()
        
        # Fetch and load events
        events_data = fetch_events(match_id)
        
        for event_data in events_data:
            load_event_data(event_data, match.id, db)
        
        db.commit()
        logger.debug(f"Loaded match {match_id} with {len(events_data)} events")
    
    except Exception as e:
        logger.error(f"Failed to load match: {e}", exc_info=True)
        db.rollback()


# ===== LOAD EVENT DATA =====

def load_event_data(event_data: dict, match_id: int, db: Session):
    """
    Load a single event (and foul if applicable).
    
    Args:
        event_data: Event dictionary from Statsbomb API
        match_id: Match ID in database
        db: Database session
    """
    try:
        event_type = event_data.get("type", {}).get("name")
        team_data = event_data.get("team", {})
        team_id = team_data.get("id")
        
        # Get or create team
        team = db.query(Team).filter(Team.statsbomb_id == team_id).first()
        if not team:
            team = get_or_create_team(team_data, db)
        
        # Statsbomb timestamps are formatted "HH:MM:SS.mmm" (time within the period),
        # not "MM:SS" - convert to total seconds for consistent storage.
        timestamp_str = event_data.get("timestamp", "00:00:00.000")
        try:
            h, m, s = timestamp_str.split(":")
            timestamp_seconds = int(h) * 3600 + int(m) * 60 + int(float(s))
        except (ValueError, AttributeError):
            timestamp_seconds = 0

        # Create event
        event = Event(
            statsbomb_id=event_data.get("id"),
            match_id=match_id,
            team_id=team.id,
            player_id=event_data.get("player", {}).get("id"),
            player_name=event_data.get("player", {}).get("name"),
            event_type=event_type,
            event_subtype=event_data.get("type", {}).get("subtype"),
            timestamp=timestamp_seconds,
            period=event_data.get("period"),
            x=event_data.get("location", [None, None])[0],
            y=event_data.get("location", [None, None])[1],
            outcome=event_data.get("outcome", {}).get("name"),
            raw_data=event_data,
        )
        db.add(event)
        db.flush()
        
        # If it's a foul, create foul record
        if event_type == "Foul Committed":
            create_foul_record(event, event_data, match_id, db)
    
    except Exception as e:
        logger.error(f"Failed to load event: {e}")
        # Don't raise, continue with other events


# ===== CREATE FOUL RECORD =====

def create_foul_record(event: Event, event_data: dict, match_id: int, db: Session):
    """
    Create a foul record from an event.
    
    Args:
        event: Event object (already created)
        event_data: Raw Statsbomb event data
        match_id: Match ID
        db: Database session
    """
    try:
        foul = Foul(
            event_id=event.id,
            match_id=match_id,
            team_fouls_id=event.team_id,
            team_fouls_against_id=None,  # Would need match context to get this
            foul_type=event_data.get("foul_committed", {}).get("type"),
            card_type=event_data.get("foul_committed", {}).get("card", {}).get("type"),
            timestamp=event.timestamp,
            x=event.x,
            y=event.y,
            period=event.period,
            raw_data=event_data,
        )
        db.add(foul)
    except Exception as e:
        logger.warning(f"Failed to create foul record: {e}")


# ===== GET OR CREATE TEAM =====

def get_or_create_team(team_data: dict, db: Session) -> Team:
    """
    Get existing team or create new one.
    
    Args:
        team_data: Team dictionary from Statsbomb API
        db: Database session
    
    Returns:
        Team object
    """
    team_id = team_data.get("id")
    
    team = db.query(Team).filter(Team.statsbomb_id == team_id).first()
    
    if not team:
        team = Team(
            statsbomb_id=team_id,
            name=team_data.get("name"),
            country=team_data.get("country", {}).get("name"),
        )
        db.add(team)
        db.flush()
    
    return team