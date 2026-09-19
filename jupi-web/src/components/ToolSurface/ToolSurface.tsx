import { useMemo, useState } from 'react'

interface ToolSurfaceProps {
  text: string
}

const winningLines = [
  [0, 1, 2], [3, 4, 5], [6, 7, 8],
  [0, 3, 6], [1, 4, 7], [2, 5, 8],
  [0, 4, 8], [2, 4, 6],
]

function hasWinner(board: string[], mark: string) {
  return winningLines.some((line) => line.every((index) => board[index] === mark))
}

function TicTacToeGame() {
  const emptyBoard = () => Array<string>(9).fill('')
  const [board, setBoard] = useState(emptyBoard)
  const [status, setStatus] = useState('Your turn. You are X.')
  const gameOver = hasWinner(board, 'X') || hasWinner(board, 'O') || board.every(Boolean)

  const chooseMove = (current: string[]) => {
    const findFinishingMove = (mark: string) => {
      for (const index of current.keys()) {
        if (current[index]) continue
        const next = [...current]
        next[index] = mark
        if (hasWinner(next, mark)) return index
      }
      return -1
    }

    const winningMove = findFinishingMove('O')
    if (winningMove >= 0) return winningMove
    const blockingMove = findFinishingMove('X')
    if (blockingMove >= 0) return blockingMove
    if (!current[4]) return 4
    const corners = [0, 2, 6, 8].filter((index) => !current[index])
    if (corners.length) return corners[0]
    return current.findIndex((cell) => !cell)
  }

  const playCell = (index: number) => {
    if (gameOver || board[index]) return
    const afterUser = [...board]
    afterUser[index] = 'X'

    if (hasWinner(afterUser, 'X')) {
      setBoard(afterUser)
      setStatus('You win! Jupi is defeated this round.')
      return
    }
    if (afterUser.every(Boolean)) {
      setBoard(afterUser)
      setStatus('A draw. The board is perfectly stubborn.')
      return
    }

    const jupiIndex = chooseMove(afterUser)
    if (jupiIndex < 0) return
    const afterJupi = [...afterUser]
    afterJupi[jupiIndex] = 'O'
    setBoard(afterJupi)
    if (hasWinner(afterJupi, 'O')) {
      setStatus('Jupi wins this round. Ask for a rematch.')
    } else if (afterJupi.every(Boolean)) {
      setStatus('A draw. The board is perfectly stubborn.')
    } else {
      setStatus('Your turn. You are X.')
    }
  }

  const newGame = () => {
    setBoard(emptyBoard())
    setStatus('Your turn. You are X.')
  }

  return (
    <section className="tool-card tic-tac-toe-card" aria-label="Tic-Tac-Toe">
      <div className="tool-card-heading">
        <div>
          <span className="tool-kicker">Game</span>
          <h3>Tic-Tac-Toe</h3>
        </div>
        <span className="tool-status">{status}</span>
      </div>
      <div className="tic-tac-toe-board">
        {board.map((mark, index) => (
          <button
            key={index}
            className={`tic-cell ${mark ? 'tic-cell-filled' : ''}`}
            onClick={() => playCell(index)}
            disabled={gameOver || Boolean(mark)}
            aria-label={`Cell ${index + 1}${mark ? `, ${mark}` : ''}`}
          >
            {mark}
          </button>
        ))}
      </div>
      <button className="tool-secondary-button" onClick={newGame}>New game</button>
    </section>
  )
}

function MusicPlayer({ query }: { query: string }) {
  const [playing, setPlaying] = useState(true)
  const [trackNumber, setTrackNumber] = useState(0)
  const searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`
  const videoId = query.match(/(?:youtube\.com\/(?:watch\?v=|shorts\/)|youtu\.be\/)([\w-]{11})/)?.[1]
  const playerUrl = videoId
    ? `https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1`
    : ''

  const skip = () => {
    setTrackNumber((current) => current + 1)
    setPlaying(true)
  }

  return (
    <section className="tool-card music-card" aria-label="Music player">
      <div className="tool-card-heading">
        <div>
          <span className="tool-kicker">Music</span>
          <h3>{query}</h3>
        </div>
        <span className="tool-status">YouTube search</span>
      </div>
      <div className={`music-player-frame ${playing && videoId ? '' : 'music-player-stopped'}`}>
        {playing && videoId ? (
          <iframe
            key={`${videoId}-${trackNumber}`}
            title={`Playing ${query}`}
            src={playerUrl}
            allow="autoplay; encrypted-media; picture-in-picture"
            allowFullScreen
          />
        ) : (
          <div className="music-player-placeholder">
            {playing ? 'Choose a result on YouTube to start playback' : 'Playback stopped'}
          </div>
        )}
      </div>
      <div className="music-controls">
        <button className="tool-secondary-button" onClick={() => setPlaying((current) => !current)}>
          {playing ? 'Pause' : 'Resume'}
        </button>
        <button className="tool-secondary-button" onClick={() => setPlaying(false)}>Stop</button>
        <button className="tool-secondary-button" onClick={skip}>Skip</button>
        <a className="tool-link-button" href={searchUrl} target="_blank" rel="noreferrer">Open YouTube</a>
      </div>
      <p className="tool-note">Playback uses YouTube and may be restricted by the selected video.</p>
    </section>
  )
}

function FractionChart({ numerator, denominator }: { numerator: number; denominator: number }) {
  const percentage = (numerator / denominator) * 100
  return (
    <section className="tool-card fraction-card" aria-label="Fraction chart">
      <div className="tool-card-heading">
        <div>
          <span className="tool-kicker">Visual math</span>
          <h3>{numerator} / {denominator}</h3>
        </div>
        <span className="tool-status">{percentage.toFixed(1)}%</span>
      </div>
      <div className="fraction-chart-layout">
        <div
          className="fraction-pie"
          style={{ background: `conic-gradient(var(--color-accent) 0 ${percentage}%, var(--color-border) ${percentage}% 100%)` }}
          role="img"
          aria-label={`${numerator} out of ${denominator}`}
        />
        <div className="fraction-legend">
          <span><i className="fraction-swatch fraction-swatch-filled" /> {numerator} parts</span>
          <span><i className="fraction-swatch" /> {denominator - numerator} parts remaining</span>
        </div>
      </div>
    </section>
  )
}

function ToolSurface({ text }: ToolSurfaceProps) {
  const lowerText = text.toLowerCase()
  const fraction = useMemo(() => {
    if (!/(show|visual|chart|graph|diagram|picture|draw|pie)/i.test(text)) return null
    const match = text.match(/(?<!\d)(\d{1,2})\s*\/\s*(100|[1-9]\d?)(?!\d)/)
    if (!match) return null
    const numerator = Number(match[1])
    const denominator = Number(match[2])
    return numerator > 0 && numerator < denominator ? { numerator, denominator } : null
  }, [text])

  if (/tic[- ]?tac[- ]toe|noughts|crosses|board game/.test(lowerText)) return <TicTacToeGame />
  if (/\b(play|listen)\b/.test(lowerText) && !/play game/.test(lowerText)) {
    const query = text.replace(/^\s*(hey\s+jupi|jupi|please)\s*,?\s*/i, '').replace(/^\s*play\s+/i, '').trim()
    return <MusicPlayer query={query || 'top music hits'} />
  }
  if (fraction) return <FractionChart {...fraction} />
  return null
}

export default ToolSurface
