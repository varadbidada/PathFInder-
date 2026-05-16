// hooks/useSession.js — Session management hook with request cancellation
import { useCallback, useRef } from "react";
import axios from "../utils/axiosConfig";
import { cancelAllRequests } from "../utils/axiosConfig";
import useCounsellorStore from "../store/counsellorStore";

const API = "";

export function useSession() {
  const {
    sessionId,
    setSessionId,
    addMessage,
    updateFromResponse,
    setLoading,
    resetSession,
  } = useCounsellorStore();

  // Initialization guard to prevent duplicate session creation
  const isInitializing = useRef(false);
  const lastSessionId = useRef(null);

  const startSession = useCallback(
    async (formData = {}) => {
      // Prevent duplicate initialization
      if (isInitializing.current) {
        console.warn(
          "[SESSION_START] Already initializing, skipping duplicate call",
        );
        return lastSessionId.current;
      }

      // Prevent re-initialization of same session
      if (sessionId && sessionId === lastSessionId.current) {
        console.warn("[SESSION_START] Session already exists:", sessionId);
        return sessionId;
      }

      isInitializing.current = true;
      console.log("[SESSION_START] ========== STARTING NEW SESSION ==========");

      try {
        setLoading(true);

        const res = await axios.post(`${API}/session/start`, formData);
        const { session_id, message, first_question } = res.data;

        console.log("[SESSION_START] New session created:", session_id);
        console.log("[SESSION_START] Adding intro messages...");

        setSessionId(session_id);
        lastSessionId.current = session_id;

        // Add messages with unique timestamps to prevent duplicates
        const baseTime = Date.now();
        addMessage({ role: "assistant", content: message, ts: baseTime });
        addMessage({
          role: "assistant",
          content: first_question,
          ts: baseTime + 1,
        });

        console.log("[SESSION_START] Session initialization complete");
        return session_id;
      } catch (err) {
        if (axios.isCancel(err)) {
          console.log("[SESSION_START] Request cancelled");
          return;
        }
        console.error("[SESSION_START] Failed to start session:", err);
        addMessage({
          role: "assistant",
          content:
            "⚠️ Failed to connect to the server. Make sure the backend is running.",
          ts: Date.now(),
        });
      } finally {
        setLoading(false);
        isInitializing.current = false;
      }
    },
    [sessionId, setSessionId, addMessage, setLoading],
  );

  const clearSession = useCallback(async () => {
    console.log("[RESTART] ========== clearSession() START ==========");
    console.log("[RESTART] Current sessionId:", sessionId);

    // Reset initialization guards
    isInitializing.current = false;
    lastSessionId.current = null;

    // Cancel ALL active requests globally
    console.log("[RESTART] Cancelling all active requests...");
    cancelAllRequests("Session restart - preventing stale context");

    // Delete session on backend
    if (sessionId) {
      try {
        console.log("[RESTART] Deleting backend session:", sessionId);
        await axios.delete(`${API}/session/${sessionId}`);
        console.log("[RESTART] Backend session deleted successfully");
      } catch (err) {
        console.warn("[RESTART] Failed to delete backend session:", err);
      }
    } else {
      console.log("[RESTART] No sessionId to delete");
    }

    // Clear frontend state
    console.log("[RESTART] Calling resetSession() on store...");
    resetSession();
    console.log("[RESTART] ========== clearSession() COMPLETE ==========");
  }, [sessionId, resetSession]);

  return { sessionId, startSession, clearSession };
}
