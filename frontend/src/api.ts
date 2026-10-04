/**
 * MatchMind Centralized API & WebSocket Configuration Client.
 *
 * Configures base endpoints dynamically based on:
 * 1. Environment variables (`VITE_API_URL`, `VITE_WS_URL`)
 * 2. Host location (local dev Vite port 5173 vs production origin)
 * 3. Protocol negotiation (ws:// vs secure wss://, http:// vs https://)
 */

export const getApiBaseUrl = (): string => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL.replace(/\/$/, "");
  }
  if (typeof window !== "undefined") {
    // If running on Vite dev server (port 5173), direct to FastAPI default port 8000
    if (window.location.port === "5173") {
      return "http://localhost:8000";
    }
    // Deployed or behind reverse proxy
    return window.location.origin;
  }
  return "http://localhost:8000";
};

export const getWsBaseUrl = (): string => {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL.replace(/\/$/, "");
  }
  if (typeof window !== "undefined") {
    if (window.location.port === "5173") {
      return "ws://localhost:8000";
    }
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}`;
  }
  return "ws://localhost:8000";
};

export const apiUrl = (endpoint: string): string => {
  const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${getApiBaseUrl()}${path}`;
};

export const wsUrl = (endpoint: string): string => {
  const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${getWsBaseUrl()}${path}`;
};
