import numpy as np
import pandas as pd

url = "https://raw.githubusercontent.com/sharmaroshan/Churn-Modelling-Dataset/master/Churn_Modelling.csv"
print("[Loyaltics India] Downloading base dataset...")
df = pd.read_csv(url)

np.random.seed(42)

region_map = {
    'France': 'Maharashtra',
    'Germany': 'Delhi NCR',
    'Spain': 'Karnataka'
}
df['State'] = df['Geography'].map(region_map)

maharashtra_mask = df['State'] == 'Maharashtra'
df.loc[maharashtra_mask, 'State'] = np.random.choice(
    ['Maharashtra', 'Tamil Nadu', 'Gujarat'], size=maharashtra_mask.sum(), p=[0.5, 0.25, 0.25]
)

df['CIBIL_Score'] = ((df['CreditScore'] - 350) / (850 - 350) * (900 - 300) + 300).round().astype(int)
df['Balance_INR'] = (df['Balance'] * 8.5).round(2)
df['Annual_Income_INR'] = (df['EstimatedSalary'] * 15.0 + 150000).round(2)

df_india = pd.DataFrame({
    'Customer_ID': df['CustomerId'],
    'CIBIL_Score': df['CIBIL_Score'],
    'State': df['State'],
    'Gender': df['Gender'],
    'Age': df['Age'],
    'Tenure_Years': df['Tenure'],
    'Balance_INR': df['Balance_INR'],
    'Num_Of_Products': df['NumOfProducts'],
    'Has_Credit_Card': df['HasCrCard'],
    'UPI_Active_User': df['IsActiveMember'],
    'Annual_Income_INR': df['Annual_Income_INR'],
    'Exited': df['Exited']
})

df_india.to_csv("Indian_Bank_Churn.csv", index=False)
print("[Loyaltics India] Saved 'Indian_Bank_Churn.csv' successfully!")
