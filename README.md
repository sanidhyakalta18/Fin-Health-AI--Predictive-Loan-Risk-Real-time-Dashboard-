# Fin-Health AI

Fin-Health AI is a fintech credit intelligence dashboard for applicant risk scoring, portfolio monitoring, and explainable lending decisions. It combines a Streamlit SaaS-style user experience with a scikit-learn risk model, SHAP explainability, PDF reporting, and deployment-ready configuration for Streamlit Community Cloud and Render.

> This project uses synthetic applicant data by default so it can be deployed safely as a public demo. Replace the synthetic data pipeline with governed production data before using it for real underwriting.

## Fintech Problem Statement

Lenders need fast credit decisions, but opaque model outputs are hard to trust, audit, and explain. Manual review is slow, while black-box automation can create compliance, customer experience, and portfolio-loss risks.

Fin-Health AI addresses this gap by giving credit teams a decision-support workspace that:

- Scores individual applicants for default risk.
- Shows model drivers with SHAP explainability.
- Tracks book-level risk concentration and credit quality.
- Saves applicant histories and personal watchlists.
- Generates PDF risk reports for review workflows.
- Surfaces deployment readiness checks before release.

## Product Overview

Fin-Health AI behaves like a lightweight fintech SaaS product:

- **Risk Analysis**: Enter borrower attributes and receive a risk label, default probability, SHAP explanation, and downloadable PDF.
- **Market Portfolio**: Score the full loan book and monitor default-risk distribution.
- **My Portfolio**: Save private applicant watchlists after local account sign-in.
- **History**: Review past analyses from the local SQLite-backed history store.
- **Deployment Readiness**: Confirm cloud prerequisites directly from the sidebar.

## Dashboard Preview

Add product screenshots to `docs/screenshots/` after your first deployment.

| View | Preview |
|------|---------|
| Home dashboard | `docs/screenshots/home.png` |
| Risk analysis | `docs/screenshots/risk-analysis.png` |
| Portfolio analytics | `docs/screenshots/portfolio.png` |
| SHAP explanation | `docs/screenshots/shap.png` |

Suggested screenshot workflow:

```bash
streamlit run app.py
# Open http://localhost:8501 and capture each main tab.
```

## Screenshots

```text
docs/screenshots/
├── home.png
├── risk-analysis.png
├── portfolio.png
└── shap.png
```

Screenshots are intentionally not committed yet so each deployment can show its own branded URL, data state, and visual polish.

## Feature List

- Applicant-level credit risk scoring.
- Predicted probability of default.
- SHAP-based model explainability.
- AI-style financial narrative insights.
- Portfolio KPI strip and distribution charts.
- Synthetic data generation for safe public demos.
- Local account registration and sign-in.
- Personal applicant portfolio storage.
- SQLite applicant analysis history.
- Downloadable PDF risk reports.
- Environment-backed configuration.
- Deployment readiness checks.
- Streamlit Cloud and Render deployment support.
- First-run bootstrap for missing demo data/model artifacts.

## Architecture

```text
.
├── app.py                         # Streamlit entry point
├── requirements.txt               # Pinned production dependencies
├── runtime.txt                    # Python runtime for cloud platforms
├── Procfile                       # Generic web startup command
├── render.yaml                    # Render blueprint
├── .streamlit/
│   ├── config.toml                # Streamlit runtime/theme config
│   └── secrets.toml.example       # Streamlit Cloud secrets template
├── data/
│   ├── raw/                       # Generated or ingested datasets
│   └── processed/                 # Cleaned feature-ready tables
├── models/                        # Generated model/scaler artifacts
├── docs/screenshots/              # README and portfolio screenshots
└── src/
    ├── bootstrap.py               # First-run demo asset generation
    ├── core/
    │   ├── config.py              # .env/env/Streamlit secrets config
    │   ├── logging_config.py      # Console + file logging
    │   └── paths.py               # Shared project paths
    ├── ml/
    │   ├── preprocessing.py       # Feature schema and validation
    │   └── artifacts.py           # Model/scaler discovery and loading
    ├── ui/
    │   ├── sections.py            # Streamlit screens
    │   └── theme.py               # Dashboard styling
    ├── generate_data.py           # Synthetic loan data generator
    ├── train_model.py             # Model training workflow
    ├── inference.py               # Applicant scoring
    ├── portfolio_dashboard.py     # Portfolio KPIs and charts
    ├── credit_risk_explainer.py   # SHAP explainability
    ├── pdf_report.py              # PDF report generation
    └── readiness.py               # Deployment readiness checks
```

