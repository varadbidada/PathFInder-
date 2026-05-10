import { useState } from 'react'

export default function InitialForm({ onSubmit }) {
    const [formData, setFormData] = useState({
        category: 'General',
        exam_type: 'JEE Main',
        jee_rank: '',
        kcet_rank: '',
        neet_rank: '',
        budget_lakh: '',
        preferred_location: '',
    })

    const handleChange = (e) => {
        const { name, value } = e.target
        setFormData((prev) => ({ ...prev, [name]: value }))
    }

    const handleSubmit = (e) => {
        e.preventDefault()
        // Convert to numbers where appropriate
        const payload = {
            ...formData,
            jee_rank: formData.jee_rank ? parseInt(formData.jee_rank, 10) : null,
            kcet_rank: formData.kcet_rank ? parseInt(formData.kcet_rank, 10) : null,
            neet_rank: formData.neet_rank ? parseInt(formData.neet_rank, 10) : null,
            budget_lakh: formData.budget_lakh ? parseFloat(formData.budget_lakh) : null,
        }
        onSubmit(payload)
    }

    return (
        <div className="flex flex-col items-center justify-center flex-1 px-6 py-12 text-center w-full max-w-2xl mx-auto">
            <h2 className="text-3xl font-black gradient-text mb-2">Before we start...</h2>
            <p className="text-slate-400 mb-8">Please share your exam details so we can tailor the recommendations.</p>

            <form onSubmit={handleSubmit} className="glass w-full rounded-3xl p-8 border border-indigo-500/20 text-left flex flex-col gap-6 shadow-2xl">
                {/* Category & Exam Type */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-semibold text-slate-300">Category</label>
                        <select
                            name="category"
                            value={formData.category}
                            onChange={handleChange}
                            className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 outline-none focus:border-indigo-500 transition-colors"
                        >
                            <option value="General">General</option>
                            <option value="OBC">OBC</option>
                            <option value="SC">SC</option>
                            <option value="ST">ST</option>
                            <option value="EWS">EWS</option>
                        </select>
                    </div>
                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-semibold text-slate-300">Primary Exam</label>
                        <select
                            name="exam_type"
                            value={formData.exam_type}
                            onChange={handleChange}
                            className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 outline-none focus:border-indigo-500 transition-colors"
                        >
                            <option value="JEE Main">JEE Main</option>
                            <option value="JEE Advanced">JEE Advanced</option>
                            <option value="State Exam">State Exam (KCET/MHCET)</option>
                            <option value="NEET">NEET</option>
                        </select>
                    </div>
                </div>

                {/* Ranks */}
                <div className="flex flex-col gap-4">
                    <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-widest mt-2">Enter your Ranks (Optional)</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="flex flex-col gap-2">
                            <label className="text-xs font-semibold text-slate-300">JEE Rank</label>
                            <input
                                type="number"
                                name="jee_rank"
                                value={formData.jee_rank}
                                onChange={handleChange}
                                placeholder="e.g. 25000"
                                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 outline-none focus:border-indigo-500 transition-colors"
                            />
                        </div>
                        <div className="flex flex-col gap-2">
                            <label className="text-xs font-semibold text-slate-300">KCET Rank</label>
                            <input
                                type="number"
                                name="kcet_rank"
                                value={formData.kcet_rank}
                                onChange={handleChange}
                                placeholder="e.g. 5000"
                                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 outline-none focus:border-indigo-500 transition-colors"
                            />
                        </div>
                        <div className="flex flex-col gap-2">
                            <label className="text-xs font-semibold text-slate-300">NEET Rank</label>
                            <input
                                type="number"
                                name="neet_rank"
                                value={formData.neet_rank}
                                onChange={handleChange}
                                placeholder="e.g. 15000"
                                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 outline-none focus:border-indigo-500 transition-colors"
                            />
                        </div>
                    </div>
                </div>

                {/* Preferences */}
                <div className="flex flex-col gap-4">
                    <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-widest mt-2">Preferences</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="flex flex-col gap-2">
                            <label className="text-xs font-semibold text-slate-300">Annual Budget (in Lakhs)</label>
                            <input
                                type="number"
                                step="0.1"
                                name="budget_lakh"
                                value={formData.budget_lakh}
                                onChange={handleChange}
                                placeholder="e.g. 5.5"
                                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 outline-none focus:border-indigo-500 transition-colors"
                            />
                        </div>
                        <div className="flex flex-col gap-2">
                            <label className="text-xs font-semibold text-slate-300">Preferred State/City</label>
                            <input
                                type="text"
                                name="preferred_location"
                                value={formData.preferred_location}
                                onChange={handleChange}
                                placeholder="e.g. Maharashtra, Bangalore, Any"
                                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 outline-none focus:border-indigo-500 transition-colors"
                            />
                        </div>
                    </div>
                </div>

                <div className="mt-4">
                    <button
                        type="submit"
                        className="w-full px-8 py-4 rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-bold text-lg
                            hover:from-indigo-500 hover:to-violet-500 active:scale-95 transition-all duration-200 shadow-xl shadow-indigo-900/40"
                    >
                        Start Session 🚀
                    </button>
                </div>
            </form>
        </div>
    )
}
