"""Unit and regression tests for Yafa-UI dashboard components and design rules."""

import pytest

from aircraft_pm.yafa_ui import (
    LUCIDE_PATHS,
    YAFA_TOKENS,
    get_lucide_svg,
    render_yafa_brand_mark,
    render_yafa_callout,
    render_yafa_kpi_card,
    render_yafa_page_header,
    render_yafa_status_dot,
)


def test_yafa_tokens_integrity():
    """Verify Yafa-UI token values match the design system specification."""
    assert YAFA_TOKENS["canvas"] == "#f8fafd"
    assert YAFA_TOKENS["surface"] == "#ffffff"
    assert YAFA_TOKENS["border_main"] == "#dadce0"
    assert YAFA_TOKENS["border_divider"] == "#e8eaed"

    # Multi-color analytical palette
    assert YAFA_TOKENS["cyan"]["strong"] == "#0891b2"
    assert YAFA_TOKENS["cyan"]["light"] == "#67e8f9"
    assert YAFA_TOKENS["blue"]["strong"] == "#2563eb"
    assert YAFA_TOKENS["green"]["strong"] == "#059669"
    assert YAFA_TOKENS["violet"]["strong"] == "#7c3aed"
    assert YAFA_TOKENS["pink"]["strong"] == "#db2777"


def test_render_yafa_status_dot_anti_capsule():
    """Verify Yafa-UI anti-capsule invariant: statuses must use 6px dots and plain text."""
    crit_html = render_yafa_status_dot("Critical")
    adv_html = render_yafa_status_dot("Advisory")
    hlth_html = render_yafa_status_dot("Healthy")

    for html, color in [(crit_html, "#dc2626"), (adv_html, "#d97706"), (hlth_html, "#059669")]:
        # Must contain 6px dot
        assert "width: 6px; height: 6px; border-radius: 50%" in html
        assert color in html
        # Anti-bubble rule: must NOT be enclosed in a capsule/pill badge
        assert "badge" not in html
        assert "padding: 4px 10px" not in html
        assert "border-radius: 9999px" not in html


def test_render_yafa_kpi_card_anatomy():
    """Verify Yafa-UI KPI card anatomy: top rule, dotted underline, quiet divider, NO decorative icon."""
    card = render_yafa_kpi_card(
        title="Fleet Mean RUL",
        value="84.2",
        accent_family="cyan",
        tooltip_desc="Average expected remaining cycles across all active monitored engines",
        delta_text="Min: 12.0 cycles",
        delta_type="neutral",
    )

    # 1. 3px top accent strip
    assert "border-top: 3px solid #67e8f9" in card
    # 2. White surface with 1px border and 8px radius
    assert "background: #ffffff" in card
    assert "border: 1px solid #dadce0" in card
    assert "border-radius: 8px" in card
    # 3. Dotted underline for metric description affordance
    assert "border-bottom: 1px dotted #8792a2" in card
    # 4. Quiet divider
    assert "border-bottom: 1px solid #e8eaed" in card
    # 5. Primary value
    assert "84.2" in card
    # 6. Anti-pattern check: NO decorative upper-right icon tile
    assert "icon-tile" not in card
    assert "width: 36px; height: 36px; background" not in card


def test_render_yafa_page_header_anatomy():
    """Verify Yafa-UI page header anatomy: 6x22px vertical bar, 36px icon tile, uppercase title."""
    header = render_yafa_page_header(
        title="Fleet Command Center",
        subtitle="Global prognostic health monitoring across active commercial turbofans",
        route_family="cyan",
        icon_name="layout-dashboard",
        badge_label="NASA C-MAPSS FD001",
    )

    assert "width: 6px; height: 22px; background-color: #0891b2" in header
    assert "width: 36px; height: 36px; background-color: #ecfeff" in header
    assert "FLEET COMMAND CENTER" in header
    assert "NASA C-MAPSS FD001" in header


def test_lucide_svg_generation():
    """Verify Lucide SVG vector generator outputs valid SVGs."""
    for icon_name in LUCIDE_PATHS:
        svg = get_lucide_svg(icon_name, size=20, color="#2563eb")
        assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"')
        assert 'width="20" height="20"' in svg
        assert 'stroke="#2563eb"' in svg
        assert svg.endswith("</svg>")


def test_render_yafa_brand_mark():
    """Verify official Yafa-UI mark contains 4 analytical accent rectangles."""
    mark = render_yafa_brand_mark(size=24)
    assert "#67e8f9" in mark  # cyan
    assert "#86efac" in mark  # green
    assert "#c4b5fd" in mark  # violet
    assert "#f9a8d4" in mark  # pink
