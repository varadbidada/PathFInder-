// components/ChatWindow.jsx — Premium dark-mode chat interface
import { useEffect, useRef, useState } from 'react'
import useCounsellorStore from '../store/counsellorStore'
import { useConversation } from '../hooks/useConversation'
import ReactMarkdown from 'react-markdown'

function TypingIndicator() {
    return (
        <div className="flex items-end gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-sm shrink-0">
                🤖
            </div>
            <div className="glass rounded-2xl rounded-bl-sm px-4 py-3">
                <div className="flex gap-1.5 items-center h-4">
                    {[0, 1, 2].map((i) => (
                        <div
                            key={i}
                            className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce"
                            style={{ animationDelay: `${i * 150}ms` }}
                        />
                    ))}
                </div>
            </div>
        </div>
    )
}

function ChatBubble({ msg }) {
    const isUser = msg.role === 'user'
    const time = new Date(msg.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    return (
        <div className={`flex items-end gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
            {/* Avatar */}
            <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm shrink-0 ${isUser
                        ? 'bg-gradient-to-br from-violet-600 to-pink-500'
                        : 'bg-gradient-to-br from-indigo-500 to-violet-600'
                    }`}
            >
                {isUser ? '👤' : '🤖'}
            </div>

            {/* Bubble */}
            <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
                <div
                    className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${isUser
                            ? 'bg-gradient-to-br from-indigo-600 to-violet-600 text-white rounded-br-sm'
                            : 'glass rounded-bl-sm text-slate-200'
                        }`}
                >
                    <ReactMarkdown
                        components={{
                            strong: ({ children }) => (
                                <strong className="text-indigo-300 font-semibold">{children}</strong>
                            ),
                            p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                        }}
                    >
                        {msg.content}
                    </ReactMarkdown>
                </div>
                <span className="text-xs text-slate-600 px-1">{time}</span>
            </div>
        </div>
    )
}

export default function ChatWindow() {
    const { messages, isLoading } = useCounsellorStore()
    const { sendMessage } = useConversation()
    const [input, setInput] = useState('')
    const bottomRef = useRef(null)
    const inputRef = useRef(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, isLoading])

    const handleSend = async () => {
        const text = input.trim()
        if (!text || isLoading) return
        setInput('')
        await sendMessage(text)
        inputRef.current?.focus()
    }

    const handleKey = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <div className="flex flex-col flex-1 min-h-0">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-6 space-y-5">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full gap-4 text-center opacity-60">
                        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-4xl">
                            🧭
                        </div>
                        <div>
                            <p className="text-lg font-semibold text-slate-300">Pathfinder is ready</p>
                            <p className="text-sm text-slate-500">Click "Start Session" to begin your counselling</p>
                        </div>
                    </div>
                )}
                {messages.map((msg, i) => (
                    <ChatBubble key={`${msg.ts}-${i}`} msg={msg} />
                ))}
                {isLoading && <TypingIndicator />}
                <div ref={bottomRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-slate-800">
                <div className="flex gap-3 items-end">
                    <textarea
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKey}
                        placeholder="Type your answer… (Enter to send)"
                        rows={2}
                        className="flex-1 resize-none rounded-xl bg-slate-900/60 border border-slate-700 text-slate-200 
              placeholder-slate-600 px-4 py-3 text-sm outline-none focus:border-indigo-500 
              focus:ring-1 focus:ring-indigo-500/50 transition-all duration-200"
                    />
                    <button
                        onClick={handleSend}
                        disabled={isLoading || !input.trim()}
                        className="p-3 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 text-white 
              hover:from-indigo-500 hover:to-violet-500 active:scale-95 transition-all duration-200
              disabled:opacity-40 disabled:cursor-not-allowed disabled:scale-100 shrink-0"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                    </button>
                </div>
                <p className="text-xs text-slate-700 mt-2 text-center">
                    Shift+Enter for new line · Enter to send
                </p>
            </div>
        </div>
    )
}