## Machine Learning Workflow

1. **Data generation or ingestion**
   - The demo uses `src/generate_data.py` to create synthetic loan applicants.
   - Production teams can replace this with an approved ingestion pipeline.

2. **Feature validation**
   - `src/ml/preprocessing.py` defines the canonical feature schema:
     - `Age`
     - `Annual_Income`
     - `Credit_Score`
     - `Loan_Amount`
     - `Debt_to_Income_Ratio`
     - `Employment_Years`

3. **Training**
   - `src/train_model.py` trains a Random Forest classifier.
   - A `StandardScaler` and model artifact are saved under `models/`.

4. **Inference**
   - `src/inference.py` loads the model/scaler pair and scores one applicant.
   - The UI receives a risk label and default probability.

5. **Portfolio analytics**
   - `src/portfolio_dashboard.py` scores many applicants and builds KPI charts.

6. **Readiness checks**
   - `src/readiness.py` validates that data, model artifacts, config, and writable paths are present.

## SHAP Explainability

Fin-Health AI uses SHAP to explain model output for individual applicants.

The SHAP workflow:

- Samples background rows from the loan dataset.
- Applies the same scaler used during training.
- Builds a tree explainer for the persisted model.
- Generates a horizontal driver chart for the default-risk class.
- Shows whether each feature increases or lowers predicted default risk.

This makes the dashboard easier to use in credit review, model monitoring, and stakeholder conversations.

## Tech Stack

| Layer | Technology |
|------|------------|
| App framework | Streamlit |
| Visualization | Plotly |
| ML model | scikit-learn Random Forest |
| Explainability | SHAP |
| Data processing | pandas, NumPy |
| Model persistence | joblib |
| Local database | SQLite |
| Configuration | `.env`, environment variables, Streamlit secrets |
| Deployment | Streamlit Community Cloud, Render |

## Local Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Fin-Health-AI
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set:

```env
FIN_HEALTH_ENV=local
FIN_HEALTH_SECRET_KEY=replace-with-a-long-random-secret
FIN_HEALTH_LOG_LEVEL=INFO
```

### 5. Generate Demo Data and Train the Model

```bash
python3 -m src.generate_data
python3 -m src.train_model
python3 -m src.readiness
```

The app also bootstraps missing demo data/model artifacts on first startup, but running these commands locally gives you clear setup feedback.

### 6. Run the Dashboard

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## Startup Configuration

The repository includes production-friendly startup files:

- `.streamlit/config.toml` configures Streamlit server behavior and theme.
- `runtime.txt` pins Python to `3.11.9`.
- `Procfile` provides a generic web process command.
- `render.yaml` defines the Render service blueprint.
- `src/bootstrap.py` creates missing synthetic data and model artifacts on first run.

## Deployment Instructions

### Deploy to Streamlit Community Cloud

1. Push this project to GitHub.
2. Confirm these files are in the repository root:
   - `app.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `runtime.txt`
3. Go to `https://share.streamlit.io`.
4. Choose **Create app**.
5. Select your GitHub repository and branch.
6. Set the entrypoint file to:

```text
app.py
```

7. Open **Advanced settings**.
8. Select Python `3.11`.
9. Add secrets using this template:

```toml
FIN_HEALTH_ENV = "production"
FIN_HEALTH_SECRET_KEY = "replace-with-a-long-random-secret"
FIN_HEALTH_LOG_LEVEL = "INFO"
FIN_HEALTH_SYNTHETIC_ROWS = "1000"
```

