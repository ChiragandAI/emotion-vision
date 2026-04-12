# Fine-Tuning Plan

This project will fine-tune two model families:

- a YOLO-based face detector when domain adaptation is needed
- a CNN-based emotion classifier

## Goal

The point of fine-tuning here is to demonstrate that the project is built on adapted models, not just off-the-shelf inference.

## Where training will happen

Use either:

- Google Colab
- Kaggle Notebooks

GPU is strongly recommended for both training tracks.

## Track 1: YOLO face detector

### Dataset

Start with one of:

- WiderFace
- a YOLO-format custom face dataset

### Training flow

1. Start from a pretrained YOLO11 checkpoint.
2. Convert or prepare the dataset in YOLO format.
3. Create a dataset YAML with train, val, and class definitions.
4. Run baseline inference on validation samples and save examples.
5. Fine-tune the detector for face-only detection only if the baseline detector is not good enough.
6. Evaluate mAP, recall, and qualitative detection behavior.
7. Export the best checkpoint into `models/detection/` if fine-tuning was actually needed.

### What to show in the portfolio

- baseline detector examples
- fine-tuned detector examples if YOLO11 required adaptation
- metric improvement or domain adaptation improvement
- notes on hyperparameters and data choices

## Track 2: Emotion classifier

### Dataset

Start with one or more of:

- RAF-DB
- FER2013
- AffectNet if available

### Training flow

1. Start from a pretrained CNN such as ResNet18.
2. Prepare dataset folders or DataLoader-compatible metadata.
3. Run a baseline evaluation.
4. Fine-tune on the target emotion dataset.
5. Track accuracy, macro F1, and confusion matrix.
6. Compare the baseline checkpoint with the fine-tuned checkpoint.
7. Export the best checkpoint into `models/emotion/`.

### Suggested model progression

1. Train a baseline with `ResNet18`.
2. Improve with `EfficientNet-B2`.
3. Keep the strongest checkpoint for deployment.

## Recommended experiment structure

For each model, record:

- dataset used
- number of epochs
- batch size
- image size
- optimizer
- learning rate
- best validation metric
- final exported checkpoint name

## Deployment handoff

After fine-tuning:

1. export the best weights
2. download them from Colab or Kaggle
3. place them in `models/detection/` and `models/emotion/`
4. point the FastAPI backend at those checkpoints
5. test local inference
6. deploy frontend and backend to a cloud target

## GPU expectation

- Training: yes, assume GPU is needed.
- Image-only demo inference: CPU can be enough if models are lightweight.
- Real-time video inference: GPU is usually preferred.

## Practical recommendation

The strongest portfolio story is:

1. validate YOLO11 out of the box
2. fine-tune the emotion classifier in Colab or Kaggle
3. fine-tune YOLO11 only if the target domain needs it
4. save metrics and visual outputs
5. export the best checkpoints
6. wire the checkpoints into the FastAPI backend
7. deploy the React plus FastAPI app
8. show baseline versus fine-tuned results on the website
