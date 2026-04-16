import { lazy, Suspense, useState } from "react";
import { useHealthCheck } from "./hooks/useHealthCheck";

const DemoPanel = lazy(() =>
  import("./components/DemoPanel").then((m) => ({ default: m.DemoPanel }))
);

export default function App() {
  useHealthCheck();
  const [menuOpen, setMenuOpen] = useState(false);
  const useCases = [
    "Emotion-aware robots and humanoids that respond with more natural timing",
    "Assistive tools for blind or low-vision users to interpret reactions in a room",
    "Support systems for autistic users who want clearer social-emotion cues",
    "Customer research and retail pilots for sentiment around products or displays",
    "Therapy, education, and coaching environments where engagement signals matter"
  ];

  return (
    <div className="app-shell">
      <button className="menu-toggle" type="button" onClick={() => setMenuOpen((value) => !value)}>
        {menuOpen ? "Close menu" : "Use cases"}
      </button>

      <aside className={`side-menu ${menuOpen ? "side-menu-open" : ""}`}>
        <div className="side-menu-header">
          <p className="hero-kicker">Use Cases</p>
          <button className="side-menu-close" type="button" onClick={() => setMenuOpen(false)}>
            ×
          </button>
        </div>
        <div className="use-case-list">
          {useCases.map((item) => (
            <article key={item} className="use-case-card">
              <span className="use-case-dot" />
              <p>{item}</p>
            </article>
          ))}
        </div>
      </aside>

      {menuOpen ? <button className="side-menu-backdrop" type="button" aria-label="Close use cases" onClick={() => setMenuOpen(false)} /> : null}

      <header className="hero">
        <div className="hero-copy">
          <div className="hero-title-row">
            <p className="hero-kicker hero-signature">Chirag Dahiya&apos;s</p>
            <h1>Emotion Detection Tool</h1>
          </div>
          <p className="hero-subtitle">
            A live demo for face bounding boxes and emotion tagging across images, videos, and webcam, with downloadable annotated outputs.
          </p>
        </div>
      </header>

      <main className="page-single">
        <Suspense fallback={<p className="muted">Loading demo...</p>}>
          <DemoPanel />
        </Suspense>
      </main>
    </div>
  );
}
