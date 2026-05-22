import streamlit as st

from investment_advisor import AdvisorServiceError, run_advisor


st.set_page_config(page_title="Indian Financial Advisor", layout="wide")

st.title("Indian Financial Advisor")
st.markdown("Get personalized investment advice based on your financial profile.")

with st.form("advisor_form"):
    age = st.number_input("Age", min_value=18, max_value=100, value=30)
    income = st.number_input("Annual Income (INR)", min_value=0.0, value=500000.0)
    net_worth = st.number_input("Net Worth (INR)", min_value=0.0, value=1000000.0)
    profession = st.text_input("Profession", value="Software Engineer")
    marital_status = st.selectbox("Marital Status", ["single", "married"])
    children = st.number_input("Number of Children", min_value=0, max_value=10, value=0)
    horizon = st.selectbox("Investment Horizon", ["short-term", "medium-term", "long-term"])
    retirement_age = st.number_input("Anticipated Retirement Age", min_value=40, max_value=80, value=60)
    risk = st.selectbox("Risk Tolerance", ["low", "medium", "high"])
    goal = st.selectbox("Investment Goal", ["wealth creation", "money saving", "retirement planning", "tax saving"])
    scope = st.radio("Advice Scope", ["basic", "comprehensive"])

    submitted = st.form_submit_button("Generate Proposal")

if submitted:
    with st.spinner("Generating your personalized investment strategy..."):
        state = {
            "age": age,
            "income": income,
            "net_worth": net_worth,
            "profession": profession,
            "marital_status": marital_status,
            "children": children,
            "horizon": horizon,
            "anticipated_retirement_age": retirement_age,
            "risk": risk,
            "goal": goal,
            "scope": scope,
        }

        try:
            result = run_advisor(state)
        except AdvisorServiceError as exc:
            st.error(str(exc))
            st.info("Open a terminal and run: `ollama serve`. If the model is missing, run: `ollama pull gemma3`.")
            st.stop()

        st.success("Proposal generated!")

        st.subheader("Profile Analysis")
        st.markdown(result["profile"])

        st.subheader("Portfolio Recommendation")
        st.markdown(result["portfolio"])

        st.subheader("Final Proposal")
        st.markdown(result["proposal"])
