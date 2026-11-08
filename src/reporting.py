"""
InfraMiner AI - Production PDF Decision & Resilience Report Generator

Generates comprehensive, publication-grade executive PDF reports directly
from live InfraMinerState runtime outputs using ReportLab.
Applies human-readable plain language headings with technical terms in parentheses,
strict viability threshold labeling, dynamic fallback counts, and consistent logistics values.
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _safe_str(val: Any, default: str = "Not available in verified source") -> str:
    """Return clean string or default if None/empty."""
    if val is None or val == "" or val == "None":
        return default
    return str(val)


def generate_pdf_report(
    state: dict,
    output_path: str | Path | None = None,
) -> bytes:
    """Generate a comprehensive PDF decision & resilience report from live state.

    Parameters
    ----------
    state : dict
        The InfraMinerState dictionary resulting from live pipeline execution.
    output_path : str | Path | None
        Optional file path to write the PDF to disk.

    Returns
    -------
    bytes
        The raw PDF bytes, suitable for Streamlit st.download_button.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F2942"),
        spaceAfter=3,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334D6E"),
        spaceAfter=10,
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0F2942"),
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor("#1A5F7A"),
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=11,
        textColor=colors.HexColor("#2C3E50"),
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor("#2C3E50"),
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor("#1A252F"),
    )
    table_cell_red = ParagraphStyle(
        "TableCellRed",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor("#C53030"),
    )
    table_cell_green = ParagraphStyle(
        "TableCellGreen",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor("#22543D"),
    )
    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
    )
    alert_style = ParagraphStyle(
        "AlertText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#856404"),
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("INFRAMINER AI — EXECUTIVE DECISION & RESILIENCE REPORT", title_style))
    story.append(
        Paragraph(
            f"Multi-Agent Sustainable Resource Sourcing and Supply Chain Reliability Assessment | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0F2942"), spaceAfter=8))

    # 1. Project Information
    story.append(Paragraph("1. Project Information & Scope", h1_style))
    p_name = _safe_str(state.get("project_name"))
    p_type = _safe_str(state.get("project_type"))
    loc = state.get("project_location") or {}
    lat = loc.get("lat")
    lng = loc.get("lng")
    loc_str = f"Lat: {lat}, Lng: {lng}" if lat is not None and lng is not None else "Not explicitly documented in source"
    p_timeline = _safe_str(state.get("project_timeline"))
    p_scope = _safe_str(state.get("project_scope"))

    proj_info_data = [
        [Paragraph("Project Name", table_cell_bold), Paragraph(p_name, table_cell)],
        [Paragraph("Project Type", table_cell_bold), Paragraph(p_type, table_cell)],
        [Paragraph("Location Coordinates", table_cell_bold), Paragraph(loc_str, table_cell)],
        [Paragraph("Timeline / Phases", table_cell_bold), Paragraph(p_timeline, table_cell)],
        [Paragraph("Project Scope Summary", table_cell_bold), Paragraph(p_scope, table_cell)],
    ]
    t_proj = Table(proj_info_data, colWidths=[120, 420])
    t_proj.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ])
    )
    story.append(t_proj)
    story.append(Spacer(1, 8))

    # Constraints
    constraints = state.get("project_constraints", [])
    if constraints:
        story.append(Paragraph("Documented Project Constraints:", h2_style))
        const_items = [[Paragraph(f"• {c}", body_style)] for c in constraints[:8]]
        t_const = Table(const_items, colWidths=[540])
        t_const.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
        story.append(t_const)
        story.append(Spacer(1, 8))

    # 2. Material Requirements
    materials = state.get("materials", [])
    story.append(Paragraph(f"2. Extracted Material Requirements ({len(materials)} Items Identified)", h1_style))
    if materials:
        mat_table_data = [
            [
                Paragraph("Material Name", table_header),
                Paragraph("Required Quantity", table_header),
                Paragraph("Unit", table_header),
                Paragraph("Specification / Grade", table_header),
                Paragraph("Construction Purpose", table_header),
            ]
        ]
        for m in materials:
            qty_val = m.get("quantity")
            qty_str = f"{qty_val:,.1f}" if isinstance(qty_val, (int, float)) else "Not available in source"
            mat_table_data.append([
                Paragraph(_safe_str(m.get("material_name")), table_cell_bold),
                Paragraph(qty_str, table_cell),
                Paragraph(_safe_str(m.get("unit")), table_cell),
                Paragraph(_safe_str(m.get("specification")), table_cell),
                Paragraph(_safe_str(m.get("purpose")), table_cell),
            ])
        t_mat = Table(mat_table_data, colWidths=[140, 75, 65, 120, 140])
        t_mat.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F2942")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ])
        )
        story.append(t_mat)
    else:
        story.append(Paragraph("No material requirements identified from project documents.", body_style))
    story.append(Spacer(1, 10))

    # 3. Source Discovery & Multimodal Delivery (Logistics Consistency Fix)
    sources = state.get("sources", [])
    routes = state.get("routes", [])
    route_by_sid = {str(r.get("source_id", "")).strip(): r for r in routes if r.get("source_id")}

    story.append(Paragraph(f"3. Candidate Sources & Multimodal Delivery ({len(sources)} Matches Evaluated)", h1_style))
    if sources:
        src_table_data = [
            [
                Paragraph("Source ID", table_header),
                Paragraph("Source Name", table_header),
                Paragraph("Material", table_header),
                Paragraph("Origin / Location", table_header),
                Paragraph("Lead Distance", table_header),
                Paragraph("Transport Mode", table_header),
            ]
        ]
        # Display representative candidate sources (up to 14)
        for s in sources[:14]:
            sid = str(s.get("source_id", "N/A")).strip()
            route_item = route_by_sid.get(sid, {})
            dist = s.get("distance_km") or route_item.get("distance_km")
            dist_str = f"{dist:.1f} km" if isinstance(dist, (int, float)) else "Not available in verified source"
            tmode = s.get("transport_mode") or route_item.get("transport_mode") or "road"
            src_table_data.append([
                Paragraph(sid, table_cell_bold),
                Paragraph(_safe_str(s.get("source_name")), table_cell),
                Paragraph(_safe_str(s.get("material_name")), table_cell),
                Paragraph(_safe_str(s.get("location")), table_cell),
                Paragraph(dist_str, table_cell),
                Paragraph(_safe_str(tmode), table_cell),
            ])
        t_src = Table(src_table_data, colWidths=[65, 140, 120, 105, 55, 55])
        t_src.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A5F7A")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ])
        )
        story.append(t_src)
    story.append(Spacer(1, 10))

    # 4. Multi-Criteria Assessment (Cost, Environment, Supply Reliability)
    story.append(Paragraph("4. Cost, Environmental & Supply Reliability Assessments", h1_style))
    cost_count = len(state.get("cost_estimates", []))
    env_count = len(state.get("environmental_assessments", []))
    res_count = len(state.get("resilience_assessments", []))
    assess_summary = (
        f"• <b>Cost Assessment:</b> {cost_count} candidate costings evaluated. Commercial purchase prices are classified as verified or calculated where documented; unstated commercial prices are flagged with neutral baselines to prevent fabrication.<br/>"
        f"• <b>Environmental Footprint:</b> {env_count} evaluations covering quarry extraction footprint, marine dredging regulations, and overland vs maritime haulage. Where numerical emissions scores are unpublished in public DPR documents, neutral baseline assumptions were applied.<br/>"
        f"• <b>Supply Reliability:</b> {res_count} evaluations factoring multi-quarry redundancy, single-source concessions, and monsoon disruption windows."
    )
    story.append(Paragraph(assess_summary, body_style))
    story.append(Spacer(1, 8))

    # 5. AHP & TOPSIS Decision Dashboard
    dec_res = state.get("decision_results", {})
    ahp = dec_res.get("ahp", {})
    weights = ahp.get("weights", {})
    cr = ahp.get("consistency_ratio", 0.0)
    cr_valid = ahp.get("is_consistent", cr < 0.10)

    story.append(Paragraph("5. Multi-Criteria Decision Framework (AHP-TOPSIS)", h1_style))
    ahp_text = (
        f"<b>Criteria Weights (AHP):</b> Cost = {weights.get('cost', 0.0):.4f} | "
        f"Logistics = {weights.get('logistics', 0.0):.4f} | "
        f"Environmental = {weights.get('environmental', 0.0):.4f} | "
        f"Supply Reliability = {weights.get('resilience', 0.0):.4f}<br/>"
        f"<b>AHP Consistency Ratio (CR):</b> {cr:.4f} ("
        f"{'CONSISTENT (CR < 0.10)' if cr_valid else 'INCONSISTENT (CR >= 0.10)'})"
    )
    story.append(Paragraph(ahp_text, body_style))
    story.append(Spacer(1, 6))

    # TOPSIS Ranking Table (Viability Fix & Logistics Distance Fix)
    ranking = dec_res.get("ranking", [])
    story.append(Paragraph(f"Evaluated Alternatives Ranking ({len(ranking)} Unique Physical Alternatives)", h2_style))
    if ranking:
        rank_table_data = [
            [
                Paragraph("Rank", table_header),
                Paragraph("Source ID", table_header),
                Paragraph("Source Name", table_header),
                Paragraph("Material", table_header),
                Paragraph("Source Score", table_header),
                Paragraph("Lead Distance", table_header),
                Paragraph("Feasibility Status", table_header),
            ]
        ]
        for alt in ranking:
            r_num = alt.get("rank", "N/A")
            sid = alt.get("source_id", "N/A")
            sname = alt.get("source_name", "N/A")
            mat = alt.get("material_name", "N/A")
            score = alt.get("closeness_coefficient", 0.0)

            # Logistics consistency: get actual distance
            dist = alt.get("actual_distance_km") or alt.get("raw_logistics")
            dist_str = f"{dist:.1f} km" if isinstance(dist, (int, float)) else "Not available in verified source"

            # Strict viability threshold: score >= 0.30
            is_feasible = score >= 0.30 and alt.get("is_viable", True)
            viab_label = "FEASIBLE" if is_feasible else "NOT FEASIBLE"
            viab_style = table_cell_green if is_feasible else table_cell_red

            rank_table_data.append([
                Paragraph(str(r_num), table_cell_bold),
                Paragraph(sid, table_cell),
                Paragraph(sname, table_cell),
                Paragraph(mat, table_cell),
                Paragraph(f"{score:.4f}", table_cell_bold),
                Paragraph(dist_str, table_cell),
                Paragraph(viab_label, viab_style),
            ])
        t_rank = Table(rank_table_data, colWidths=[30, 55, 145, 135, 60, 55, 60])
        t_rank.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F2942")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ])
        )
        story.append(t_rank)
    story.append(Spacer(1, 10))

    # 6. Material-Wise Sourcing & Resilience Plan (Dynamic Fallback Count)
    sourcing_plan = dec_res.get("final_sourcing_plan", [])
    story.append(Paragraph("6. Material-Wise Sourcing & Resilience Plan", h1_style))
    if sourcing_plan:
        plan_table_data = [
            [
                Paragraph("Material", table_header),
                Paragraph("Primary Source Under Current Model", table_header),
                Paragraph("Score", table_header),
                Paragraph("Backup Sources", table_header),
                Paragraph("Supply Reliability Status", table_header),
            ]
        ]
        for sp in sourcing_plan:
            mat_name = sp.get("material_name", "N/A")
            p_src = sp.get("primary_source", {})
            p_name_val = p_src.get("source_name", "N/A")
            p_score = p_src.get("closeness_coefficient", 0.0)

            fb_sources = sp.get("fallback_sources", [])
            fb_list = [f"{fb.get('source_name')} ({fb.get('source_id')})" for fb in fb_sources]

            if not sp.get("has_viable_source", True) or "No viable" in p_name_val or p_score < 0.30:
                p_display = Paragraph("NO FEASIBLE SOURCE FOUND", table_cell_red)
                score_str = f"{p_score:.4f}" if p_score > 0 else "0.0000"
                fb_str = "None (No feasible source)"
                res_status = Paragraph("NO FEASIBLE SOURCE", table_cell_red)
            else:
                p_display = Paragraph(f"{p_name_val} ({p_src.get('source_id', '')})", table_cell_bold)
                score_str = f"{p_score:.4f}"
                fb_str = "<br/>• ".join(["• " + f for f in fb_list]) if fb_list else "None (Single-source dependency)"

                if len(fb_list) >= 2:
                    res_status = Paragraph("RESILIENT (High redundancy)", table_cell_green)
                elif len(fb_list) == 1:
                    res_status = Paragraph("LIMITED RELIABILITY (1 backup)", table_cell)
                else:
                    res_status = Paragraph("SINGLE-SOURCE DEPENDENCY", table_cell_red)

            plan_table_data.append([
                Paragraph(mat_name, table_cell_bold),
                p_display,
                Paragraph(score_str, table_cell),
                Paragraph(fb_str, table_cell),
                res_status,
            ])
        t_plan = Table(plan_table_data, colWidths=[120, 140, 45, 145, 90])
        t_plan.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A5F7A")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ])
        )
        story.append(t_plan)
    story.append(Spacer(1, 10))

    # 7. Dynamic Fallback Summary & Narrative
    # Calculate unique fallback count dynamically across sourcing plan
    all_plan_fbs = [fb for sp in sourcing_plan for fb in sp.get("fallback_sources", [])]
    unique_fbs = {fb.get("source_id") or fb.get("source_name") for fb in all_plan_fbs if fb}
    dynamic_fb_count = len(unique_fbs)

    story.append(Paragraph(f"7. Supply Chain Reliability & Disruption Mitigation ({dynamic_fb_count} Unique Backup Sources Identified)", h1_style))
    res_narrative = dec_res.get("resilience_explanation")
    if res_narrative:
        story.append(Paragraph(res_narrative, body_style))
    else:
        story.append(
            Paragraph(
                f"A total of {dynamic_fb_count} unique backup alternative(s) were identified across materials. "
                "These alternatives provide critical operational buffering against supply chain disruptions, "
                "such as seasonal monsoon closures, transport corridor failures, or quarry capacity limits.",
                body_style,
            )
        )
    story.append(Spacer(1, 8))

    # 8. Evidence & Provenance
    story.append(Paragraph("8. Evidence, Provenance & Methodological Audit", h1_style))
    prov_text = (
        "• <b>Project Scope Grounding:</b> Project identity, structural requirements, and material specifications extracted strictly from indexed DPR pages.<br/>"
        "• <b>Quarry & Material Sourcing Provenance:</b> Source names, lead distances, and reserve volumes derived from state mining department surveys, CIDCO/MMRDA regional master plans, and environmental clearance documents.<br/>"
        "• <b>Cost & Commercial Pricing Audit:</b> Documented tariff rates and freight estimates apply standard ministry schedule of rates (SoR). Where commercial purchase unit prices are unpublished in public records, neutral mathematical placeholders prevent numerical fabrication.<br/>"
        "• <b>Feasibility & Viability Threshold Rule:</b> Alternatives achieving TOPSIS closeness coefficient &lt; 0.30 are formally rejected as non-viable to prevent unfeasible procurement commitments."
    )
    story.append(Paragraph(prov_text, body_style))
    story.append(Spacer(1, 8))

    # 9. Disclaimers & Governance Notice
    story.append(Paragraph("9. Operational Limitations & Governance Notice", h1_style))
    disclaimer_text = (
        "<b>NOTICE:</b> InfraMiner AI is an automated multi-criteria decision-support system. Sourcing evaluations tagged as "
        "PROVISIONAL_INDICATIVE reflect constraints in publicly disclosed DPR documentation. Formal competitive bidding, "
        "physical quarry core sampling, and statutory coastal regulatory approvals (CRZ/MoEFCC) are mandatory prior to financial commitment."
    )
    story.append(Paragraph(disclaimer_text, alert_style))

    # Build PDF document
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with out_p.open("wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
