import shap
import joblib
import pandas as pd
from loyaltics_ml_engine import LoyalticsIndianFeatureEngineer

class LoyalticsExplainer:
    def __init__(self, artifact_path='loyaltics_model.pkl'):
        artifact = joblib.load(artifact_path)
        self.pipeline = artifact['model']
        
        self.feat_eng = self.pipeline.named_steps['feature_engineer']
        self.preprocessor = self.pipeline.named_steps['preprocessor']
        self.xgb_model = self.pipeline.named_steps['classifier']
        
        self.explainer = shap.TreeExplainer(self.xgb_model)
        self.feature_names = self.preprocessor.get_feature_names_out()

    def explain_customer(self, customer_dict: dict, top_n: int = 3):
        df_raw = pd.DataFrame([customer_dict])
        df_eng = self.feat_eng.transform(df_raw)
        X_transformed = self.preprocessor.transform(df_eng)
        
        shap_values = self.explainer.shap_values(X_transformed)[0]
        
        contributions = pd.DataFrame({
            'Feature': [f.split('__')[-1] for f in self.feature_names],
            'SHAP_Impact': shap_values
        }).sort_values(by='SHAP_Impact', key=abs, ascending=False)
        
        return contributions.head(top_n).to_dict(orient='records')

if __name__ == "__main__":
    explainer = LoyalticsExplainer()
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
    print("\nTop Churn Drivers for Indian Customer:")
    for driver in explainer.explain_customer(sample_indian_customer):
        direction = "Increases Churn Risk" if driver['SHAP_Impact'] > 0 else "Reduces Churn Risk"
        print(f"- {driver['Feature']}: {driver['SHAP_Impact']:+.3f} ({direction})")
