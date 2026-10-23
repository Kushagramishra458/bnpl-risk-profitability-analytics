import streamlit as st
import pandas as pd
import numpy as np
import joblib

st.set_page_config(
    page_title="BNPL Credit Underwriting Engine",
    page_icon="💳",
    layout="wide"
)

# Load pipeline
@st.cache_resource
def load_model():
    return joblib.load('bnpl_model_pipeline.pkl')

pipeline = load_model()

# Header
st.title("💳 BNPL Credit Risk & Profitability Engine")
st.markdown("Automated loan evaluation, default risk scoring, and dynamic limit allocation.")
st.divider()

# Input layout
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📋 Loan & Customer Parameters")
    
    principal = st.number_input(
        "Requested Principal (NGN)", 
        min_value=5000.0, 
        max_value=500000.0, 
        value=35000.0, 
        step=5000.0
    )
    
    credit_score = st.slider(
        "Credit Score", 
        min_value=300, 
        max_value=850, 
        value=620
    )
    
    interest_rate = st.number_input(
        "Monthly Base Interest Rate (decimal, e.g. 0.03 for 3%)", 
        min_value=0.0, 
        max_value=0.20, 
        value=0.03, 
        step=0.005,
        format="%.4f"
    )
    
    tenor_days = st.selectbox("Tenor (Days)", [14, 30, 60, 90], index=1)
    num_installments = st.selectbox("Number of Installments", [1, 2, 3, 4], index=0)

with col2:
    st.subheader("🏪 Merchant & Profile Details")
    
    first_time = st.radio("First Time Customer?", [False, True], index=0)
    
    merchant_category = st.selectbox(
        "Merchant Category", 
        ['groceries', 'furniture', 'electronics', 'fashion', 'health', 'beauty', 'other']
    )
    
    provider = st.selectbox(
        "Lending Provider", 
        ['FairMoney', 'Branch', 'Carbon', 'PayLater', 'Renmoney']
    )
    
    customer_state = st.selectbox(
        "Customer State", 
        ['Lagos', 'Abuja (FCT)', 'Oyo', 'Ekiti', 'Kano', 'Rivers', 'Ogun', 'Other']
    )

st.divider()

# Prediction logic
if st.button("🚀 Evaluate Loan Application", type="primary"):
    input_data = pd.DataFrame([{
        'principal_ngn': principal,
        'interest_rate_monthly': interest_rate,
        'tenor_days': tenor_days,
        'num_installments': num_installments,
        'credit_score': credit_score,
        'first_time_customer': first_time,
        'merchant_category': merchant_category,
        'provider': provider,
        'customer_state': customer_state
    }])
    
    # Probability computation
    prob_default = pipeline.predict_proba(input_data)[0, 1]
    
    # Financial expected value
    potential_interest = principal * interest_rate * (tenor_days / 30)
    expected_profit = ((1 - prob_default) * potential_interest) - (prob_default * principal)

    # Decision Engine Logic
    if prob_default >= 0.12 or expected_profit <= 0:
        decision = "Decline"
        status_color = "red"
        approved_limit = 0.0
        pricing = interest_rate
        mandate = "N/A"
        reason = "Projected default risk exceeds safety threshold or expected profit is negative."
    elif prob_default >= 0.06:
        decision = "Approve with Conditions"
        status_color = "orange"
        approved_limit = min(principal, 50000.0)
        risk_premium = (prob_default - 0.05) * 0.25
        pricing = interest_rate + risk_premium
        mandate = "Minimum 2-3 Installments required (0% historical default pattern)"
        reason = "Borderline risk; requires down-structured installments and risk markup."
    else:
        decision = "Approve"
        status_color = "green"
        approved_limit = max(principal, 100000.0)
        pricing = interest_rate
        mandate = "Flexible"
        reason = "Prime profile; minimal default risk."

    # Render results
    res_col1, res_col2, res_col3, res_col4 = st.columns(4)
    res_col1.metric("Predicted Default Risk", f"{prob_default * 100:.2f}%")
    res_col2.metric("Expected Net Profit", f"₦{expected_profit:,.2f}")
    res_col3.metric("Approved Limit", f"₦{approved_limit:,.2f}")
    res_col4.metric("Risk-Adjusted Monthly Rate", f"{pricing * 100:.2f}%")

    if decision == "Approve":
        st.success(f"**Decision: {decision}** — {reason}")
    elif decision == "Approve with Conditions":
        st.warning(f"**Decision: {decision}** — {reason}")
        st.info(f"👉 **Mandatory Terms:** {mandate}")
    else:
        st.error(f"**Decision: {decision}** — {reason}")