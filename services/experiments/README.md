# Experiments

This directory contains machine learning models and training scripts for extracting topics from journal entries.

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

### Train and Register Model

```bash
cd experiments/
python -m src.training.train_topics
```

This will:
- Train an adaptive topic extraction model on sample journal data
- Register the model to MLflow as "adaptive_journal_topics" 
- Log training metrics and parameters
- Create topic labels based on common journal themes

### Model Features

- **Adaptive topic count**: Extracts 2-6 topics based on entry length
- **Smart topic labeling**: Maps topics to human-readable themes (work, stress, gratitude, etc.)
- **Confidence thresholds**: Only returns high-confidence topics
- **MLflow integration**: Full experiment tracking and model versioning

### Model Usage

The trained model is consumed by the analyzer service via MLflow model registry. No direct imports needed between services.

### Sample Output

```
Short entry (4 words): 1 topics
  - daily_life: 0.456

Medium entry (16 words): 2 topics  
  - work: 0.523
  - accomplishment: 0.334

Long entry (54 words): 4 topics
  - stress: 0.412
  - work: 0.298
  - gratitude: 0.201
  - reflection: 0.089
```
