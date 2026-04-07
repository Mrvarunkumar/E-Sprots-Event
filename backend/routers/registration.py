"""
Registration router — handles team sign-ups
POST /register
GET  /counts   (public — for eventcount.html)
"""
import re
from fastapi import APIRouter, HTTPException, status
from database import db_client, admin_db
from models import (
    TeamRegistrationRequest,
    TeamRegistrationResponse,
    EventCountResponse,
)

router = APIRouter(prefix="/api", tags=["Registration"])


# ─── HELPER: generate human-readable team ID ─────────────────────────────────
def _generate_team_id(game: str) -> str:
    """
    Query current count from DB and produce IDs like BGMI-0012, FF-0003.
    Uses the count of existing teams + 1 as the suffix.
    """
    if game == "BGMI":
        prefix = "BGMI"
    elif game == "Free Fire":
        prefix = "FF"
    elif game == "Hackathon":
        prefix = "HCK"
    else:
        prefix = "QZ"
    try:
        result = (
            admin_db.table("teams")
            .select("id", count="exact")
            .eq("game", game)
            .execute()
        )
        count = result.count if result.count is not None else 0
        return f"{prefix}-{str(count + 1).zfill(4)}"
    except Exception:
        # Fallback with timestamp
        from datetime import datetime
        ts = datetime.now().strftime("%H%M%S")
        return f"{prefix}-{ts}"


# ─── POST /register ───────────────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=TeamRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new esports team",
)
async def register_team(payload: TeamRegistrationRequest):
    """
    Accepts a full team registration (captain + up to 3 players).
    Saves to Supabase and returns a unique team_id.
    """
    # Prevent duplicate captain phone
    existing = (
        admin_db.table("teams")
        .select("team_id")
        .eq("captain_phone", payload.captain_phone)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A team with captain phone {payload.captain_phone} is already registered.",
        )

    team_id = _generate_team_id(payload.game)

    record = {
        "team_id":        team_id,
        "game":           payload.game,
        "email":          payload.email,
        "branch":         payload.branch,
        "semester":       payload.semester,
        "captain_name":   payload.captain_name,
        "captain_phone":  payload.captain_phone,
        "captain_usn":    payload.captain_usn,
        "player2_name":   payload.player2_name,
        "player2_phone":  payload.player2_phone,
        "player2_usn":    payload.player2_usn,
        "player3_name":   payload.player3_name,
        "player3_phone":  payload.player3_phone,
        "player3_usn":    payload.player3_usn,
        "player4_name":   payload.player4_name,
        "player4_phone":  payload.player4_phone,
        "player4_usn":    payload.player4_usn,
        "payment_status": "pending",
        "is_verified":    False,
    }

    try:
        result = admin_db.table("teams").insert(record).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed — no data returned from database.",
        )

    return TeamRegistrationResponse(
        success=True,
        team_id=team_id,
        message=f"Team registered successfully! Your Team ID is {team_id}. "
                f"Please complete payment to confirm your slot.",
    )


# ─── GET /counts ──────────────────────────────────────────────────────────────
@router.get(
    "/counts",
    response_model=EventCountResponse,
    summary="Get registration counts per game (public)",
)
async def get_event_counts():
    """
    Public endpoint consumed by eventcount.html.
    Returns the number of registered teams per game.
    """
    try:
        ff_res = (
            db_client.table("teams")
            .select("id", count="exact")
            .eq("game", "Free Fire")
            .execute()
        )
        bgmi_res = (
            db_client.table("teams")
            .select("id", count="exact")
            .eq("game", "BGMI")
            .execute()
        )
        hackathon_res = (
            db_client.table("teams")
            .select("id", count="exact")
            .eq("game", "Hackathon")
            .execute()
        )
        quiz_res = (
            db_client.table("teams")
            .select("id", count="exact")
            .eq("game", "Quiz")
            .execute()
        )
        ff_count   = ff_res.count   or 0
        bgmi_count = bgmi_res.count or 0
        hackathon_count = hackathon_res.count or 0
        quiz_count = quiz_res.count or 0

        return EventCountResponse(
            freefire_count=ff_count,
            bgmi_count=bgmi_count,
            hackathon_count=hackathon_count,
            quiz_count=quiz_count,
            total=ff_count + bgmi_count + hackathon_count + quiz_count,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not fetch counts: {str(e)}",
        )
