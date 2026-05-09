import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { clearStoredToken, getStoredToken, googleLogin, renderGoogleSignInButton } from './api/auth'
import { login, register } from './api/auth'
import { createChat, createUserMessage, deleteChat, downloadAttachment, extractAttachmentText, getChats, getMessages, sendChatMessage, uploadAttachment, updateChatTitle } from './api/chat'
import { generateImage, getImageStatus, deleteGeneratedImage } from './api/image_generation'
import { getChatPdfDocuments, getPdfDocumentStatus, uploadPdfForChat } from './api/pdf_rag'
import type { Attachment, Chat, Message, GeneratedImage } from './types/chat'
import type { PdfDocument } from './types/pdf_rag'
import { AttachmentPreview } from './components/chat/AttachmentPreview'
import { AttachmentUploadButton } from './components/chat/AttachmentUploadButton'
import { GeneratedImageDisplay } from './components/chat/GeneratedImageDisplay'
import { PdfDocumentStatusList } from './components/chat/PdfDocumentStatusList'
import { PdfUploadButton } from './components/chat/PdfUploadButton'
import './components/chat/ImageGeneration.css'

type ChatRole = 'user' | 'assistant'

type ChatMessage = {
  id: string
  role: ChatRole
  content: string
  attachments: Attachment[]
  generated_images?: GeneratedImage[]
}

