
import pandas as pd
import joblib, json
from datetime import datetime

model = joblib.load('churn_model.pkl')
scaler = joblib.load('scaler.pkl')
with open('model_config.json') as f:
    config = json.load(f)

# Load active customers (replace with your data source)
customers = pd.read_csv('active_customers.csv')
customer_ids = customers['customerID']

# Preprocess: same pipeline as training
# ... feature engineering, encoding, scaling ...

# Predict
probas = model.predict_proba(customers_scaled)[:, 1]

# Build output
output = pd.DataFrame({
    'customerID': customer_ids,
    'churn_probability': probas,
    'risk_level': pd.cut(probas, bins=[0, 0.2, 0.4, 0.6, 1.0],
                          labels=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
    'scored_at': datetime.utcnow().isoformat()
})

high_risk = output[output['risk_level'].isin(['HIGH', 'CRITICAL'])]
output.to_csv(f'predictions_{datetime.utcnow().strftime("%Y%m%d")}.csv', index=False)
high_risk.to_csv('high_risk_customers.csv', index=False)
print(f'Scored: {len(output):,} customers')
print(f'High-risk: {len(high_risk):,}')
