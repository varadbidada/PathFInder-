// hooks/useConversation.js — Chat interaction hook with request cancellation
import { useCallback } from "react";
import axios from "../utils/axiosConfig";
import useCounsellorStore from "../store/counsellorStore";

const API = "";

export function useConversation() {
  const { sessionId, messages, addMessage, updateFromResponse, setLoading } =
    useCounsellorStore();

  const sendMessage = useCallback(
    async (text) => {
      if (!sessionId || !text.trim()) return;

      addMessage({ role: "user", content: text, ts: Date.now() });
      setLoading(true);

      // Add a helpful message for first-time Ollama users
      const isFirstMessage = messages.length <= 2; // Only intro messages
      if (isFirstMessage) {
        addMessage({
          role: "assistant",
          content:
            "⏳ Processing your message with Ollama AI... This may take 10-20 seconds for the first response.",
          ts: Date.now(),
        });
      }

      try {
        const res = await axios.post(
          `${API}/chat`,
          {
            session_id: sessionId,
            user_message: text,
          },
          {
            timeout: 90000, // 90 seconds for Ollama responses
          },
        );

        const data = res.data;
        updateFromResponse(data);

        // The backend returns assistant_message, not question_text
        const responseText =
          data.assistant_message ||
          data.next_question ||
          "I'm processing your response...";

        addMessage({
          role: "assistant",
          content: responseText,
          ts: Date.now(),
        });

        return data;
      } catch (err) {
        if (axios.isCancel(err)) {
          console.log("[CHAT] Request cancelled:", err.message);
          return;
        }

        console.error("[CHAT] Error:", err);

        let errMsg = "⚠️ Something went wrong. Please try again.";

        if (err.code === "ECONNABORTED" || err.message.includes("timeout")) {
          errMsg =
            "⏳ The AI is taking longer than expected. This is normal for the first response with Ollama. Please wait a moment and try again.";
        } else if (err.response?.status === 500) {
          errMsg =
            "🤖 The AI service is processing your request. Please wait a moment and try again.";
        } else if (err.response?.data?.detail) {
          errMsg = err.response.data.detail;
        }

        addMessage({ role: "assistant", content: errMsg, ts: Date.now() });
      } finally {
        setLoading(false);
      }
    },
    [sessionId, addMessage, updateFromResponse, setLoading],
  );

  const runWhatIf = useCallback(
    async (rank) => {
      if (!sessionId) return null;
      try {
        const res = await axios.post(`${API}/what-if`, {
          session_id: sessionId,
          hypothetical_rank: rank,
        });
        return res.data;
      } catch (err) {
        console.error("[WHAT_IF] Failed:", err);
        return null;
      }
    },
    [sessionId],
  );

  return { sendMessage, runWhatIf };
}
