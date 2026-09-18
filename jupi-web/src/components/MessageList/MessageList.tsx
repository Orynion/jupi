import type { ConversationMessage } from '../../types/api'
import Message from '../Message/Message'

interface MessageListProps {
  messages: ConversationMessage[]
}

function MessageList({ messages }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="message-list-empty">
        No messages yet. Start the conversation.
      </div>
    )
  }

  return (
    <div className="message-list">
      {messages.map((message) => (
        <Message key={message.id} message={message} />
      ))}
    </div>
  )
}

export default MessageList