export type SheetSourceType = 'csv' | 'xlsx' | 'google_sheets'

export type SheetDatasourceStatus = 'pending' | 'processing' | 'ready' | 'failed'

export type SheetDatasource = {
  id: string
  chat_id: string
  user_id: string
  source_type: SheetSourceType
  file_name: string | null
  storage_path: string | null
  file_size_bytes: number | null
  sheet_url: string | null
  sheet_id: string | null
  sheet_tab: string | null
  status: SheetDatasourceStatus
  row_count: number | null
  column_count: number | null
  column_names: string[] | null
  sheet_tabs: string[] | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export type SheetUploadResponse = {
  datasource: SheetDatasource
}

export type ConnectGoogleSheetRequest = {
  chat_id: string
  sheet_url: string
  sheet_tab?: string | null
}

export type ConnectGoogleSheetResponse = {
  datasource: SheetDatasource
}

export type SheetQueryRequest = {
  datasource_id: string
  question: string
  chat_id?: string | null
  sheet_tab?: string | null
}

export type SheetQueryTableRow = {
  columns: string[]
  rows: string[][]
}

export type SheetQueryResponse = {
  chat_id: string
  user_message_id: string
  assistant_message_id: string
  datasource_id: string
  question: string
  answer: string
  table: SheetQueryTableRow | null
  execution_duration_ms: number
}

export type ListDatasourcesResponse = {
  items: SheetDatasource[]
}
