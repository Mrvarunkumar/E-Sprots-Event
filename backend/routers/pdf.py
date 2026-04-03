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
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from database import admin_db

router = APIRouter(tags=["PDF"])

# ─── COLOR PALETTE (FORMAL) ───────────────────────────────────────────────────
DOC_BG       = colors.white
TEXT_MAIN    = colors.black
TEXT_MUTED   = colors.HexColor("#555555")
BORDER_COLOR = colors.HexColor("#000000")
CARD_BG_1    = colors.white
CARD_BG_2    = colors.HexColor("#F5F5F5")
HEADER_BG    = colors.HexColor("#EFEFEF")


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
        fontName="Helvetica-Bold", fontSize=16, textColor=TEXT_MAIN,
        alignment=TA_CENTER, spaceAfter=14, spaceBefore=10,
    )
    heading_style = ParagraphStyle(
        "heading", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=11, textColor=TEXT_MAIN,
        alignment=TA_LEFT, spaceBefore=8, spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "body", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, textColor=TEXT_MAIN,
        alignment=TA_LEFT, leading=14,
    )
    right_align_style = ParagraphStyle(
        "right_align", parent=body_style, alignment=TA_RIGHT,
    )
    footer_style = ParagraphStyle(
        "footer", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9, textColor=TEXT_MUTED,
        alignment=TA_CENTER,
    )

    # ── Official Header ───────────────────────────────────────────────────────
    raw_date = team.get("created_at")
    if not raw_date:
        raw_date = datetime.now(timezone.utc).isoformat()
    reg_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).strftime("%d %b %Y")
    header_data = [
        [
            Paragraph("<b>APEX ARENA E-SPORTS</b><br/>VTU Kalburagi Events Committee<br/>Kalburagi, Karnataka", body_style),
            Paragraph(f"<b>Date of Issue:</b> {datetime.now().strftime('%d %b %Y')}<br/><b>Registration Date:</b> {reg_date}<br/><b>Reference No:</b> {team['team_id']}", right_align_style)
        ]
    ]
    header_table = Table(header_data, colWidths=["50%", "50%"])
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=BORDER_COLOR, spaceBefore=12, spaceAfter=8))

    # ── Title ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("OFFICIAL REGISTRATION ACKNOWLEDGEMENT", title_style))

    # ── Intro Paragraph ───────────────────────────────────────────────────────
    intro_text = f"This document serves as the official confirmation of registration for the Apex Arena E-Sports Tournament. The team has successfully registered under the identifier <b>{team['team_id']}</b>."
    story.append(Paragraph(intro_text, body_style))
    story.append(Spacer(1, 12))

    # ── Status banner ─────────────────────────────────────────────────────────
    status = team.get("payment_status", "pending").upper()
    status_data = [[f"PAYMENT STATUS: {status}"]]
    status_table = Table(status_data, colWidths=["100%"])
    status_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), HEADER_BG),
        ("TEXTCOLOR",     (0, 0), (-1, -1), TEXT_MAIN),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID",          (0, 0), (-1, -1), 1, BORDER_COLOR),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 14))

    # ── Team Info ─────────────────────────────────────────────────────────────
    story.append(Paragraph("TEAM PARTICULARS", heading_style))
    info_data = [
        ["Event Category", team.get("game", "—"), "College Branch", team.get("branch", "—")],
        ["Contact Email", team.get("email", "—"), "Semester", team.get("semester", "—")],
    ]
    info_table = Table(info_data, colWidths=[35 * mm, 60 * mm, 35 * mm, 40 * mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CARD_BG_1),
        ("TEXTCOLOR",     (0, 0), (-1, -1), TEXT_MAIN),
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",      (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTNAME",      (1, 0), (1, -1), "Helvetica"),
        ("FONTNAME",      (3, 0), (3, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 1, BORDER_COLOR),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))

    # ── Players ───────────────────────────────────────────────────────────────
    story.append(Paragraph("REGISTERED SQUAD MEMBERS", heading_style))

    players = [
        ("Captain", "captain_name", "captain_phone", "captain_usn"),
        ("Player 2",  "player2_name", "player2_phone", "player2_usn"),
        ("Player 3",  "player3_name", "player3_phone", "player3_usn"),
        ("Player 4",  "player4_name", "player4_phone", "player4_usn"),
    ]

    player_header = ["Designation", "Full Name", "Contact", "USN"]
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
        ("BACKGROUND",    (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0), TEXT_MAIN),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN",         (0, 0), (-1, 0), "CENTER"),
        ("BACKGROUND",    (0, 1), (-1, -1), CARD_BG_1),
        ("TEXTCOLOR",     (0, 1), (-1, -1), TEXT_MAIN),
        ("FONTNAME",      (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",      (1, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9.5),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID",          (0, 0), (-1, -1), 1, BORDER_COLOR),
    ]))
    story.append(player_table)
    story.append(Spacer(1, 40))

    # ── Signatory ─────────────────────────────────────────────────────────────
    sig_data = [
        [
            Paragraph("<b>Participant Signature</b><br/><br/><br/>_______________________", body_style),
            Paragraph("<b>Authorized Signatory</b><br/><br/><br/>_______________________<br/>Apex Arena Committee", right_align_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=["50%", "50%"])
    story.append(sig_table)
    story.append(Spacer(1, 30))

    # ── Important note ────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceAfter=8))
    story.append(Paragraph(
        "<b>Note:</b> This is a digitally generated document. Please retain a printed copy of this acknowledgement and present it alongside a valid institutional ID card at the venue.",
        ParagraphStyle("note", parent=body_style, textColor=TEXT_MAIN, fontSize=8.5, leading=12),
    ))
    story.append(Spacer(1, 15))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Paragraph(
        f"Document generated on {datetime.now().strftime('%d %b %Y %H:%M')} — apex-arena.events",
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
