"""
Pydantic models — request bodies, response shapes, enums
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Literal
from datetime import datetime
import re


# ─── ENUMS ───────────────────────────────────────────────────────────────────
GameType    = Literal["BGMI", "Free Fire", "Hackathon", "Quiz"]
BranchType  = Literal["CSE", "AI&DS", "ECE"]
PayStatus   = Literal["pending", "paid", "verified", "rejected"]


# ─── PLAYER ──────────────────────────────────────────────────────────────────
class Player(BaseModel):
    name:  str
    phone: str
    usn:   str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"\D", "", v)
        if len(cleaned) not in (10, 12):
            raise ValueError("Phone must be 10 digits (or 12 with country code)")
        return cleaned

    @field_validator("usn")
    @classmethod
    def validate_usn(cls, v: str) -> str:
        return v.strip().upper()


# ─── REGISTRATION REQUEST ─────────────────────────────────────────────────────
class TeamRegistrationRequest(BaseModel):
    game:     GameType
    email:    EmailStr
    branch:   BranchType
    semester: str

    # Captain (required)
    captain_name:  str
    captain_phone: str
    captain_usn:   str

    # Players 2-4 (optional — game may have < 4 required, but we accept up to 4)
    player2_name:  Optional[str] = None
    player2_phone: Optional[str] = None
    player2_usn:   Optional[str] = None

    player3_name:  Optional[str] = None
    player3_phone: Optional[str] = None
    player3_usn:   Optional[str] = None

    player4_name:  Optional[str] = None
    player4_phone: Optional[str] = None
    player4_usn:   Optional[str] = None

    @field_validator("captain_phone", "player2_phone", "player3_phone", "player4_phone", mode="before")
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        cleaned = re.sub(r"\D", "", str(v))
        if len(cleaned) not in (10, 12):
            raise ValueError("Phone must be 10 digits")
        return cleaned

    @field_validator("captain_usn", "player2_usn", "player3_usn", "player4_usn", mode="before")
    @classmethod
    def uppercase_usn(cls, v):
        return v.strip().upper() if v else v

    @field_validator("semester")
    @classmethod
    def validate_semester(cls, v: str) -> str:
        if v.strip() not in [str(i) for i in range(1, 9)]:
            raise ValueError("Semester must be 1-8")
        return v.strip()


# ─── REGISTRATION RESPONSE ────────────────────────────────────────────────────
class TeamRegistrationResponse(BaseModel):
    success:  bool
    team_id:  str
    message:  str


# ─── TEAM RECORD (returned from DB) ──────────────────────────────────────────
class TeamRecord(BaseModel):
    id:             str
    team_id:        str
    game:           str
    email:          str
    branch:         str
    semester:       str
    captain_name:   str
    captain_phone:  str
    captain_usn:    str
    player2_name:   Optional[str] = None
    player2_phone:  Optional[str] = None
    player2_usn:    Optional[str] = None
    player3_name:   Optional[str] = None
    player3_phone:  Optional[str] = None
    player3_usn:    Optional[str] = None
    player4_name:   Optional[str] = None
    player4_phone:  Optional[str] = None
    player4_usn:    Optional[str] = None
    payment_status: str
    is_verified:    bool
    created_at:     datetime


# ─── ADMIN LOGIN ──────────────────────────────────────────────────────────────
class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    success:      bool
    access_token: str
    token_type:   str = "bearer"
    message:      str


# ─── STATS ───────────────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_registrations: int
    paid_teams:          int
    verified_teams:      int
    bgmi_count:          int
    freefire_count:      int


# ─── PAYMENT VERIFICATION ─────────────────────────────────────────────────────
class VerifyPaymentRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        return re.sub(r"\D", "", v)


class VerifyPaymentResponse(BaseModel):
    success:    bool
    message:    str
    team_id:    Optional[str] = None
    team_name:  Optional[str] = None
    game:       Optional[str] = None


# ─── EVENT COUNT (public) ─────────────────────────────────────────────────────
class EventCountResponse(BaseModel):
    freefire_count: int
    bgmi_count:     int
    hackathon_count: int
    quiz_count:     int
    total:          int


# ─── GENERIC MESSAGE ─────────────────────────────────────────────────────────
class MessageResponse(BaseModel):
    success: bool
    message: str
