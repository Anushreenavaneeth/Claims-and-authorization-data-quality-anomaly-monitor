# Machine Learning Architecture

The ML models operate across three distinct domains:
1. **ML1 (Anomaly Detection)**: Isolation Forest or Autoencoders to evaluate incoming data batches and tag volumetric/statistical anomalies.
2. **ML2 (Root Cause)**: Classification or association rules flagging the root fields causing data quality failures.
3. **ML3 (SLA Prediction)**: Regression models estimating remediation latency and processing time to predict breach risks.