function createId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function toUiMessages(items: Message[]): ChatMessage[] {
  return items.map((item) => ({
    id: item.id,
    role: item.role,
    content: item.content,
    attachments: item.attachments || [],
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
  const [pendingAttachments, setPendingAttachments] = useState<{ file: File; type: string }[]>([])
  const [pdfDocuments, setPdfDocuments] = useState<PdfDocument[]>([])

  const [isBootstrapping, setIsBootstrapping] = useState(false)
  const [isLoadingChats, setIsLoadingChats] = useState(false)
  const [isLoadingMessages, setIsLoadingMessages] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [isUploadingAttachment, setIsUploadingAttachment] = useState(false)
  const [isUploadingPdf, setIsUploadingPdf] = useState(false)
  const [isGeneratingImage, setIsGeneratingImage] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const listRef = useRef<HTMLDivElement | null>(null)
  const googleButtonRef = useRef<HTMLDivElement | null>(null)
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

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
          const [chatMessages, chatPdfDocs] = await Promise.all([
            getMessages(first.id),
            getChatPdfDocuments(first.id),
          ])
          if (cancelled) {
            return
          }
          setMessages(toUiMessages(chatMessages))
          setPdfDocuments(chatPdfDocs)
        } else {
          setActiveChatId(null)
          setMessages([])
          setPdfDocuments([])
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
      const [history, chatPdfDocs] = await Promise.all([
        getMessages(chatId),
        getChatPdfDocuments(chatId),
      ])
      setMessages(toUiMessages(history))
      setPdfDocuments(chatPdfDocs)
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
      setPdfDocuments([])
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
        const [history, chatPdfDocs] = await Promise.all([
          getMessages(first.id),
          getChatPdfDocuments(first.id),
        ])
        setMessages(toUiMessages(history))
        setPdfDocuments(chatPdfDocs)
      } else {
        setActiveChatId(null)
        setMessages([])
        setPdfDocuments([])
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
    setPdfDocuments([])
    setInput('')
    setPassword('')
    setError(null)
  }

  async function handleAttachmentSelect(file: File, fileType: string) {
    setError(null)
    // Store pending attachment - will be uploaded after message is sent
    setPendingAttachments((prev) => [...prev, { file, type: fileType }])
  }

  async function handleDownloadAttachment(attachmentId: string) {
    try {
      await downloadAttachment(attachmentId)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to download attachment'
      setError(message)
    }
  }

  async function refreshPdfDocuments(chatId: string) {
    try {
      const docs = await getChatPdfDocuments(chatId)
      setPdfDocuments(docs)
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Failed to load PDF documents'
      setError(message)
    }
  }

  async function pollPdfDocumentStatus(chatId: string, documentId: string) {
    let attempts = 0
    const maxAttempts = 180

    const poll = async () => {
      attempts += 1
      try {
        const latest = await getPdfDocumentStatus(documentId)
        setPdfDocuments((prev) => prev.map((item) => (item.id === latest.id ? latest : item)))

        if (latest.status === 'completed' || latest.status === 'failed' || attempts >= maxAttempts) {
          if (attempts >= maxAttempts && latest.status !== 'completed' && latest.status !== 'failed') {
            setError('PDF indexing timeout. You can ask questions later once processing finishes.')
          }
          return true
        }
      } catch {
        if (attempts >= maxAttempts) {
          return true
        }
      }
      return false
    }

    const doneImmediately = await poll()
    if (doneImmediately) {
      await refreshPdfDocuments(chatId)
      return
    }

    await new Promise<void>((resolve) => {
      const interval = setInterval(async () => {
        const done = await poll()
        if (done) {
          clearInterval(interval)
          resolve()
        }
      }, 1000)
    })

    await refreshPdfDocuments(chatId)
  }

  async function handlePdfUpload(file: File) {
    if (isSending || isGeneratingImage || isUploadingAttachment || isUploadingPdf || !token) {
      return
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are supported')
      return
    }

    setError(null)
    setIsUploadingPdf(true)

    try {
      let chatId = activeChatId
      if (!chatId) {
        const created = await createChat()
        chatId = created.id
        setActiveChatId(chatId)
      }

      const createdMessage = await createUserMessage(chatId, `Uploaded PDF: ${file.name}`)
      const uploadedDoc = await uploadPdfForChat(chatId, createdMessage.id, file)

      const uploadedMessage: ChatMessage = {
        id: createdMessage.id,
        role: 'user',
        content: `Uploaded PDF: ${file.name}`,
        attachments: [],
      }
      setMessages((prev) => {
        const exists = prev.some((msg) => msg.id === uploadedMessage.id)
        return exists ? prev : [...prev, uploadedMessage]
      })

      setPdfDocuments((prev) => {
        const exists = prev.some((item) => item.id === uploadedDoc.id)
        return exists ? prev : [uploadedDoc, ...prev]
      })

      await pollPdfDocumentStatus(chatId, uploadedDoc.id)
      await refreshChats(true)
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Failed to upload PDF'
      setError(message)
    } finally {
      setIsUploadingPdf(false)
    }
  }

  // Helper function to trigger image generation
  async function triggerImageGeneration(
    prompt: string,
    chatId: string,
    backendMessageId: string,
    targetUiMessageId: string,
  ) {
    try {
      setIsGeneratingImage(true)
      const generationResponse = await generateImage({
        prompt,
        chat_id: chatId,
        message_id: backendMessageId,
      })

      // Start polling for image generation status
      let pollCount = 0
      const maxPolls = 120

      const pollGeneration = async () => {
        if (pollCount >= maxPolls) {
          setError('Image generation timeout')
          setIsGeneratingImage(false)
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current)
            pollingIntervalRef.current = null
          }
          return
        }

        try {
          const status = await getImageStatus(generationResponse.id)
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === targetUiMessageId ? { ...msg, generated_images: [status] } : msg
            )
          )

          if (status.status === 'completed' || status.status === 'failed') {
            setIsGeneratingImage(false)
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current)
              pollingIntervalRef.current = null
            }
          }
          pollCount++
        } catch (err) {
          console.error('Polling failed:', err)
        }
      }

      await pollGeneration()
      if (generationResponse.status === 'pending') {
        pollingIntervalRef.current = setInterval(pollGeneration, 1000)
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate image'
      setError(message)
      setIsGeneratingImage(false)
    }
  }

  async function handleDeleteGeneratedImage(imageId: string) {
    try {
      await deleteGeneratedImage(imageId)
      setMessages((prev) =>
        prev.map((msg) => ({
          ...msg,
          generated_images: msg.generated_images?.filter((img) => img.id !== imageId),
        }))
      )
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete image'
      setError(message)
    }
  }

  // Cleanup polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [])

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
      attachments: [],
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

      // First, send the text message
      const attachmentContext = pendingAttachments.map(
        (item) => `${item.type}: ${item.file.name} (${item.file.type || 'unknown MIME'})`,
      )

      const response = await sendChatMessage({
        message: trimmed,
        chat_id: chatId,
        attachment_context: attachmentContext,
      })

      const messageIdForAttachments = response.user_message_id

      // If there are pending attachments, upload them to this message
      if (pendingAttachments.length > 0) {
        setIsUploadingAttachment(true)
        const uploadedAttachments: Attachment[] = []
        const summaryBlocks: string[] = []
        const extractionErrors: string[] = []
        const uploadErrors: string[] = []
        const extractionEligibleTypes = new Set(['image', 'video', 'document', 'code', 'formula'])

        for (const attachment of pendingAttachments) {
          try {
            console.log(`Uploading attachment: ${attachment.file.name} (${attachment.type})`)
            const result = await uploadAttachment(messageIdForAttachments, attachment.type, attachment.file)
            console.log(`Successfully uploaded: ${result.file_name}`)
            uploadedAttachments.push({
              id: result.id,
              file_name: result.file_name,
              file_type: result.file_type as any,
              mime_type: result.mime_type,
              file_size: result.file_size,
              upload_timestamp: result.upload_timestamp,
            })

            if (extractionEligibleTypes.has(attachment.type)) {
              try {
                const extracted = await extractAttachmentText(result.id)
                const summaryText = (extracted.summary_text || '').trim()
                if (summaryText.length > 0) {
                  summaryBlocks.push(`${result.file_name} [${extracted.attachment_type}]\n${summaryText}`)
                }
              } catch (ocrError) {
                const extractionMsg = ocrError instanceof Error ? ocrError.message : 'Content extraction failed'
                console.error(`Extraction failed for ${attachment.file.name}: ${extractionMsg}`)
                extractionErrors.push(`${attachment.file.name}: ${extractionMsg}`)
              }
            }
          } catch (attachError) {
            const msg = attachError instanceof Error ? attachError.message : 'Attachment upload failed'
            console.error(`Upload failed for ${attachment.file.name}: ${msg}`)
            uploadErrors.push(`${attachment.file.name}: ${msg}`)
          }
        }

        // Update the user message with attachments
        setMessages((prev) =>
          prev.map((msg) => (msg.id === userMessage.id ? { ...msg, attachments: uploadedAttachments } : msg))
        )

        if (uploadErrors.length > 0) {
          setError(`Attachment upload issues:\n${uploadErrors.join('\n')}`)
        } else if (extractionErrors.length > 0) {
          setError(`Attachment extraction issues:\n${extractionErrors.join('\n')}`)
        }

        if (summaryBlocks.length > 0) {
          response.reply = `I analyzed your uploaded file(s). Here is a clean summary:\n\n${summaryBlocks.join('\n\n---\n\n')}\n\n${response.reply}`
        }

        setPendingAttachments([])
        setIsUploadingAttachment(false)
      }

      const assistantMessage: ChatMessage = {
        id: createId(),
        role: 'assistant',
        content: response.reply,
        attachments: [],
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

  async function handleGenerateImageClick() {
    const trimmed = input.trim()
    if (!trimmed || isSending || isGeneratingImage || !token) {
      return
    }

    const userMessage: ChatMessage = {
      id: createId(),
      role: 'user',
      content: trimmed,
      attachments: [],
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setError(null)

    try {
      let chatId = activeChatId
      if (!chatId) {
        const created = await createChat()
        chatId = created.id
        setActiveChatId(chatId)
      }

      let backendMessageId: string
      try {
        const createdUserMessage = await createUserMessage(chatId, trimmed)
        backendMessageId = createdUserMessage.id
      } catch (requestError) {
        const message = requestError instanceof Error ? requestError.message : ''
        // Backward-compatibility path for servers that do not expose POST /api/chats/{chat_id}/messages yet.
        if (message.toLowerCase().includes('method not allowed') || message.includes('405')) {
          const response = await sendChatMessage({
            message: trimmed,
            chat_id: chatId,
          })
          backendMessageId = response.user_message_id
        } else {
          throw requestError
        }
      }

      const imageRequestMessage: ChatMessage = {
        id: createId(),
        role: 'assistant',
        content: `Generating image: ${trimmed}`,
        attachments: [],
        generated_images: [],
      }
      setMessages((prev) => [...prev, imageRequestMessage])

      await triggerImageGeneration(trimmed, chatId, backendMessageId, imageRequestMessage.id)
      await refreshChats(true)
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Failed to generate image'
      setError(message)
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
          <PdfDocumentStatusList items={pdfDocuments} isUploading={isUploadingPdf} />
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
              <div className="bubble">
                {message.content}
                {message.attachments && message.attachments.length > 0 && (
                  <div className="message-attachments">
                    {message.attachments.map((attachment) => (
                      <AttachmentPreview
                        key={attachment.id}
                        attachment={attachment}
                        onDownload={handleDownloadAttachment}
                      />
                    ))}
                  </div>
                )}
                {message.generated_images && message.generated_images.length > 0 && (
                  <div className="message-generated-images">
                    {message.generated_images.map((image) => (
                      <GeneratedImageDisplay
                        key={image.id}
                        image={image}
                        onDelete={handleDeleteGeneratedImage}
                      />
                    ))}
                  </div>
                )}
              </div>
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
            <div className="composer-input-wrapper">
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                className="composer-input"
                placeholder="Ask anything..."
                rows={2}
                disabled={isSending || isBootstrapping || isUploadingAttachment || isUploadingPdf || isGeneratingImage}
              />
              {pendingAttachments.length > 0 && (
                <div className="pending-attachments">
                  {pendingAttachments.map((attachment, idx) => (
                    <div key={idx} className="pending-attachment">
                      <span>{attachment.file.name}</span>
                      <button
                        type="button"
                        onClick={() =>
                          setPendingAttachments((prev) =>
                            prev.filter((_, i) => i !== idx)
                          )
                        }
                        className="remove-attachment"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
              <AttachmentUploadButton
                onAttachmentSelect={handleAttachmentSelect}
                disabled={isSending || isBootstrapping || isUploadingAttachment || isUploadingPdf || isGeneratingImage}
              />
              <PdfUploadButton
                onSelect={(file) => void handlePdfUpload(file)}
                disabled={isSending || isBootstrapping || isUploadingAttachment || isUploadingPdf || isGeneratingImage}
              />
              <button
                type="button"
                className="composer-send"
                onClick={() => void handleGenerateImageClick()}
                disabled={
                  isSending || isBootstrapping || isUploadingAttachment || isUploadingPdf || isGeneratingImage || input.trim().length === 0
                }
              >
                {isGeneratingImage ? 'Generating...' : 'Genrate Image'}
              </button>
              <button
                type="submit"
                className="composer-send"
                disabled={
                  isSending || isBootstrapping || isUploadingAttachment || isUploadingPdf || isGeneratingImage || input.trim().length === 0
                }
              >
                {isSending ? 'Sending...' : isUploadingAttachment ? 'Uploading...' : isUploadingPdf ? 'Indexing PDF...' : isGeneratingImage ? 'Generating...' : 'Send'}
              </button>
            </div>
          </form>
          {error ? <p className="error-text">{error}</p> : null}
        </footer>
      </section>
    </main>
  )
}

export default App
