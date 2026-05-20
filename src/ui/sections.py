"""
Streamlit UI sections: sidebar auth and tab bodies.
"""

from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from src.applicant_history import (
    add_analysis,
    clear_history,
    delete_analysis,
    delete_history_database,
    history_summary,
    load_analyses,
)
from src.auth import authenticate, register_user
from src.core.config import get_config
from src.inference import FEATURE_COLUMNS, predict_risk, resolved_artifact_paths
from src.pdf_report import build_risk_report_pdf
from src.user_portfolio import (
    add_applicant,
    applicants_to_dataframe,
    clear_portfolio,
    load_portfolio,
    remove_applicant,
)


PLOTLY_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": False,
    "modeBarButtonsToRemove": [
        "lasso2d",
        "select2d",
        "toggleSpikelines",
    ],
}


def init_session_state() -> None:
    defaults = {
        "auth_user": None,
        "auth_display_name": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def is_logged_in() -> bool:
    return bool(st.session_state.get("auth_user"))


def current_user_email() -> str | None:
    return st.session_state.get("auth_user")


def _render_status_pill(label: str, detail: str, tone: str = "ready") -> None:
    st.markdown(
        f"""
        <div class="fh-status fh-status-{tone}">
            <span>{label}</span>
            <strong>{detail}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _apply_chart_transition(fig) -> None:
    fig.update_layout(transition={"duration": 350, "easing": "cubic-in-out"})


def _insight_card(title: str, body: str, tone: str = "neutral") -> str:
    return (
        f'<div class="fh-insight-card fh-insight-{tone}">'
        f'<div class="fh-insight-label">AI insight</div>'
        f"<h4>{escape(title)}</h4>"
        f"<p>{escape(body)}</p>"
        "</div>"
    )


def _render_insight_cards(insights: list[dict[str, str]]) -> None:
    if not insights:
        return
    cards = "\n".join(
        _insight_card(
            insight["title"],
            insight["body"],
            insight.get("tone", "neutral"),
        )
        for insight in insights
    )
    st.markdown(
        f"""
        <section class="fh-insights-panel">
            <div class="fh-insights-header">
                <span>AI-generated insights</span>
                <strong>Financial narrative summary</strong>
            </div>
            <div class="fh-insights-grid">
                {cards}
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _format_history_timestamp(value: str) -> str:
    try:
        dt = pd.to_datetime(value, utc=True)
    except (TypeError, ValueError):
        return str(value)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def _applicant_insights(input_data: dict[str, Any], result: dict[str, Any]) -> list[dict[str, str]]:
    income = float(input_data["Income"])
    loan = float(input_data["Loan"])
    debt = float(input_data["Debt"])
    credit_score = float(input_data["Credit Score"])
    employment_years = float(input_data["Employment Years"])
    probability = float(result["probability_score"])
    loan_to_income = loan / income if income > 0 else 0.0

    insights: list[dict[str, str]] = []

    if debt >= 0.45:
        insights.append(
            {
                "title": "High debt-service pressure",
                "body": (
                    f"DTI is {debt:.0%}, which indicates constrained monthly cash flow. "
                    "A lender should review repayment buffers, recurring obligations, and income stability before approval."
                ),
                "tone": "danger",
            }
        )
    elif debt >= 0.32:
        insights.append(
            {
                "title": "Moderate debt utilization",
                "body": (
                    f"DTI is {debt:.0%}. The profile is serviceable, but affordability should be monitored if new credit is added."
                ),
                "tone": "warning",
            }
        )
    else:
        insights.append(
            {
                "title": "Healthy debt capacity",
                "body": (
                    f"DTI is {debt:.0%}, suggesting the applicant has manageable recurring obligations relative to income."
                ),
                "tone": "positive",
            }
        )

    if loan_to_income >= 0.55:
        insights.append(
            {
                "title": "Overspending indicator",
                "body": (
                    f"The requested loan is {loan_to_income:.0%} of annual income. "
                    "This may signal elevated leverage appetite and should trigger a closer affordability review."
                ),
                "tone": "danger",
            }
        )
    elif loan_to_income >= 0.35:
        insights.append(
            {
                "title": "Elevated loan exposure",
                "body": (
                    f"Loan-to-income is {loan_to_income:.0%}. The exposure is meaningful, but may be acceptable with strong cash-flow evidence."
                ),
                "tone": "warning",
            }
        )
    else:
        insights.append(
            {
                "title": "Controlled borrowing request",
                "body": (
                    f"Loan-to-income is {loan_to_income:.0%}, which points to a more conservative borrowing profile."
                ),
                "tone": "positive",
            }
        )

    if employment_years < 2:
        insights.append(
            {
                "title": "Low employment stability",
                "body": (
                    f"Employment history is {employment_years:.0f} year(s). "
                    "Short tenure can increase income volatility risk and may justify additional verification."
                ),
                "tone": "warning",
            }
        )
    elif employment_years >= 5:
        insights.append(
            {
                "title": "Stable income profile",
                "body": (
                    f"{employment_years:.0f} years of employment supports a stronger repayment narrative and lowers operational uncertainty."
                ),
                "tone": "positive",
            }
        )

    if credit_score >= 740:
        insights.append(
            {
                "title": "Strong credit quality",
                "body": (
                    f"A credit score of {credit_score:.0f} is a positive financial indicator and supports lower expected default risk."
                ),
                "tone": "positive",
            }
        )
    elif credit_score < 580:
        insights.append(
            {
                "title": "Subprime credit signal",
                "body": (
                    f"A credit score of {credit_score:.0f} indicates weaker bureau performance and should be paired with tighter terms or review."
                ),
                "tone": "danger",
            }
        )

    insights.append(
        {
            "title": "Model risk narrative",
            "body": (
                f"The model estimates a {probability:.1%} probability of default. "
                "Use this as a decision-support signal alongside policy rules, verification checks, and manual credit judgment."
            ),
            "tone": "danger" if probability >= get_config().high_risk_threshold else "positive",
        }
    )
    return insights[:5]


def _portfolio_insights(kpis: dict[str, Any], n: int) -> list[dict[str, str]]:
    high_risk_count = int(kpis.get("high_risk_count", 0))
    high_risk_share = high_risk_count / n if n else 0.0
    mean_default = float(kpis.get("mean_predicted_default_pct", 0.0))
    median_score = float(kpis.get("median_credit_score", 0.0))
    actual_default = kpis.get("actual_default_rate_pct")

    insights = [
        {
            "title": "Portfolio health summary",
            "body": (
                f"{high_risk_share:.1%} of applicants are above the high-risk threshold, "
                f"with an average predicted default risk of {mean_default:.1f}%."
            ),
            "tone": "danger" if high_risk_share >= 0.45 else "warning" if high_risk_share >= 0.25 else "positive",
        }
    ]

    if median_score < 620:
        insights.append(
            {
                "title": "Credit quality concentration",
                "body": (
                    f"Median credit score is {median_score:.0f}, indicating the book skews toward weaker credit tiers. "
                    "Consider segment-level limits or tighter approval criteria."
                ),
                "tone": "danger",
            }
        )
    elif median_score >= 700:
        insights.append(
            {
                "title": "Positive bureau profile",
                "body": (
                    f"Median credit score is {median_score:.0f}, suggesting healthier credit quality across the portfolio."
                ),
                "tone": "positive",
            }
        )
    else:
        insights.append(
            {
                "title": "Mixed credit distribution",
                "body": (
                    f"Median credit score is {median_score:.0f}. The portfolio may benefit from additional tier-based monitoring."
                ),
                "tone": "warning",
            }
        )

    if actual_default is not None:
        drift = float(actual_default) - mean_default
        if drift >= 8:
            insights.append(
                {
                    "title": "Observed default pressure",
                    "body": (
                        f"Actual default rate is {float(actual_default):.1f}%, materially above predicted risk. "
                        "This may indicate calibration drift or recent portfolio stress."
                    ),
                    "tone": "danger",
                }
            )
        else:
            insights.append(
                {
                    "title": "Risk calibration check",
                    "body": (
                        f"Actual default rate is {float(actual_default):.1f}% versus {mean_default:.1f}% predicted. "
                        "Monitor this spread to validate model calibration over time."
                    ),
                    "tone": "neutral",
                }
            )
    else:
        insights.append(
            {
                "title": "Custom portfolio context",
                "body": (
                    "Actual default outcomes are unavailable for this saved portfolio, so the summary relies on predicted risk signals only."
                ),
                "tone": "neutral",
            }
        )

    return insights


def render_sidebar_login() -> None:
    """Login / register column in the sidebar."""
    st.sidebar.markdown("### Account")
    if is_logged_in():
        st.sidebar.success(f"Signed in as **{st.session_state.auth_display_name}**")
        st.sidebar.caption(st.session_state.auth_user)
        if st.sidebar.button("Sign out", width="stretch"):
            st.session_state.auth_user = None
            st.session_state.auth_display_name = None
            st.rerun()
        return

    mode = st.sidebar.radio("Mode", ["Sign in", "Register"], horizontal=True, label_visibility="collapsed")

    with st.sidebar.form("auth_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder="you@company.com")
        if mode == "Register":
            display_name = st.text_input("Display name", placeholder="Your name")
        else:
            display_name = ""
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(
            "Create account" if mode == "Register" else "Sign in",
            width="stretch",
        )

    if submitted:
        if mode == "Register":
            ok, msg = register_user(email, password, display_name)
            if ok:
                ok_in, _, user = authenticate(email, password)
                if ok_in and user:
                    st.session_state.auth_user = user["email"]
                    st.session_state.auth_display_name = user["display_name"]
                    st.sidebar.success("Account created — you are signed in.")
                    st.rerun()
                st.sidebar.success(msg)
            else:
                st.sidebar.error(msg)
        else:
            ok, msg, user = authenticate(email, password)
            if ok and user:
                st.session_state.auth_user = user["email"]
                st.session_state.auth_display_name = user["display_name"]
                st.sidebar.success(msg)
                st.rerun()
            st.sidebar.error(msg)

    st.sidebar.caption("Sign in to build and save your personal applicant portfolio.")


def render_home_tab() -> None:
    _render_status_pill("Workspace ready", "Model artifacts, dashboards, and portfolio tools are available.", "ready")
    st.markdown("### Welcome to Fin-Health AI")
    st.markdown(
        """
        Move across the tabs to score individual applicants, review portfolio health,
        and manage a private applicant watchlist.
        """
    )
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        """
        <div class="fh-card">
            <div class="fh-card-kicker">Decisioning</div>
            <h3>Risk analysis</h3>
            <p>Score one applicant and inspect the strongest SHAP drivers behind the model output.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c2.markdown(
        """
        <div class="fh-card">
            <div class="fh-card-kicker">Portfolio</div>
            <h3>Market portfolio</h3>
            <p>Track book-level KPIs, mean predicted default risk, and credit score distribution.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c3.markdown(
        """
        <div class="fh-card">
            <div class="fh-card-kicker">Watchlist</div>
            <h3>My portfolio</h3>
            <p>Build a private applicant list and monitor custom portfolio analytics after sign-in.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if is_logged_in():
        portfolio = load_portfolio(current_user_email())
        n = len(portfolio.get("applicants", []))
        st.metric("Your saved applicants", n)


def _applicant_form_defaults() -> dict[str, Any]:
    return {
        "age": 35,
        "income": 72000,
        "c_score": 700,
        "loan": 25000,
        "debt": 0.28,
        "exp": 6,
    }


def render_risk_analysis_tab(
    cached_shap_bundle,
) -> None:
    col_input, col_viz = st.columns([1, 2])
    defaults = _applicant_form_defaults()

    with col_input:
        st.subheader("Applicant profile")
        with st.form("risk_form"):
            age = st.number_input("Age", 18, 90, defaults["age"])
            income = st.number_input(
                "Annual income ($)",
                min_value=0,
                max_value=None,
                value=defaults["income"],
                step=1000,
            )
            c_score = st.slider("Credit score", 300, 850, defaults["c_score"])
            loan = st.number_input(
                "Loan amount ($)",
                min_value=0,
                max_value=None,
                value=defaults["loan"],
                step=1000,
            )
            debt = st.slider("Debt-to-income (DTI)", 0.0, 1.0, defaults["debt"])
            exp = st.number_input("Years of employment", 0, 40, defaults["exp"])
            submit = st.form_submit_button("Run risk analysis", width="stretch")

    with col_viz:
        if not submit:
            _render_status_pill(
                "Awaiting applicant profile",
                "Complete the form and run risk analysis to generate a prediction.",
                "idle",
            )
            st.info("Complete the profile and run **Risk analysis** to see prediction and SHAP.")
            return

        input_data = {
            "Age": age,
            "Income": income,
            "Credit Score": c_score,
            "Loan": loan,
            "Debt": debt,
            "Employment Years": exp,
        }
        progress = st.progress(0, text="Validating applicant profile...")
        with st.status("Processing applicant risk profile", expanded=True) as status:
            st.write("Checking feature values and preparing model input.")
            progress.progress(20, text="Preparing model features...")
            with st.spinner("Running credit risk model..."):
                try:
                    result = predict_risk(input_data)
                except (FileNotFoundError, ValueError) as exc:
                    progress.progress(100, text="Risk analysis could not run.")
                    status.update(label="Prediction failed", state="error", expanded=False)
                    st.error(str(exc))
                    return
            with st.spinner("Saving analysis to local history..."):
                try:
                    history_id = add_analysis(
                        user_email=current_user_email(),
                        input_data=input_data,
                        result=result,
                    )
                except Exception as exc:  # noqa: BLE001
                    progress.progress(100, text="Risk analysis could not be saved.")
                    status.update(label="History save failed", state="error", expanded=False)
                    st.error(f"Prediction completed, but history could not be saved: {exc}")
                    return
            progress.progress(62, text="Model prediction saved. Preparing risk summary...")
            status.update(label="Prediction complete", state="complete", expanded=False)

        st.subheader("Risk assessment")
        prob = result["probability_score"]
        if result["prediction"] == "Low Risk":
            st.success(f"### {result['prediction']}")
            _render_status_pill("Decision signal", "Applicant is currently below the high-risk threshold.", "success")
        else:
            st.error(f"### {result['prediction']}")
            _render_status_pill("Decision signal", "Applicant should receive elevated credit review.", "danger")
        st.metric("Default probability", f"{prob * 100:.1f}%")
        st.progress(prob, text=f"Predicted default probability: {prob * 100:.1f}%")
        st.caption(f"Saved to applicant history as analysis #{history_id}.")

        st.subheader("AI financial insights")
        with st.spinner("Generating financial insights..."):
            insights = _applicant_insights(input_data, result)
            _render_insight_cards(insights)

        shap_fig = None
        st.subheader("Why this prediction? (SHAP)")
        rp = resolved_artifact_paths()
        if rp:
            model_path, scaler_path = rp
            try:
                from src.credit_risk_explainer import explain_credit_prediction

                with st.spinner("Building explanation chart..."):
                    progress.progress(82, text="Generating SHAP explanation...")
                    explainer, model, scaler = cached_shap_bundle(
                        model_path.stat().st_mtime,
                        scaler_path.stat().st_mtime,
                    )
                    fig = explain_credit_prediction(
                        input_data,
                        explainer=explainer,
                        scaler=scaler,
                        model=model,
                    )
                    _apply_chart_transition(fig)
                    shap_fig = fig
                progress.progress(100, text="Risk analysis ready.")
                st.success("Risk assessment and explanation are ready.")
                st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)
            except Exception as exc:  # noqa: BLE001
                progress.progress(100, text="Prediction complete. Explanation unavailable.")
                st.warning(f"Explainability chart unavailable: {exc}")
        else:
            progress.progress(100, text="Prediction complete. Train artifacts to enable SHAP.")
            st.warning("Train the model to enable SHAP explanations.")

        st.subheader("Download risk report")
        with st.spinner("Preparing PDF report..."):
            pdf_bytes = build_risk_report_pdf(
                input_data=input_data,
                result=result,
                insights=insights,
                shap_fig=shap_fig,
            )
        st.download_button(
            "Download PDF risk report",
            data=pdf_bytes,
            file_name=f"fin_health_risk_report_{history_id}.pdf",
            mime="application/pdf",
            width="stretch",
        )

        if is_logged_in():
            if st.button("Save this applicant to My portfolio"):
                add_applicant(
                    current_user_email(),
                    label=f"Applicant {c_score:.0f} score",
                    age=age,
                    annual_income=income,
                    credit_score=c_score,
                    loan_amount=loan,
                    debt_to_income=debt,
                    employment_years=exp,
                )
                st.success("Saved to your portfolio. Open the **My portfolio** tab to review.")


def render_market_portfolio_tab(cached_portfolio_bundle) -> None:
    from src.core.config import get_config

    data_path = get_config().loan_data_path

    st.markdown("### Market portfolio health")
    st.caption("Full synthetic loan book (`loan_data.csv`) scored with your trained model.")
    _render_status_pill("Portfolio engine", "Ready to score the current loan book.", "ready")

    rp = resolved_artifact_paths()
    if not rp:
        _render_status_pill("Setup required", "Model artifacts were not found.", "danger")
        st.warning("Train the model first (`python -m src.train_model`).")
        return
    if not data_path.is_file():
        _render_status_pill("Data required", "The synthetic loan book is missing.", "danger")
        st.warning(f"Missing `{data_path}`. Run `python -m src.generate_data`.")
        return

    model_path, scaler_path = rp
    try:
        progress = st.progress(0, text="Loading loan book...")
        with st.status("Scoring market portfolio", expanded=True) as status:
            st.write("Loading applicants and applying the trained risk model.")
            progress.progress(35, text="Scoring applicants...")
            with st.spinner("Calculating portfolio KPIs and charts..."):
                kpis, gauge_fig, hist_fig = cached_portfolio_bundle(
                    data_path.stat().st_mtime,
                    model_path.stat().st_mtime,
                    scaler_path.stat().st_mtime,
                )
            progress.progress(80, text="Preparing dashboard visuals...")
            _apply_chart_transition(gauge_fig)
            _apply_chart_transition(hist_fig)
            progress.progress(100, text="Portfolio dashboard ready.")
            status.update(label="Portfolio scoring complete", state="complete", expanded=False)
        st.success(f"Scored {kpis['n_applicants']:,} applicants successfully.")
        _render_portfolio_kpis_and_charts(kpis, gauge_fig, hist_fig, kpis["n_applicants"])
    except Exception as exc:  # noqa: BLE001
        _render_status_pill("Portfolio scoring failed", "Review the error details below.", "danger")
        st.error(f"Portfolio view failed: {exc}")


def render_history_tab() -> None:
    st.markdown("### Applicant analysis history")
    st.caption("SQLite-backed record of previous risk analyses from this dashboard.")

    email = current_user_email()
    if email:
        st.info(f"Showing saved analyses for **{email}**.")
    else:
        st.info("Sign in to keep history associated with your account. Anonymous analyses stay local.")

    summary = history_summary(user_email=email)
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Total analyses", f"{summary['total']:,}")
    h2.metric("High-risk results", f"{summary['high_risk']:,}")
    avg = summary["avg_probability_pct"]
    h3.metric("Avg default probability", f"{avg:.1f}%" if avg is not None else "N/A")
    h4.metric(
        "Latest analysis",
        _format_history_timestamp(summary["latest_at"]) if summary["latest_at"] else "N/A",
    )

    df = load_analyses(user_email=email, limit=100)
    if df.empty:
        st.warning("No previous analyses found. Run a risk analysis to populate this dashboard.")
        if st.button("Delete empty history database", type="secondary"):
            if delete_history_database():
                st.success("History database deleted. It will be recreated on the next analysis.")
                st.rerun()
            st.info("No history database file was found.")
        return

    view = df.copy()
    view["created_at"] = view["created_at"].map(_format_history_timestamp)
    view["probability_score"] = (view["probability_score"] * 100).round(1)
    view = view.rename(
        columns={
            "id": "Analysis ID",
            "created_at": "Timestamp",
            "age": "Age",
            "annual_income": "Income",
            "credit_score": "Credit score",
            "loan_amount": "Loan",
            "debt_to_income": "DTI",
            "employment_years": "Employment years",
            "prediction": "Prediction",
            "probability_score": "Default probability (%)",
        }
    )
    st.dataframe(
        view[
            [
                "Analysis ID",
                "Timestamp",
                "Prediction",
                "Default probability (%)",
                "Credit score",
                "Income",
                "Loan",
                "DTI",
                "Employment years",
            ]
        ],
        width="stretch",
        hide_index=True,
    )

    selected_id = st.selectbox(
        "View analysis details",
        options=df["id"].tolist(),
        format_func=lambda row_id: (
            f"#{row_id} · "
            f"{df.loc[df['id'] == row_id, 'prediction'].iloc[0]} · "
            f"{_format_history_timestamp(df.loc[df['id'] == row_id, 'created_at'].iloc[0])}"
        ),
    )

    del_col, clear_col = st.columns(2)
    with del_col:
        if st.button("Delete selected analysis", type="secondary", width="stretch"):
            with st.spinner("Deleting selected history record..."):
                removed = delete_analysis(int(selected_id), user_email=email)
            if removed:
                st.success(f"Deleted analysis #{selected_id}.")
                st.rerun()
            st.warning("That analysis could not be found.")
    with clear_col:
        if st.button("Clear visible history", type="secondary", width="stretch"):
            with st.spinner("Clearing analysis history..."):
                removed_count = clear_history(user_email=email)
            st.success(f"Deleted {removed_count} history record(s).")
            st.rerun()

    with st.expander("Database management"):
        st.caption(
            "Use this only when you want to remove the local SQLite history database file. "
            "A fresh empty database will be created automatically when you run the next analysis."
        )
        confirm_delete_db = st.checkbox("I understand this deletes the local history database file.")
        if st.button("Delete history database", type="secondary", disabled=not confirm_delete_db):
            with st.spinner("Deleting SQLite history database..."):
                deleted = delete_history_database()
            if deleted:
                st.success("History database deleted.")
                st.rerun()
            st.info("No history database file was found.")

    row = df.loc[df["id"] == selected_id].iloc[0]
    detail_input = {
        "Age": row["age"],
        "Income": row["annual_income"],
        "Credit Score": row["credit_score"],
        "Loan": row["loan_amount"],
        "Debt": row["debt_to_income"],
        "Employment Years": row["employment_years"],
    }
    detail_result = {
        "prediction": row["prediction"],
        "probability_score": row["probability_score"],
    }

    st.markdown("#### Previous analysis summary")
    d1, d2, d3 = st.columns(3)
    d1.metric("Prediction", str(row["prediction"]))
    d2.metric("Default probability", f"{float(row['probability_score']) * 100:.1f}%")
    d3.metric("Timestamp", _format_history_timestamp(str(row["created_at"])))
    _render_insight_cards(_applicant_insights(detail_input, detail_result))


def _render_portfolio_kpis_and_charts(
    kpis: dict[str, Any],
    gauge_fig,
    hist_fig,
    n: int,
    *,
    title_caption: str | None = None,
) -> None:
    if title_caption:
        st.caption(title_caption)
    else:
        st.caption(
            f"{n:,} applicants · High-risk = P(default) ≥ {get_config().high_risk_threshold:.0%} · "
            f"Gauge benchmark line = {get_config().portfolio_gauge_threshold_pct:.0f}% mean predicted default."
        )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total applicants", f"{n:,}")
    k2.metric("Median credit score", f"{kpis['median_credit_score']:.0f}")
    k3.metric("High-risk count", f"{kpis['high_risk_count']:,}")
    dr = kpis["actual_default_rate_pct"]
    k4.metric("Actual default rate", f"{dr:.1f}%" if dr is not None else "N/A")

    _render_insight_cards(_portfolio_insights(kpis, n))

    gcol, hcol = st.columns(2)
    with gcol:
        st.plotly_chart(gauge_fig, width="stretch", config=PLOTLY_CONFIG)
    with hcol:
        st.plotly_chart(hist_fig, width="stretch", config=PLOTLY_CONFIG)


def render_my_portfolio_tab() -> None:
    st.markdown("### My portfolio")
    if not is_logged_in():
        st.warning("Sign in using the **Account** panel in the left column to build your portfolio.")
        return

    email = current_user_email()
    portfolio = load_portfolio(email)
    applicants = portfolio.get("applicants", [])

    st.caption(f"Private portfolio for **{st.session_state.auth_display_name}** · {len(applicants)} applicant(s)")
    _render_status_pill(
        "Private workspace",
        f"{len(applicants)} saved applicant(s) available for review.",
        "ready" if applicants else "idle",
    )

    col_add, col_list = st.columns([1, 2])

    with col_add:
        st.subheader("Add applicant")
        with st.form("add_to_portfolio"):
            label = st.text_input("Label", placeholder="e.g. Q2 renewal — Acme Corp")
            age = st.number_input("Age", 18, 90, 35, key="my_age")
            income = st.number_input("Annual income ($)", 0, None, 65000, step=1000, key="my_income")
            c_score = st.slider("Credit score", 300, 850, 680, key="my_score")
            loan = st.number_input("Loan amount ($)", 0, None, 15000, step=1000, key="my_loan")
            debt = st.slider("DTI", 0.0, 1.0, 0.25, key="my_dti")
            exp = st.number_input("Employment years", 0, 40, 5, key="my_exp")
            notes = st.text_area("Notes (optional)", height=68)
            add_btn = st.form_submit_button("Add to portfolio", width="stretch")

        if add_btn:
            with st.spinner("Saving applicant to your portfolio..."):
                add_applicant(
                    email,
                    label=label,
                    age=age,
                    annual_income=income,
                    credit_score=c_score,
                    loan_amount=loan,
                    debt_to_income=debt,
                    employment_years=exp,
                    notes=notes,
                )
            st.success("Applicant added.")
            st.rerun()

        if applicants and st.button("Clear entire portfolio", type="secondary"):
            with st.spinner("Clearing portfolio..."):
                clear_portfolio(email)
            st.rerun()

    with col_list:
        st.subheader("Your applicants")
        if not applicants:
            st.info("No applicants yet. Use the form on the left or save from **Risk analysis**.")
            return

        table_rows = []
        for a in applicants:
            table_rows.append(
                {
                    "Label": a.get("label"),
                    "Age": a.get("Age"),
                    "Income": a.get("Annual_Income"),
                    "Credit score": a.get("Credit_Score"),
                    "Loan": a.get("Loan_Amount"),
                    "DTI": a.get("Debt_to_Income_Ratio"),
                    "Emp. years": a.get("Employment_Years"),
                    "Notes": a.get("notes", ""),
                    "id": a.get("id"),
                }
            )
        st.dataframe(
            pd.DataFrame(table_rows).drop(columns=["id"]),
            width="stretch",
            hide_index=True,
        )

        remove_id = st.selectbox(
            "Remove applicant",
            options=[a["id"] for a in applicants],
            format_func=lambda i: next(
                (x.get("label", i) for x in applicants if x.get("id") == i),
                i,
            ),
        )
        if st.button("Remove selected"):
            with st.spinner("Removing applicant..."):
                remove_applicant(email, remove_id)
            st.rerun()

    st.divider()
    st.subheader("My portfolio analytics")
    df = applicants_to_dataframe(portfolio)
    if df.empty:
        st.info("Add at least one complete applicant to see portfolio analytics.")
        return

    rp = resolved_artifact_paths()
    if not rp:
        st.warning("Train the model to score your portfolio.")
        return

    from src.portfolio_dashboard import build_portfolio_bundle

    try:
        progress = st.progress(0, text="Preparing your portfolio analytics...")
        with st.spinner("Scoring your saved applicants..."):
            progress.progress(45, text="Applying trained risk model...")
            kpis, gauge_fig, hist_fig = build_portfolio_bundle(df=df[FEATURE_COLUMNS])
            _apply_chart_transition(gauge_fig)
            _apply_chart_transition(hist_fig)
            progress.progress(100, text="Your analytics are ready.")
        st.success("Your portfolio analytics are up to date.")
        _render_portfolio_kpis_and_charts(
            kpis,
            gauge_fig,
            hist_fig,
            kpis["n_applicants"],
            title_caption=(
                f"Your {kpis['n_applicants']} applicant(s) · "
                "Labels in table above · Default rate N/A for custom portfolios."
            ),
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not score your portfolio: {exc}")
