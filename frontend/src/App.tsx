import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { clearStoredToken, getStoredToken, googleLogin, renderGoogleSignInButton } from './api/auth'
import { login, register } from './api/auth'
import { createChat, createUserMessage, deleteChat, extractAttachmentText, getChats, getMessages, sendChatMessage, uploadAttachment, updateChatTitle } from './api/chat'
import { generateImage, getImageStatus, deleteGeneratedImage } from './api/image_generation'
import { getChatPdfDocuments, getPdfDocumentStatus, uploadPdfForChat } from './api/pdf_rag'
import type { Attachment, Chat, Message, GeneratedImage } from './types/chat'
import type { PdfDocument } from './types/pdf_rag'
import { AttachmentUploadButton } from './components/chat/AttachmentUploadButton'
import { GeneratedImageDisplay } from './components/chat/GeneratedImageDisplay'
import { PdfDocumentStatusList } from './components/chat/PdfDocumentStatusList'
import { PdfUploadButton } from './components/chat/PdfUploadButton'
import './components/chat/ImageGeneration.css'
import { SQLQueryResult } from './components/sql/SQLQueryResult'
import { NLSQLComposer } from './components/sql/NLSQLComposer'
import { DBConnectionManager } from './components/sql/DBConnectionManager'
import './components/sql/sql.css'
import { executeNLSQL } from './api/nl_sql'
import { runResearchQuery } from './api/research_agent'
import type { SQLQueryExecution } from './types/nl_sql'
import { SheetUploadButton } from './components/sheet/SheetUploadButton'
import { GoogleSheetConnect } from './components/sheet/GoogleSheetConnect'
import { SheetDatasourceList } from './components/sheet/SheetDatasourceList'
import { SheetComposer } from './components/sheet/SheetComposer'
import { SheetQueryResult } from './components/sheet/SheetQueryResult'
import { ResearchDigestView } from './components/ResearchDigestView'
import { TicTacToeGame } from './components/TicTacToe/TicTacToeGame'
import { FarmerDashboard } from './components/FarmerDashboard/FarmerDashboard'
import './components/sheet/sheet.css'
import { listChatDatasources, uploadSheetFile } from './api/sheet_agent'
import type { SheetDatasource, SheetQueryResponse } from './types/sheet_agent'

const SHEET_RESULT_MARKER_PREFIX = '\n\n[SHEET_RESULT]'
const RESEARCH_DIGEST_MARKER_PREFIX = '\n\n[RESEARCH_DIGEST]'

type ResearchDigest = {
  summary: string
  key_findings: Array<{ topic: string; finding: string; evidence_papers: string[] }>
  methodologies: Array<{ name: string; frequency: number; papers: string[] }>
  limitations: string[]
  trends: Array<{ trend: string; direction: 'increasing' | 'decreasing' | 'stable'; recent_papers: string[] }>
  total_papers_reviewed: number
  papers_cited: Array<{
    arxiv_id: string
    title: string
    authors: string[]
    abstract: string
    published_date: string
    categories: string[]
    pdf_url: string
    relevance_score: number
  }>
  search_duration_seconds: number
}

function parsePersistedSheetResult(rawContent: string): { cleanContent: string; sheetResult: SheetQueryResponse | null } {
  const markerIndex = rawContent.lastIndexOf(SHEET_RESULT_MARKER_PREFIX)
  if (markerIndex === -1) {
    return { cleanContent: rawContent, sheetResult: null }
  }

  const cleanContent = rawContent.slice(0, markerIndex)
  const markerPayload = rawContent.slice(markerIndex + SHEET_RESULT_MARKER_PREFIX.length).trim()

  try {
    const parsed = JSON.parse(markerPayload) as {
      datasource_id?: string
      question?: string
      answer?: string
      table?: SheetQueryResponse['table']
      execution_duration_ms?: number
    }

    if (!parsed.answer || !parsed.datasource_id) {
      return { cleanContent: rawContent, sheetResult: null }
    }

    const hydrated: SheetQueryResponse = {
      chat_id: '',
      user_message_id: '',
      assistant_message_id: '',
      datasource_id: parsed.datasource_id,
      question: parsed.question ?? '',
      answer: parsed.answer,
      table: parsed.table ?? null,
      execution_duration_ms: parsed.execution_duration_ms ?? 0,
    }

    return { cleanContent, sheetResult: hydrated }
  } catch {
    return { cleanContent: rawContent, sheetResult: null }
  }
}

