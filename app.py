"""
Fin-Health AI — Streamlit dashboard entry point.
"""

import streamlit as st

from src.bootstrap import ensure_demo_assets
from src.core.config import get_config
from src.core.logging_config import configure_logging
from src.readiness import readiness_summary
from src.ui.sections import (
    init_session_state,
    render_history_tab,
    render_home_tab,
    render_market_portfolio_tab,
    render_my_portfolio_tab,
    render_risk_analysis_tab,
    render_sidebar_login,
)
from src.ui.theme import load_custom_css

configure_logging()
config = get_config()

st.set_page_config(
    page_title=config.app_name,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
bootstrap_actions = ensure_demo_assets()
load_custom_css()
init_session_state()


@st.cache_resource(show_spinner="Building SHAP explainer…")
def _cached_shap_bundle(model_mtime: float, scaler_mtime: float):
    from src.credit_risk_explainer import build_shap_explainer_bundle

    return build_shap_explainer_bundle()


@st.cache_data(show_spinner="Scoring market portfolio…")
def _cached_market_portfolio_bundle(loan_mtime: float, model_mtime: float, scaler_mtime: float):
    from src.portfolio_dashboard import build_portfolio_bundle

    return build_portfolio_bundle()


# ── Layout: sidebar login column + main workspace ─────────────────────────────
render_sidebar_login()

st.sidebar.divider()
st.sidebar.header("System status")
st.sidebar.success(f"Model: {config.model_display_name} ({config.model_version})")
st.sidebar.info("Use tabs for each workflow.")
if bootstrap_actions:
    with st.sidebar.expander("Startup actions"):
        for action in bootstrap_actions:
            st.caption(action)
with st.sidebar.expander("Deployment readiness"):
    ready, checks = readiness_summary()
    for check in checks:
        if check.ok:
            st.success(check.name)
        else:
            st.warning(f"{check.name}: {check.detail}")
    if ready:
        st.caption("All readiness checks passed.")

st.markdown(
    """
    <section class="fh-hero">
        <p class="fh-eyebrow">Credit intelligence dashboard</p>
        <h1>Fin-Health AI</h1>
        <p>
            Predictive credit risk, portfolio analytics, and personal applicant
            watchlists in one clean analytics workspace.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

tab_home, tab_risk, tab_market, tab_my, tab_history = st.tabs(
    [
        "Home",
        "Risk analysis",
        "Market portfolio",
        "My portfolio",
        "History",
    ]
)

with tab_home:
    render_home_tab()

with tab_risk:
    render_risk_analysis_tab(_cached_shap_bundle)

with tab_market:
    render_market_portfolio_tab(_cached_market_portfolio_bundle)

with tab_my:
    render_my_portfolio_tab()

with tab_history:
    render_history_tab()
