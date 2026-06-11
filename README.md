<div align="center">

<img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
<img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
<img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
<img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
<img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch" />
<img src="https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn" />
<img src="https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Gemini AI" />

# FinSight AI 🚀

### Enterprise Multi-Cloud FinOps & Autonomous Diagnostic Engine

**A B2B SaaS platform that completely decouples heavy machine learning from live web traffic. It predicts cloud overruns using an ensemble ML pipeline and deploys LangGraph-orchestrated LLM agents to automatically generate root-cause engineering diagnostics.**

</div>

---

## 📖 The Origin Story: The Death of "Cloud Bill Shock"

Every enterprise engineering team experiences "Cloud Bill Shock." A developer spins up a massive GPU instance for an ML experiment on Friday and forgets to tear it down. By Monday, the company has burned $15,000.

Traditional FinOps tools rely on **Static Alarms**. If a team goes over a hardcoded $5,000 budget, an email fires. This creates massive **Alert Fatigue**. Spikes on Cyber Monday are normal; spikes on a random Tuesday are not. Furthermore, when an anomaly *is* detected, it takes engineering managers hours of digging through AWS Cost Explorer to find out exactly *who* caused it and *why*.

I realized the industry needed a system that learns organic company growth dynamically. It needed to isolate structural anomalies without human intervention, and when an anomaly breached the threshold, it needed an autonomous AI agent to interrogate the database and write the incident report for the manager. **FinSight AI was born.**

---

## 🧠 Core Engineering

FinSight AI is not a standard CRUD application. It is a highly scalable, multi-tenant ecosystem architected explicitly to handle massive telemetry datasets without blocking the React client.

### 🏭 Decoupled Two-Universe Architecture

To guarantee sub-50ms load times on the frontend, the platform physically separates ML computation from the web gateway:

* **The Offline Batch Layer:** Asynchronous Python workers wake up nightly, extract telemetry data, run the complex Tri-Layer anomaly detection models in RAM, generate future forecast vectors, and write the evaluated states securely back to the database.
* **The Live Web Layer:** When a CFO logs in, the FastAPI gateway queries pre-computed views from PostgreSQL. Zero machine learning runs during the HTTP request, resulting in instant rendering of the heavy React data visualizations.

### 🛡️ Tri-Layer ML Consensus Engine

To eliminate false alarms, an anomaly must survive a three-tier mathematical consensus before it reaches the SOC dashboard:

* **Tier 1 (Statistical):** STL Decomposition & Residual Z-Scoring immediately catches global, sudden spikes.
* **Tier 2 (Machine Learning):** Multi-variable `Isolation Forests` detect subtle, slow-drifting cost creep.
* **Tier 3 (Deep Learning):** `PyTorch LSTM Autoencoders` calculate sequence reconstruction errors over 14-day memory windows to identify complex pattern breaks.
* **The Ensemble Judge:** A final Python routing script acts as a logic gate, ensuring only authoritative anomalies are flagged.

### 🤖 Autonomous LangGraph RCA Agents

* **Dynamic Scoping:** When an incident is clicked, an autonomous LangGraph state machine is deployed.
* **Context Fetching:** The agent dynamically writes SQL queries scoped *only* to the offending Cloud Provider and Category, pulling transaction logs directly from the database.
* **Gemini Flash Analysis:** Google's Gemini API ingests the raw logs, maps the data back to specific engineering teams (`normalized_team`) and environments (`normalized_env`), and generates a human-readable executive Root Cause Analysis (RCA) report.

### 🏢 Enterprise Multi-Tenancy & Zero-Trust

* **Row-Level Database Isolation:** Customer data is cryptographically isolated via composite PostgreSQL indexing (`organization_id` + `timestamp`).
* **Security operations:** All API routes are protected by stateless, asymmetric JWT signatures and native Bcrypt password hashing.

### 🎨 SOC UI/UX & Data Visualization

* **Datadog/Bloomberg Aesthetics:** A custom true-dark (`#0a0f1c`) CSS theme using glassmorphism, precise SVG linear gradients, and neon focal accents.
* **Recharts Engine:** Custom HTML tooltips and reactive data dots built on top of Recharts, transforming raw data arrays into a premium enterprise control plane.

---

## 🛠️ Technology Stack

* **Frontend:** React.js, Vite, Tailwind CSS (Custom SOC Design System), Recharts
* **Backend Gateway:** FastAPI, Uvicorn, SQLAlchemy, PostgreSQL, Python-Dotenv
* **Machine Learning Pipeline:** PyTorch (LSTMs), LightGBM, Meta Prophet, Scikit-Learn (Isolation Forest), Statsmodels
* **Agentic AI:** LangGraph, LangChain, Google Generative AI SDK (Gemini 2.5 Flash)
* **Security:** JWT (JSON Web Tokens), Bcrypt, FastAPI HTTPBearer

---

## 🗺️ System Architecture Data Flow

