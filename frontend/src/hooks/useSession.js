// hooks/useSession.js — Session management hook
import { useCallback } from 'react'
import axios from 'axios'
import useCounsellorStore from '../store/counsellorStore'

const API = '/api'

export function useSession() {
    const { sessionId, setSessionId, addMessage, updateFromResponse, setLoading, resetSession } =
        useCounsellorStore()

    const startSession = useCallback(async (formData = {}) => {
        try {
            setLoading(true)
            const res = await axios.post(`${API}/session/start`, formData)
            const { session_id, message, first_question } = res.data
            setSessionId(session_id)
            addMessage({ role: 'assistant', content: message, ts: Date.now() })
            addMessage({ role: 'assistant', content: first_question, ts: Date.now() + 1 })
            return session_id
        } catch (err) {
            console.error('Failed to start session:', err)
            addMessage({
                role: 'assistant',
                content: '⚠️ Failed to connect to the server. Make sure the backend is running.',
                ts: Date.now(),
            })
        } finally {
            setLoading(false)
        }
    }, [setSessionId, addMessage, setLoading])

    const clearSession = useCallback(async () => {
        if (sessionId) {
            try {
                await axios.delete(`${API}/session/${sessionId}`)
            } catch (_) { }
        }
        resetSession()
    }, [sessionId, resetSession])

    return { sessionId, startSession, clearSession }
}
