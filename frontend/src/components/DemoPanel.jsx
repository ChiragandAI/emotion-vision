import { useEffect, useRef, useState } from "react";
import { getApiBaseUrl, inferImage, inferVideo } from "../services/api";

function drawFacesOnCanvas(canvas, media, faces, color = "#d22f27") {
  if (!canvas || !media || !faces) {
    return;
  }

  const rect = media.getBoundingClientRect();
  const sourceWidth = media.naturalWidth || media.videoWidth || rect.width;
  const sourceHeight = media.naturalHeight || media.videoHeight || rect.height;
  if (!rect.width || !rect.height || !sourceWidth || !sourceHeight) {
    return;
  }

  canvas.width = rect.width;
  canvas.height = rect.height;
  canvas.style.width = `${rect.width}px`;
  canvas.style.height = `${rect.height}px`;

  const scaleX = rect.width / sourceWidth;
  const scaleY = rect.height / sourceHeight;
  const context = canvas.getContext("2d");
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.lineWidth = 3;
  context.strokeStyle = color;
  context.fillStyle = color;
  context.font = "16px sans-serif";

  faces.forEach((face) => {
    const [x1, y1, x2, y2] = face.box;
    const left = x1 * scaleX;
    const top = y1 * scaleY;
    const width = (x2 - x1) * scaleX;
    const height = (y2 - y1) * scaleY;
    const text = `${face.emotion_label} ${(face.emotion_confidence * 100).toFixed(0)}%`;
    const textWidth = context.measureText(text).width;

    context.strokeRect(left, top, width, height);
    context.fillRect(left, Math.max(0, top - 28), textWidth + 14, 22);
    context.fillStyle = "#ffffff";
    context.fillText(text, left + 7, Math.max(16, top - 12));
    context.fillStyle = color;
  });
}

function AnnotatedImage({ src, faces, alt }) {
  const imageRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    const image = imageRef.current;
    const canvas = canvasRef.current;
    if (!image || !canvas || !src) {
      return;
    }

    const render = () => drawFacesOnCanvas(canvas, image, faces);
    if (image.complete) {
      render();
    } else {
      image.onload = render;
    }

    window.addEventListener("resize", render);
    return () => {
      window.removeEventListener("resize", render);
      if (image) {
        image.onload = null;
      }
    };
  }, [src, faces]);

  return (
    <div className="annotated-preview">
      <img ref={imageRef} className="image-preview" src={src} alt={alt} />
      <canvas ref={canvasRef} className="media-overlay" />
    </div>
  );
}

function VideoSampleCard({ frame }) {
  return (
    <div className="video-sample-card">
      <AnnotatedImage src={frame.image_data_url} faces={frame.faces} alt={`Video frame ${frame.frame_index}`} />
      <div className="video-sample-meta">
        <p className="prediction-label">frame {frame.frame_index}</p>
        <p className="prediction-meta">{frame.faces.length} faces</p>
        {frame.faces[0] ? (
          <p className="prediction-meta">
            {frame.faces[0].emotion_label} {(frame.faces[0].emotion_confidence * 100).toFixed(0)}%
          </p>
        ) : null}
      </div>
    </div>
  );
}

