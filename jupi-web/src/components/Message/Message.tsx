import type { ConversationMessage } from '../../types/api'

interface MessageProps {
  message: ConversationMessage
}

function Message({ message }: MessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
      <span className="message-role">{isUser ? 'You' : 'Saturnia'}</span>
      <p className="message-content">{message.content}</p>
    </div>
  )
}

export default Message