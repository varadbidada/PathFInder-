// store/counsellorStore.js — Zustand global state
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useCounsellorStore = create(
    persist(
        (set, get) => ({
            // Session state
            sessionId: null,
            messages: [],
            branchScores: { CS: 0, Electronics: 0, Mechanical: 0, Civil: 0, Medical: 0 },
            overallConfidence: 0,
            currentCategory: 'INTEREST',
            isComplete: false,
            isLoading: false,

            // Results
            report: null,
            profileSummary: null,
            hypotheticalRank: null,
            whatIfColleges: null,

            // Compare mode
            compareMode: false,
            selectedForCompare: [],

            // Actions
            setSessionId: (id) => set({ sessionId: id }),

            addMessage: (msg) =>
                set((state) => ({ messages: [...state.messages, msg] })),

            setMessages: (messages) => set({ messages }),

            updateFromResponse: (data) =>
                set({
                    branchScores: data.branch_scores || get().branchScores,
                    overallConfidence: data.overall_confidence ?? get().overallConfidence,
                    currentCategory: data.current_category || get().currentCategory,
                    isComplete: data.is_complete ?? false,
                    report: data.report || get().report,
                    profileSummary: data.profile_summary || get().profileSummary,
                }),

            setLoading: (v) => set({ isLoading: v }),

            setReport: (report) => set({ report }),

            setWhatIf: (rank, colleges) =>
                set({ hypotheticalRank: rank, whatIfColleges: colleges }),

            toggleCompare: (collegeId) =>
                set((state) => {
                    const sel = state.selectedForCompare
                    if (sel.includes(collegeId)) {
                        return { selectedForCompare: sel.filter((id) => id !== collegeId) }
                    }
                    if (sel.length >= 2) return state
                    return { selectedForCompare: [...sel, collegeId] }
                }),

            clearCompare: () => set({ selectedForCompare: [], compareMode: false }),

            setCompareMode: (v) => set({ compareMode: v }),

            resetSession: () =>
                set({
                    sessionId: null,
                    messages: [],
                    branchScores: { CS: 0, Electronics: 0, Mechanical: 0, Civil: 0, Medical: 0 },
                    overallConfidence: 0,
                    currentCategory: 'INTEREST',
                    isComplete: false,
                    isLoading: false,
                    report: null,
                    profileSummary: null,
                    hypotheticalRank: null,
                    whatIfColleges: null,
                    compareMode: false,
                    selectedForCompare: [],
                }),
        }),
        {
            name: 'pathfinder-session',
            partialize: (state) => ({
                sessionId: state.sessionId,
                messages: state.messages,
                branchScores: state.branchScores,
                overallConfidence: state.overallConfidence,
                currentCategory: state.currentCategory,
                isComplete: state.isComplete,
                report: state.report,
            }),
        }
    )
)

export default useCounsellorStore
