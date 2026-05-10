// components/CollegeCard.jsx — College card with tier badge and Reddit insights
import { useState } from 'react'
import useCounsellorStore from '../store/counsellorStore'

function RedditModal({ college, onClose }) {
    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div className="bg-slate-950 rounded-3xl p-6 max-w-lg w-full border border-[#ff4500]/30 shadow-2xl relative flex flex-col max-h-[90vh]">
                <div className="absolute top-0 right-0 w-32 h-32 bg-[#ff4500]/20 rounded-full blur-3xl pointer-events-none" />
                
                {/* Fixed Header */}
                <div className="flex-shrink-0 relative z-10 mb-4">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            <span className="text-[#ff4500]">Reddit</span> 
                            <span className="text-slate-300 text-sm font-medium border-l border-slate-700 pl-2">Insights</span>
                        </h2>
                        <button onClick={onClose} className="text-slate-400 hover:text-slate-200 transition-colors text-xl">✕</button>
                    </div>
                    
                    <div>
                        <h3 className="text-lg font-bold text-slate-100 mb-1">{college.name}</h3>
                        <p className="text-xs text-slate-400">AI summarized from real student discussions</p>
                    </div>
                </div>

                {/* Scrollable Content */}
                <div className="overflow-y-auto pr-2 relative z-10 custom-scrollbar">
                    <ul className="space-y-4">
                        {college.reddit_insights.map((bullet, i) => {
                            const cleanBullet = bullet.replace(/^•\s*/, '');
                            const urlMatch = cleanBullet.match(/(https?:\/\/[^\s]+)/);
                            
                            return (
                                <li key={i} className="flex items-start gap-3 bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                                    <span className="text-[#ff4500] shrink-0 text-sm">{urlMatch ? '🔗' : '💡'}</span>
                                    <span className="text-sm text-slate-200 leading-relaxed font-medium break-all">
                                        {urlMatch ? (
                                            <a href={urlMatch[0]} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2">
                                                {cleanBullet.replace('Source:', 'Source').trim()}
                                            </a>
                                        ) : (
                                            cleanBullet
                                        )}
                                    </span>
                                </li>
                            )
                        })}
                    </ul>
                </div>
            </div>
        </div>
    )
}

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
                <div className="mt-4 pt-3 border-t border-slate-800/50">
                    <button
                        onClick={() => setExpanded(true)}
                        className="w-full flex items-center justify-center gap-2 py-2 rounded-xl bg-[#ff4500]/10 hover:bg-[#ff4500]/20 text-[#ff4500] border border-[#ff4500]/20 text-xs font-bold transition-all"
                    >
                        💬 View Student Insights
                    </button>
                    {expanded && (
                        <RedditModal college={college} onClose={() => setExpanded(false)} />
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
