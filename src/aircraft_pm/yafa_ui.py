"""Yafa-UI Analytical Dashboard Components & Design Tokens for AeroGuard.

Implements the Yafa-UI visual system:
- 4-layer shell: white sidebar/top-bar, page identity bar, #f8fafd analytical canvas.
- Multi-color analytical palette (cyan, blue, green, violet, pink, amber).
- Standard KPI card anatomy with 3-4px top accent strip, dotted-underlined description affordance,
  quiet divider, and NO decorative upper-right icon.
- Semantic statuses rendered strictly as 6px dots + plain neutral text (anti-capsule invariant).
- Rectangular anti-bubble geometry (0-8px corners).
- Code-native Lucide SVG icons.
"""

from typing import Dict, Optional


# Yafa-UI Analytical Color Tokens
YAFA_TOKENS = {
    "canvas": "#f8fafd",
    "surface": "#ffffff",
    "border_main": "#dadce0",
    "border_divider": "#e8eaed",
    "border_interactive": "#8792a2",
    "text_strong": "#202124",
    "text_body": "#3c4043",
    "text_muted": "#5f6368",
    "brand_blue": "#2563eb",
    # Route Accent Families (Strong, Light Accent, Soft Tint)
    "cyan": {"strong": "#0891b2", "light": "#67e8f9", "soft": "#ecfeff"},
    "blue": {"strong": "#2563eb", "light": "#5dadec", "soft": "#eff6ff"},
    "green": {"strong": "#059669", "light": "#86efac", "soft": "#ecfdf5"},
    "violet": {"strong": "#7c3aed", "light": "#c4b5fd", "soft": "#f5f3ff"},
    "pink": {"strong": "#db2777", "light": "#f9a8d4", "soft": "#fdf2f8"},
    "amber": {"strong": "#d97706", "light": "#fbbf24", "soft": "#fffbeb"},
    # Semantic States
    "success": {"strong": "#059669", "soft": "#ecfdf5"},
    "warning": {"strong": "#d97706", "soft": "#fffbeb"},
    "danger": {"strong": "#dc2626", "soft": "#fef2f2"},
    "info": {"strong": "#2563eb", "soft": "#eff6ff"},
}

# Lucide SVG Icon Vector Paths (Canonical 24x24 Lucide geometry)
LUCIDE_PATHS: Dict[str, str] = {
    "layout-dashboard": (
        '<rect width="7" height="9" x="3" y="3" rx="1"/>'
        '<rect width="7" height="5" x="14" y="3" rx="1"/>'
        '<rect width="7" height="9" x="14" y="12" rx="1"/>'
        '<rect width="7" height="5" x="3" y="16" rx="1"/>'
    ),
    "activity": (
        '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.48 12H2"/>'
    ),
    "radio": (
        '<path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9"/>'
        '<path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5"/>'
        '<circle cx="12" cy="12" r="2"/>'
        '<path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5"/>'
        '<path d="M19.1 4.9C23 8.8 23 15.1 19.1 19"/>'
    ),
    "layers": (
        '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/>'
        '<path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/>'
        '<path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>'
    ),
    "wrench": (
        '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'
    ),
    "sliders": (
        '<line x1="4" x2="4" y1="21" y2="14"/>'
        '<line x1="4" x2="4" y1="10" y2="3"/>'
        '<line x1="12" x2="12" y1="21" y2="12"/>'
        '<line x1="12" x2="12" y1="8" y2="3"/>'
        '<line x1="20" x2="20" y1="21" y2="16"/>'
        '<line x1="20" x2="20" y1="12" y2="3"/>'
        '<line x1="1" x2="7" y1="14" y2="14"/>'
        '<line x1="9" x2="15" y1="8" y2="8"/>'
        '<line x1="17" x2="23" y1="16" y2="16"/>'
    ),
    "shield-check": (
        '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
        '<path d="m9 12 2 2 4-4"/>'
    ),
    "download": (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="7 10 12 15 17 10"/>'
        '<line x1="12" x2="12" y1="15" y2="3"/>'
    ),
}


