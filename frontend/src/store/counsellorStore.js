// store/counsellorStore.js — Zustand global state
// No persistence - clean restart every time
import { create } from "zustand";

// Logging middleware for debugging state changes
const logMiddleware = (config) => (set, get, api) =>
  config(
    (...args) => {
      console.log("[STORE] State update:", args[0]);
      set(...args);
    },
    get,
    api,
  );

const useCounsellorStore = create(
  logMiddleware((set, get) => ({
    // Session state
    sessionId: null,
    messages: [],
    branchScores: {
      CS: 0,
      Electronics: 0,
      Mechanical: 0,
      Civil: 0,
      Medical: 0,
    },
    overallConfidence: 0,
    currentCategory: "INTEREST",
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
    setSessionId: (id) => {
      const currentId = get().sessionId;

      if (currentId === id) {
        console.warn("[STORE] Session ID already set to:", id);
        return;
      }

      console.log("[STORE] Setting session ID:", id);
      set({ sessionId: id });
    },

    addMessage: (msg) => {
      const state = get();

      // Prevent duplicate messages with same timestamp
      const isDuplicate = state.messages.some(
        (m) =>
          m.ts === msg.ts && m.content === msg.content && m.role === msg.role,
      );

      if (isDuplicate) {
        console.warn(
          "[STORE] Duplicate message detected, skipping:",
          msg.content.substring(0, 50),
        );
        return;
      }

      console.log(
        "[STORE] Adding message:",
        msg.role,
        msg.content.substring(0, 50),
      );
      set((state) => ({ messages: [...state.messages, msg] }));
    },

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
        const sel = state.selectedForCompare;
        if (sel.includes(collegeId)) {
          return { selectedForCompare: sel.filter((id) => id !== collegeId) };
        }
        if (sel.length >= 2) return state;
        return { selectedForCompare: [...sel, collegeId] };
      }),

    clearCompare: () => set({ selectedForCompare: [], compareMode: false }),

    setCompareMode: (v) => set({ compareMode: v }),

    resetSession: () => {
      console.log("[STORE] Resetting session - clearing ALL state");
      set({
        sessionId: null,
        messages: [],
        branchScores: {
          CS: 0,
          Electronics: 0,
          Mechanical: 0,
          Civil: 0,
          Medical: 0,
        },
        overallConfidence: 0,
        currentCategory: "INTEREST",
        isComplete: false,
        isLoading: false,
        report: null,
        profileSummary: null,
        hypotheticalRank: null,
        whatIfColleges: null,
        compareMode: false,
        selectedForCompare: [],
      });
      console.log("[STORE] Session reset complete");
    },

    // Debug method to verify clean state
    verifyCleanState: () => {
      const state = get();
      const issues = [];

      if (state.sessionId !== null) issues.push("sessionId not null");
      if (state.messages.length > 0)
        issues.push(`${state.messages.length} messages remain`);
      if (state.isComplete) issues.push("isComplete still true");
      if (state.report !== null) issues.push("report not cleared");

      if (issues.length > 0) {
        console.error("[STORE] State NOT clean after reset:", issues);
        return false;
      }

      console.log("[STORE] State verified clean ✓");
      return true;
    },
  })),
);

export default useCounsellorStore;
