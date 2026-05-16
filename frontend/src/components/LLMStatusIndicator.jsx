// components/LLMStatusIndicator.jsx — Real-time LLM provider status
import { useState, useEffect } from "react";
import axios from "../utils/axiosConfig";

export default function LLMStatusIndicator() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await axios.get("/api/llm-status");
        setStatus(response.data);
      } catch (error) {
        console.error("Failed to fetch LLM status:", error);
        setStatus(null);
      } finally {
        setLoading(false);
      }
    };

    checkStatus();
    // Check status every 30 seconds
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700">
        <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
        <span className="text-xs text-slate-400">Checking LLM...</span>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-900/20 border border-red-500/30">
        <div className="w-2 h-2 rounded-full bg-red-500" />
        <span className="text-xs text-red-400">LLM Offline</span>
      </div>
    );
  }

  const { active_provider, active_model, groq, ollama, ollama_model } = status;

  if (!active_provider) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-orange-900/20 border border-orange-500/30">
        <div className="w-2 h-2 rounded-full bg-orange-500" />
        <span className="text-xs text-orange-400">No LLM Available</span>
      </div>
    );
  }

  const isOnline = active_provider === "groq";
  const isOffline = active_provider === "ollama";

  return (
    <div
      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${
        isOnline
          ? "bg-blue-900/20 border-blue-500/30"
          : "bg-green-900/20 border-green-500/30"
      }`}
    >
      <div
        className={`w-2 h-2 rounded-full ${
          isOnline ? "bg-blue-500" : "bg-green-500"
        }`}
      />
      <span
        className={`text-xs ${isOnline ? "text-blue-400" : "text-green-400"}`}
      >
        {isOnline ? "🌐 Online" : "🔒 Offline"} •{" "}
        {active_model?.split(":")[0] || active_model}
      </span>
      {/* Tooltip with full status */}
      <div className="group relative">
        <span className="text-xs text-slate-500 cursor-help">ℹ️</span>
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
          <div>Provider: {active_provider}</div>
          <div>Model: {active_model}</div>
          <div>Groq: {groq ? "✅" : "❌"}</div>
          <div>Ollama: {ollama ? `✅ (${ollama_model})` : "❌"}</div>
        </div>
      </div>
    </div>
  );
}