function parsePersistedResearchDigest(rawContent: string): {
  cleanContent: string
  researchDigest: ResearchDigest | null
  researchQuery: string | null
} {
  const markerIndex = rawContent.lastIndexOf(RESEARCH_DIGEST_MARKER_PREFIX)
  if (markerIndex === -1) {
    return { cleanContent: rawContent, researchDigest: null, researchQuery: null }
  }

  const cleanContent = rawContent.slice(0, markerIndex)
  const markerPayload = rawContent.slice(markerIndex + RESEARCH_DIGEST_MARKER_PREFIX.length).trim()

  let researchQuery: string | null = null
  const queryMatch = cleanContent.match(/Research completed on:\s*(.+)/i)
  if (queryMatch?.[1]) {
    researchQuery = queryMatch[1].trim()
  }

  try {
    const parsed = JSON.parse(markerPayload) as ResearchDigest
    return { cleanContent, researchDigest: parsed, researchQuery }
  } catch {
    return { cleanContent: rawContent, researchDigest: null, researchQuery: null }
  }
}

type ChatRole = 'user' | 'assistant'

type ChatMessage = {
  id: string
  role: ChatRole
  content: string
  attachments: Attachment[]
  generated_images?: GeneratedImage[]
  alignment?: 'right' | 'left'
  sql_query_executions?: SQLQueryExecution[]
  sheet_result?: SheetQueryResponse
  research_digest?: ResearchDigest
  research_query?: string
}

