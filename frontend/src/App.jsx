import { lazy, Suspense, useState } from "react";
import { useHealthCheck } from "./hooks/useHealthCheck";

const DemoPanel = lazy(() =>
  import("./components/DemoPanel").then((m) => ({ default: m.DemoPanel }))
);

export default function App() {
  useHealthCheck();
  const [menuOpen, setMenuOpen] = useState(false);
  const [diagramOpen, setDiagramOpen] = useState(false);
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
        {menuOpen ? "Close menu" : "About & use cases"}
      </button>

      <aside className={`side-menu ${menuOpen ? "side-menu-open" : ""}`}>
        <div className="side-menu-header">
          <p className="hero-kicker">About this project</p>
          <button className="side-menu-close" type="button" onClick={() => setMenuOpen(false)}>
            ×
          </button>
        </div>
        <p className="side-menu-about">
          Emotion Vision is an end-to-end face detection and emotion classification system &mdash; a fine-tuned YOLO face detector feeds a ResNet18 emotion classifier, both served behind a FastAPI backend that streams per-frame video progress to the browser over Server-Sent Events. The React + Vite frontend ships on Vercel while the inference service runs on Google Cloud Run, with Docker images built and pushed by GitHub Actions on every commit to <code>main</code>. Cloud infrastructure &mdash; Artifact Registry, Cloud Run, GCS, and Secret Manager &mdash; is provisioned with Terraform, and the API is rate-limited and CORS-restricted at the edge. Training code, Dockerfiles, IaC modules, and CI/CD workflows are all on GitHub.
        </p>
        <button
          type="button"
          className="side-menu-link"
          onClick={() => {
            setDiagramOpen(true);
            setMenuOpen(false);
          }}
        >
          View architecture diagram &rarr;
        </button>

        <p className="hero-kicker side-menu-section">Use cases</p>
        <div className="use-case-list">
          {useCases.map((item) => (
            <article key={item} className="use-case-card">
              <span className="use-case-dot" />
              <p>{item}</p>
            </article>
          ))}
        </div>
      </aside>

      {menuOpen ? <button className="side-menu-backdrop" type="button" aria-label="Close menu" onClick={() => setMenuOpen(false)} /> : null}

      {diagramOpen ? (
        <div className="diagram-modal" role="dialog" aria-label="Architecture diagram">
          <button className="diagram-backdrop" type="button" aria-label="Close diagram" onClick={() => setDiagramOpen(false)} />
          <div className="diagram-content">
            <button className="side-menu-close diagram-close" type="button" onClick={() => setDiagramOpen(false)}>×</button>
            <img src="/architecture.svg" alt="Emotion Vision architecture diagram" />
          </div>
        </div>
      ) : null}

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
        <div className="hero-socials">
          <a className="social-link" href="https://github.com/ChiragandAI/emotion-vision" target="_blank" rel="noopener noreferrer" aria-label="GitHub repository">
            <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
              <path fill="currentColor" d="M12 .5a11.5 11.5 0 0 0-3.64 22.42c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.53-1.34-1.3-1.7-1.3-1.7-1.06-.72.08-.71.08-.71 1.17.08 1.78 1.2 1.78 1.2 1.04 1.78 2.73 1.27 3.4.97.1-.75.4-1.27.74-1.56-2.55-.29-5.24-1.28-5.24-5.7 0-1.26.45-2.29 1.18-3.1-.12-.29-.51-1.46.11-3.05 0 0 .96-.31 3.15 1.18a10.9 10.9 0 0 1 5.74 0c2.18-1.49 3.14-1.18 3.14-1.18.63 1.59.23 2.76.11 3.05.74.81 1.18 1.84 1.18 3.1 0 4.43-2.69 5.4-5.26 5.69.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.55A11.5 11.5 0 0 0 12 .5z"/>
            </svg>
          </a>
          <a className="social-link" href="https://www.linkedin.com/in/chiragdahiya" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn profile">
            <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
              <path fill="currentColor" d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.86 0-2.14 1.45-2.14 2.94v5.67H9.36V9h3.41v1.56h.05c.47-.9 1.63-1.85 3.36-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0z"/>
            </svg>
          </a>
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
