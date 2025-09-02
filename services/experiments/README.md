# Experiments

This directory contains machine learning models and training scripts for extracting topics from journal entries.

The model examples included here are designed to be as simple as possible for learning and practice purposes. In real-world scenarios, you would typically have dedicated data scientists curating and refining these models over extended periods of time.

## Structure

```
experiments/
├── src/
│   ├── models/
│   │   └── topic_extractor.py      # AdaptiveJournalTopicExtractor class
│   └── training/
│       └── train_topics.py         # Model training and MLflow registration
└── README.md
```

## Quick Start

### Prerequisites
- MLflow server running on `http://localhost:5000`
- Required Python packages: `mlflow`, `scikit-learn`, `pandas`, `numpy`

### Train and Register Models

Scripts are provided in the `training/` folder to train various ML Models.

For example:

```bash
# spin up full stack w/ MLFlow
make up

cd services/experiments/
python -m src.training.train_topics
```

This will:
- Train an adaptive topic extraction model on sample journal data
- Register the model to MLflow as "adaptive_journal_topics" 
- Log training metrics and parameters
- Create topic labels based on common journal themes