10. Click **Deploy**.
11. After launch, open the sidebar and expand **Deployment readiness**.
12. Confirm all checks pass.

### Deploy to Render

#### Option A: Blueprint Deploy

1. Push the repository to GitHub.
2. In Render, choose **New** > **Blueprint**.
3. Connect the GitHub repository.
4. Render reads `render.yaml` automatically.
5. Confirm the service settings:

```text
Runtime: Python
Build command: pip install -r requirements.txt
Start command: streamlit run app.py --server.address=0.0.0.0 --server.port=$PORT --server.headless=true
Health check path: /_stcore/health
```

6. Deploy the service.

#### Option B: Manual Web Service

1. In Render, choose **New** > **Web Service**.
2. Connect the GitHub repository.
3. Set runtime to **Python**.
4. Set build command:

```bash
pip install -r requirements.txt
```

5. Set start command:

```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=$PORT --server.headless=true
```

6. Add environment variables:

```env
PYTHON_VERSION=3.11.9
FIN_HEALTH_ENV=production
FIN_HEALTH_SECRET_KEY=replace-with-a-long-random-secret
FIN_HEALTH_LOG_LEVEL=INFO
FIN_HEALTH_SYNTHETIC_ROWS=1000
```

7. Set health check path:

```text
/_stcore/health
```

8. Deploy and confirm the sidebar readiness checks pass.

## Deployment Notes

- Generated CSVs, SQLite files, user registries, portfolios, logs, and model binaries are ignored by Git.
- Fresh deployments automatically generate synthetic data and train the demo model if artifacts are missing.
- Streamlit caches the SHAP explainer and portfolio scoring bundle for better performance.
- For production lending, train offline in a controlled pipeline and deploy reviewed model artifacts instead of training on app startup.
- Render free instances may sleep when inactive, so first request after idle can be slower.

## Performance Improvements Included

- Pinned dependency versions for reproducible installs.
- Lazy imports for SHAP and dashboard-heavy modules.
- Streamlit caching for SHAP explainer construction.
- Streamlit caching for portfolio scoring.
- First-run artifact bootstrap only when files are missing.
- Centralized feature validation to prevent repeated defensive logic.
- Configurable SHAP background sample count via `FIN_HEALTH_SHAP_BACKGROUND_SAMPLES`.

## Configuration Reference

| Variable | Purpose | Default |
|----------|---------|---------|
| `FIN_HEALTH_ENV` | Runtime environment label | `local` |
| `FIN_HEALTH_SECRET_KEY` | App secret value | `change-me-in-.env` |
| `FIN_HEALTH_LOG_LEVEL` | Logging level | `INFO` |
| `FIN_HEALTH_DATA_DIR` | Data directory | `data` |
| `FIN_HEALTH_LOAN_DATA_PATH` | Loan dataset path | `data/raw/loan_data.csv` |
| `FIN_HEALTH_MODEL_PATH` | Model artifact path | `models/risk_model.pkl` |
| `FIN_HEALTH_SCALER_PATH` | Scaler artifact path | `models/scaler.pkl` |
| `FIN_HEALTH_HIGH_RISK_THRESHOLD` | High-risk cutoff | `0.55` |
| `FIN_HEALTH_SHAP_BACKGROUND_SAMPLES` | SHAP sample size | `400` |
| `FIN_HEALTH_SYNTHETIC_ROWS` | Synthetic dataset size | `1000` |

## Future Improvements

- Replace synthetic data with governed warehouse ingestion.
- Add model registry support for approved artifact promotion.
- Add drift monitoring and calibration dashboards.
- Add role-based access control.
- Add database-backed users and portfolios for hosted multi-user use.
- Add audit logs for credit decision review.
- Add fairness metrics and adverse-action reason codes.
- Add CI checks for linting, tests, and deployment readiness.
- Add Docker deployment for enterprise environments.

## License

Use and extend this project for education, prototyping, and internal fintech analytics. Validate all models, data governance, compliance, and security controls before using in real credit decisions.
