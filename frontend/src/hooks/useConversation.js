// hooks/useConversation.js — Chat interaction hook
import { useCallback } from 'react'
import axios from 'axios'
import useCounsellorStore from '../store/counsellorStore'

const API = '/api'

export function useConversation() {
    const { sessionId, addMessage, updateFromResponse, setLoading } = useCounsellorStore()

    const sendMessage = useCallback(
        async (text) => {
            if (!sessionId || !text.trim()) return

            addMessage({ role: 'user', content: text, ts: Date.now() })
            setLoading(true)

            try {
                const res = await axios.post(`${API}/chat`, {
                    session_id: sessionId,
                    user_message: text,
                })
                const data = res.data
                updateFromResponse(data)
                addMessage({ role: 'assistant', content: data.assistant_message, ts: Date.now() })
                return data
            } catch (err) {
                const errMsg =
                    err.response?.data?.detail ||
                    '⚠️ Something went wrong. Please try again.'
                addMessage({ role: 'assistant', content: errMsg, ts: Date.now() })
            } finally {
                setLoading(false)
            }
        },
        [sessionId, addMessage, updateFromResponse, setLoading]
    )

    const runWhatIf = useCallback(
        async (rank) => {
            if (!sessionId) return null
            try {
                const res = await axios.post(`${API}/what-if`, {
                    session_id: sessionId,
                    hypothetical_rank: rank,
                })
                return res.data
            } catch (err) {
                console.error('What-if failed:', err)
                return null
            }
        },
        [sessionId]
    )

    return { sendMessage, runWhatIf }
}
