export type DBProvider = 'postgresql' | 'mysql' | 'sqlserver' | 'sqlite'

export type DBConnection = {
  id: string
  user_id: string
  name: string
  provider: DBProvider
  host: string | null
  port: number | null
  database_name: string | null
  username: string | null
  sqlite_path: string | null
  extra_options: Record<string, unknown> | null
  is_active: boolean
  has_password: boolean
  last_validated_at: string | null
  created_at: string
  updated_at: string
}

export type DBConnectionCreateRequest = {
  name: string
  provider: DBProvider
  host?: string
  port?: number
  database_name?: string
  username?: string
  password?: string
  sqlite_path?: string
  extra_options?: Record<string, unknown>
}

export type DBConnectionUpdateRequest = Partial<DBConnectionCreateRequest> & {
  is_active?: boolean
}

export type DBConnectionValidationResponse = {
  success: boolean
  message: string
}

export type SchemaColumn = {
  name: string
  data_type: string
  nullable: boolean
}

export type SchemaRelationship = {
  constrained_columns: string[]
  referred_table: string | null
  referred_columns: string[]
}

export type SchemaTable = {
  table_name: string
  columns: SchemaColumn[]
  relationships: SchemaRelationship[]
}

export type SchemaMetadataResponse = {
  connection_id: string
  tables: SchemaTable[]
}

export type SQLExecutionStatus = 'pending' | 'succeeded' | 'failed'

export type SQLQueryExecution = {
  id: string
  connection_id: string
  user_id: string
  chat_id: string
  message_id: string | null
  user_question: string
  generated_sql: string
  sql_explanation: string | null
  execution_status: SQLExecutionStatus
  error_message: string | null
  execution_started_at: string
  execution_finished_at: string | null
  execution_duration_ms: number | null
  row_count: number | null
  returned_columns: string[]
  result_rows: Array<Record<string, unknown>>
  retry_count: number
}

export type ExecuteNLQueryRequest = {
  connection_id: string
  question: string
  chat_id?: string
  max_rows?: number
}

export type ExecuteNLQueryResponse = {
  chat_id: string
  user_message_id: string
  assistant_message_id: string
  reply: string
  execution: SQLQueryExecution
}

export type SQLQueryHistoryResponse = {
  items: SQLQueryExecution[]
}
