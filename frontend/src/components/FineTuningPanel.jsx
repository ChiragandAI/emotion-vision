export function FineTuningPanel() {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="section-kicker">Training Story</p>
        <h2>How Fine-Tuning Is Showcased</h2>
      </div>
      <ul className="detail-list">
        <li>Fine-tune YOLO on a face dataset such as WiderFace or a domain-specific YOLO dataset.</li>
        <li>Fine-tune a CNN classifier such as ResNet18 or EfficientNet-B2 on RAF-DB, AffectNet, or FER2013.</li>
        <li>Compare pretrained baseline metrics with fine-tuned checkpoints.</li>
        <li>Export final weights from Colab or Kaggle for deployment through FastAPI.</li>
      </ul>
    </section>
  );
}

