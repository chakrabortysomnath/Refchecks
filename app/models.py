"""
SQLAlchemy ORM models for RefChecks database.
Defines 8 tables: competitions, matches, teams, events, fouls, 
attack_events, defense_events, bias_metrics, and users.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


# ===== TABLE 1: COMPETITIONS =====

class Competition(Base):
    __tablename__ = "competitions"
    
    id = Column(Integer, primary_key=True)
    statsbomb_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    season = Column(Integer, nullable=False)
    country = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    matches = relationship("Match", back_populates="competition")
    bias_metrics = relationship("BiasMetrics", back_populates="competition")
    
    def __repr__(self):
        return f"<Competition {self.name} ({self.season})>"


# ===== TABLE 2: TEAMS =====

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    statsbomb_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    country = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")
    events = relationship("Event", back_populates="team")
    attack_events = relationship("AttackEvent", back_populates="team")
    defense_events = relationship("DefenseEvent", back_populates="team")
    bias_metrics = relationship("BiasMetrics", back_populates="team")
    
    def __repr__(self):
        return f"<Team {self.name}>"


# ===== TABLE 3: MATCHES =====

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True)
    statsbomb_id = Column(String(50), unique=True, nullable=False)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    home_team_name = Column(String(100))
    away_team_name = Column(String(100))
    match_date = Column(DateTime, nullable=False)
    home_score = Column(Integer)
    away_score = Column(Integer)
    status = Column(String(20))  # completed, scheduled, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for faster queries
    __table_args__ = (
        Index("idx_match_competition", "competition_id"),
        Index("idx_match_teams", "home_team_id", "away_team_id"),
    )
    
    # Relationships
    competition = relationship("Competition", back_populates="matches")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    events = relationship("Event", back_populates="match")
    fouls = relationship("Foul", back_populates="match")
    attack_events = relationship("AttackEvent", back_populates="match")
    defense_events = relationship("DefenseEvent", back_populates="match")
    
    def __repr__(self):
        return f"<Match {self.home_team_name} vs {self.away_team_name}>"


# ===== TABLE 4: EVENTS (All Statsbomb events) =====

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True)
    statsbomb_id = Column(String(50), unique=True, nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_id = Column(Integer)
    player_name = Column(String(100))
    event_type = Column(String(50), nullable=False)  # Pass, Shot, Tackle, etc.
    event_subtype = Column(String(50))
    timestamp = Column(Integer)  # Seconds into match
    period = Column(Integer)  # 1=1st half, 2=2nd half, etc.
    x = Column(Float)  # Pitch coordinates (0-120)
    y = Column(Float)  # Pitch coordinates (0-80)
    outcome = Column(String(20))  # Successful, Unsuccessful, etc.
    raw_data = Column(JSON)  # Store raw Statsbomb data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_event_match_team", "match_id", "team_id"),
        Index("idx_event_type", "event_type"),
    )
    
    # Relationships
    match = relationship("Match", back_populates="events")
    team = relationship("Team", back_populates="events")
    
    def __repr__(self):
        return f"<Event {self.event_type} - {self.player_name}>"


# ===== TABLE 5: FOULS (Whistled fouls from Statsbomb) =====

class Foul(Base):
    __tablename__ = "fouls"
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    team_fouls_id = Column(Integer, ForeignKey("teams.id"))  # Team that committed
    team_fouls_against_id = Column(Integer, ForeignKey("teams.id"))  # Team that was fouled
    foul_type = Column(String(100))  # Tackle, Handball, Contact, etc.
    card_type = Column(String(20))  # Yellow, Red, None
    timestamp = Column(Integer)
    x = Column(Float)
    y = Column(Float)
    period = Column(Integer)
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_foul_match", "match_id"),
        Index("idx_foul_teams", "team_fouls_id", "team_fouls_against_id"),
    )
    
    # Relationships
    match = relationship("Match", back_populates="fouls")
    
    def __repr__(self):
        return f"<Foul {self.foul_type} in match {self.match_id}>"


# ===== TABLE 6: ATTACK EVENTS (Cached attack counts) =====

class AttackEvent(Base):
    __tablename__ = "attack_events"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    attack_count = Column(Integer, default=0)  # Total attacks
    shot_count = Column(Integer, default=0)
    shot_assist_count = Column(Integer, default=0)
    final_third_pass_count = Column(Integer, default=0)
    dribble_count = Column(Integer, default=0)
    carry_count = Column(Integer, default=0)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Unique constraint: one record per match/team combo
    __table_args__ = (
        UniqueConstraint("match_id", "team_id", name="uq_attack_match_team"),
    )
    
    # Relationships
    match = relationship("Match", back_populates="attack_events")
    team = relationship("Team", back_populates="attack_events")
    
    def __repr__(self):
        return f"<AttackEvent {self.team_id} in match {self.match_id}>"


# ===== TABLE 7: DEFENSE EVENTS (Cached defense counts) =====

class DefenseEvent(Base):
    __tablename__ = "defense_events"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    defense_count = Column(Integer, default=0)  # Total defenses
    tackle_count = Column(Integer, default=0)
    interception_count = Column(Integer, default=0)
    block_count = Column(Integer, default=0)
    clearance_count = Column(Integer, default=0)
    duel_won_count = Column(Integer, default=0)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Unique constraint: one record per match/team combo
    __table_args__ = (
        UniqueConstraint("match_id", "team_id", name="uq_defense_match_team"),
    )
    
    # Relationships
    match = relationship("Match", back_populates="defense_events")
    team = relationship("Team", back_populates="defense_events")
    
    def __repr__(self):
        return f"<DefenseEvent {self.team_id} in match {self.match_id}>"


# ===== TABLE 8: BIAS METRICS (Cached analysis results) =====

class BiasMetrics(Base):
    __tablename__ = "bias_metrics"
    
    id = Column(Integer, primary_key=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    fouls_committed_count = Column(Integer, default=0)
    fouls_conceded_count = Column(Integer, default=0)
    total_attacks = Column(Integer, default=0)
    total_defenses = Column(Integer, default=0)
    fouls_per_attack = Column(Float, default=0.0)
    fouls_per_defense = Column(Float, default=0.0)
    chi_square_stat = Column(Float)
    p_value = Column(Float)
    is_significant = Column(Boolean, default=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Unique constraint: one record per competition/team combo
    __table_args__ = (
        UniqueConstraint("competition_id", "team_id", name="uq_bias_comp_team"),
    )
    
    # Relationships
    competition = relationship("Competition", back_populates="bias_metrics")
    team = relationship("Team", back_populates="bias_metrics")
    
    def __repr__(self):
        return f"<BiasMetrics {self.team_id} in competition {self.competition_id}>"


# ===== TABLE 9: USERS (For authentication) =====

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    google_id = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(100))
    role = Column(String(20), default="user")  # user, reviewer, admin
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
