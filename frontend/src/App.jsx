// App.jsx — Main Application Layout
import { useEffect, useState, useRef } from 'react'
import useCounsellorStore from './store/counsellorStore'
import { useSession } from './hooks/useSession'
import ChatWindow from './components/ChatWindow'
import ScoreSidebar from './components/ScoreSidebar'
import CollegeCard from './components/CollegeCard'
import WhatIfSlider from './components/WhatIfSlider'
import InitialForm from './components/InitialForm'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'

// ── Compare Modal ───────────────────────────────────────────────────────────
function CompareModal({ colleges, onClose }) {
  const [a, b] = colleges
  if (!a || !b) return null

  const fields = [
    { label: 'Branch', keyA: () => a.branch, keyB: () => b.branch },
    { label: 'Location', keyA: () => a.location, keyB: () => b.location },
    { label: 'Cutoff Rank', keyA: () => `#${a.cutoff_rank?.toLocaleString()}`, keyB: () => `#${b.cutoff_rank?.toLocaleString()}` },
    { label: 'Annual Fees', keyA: () => a.annual_fees, keyB: () => b.annual_fees },
    { label: 'Avg Package', keyA: () => a.placement_avg, keyB: () => b.placement_avg },
    { label: 'Accreditation', keyA: () => a.accreditation, keyB: () => b.accreditation },
    { label: 'Tier', keyA: () => a.tier, keyB: () => b.tier },
  ]

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass rounded-3xl p-8 max-w-3xl w-full border border-indigo-500/30 shadow-2xl">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold gradient-text">Compare Colleges</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200 transition-colors text-xl">✕</button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className="text-left text-slate-500 pb-4 pr-4 font-medium w-32">Feature</th>
                <th className="text-center pb-4 px-4 text-indigo-300 font-semibold">{a.name}</th>
                <th className="text-center pb-4 px-4 text-violet-300 font-semibold">{b.name}</th>
              </tr>
            </thead>
            <tbody>
              {fields.map(({ label, keyA, keyB }) => (
                <tr key={label} className="border-t border-slate-800">
                  <td className="py-3 pr-4 text-slate-500 font-medium">{label}</td>
                  <td className="py-3 px-4 text-center text-slate-200">{keyA()}</td>
                  <td className="py-3 px-4 text-center text-slate-200">{keyB()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ── Results Panel ───────────────────────────────────────────────────────────
function ResultsPanel() {
  const { report, selectedForCompare, clearCompare } = useCounsellorStore()
  const [tab, setTab] = useState('recommendations')
  const [compareOpen, setCompareOpen] = useState(false)
  const reportRef = useRef(null)

  if (!report) return null

  const { colleges, recommended_branch, branch_summary, student_rank, total_colleges, confidence } = report

  const allColleges = [
    ...(colleges?.Dream || []),
    ...(colleges?.Moderate || []),
    ...(colleges?.Safe || []),
  ]

  // Find college objects for compare
  const compareColleges = selectedForCompare
    .map((id) => allColleges.find((c) => c.id === id))
    .filter(Boolean)

  const handleExportPDF = async () => {
    if (!reportRef.current) return
    const canvas = await html2canvas(reportRef.current, { backgroundColor: '#0f0f1a', scale: 1.5 })
    const pdf = new jsPDF({ orientation: 'portrait', unit: 'px', format: [canvas.width / 1.5, canvas.height / 1.5] })
    pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, canvas.width / 1.5, canvas.height / 1.5)
    pdf.save(`Pathfinder_Report_${recommended_branch}.pdf`)
  }

  return (
    <div className="flex flex-col gap-6 mt-2">
      {/* Summary Banner */}
      <div className="glass rounded-2xl p-6 border border-indigo-500/20">
        <div className="flex flex-wrap items-start gap-4 justify-between">
          <div>
            <p className="text-xs text-indigo-400 uppercase tracking-widest font-semibold mb-1">Your Best-Fit Branch</p>
            <h2 className="text-3xl font-black gradient-text">{recommended_branch} Engineering</h2>
            <p className="text-sm text-slate-400 mt-2 max-w-xl">{branch_summary}</p>
          </div>
          <div className="flex flex-col items-end gap-2 shrink-0">
            <div className="text-right">
              <p className="text-xs text-slate-500">Matched Colleges</p>
              <p className="text-3xl font-bold text-slate-100">{total_colleges}</p>
            </div>
            <div className="flex gap-3">
              {['Dream', 'Moderate', 'Safe'].map((tier) => (
                <span key={tier} className="text-xs text-slate-400">
                  <span className="font-bold text-slate-200">{colleges?.[tier]?.length || 0}</span> {tier}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap gap-3 justify-between items-center">
        <div className="flex gap-1 glass rounded-xl p-1">
          {['recommendations', 'option-entry', 'what-if'].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${tab === t
                  ? 'bg-indigo-600 text-white shadow-lg'
                  : 'text-slate-400 hover:text-slate-200'
                }`}
            >
              {t === 'recommendations' ? '🎓 Colleges' : t === 'option-entry' ? '📋 Option Entry' : '🎯 What-If'}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          {selectedForCompare.length === 2 && (
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
            onClick={handleExportPDF}
            className="px-4 py-2 rounded-xl border border-indigo-500/40 text-indigo-300 hover:bg-indigo-500/10 text-sm font-semibold transition-all"
          >
            📄 Export PDF
          </button>
        </div>
      </div>

      {tab === 'what-if' && <WhatIfSlider />}

      {tab === 'option-entry' && (
        <div className="glass rounded-3xl p-8 border border-indigo-500/20 shadow-2xl mt-4">
          <h3 className="text-xl font-bold gradient-text mb-2">Counselling Option Entry List</h3>
          <p className="text-sm text-slate-400 mb-6">Fill your choices in this exact priority order during your counselling process to maximize your chances.</p>
          <div className="flex flex-col gap-3">
            {report.option_entry_list?.map((college, index) => (
              <div key={college.id} className="flex items-center gap-4 p-4 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-indigo-500/40 transition-colors">
                <div className="w-8 h-8 flex-shrink-0 rounded-full bg-indigo-500/20 text-indigo-300 font-bold flex items-center justify-center">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-slate-200 font-bold truncate">{college.name}</h4>
                  <p className="text-xs text-slate-500 truncate">{college.branch} • {college.location}</p>
                </div>
                <div className="flex-shrink-0 text-right hidden sm:block">
                  <span className={`text-xs px-2 py-1 rounded-lg font-medium ${
                    college.tier === 'Dream' ? 'bg-violet-500/10 text-violet-400' :
                    college.tier === 'Moderate' ? 'bg-sky-500/10 text-sky-400' :
                    'bg-emerald-500/10 text-emerald-400'
                  }`}>
                    {college.tier}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'recommendations' && (
        <div ref={reportRef}>
          {['Dream', 'Moderate', 'Safe'].map((tier) => {
            const tierColleges = colleges?.[tier] || []
            if (tierColleges.length === 0) return null
            const tierColors = {
              Dream: 'text-violet-400',
              Moderate: 'text-sky-400',
              Safe: 'text-emerald-400',
            }
            const tierIcons = { Dream: '🌟', Moderate: '🎯', Safe: '🛡️' }
            return (
              <div key={tier} className="mb-8">
                <h3 className={`text-lg font-bold mb-4 flex items-center gap-2 ${tierColors[tier]}`}>
                  {tierIcons[tier]} {tier} Colleges
                  <span className="text-sm font-normal text-slate-500">({tierColleges.length})</span>
                </h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {tierColleges.map((college) => (
                    <CollegeCard key={college.id} college={college} showCompare={true} />
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {compareOpen && compareColleges.length === 2 && (
        <CompareModal colleges={compareColleges} onClose={() => setCompareOpen(false)} />
      )}
    </div>
  )
}

// ── Main App ────────────────────────────────────────────────────────────────
export default function App() {
  const { sessionId, isComplete } = useCounsellorStore()
  const { startSession, clearSession } = useSession()
  const [view, setView] = useState('landing') // 'landing' | 'form' | 'chat' | 'results'

  useEffect(() => {
    if (isComplete) {
      setTimeout(() => setView('results'), 800)
    }
  }, [isComplete])

  const handleStartClick = () => {
    setView('form')
  }

  const handleFormSubmit = async (formData) => {
    await startSession(formData)
    setView('chat')
  }

  const handleRestart = async () => {
    await clearSession()
    setView('landing')
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'linear-gradient(135deg, #0f0f1a 0%, #0d1117 50%, #0f0f1a 100%)' }}>
      {/* Navbar */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800/60 backdrop-blur-md sticky top-0 z-40 bg-slate-950/80">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-lg">
            🧭
          </div>
          <div>
            <h1 className="text-lg font-black gradient-text leading-none">Pathfinder</h1>
            <p className="text-xs text-slate-500">AI Career Counsellor</p>
          </div>
        </div>
        <nav className="flex items-center gap-3">
          {isComplete && (
            <>
              <button
                onClick={() => setView('chat')}
                className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${view === 'chat' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                  }`}
              >
                💬 Chat
              </button>
              <button
                onClick={() => setView('results')}
                className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${view === 'results' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
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
      </header>

      {/* Hero – no session */}
      {!sessionId && view !== 'form' && (
        <main className="flex flex-col items-center justify-center flex-1 px-6 py-16 text-center">
          {/* Decorative blobs */}
          <div className="absolute top-32 left-1/4 w-72 h-72 bg-indigo-900/20 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute top-48 right-1/4 w-64 h-64 bg-violet-900/20 rounded-full blur-3xl pointer-events-none" />

          <span className="text-7xl mb-6">🧭</span>
          <h2 className="text-5xl font-black gradient-text mb-4">Find Your Path</h2>
          <p className="text-xl text-slate-400 max-w-2xl mb-8 leading-relaxed">
            AI-powered career counselling for Indian engineering students.
            Discover your best-fit branch and colleges in a 5-minute conversation.
          </p>
          <div className="flex flex-wrap gap-4 justify-center mb-12">
            {['🧠 Psychometric Signals', '📊 Rule Engine Scoring', '🎓 30+ Colleges', '🔴 Reddit Insights'].map((f) => (
              <span key={f} className="glass px-4 py-2 rounded-full text-sm text-slate-300 font-medium">
                {f}
              </span>
            ))}
          </div>
          <button
            onClick={handleStartClick}
            className="px-8 py-4 rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-bold text-lg
              hover:from-indigo-500 hover:to-violet-500 active:scale-95 transition-all duration-200 shadow-2xl shadow-indigo-900/50 glow"
          >
            ✨ Start Your Session
          </button>
          <p className="text-xs text-slate-600 mt-4">No sign-up required · Free · Takes ~5 minutes</p>
        </main>
      )}

      {/* Initial Form */}
      {!sessionId && view === 'form' && (
        <InitialForm onSubmit={handleFormSubmit} />
      )}

      {/* Chat layout */}
      {sessionId && view === 'chat' && (
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
      {sessionId && view === 'results' && (
        <main className="flex-1 overflow-y-auto px-4 sm:px-8 py-8 max-w-6xl mx-auto w-full">
          <ResultsPanel />
        </main>
      )}
    </div>
  )
}
