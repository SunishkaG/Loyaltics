import __main__
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from loyaltics_ml_engine import LoyalticsPredictor, LoyalticsIndianFeatureEngineer
from loyaltics_explainer import LoyalticsExplainer

# Map custom transformer into __main__ so joblib/pickle finds it under Uvicorn & Streamlit
__main__.LoyalticsIndianFeatureEngineer = LoyalticsIndianFeatureEngineer

# Initialize FastAPI App
app = FastAPI(
    title="Loyaltics Core Banking AI API",
    description="Enterprise REST API for Indian Retail Bank Churn Prediction, SHAP Explainability, What-If Simulation, and RBI Compliance Audit Logging.",
    version="2.0.0"
)

# Load ML Model & SHAP Explainer once at startup
predictor = LoyalticsPredictor("loyaltics_model.pkl")
explainer = LoyalticsExplainer("loyaltics_model.pkl")
DB_PATH = "loyaltics_audit.db"


# ==========================================
# 1. SQLITE AUDIT LOGGING DATABASE
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            state TEXT,
            cibil_score INTEGER,
            age INTEGER,
            balance_inr REAL,
            upi_active INTEGER,
            churn_prob_pct REAL,
            risk_tier TEXT,
            revenue_at_risk_inr REAL,
            recommended_action TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


def log_prediction_to_db(payload: dict, result: dict, revenue_at_risk: float):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO prediction_logs (
            timestamp, state, cibil_score, age, balance_inr, upi_active,
            churn_prob_pct, risk_tier, revenue_at_risk_inr, recommended_action
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        payload["State"],
        payload["CIBIL_Score"],
        payload["Age"],
        payload["Balance_INR"],
        payload["UPI_Active_User"],
        result["churn_probability_pct"],
        result["risk_tier"],
        revenue_at_risk,
        result["recommended_action"]
    ))
    conn.commit()
    conn.close()


# ==========================================
# 2. PYDANTIC STRICT INPUT VALIDATION
# ==========================================
class CustomerInput(BaseModel):
    CIBIL_Score: int = Field(..., ge=300, le=900, description="Indian CIBIL Score (300 to 900)")
    State: str = Field(..., example="Delhi NCR")
    Gender: str = Field(..., pattern="^(Male|Female)$", example="Female")
    Age: int = Field(..., ge=18, le=100, example=46)
    Tenure_Years: int = Field(..., ge=0, le=50, example=2)
    Balance_INR: float = Field(..., ge=0.0, example=950000.0)
    Num_Of_Products: int = Field(..., ge=1, le=4, example=1)
    Has_Credit_Card: int = Field(..., ge=0, le=1, example=1)
    UPI_Active_User: int = Field(..., ge=0, le=1, example=0)
    Annual_Income_INR: float = Field(..., ge=0.0, example=1400000.0)


# ==========================================
# 3. FINANCIAL & WHAT-IF SIMULATION LOGIC
# ==========================================
def calculate_financial_impact(customer: dict, churn_prob_pct: float) -> dict:
    """
    Estimates annual bank net-interest margin (NIM ~3.5% on deposits) +
    product fee revenue (~Rs 2,500 per product) to compute Expected Revenue at Risk.
    """
    annual_deposit_value = customer["Balance_INR"] * 0.035
    annual_product_fees = customer["Num_Of_Products"] * 2500.0
    estimated_annual_clv = round(annual_deposit_value + annual_product_fees, 2)
    revenue_at_risk = round(estimated_annual_clv * (churn_prob_pct / 100.0), 2)
    return {
        "estimated_annual_customer_value_inr": estimated_annual_clv,
        "expected_revenue_at_risk_inr": revenue_at_risk
    }


def simulate_counterfactuals(customer: dict, base_prob: float) -> List[Dict[str, Any]]:
    """
    Simulates actionable interventions to show how much churn probability drops
    if the bank takes specific retention steps.
    """
    interventions = []

    # Scenario A: Onboard customer onto UPI / Mobile Banking if currently inactive
    if customer["UPI_Active_User"] == 0:
        sim_upi = customer.copy()
        sim_upi["UPI_Active_User"] = 1
        new_prob = predictor.predict_customer(sim_upi)["churn_probability_pct"]
        interventions.append({
            "intervention": "Activate Customer on UPI / Mobile App",
            "new_churn_prob_pct": new_prob,
            "risk_reduction_pct": round(base_prob - new_prob, 2)
        })

    # Scenario B: Bundle a 2nd product (e.g., FD or SIP) if holding only 1 product
    if customer["Num_Of_Products"] == 1:
        sim_prod = customer.copy()
        sim_prod["Num_Of_Products"] = 2
        new_prob = predictor.predict_customer(sim_prod)["churn_probability_pct"]
        interventions.append({
            "intervention": "Cross-Sell 2nd Product (Auto-Sweep FD / SIP)",
            "new_churn_prob_pct": new_prob,
            "risk_reduction_pct": round(base_prob - new_prob, 2)
        })

    # Scenario C: Combined Digital + Product Bundle
    if customer["UPI_Active_User"] == 0 and customer["Num_Of_Products"] == 1:
        sim_both = customer.copy()
        sim_both["UPI_Active_User"] = 1
        sim_both["Num_Of_Products"] = 2
        new_prob = predictor.predict_customer(sim_both)["churn_probability_pct"]
        interventions.append({
            "intervention": "Combined: UPI Activation + 2nd Product Bundle",
            "new_churn_prob_pct": new_prob,
            "risk_reduction_pct": round(base_prob - new_prob, 2)
        })

    return sorted(interventions, key=lambda x: x["risk_reduction_pct"], reverse=True)


# ==========================================
# 4. REST API ENDPOINTS
# ==========================================
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Loyaltics Core Banking AI Engine",
        "optimal_threshold_pct": round(predictor.threshold * 100, 2)
    }


@app.post("/predict")
def predict_and_explain(customer: CustomerInput):
    payload = customer.model_dump()
    
    # 1. Core Prediction
    pred_result = predictor.predict_customer(payload)
    
    # 2. SHAP Explainability
    shap_drivers = explainer.explain_customer(payload, top_n=4)
    
    # 3. Financial Impact (CLV & Revenue at Risk)
    financials = calculate_financial_impact(payload, pred_result["churn_probability_pct"])
    
    # 4. Counterfactual What-If Interventions
    what_if_scenarios = simulate_counterfactuals(payload, pred_result["churn_probability_pct"])
    
    # 5. Log to SQLite Audit Trail
    log_prediction_to_db(payload, pred_result, financials["expected_revenue_at_risk_inr"])

    return {
        "prediction": pred_result,
        "financial_impact": financials,
        "shap_explanations": shap_drivers,
        "what_if_interventions": what_if_scenarios
    }


@app.get("/audit-logs")
def get_recent_audit_logs(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prediction_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"total_returned": len(rows), "audit_logs": rows}