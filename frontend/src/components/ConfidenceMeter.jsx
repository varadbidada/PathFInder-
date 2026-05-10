// components/ConfidenceMeter.jsx — Animated circular confidence ring
import { useEffect, useRef } from 'react'

export default function ConfidenceMeter({ confidence = 0, branch = 'CS' }) {
    const canvasRef = useRef(null)
    const pct = Math.round(confidence * 100)
    const radius = 52
    const circumference = 2 * Math.PI * radius

    useEffect(() => {
        const canvas = canvasRef.current
        if (!canvas) return
        const ctx = canvas.getContext('2d')
        const size = canvas.width
        const cx = size / 2
        const cy = size / 2
        const r = radius

        ctx.clearRect(0, 0, size, size)

        // Track
        ctx.beginPath()
        ctx.arc(cx, cy, r, 0, 2 * Math.PI)
        ctx.strokeStyle = 'rgba(99,102,241,0.15)'
        ctx.lineWidth = 8
        ctx.stroke()

        // Progress arc
        const angle = (confidence * 2 * Math.PI) - Math.PI / 2
        const grad = ctx.createLinearGradient(0, 0, size, size)
        grad.addColorStop(0, '#6366f1')
        grad.addColorStop(1, '#a855f7')

        ctx.beginPath()
        ctx.arc(cx, cy, r, -Math.PI / 2, angle)
        ctx.strokeStyle = grad
        ctx.lineWidth = 8
        ctx.lineCap = 'round'
        ctx.stroke()
    }, [confidence])

    const color =
        pct >= 75 ? 'text-emerald-400' : pct >= 50 ? 'text-yellow-400' : 'text-red-400'

    return (
        <div className="flex flex-col items-center gap-2">
            <p className="text-xs text-slate-400 uppercase tracking-widest font-semibold">Confidence</p>
            <div className="relative w-32 h-32 flex items-center justify-center">
                <canvas ref={canvasRef} width={128} height={128} className="absolute inset-0" />
                <div className="flex flex-col items-center z-10">
                    <span className={`text-3xl font-bold ${color}`}>{pct}%</span>
                    <span className="text-xs text-slate-400 mt-1">{branch}</span>
                </div>
            </div>
        </div>
    )
}