def get_lucide_svg(
    name: str,
    size: int = 18,
    color: str = "currentColor",
    stroke_width: float = 2.25,
) -> str:
    """Render a clean, code-native Lucide SVG icon."""
    path = LUCIDE_PATHS.get(name, LUCIDE_PATHS["activity"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true" style="vertical-align: middle; display: inline-block;">{path}</svg>'
    )


def render_yafa_brand_mark(size: int = 24) -> str:
    """Render the official Yafa-UI mark: 4 analytical accent rectangles in LayoutDashboard geometry."""
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
        f'<rect x="3" y="3" width="7" height="9" rx="1.5" fill="#67e8f9"/>'
        f'<rect x="14" y="3" width="7" height="5" rx="1.5" fill="#86efac"/>'
        f'<rect x="14" y="12" width="7" height="9" rx="1.5" fill="#c4b5fd"/>'
        f'<rect x="3" y="16" width="7" height="5" rx="1.5" fill="#f9a8d4"/>'
        f'</svg>'
    )


def render_yafa_page_header(
    title: str,
    subtitle: str,
    route_family: str = "cyan",
    icon_name: str = "layout-dashboard",
    badge_label: Optional[str] = None,
) -> str:
    """Render standard Yafa-UI page identity bar.

    Anatomy:
    - 6x22px vertical accent bar in route strong color
    - 36x36px icon tile (soft route tint, 6px radius)
    - 15-16px uppercase 800 title in #202124
    - Concise subtitle in #5f6368
    - Optional right-aligned context badge
    """
    fam = YAFA_TOKENS.get(route_family, YAFA_TOKENS["cyan"])
    strong_col = fam["strong"]
    soft_col = fam["soft"]
    icon_svg = get_lucide_svg(icon_name, size=18, color=strong_col, stroke_width=2.25)

    badge_html = ""
    if badge_label:
        badge_html = (
            f'<div style="font-size: 11px; font-weight: 700; color: #5f6368; '
            f'background: #ffffff; border: 1px solid #dadce0; border-radius: 4px; padding: 4px 10px; '
            f'text-transform: uppercase; letter-spacing: 0.05em;">{badge_label}</div>'
        )

    return f"""
    <div style="display: flex; align-items: center; justify-content: space-between; gap: 16px;
                padding: 14px 0 18px 0; border-bottom: 1px solid #dadce0; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 6px; height: 22px; background-color: {strong_col}; border-radius: 2px;"></div>
            <div style="width: 36px; height: 36px; background-color: {soft_col}; border-radius: 6px;
                        display: flex; align-items: center; justify-content: center; border: 1px solid {fam['light']}40;">
                {icon_svg}
            </div>
            <div>
                <div style="font-size: 15px; font-weight: 800; color: #202124; text-transform: uppercase;
                            letter-spacing: 0.04em; line-height: 1.2;">
                    {title.upper()}
                </div>
                <div style="font-size: 13px; color: #5f6368; margin-top: 2px; font-weight: 400;">
                    {subtitle}
                </div>
            </div>
        </div>
        {badge_html}
    </div>
    """


