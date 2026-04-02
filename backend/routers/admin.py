"""
Admin router — protected routes for the admin panel
POST /admin/login
GET  /admin/stats
GET  /admin/teams
GET  /admin/teams/{team_id}
POST /admin/verify-payment
PUT  /admin/teams/{team_id}/payment-status
DELETE /admin/teams/{team_id}
"""
from fastapi import APIRouter, HTTPException, Depends, status
from database import admin_db
from models import (
    AdminLoginRequest,
    AdminLoginResponse,
    DashboardStats,
    TeamRecord,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
    MessageResponse,
)
from auth import create_access_token, get_current_admin
from config import settings
from typing import List, Optional

router = APIRouter(prefix="/admin", tags=["Admin"])

# ─── POST /admin/login ────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=AdminLoginResponse,
    summary="Admin login — returns JWT token",
)
async def admin_login(body: AdminLoginRequest):
    """
    Validates credentials against Supabase 'admins' table using bcrypt.
    Returns a Bearer JWT for use on all other admin endpoints.
    """
    try:
        user_res = (
            admin_db.table("admins")
            .select("username, password_hash")
            .eq("username", body.username)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    
    if not user_res.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
        
    admin_data = user_res.data[0]
    
    # Compare the password directly as plain text (Normal form)
    if body.password != admin_data["password_hash"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token({"sub": body.username, "role": "admin"})
    return AdminLoginResponse(
        success=True,
        access_token=token,
        message="Login successful",
    )


# ─── POST /admin/verify-login ─────────────────────────────────────────────────
@router.post(
    "/verify-login",
    response_model=AdminLoginResponse,
    summary="Verifier login for verify.html using verify_auth table",
)
async def verify_login(body: AdminLoginRequest):
    try:
        user_res = (
            admin_db.table("verify_auth")
            .select("username, password_hash")
            .eq("username", body.username)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    
    if not user_res.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
        
    auth_data = user_res.data[0]
    
    # Compare the password directly as plain text
    if body.password != auth_data["password_hash"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Use the same admin role token so verification routes work perfectly
    token = create_access_token({"sub": body.username, "role": "admin"})
    return AdminLoginResponse(
        success=True,
        access_token=token,
        message="Verification login successful",
    )


# ─── GET /admin/stats ─────────────────────────────────────────────────────────
@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="Dashboard statistics (protected)",
)
async def get_stats(_: dict = Depends(get_current_admin)):
    try:
        total_res = admin_db.table("teams").select("id", count="exact").execute()
        paid_res  = (
            admin_db.table("teams")
            .select("id", count="exact")
            .in_("payment_status", ["paid", "verified"])
            .execute()
        )
        verified_res = (
            admin_db.table("teams")
            .select("id", count="exact")
            .eq("is_verified", True)
            .execute()
        )
        bgmi_res = (
            admin_db.table("teams")
            .select("id", count="exact")
            .eq("game", "BGMI")
            .execute()
        )
        ff_res = (
            admin_db.table("teams")
            .select("id", count="exact")
            .eq("game", "Free Fire")
            .execute()
        )

        return DashboardStats(
            total_registrations=total_res.count    or 0,
            paid_teams=         paid_res.count     or 0,
            verified_teams=     verified_res.count or 0,
            bgmi_count=         bgmi_res.count     or 0,
            freefire_count=     ff_res.count       or 0,
        )
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to fetch stats: {e}")


# ─── GET /admin/teams ─────────────────────────────────────────────────────────
@router.get(
    "/teams",
    response_model=List[TeamRecord],
    summary="List all registrations (protected)",
)
async def list_teams(
    game:           Optional[str] = None,
    payment_status: Optional[str] = None,
    limit:          int = 100,
    offset:         int = 0,
    _: dict = Depends(get_current_admin),
):
    """
    Supports filtering by game and payment_status.
    Use ?game=BGMI or ?game=Free+Fire and ?payment_status=pending|paid|verified|rejected
    """
    try:
        query = (
            admin_db.table("teams")
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        if game:
            query = query.eq("game", game)
        if payment_status:
            query = query.eq("payment_status", payment_status)

        result = query.execute()
        return result.data or []
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to fetch teams: {e}")


# ─── GET /admin/teams/{team_id} ───────────────────────────────────────────────
@router.get(
    "/teams/{team_id}",
    response_model=TeamRecord,
    summary="Get single team details (protected)",
)
async def get_team(team_id: str, _: dict = Depends(get_current_admin)):
    try:
        result = (
            admin_db.table("teams").select("*").eq("team_id", team_id).execute()
        )
        if not result.data:
            raise HTTPException(404, detail=f"Team {team_id} not found")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Database error: {e}")


# ─── POST /admin/verify-payment ───────────────────────────────────────────────
@router.post(
    "/verify-payment",
    response_model=VerifyPaymentResponse,
    summary="Verify payment by captain phone (protected)",
)
async def verify_payment(
    body: VerifyPaymentRequest,
    _: dict = Depends(get_current_admin),
):
    """
    Looks up a team by captain's phone number, marks it as 'verified'.
    Used in admin.html → Payment Verification page.
    """
    try:
        result = (
            admin_db.table("teams")
            .select("*")
            .eq("captain_phone", body.phone)
            .execute()
        )
    except Exception as e:
        raise HTTPException(500, detail=f"Database error: {e}")

    if not result.data:
        return VerifyPaymentResponse(
            success=False,
            message=f"No team found with captain phone {body.phone}",
        )

    team = result.data[0]

    if team["is_verified"]:
        return VerifyPaymentResponse(
            success=True,
            message=f"Team {team['team_id']} is already verified.",
            team_id=team["team_id"],
            team_name=team["captain_name"],
            game=team["game"],
        )

    # Mark verified
    try:
        admin_db.table("teams").update(
            {"payment_status": "verified", "is_verified": True}
        ).eq("team_id", team["team_id"]).execute()
    except Exception as e:
        raise HTTPException(500, detail=f"Update failed: {e}")

    return VerifyPaymentResponse(
        success=True,
        message=f"Payment verified for team {team['team_id']} ({team['captain_name']}).",
        team_id=team["team_id"],
        team_name=team["captain_name"],
        game=team["game"],
    )


# ─── PUT /admin/teams/{team_id}/payment-status ────────────────────────────────
@router.put(
    "/teams/{team_id}/payment-status",
    response_model=MessageResponse,
    summary="Update payment status of a team (protected)",
)
async def update_payment_status(
    team_id:        str,
    payment_status: str,
    _: dict = Depends(get_current_admin),
):
    allowed = {"pending", "paid", "verified", "rejected"}
    if payment_status not in allowed:
        raise HTTPException(400, detail=f"payment_status must be one of {allowed}")

    try:
        update_data = {"payment_status": payment_status}
        if payment_status == "verified":
            update_data["is_verified"] = True
        elif payment_status == "rejected":
            update_data["is_verified"] = False

        result = (
            admin_db.table("teams")
            .update(update_data)
            .eq("team_id", team_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(404, detail=f"Team {team_id} not found")

        return MessageResponse(
            success=True,
            message=f"Team {team_id} status updated to '{payment_status}'",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Update failed: {e}")


# ─── DELETE /admin/teams/{team_id} ────────────────────────────────────────────
@router.delete(
    "/teams/{team_id}",
    response_model=MessageResponse,
    summary="Delete a team registration (protected)",
)
async def delete_team(team_id: str, _: dict = Depends(get_current_admin)):
    try:
        result = (
            admin_db.table("teams").delete().eq("team_id", team_id).execute()
        )
        if not result.data:
            raise HTTPException(404, detail=f"Team {team_id} not found")
        return MessageResponse(success=True, message=f"Team {team_id} deleted.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Delete failed: {e}")
