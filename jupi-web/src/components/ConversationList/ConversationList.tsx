import type { ConversationSummary } from '../../types/api'
import ConversationItem from '../ConversationItem/ConversationItem'

interface ConversationListProps {
  conversations: ConversationSummary[]
  selectedId: string | null
  onSelect: (id: string) => void
  onNewChat: () => void
}

function ConversationList({
  conversations,
  selectedId,
  onSelect,
  onNewChat,
}: ConversationListProps) {
  return (
    <aside className="conversation-list">
      <div className="conversation-list-header">
        <button className="new-chat-button" onClick={onNewChat}>
          + New Chat
        </button>
      </div>

      <ul className="conversation-list-items">
        {conversations.map((conversation) => (
          <li key={conversation.id}>
            <ConversationItem
              conversation={conversation}
              selected={conversation.id === selectedId}
              onSelect={onSelect}
            />
          </li>
        ))}
      </ul>
    </aside>
  )
}

export default ConversationList