def render_yafa_kpi_card(
    title: str,
    value: str,
    accent_family: str = "cyan",
    tooltip_desc: str = "",
    delta_text: str = "",
    delta_type: str = "neutral",
) -> str:
    """Render standard Yafa-UI KPI card.

    Invariants preserved:
    - 3-4px top accent rule from multi-color sequence (cyan, blue, green, violet, pink)
    - Surface is white with 1px #dadce0 border and 8px radius
    - Title has a dotted underline as hover/tap description affordance
    - Quiet divider #e8eaed
    - Primary value (28-32px / 700)
    - Comparison delta has a transparent/white surface with 1px border; color on text only
    - NO decorative upper-right icon tile!
    """
    fam = YAFA_TOKENS.get(accent_family, YAFA_TOKENS["cyan"])
    top_strip = fam["light"]

    # Delta styling: transparent/white surface, 1px neutral border, color ONLY on text
    if delta_type == "success":
        delta_style = "color: #059669; border: 1px solid #dadce0;"
    elif delta_type == "danger":
        delta_style = "color: #dc2626; border: 1px solid #dadce0;"
    elif delta_type == "warning":
        delta_style = "color: #d97706; border: 1px solid #dadce0;"
    else:
        delta_style = "color: #5f6368; border: 1px solid #dadce0;"

    delta_html = ""
    if delta_text:
        delta_html = (
            f'<div style="display: inline-block; font-size: 11.5px; font-weight: 600; '
            f'border-radius: 9999px; padding: 2px 8px; background: transparent; {delta_style} margin-top: 6px;">'
            f'{delta_text}</div>'
        )

    return f"""
    <div style="background: #ffffff; border: 1px solid #dadce0; border-top: 3px solid {top_strip};
                border-radius: 8px; padding: 16px 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); min-height: 120px;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span style="font-size: 13.5px; font-weight: 600; color: #3c4043; border-bottom: 1px dotted #8792a2;
                         cursor: help;" title="{tooltip_desc or title}">
                {title}
            </span>
        </div>
        <div style="border-bottom: 1px solid #e8eaed; margin: 10px 0 10px 0;"></div>
        <div style="font-size: 28px; font-weight: 700; color: #202124; line-height: 1.1; letter-spacing: -0.01em;">
            {value}
        </div>
        {delta_html}
    </div>
    """


def render_yafa_status_dot(status: str) -> str:
    """Render semantic status as a 6px semantic dot + plain text (Anti-capsule invariant).

    Never wrap dot and label in a bordered or tinted capsule pill.
    """
    clean_st = status.strip().capitalize()
    if clean_st.startswith("Crit"):
        color = "#dc2626"
        label = "Critical"
    elif clean_st.startswith("Adv"):
        color = "#d97706"
        label = "Advisory"
    elif clean_st.startswith("Health"):
        color = "#059669"
        label = "Healthy"
    else:
        color = "#5f6368"
        label = status

    return (
        f'<span style="display: inline-flex; align-items: center; gap: 7px; font-weight: 600; '
        f'font-size: 13px; color: {color}; white-space: nowrap;">'
        f'<span style="width: 6px; height: 6px; border-radius: 50%; background-color: {color}; flex-shrink: 0;"></span>'
        f'{label}</span>'
    )


def render_yafa_callout(
    text: str,
    callout_type: str = "info",
    title: Optional[str] = None,
) -> str:
    """Render Yafa-UI analytical callout box with 4px left accent rule and pale tint."""
    if callout_type == "danger":
        accent = "#dc2626"
        bg = "#fef2f2"
        border_col = "#fecaca"
        txt_col = "#991b1b"
    elif callout_type == "warning":
        accent = "#d97706"
        bg = "#fffbeb"
        border_col = "#fde68a"
        txt_col = "#92400e"
    elif callout_type == "success":
        accent = "#059669"
        bg = "#ecfdf5"
        border_col = "#a7f3d0"
        txt_col = "#065f46"
    else:  # info
        accent = "#2563eb"
        bg = "#eff6ff"
        border_col = "#bfdbfe"
        txt_col = "#1e40af"

    title_html = (
        f'<div style="font-weight: 700; font-size: 13px; text-transform: uppercase; '
        f'letter-spacing: 0.04em; margin-bottom: 4px; color: {accent};">{title}</div>'
        if title
        else ""
    )

    return f"""
    <div style="background-color: {bg}; border: 1px solid {border_col}; border-left: 4px solid {accent};
                border-radius: 6px; padding: 12px 16px; margin: 14px 0; font-size: 13px; color: {txt_col}; line-height: 1.45;">
        {title_html}
        {text}
    </div>
    """