function createId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function toUiMessages(items: Message[]): ChatMessage[] {
  return items.map((item) => {
    const parsedResearch = item.role === 'assistant'
      ? parsePersistedResearchDigest(item.content)
      : { cleanContent: item.content, researchDigest: null, researchQuery: null }

    const parsedSheet = item.role === 'assistant'
      ? parsePersistedSheetResult(parsedResearch.cleanContent)
      : { cleanContent: parsedResearch.cleanContent, sheetResult: null }

    return {
      id: item.id,
      role: item.role, // Preserve the original role for alignment
      content: parsedSheet.cleanContent,
      attachments: item.attachments || [],
      generated_images: item.generated_images || [],
      alignment: item.role === 'user' ? 'right' : 'left',
      sql_query_executions: (item as Message & { sql_query_executions?: SQLQueryExecution[] }).sql_query_executions ?? [],
      sheet_result: parsedSheet.sheetResult ?? undefined,
      research_digest: parsedResearch.researchDigest ?? undefined,
      research_query: parsedResearch.researchQuery ?? undefined,
    }
  })
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
  const [isRunningNLSQL, setIsRunningNLSQL] = useState(false)
  const [mainAppMode, setMainAppMode] = useState<'chat' | 'farm'>('chat')
  const [chatMode, setChatMode] = useState<'chat' | 'database' | 'sheets' | 'research' | 'tictactoe'>('chat')
  const [researchDepth, setResearchDepth] = useState<'quick' | 'balanced' | 'deep'>('balanced')
  const [researchMaxPapers, setResearchMaxPapers] = useState<number>(20)
  const [showDBManager, setShowDBManager] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [sheetDatasources, setSheetDatasources] = useState<SheetDatasource[]>([])
  const [selectedDatasource, setSelectedDatasource] = useState<SheetDatasource | null>(null)
  const [isUploadingSheet, setIsUploadingSheet] = useState(false)
  const [isQueryingSheet, setIsQueryingSheet] = useState(false)

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
          const chatMessages = await getMessages(first.id)
          if (cancelled) {
            return
          }
          setMessages(toUiMessages(chatMessages))

          const [pdfResult, datasourceResult] = await Promise.allSettled([
            getChatPdfDocuments(first.id),
            listChatDatasources(first.id),
          ])
          if (cancelled) {
            return
          }

          if (pdfResult.status === 'fulfilled') {
            setPdfDocuments(pdfResult.value)
          } else {
            setPdfDocuments([])
            console.warn('Failed to load PDF documents during bootstrap:', pdfResult.reason)
          }

          if (datasourceResult.status === 'fulfilled') {
            setSheetDatasources(datasourceResult.value)
          } else {
            setSheetDatasources([])
            console.warn('Failed to load sheet datasources during bootstrap:', datasourceResult.reason)
          }

          setSelectedDatasource(null)
        } else {
          setActiveChatId(null)
          setMessages([])
          setPdfDocuments([])
          setSheetDatasources([])
          setSelectedDatasource(null)
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }
        const rawMessage = requestError instanceof Error ? requestError.message : 'Could not load chats'
        const message = rawMessage.toLowerCase() === 'failed to fetch' ? null : rawMessage
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
    setSelectedDatasource(null)
    setIsLoadingMessages(true)
    setError(null)
    try {
      const history = await getMessages(chatId)
      setMessages(toUiMessages(history))

      const [pdfResult, datasourceResult] = await Promise.allSettled([
        getChatPdfDocuments(chatId),
        listChatDatasources(chatId),
      ])

      if (pdfResult.status === 'fulfilled') {
        setPdfDocuments(pdfResult.value)
      } else {
        setPdfDocuments([])
        console.warn('Failed to load PDF documents for chat:', pdfResult.reason)
      }

      if (datasourceResult.status === 'fulfilled') {
        setSheetDatasources(datasourceResult.value)
      } else {
        setSheetDatasources([])
        console.warn('Failed to load sheet datasources for chat:', datasourceResult.reason)
      }
    } catch (requestError) {
      const rawMessage = requestError instanceof Error ? requestError.message : 'Could not load chat messages'
      const message = rawMessage.toLowerCase() === 'failed to fetch' ? null : rawMessage
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
      setSheetDatasources([])
      setSelectedDatasource(null)
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

        const [pdfResult, datasourceResult] = await Promise.allSettled([
          getChatPdfDocuments(first.id),
          listChatDatasources(first.id),
        ])

        if (pdfResult.status === 'fulfilled') {
          setPdfDocuments(pdfResult.value)
        } else {
          setPdfDocuments([])
          console.warn('Failed to load PDF documents after deleting chat:', pdfResult.reason)
        }

        if (datasourceResult.status === 'fulfilled') {
          setSheetDatasources(datasourceResult.value)
        } else {
          setSheetDatasources([])
          console.warn('Failed to load sheet datasources after deleting chat:', datasourceResult.reason)
        }

        setSelectedDatasource(null)
      } else {
        setActiveChatId(null)
        setMessages([])
        setPdfDocuments([])
        setSheetDatasources([])
        setSelectedDatasource(null)
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
              file_type: result.file_type as Attachment['file_type'],
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

  async function handleSheetUpload(file: File) {
    if (!activeChatId || isUploadingSheet) return
    setIsUploadingSheet(true)
    setError(null)
    try {
      const datasource = await uploadSheetFile(activeChatId, file)
      setSheetDatasources((prev) => {
        const exists = prev.some((ds) => ds.id === datasource.id)
        return exists ? prev : [datasource, ...prev]
      })
      setSelectedDatasource(datasource)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload file')
    } finally {
      setIsUploadingSheet(false)
    }
  }

  function handleSheetQueryResult(result: SheetQueryResponse) {
    const userMsg: ChatMessage = {
      id: result.user_message_id,
      role: 'user',
      content: result.question,
      attachments: [],
      alignment: 'right',
    }
    const assistantMsg: ChatMessage = {
      id: result.assistant_message_id,
      role: 'assistant',
      content: result.answer,
      attachments: [],
      alignment: 'left',
      sheet_result: result,
    }
    setMessages((prev) => [...prev, userMsg, assistantMsg])
  }

  async function handleNLSQLQuery(connectionId: string, question: string) {
    if (isRunningNLSQL || isSending || !token) return
    setIsRunningNLSQL(true)
    setError(null)

    const userMsg: ChatMessage = {
      id: createId(),
      role: 'user',
      content: question,
      attachments: [],
      alignment: 'right',
    }
    setMessages((prev) => [...prev, userMsg])

    try {
      const result = await executeNLSQL({
        connection_id: connectionId,
        question,
        chat_id: activeChatId ?? undefined,
      })

      setActiveChatId(result.chat_id)

      const assistantMsg: ChatMessage = {
        id: result.assistant_message_id,
        role: 'assistant',
        content: result.reply,
        attachments: [],
        alignment: 'left',
        sql_query_executions: [result.execution],
      }
      setMessages((prev) => [...prev, assistantMsg])
      await refreshChats(true)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Database query failed')
    } finally {
      setIsRunningNLSQL(false)
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

  async function handleResearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
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
    setIsSending(true)

    try {
      let chatId = activeChatId
      if (!chatId) {
        const created = await createChat()
        chatId = created.id
        setActiveChatId(chatId)
      }

      const response = await runResearchQuery({
        query: trimmed,
        chat_id: chatId,
        depth: researchDepth,
        max_papers: researchMaxPapers,
      })

      const assistantMessage: ChatMessage = {
        id: createId(),
        role: 'assistant',
        content: response.digest.summary,
        attachments: [],
        research_digest: response.digest,
        research_query: response.query,
      }

      setMessages((prev) => [...prev, assistantMessage])
      setActiveChatId(response.chat_id)
      await refreshChats(true)
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Research request failed'
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

  // Show Farm Dashboard if in farm mode
  if (mainAppMode === 'farm') {
    return (
      <div>
        <button
          onClick={() => setMainAppMode('chat')}
          style={{
            position: 'fixed',
            top: '10px',
            right: '10px',
            zIndex: 1000,
            padding: '8px 16px',
            backgroundColor: '#4B5563',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          ← Back to Chat
        </button>
        <FarmerDashboard />
      </div>
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
          <div style={{ display: 'flex', gap: '8px' }}>
            <button type="button" className="ghost-btn" onClick={handleLogout}>
              Logout
            </button>
          </div>
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

        <button
          type="button"
          className="ghost-btn"
          style={{ marginTop: '8px' }}
          onClick={() => setShowDBManager((v) => !v)}
        >
          {showDBManager ? '✕ Close DB Manager' : '🗄 Databases'}
        </button>
        {showDBManager && (
          <div style={{ marginTop: '8px', overflow: 'auto', maxHeight: '340px' }}>
            <DBConnectionManager
              selectedConnectionId={null}
              onConnectionSelected={() => {
                setChatMode('database')
                setShowDBManager(false)
              }}
            />
          </div>
        )}
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
          {chatMode === 'tictactoe' ? (
            <TicTacToeGame />
          ) : null}
          {chatMode !== 'tictactoe' && (isBootstrapping || isLoadingMessages) ? <p className="meta-text">Loading messages...</p> : null}
          {chatMode !== 'tictactoe' && !isBootstrapping && !isLoadingMessages && messages.length === 0 ? (
            <article className="bubble-row bubble-assistant">
              <div className="bubble">Hello. Start typing and I will save this chat automatically.</div>
            </article>
          ) : null}
          {chatMode !== 'tictactoe' && messages.map((message) => (
            <>
              {message.role === 'user' && message.content && (
                <article key={`${message.id}-text`} className="bubble-row bubble-user"> {/* User input on the right */}
                  <div className="bubble">{message.content}</div>
                </article>
              )}
              {message.role === 'assistant' && message.content && (!message.generated_images || message.generated_images.length === 0) && (
                <article key={`${message.id}-text`} className="bubble-row bubble-assistant">
                  <div className="bubble">
                    {message.research_digest ? (
                      <ResearchDigestView
                        digest={message.research_digest}
                        query={message.research_query || 'Research Query'}
                      />
                    ) : (
                      <span>{message.content}</span>
                    )}
                    {message.sql_query_executions && message.sql_query_executions.length > 0 &&
                      message.sql_query_executions.map((exec) => (
                        <SQLQueryResult key={exec.id} execution={exec} />
                      ))
                    }
                    {message.sheet_result && (
                      <SheetQueryResult result={message.sheet_result} />
                    )}
                  </div>
                </article>
              )}
              {message.generated_images && message.generated_images.length > 0 && (
                message.generated_images.map((image) => (
                  <article key={`${message.id}-image-${image.id}`} className="bubble-row bubble-assistant"> {/* Rendered image on the left */}
                    <div className="bubble">
                      <GeneratedImageDisplay
                        image={image}
                        onDelete={handleDeleteGeneratedImage}
                      />
                      <p className="image-prompt">Prompt: {message.content}</p> {/* Text under the image */}
                    </div>
                  </article>
                ))
              )}
            </>
          ))}

          {isSending ? (
            <article className="bubble-row bubble-assistant">
              <div className="bubble bubble-loading">Thinking</div>
            </article>
          ) : null}
          {isRunningNLSQL ? (
            <article className="bubble-row bubble-assistant">
              <div className="bubble bubble-loading">Querying database</div>
            </article>
          ) : null}
          {isQueryingSheet ? (
            <article className="bubble-row bubble-assistant">
              <div className="bubble bubble-loading">Analyzing data</div>
            </article>
          ) : null}
        </div>

        <footer className="chat-footer">
          <div className="chat-mode-toggle">
            <button
              type="button"
              className={chatMode === 'chat' ? 'mode-pill active' : 'mode-pill'}
              onClick={() => setChatMode('chat')}
            >💬 Chat</button>
            <button
              type="button"
              className={chatMode === 'database' ? 'mode-pill active' : 'mode-pill'}
              onClick={() => setChatMode('database')}
            >🗄 Database</button>
            <button
              type="button"
              className={chatMode === 'sheets' ? 'mode-pill active' : 'mode-pill'}
              onClick={() => setChatMode('sheets')}
            >📊 Sheets</button>
            <button
              type="button"
              className={chatMode === 'research' ? 'mode-pill active' : 'mode-pill'}
              onClick={() => setChatMode('research')}
            >🔬 Research</button>
            <button
              type="button"
              className={chatMode === 'tictactoe' ? 'mode-pill active' : 'mode-pill'}
              onClick={() => setChatMode('tictactoe')}
            >🎮 Game</button>
            <button
              type="button"
              className="mode-pill"
              onClick={() => setMainAppMode('farm')}
              title="Farm AI Dashboard"
            >🌾 Farm</button>
          </div>
          {chatMode === 'sheets' ? (
            <div style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <SheetDatasourceList
                items={sheetDatasources}
                isUploading={isUploadingSheet}
                onDeleted={(id) => {
                  setSheetDatasources((prev) => prev.filter((ds) => ds.id !== id))
                  if (selectedDatasource?.id === id) setSelectedDatasource(null)
                }}
                onSelect={setSelectedDatasource}
                selectedId={selectedDatasource?.id ?? null}
              />
              {selectedDatasource ? (
                <SheetComposer
                  chatId={activeChatId ?? ''}
                  datasource={selectedDatasource}
                  onResult={(result) => {
                    setIsQueryingSheet(false)
                    handleSheetQueryResult(result)
                  }}
                  onClear={() => setSelectedDatasource(null)}
                />
              ) : (
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', position: 'relative' }}>
                  <SheetUploadButton
                    onSelect={(file) => void handleSheetUpload(file)}
                    disabled={!activeChatId || isUploadingSheet}
                  />
                  <div style={{ position: 'relative' }}>
                    <GoogleSheetConnect
                      chatId={activeChatId ?? ''}
                      onConnected={(ds) => {
                        setSheetDatasources((prev) => {
                          const exists = prev.some((d) => d.id === ds.id)
                          return exists ? prev : [ds, ...prev]
                        })
                        setSelectedDatasource(ds)
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          ) : chatMode === 'database' ? (
            <div style={{ padding: '10px 12px' }}>
              <NLSQLComposer
                onSubmit={(cid, q) => void handleNLSQLQuery(cid, q)}
                isLoading={isRunningNLSQL}
                activeChatId={activeChatId}
                disabled={isSending || isBootstrapping}
              />
            </div>
          ) : chatMode === 'tictactoe' ? null : chatMode === 'research' ? (
            <form onSubmit={handleResearchSubmit} className="composer">
              <div className="composer-input-wrapper">
                <textarea
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  className="composer-input"
                  placeholder="Ask a research question (for example: latest advances in agentic AI)"
                  rows={2}
                  disabled={isSending || isBootstrapping || isGeneratingImage}
                />
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span className="meta-text" style={{ margin: 0 }}>Depth</span>
                  <select
                    value={researchDepth}
                    onChange={(event) => setResearchDepth(event.target.value as 'quick' | 'balanced' | 'deep')}
                    disabled={isSending || isBootstrapping}
                  >
                    <option value="quick">Quick</option>
                    <option value="balanced">Balanced</option>
                    <option value="deep">Deep</option>
                  </select>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span className="meta-text" style={{ margin: 0 }}>Max papers</span>
                  <input
                    type="number"
                    min={1}
                    max={50}
                    value={researchMaxPapers}
                    onChange={(event) => setResearchMaxPapers(Math.max(1, Math.min(50, Number(event.target.value) || 20)))}
                    disabled={isSending || isBootstrapping}
                    style={{ width: '80px' }}
                  />
                </label>
                <button
                  type="submit"
                  className="composer-send"
                  disabled={isSending || isBootstrapping || input.trim().length === 0}
                >
                  {isSending ? 'Researching...' : 'Run Research Agent'}
                </button>
              </div>
            </form>
          ) : (
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
                type="submit"
                className="composer-send"
                disabled={
                  isSending || isBootstrapping || isUploadingAttachment || isUploadingPdf || isGeneratingImage || input.trim().length === 0
                }
              >
                {isSending ? 'Sending...' : isUploadingAttachment ? 'Uploading...' : isUploadingPdf ? 'Indexing PDF...' : isGeneratingImage ? 'Generating...' : 'Send'}
              </button>
              <button
                type="button"
                className="composer-send"
                onClick={() => void handleGenerateImageClick()}
                disabled={
                  isSending || isBootstrapping || isUploadingAttachment || isUploadingPdf || isGeneratingImage || input.trim().length === 0
                }
              >
                {isGeneratingImage ? 'Generating...' : 'Generate Image'}
              </button>
            </div>
          </form>
          )}
          {error ? <p className="error-text">{error}</p> : null}
        </footer>
      </section>
    </main>
  )
}

export default App
