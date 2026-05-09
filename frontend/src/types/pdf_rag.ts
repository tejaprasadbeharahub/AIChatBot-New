export type PdfDocumentStatus = 'pending' | 'processing' | 'completed' | 'failed'

export type PdfDocument = {
  id: string
  attachment_id: string
  message_id: string
  chat_id: string
  user_id: string
  file_name: string
  storage_path: string
  status: PdfDocumentStatus
  chunk_count: number | null
  embedding_model: string | null
  vector_collection_id: string | null
  error_message: string | null
  upload_timestamp: string
  processed_at: string | null
}

export type PdfUploadResponse = {
  document: PdfDocument
}

export type PdfChunkMatch = {
  chunk_id: string
  content: string
  document_id: string
  file_name: string
  chunk_index: number
  score: number
}

export type PdfQueryResponse = {
  query: string
  chat_id: string
  matches: PdfChunkMatch[]
}