export function DemoPanel() {
  const apiBaseUrl = getApiBaseUrl();
  const imageLimitMb = 8;
  const videoLimitMb = 120;
  const webcamLimitMinutes = 3;
  const [mode, setMode] = useState("image");
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileName, setFileName] = useState("No file selected");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");
  const [capturedFrameUrl, setCapturedFrameUrl] = useState("");
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraLoading, setCameraLoading] = useState(false);
  const [cameraMessage, setCameraMessage] = useState("Camera idle");
  const [liveMode, setLiveMode] = useState(false);
  const [cameraAspectRatio, setCameraAspectRatio] = useState(16 / 9);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const streamRef = useRef(null);
  const liveLoopRef = useRef(null);
  const liveTimeoutRef = useRef(null);

  useEffect(() => {
    return () => stopCamera();
  }, []);

  useEffect(() => {
    if (mode !== "webcam") {
      setLiveMode(false);
    }
  }, [mode]);

  useEffect(() => {
    if (!cameraActive || !liveMode || mode !== "webcam") {
      if (liveLoopRef.current) {
        window.clearInterval(liveLoopRef.current);
        liveLoopRef.current = null;
      }
      if (liveTimeoutRef.current) {
        window.clearTimeout(liveTimeoutRef.current);
        liveTimeoutRef.current = null;
      }
      return;
    }

    liveLoopRef.current = window.setInterval(() => {
      captureFrame(true);
    }, 1400);
    liveTimeoutRef.current = window.setTimeout(() => {
      setLiveMode(false);
      setCameraMessage(`Live mode stopped after ${webcamLimitMinutes} minutes`);
    }, webcamLimitMinutes * 60 * 1000);

    return () => {
      if (liveLoopRef.current) {
        window.clearInterval(liveLoopRef.current);
        liveLoopRef.current = null;
      }
      if (liveTimeoutRef.current) {
        window.clearTimeout(liveTimeoutRef.current);
        liveTimeoutRef.current = null;
      }
    };
  }, [cameraActive, liveMode, mode]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
      if (capturedFrameUrl) {
        URL.revokeObjectURL(capturedFrameUrl);
      }
    };
  }, [previewUrl, capturedFrameUrl]);

  function updatePreview(url) {
    setPreviewUrl((current) => {
      if (current) {
        URL.revokeObjectURL(current);
      }
      return url;
    });
  }

  function updateCapturedFrame(url) {
    setCapturedFrameUrl((current) => {
      if (current) {
        URL.revokeObjectURL(current);
      }
      return url;
    });
  }

  function resetUploadState() {
    setSelectedFile(null);
    setFileName("No file selected");
    updatePreview("");
    updateCapturedFrame("");
    setResult(null);
    setError("");
  }

  function clearSelectedMedia() {
    setSelectedFile(null);
    setFileName("No file selected");
    setResult(null);
    setError("");
    updatePreview("");
    if (mode !== "webcam") {
      updateCapturedFrame("");
    }
  }

  function selectMode(nextMode) {
    setMode(nextMode);
    setLiveMode(false);
    setCameraMessage(nextMode === "webcam" ? "Camera idle" : "Webcam paused");
    resetUploadState();
  }

  function handleChange(event) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setSelectedFile(file);
    setFileName(file.name);
    setError("");
    setResult(null);
    updateCapturedFrame("");
    updatePreview(URL.createObjectURL(file));
  }

  async function handleSubmit() {
    if (!selectedFile) {
      setError(`Select a ${mode} file first.`);
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = mode === "image" ? await inferImage(selectedFile) : await inferVideo(selectedFile);
      setResult(data);
    } catch (err) {
      setError(err.message || "Could not run inference.");
    } finally {
      setLoading(false);
    }
  }

  async function startCamera() {
    setError("");
    setCameraLoading(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" },
        audio: false
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
      setCameraMessage("Camera ready");
      clearOverlay();
    } catch (err) {
      setError(err.message || "Could not access webcam.");
      setCameraMessage("Camera unavailable");
    } finally {
      setCameraLoading(false);
    }
  }

  function stopCamera() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
    setLiveMode(false);
    setCameraAspectRatio(16 / 9);
    if (liveTimeoutRef.current) {
      window.clearTimeout(liveTimeoutRef.current);
      liveTimeoutRef.current = null;
    }
    clearOverlay();
  }

  function clearOverlay() {
    const overlay = overlayCanvasRef.current;
    if (!overlay) {
      return;
    }
    const context = overlay.getContext("2d");
    context.clearRect(0, 0, overlay.width, overlay.height);
  }

  function drawLiveOverlay(faces) {
    const overlay = overlayCanvasRef.current;
    const video = videoRef.current;
    if (!overlay || !video || video.videoWidth === 0 || video.videoHeight === 0) {
      return;
    }
    drawFacesOnCanvas(overlay, video, faces, "#d22f27");
  }

  async function captureFrame(silent = false) {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.videoWidth === 0 || video.videoHeight === 0) {
      setError("Camera frame is not ready yet.");
      return;
    }

    if (!silent) {
      setLoading(true);
      setError("");
      setCameraMessage("Capturing frame");
    }

    const maxSide = 960;
    const scale = Math.min(1, maxSide / Math.max(video.videoWidth, video.videoHeight));
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.8));
    if (!blob) {
      if (!silent) {
        setLoading(false);
      }
      setError("Could not capture webcam frame.");
      return;
    }

    const frameFile = new File([blob], "webcam-frame.jpg", { type: "image/jpeg" });
    if (!silent) {
      updateCapturedFrame(URL.createObjectURL(blob));
      setFileName("webcam-frame.jpg");
    }

    try {
      const data = await inferImage(frameFile);
      setResult(data);
      drawLiveOverlay(data.faces);
      setCameraMessage(silent ? "Live webcam active" : "Latest frame analyzed");
    } catch (err) {
      setError(err.message || "Could not run webcam inference.");
      setResult(null);
      setCameraMessage("Frame analysis failed");
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }

  function handleVideoMetadata() {
    const video = videoRef.current;
    if (!video || !video.videoWidth || !video.videoHeight) {
      return;
    }
    setCameraAspectRatio(video.videoWidth / video.videoHeight);
  }

  return (
    <section className="panel panel-feature">
      <div className="panel-heading">
        <h2>Analyze media</h2>
      </div>

      <div className="mode-switch">
        <button className={`chip-button ${mode === "image" ? "chip-active" : ""}`} type="button" onClick={() => selectMode("image")}>
          Image
        </button>
        <button className={`chip-button ${mode === "video" ? "chip-active" : ""}`} type="button" onClick={() => selectMode("video")}>
          Video
        </button>
        <button className={`chip-button ${mode === "webcam" ? "chip-active" : ""}`} type="button" onClick={() => selectMode("webcam")}>
          Webcam
        </button>
      </div>

      {mode === "webcam" ? (
        <div className="panel-block">
          <div className="block-header">
            <p className="block-kicker">Live Webcam</p>
            <p className="block-copy">Capture once or enable live analysis only in webcam mode.</p>
            <p className="limit-text">Limit: live streaming stops automatically after {webcamLimitMinutes} minutes.</p>
          </div>
          <div className="control-stack">
            <div className="camera-row">
              <button className="action-button" type="button" onClick={startCamera} disabled={cameraActive || cameraLoading}>
                {cameraLoading ? "Starting..." : "Start webcam"}
              </button>
              <button className="action-button action-button-muted" type="button" onClick={stopCamera} disabled={!cameraActive}>
                Stop webcam
              </button>
              <button className="action-button" type="button" onClick={() => captureFrame(false)} disabled={!cameraActive || loading}>
                Capture frame
              </button>
              <button className={`action-button ${liveMode ? "" : "action-button-muted"}`} type="button" onClick={() => setLiveMode((value) => !value)} disabled={!cameraActive}>
                {liveMode ? "Stop live" : "Live analyze"}
              </button>
            </div>
            <p className="muted">{cameraMessage}</p>
          </div>
          <div className="camera-preview-wrap" style={{ aspectRatio: `${cameraAspectRatio}` }}>
            <video ref={videoRef} className="camera-preview" autoPlay muted playsInline onLoadedMetadata={handleVideoMetadata} />
            <canvas ref={overlayCanvasRef} className="camera-overlay" />
            <canvas ref={canvasRef} className="camera-canvas" />
          </div>
        </div>
      ) : (
        <div className="panel-block">
          <div className="block-header">
            <p className="block-kicker">Upload</p>
            <p className="block-copy">
              {mode === "image" ? "Select an image and submit once for analysis." : "Select a video and submit once for a rendered output."}
            </p>
            <p className="limit-text">
              {mode === "image" ? `Limit: up to ${imageLimitMb} MB per image.` : `Limit: up to ${videoLimitMb} MB per video.`}
            </p>
          </div>
          <label className="upload-box">
            <input type="file" accept={mode === "image" ? "image/*" : "video/*"} onChange={handleChange} />
            <span>{mode === "image" ? "Select image" : "Select video"}</span>
            <small>{fileName}</small>
          </label>
          <button className="submit-button" type="button" onClick={handleSubmit} disabled={!selectedFile || loading}>
            <span className="submit-button-edge" />
            <span className="submit-button-text">{loading ? "Processing..." : `Submit ${mode}`}</span>
          </button>
        </div>
      )}

      {capturedFrameUrl ? (
        <div className="image-preview-wrap">
          <AnnotatedImage src={capturedFrameUrl} faces={result?.faces || []} alt="Captured webcam frame" />
        </div>
      ) : null}

      {previewUrl ? (
        <div className="image-preview-wrap">
          {mode !== "webcam" ? (
            <button className="media-clear-button" type="button" onClick={clearSelectedMedia} aria-label="Remove selected media">
              ×
            </button>
          ) : null}
          {mode === "image" ? (
            <AnnotatedImage src={previewUrl} faces={result?.faces || []} alt="Selected preview" />
          ) : (
            <video className="image-preview" src={previewUrl} controls />
          )}
        </div>
      ) : null}

      {mode === "video" && result?.annotated_video_url ? (
        <div className="image-preview-wrap">
          <div className="video-output-header">
            <p className="block-kicker">Annotated Output</p>
            <a className="download-link" href={`${apiBaseUrl}${result.annotated_video_url}`} download>
              Download video
            </a>
          </div>
          <video className="image-preview" src={`${apiBaseUrl}${result.annotated_video_url}`} controls />
        </div>
      ) : null}

      {loading ? <p className="muted">Running inference...</p> : null}
      {error ? <p className="error-text">{error}</p> : null}

      {result ? (
        <div className="result-grid">
          <div className="result-summary">
            <p className="metric-label">{mode === "video" ? "Frames" : "Faces"}</p>
            <p className="metric-value">{mode === "video" ? result.frames_processed : result.faces.length}</p>
            <p className="muted">Response mode: {result.mode}</p>
          </div>
          <div className="result-card">
            <p className="result-title">Predictions</p>
            {mode === "video"
              ? result.sample_frames.map((frame) => <VideoSampleCard key={`frame-${frame.frame_index}`} frame={frame} />)
              : result.faces.map((face, index) => (
                  <div key={`${face.emotion_label}-${index}`} className="face-card">
                    <p className="prediction-label">{face.emotion_label}</p>
                    <p className="prediction-meta">confidence {face.emotion_confidence.toFixed(2)}</p>
                  </div>
                ))}
          </div>
        </div>
      ) : (
        <p className="muted">Choose a mode, then upload media or use the webcam.</p>
      )}
    </section>
  );
}
