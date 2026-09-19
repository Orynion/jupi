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
      <div className="sidebar-brand" aria-label="Jupi Home">
        <span className="sidebar-brand-mark">J</span>
      </div>

      <nav className="sidebar-navigation" aria-label="Main navigation">
        <button className="sidebar-nav-button sidebar-nav-button-primary" onClick={onNewChat}>
          <span aria-hidden="true">+</span>
          New Chat
        </button>
        <button className="sidebar-nav-button sidebar-nav-button-active" type="button">
          <span aria-hidden="true">&#9635;</span>
          Chats
        </button>
        <button className="sidebar-nav-button" type="button">
          <span aria-hidden="true">&#8981;</span>
          Search
        </button>
      </nav>

      <section className="conversation-list-section" aria-label="Conversations">
        <div className="conversation-list-heading">Recent chats</div>
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
      </section>

      <button className="sidebar-nav-button sidebar-settings-button" type="button">
        <span aria-hidden="true">&#9881;</span>
        Settings
      </button>
    </aside>
  )
}

export default ConversationList