# Backend

FastAPI service for portfolio demo hosting and inference orchestration.

## Run locally

```bash
pip install -r backend/requirements.txt
INFERENCE_MODE=local uvicorn app.main:app --reload --app-dir backend
```

## Inference modes

- `INFERENCE_MODE=mock`: return a safe mock response so you can test the API before real model weights are available
- `INFERENCE_MODE=local`: load local fine-tuned weights through the Python pipeline
- `INFERENCE_MODE=provider`: send requests to an external inference provider through `ProviderInferenceClient`