```mermaid
graph TD
    subgraph Offline Batch Pipeline [Nightly Data Engineering & ML Pipeline]
        A[Raw Multi-Cloud Telemetry\nAWS, GCP, Azure] -->|normalize_billing.py| B(Unified Relational Data)
        B --> C{Tri-Layer Consensus Engine}
        C -->|anomaly_statistical.py| D[Tier 1: STL Z-Score]
        C -->|anomaly_ml.py| E[Tier 2: Isolation Forest]
        C -->|anomaly_dl.py| F[Tier 3: PyTorch LSTM]
        D --> G[ensemble_eval.py]
        E --> G
        F --> G
        G -->|forecasting_engine.py| H[90-Day Prediction Vector]
        H -->|load_to_db.py| I[(PostgreSQL Hypertable)]
    end

    subgraph Online Web Layer [Real-Time SOC Gateway]
        I <-->|Sub-50ms Queries| J[FastAPI Gateway]
        J <-->|JWT Secured| K[React Enterprise Dashboard]
        
        K -->|Deploy Triage Agent| L{LangGraph State Machine}
        L -->|Context Fetch| I
        L -->|Inference Payload| M[Gemini Flash API]
        M -->|RCA Generation| J
    end
    
    style Offline Batch Pipeline fill:#0f172a,stroke:#334155,stroke-width:2px,color:#fff
    style Online Web Layer fill:#0a0f1c,stroke:#4f46e5,stroke-width:2px,color:#fff
    style I fill:#316192,stroke:#fff,color:#fff
    style K fill:#20232A,stroke:#61DAFB,color:#fff
    style M fill:#8E75B2,stroke:#fff,color:#fff

```

To guarantee a seamless, zero-latency dashboard experience, the data flow is strictly optimized:

1.  **Ingestion:** Background workers extract and normalize raw CSV billing logs from AWS, GCP, and Azure into a unified relational schema.
2.  **The Tri-Layer Gauntlet:** The normalized data is passed through Statistical, Machine Learning, and Deep Learning models. The `ensemble_eval.py` script tallies the votes and logs confirmed anomalies.
3.  **The Forecast:** `forecasting_engine.py` calculates 90-day predictive run-rates using Prophet/LightGBM and commits the vectors to the database.
4.  **Live Gateway Access:** An enterprise user authenticates via Bcrypt/JWT. The FastAPI server queries the pre-computed database and streams it to the React Dashboard in <50ms.
5.  **Autonomous Triage:** The user clicks "Initialize Triage" on a detected anomaly. The LangGraph agent wakes up, fetches the scoped SQL context, and streams a Gemini-generated RCA report directly to the UI.


---

## 🧠 Engineering Design Choices (FAQ)

**Q: Why use WMAPE over standard MAPE for backtesting your forecasting models?** Cloud bills often drop to near-zero on weekends for staging environments. Standard MAPE triggers divide-by-zero errors and aggressively distorts metrics for small environments. FinSight uses Weighted Mean Absolute Percentage Error (WMAPE) to weight absolute errors against the total real spend volume, ensuring our Prophet and LightGBM models scale flawlessly across both $100 serverless functions and $100,000 data warehouses.

**Q: Why LangGraph instead of standard LangChain for the RCA Agent?** Incident response is non-linear. LangChain is excellent for linear RAG pipelines, but FinSight requires conditional state routing. LangGraph allows the triage agent to inspect an anomaly's tag, and if it determines the spike occurred in a `dev` sandbox, it autonomously alters its execution path to prevent false-alarm fatigue before drafting the executive report.

**Q: Why do the ML workers use `os.path.join` and absolute paths instead of relative paths?** When deploying to cloud infrastructure (like Render or AWS Beanstalk), entry points vary and cron jobs often execute from root directories. Dynamic absolute path resolution prevents `FileNotFoundError` crashes when the system scales beyond local development. *(Note: While local development uses files for ML handoffs, the production architecture converts these to isolated `to_sql` SQLAlchemy transactions to survive ephemeral cloud filesystems).*

---

## 🚀 Getting Started (Local Development)

### Prerequisites

* Node.js (v18+)
* Python 3.10+
* Local PostgreSQL Instance
* Google Gemini API Key

### Installation & Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/FinSight-AI.git
cd FinSight-AI

```


2. **Database Initialization:**
Execute the schema inside your PostgreSQL client to generate the multi-tenant UUID tables:
```bash
psql -U postgres -d finops_intelligence -f database/init.sql

```


3. **Backend & Machine Learning Setup:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

```


Create a `.env` file in the `/backend` directory:
```env
DATABASE_URL=postgresql://your_db_user:your_db_password@localhost:5432/finops_intelligence
JWT_SECRET=your_super_secret_cryptographic_key
JWT_ALGORITHM=HS256
GEMINI_API_KEY=your_google_gemini_key

```


4. **Run the Nightly ML Pipeline (Simulated):**
Execute these workers sequentially to generate mock data, evaluate anomalies, and load the state into your database.
```bash
python workers/generate_mock_billing.py
python workers/normalize_billing.py
python workers/anomaly_statistical.py
python workers/anomaly_ml.py
python workers/anomaly_dl.py
python workers/ensemble_eval.py
python workers/ensemble_backtest.py
python workers/patch_forecast_data.py
python workers/load_to_db.py

```


5. **Start the API Gateway:**
```bash
python -m app.main
# Server runs on http://localhost:8000

```


6. **Start the React SOC Frontend:**
```bash
cd ../frontend
npm install

```


Create a `.env` file in the `/frontend` directory:
```env
VITE_API_URL=http://localhost:8000

```


```bash
npm run dev
# Dashboard boots at http://localhost:5173

```

<div align="center"><b>Engineered with ⚡ and ☕ to eliminate multi-cloud volatility.</b></div>