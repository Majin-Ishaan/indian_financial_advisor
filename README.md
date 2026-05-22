# Indian Investment Advisor App

A locally-running, AI-powered investment advisor tailored for the Indian financial market. Enter your financial profile and receive a personalised investment proposal covering portfolio allocation, macroeconomic context, and actionable strategies — all using Indian instruments (mutual funds, PPF, ELSS, NPS, NSE/BSE stocks, FDs).

---

## Features

- **Profile analysis** — assesses age, income, net worth, profession, risk tolerance, and investment goals
- **Research planning** — generates a structured research plan based on your profile
- **Live market data** — fetches real-time NSE/BSE data via `yfinance` (Nifty 50, Sensex, top Indian stocks) in comprehensive mode
- **Macroeconomic analysis** — incorporates Indian macro factors into the recommendation
- **Portfolio recommendation** — builds a diversified allocation using only Indian instruments
- **Final proposal** — delivers a complete investment strategy with expected returns and risk management

Two advice modes:
- **Basic** — profile analysis + portfolio recommendation (faster)
- **Comprehensive** — adds live market data fetch and macroeconomic analysis before building the portfolio

---

## Architecture

The app is built on a multi-node workflow orchestrated by LangGraph (where available), with a pure-Python fallback.

```
User Input (Streamlit)
        │
        ▼
┌─────────────────────┐
│  Analyze Profile    │  ← investor demographics, goals, risk
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Plan Research     │  ← key areas and data points to gather
└────────┬────────────┘
         │
    scope router
   ┌─────┴──────┐
   │ basic      │ comprehensive
   │            ├──────────────────┐
   │            ▼                  ▼
   │   Fetch Market Data    Analyze Macro
   │   (yfinance: NSE/BSE)  (Indian macro factors)
   │            └──────────────────┘
   │                       │
   └───────────────────────┤
                           ▼
              ┌─────────────────────┐
              │   Build Portfolio   │  ← disposable income calc + allocation
              └────────┬────────────┘
                       │
                       ▼
              ┌─────────────────────┐
              │  Generate Proposal  │  ← strategy, returns, risk mgmt
              └─────────────────────┘
```

**Stack:**
- `Streamlit` — frontend UI
- `LangChain` + `Ollama (Gemma 3)` — local LLM inference
- `LangGraph` — agent graph orchestration
- `yfinance` — live Indian market data
- `concurrent.futures` — parallel market data fetching

---

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed and running locally

---

## Setup

**1. Clone the repository**
```bash
git clone https://github.com/Majin-Ishaan/investment_advisor.git
cd investment_advisor
```

**2. Install dependencies**
```bash
pip install streamlit langchain langchain-community langgraph yfinance
```

**3. Pull the Gemma 3 model via Ollama**
```bash
ollama pull gemma3
```

**4. Start the Ollama server** (if not already running)
```bash
ollama serve
```

**5. Run the app**
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Usage

Fill in your financial profile in the sidebar form:

| Field | Description |
|---|---|
| Age | Your current age |
| Annual Income (INR) | Gross yearly income |
| Net Worth (INR) | Total assets minus liabilities |
| Profession | Your current occupation |
| Marital Status | Single or married |
| Number of Children | Dependants |
| Investment Horizon | Short / medium / long-term |
| Anticipated Retirement Age | Target retirement age |
| Risk Tolerance | Low / medium / high |
| Investment Goal | Wealth creation, saving, retirement, or tax saving |
| Advice Scope | Basic or comprehensive |

Click **Generate Proposal** to receive your personalised investment strategy.

---

## Investment Instruments Covered

The advisor recommends only Indian market instruments:

- **Equity** — direct NSE/BSE stocks, equity mutual funds, ELSS (tax-saving)
- **Debt** — FDs, debt mutual funds, government bonds
- **Hybrid** — balanced/hybrid mutual funds
- **Retirement** — PPF, NPS
- **Market indices** — Nifty 50 (`^NSEI`), Sensex (`^BSESN`)

---

## Project Structure

```
investment_advisor/
├── app.py                  # Streamlit UI
├── investment_advisor.py   # Agent nodes, LangGraph workflow, LLM calls
├── investment_tool/
│   ├── basic.ipynb         # Exploratory notebook (basic flow)
│   └── investment_advisor.ipynb  # Exploratory notebook (full flow)
└── .gitignore
```

---

## Known Limitations

- Requires Ollama running locally — no cloud LLM fallback currently
- Live market data depends on `yfinance` availability; missing data falls back gracefully
- LangGraph is optional — the app falls back to a sequential Python workflow if LangGraph is not installed
- Inference latency is sequential per node; async optimisation is in progress

---

## Roadmap

- [ ] Async LLM inference to reduce end-to-end latency
- [ ] ChromaDB vector store for RAG over historical market reports
- [ ] Support for additional models via Ollama (Mistral, LLaMA 3)
- [ ] Export proposal as PDF
- [ ] Docker containerisation

---
