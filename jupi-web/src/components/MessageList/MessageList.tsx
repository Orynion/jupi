import type { ConversationMessage } from '../../types/api'
import Message from '../Message/Message'
import ToolSurface from '../ToolSurface/ToolSurface'

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
        <div className="message-with-tool" key={message.id}>
          <Message message={message} />
          {message.role === 'user' && <ToolSurface text={message.content} />}
        </div>
      ))}
    </div>
  )
}

export default MessageList