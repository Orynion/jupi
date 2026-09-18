import type { ConversationSummary } from '../../types/api'

interface ConversationItemProps {
  conversation: ConversationSummary
  selected: boolean
  onSelect: (id: string) => void
}

function ConversationItem({
  conversation,
  selected,
  onSelect,
}: ConversationItemProps) {
  const truncatedTitle =
    conversation.title.length > 30
      ? conversation.title.slice(0, 30) + '...'
      : conversation.title

  return (
    <button
      className={`conversation-item ${selected ? 'selected' : ''}`}
      onClick={() => onSelect(conversation.id)}
      aria-pressed={selected}
    >
      <span className="conversation-title">{truncatedTitle}</span>
      <span className="conversation-meta">
        {conversation.message_count} message{conversation.message_count === 1 ? '' : 's'}
      </span>
    </button>
  )
}

export default ConversationItem