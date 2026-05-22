import concurrent.futures
import re
from typing import Literal, TypedDict

try:
    import yfinance as yf
except ImportError:
    yf = None


llm = None


class AdvisorServiceError(RuntimeError):
    """Raised when the local AI service cannot generate advice."""


def get_llm():
    global llm
    if llm is None:
        try:
            from langchain_community.llms import Ollama
        except ImportError as exc:
            raise RuntimeError(
                "The Ollama LangChain integration is not installed correctly. "
                "Install the project dependencies before generating advice."
            ) from exc
        llm = Ollama(model="gemma3")
    return llm


def invoke_llm(prompt: str) -> str:
    try:
        return get_llm().invoke(prompt)
    except Exception as exc:
        message = str(exc)
        if "localhost" in message and "11434" in message:
            raise AdvisorServiceError(
                "Ollama is not running on localhost:11434. Start Ollama, make sure the gemma3 model is available, "
                "then generate the proposal again."
            ) from exc
        raise AdvisorServiceError(f"The AI model could not generate a response: {message}") from exc


class InvestorState(TypedDict, total=False):
    age: int
    income: float
    net_worth: float
    profession: str
    horizon: str
    anticipated_retirement_age: int
    risk: str
    goal: str
    scope: Literal["basic", "comprehensive"]
    marital_status: str
    children: int

    # Agent output
    profile: str
    research_plan: str
    market_data: str
    macro_analysis: str
    portfolio: str
    proposal: str


SECTION_NAMES = {
    "profile": "PROFILE_ANALYSIS",
    "research_plan": "RESEARCH_PLAN",
    "macro_analysis": "MACRO_ANALYSIS",
    "portfolio": "PORTFOLIO_RECOMMENDATION",
    "proposal": "FINAL_PROPOSAL",
}


def extract_section(text: str, section_name: str) -> str:
    section_titles = "|".join(re.escape(title) for title in SECTION_NAMES.values())
    pattern = rf"(?s)## {re.escape(section_name)}\s*(.*?)(?=\n## (?:{section_titles})\s*|\Z)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else text.strip()


def analyze_investor_profile(state: InvestorState) -> InvestorState:
    print("Node: Analyze Investor Profile")
    print("Received state:", state.keys())
    prompt = f"""
    You are a financial advisor specializing in the Indian market. Avoid any US-based instruments.
    Focus your recommendations entirely on the Indian financial market and taxation system. Use INR and Indian investment instruments.
    The user provided inputs for income and net worth are in Indian Rupees.
    Analyze this investor's profile:
    - Age: {state['age']}
    - Income: INR {state['income']}
    - Net Worth: INR {state['net_worth']}
    - Profession: {state['profession']}
    - Marital Status: {state['marital_status']}
    - Children: {state['children']}
    - Investment Horizon: {state['horizon']} (Anticipated Retirement Age: {state['anticipated_retirement_age']})
    - Risk Tolerance: {state['risk']}
    - Investment Goal: {state['goal']}

    Provide a detailed analysis of the investor's profile, including their financial situation, risk tolerance, and investment goals.
    Provide a complete and final analysis. Do not ask the user any follow-up questions.
    """
    state["profile"] = invoke_llm(prompt)
    return state


def plan_research(state: InvestorState) -> InvestorState:
    print("Node: Plan Research")
    prompt = f"""
    You are a financial advisor specializing in the Indian market. Avoid any US-based instruments.
    Focus your recommendations entirely on the Indian financial market and taxation system. Use INR and Indian investment instruments.
    Based on the investor's profile, create a research plan that includes:
    {state['profile']}
    - Key areas to research
    - Specific data points to gather
    - Any additional information needed to build a comprehensive investment strategy

    Profile: {state['profile']}
    """
    state["research_plan"] = invoke_llm(prompt)
    return state


def route_based_on_scope(state: InvestorState) -> list[str]:
    print("Router: Checking Scope")
    if state["scope"] == "comprehensive":
        return ["fetch_market_data", "analyze_macro"]
    return ["build_portfolio"]


