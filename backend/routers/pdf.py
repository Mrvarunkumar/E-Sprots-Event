"""
PDF router — generates and downloads team confirmation PDF
GET /download-pdf?teamId=BGMI-0001
"""
import io
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from database import admin_db

router = APIRouter(tags=["PDF"])

# ─── COLOR PALETTE ────────────────────────────────────────────────────────────
DARK_BG      = colors.HexColor("#0D0D0D")
ACCENT_RED   = colors.HexColor("#FF3C00")
ACCENT_GOLD  = colors.HexColor("#FFD700")
CARD_BG      = colors.HexColor("#1A1A1A")
WHITE        = colors.white
LIGHT_GREY   = colors.HexColor("#AAAAAA")
VERIFIED_GRN = colors.HexColor("#00FF88")
PENDING_ORG  = colors.HexColor("#FFA500")


def _build_pdf(team: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Styles ────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "title", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=22, textColor=ACCENT_RED,
        alignment=TA_CENTER, spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "sub", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, textColor=LIGHT_GREY,
        alignment=TA_CENTER, spaceAfter=2,
    )
    heading_style = ParagraphStyle(
        "heading", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=13, textColor=ACCENT_GOLD,
        alignment=TA_LEFT, spaceBefore=8, spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "body", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, textColor=WHITE,
        alignment=TA_LEFT,
    )
    team_id_style = ParagraphStyle(
        "teamid", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=18, textColor=ACCENT_GOLD,
        alignment=TA_CENTER, spaceBefore=6, spaceAfter=6,
    )
    footer_style = ParagraphStyle(
        "footer", parent=styles["Normal"],
        fontName="Helvetica-Oblique", fontSize=8, textColor=LIGHT_GREY,
        alignment=TA_CENTER,
    )

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("⚡ APEX ARENA", title_style))
    story.append(Paragraph("VTU Kalburagi — E-Sports Event", sub_style))
    story.append(Paragraph("Team Registration Confirmation", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_RED, spaceAfter=8))

    # ── Team ID badge ─────────────────────────────────────────────────────────
    story.append(Paragraph(f"TEAM ID: {team['team_id']}", team_id_style))

    # ── Status banner ─────────────────────────────────────────────────────────
    status        = team.get("payment_status", "pending").upper()
    status_color  = VERIFIED_GRN if status == "VERIFIED" else PENDING_ORG
    status_label  = f"Payment Status: {status}"
    status_data   = [[status_label]]
    status_table  = Table(status_data, colWidths=["100%"])
    status_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), CARD_BG),
        ("TEXTCOLOR",   (0, 0), (-1, -1), status_color),
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 11),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",  (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 8))

    # ── Team Info ─────────────────────────────────────────────────────────────
    story.append(Paragraph("TEAM INFORMATION", heading_style))
    info_data = [
        ["Game",     team.get("game", "—"),    "Branch",   team.get("branch", "—")],
        ["Email",    team.get("email", "—"),   "Semester", team.get("semester", "—")],
        ["Registered",
         datetime.fromisoformat(
             team.get("created_at", datetime.now(timezone.utc).isoformat())
             .replace("Z", "+00:00")
         ).strftime("%d %b %Y %I:%M %p"), "", ""],
    ]
    info_table = Table(info_data, colWidths=[35 * mm, 60 * mm, 35 * mm, 40 * mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CARD_BG),
        ("TEXTCOLOR",     (0, 0), (0, -1), ACCENT_RED),
        ("TEXTCOLOR",     (2, 0), (2, -1), ACCENT_RED),
        ("TEXTCOLOR",     (1, 0), (1, -1), WHITE),
        ("TEXTCOLOR",     (3, 0), (3, -1), WHITE),
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",      (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTNAME",      (1, 0), (1, -1), "Helvetica"),
        ("FONTNAME",      (3, 0), (3, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.5, ACCENT_RED),
        ("SPAN",          (1, 2), (3, 2)),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    # ── Players ───────────────────────────────────────────────────────────────
    story.append(Paragraph("SQUAD ROSTER", heading_style))

    players = [
        ("CAPTAIN ★", "captain_name", "captain_phone", "captain_usn"),
        ("PLAYER 2",  "player2_name", "player2_phone", "player2_usn"),
        ("PLAYER 3",  "player3_name", "player3_phone", "player3_usn"),
        ("PLAYER 4",  "player4_name", "player4_phone", "player4_usn"),
    ]

    player_header = ["Role", "Name", "Phone", "USN"]
    player_data   = [player_header]
    for label, name_key, phone_key, usn_key in players:
        n = team.get(name_key) or "—"
        p = team.get(phone_key) or "—"
        u = team.get(usn_key)  or "—"
        player_data.append([label, n, p, u])

    player_table = Table(
        player_data,
        colWidths=[30 * mm, 55 * mm, 40 * mm, 45 * mm],
    )
    player_table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND",    (0, 0), (-1, 0), ACCENT_RED),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN",         (0, 0), (-1, 0), "CENTER"),
        # Data rows alternating
        ("BACKGROUND",    (0, 1), (-1, 1), CARD_BG),
        ("BACKGROUND",    (0, 2), (-1, 2), colors.HexColor("#222222")),
        ("BACKGROUND",    (0, 3), (-1, 3), CARD_BG),
        ("BACKGROUND",    (0, 4), (-1, 4), colors.HexColor("#222222")),
        ("TEXTCOLOR",     (0, 1), (0, -1), ACCENT_GOLD),
        ("TEXTCOLOR",     (1, 1), (-1, -1), WHITE),
        ("FONTNAME",      (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",      (1, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("GRID",          (0, 0), (-1, -1), 0.5, ACCENT_RED),
    ]))
    story.append(player_table)
    story.append(Spacer(1, 14))

    # ── Important note ────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=ACCENT_RED, spaceAfter=6))
    story.append(Paragraph(
        "⚠ Please carry this confirmation on the day of the event along with a valid college ID card.",
        ParagraphStyle("note", parent=body_style, textColor=ACCENT_GOLD, fontSize=9),
    ))
    story.append(Spacer(1, 20))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GREY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %b %Y %I:%M %p')} | "
        "Apex Arena — VTU Kalburagi E-Sports Event",
        footer_style,
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ─── GET /download-pdf ────────────────────────────────────────────────────────
@router.get("/download-pdf", summary="Download team confirmation PDF (public with teamId)")
async def download_pdf(teamId: str = Query(..., description="Team ID e.g. BGMI-0001")):
    """
    Public endpoint — called from success.html after registration.
    Generates a stylish PDF confirmation for the team.
    """
    try:
        result = (
            admin_db.table("teams").select("*").eq("team_id", teamId).execute()
        )
    except Exception as e:
        raise HTTPException(500, detail=f"Database error: {e}")

    if not result.data:
        raise HTTPException(404, detail=f"Team '{teamId}' not found")

    team     = result.data[0]
    pdf_data = _build_pdf(team)
    filename = f"Apex_Arena_{teamId.replace('-', '_')}_Confirmation.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_data),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
