"""
Fin-Health AI dashboard theme (CSS injection).

Call ``load_custom_css()`` immediately after ``st.set_page_config()`` in ``app.py``.
"""

import streamlit as st


def load_custom_css() -> None:
    """
    Inject a modern SaaS analytics theme with light and dark mode polish.
    """
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        color-scheme: light;
        --bg-base: #f5f7fb;
        --bg-canvas: radial-gradient(circle at top left, rgba(35, 99, 235, 0.08), transparent 30%),
                     linear-gradient(180deg, #fbfdff 0%, #f5f7fb 48%, #eef3f8 100%);
        --bg-sidebar: linear-gradient(180deg, #ffffff 0%, #f7fafc 48%, #eef4f7 100%);
        --surface: rgba(255, 255, 255, 0.92);
        --surface-strong: #ffffff;
        --surface-muted: #f8fafc;
        --surface-raised: #ffffff;
        --surface-tint: #eef6f2;
        --border: rgba(15, 23, 42, 0.10);
        --border-strong: rgba(15, 23, 42, 0.16);
        --border-focus: #2563eb;
        --text-primary: #111827;
        --text-secondary: #405166;
        --text-muted: #667085;
        --navy-deep: #0f172a;
        --navy: #1d4ed8;
        --navy-soft: #2563eb;
        --teal: #0f766e;
        --sage: #7aa58b;
        --green: #15803d;
        --amber: #b7791f;
        --red: #b91c1c;
        --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.04);
        --shadow-md: 0 12px 30px rgba(15, 23, 42, 0.08);
        --shadow-lg: 0 22px 60px rgba(15, 23, 42, 0.12);
        --radius: 10px;
        --radius-lg: 14px;
        --font: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
        --gradient-btn: linear-gradient(135deg, #1d4ed8 0%, #0f766e 100%);
        --gradient-btn-hover: linear-gradient(135deg, #2563eb 0%, #0d9488 100%);
    }

    @media (prefers-color-scheme: dark) {
        :root {
            color-scheme: dark;
            --bg-base: #090e17;
            --bg-canvas: radial-gradient(circle at top left, rgba(59, 130, 246, 0.16), transparent 32%),
                         linear-gradient(180deg, #0b1220 0%, #090e17 55%, #0d141c 100%);
            --bg-sidebar: linear-gradient(180deg, #0f172a 0%, #101827 54%, #0c131d 100%);
            --surface: rgba(17, 24, 39, 0.86);
            --surface-strong: #111827;
            --surface-muted: #141d2b;
            --surface-raised: #151f2e;
            --surface-tint: rgba(20, 184, 166, 0.08);
            --border: rgba(226, 232, 240, 0.11);
            --border-strong: rgba(226, 232, 240, 0.18);
            --border-focus: #60a5fa;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --navy-deep: #f8fafc;
            --navy: #60a5fa;
            --navy-soft: #93c5fd;
            --teal: #5eead4;
            --sage: #a7c7b4;
            --green: #86efac;
            --amber: #facc15;
            --red: #fca5a5;
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.25);
            --shadow-md: 0 14px 34px rgba(0, 0, 0, 0.28);
            --shadow-lg: 0 24px 64px rgba(0, 0, 0, 0.38);
            --gradient-btn: linear-gradient(135deg, #2563eb 0%, #0f766e 100%);
            --gradient-btn-hover: linear-gradient(135deg, #3b82f6 0%, #14b8a6 100%);
        }
    }

    html, body,
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"] {
        background: var(--bg-canvas) !important;
        background-color: var(--bg-base) !important;
        color: var(--text-primary) !important;
        font-family: var(--font) !important;
    }

    /* Hide Streamlit chrome — do NOT hide stToolbar (sidebar open/close lives there) */
    #MainMenu, footer,
    [data-testid="stDecoration"] {
        visibility: hidden !important;
        height: 0 !important;
    }

    /* Sidebar collapse / expand control — must stay visible */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stHeader"] [data-testid="stToolbar"] {
        visibility: visible !important;
        height: auto !important;
        opacity: 1 !important;
        display: flex !important;
        z-index: 999999 !important;
    }

    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="collapsedControl"] button {
        color: var(--navy-deep) !important;
        background-color: #FFFFFF !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1440px !important;
        padding: 2.15rem 2.75rem 3.5rem !important;
    }

    [data-testid="stVerticalBlock"] {
        gap: 1rem !important;
    }

    [data-testid="stMainBlockContainer"] > div {
        animation: fh-fade-up 420ms ease both;
    }

    div[data-testid="column"] {
        min-width: 0 !important;
    }

    [data-testid="stSidebar"] {
        background: var(--bg-sidebar) !important;
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border-strong) !important;
        box-shadow: 12px 0 34px rgba(15, 23, 42, 0.08) !important;
        min-width: 18rem !important;
    }

    [data-testid="stSidebar"][aria-expanded="true"],
    [data-testid="stSidebar"][data-collapsed="false"] {
        transform: none !important;
        visibility: visible !important;
    }

    [data-testid="stSidebarContent"] {
        padding: 1.25rem 1.05rem 2rem !important;
    }

    [data-testid="stSidebar"] * {
        font-family: var(--font) !important;
        color: var(--text-primary) !important;
    }

    [data-testid="stSidebarContent"] h1,
    [data-testid="stSidebarContent"] h2,
    [data-testid="stSidebarContent"] h3 {
        color: var(--navy-deep) !important;
        font-size: 0.92rem !important;
        font-weight: 750 !important;
        letter-spacing: 0.01em !important;
    }

    [data-testid="stSidebarContent"] hr {
        border-color: var(--border) !important;
        margin: 1rem 0 !important;
    }

    [data-testid="stSidebar"] [data-testid="stForm"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow-sm) !important;
        padding: 0.85rem 0.65rem !important;
    }

    [data-testid="stSidebar"] [data-testid="stAlert"] {
        border-radius: var(--radius) !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font) !important;
        font-weight: 760 !important;
        color: var(--navy-deep) !important;
        letter-spacing: 0 !important;
        line-height: 1.18 !important;
    }

    h1 {
        font-size: clamp(2rem, 3.2vw, 3.15rem) !important;
        margin: 0.1rem 0 0.15rem !important;
    }

    h2, h3 {
        margin-top: 0.55rem !important;
    }

    p, li, span, label, div {
        font-family: var(--font) !important;
        color: var(--text-primary) !important;
    }

    [data-testid="stIconMaterial"],
    [data-testid="stIconMaterial"] *,
    .material-icons,
    .material-symbols-rounded,
    .material-symbols-outlined {
        font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
        font-weight: normal !important;
        font-style: normal !important;
        letter-spacing: normal !important;
        line-height: 1 !important;
        text-transform: none !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-feature-settings: "liga" !important;
        -webkit-font-smoothing: antialiased !important;
        font-feature-settings: "liga" !important;
    }

    [data-testid="stCaptionContainer"] p {
        color: var(--text-muted) !important;
        font-size: 0.82rem !important;
        line-height: 1.55 !important;
    }

    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li {
        line-height: 1.65 !important;
    }

    [data-testid="stMarkdownContainer"] strong {
        color: var(--navy-deep) !important;
        font-weight: 700 !important;
    }

    .fh-hero {
        background:
            linear-gradient(135deg, rgba(29, 78, 216, 0.10), rgba(15, 118, 110, 0.10)),
            var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-md);
        padding: clamp(1.15rem, 2.4vw, 1.8rem);
        margin-bottom: 0.35rem;
    }

    .fh-eyebrow {
        color: var(--teal) !important;
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin: 0 0 0.5rem;
        text-transform: uppercase;
    }

    .fh-hero h1 {
        margin: 0 0 0.25rem !important;
    }

    .fh-hero p {
        color: var(--text-secondary) !important;
        font-size: 0.98rem;
        margin: 0;
        max-width: 780px;
    }

    .fh-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-sm);
        min-height: 150px;
        padding: 1.05rem;
        transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    }

    .fh-card:hover {
        border-color: var(--border-strong);
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }

    .fh-card-kicker {
        color: var(--teal) !important;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.07em;
        margin-bottom: 0.45rem;
        text-transform: uppercase;
    }

    .fh-card h3 {
        font-size: 1rem !important;
        margin: 0 0 0.35rem !important;
    }

    .fh-card p {
        color: var(--text-secondary) !important;
        font-size: 0.9rem;
        line-height: 1.55 !important;
        margin: 0;
    }

    .fh-status {
        align-items: center;
        animation: fh-fade-up 360ms ease both;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        box-shadow: var(--shadow-sm);
        display: flex;
        gap: 0.75rem;
        justify-content: space-between;
        margin: 0.25rem 0 0.7rem;
        overflow: hidden;
        padding: 0.8rem 0.95rem;
        position: relative;
    }

    .fh-status::before {
        content: "";
        background: linear-gradient(180deg, var(--navy), var(--teal));
        bottom: 0;
        left: 0;
        position: absolute;
        top: 0;
        width: 4px;
    }

    .fh-status::after {
        animation: fh-sheen 2.8s ease-in-out infinite;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.22), transparent);
        content: "";
        inset: 0;
        opacity: 0.7;
        pointer-events: none;
        position: absolute;
        transform: translateX(-100%);
    }

    .fh-status span {
        color: var(--text-muted) !important;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        white-space: nowrap;
    }

    .fh-status strong {
        color: var(--text-primary) !important;
        font-size: 0.9rem;
        font-weight: 650;
        text-align: right;
    }

    .fh-status-success::before {
        background: var(--green);
    }

    .fh-status-danger::before {
        background: var(--red);
    }

    .fh-status-idle::before {
        background: var(--amber);
    }

    .fh-insights-panel {
        animation: fh-fade-up 380ms ease both;
        margin: 0.35rem 0 1.25rem;
    }

    .fh-insights-header {
        align-items: baseline;
        display: flex;
        gap: 0.7rem;
        justify-content: space-between;
        margin-bottom: 0.65rem;
    }

    .fh-insights-header span {
        color: var(--teal) !important;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .fh-insights-header strong {
        color: var(--text-muted) !important;
        font-size: 0.84rem;
        font-weight: 650;
    }

    .fh-insights-grid {
        display: grid;
        gap: 0.85rem;
        grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    }

    .fh-insight-card {
        background:
            linear-gradient(145deg, rgba(255, 255, 255, 0.72), rgba(248, 250, 252, 0.84)),
            var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-sm);
        min-height: 148px;
        overflow: hidden;
        padding: 1rem 1rem 1.05rem;
        position: relative;
        transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    }

    .fh-insight-card::before {
        content: "";
        background: linear-gradient(180deg, var(--navy), var(--teal));
        bottom: 0;
        left: 0;
        position: absolute;
        top: 0;
        width: 4px;
    }

    .fh-insight-card:hover {
        border-color: var(--border-strong);
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }

    .fh-insight-label {
        color: var(--text-muted) !important;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-bottom: 0.55rem;
        text-transform: uppercase;
    }

    .fh-insight-card h4 {
        color: var(--text-primary) !important;
        font-size: 1rem !important;
        margin: 0 0 0.4rem !important;
    }

    .fh-insight-card p {
        color: var(--text-secondary) !important;
        font-size: 0.88rem;
        line-height: 1.55 !important;
        margin: 0;
    }

    .fh-insight-positive::before {
        background: var(--green);
    }

    .fh-insight-warning::before {
        background: var(--amber);
    }

    .fh-insight-danger::before {
        background: var(--red);
    }

    @media (prefers-color-scheme: dark) {
        .fh-insight-card {
            background:
                linear-gradient(145deg, rgba(17, 24, 39, 0.86), rgba(20, 29, 43, 0.92)),
                var(--surface);
        }
    }

    [data-testid="stMetric"] {
        position: relative !important;
        overflow: hidden !important;
        background: linear-gradient(145deg, var(--surface-strong), var(--surface-muted)) !important;
        border: 1px solid var(--border) !important;
        box-shadow: var(--shadow-md) !important;
        border-radius: var(--radius-lg) !important;
        padding: 1.15rem 1.25rem !important;
        min-height: 132px !important;
        animation: fh-fade-up 360ms ease both !important;
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease !important;
    }

    [data-testid="stMetric"]::before {
        content: "";
        position: absolute;
        inset: 0 auto 0 0;
        width: 4px;
        background: linear-gradient(180deg, var(--navy), var(--teal));
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-2px) !important;
        border-color: var(--border-strong) !important;
        box-shadow: var(--shadow-lg) !important;
    }

    [data-testid="stMetricLabel"] > div {
        font-size: 0.72rem !important;
        font-weight: 750 !important;
        letter-spacing: 0.055em !important;
        text-transform: uppercase !important;
        color: var(--text-muted) !important;
    }

    [data-testid="stMetricValue"] > div {
        color: var(--text-primary) !important;
        font-size: clamp(1.65rem, 2.4vw, 2.2rem) !important;
        font-weight: 800 !important;
        line-height: 1.15 !important;
        letter-spacing: 0 !important;
    }

    [data-testid="stMetricDelta"] {
        font-size: 13px !important;
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
    }

    [data-testid="stNumberInput"] input,
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {
        background-color: var(--surface-strong) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        color: var(--text-primary) !important;
        font-family: var(--font) !important;
        font-size: 14px !important;
        transition: border-color 0.15s, box-shadow 0.15s !important;
    }

    [data-testid="stNumberInput"] input:focus,
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: var(--border-focus) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.16) !important;
        outline: none !important;
    }

    [data-baseweb="select"] > div:first-child {
        background-color: var(--surface-strong) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        color: var(--text-primary) !important;
    }

    [data-baseweb="slider"] [role="slider"] {
        background: var(--gradient-btn) !important;
        border: 2px solid var(--surface-strong) !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.22) !important;
    }

    [data-baseweb="slider"] > div > div {
        color: var(--navy) !important;
    }

    [data-testid="stButton"] > button,
    [data-testid="stFormSubmitButton"] > button {
        background: var(--gradient-btn) !important;
        border: none !important;
        border-radius: var(--radius) !important;
        color: #FFFFFF !important;
        font-family: var(--font) !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        letter-spacing: 0 !important;
        padding: 0.64rem 1.1rem !important;
        transition: transform 0.15s, box-shadow 0.15s, filter 0.15s !important;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.22) !important;
    }

    [data-testid="stButton"] > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background: var(--gradient-btn-hover) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 14px 34px rgba(37, 99, 235, 0.28) !important;
    }

    [data-testid="stButton"] > button:active,
    [data-testid="stFormSubmitButton"] > button:active {
        transform: translateY(0) !important;
    }

    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        width: fit-content !important;
        max-width: 100% !important;
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow-sm) !important;
        padding: 5px !important;
        gap: 4px !important;
        margin: 1.25rem 0 1.1rem !important;
        overflow-x: auto !important;
    }

    [data-testid="stTabs"] [data-baseweb="tab"] {
        background: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        color: var(--text-secondary) !important;
        font-family: var(--font) !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        padding: 0.58rem 1rem !important;
        transition: background 0.15s, color 0.15s !important;
        white-space: nowrap !important;
    }

    [data-testid="stTabs"] [aria-selected="true"] {
        background: var(--gradient-btn) !important;
        color: #FFFFFF !important;
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.2) !important;
    }

    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    [data-testid="stForm"],
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    [data-testid="stForm"] {
        padding: 1.1rem !important;
    }

    [data-testid="stAlert"] {
        animation: fh-fade-up 300ms ease both !important;
        border-radius: var(--radius) !important;
        border-color: var(--border) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    [data-testid="stPlotlyChart"] {
        animation: fh-chart-in 460ms ease both !important;
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        box-shadow: var(--shadow-md) !important;
        padding: 0.55rem !important;
        overflow: hidden !important;
    }

    [data-testid="stStatusWidget"] {
        animation: fh-fade-up 320ms ease both !important;
    }

    [data-testid="stExpander"] {
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow-sm) !important;
        overflow: hidden !important;
    }

    hr {
        border-color: var(--border) !important;
        margin: 1.45rem 0 !important;
    }

    div[data-testid="stProgress"] > div {
        background: var(--surface-muted) !important;
        border-radius: 999px !important;
    }

    div[data-testid="stProgress"] div[role="progressbar"] {
        background: var(--gradient-btn) !important;
        border-radius: 999px !important;
        transition: width 0.35s ease !important;
    }

    @media (max-width: 980px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1.25rem 1rem 2.5rem !important;
        }

        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            width: 100% !important;
        }

        [data-testid="stMetric"] {
            min-height: 112px !important;
            padding: 1rem 1.05rem !important;
        }
    }

    @media (max-width: 640px) {
        h1 {
            font-size: 2rem !important;
        }

        [data-testid="stMetricValue"] > div {
            font-size: 1.55rem !important;
        }

        [data-testid="stTabs"] [data-baseweb="tab"] {
            padding: 0.55rem 0.75rem !important;
            font-size: 0.82rem !important;
        }

        .fh-status {
            align-items: flex-start;
            flex-direction: column;
            gap: 0.25rem;
        }

        .fh-status strong {
            text-align: left;
        }

        .fh-insights-header {
            align-items: flex-start;
            flex-direction: column;
            gap: 0.2rem;
        }

        .fh-insights-grid {
            grid-template-columns: 1fr;
        }
    }

    @keyframes fh-fade-up {
        from {
            opacity: 0;
            transform: translateY(8px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fh-chart-in {
        from {
            opacity: 0;
            transform: translateY(10px) scale(0.995);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    @keyframes fh-sheen {
        0%, 65% {
            transform: translateX(-100%);
        }
        100% {
            transform: translateX(100%);
        }
    }

    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            animation-duration: 0.001ms !important;
            animation-iteration-count: 1 !important;
            scroll-behavior: auto !important;
            transition-duration: 0.001ms !important;
        }
    }

    ::-webkit-scrollbar              { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track        { background: transparent; }
    ::-webkit-scrollbar-thumb        { background: linear-gradient(180deg, var(--navy-soft), var(--teal)); border-radius: 999px; }
    ::-webkit-scrollbar-thumb:hover  { background: var(--navy); }
    </style>
    """,
        unsafe_allow_html=True,
    )
