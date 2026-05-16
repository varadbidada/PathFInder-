// App.jsx — Enhanced Main Application Layout with Modern UI
import { useEffect, useState, useRef } from "react";
import useCounsellorStore from "./store/counsellorStore";
import { useSession } from "./hooks/useSession";
import ChatWindow from "./components/ChatWindow";
import ScoreSidebar from "./components/ScoreSidebar";
import CollegeCard from "./components/CollegeCard";
import WhatIfSlider from "./components/WhatIfSlider";
import InitialForm from "./components/InitialForm";
import LLMStatusIndicator from "./components/LLMStatusIndicator";
import DebugPanel from "./components/DebugPanel";
import { jsPDF } from "jspdf";
import html2canvas from "html2canvas";

// Log initial app load
console.log("[APP] ========== APPLICATION INITIALIZING ==========");
console.log("[APP] Timestamp:", new Date().toISOString());
console.log("[APP] localStorage keys:", Object.keys(localStorage));
console.log("[APP] sessionStorage keys:", Object.keys(sessionStorage));

// ── Compare Modal ───────────────────────────────────────────────────────────
function CompareModal({ colleges, onClose }) {
  if (!colleges || colleges.length === 0) return null;

  const fields = [
    { label: "Branch", val: (c) => c.branch },
    { label: "Location", val: (c) => c.location },
    { label: "Cutoff Rank", val: (c) => `#${c.cutoff_rank?.toLocaleString()}` },
    {
      label: "Annual Fees",
      val: (c) => `₹${(c.annual_fees / 100000).toFixed(2)}L`,
    },
    {
      label: "Avg Package",
      val: (c) => `₹${(c.placement_avg / 100000).toFixed(2)}L`,
    },
    { label: "Accreditation", val: (c) => c.accreditation },
    { label: "Tier", val: (c) => c.tier },
  ];

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass rounded-3xl p-8 max-w-5xl w-full border border-indigo-500/30 shadow-2xl">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold gradient-text">Compare Colleges</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition-colors text-xl"
          >
            ✕
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-max">
            <thead>
              <tr>
                <th className="text-left text-slate-500 pb-4 pr-4 font-medium w-32">
                  Feature
                </th>
                {colleges.map((c, i) => (
                  <th
                    key={c.id}
                    className={`text-center pb-4 px-4 font-semibold ${i % 2 === 0 ? "text-indigo-300" : "text-violet-300"}`}
                  >
                    {c.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {fields.map(({ label, val }) => (
                <tr key={label} className="border-t border-slate-800">
                  <td className="py-3 pr-4 text-slate-500 font-medium">
                    {label}
                  </td>
                  {colleges.map((c) => (
                    <td
                      key={c.id}
                      className="py-3 px-4 text-center text-slate-200"
                    >
                      {val(c)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Results Panel ───────────────────────────────────────────────────────────
function ResultsPanel() {
  const { report, selectedForCompare, clearCompare } = useCounsellorStore();
  const [tab, setTab] = useState("recommendations");
  const [compareOpen, setCompareOpen] = useState(false);
  const reportRef = useRef(null);

  if (!report) return null;

  const {
    colleges,
    recommended_branch,
    branch_summary,
    student_rank,
    total_colleges,
    confidence,
  } = report;

  const allColleges = [
    ...(colleges?.Dream || []),
    ...(colleges?.Moderate || []),
    ...(colleges?.Safe || []),
  ];

  // Find college objects for compare
  const compareColleges = selectedForCompare
    .map((id) => allColleges.find((c) => c.id === id))
    .filter(Boolean);

  const handleExportPDF = async () => {
    try {
      if (!reportRef.current) return;

      const btn = document.getElementById("export-pdf-btn");
      if (btn) btn.innerText = "⏳ Generating...";

      const canvas = await html2canvas(reportRef.current, {
        backgroundColor: "#0f0f1a",
        scale: 1.5,
        useCORS: true,
        logging: false,
      });
      const pdf = new jsPDF({
        orientation: "portrait",
        unit: "px",
        format: [canvas.width / 1.5, canvas.height / 1.5],
      });
      pdf.addImage(
        canvas.toDataURL("image/png"),
        "PNG",
        0,
        0,
        canvas.width / 1.5,
        canvas.height / 1.5,
      );
      pdf.save(`Pathfinder_Report_${recommended_branch}.pdf`);

      if (btn) btn.innerText = "📄 Export PDF";
    } catch (err) {
      console.error("PDF Export failed:", err);
      const btn = document.getElementById("export-pdf-btn");
      if (btn) btn.innerText = "📄 Export PDF";

      // Fallback to native print dialog
      alert(
        "Advanced PDF generation failed (likely due to strict browser security). Falling back to standard browser print...",
      );
      window.print();
    }
  };

  return (
    <div className="flex flex-col gap-6 mt-2" ref={reportRef}>
      {/* Summary Banner */}
      <div className="glass rounded-2xl p-6 border border-indigo-500/20">
        <div className="flex flex-wrap items-start gap-4 justify-between">
          <div>
            <p className="text-xs text-indigo-400 uppercase tracking-widest font-semibold mb-1">
              Your Best-Fit Branch
            </p>
            <h2 className="text-3xl font-black gradient-text">
              {recommended_branch} Engineering
            </h2>
            <p className="text-sm text-slate-400 mt-2 max-w-xl">
              {branch_summary}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2 shrink-0">
            <div className="text-right">
              <p className="text-xs text-slate-500">Matched Colleges</p>
              <p className="text-3xl font-bold text-slate-100">
                {total_colleges}
              </p>
            </div>
            <div className="flex gap-3">
              {["Dream", "Moderate", "Safe"].map((tier) => (
                <span key={tier} className="text-xs text-slate-400">
                  <span className="font-bold text-slate-200">
                    {colleges?.[tier]?.length || 0}
                  </span>{" "}
                  {tier}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap gap-3 justify-between items-center">
        <div className="flex gap-1 glass rounded-xl p-1">
          {["recommendations", "option-entry", "what-if"].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
                tab === t
                  ? "bg-indigo-600 text-white shadow-lg"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {t === "recommendations"
                ? "🎓 Colleges"
                : t === "option-entry"
                  ? "📋 Option Entry"
                  : "🎯 What-If"}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          {selectedForCompare.length >= 2 && (
            <button
              onClick={() => setCompareOpen(true)}
              className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold transition-all"
            >
              ⚖️ Compare ({selectedForCompare.length})
            </button>
          )}
          {selectedForCompare.length > 0 && (
            <button
              onClick={clearCompare}
              className="px-3 py-2 rounded-xl border border-slate-700 text-slate-400 hover:text-slate-200 text-sm transition-all"
            >
              Clear
            </button>
          )}
          <button
            id="export-pdf-btn"
            onClick={handleExportPDF}
            className="px-4 py-2 rounded-xl border border-indigo-500/40 text-indigo-300 hover:bg-indigo-500/10 text-sm font-semibold transition-all"
          >
            📄 Export PDF
          </button>
        </div>
      </div>

      {tab === "what-if" && <WhatIfSlider />}

      {tab === "option-entry" && (
        <div className="glass rounded-3xl p-8 border border-indigo-500/20 shadow-2xl mt-4">
          <h3 className="text-xl font-bold gradient-text mb-2">
            Counselling Option Entry List
          </h3>
          <p className="text-sm text-slate-400 mb-6">
            Fill your choices in this exact priority order during your
            counselling process to maximize your chances.
          </p>
          <div className="flex flex-col gap-3">
            {report.option_entry_list?.map((college, index) => (
              <div
                key={college.id}
                className="flex items-center gap-4 p-4 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-indigo-500/40 transition-colors"
              >
                <div className="w-8 h-8 flex-shrink-0 rounded-full bg-indigo-500/20 text-indigo-300 font-bold flex items-center justify-center">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-slate-200 font-bold truncate">
                    {college.name}
                  </h4>
                  <p className="text-xs text-slate-500 truncate">
                    {college.branch} • {college.location}
                  </p>
                </div>
                <div className="flex-shrink-0 text-right hidden sm:block">
                  <span
                    className={`text-xs px-2 py-1 rounded-lg font-medium ${
                      college.tier === "Dream"
                        ? "bg-violet-500/10 text-violet-400"
                        : college.tier === "Moderate"
                          ? "bg-sky-500/10 text-sky-400"
                          : "bg-emerald-500/10 text-emerald-400"
                    }`}
                  >
                    {college.tier}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "recommendations" && (
        <div>
          {["Dream", "Moderate", "Safe"].map((tier) => {
            const tierColleges = colleges?.[tier] || [];
            if (tierColleges.length === 0) return null;
            const tierColors = {
              Dream: "text-violet-400",
              Moderate: "text-sky-400",
              Safe: "text-emerald-400",
            };
            const tierIcons = { Dream: "🌟", Moderate: "🎯", Safe: "🛡️" };
            return (
              <div key={tier} className="mb-8">
                <h3
                  className={`text-lg font-bold mb-4 flex items-center gap-2 ${tierColors[tier]}`}
                >
                  {tierIcons[tier]} {tier} Colleges
                  <span className="text-sm font-normal text-slate-500">
                    ({tierColleges.length})
                  </span>
                </h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {tierColleges.map((college) => (
                    <CollegeCard
                      key={college.id}
                      college={college}
                      showCompare={true}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {compareOpen && compareColleges.length >= 2 && (
        <CompareModal
          colleges={compareColleges}
          onClose={() => setCompareOpen(false)}
        />
      )}
    </div>
  );
}

// ── Main App ────────────────────────────────────────────────────────────────
export default function App() {
  const { sessionId, isComplete, messages, branchScores, report } =
    useCounsellorStore();
  const { startSession, clearSession } = useSession();
  const [view, setView] = useState("landing"); // 'landing' | 'form' | 'chat' | 'results'

  // Initialization guard to prevent duplicate form submissions
  const isSubmitting = useRef(false);

  // Log initial state on mount
  useEffect(() => {
    console.log("[APP] ========== COMPONENT MOUNTED ==========");
    console.log("[APP] Initial state:", {
      sessionId,
      isComplete,
      messageCount: messages.length,
      hasReport: !!report,
      branchScores,
      view,
    });

    // Verify clean state on mount
    if (sessionId || messages.length > 0 || report) {
      console.error("[APP] ⚠️ STALE STATE DETECTED ON MOUNT!");
      console.error("[APP] This indicates persistence/hydration bug");
      console.error("[APP] sessionId:", sessionId);
      console.error("[APP] messages:", messages.length);
      console.error("[APP] report:", !!report);

      // FORCE RESET if stale data detected
      console.log("[APP] Force resetting store to clean state...");
      const { resetSession } = useCounsellorStore.getState();
      resetSession();
      console.log("[APP] Force reset complete");
    } else {
      console.log("[APP] ✓ Clean state confirmed on mount");
    }

    return () => {
      console.log("[APP] ========== COMPONENT UNMOUNTING ==========");
    };
  }, []); // Run only once on mount

  useEffect(() => {
    if (isComplete) {
      setTimeout(() => setView("results"), 800);
    }
  }, [isComplete]);

  const handleStartClick = () => {
    setView("form");
  };

  const handleFormSubmit = async (formData) => {
    // Prevent duplicate submissions (React StrictMode protection)
    if (isSubmitting.current) {
      console.warn("[APP] Form already submitting, ignoring duplicate call");
      return;
    }

    isSubmitting.current = true;
    console.log("[APP] Form submitted, starting session...");
    console.log("[APP] Form data:", formData);

    try {
      const newSessionId = await startSession(formData);
      console.log("[APP] Session started successfully:", newSessionId);

      if (newSessionId) {
        console.log("[APP] Changing view to chat...");
        setView("chat");
        console.log("[APP] View changed to chat");
      } else {
        console.error("[APP] No session ID returned");
        alert(
          "Failed to start session. Please check the debug panel for details.",
        );
      }
    } catch (err) {
      console.error("[APP] Form submission failed:", err);
      alert(
        `Session creation failed: ${err.message}. Please check if the backend is running.`,
      );
    } finally {
      // Reset after a delay to allow for proper initialization
      setTimeout(() => {
        isSubmitting.current = false;
      }, 1000);
    }
  };

  const handleRestart = async () => {
    console.log("[RESTART] ========== RESTART INITIATED ==========");
    console.log("[RESTART] User clicked restart button");

    // Step 1: Cancel all pending requests and clear backend session
    console.log("[RESTART] Step 1: Clearing session and cancelling requests");
    await clearSession();

    // Step 2: Verify store is clean
    console.log("[RESTART] Step 2: Verifying store state");
    const { verifyCleanState } = useCounsellorStore.getState();
    const isClean = verifyCleanState();

    if (!isClean) {
      console.error("[RESTART] WARNING: Store not clean after reset!");
    }

    // Step 3: Clear ALL browser storage
    console.log("[RESTART] Step 3: Clearing browser storage");
    try {
      localStorage.clear();
      sessionStorage.clear();
      console.log("[RESTART] Browser storage cleared");
    } catch (err) {
      console.error("[RESTART] Failed to clear storage:", err);
    }

    // Step 4: Reset view to landing
    console.log("[RESTART] Step 4: Resetting view to landing");
    setView("landing");

    // Step 5: Force page reload to ensure complete state reset
    console.log("[RESTART] Step 5: Reloading page in 100ms");
    setTimeout(() => {
      console.log("[RESTART] ========== RELOADING PAGE ==========");
      window.location.reload();
    }, 100);
  };

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{
        background:
          "linear-gradient(135deg, #0f0f1a 0%, #0d1117 50%, #0f0f1a 100%)",
      }}
    >
      {/* Navbar */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800/60 backdrop-blur-md sticky top-0 z-40 bg-slate-950/80">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-lg">
            🧭
          </div>
          <div>
            <h1 className="text-lg font-black gradient-text leading-none">
              Pathfinder
            </h1>
            <p className="text-xs text-slate-500">AI Career Counsellor</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* LLM Status Indicator */}
          <LLMStatusIndicator />

          <nav className="flex items-center gap-3">
            {isComplete && (
              <>
                <button
                  onClick={() => setView("chat")}
                  className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                    view === "chat"
                      ? "bg-indigo-600 text-white"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  💬 Chat
                </button>
                <button
                  onClick={() => setView("results")}
                  className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                    view === "results"
                      ? "bg-indigo-600 text-white"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  🎓 Results
                </button>
              </>
            )}
            {sessionId ? (
              <button
                onClick={handleRestart}
                className="px-4 py-2 rounded-xl border border-slate-700 text-slate-400 hover:text-red-400 hover:border-red-500/40 text-sm transition-all"
              >
                🔄 Restart
              </button>
            ) : (
              <button
                onClick={handleStartClick}
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-semibold text-sm hover:from-indigo-500 hover:to-violet-500 transition-all shadow-lg shadow-indigo-900/40"
              >
                ✨ Start Session
              </button>
            )}
          </nav>
        </div>
      </header>

      {/* Hero – no session */}
      {!sessionId && view !== "form" && (
        <main className="flex flex-col items-center justify-center flex-1 px-6 py-16 text-center">
          {/* Decorative blobs */}
          <div className="absolute top-32 left-1/4 w-72 h-72 bg-indigo-900/20 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute top-48 right-1/4 w-64 h-64 bg-violet-900/20 rounded-full blur-3xl pointer-events-none" />

          <span className="text-7xl mb-6">🧭</span>
          <h2 className="text-5xl font-black gradient-text mb-4">
            Find Your Perfect Engineering Path
          </h2>
          <p className="text-xl text-slate-400 max-w-2xl mb-8 leading-relaxed">
            AI-powered career counselling for Indian engineering students.
            Discover your best-fit branch and colleges through intelligent
            conversation with advanced ML models.
          </p>

          {/* Enhanced Features Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12 max-w-4xl">
            {[
              {
                icon: "🧠",
                title: "Psychometric Analysis",
                desc: "Deep personality insights",
              },
              {
                icon: "🤖",
                title: "Dual-Mode AI",
                desc: "Online & Offline capable",
              },
              {
                icon: "📊",
                title: "ML Predictions",
                desc: "XGBoost cutoff models",
              },
              { icon: "🎓", title: "532+ Colleges", desc: "Real JoSAA data" },
              {
                icon: "🔴",
                title: "Social Insights",
                desc: "Reddit & Twitter analysis",
              },
              {
                icon: "⚡",
                title: "Real-time",
                desc: "Instant recommendations",
              },
              {
                icon: "🔒",
                title: "Privacy First",
                desc: "Works completely offline",
              },
              { icon: "📱", title: "Modern UI", desc: "Responsive design" },
            ].map((feature, i) => (
              <div
                key={i}
                className="glass p-4 rounded-2xl border border-slate-800/50 hover:border-indigo-500/30 transition-all group"
              >
                <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">
                  {feature.icon}
                </div>
                <h3 className="text-sm font-bold text-slate-200 mb-1">
                  {feature.title}
                </h3>
                <p className="text-xs text-slate-500">{feature.desc}</p>
              </div>
            ))}
          </div>

          {/* Model Performance Stats */}
          <div className="glass rounded-2xl p-6 mb-8 border border-indigo-500/20 max-w-2xl">
            <h3 className="text-lg font-bold gradient-text mb-4">
              🎯 AI Model Performance
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-green-400">10.3%</div>
                <div className="text-xs text-slate-500">Prediction Error</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-400">51.9%</div>
                <div className="text-xs text-slate-500">Within 1K Rank</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-violet-400">
                  XGBoost
                </div>
                <div className="text-xs text-slate-500">Best Model</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-indigo-400">5.2K+</div>
                <div className="text-xs text-slate-500">Training Data</div>
              </div>
            </div>
          </div>

          <button
            onClick={handleStartClick}
            className="px-8 py-4 rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-bold text-lg
              hover:from-indigo-500 hover:to-violet-500 active:scale-95 transition-all duration-200 shadow-2xl shadow-indigo-900/50 glow"
          >
            ✨ Start Your AI Counselling Session
          </button>
          <p className="text-xs text-slate-600 mt-4">
            No sign-up required · Free · Takes ~5 minutes · Works offline with
            Ollama
          </p>
        </main>
      )}

      {/* Initial Form */}
      {!sessionId && view === "form" && (
        <InitialForm onSubmit={handleFormSubmit} />
      )}

      {/* Chat layout */}
      {sessionId && view === "chat" && (
        <div className="flex flex-1 min-h-0 gap-0">
          {/* Chat main */}
          <main className="flex flex-col flex-1 min-h-0 border-r border-slate-800/50">
            <ChatWindow />
          </main>
          {/* Score Sidebar */}
          <aside className="hidden lg:flex flex-col border-l border-slate-800/50 bg-slate-950/50">
            <ScoreSidebar />
          </aside>
        </div>
      )}

      {/* Results layout */}
      {sessionId && view === "results" && (
        <main className="flex-1 overflow-y-auto px-4 sm:px-8 py-8 max-w-6xl mx-auto w-full">
          <ResultsPanel />
        </main>
      )}

      {/* Debug Panel */}
      <DebugPanel />
    </div>
  );
}
