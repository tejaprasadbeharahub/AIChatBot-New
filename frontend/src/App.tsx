import { useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { clearStoredToken, getStoredToken, googleLogin, login, register, renderGoogleSignInButton } from './api/auth'
import { createChat, deleteChat, getChats, getMessages, sendChatMessage, updateChatTitle } from './api/chat'
import type { Chat, Message } from './types/chat'

type ChatRole = 'user' | 'assistant'

type ChatMessage = {
  id: string
  role: ChatRole
  content: string
}

function createId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function toUiMessages(items: Message[]): ChatMessage[] {
  return items.map((item) => ({
    id: item.id,
    role: item.role,
    content: item.content,
  }))
}

function formatChatTitle(chat: Chat): string {
  if (chat.title && chat.title.trim().length > 0) {
    return chat.title
  }
  return 'Untitled chat'
}

function App() {
  const [token, setToken] = useState<string | null>(() => getStoredToken())
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID?.trim() ?? ''

  const [chats, setChats] = useState<Chat[]>([])
  const [activeChatId, setActiveChatId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')

  const [isBootstrapping, setIsBootstrapping] = useState(false)
  const [isLoadingChats, setIsLoadingChats] = useState(false)
  const [isLoadingMessages, setIsLoadingMessages] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const listRef = useRef<HTMLDivElement | null>(null)
  const googleButtonRef = useRef<HTMLDivElement | null>(null)

  const turnsForApi = useMemo(
    () => messages.map((message) => ({ role: message.role, content: message.content })),
    [messages],
  )

  useEffect(() => {
    const container = listRef.current
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  }, [messages, isSending])

  useEffect(() => {
    if (!token) {
      return
    }

    let cancelled = false
    async function bootstrap() {
      setIsBootstrapping(true)
      setError(null)
      try {
        const allChats = await getChats()
        if (cancelled) {
          return
        }
        setChats(allChats)
        if (allChats.length > 0) {
          const first = allChats[0]
          setActiveChatId(first.id)
          const chatMessages = await getMessages(first.id)
          if (cancelled) {
            return
          }
          setMessages(toUiMessages(chatMessages))
        } else {
          setActiveChatId(null)
          setMessages([])
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }
        const message = requestError instanceof Error ? requestError.message : 'Could not load chats'
        setError(message)
      } finally {
        if (!cancelled) {
          setIsBootstrapping(false)
        }
      }
    }

    void bootstrap()
    return () => {
      cancelled = true
    }
  }, [token])

  async function refreshChats(keepCurrent = true): Promise<Chat[]> {
    setIsLoadingChats(true)
    try {
      const allChats = await getChats()
      setChats(allChats)
      if (!keepCurrent && allChats.length > 0) {
        setActiveChatId(allChats[0].id)
      }
      return allChats
    } finally {
      setIsLoadingChats(false)
    }
  }

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!email.trim() || !password.trim()) {
      return
    }

    setError(null)
    setIsBootstrapping(true)
    try {
      const normalizedEmail = email.trim().toLowerCase()
      if (authMode === 'login') {
        const result = await login(normalizedEmail, password)
        setToken(result.access_token)
      } else {
        const result = await register(normalizedEmail, password)
        setToken(result.access_token)
      }
      setPassword('')
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Authentication failed'
      setError(message)
    } finally {
      setIsBootstrapping(false)
    }
  }

  useEffect(() => {
    if (token || !googleButtonRef.current) {
      return
    }

    let active = true
    const googleButtonContainer = googleButtonRef.current

    void renderGoogleSignInButton({
      clientId: googleClientId,
      container: googleButtonContainer,
      onCredential: async (tokenFromGoogle) => {
        if (!active) {
          return
        }
        setError(null)
        setIsBootstrapping(true)
        try {
          const result = await googleLogin(tokenFromGoogle.trim())
          if (active) {
            setToken(result.access_token)
          }
        } catch (requestError) {
          if (!active) {
            return
          }
          const message = requestError instanceof Error ? requestError.message : 'Google authentication failed'
          setError(message)
        } finally {
          if (active) {
            setIsBootstrapping(false)
          }
        }
      },
      onError: (message) => {
        if (active) {
          setError(message)
        }
      },
    }).catch((requestError) => {
      if (!active) {
        return
      }
      const message = requestError instanceof Error ? requestError.message : 'Google authentication failed'
      setError(message)
    })

    return () => {
      active = false
      googleButtonContainer.innerHTML = ''
    }
  }, [googleClientId, token])

  async function handleChatSelect(chatId: string) {
    setActiveChatId(chatId)
    setIsLoadingMessages(true)
    setError(null)
    try {
      const history = await getMessages(chatId)
      setMessages(toUiMessages(history))
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Could not load chat messages'
      setError(message)
    } finally {
      setIsLoadingMessages(false)
    }
  }

  async function startNewChat() {
    setError(null)
    try {
      const created = await createChat()
      setActiveChatId(created.id)
      setMessages([])
      setInput('')
      await refreshChats(true)
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Could not create chat'
      setError(message)
    }
  }

  async function handleRenameActiveChat() {
    if (!activeChatId) {
      return
    }
    const title = window.prompt('Enter new chat name')
    if (!title || title.trim().length === 0) {
      return
    }
    setError(null)
    try {
      await updateChatTitle(activeChatId, { title: title.trim() })
      await refreshChats(true)
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Could not rename chat'
      setError(message)
    }
  }

  async function handleDeleteActiveChat() {
    if (!activeChatId) {
      return
    }
    const approved = window.confirm('Delete this chat thread?')
    if (!approved) {
      return
    }
    setError(null)
    try {
      await deleteChat(activeChatId)
      const allChats = await refreshChats(false)
      if (allChats.length > 0) {
        const first = allChats[0]
        setActiveChatId(first.id)
        const history = await getMessages(first.id)
        setMessages(toUiMessages(history))
      } else {
        setActiveChatId(null)
        setMessages([])
      }
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Could not delete chat'
      setError(message)
    }
  }

  async function handleLogout() {
    clearStoredToken()
    setToken(null)
    setChats([])
    setActiveChatId(null)
    setMessages([])
    setInput('')
    setPassword('')
    setError(null)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || isSending || !token) {
      return
    }

    const userMessage: ChatMessage = {
      id: createId(),
      role: 'user',
      content: trimmed,
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setError(null)
    setIsSending(true)

    try {
      let chatId = activeChatId
      if (!chatId) {
        const created = await createChat()
        chatId = created.id
        setActiveChatId(chatId)
      }

      const response = await sendChatMessage({
        message: trimmed,
        history: turnsForApi,
        chat_id: chatId,
      })

      const assistantMessage: ChatMessage = {
        id: createId(),
        role: 'assistant',
        content: response.reply,
      }
      setMessages((prev) => [...prev, assistantMessage])
      setActiveChatId(response.chat_id)
      await refreshChats(true)
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Unexpected error'
      setError(message)
    } finally {
      setIsSending(false)
    }
  }

  if (!token) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <p className="eyebrow">Amzur Employee Access</p>
          <h1>Sign in to your AI Workspace</h1>
          <p className="subtitle">Use your @amzur.com account to load your saved chat history.</p>

          <div className="auth-switch">
            <button
              type="button"
              className={authMode === 'login' ? 'tab active' : 'tab'}
              onClick={() => setAuthMode('login')}
            >
              Login
            </button>
            <button
              type="button"
              className={authMode === 'register' ? 'tab active' : 'tab'}
              onClick={() => setAuthMode('register')}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleAuth} className="auth-form">
            <label>
              Work Email
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@amzur.com"
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter password"
                minLength={8}
                required
              />
            </label>
            <button type="submit" className="auth-submit" disabled={isBootstrapping}>
              {isBootstrapping ? 'Please wait...' : authMode === 'login' ? 'Login' : 'Create account'}
            </button>
            <div ref={googleButtonRef} />
          </form>
          {error ? <p className="error-text">{error}</p> : null}
        </section>
      </main>
    )
  }

  return (
    <main className="workspace-shell">
      <aside className="chat-list-panel">
        <div className="list-header">
          <div>
            <p className="eyebrow">LangChain + Gemini</p>
            <h2>Amzur AI Chatbot</h2>
          </div>
          <button type="button" className="ghost-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>

        <button type="button" className="new-chat-btn" onClick={() => void startNewChat()}>
          + New chat
        </button>

        <div className="auth-switch">
          <button type="button" className="tab" disabled={!activeChatId} onClick={() => void handleRenameActiveChat()}>
            Rename
          </button>
          <button type="button" className="tab" disabled={!activeChatId} onClick={() => void handleDeleteActiveChat()}>
            Delete
          </button>
        </div>

        <div className="chat-list" aria-live="polite">
          {isLoadingChats ? <p className="meta-text">Refreshing chats...</p> : null}
          {chats.length === 0 ? <p className="meta-text">No previous chats yet.</p> : null}
          {chats.map((chat) => (
            <button
              key={chat.id}
              type="button"
              className={chat.id === activeChatId ? 'chat-item active' : 'chat-item'}
              onClick={() => void handleChatSelect(chat.id)}
            >
              <span>{formatChatTitle(chat)}</span>
            </button>
          ))}
        </div>
      </aside>

      <section className="chat-surface">
        <header className="chat-header">
          <div>
            <p className="eyebrow">Private Workspace</p>
            <h1>{activeChatId ? 'Conversation' : 'Start a new conversation'}</h1>
            <p className="subtitle">Your chats are saved to PostgreSQL and restored after login.</p>
          </div>
        </header>

        <div ref={listRef} className="message-list" aria-live="polite">
          {isBootstrapping || isLoadingMessages ? <p className="meta-text">Loading messages...</p> : null}
          {!isBootstrapping && !isLoadingMessages && messages.length === 0 ? (
            <article className="bubble-row bubble-assistant">
              <div className="bubble">Hello. Start typing and I will save this chat automatically.</div>
            </article>
          ) : null}
          {messages.map((message) => (
            <article key={message.id} className={`bubble-row ${message.role === 'user' ? 'bubble-user' : 'bubble-assistant'}`}>
              <div className="bubble">{message.content}</div>
            </article>
          ))}

          {isSending ? (
            <article className="bubble-row bubble-assistant">
              <div className="bubble bubble-loading">Thinking</div>
            </article>
          ) : null}
        </div>

        <footer className="chat-footer">
          <form onSubmit={handleSubmit} className="composer">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              className="composer-input"
              placeholder="Ask anything..."
              rows={2}
              disabled={isSending || isBootstrapping}
            />
            <button type="submit" className="composer-send" disabled={isSending || isBootstrapping || input.trim().length === 0}>
              {isSending ? 'Sending...' : 'Send'}
            </button>
          </form>
          {error ? <p className="error-text">{error}</p> : null}
        </footer>
      </section>
    </main>
  )
}

export default App
