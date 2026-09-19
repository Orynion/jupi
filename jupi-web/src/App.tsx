import { useCallback, useEffect, useRef, useState } from 'react'
import Layout from './components/Layout/Layout'
import ConversationList from './components/ConversationList/ConversationList'
import ChatView from './components/ChatView/ChatView'
import { createConversation, getConversation, getHealth, listConversations, sendMessage } from './api/client'
import type { Conversation, ConversationSummary, HealthResponse } from './types/api'

type BackendStatus = 'checking' | 'ok' | 'error'

function App() {
  const [backendStatus, setBackendStatus] = useState<BackendStatus>('checking')
  const [healthError, setHealthError] = useState<string | null>(null)
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null)
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const isInitialized = useRef(false)

  // Health check on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await getHealth()
        setBackendStatus('ok')
        setHealthError(null)
      } catch (e) {
        setBackendStatus('error')
        setHealthError(e instanceof Error ? e.message : 'Health check failed')
      }
    }
    checkHealth()
  }, [])

  // Load conversations on mount (once, StrictMode-safe)
  useEffect(() => {
    if (isInitialized.current) return
    isInitialized.current = true

    const load = async () => {
      try {
        const data = await listConversations()
        setConversations(data)

        if (data.length > 0) {
          const first = data[0]
          setSelectedConversationId(first.id)
          await loadConversationData(first.id)
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load conversations')
      }
    }
    load()
  }, [])

  const loadConversationData = async (id: string): Promise<Conversation | null> => {
    try {
      const conv = await getConversation(id)
      setSelectedConversation(conv)
      return conv
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load conversation')
      return null
    }
  }

  const handleSelectConversation = useCallback(async (id: string) => {
    setSelectedConversationId(id)
    setSelectedConversation(null)
    setError(null)
    await loadConversationData(id)
  }, [])

  const handleCreateConversation = useCallback(async () => {
    try {
      const conv = await createConversation()
      setConversations((prev) => [conv, ...prev])
      setSelectedConversationId(conv.id)
      setSelectedConversation(conv)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create conversation')
    }
  }, [])

  const handleSendMessage = useCallback(
    async (message: string) => {
      if (!selectedConversationId || !message.trim()) return

      setIsLoading(true)
      setError(null)

      try {
        const response = await sendMessage({
          message,
          conversation_id: selectedConversationId,
        })

        // Refresh the selected conversation data
        const updated = await loadConversationData(selectedConversationId)

        if (updated) {
          // Update conversation in list if title changed
          setConversations((prev) =>
            prev.map((c) =>
              c.id === selectedConversationId
                ? { ...c, title: updated.title, updated_at: updated.updated_at }
                : c,
            ),
          )
        }

        return response.response
      } catch (e) {
        const errMsg = e instanceof Error ? e.message : 'Failed to send message'
        setError(errMsg)
        throw e
      } finally {
        setIsLoading(false)
      }
    },
    [selectedConversationId],
  )

  const handleRefreshList = useCallback(async () => {
    try {
      const data = await listConversations()
      setConversations(data)
    } catch (e) {
      // Silent fail - don't interrupt the user
    }
  }, [])

  return (
    <Layout>
      <header className="app-header">
        <div className="brand">
          <div>
            <h1 className="brand-title">Conversation</h1>
          </div>
        </div>
        <div className="header-status">
          <span className={`status-dot status-${backendStatus}`} />
          <span>
            {backendStatus === 'checking' && 'Checking backend...'}
            {backendStatus === 'ok' && 'Backend connected'}
            {backendStatus === 'error' && `Backend error: ${healthError}`}
          </span>
        </div>
      </header>

      <div className="app-body">
        <ConversationList
          conversations={conversations}
          selectedId={selectedConversationId}
          onSelect={handleSelectConversation}
          onNewChat={handleCreateConversation}
        />

        <ChatView
          conversation={selectedConversation}
          onSend={handleSendMessage}
          loading={isLoading}
        />
      </div>

      {error && (
        <div className="app-error" role="alert">
          {error}
          <button onClick={handleRefreshList}>Retry</button>
        </div>
      )}
    </Layout>
  )
}

export default App