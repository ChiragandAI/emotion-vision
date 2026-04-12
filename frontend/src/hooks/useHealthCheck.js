import { useEffect, useState } from "react";
import { getHealth, getApiBaseUrl, getDemoInfo } from "../services/api";

export function useHealthCheck() {
  const [status, setStatus] = useState({ state: "idle", label: "Backend not checked" });
  const [demo, setDemo] = useState({ mode: "unknown", capabilities: [] });

  useEffect(() => {
    let active = true;

    Promise.all([getHealth(), getDemoInfo()])
      .then(([, demoInfo]) => {
        if (active) {
          setStatus({ state: "ready", label: "Backend reachable" });
          setDemo(demoInfo);
        }
      })
      .catch(() => {
        if (active) {
          setStatus({ state: "offline", label: "Backend offline" });
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return { status, apiBaseUrl: getApiBaseUrl(), demo };
}
