// components/DebugPanel.jsx — Debug panel to help troubleshoot issues
import { useState, useEffect } from "react";
import useCounsellorStore from "../store/counsellorStore";
import axios from "../utils/axiosConfig";

export default function DebugPanel() {
  const [backendStatus, setBackendStatus] = useState("checking");
  const [llmStatus, setLLMStatus] = useState(null);
  const [showDebug, setShowDebug] = useState(false);

  const { sessionId, messages, branchScores, isComplete, isLoading, report } =
    useCounsellorStore();

  useEffect(() => {
    checkBackendStatus();
    checkLLMStatus();
  }, []);

  const checkBackendStatus = async () => {
    try {
      const response = await axios.get("/health");
      if (response.status === 200) {
        setBackendStatus("connected");
      } else {
        setBackendStatus("error");
      }
    } catch (error) {
      setBackendStatus("disconnected");
      console.error("Backend connection failed:", error);
    }
  };

  const checkLLMStatus = async () => {
    try {
      const response = await axios.get("/api/llm-status");
      setLLMStatus(response.data);
    } catch (error) {
      setLLMStatus({ error: error.message });
    }
  };

  const testSessionCreation = async () => {
    try {
      const response = await axios.post("/session/start", {
        jee_rank: 5000,
        budget_lakh: 3.0,
        preferred_location: "Test",
      });
      console.log("Test session response:", response.data);
      alert(`Test session created: ${response.data.session_id}`);
    } catch (error) {
      console.error("Test session failed:", error);
      alert(`Test session failed: ${error.message}`);
    }
  };

  if (!showDebug) {
    return (
      <button
        onClick={() => setShowDebug(true)}
        className="fixed bottom-4 right-4 px-3 py-2 bg-red-600 text-white rounded-lg text-xs font-mono z-50"
      >
        🐛 Debug
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 w-80 bg-slate-900 border border-slate-700 rounded-lg p-4 text-xs font-mono z-50 max-h-96 overflow-y-auto">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-white font-bold">🐛 Debug Panel</h3>
        <button
          onClick={() => setShowDebug(false)}
          className="text-slate-400 hover:text-white"
        >
          ✕
        </button>
      </div>

      {/* Backend Status */}
      <div className="mb-3">
        <div className="text-slate-400 mb-1">Backend Status:</div>
        <div
          className={`${
            backendStatus === "connected"
              ? "text-green-400"
              : backendStatus === "checking"
                ? "text-yellow-400"
                : "text-red-400"
          }`}
        >
          {backendStatus === "connected"
            ? "✅ Connected"
            : backendStatus === "checking"
              ? "⏳ Checking..."
              : "❌ Disconnected"}
        </div>
      </div>

      {/* LLM Status */}
      <div className="mb-3">
        <div className="text-slate-400 mb-1">LLM Status:</div>
        {llmStatus ? (
          <div className="text-slate-300">
            {llmStatus.error ? (
              <div className="text-red-400">❌ {llmStatus.error}</div>
            ) : (
              <>
                <div>Provider: {llmStatus.active_provider || "None"}</div>
                <div>Model: {llmStatus.active_model || "None"}</div>
                <div>Groq: {llmStatus.groq ? "✅" : "❌"}</div>
                <div>Ollama: {llmStatus.ollama ? "✅" : "❌"}</div>
              </>
            )}
          </div>
        ) : (
          <div className="text-yellow-400">⏳ Checking...</div>
        )}
      </div>

      {/* Frontend State */}
      <div className="mb-3">
        <div className="text-slate-400 mb-1">Frontend State:</div>
        <div className="text-slate-300">
          <div>Session ID: {sessionId ? "✅ Set" : "❌ None"}</div>
          <div>Messages: {messages.length}</div>
          <div>Loading: {isLoading ? "✅" : "❌"}</div>
          <div>Complete: {isComplete ? "✅" : "❌"}</div>
          <div>Report: {report ? "✅" : "❌"}</div>
        </div>
      </div>

      {/* Branch Scores */}
      <div className="mb-3">
        <div className="text-slate-400 mb-1">Branch Scores:</div>
        <div className="text-slate-300">
          {Object.entries(branchScores).map(([branch, score]) => (
            <div key={branch}>
              {branch}: {score.toFixed(2)}
            </div>
          ))}
        </div>
      </div>

      {/* Test Buttons */}
      <div className="space-y-2">
        <button
          onClick={checkBackendStatus}
          className="w-full px-2 py-1 bg-blue-600 text-white rounded text-xs"
        >
          🔄 Refresh Backend
        </button>
        <button
          onClick={checkLLMStatus}
          className="w-full px-2 py-1 bg-green-600 text-white rounded text-xs"
        >
          🤖 Refresh LLM
        </button>
        <button
          onClick={testSessionCreation}
          className="w-full px-2 py-1 bg-purple-600 text-white rounded text-xs"
        >
          🧪 Test Session
        </button>
      </div>
    </div>
  );
}
