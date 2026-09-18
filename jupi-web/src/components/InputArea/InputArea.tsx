import { useState } from 'react'

interface InputAreaProps {
  onSend: (message: string) => void
  disabled: boolean
  loading: boolean
}

function InputArea({ onSend, disabled, loading }: InputAreaProps) {
  const [value, setValue] = useState('')

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  return (
    <form className="input-area" onSubmit={handleSubmit}>
      <input
        type="text"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Type a message..."
        aria-label="Message"
        disabled={disabled || loading}
      />
      <button type="submit" disabled={disabled || loading || !value.trim()}>
        {loading ? 'Thinking...' : 'Send'}
      </button>
    </form>
  )
}

export default InputArea