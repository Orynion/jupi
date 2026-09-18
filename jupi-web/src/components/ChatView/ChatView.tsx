import type { Conversation } from '../../types/api'
import MessageList from '../MessageList/MessageList'
import InputArea from '../InputArea/InputArea'

interface ChatViewProps {
  conversation: Conversation | null
  onSend: (message: string) => void
  loading: boolean
}

function ChatView({ conversation, onSend, loading }: ChatViewProps) {
  return (
    <section className="chat-view">
      <header className="chat-view-header">
        <h2 className="chat-view-title">
          {conversation?.title ?? 'No conversation selected'}
        </h2>
        {conversation && (
          <span className="chat-view-meta">
            {conversation.messages.length} message{conversation.messages.length === 1 ? '' : 's'}
          </span>
        )}
      </header>

      <div className="chat-view-messages" role="log" aria-live="polite">
        {conversation ? (
          <MessageList messages={conversation.messages} />
        ) : (
          <div className="chat-view-placeholder">
            Select a conversation or create a new one.
          </div>
        )}
      </div>

      <footer className="chat-view-input">
        <InputArea onSend={onSend} disabled={!conversation} loading={loading} />
      </footer>
    </section>
  )
}

export default ChatView