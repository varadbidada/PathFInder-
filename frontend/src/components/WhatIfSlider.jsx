// components/WhatIfSlider.jsx — Rank simulator slider
import { useState, useCallback } from 'react'
import { useConversation } from '../hooks/useConversation'
import useCounsellorStore from '../store/counsellorStore'
import CollegeCard from './CollegeCard'

export default function WhatIfSlider() {
    const { report } = useCounsellorStore()
    const { runWhatIf } = useConversation()
    const [rank, setRank] = useState(report?.student_rank || 5000)
    const [whatIfData, setWhatIfData] = useState(null)
    const [loading, setLoading] = useState(false)

    const handleSimulate = useCallback(async () => {
        setLoading(true)
        const data = await runWhatIf(rank)
        if (data) setWhatIfData(data)
        setLoading(false)
    }, [rank, runWhatIf])

    const allColleges = whatIfData
        ? [
            ...(whatIfData.colleges?.Dream || []),
            ...(whatIfData.colleges?.Moderate || []),
            ...(whatIfData.colleges?.Safe || []),
        ]
        : []

    return (
        <div className="glass rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-6">
                <span className="text-2xl">🎯</span>
                <div>
                    <h3 className="font-bold text-lg text-slate-100">What-If Simulator</h3>
                    <p className="text-sm text-slate-500">Drag the slider to see how a different rank changes your options</p>
                </div>
            </div>

            {/* Slider */}
            <div className="space-y-4">
                <div className="flex justify-between text-sm text-slate-400">
                    <span>Rank 1 (Best)</span>
                    <span className="font-bold text-indigo-300 text-lg">#{rank.toLocaleString()}</span>
                    <span>Rank 1,00,000</span>
                </div>
                <input
                    type="range"
                    min="1"
                    max="100000"
                    step="100"
                    value={rank}
                    onChange={(e) => setRank(Number(e.target.value))}
                    className="w-full h-2 bg-slate-700 rounded-full appearance-none cursor-pointer
            [&::-webkit-slider-thumb]:appearance-none
            [&::-webkit-slider-thumb]:w-5
            [&::-webkit-slider-thumb]:h-5
            [&::-webkit-slider-thumb]:rounded-full
            [&::-webkit-slider-thumb]:bg-indigo-500
            [&::-webkit-slider-thumb]:shadow-lg
            [&::-webkit-slider-thumb]:cursor-pointer"
                />
                <button
                    onClick={handleSimulate}
                    disabled={loading}
                    className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-semibold
            hover:from-indigo-500 hover:to-violet-500 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? '⏳ Simulating…' : '🔮 Simulate This Rank'}
                </button>
            </div>

            {/* Results */}
            {allColleges.length > 0 && (
                <div className="mt-6 space-y-3">
                    <p className="text-sm text-slate-400">
                        Showing {allColleges.length} colleges for rank <span className="text-indigo-300 font-bold">#{rank.toLocaleString()}</span>
                    </p>
                    <div className="grid grid-cols-1 gap-4 max-h-96 overflow-y-auto pr-1">
                        {allColleges.map((c) => (
                            <CollegeCard key={c.id} college={c} showCompare={false} />
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
