export function ArchitecturePanel() {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="section-kicker">System Design</p>
        <h2>Frontend to Inference Path</h2>
      </div>
      <ul className="detail-list">
        <li>React handles uploads, webcam UX, result rendering, and portfolio presentation.</li>
        <li>FastAPI acts as the only boundary for uploads, inference, and result formatting.</li>
        <li>The backend can route requests to self-hosted fine-tuned weights or an external inference provider.</li>
        <li>Cloud deployment can begin on free or low-cost tiers and grow later if traffic increases.</li>
      </ul>
    </section>
  );
}

