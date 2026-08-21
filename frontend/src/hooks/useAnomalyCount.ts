/**
 * useAnomalyCount
 * ---------------
 * Fetches the live OPEN anomaly count from the REST API on mount,
 * then keeps it updated via the WebSocket feed.
 *
 * Used by DashboardShell to drive the sidebar badge.
 */
import { useState, useEffect, useRef } from 'react';
import api from '../services/api';

export function useAnomalyCount() {
  const [openCount, setOpenCount] = useState<number>(0);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Initial REST fetch
  useEffect(() => {
    api.get('/anomalies?status=OPEN&page_size=1')
      .then(r => setOpenCount(r.data.total ?? 0))
      .catch(() => {}); // silent — sidebar badge is non-critical
  }, []);

  // WebSocket for live updates
  useEffect(() => {
    const base = (import.meta.env.VITE_API_URL || 'http://localhost:8000')
      .replace('http', 'ws');
    const ws = new WebSocket(`${base}/anomalies/ws`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.type === 'NEW_ANOMALY') {
          setOpenCount(c => c + 1);
        }
        if (msg.type === 'STATUS_CHANGED' && msg.data.status === 'RESOLVED') {
          setOpenCount(c => Math.max(0, c - 1));
        }
      } catch { /* ignore malformed */ }
    };

    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    // Heartbeat ping every 30s to keep connection alive
    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('PING');
    }, 30_000);

    return () => {
      clearInterval(ping);
      ws.close();
    };
  }, []);

  return { openCount, connected };
}
