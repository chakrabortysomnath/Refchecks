"""
Pydantic schemas for request/response validation and serialization.
Separate from ORM models for cleaner API contracts.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ===== COMPETITION SCHEMAS =====

class CompetitionBase(BaseModel):
    name: str
    season: int
    country: Optional[str] = None


class CompetitionCreate(CompetitionBase):
    statsbomb_id: str


class CompetitionResponse(CompetitionBase):
    id: int
    statsbomb_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===== TEAM SCHEMAS =====

class TeamBase(BaseModel):
    name: str
    country: Optional[str] = None


class TeamCreate(TeamBase):
    statsbomb_id: int


class TeamResponse(TeamBase):
    id: int
    statsbomb_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== MATCH SCHEMAS =====

class MatchBase(BaseModel):
    home_team_name: str
    away_team_name: str
    match_date: datetime
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: Optional[str] = None


class MatchCreate(MatchBase):
    statsbomb_id: str
    competition_id: int
    home_team_id: int
    away_team_id: int


class MatchResponse(MatchBase):
    id: int
    statsbomb_id: str
    competition_id: int
    home_team_id: int
    away_team_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===== EVENT SCHEMAS =====

class EventBase(BaseModel):
    event_type: str
    player_name: Optional[str] = None
    timestamp: Optional[int] = None
    period: Optional[int] = None
    x: Optional[float] = None
    y: Optional[float] = None


class EventCreate(EventBase):
    statsbomb_id: str
    match_id: int
    team_id: int
    player_id: Optional[int] = None
    event_subtype: Optional[str] = None
    outcome: Optional[str] = None
    raw_data: Optional[dict] = None


class EventResponse(EventBase):
    id: int
    statsbomb_id: str
    match_id: int
    team_id: int
    event_subtype: Optional[str] = None
    outcome: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== FOUL SCHEMAS =====

class FoulBase(BaseModel):
    foul_type: str
    card_type: Optional[str] = None
    timestamp: Optional[int] = None
    x: Optional[float] = None
    y: Optional[float] = None
    period: Optional[int] = None


class FoulCreate(FoulBase):
    event_id: int
    match_id: int
    team_fouls_id: int
    team_fouls_against_id: int
    raw_data: Optional[dict] = None


class FoulResponse(FoulBase):
    id: int
    event_id: int
    match_id: int
    team_fouls_id: int
    team_fouls_against_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== ATTACK/DEFENSE EVENT SCHEMAS =====

class AttackEventResponse(BaseModel):
    id: int
    match_id: int
    team_id: int
    attack_count: int
    shot_count: int
    shot_assist_count: int
    final_third_pass_count: int
    dribble_count: int
    carry_count: int
    calculated_at: datetime
    
    class Config:
        from_attributes = True


class DefenseEventResponse(BaseModel):
    id: int
    match_id: int
    team_id: int
    defense_count: int
    tackle_count: int
    interception_count: int
    block_count: int
    clearance_count: int
    duel_won_count: int
    calculated_at: datetime
    
    class Config:
        from_attributes = True


# ===== BIAS METRICS SCHEMAS =====

class BiasMetricsResponse(BaseModel):
    id: int
    competition_id: int
    team_id: int
    fouls_committed_count: int
    fouls_conceded_count: int
    total_attacks: int
    total_defenses: int
    fouls_per_attack: float
    fouls_per_defense: float
    chi_square_stat: Optional[float] = None
    p_value: Optional[float] = None
    is_significant: bool
    calculated_at: datetime
    
    class Config:
        from_attributes = True


class BiasAnalysisResponse(BaseModel):
    """Response for full bias analysis"""
    competition_id: int
    analysis_date: datetime
    teams: List[BiasMetricsResponse]


# ===== USER SCHEMAS =====

class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    google_id: str


class UserResponse(UserBase):
    id: int
    google_id: str
    role: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===== AUTHENTICATION SCHEMAS =====

class GoogleTokenRequest(BaseModel):
    """OAuth token from Google client"""
    token: str = Field(..., description="Google OAuth ID token")


class TokenResponse(BaseModel):
    """JWT token for authenticated requests"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user id or email
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp


# ===== MATCH DETAIL SCHEMA =====

class MatchDetailResponse(BaseModel):
    """Full match details with fouls"""
    match: MatchResponse
    fouls: List[FoulResponse]
    home_team_attacks: int
    away_team_attacks: int
    home_team_defenses: int
    away_team_defenses: int
    home_team_fouls_committed: List[FoulResponse]
    away_team_fouls_committed: List[FoulResponse]


# ===== VISUALIZATION DATA SCHEMA =====

class HeatmapDataPoint(BaseModel):
    team: str
    match_id: int
    match_description: str
    foul_ratio: float
    fouls_committed: int
    attacks: int


class ScatterDataPoint(BaseModel):
    team: str
    team_id: int
    attacks: int
    defenses: int
    fouls_committed: int
    match_importance: str


class StatisticsResponse(BaseModel):
    """Response for visualization data"""
    competition_id: int
    heatmap_data: List[HeatmapDataPoint]
    scatter_data: List[ScatterDataPoint]
