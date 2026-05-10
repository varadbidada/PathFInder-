// components/CollegeCard.jsx — College card with tier badge and Reddit insights
import { useState } from 'react'
import useCounsellorStore from '../store/counsellorStore'

const TIER_CONFIG = {
    Dream: { color: 'from-violet-600 to-purple-600', bg: 'bg-violet-500/10 border-violet-500/30', icon: '🌟', text: 'text-violet-300' },
    Moderate: { color: 'from-sky-600 to-blue-600', bg: 'bg-sky-500/10 border-sky-500/30', icon: '🎯', text: 'text-sky-300' },
    Safe: { color: 'from-emerald-600 to-teal-600', bg: 'bg-emerald-500/10 border-emerald-500/30', icon: '🛡️', text: 'text-emerald-300' },
}

export default function CollegeCard({ college, showCompare = false }) {
    const [expanded, setExpanded] = useState(false)
    const { selectedForCompare, toggleCompare } = useCounsellorStore()
    const config = TIER_CONFIG[college.tier] || TIER_CONFIG.Safe
    const isSelected = selectedForCompare.includes(college.id)

    return (
        <div
            className={`glass rounded-2xl p-5 border transition-all duration-300 glass-hover ${isSelected ? 'border-indigo-400 glow' : ''
                }`}
        >
            {/* Header */}
            <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                    <span
                        className={`inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full border ${config.bg} ${config.text} mb-2`}
                    >
                        {config.icon} {college.tier}
                    </span>
                    <h3 className="font-bold text-slate-100 text-base leading-tight">{college.name}</h3>
                    <p className="text-sm text-indigo-400 font-medium">{college.branch} Engineering</p>
                </div>
                {showCompare && (
                    <button
                        onClick={() => toggleCompare(college.id)}
                        className={`shrink-0 text-xs px-3 py-1.5 rounded-lg border transition-all duration-200 ${isSelected
                                ? 'bg-indigo-600 border-indigo-500 text-white'
                                : 'border-slate-600 text-slate-400 hover:border-indigo-500 hover:text-indigo-300'
                            }`}
                    >
                        {isSelected ? '✓ Selected' : 'Compare'}
                    </button>
                )}
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 gap-3 mt-4">
                <Stat icon="📍" label="Location" value={college.location} />
                <Stat icon="💰" label="Fees/yr" value={college.annual_fees} />
                <Stat icon="🏆" label="Avg Package" value={college.placement_avg} />
                <Stat icon="📋" label="Cutoff Rank" value={`#${college.cutoff_rank?.toLocaleString()}`} />
            </div>

            {/* Accreditation */}
            <div className="mt-3">
                <span className="text-xs text-slate-500">
                    🏛️ {college.accreditation}
                </span>
            </div>

            {/* Reddit Insights */}
            {college.reddit_insights?.length > 0 && (
                <div className="mt-4">
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
                    >
                        {expanded ? '▼' : '▶'} Student Insights (Reddit)
                    </button>
                    {expanded && (
                        <ul className="mt-2 space-y-1.5">
                            {college.reddit_insights.map((bullet, i) => (
                                <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                                    <span className="text-indigo-400 mt-0.5 shrink-0">•</span>
                                    <span>{bullet.replace(/^•\s*/, '')}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            )}
        </div>
    )
}

function Stat({ icon, label, value }) {
    return (
        <div className="bg-slate-900/40 rounded-xl p-2.5">
            <p className="text-xs text-slate-500 mb-0.5">{icon} {label}</p>
            <p className="text-sm font-semibold text-slate-200 truncate">{value}</p>
        </div>
    )
}
