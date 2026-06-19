// components/ScoreSidebar.jsx — Animated branch score bar chart
import { useEffect, useState } from 'react'
import useCounsellorStore from '../store/counsellorStore'
import ConfidenceMeter from './ConfidenceMeter'

const BRANCH_COLORS = {
    CS: 'from-indigo-500 to-violet-500',
    Electronics: 'from-sky-500 to-cyan-400',
    Mechanical: 'from-orange-500 to-amber-400',
    Civil: 'from-emerald-500 to-teal-400',
    Medical: 'from-rose-500 to-pink-400',
}

const BRANCH_ICONS = {
    CS: '💻',
    Electronics: '⚡',
    Mechanical: '⚙️',
    Civil: '🏗️',
    Medical: '🩺',
}

export default function ScoreSidebar() {
    const { branchScores, overallConfidence, currentCategory } = useCounsellorStore()
    const [animatedScores, setAnimatedScores] = useState(branchScores)

    useEffect(() => {
        const timer = setTimeout(() => setAnimatedScores(branchScores), 50)
        return () => clearTimeout(timer)
    }, [branchScores])

    const topBranch = Object.entries(branchScores).sort(([, a], [, b]) => b - a)[0]?.[0] || 'CS'

    const categoryLabels = {
        INTEREST: '🎯 Interests',
        APTITUDE: '🧠 Aptitude',
        RANK: '📊 Rank',
        BUDGET: '💰 Budget',
        LOCATION: '📍 Location',
        TIE_BREAKER: '⚡ Tie-breaker',
        CONFIRMATION: '✅ Confirming',
    }

    const prettyCategory =
        categoryLabels[currentCategory] ||
        currentCategory
            .toLowerCase()
            .split('_')
            .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
            .join(' ')

    return (
        <aside className="w-72 flex flex-col gap-6 p-5">
            {/* Header */}
            <div>
                <h2 className="text-lg font-bold gradient-text">Branch Fit Score</h2>
                <p className="text-xs text-slate-500 mt-1">Updates with each answer</p>
            </div>

            {/* Confidence Ring */}
            <div className="glass rounded-2xl p-4 flex justify-center">
                <ConfidenceMeter confidence={overallConfidence} branch={topBranch} />
            </div>

            {/* Score Bars */}
            <div className="glass rounded-2xl p-4 flex flex-col gap-3">
                {Object.entries(animatedScores).map(([branch, score]) => {
                    const pct = Math.round(score * 100)
                    return (
                        <div key={branch}>
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-sm font-medium text-slate-300">
                                    {BRANCH_ICONS[branch]} {branch}
                                </span>
                                <span className="text-xs font-bold text-slate-400">{pct}%</span>
                            </div>
                            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                <div
                                    className={`h-full rounded-full bg-gradient-to-r ${BRANCH_COLORS[branch] || 'from-indigo-500 to-violet-500'} transition-all duration-700 ease-out`}
                                    style={{ width: `${pct}%` }}
                                />
                            </div>
                        </div>
                    )
                })}
            </div>

            {/* Current Stage */}
            <div className="glass rounded-2xl p-4">
                <p className="text-xs text-slate-500 uppercase tracking-widest mb-2">Current Stage</p>
                <p className="text-sm font-semibold text-indigo-300">
                    {prettyCategory}
                </p>
                <div className="mt-3 flex gap-1">
                    {['INTEREST', 'APTITUDE', 'RANK', 'BUDGET', 'LOCATION', 'CONFIRMATION'].map((cat, i) => (
                        <div
                            key={cat}
                            className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${i <=
                                    ['INTEREST', 'APTITUDE', 'RANK', 'BUDGET', 'LOCATION', 'CONFIRMATION'].indexOf(
                                        currentCategory
                                    )
                                    ? 'bg-indigo-500'
                                    : 'bg-slate-700'
                                }`}
                        />
                    ))}
                </div>
            </div>
        </aside>
    )
}