def get_stock_info(symbol: str) -> str:
    if yf is None:
        return f"{symbol}: market data unavailable because yfinance is not installed."

    stock = yf.Ticker(symbol)
    try:
        fast_info = stock.fast_info
        return f"""
    {symbol}
    - Current Price: INR {fast_info.get('last_price', 'N/A')}
    - Previous Close: INR {fast_info.get('previous_close', 'N/A')}
    - Day High / Low: INR {fast_info.get('day_high', 'N/A')} / INR {fast_info.get('day_low', 'N/A')}
    - Year High / Low: INR {fast_info.get('year_high', 'N/A')} / INR {fast_info.get('year_low', 'N/A')}
    """
    except Exception:
        info = stock.info
    return f"""
    {info.get('shortName', symbol)} ({symbol})
    - Current Price: INR {info.get('regularMarketPrice', 'N/A')}
    - Sector: {info.get('sector', 'N/A')}
    - P/E Ratio: {info.get('trailingPE', 'N/A')}
    - Market Cap: INR {info.get('marketCap', 'N/A')}
    - Day High / Low: INR {info.get('dayHigh', 'N/A')} / INR {info.get('dayLow', 'N/A')}
    """


def fetch_indian_market_data(symbols: list[str] | None = None) -> str:
    if symbols is None:
        symbols = ["^NSEI", "^BSESN", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(get_stock_info, symbols)
    return "\n".join(results)


def fetch_market_data(state: InvestorState) -> dict:
    print("Node: Fetch Market Data")
    market_summary = fetch_indian_market_data()
    prompt = f"""
    {market_summary}
    Use this market data to inform the investment strategy.
    """
    return {"market_data": invoke_llm(prompt)}


def analyze_macro(state: InvestorState) -> dict:
    print("Node: Analyze Macroeconomic Factors")
    result = invoke_llm("Analyze the macroeconomic factors that could impact the investor's portfolio.")
    return {"macro_analysis": result}


def build_portfolio(state: InvestorState) -> InvestorState:
    print("Node: Build Portfolio")
    market_data = state.get("market_data", "No live market data was requested for this basic recommendation.")
    macro_analysis = state.get("macro_analysis", "No separate macroeconomic analysis was requested for this basic recommendation.")
    prompt = f"""
    You are a financial advisor specializing in the Indian market. Avoid any US-based instruments.
    Focus your recommendations entirely on the Indian financial market and taxation system. Use INR and Indian investment instruments.
    Given:
    - Investor Profile: {state['profile']}
    - Market Data: {market_data}
    - Macro Analysis: {macro_analysis}

    The investor's reported income is their total yearly income, but you must:
    1. Deduct an estimated amount for essential living expenses (e.g., 50-60% of monthly income).
    2. Only allocate the remaining disposable income towards investments.
    3. Explain the calculation of disposable income before creating the investment portfolio.

    Recommend a diversified investment portfolio that aligns with the investor's risk tolerance and investment goals.
    Provide a complete and final analysis. Do not ask the user any follow-up questions.
    """
    state["market_data"] = market_data
    state["macro_analysis"] = macro_analysis
    state["portfolio"] = invoke_llm(prompt)
    return state


def generate_proposal(state: InvestorState) -> InvestorState:
    print("Node: Generate Proposal")
    prompt = f"""
    You are a seasoned Indian financial advisor. Do NOT suggest any US-based instruments like 401(k), IRA, Roth accounts, or US ETFs.
    Focus your recommendations entirely on the Indian financial market and taxation system. Use INR and Indian investment instruments.
    IMPORTANT: The income provided is gross yearly income.
    - First, assume 50-60% is allocated to essential living expenses.
    - Use only the remaining disposable income for investment planning.
    - Show the deduction step clearly in your proposal.

    Include:
    - Investment Strategy
    - Expected Returns
    - Risk Management Strategies
    - Recommendations for Future Actions

    Profile: {state['profile']}
    Market Data: {state['market_data']}
    Research Plan: {state['research_plan']}
    Macro Analysis: {state['macro_analysis']}
    Portfolio: {state['portfolio']}

    Instructions:
    1. Do NOT recommend 401(k), IRA, or US-based ETFs.
    2. Base your advice on Indian investment instruments like PPF, ELSS, NPS, Mutual Funds, Direct Stocks (NSE/BSE), FDs, and Indian ETFs.
    3. Consider Indian tax laws, risk profiles, and market conditions.
    4. Provide advice in INR wherever applicable.
    Provide a complete and final analysis. Do not ask the user any follow-up questions.
    """
    state["proposal"] = invoke_llm(prompt)
    return state


def generate_full_advice(state: InvestorState) -> InvestorState:
    print("Node: Generate Full Advice")
    market_data = state.get("market_data", "No live market data was requested for this basic recommendation.")
    macro_context = (
        "Include relevant Indian macroeconomic considerations directly in the macro and final proposal sections."
        if state["scope"] == "comprehensive"
        else "Keep macro comments brief because this is a basic recommendation."
    )
    prompt = f"""
    You are a seasoned Indian financial advisor. Do NOT suggest any US-based instruments like 401(k), IRA, Roth accounts, or US ETFs.
    Focus entirely on the Indian financial market and Indian taxation system. Use INR and Indian investment instruments.

    Investor inputs:
    - Age: {state['age']}
    - Gross Annual Income: INR {state['income']}
    - Net Worth: INR {state['net_worth']}
    - Profession: {state['profession']}
    - Marital Status: {state['marital_status']}
    - Children: {state['children']}
    - Investment Horizon: {state['horizon']}
    - Anticipated Retirement Age: {state['anticipated_retirement_age']}
    - Risk Tolerance: {state['risk']}
    - Investment Goal: {state['goal']}
    - Advice Scope: {state['scope']}

    Market data:
    {market_data}

    Requirements:
    - Assume 50-60% of gross income goes to essential living expenses.
    - Use only the remaining disposable income for investment planning.
    - Show the disposable-income calculation clearly.
    - Recommend Indian instruments such as PPF, ELSS, NPS, mutual funds, direct NSE/BSE stocks, FDs, and Indian ETFs.
    - {macro_context}
    - Provide complete advice. Do not ask follow-up questions.

    Return exactly these Markdown sections, using these headings:
    ## PROFILE_ANALYSIS
    ## RESEARCH_PLAN
    ## MACRO_ANALYSIS
    ## PORTFOLIO_RECOMMENDATION
    ## FINAL_PROPOSAL
    """
    report = invoke_llm(prompt)
    for key, section_name in SECTION_NAMES.items():
        state[key] = extract_section(report, section_name)
    state["market_data"] = market_data
    return state


def build_langgraph_workflow():
    try:
        from langgraph.graph import END, StateGraph
    except ImportError:
        return None

    investor_graph = StateGraph(InvestorState)
    investor_graph.add_node("analyze_profile", analyze_investor_profile)
    investor_graph.add_node("plan_research", plan_research)
    investor_graph.add_node("fetch_market_data", fetch_market_data)
    investor_graph.add_node("analyze_macro", analyze_macro)
    investor_graph.add_node("build_portfolio", build_portfolio)
    investor_graph.add_node("generate_proposal", generate_proposal)

    investor_graph.set_entry_point("analyze_profile")
    investor_graph.add_edge("analyze_profile", "plan_research")
    investor_graph.add_conditional_edges(
        "plan_research",
        route_based_on_scope,
        ["fetch_market_data", "analyze_macro", "build_portfolio"],
    )

    investor_graph.add_edge(["fetch_market_data", "analyze_macro"], "build_portfolio")
    investor_graph.add_edge("build_portfolio", "generate_proposal")
    investor_graph.add_edge("generate_proposal", END)
    return investor_graph.compile()


compiled_investor_graph = build_langgraph_workflow()


def run_python_workflow(state: InvestorState) -> InvestorState:
    if state["scope"] == "comprehensive":
        state.update(fetch_market_data(state))
    else:
        state["market_data"] = "No live market data was requested for this basic recommendation."

    return generate_full_advice(state)


def normalize_state(state: dict) -> InvestorState:
    normalized = dict(state)
    if "marital_status" not in normalized and "martial_status" in normalized:
        normalized["marital_status"] = normalized.pop("martial_status")
    if "anticipated_retirement_age" not in normalized and "anticipated_retirment_age" in normalized:
        normalized["anticipated_retirement_age"] = normalized.pop("anticipated_retirment_age")
    return normalized  # type: ignore


def run_advisor(state: dict) -> dict:
    """Run the investment advisor graph with the provided state."""
    return run_python_workflow(normalize_state(state))
