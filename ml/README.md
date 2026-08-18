# Machine Learning Models

This repository houses three operational ML pipelines:
* **ml1_anomaly_detection**: Trains unsupervised anomaly detection models (e.g. Isolation Forest) on historic pipeline throughput logs.
* **ml2_root_cause**: Analyzes anomaly context and lists critical fields contributing to error rates using association/classification tree algorithms.
* **ml3_sla_prediction**: Predicts processing timeline breaches based on current ingestion queue size, pipeline status, and anomaly severity.

## Training models
To run training pipelines, navigate to the specific model folder and follow the instructions in the readme.
