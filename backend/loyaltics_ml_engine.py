import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import (
    classification_report, roc_auc_score, confusion_matrix, precision_recall_curve
)
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

class LoyalticsIndianFeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy()
        df['BalanceIncomeRatio'] = df['Balance_INR'] / (df['Annual_Income_INR'] + 1.0)
        df['TenureByAge'] = df['Tenure_Years'] / (df['Age'] - 17.0)
        df['CIBILGivenAge'] = df['CIBIL_Score'] / (df['Age'] - 17.0)
        df['EngagementScore'] = (
            df['UPI_Active_User'] * 2 + 
            df['Num_Of_Products'] + 
            df['Has_Credit_Card']
        )
        df['IsZeroBalance'] = (df['Balance_INR'] == 0).astype(int)
        return df

def load_indian_data(csv_path="Indian_Bank_Churn.csv"):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"'{csv_path}' not found! Run 'python create_indian_data.py' first.")
    print(f"[Loyaltics India] Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    if 'Customer_ID' in df.columns:
        df = df.drop(columns=['Customer_ID'])
    return df

def train_loyaltics_model():
    df = load_indian_data()
    X = df.drop(columns=['Exited'])
    y = df['Exited']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    numeric_features = [
        'CIBIL_Score', 'Age', 'Tenure_Years', 'Balance_INR', 'Num_Of_Products', 
        'Annual_Income_INR', 'BalanceIncomeRatio', 'TenureByAge', 
        'CIBILGivenAge', 'EngagementScore'
    ]
    binary_features = ['Has_Credit_Card', 'UPI_Active_User', 'IsZeroBalance']
    categorical_features = ['State', 'Gender']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('bin', 'passthrough', binary_features),
            ('cat', OneHotEncoder(drop='first', handle_unknown='ignore'), categorical_features)
        ]
    )

    pipeline = ImbPipeline(steps=[
        ('feature_engineer', LoyalticsIndianFeatureEngineer()),
        ('preprocessor', preprocessor),
        ('smote', SMOTE(sampling_strategy=0.65, random_state=42)),
        ('classifier', XGBClassifier(
            objective='binary:logistic',
            eval_metric='logloss',
            random_state=42,
            n_jobs=-1
        ))
    ])

    param_distributions = {
        'classifier__n_estimators': [150, 250, 350],
        'classifier__max_depth': [3, 4, 5, 6],
        'classifier__learning_rate': [0.03, 0.05, 0.1],
        'classifier__subsample': [0.8, 0.9, 1.0],
        'classifier__colsample_bytree': [0.8, 0.9, 1.0]
    }

    print("[Loyaltics India] Training XGBoost pipeline on Indian Banking Data...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    search = RandomizedSearchCV(
        pipeline,
        param_distributions=param_distributions,
        n_iter=10,
        scoring='roc_auc',
        cv=cv,
        verbose=1,
        random_state=42,
        n_jobs=-1
    )

    search.fit(X_train, y_train)
    best_model = search.best_estimator_

    y_probs = best_model.predict_proba(X_test)[:, 1]
    precisions, recalls, thresholds = precision_recall_curve(y_test, y_probs)
    f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-8)
    optimal_threshold = thresholds[np.argmax(f1_scores[:-1])]
    y_pred_optimal = (y_probs >= optimal_threshold).astype(int)

    print("\n" + "="*50)
    print("LOYALTICS (INDIAN BANKING) EVALUATION REPORT")
    print("="*50)
    print(f"Test Set ROC-AUC  : {roc_auc_score(y_test, y_probs):.4f}")
    print(f"Optimal Threshold : {optimal_threshold:.4f}")
    print(classification_report(y_test, y_pred_optimal, target_names=['Retained (0)', 'Churned (1)']))

    artifact = {
        'model': best_model,
        'threshold': float(optimal_threshold),
        'feature_columns': list(X.columns)
    }
    joblib.dump(artifact, 'loyaltics_model.pkl')
    print("[Loyaltics India] Saved trained model to 'loyaltics_model.pkl'")

class LoyalticsPredictor:
    def __init__(self, artifact_path='loyaltics_model.pkl'):
        artifact = joblib.load(artifact_path)
        self.model = artifact['model']
        self.threshold = artifact['threshold']

    def predict_customer(self, customer_dict: dict) -> dict:
        df_input = pd.DataFrame([customer_dict])
        churn_prob = float(self.model.predict_proba(df_input)[:, 1][0])
        is_churn = bool(churn_prob >= self.threshold)

        if churn_prob >= 0.70:
            risk_tier = "CRITICAL RISK"
            action = "Assign dedicated Relationship Manager (RM) + Offer zero-AMC Credit Card & higher FD interest rate."
        elif churn_prob >= self.threshold:
            risk_tier = "MODERATE RISK"
            action = "Send WhatsApp/SMS UPI cashback offer & waive minimum average balance (MAB) charges."
        else:
            risk_tier = "LOW RISK"
            action = "Healthy account; eligible for pre-approved Personal Loan / Mutual Fund SIP cross-sell."

        return {
            "churn_probability_pct": round(churn_prob * 100, 2),
            "will_churn": is_churn,
            "risk_tier": risk_tier,
            "recommended_action": action
        }

if __name__ == "__main__":
    train_loyaltics_model()
    predictor = LoyalticsPredictor('loyaltics_model.pkl')
    sample_indian_customer = {
        'CIBIL_Score': 610,
        'State': 'Delhi NCR',
        'Gender': 'Female',
        'Age': 46,
        'Tenure_Years': 2,
        'Balance_INR': 950000.0,
        'Num_Of_Products': 1,
        'Has_Credit_Card': 1,
        'UPI_Active_User': 0,
        'Annual_Income_INR': 1400000.0
    }
    print("\nSAMPLE INDIAN CUSTOMER PREDICTION:")
    for k, v in predictor.predict_customer(sample_indian_customer).items():
        print(f"{k:<24}: {v}")
