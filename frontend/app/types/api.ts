// Base Types
export interface UserBase {
  email: string
  first_name?: string
  last_name?: string
}

export interface DocumentBase {
  title: string
  document_type: string
  status: string
}

export interface DocumentVersionBase {
  version_number: number
  storage_path: string
  file_type: string
  is_signed: boolean
}

export interface DocumentChunkBase {
  chunk_index: number
  heading?: string
  raw_text: string
  page_number?: number
  char_start: number
  char_end: number
}

export interface AuditFlagBase {
  risk_level: string
  category: string
  issue_summary: string
  detailed_explanation: string
  playbook_counter_proposal?: string
  status: string
}

export interface ObligationBase {
  title: string
  description?: string
  due_date?: string
  trigger_condition?: string
  alert_lead_days: number
  status: string
}

export interface DocumentRelationshipBase {
  relationship_type: string
}

// Request Types
export interface DocumentCreate {
  file: File
  document_type: string
}

export interface DocumentUpdate {
  title?: string
  status?: string
}

export interface DocumentVersionCreate extends DocumentVersionBase {
  document_id: string
}

export interface DocumentChunkCreate extends DocumentChunkBase {
  document_version_id: string
}

export interface AuditFlagCreate extends AuditFlagBase {
  document_version_id: string
  document_chunk_id?: string
}

export interface AuditFlagStatusUpdate {
  status: string
}

export interface ObligationCreate extends ObligationBase {
  document_id: string
  document_chunk_id?: string
}

export interface ObligationStatusUpdate {
  status: string
}

export interface DocumentChatRequest {
  question: string
  flag_ids?: string[]
  obligation_ids?: string[]
  chunk_ids?: string[]
}

export interface DocumentRelationshipCreate extends DocumentRelationshipBase {
  source_document_id: string
  target_document_id: string
}

// Response Types
export interface UserResponse extends UserBase {
  id: string
  created_at: string
  updated_at: string
}

export interface DocumentResponse extends DocumentBase {
  id: string
  user_id: string
  current_version_id?: string
  created_at: string
  updated_at: string
}

export interface DocumentVersionResponse extends DocumentVersionBase {
  id: string
  document_id: string
  parsed_markdown?: string
  created_at: string
}

export interface DocumentChunkResponse extends DocumentChunkBase {
  id: string
  document_version_id: string
  created_at: string
}

export interface AuditFlagResponse extends AuditFlagBase {
  id: string
  document_version_id: string
  document_chunk_id?: string
  created_at: string
}

export interface ObligationResponse extends ObligationBase {
  id: string
  document_id: string
  document_chunk_id?: string
  created_at: string
  updated_at: string
}

export interface DocumentRelationshipResponse extends DocumentRelationshipBase {
  id: string
  source_document_id: string
  target_document_id: string
  created_at: string
}

export interface DocumentChatResponse {
  answer: string
  sources?: Array<{
    type: 'flag' | 'obligation' | 'chunk'
    id: string
  }>
}

export interface DocumentRelationshipSuccessResponse {
  id: string
  status: string
}

export interface DocumentFlagSummary {
  total: number
  unresolved: number
  resolved: number
  by_risk_level: Record<string, number>
}

export interface DocumentVersionSummary {
  id: string
  version_number: number
  created_at: string
  storage_path: string
  file_type: string
  is_signed: boolean
  flag_count: number
}

export interface DocumentDetailResponse {
  document: DocumentResponse
  versions: DocumentVersionSummary[]
  flag_summary: DocumentFlagSummary
}

export interface DocumentChunkPreviewResponse {
  id: string
  chunk_index: number
  heading?: string
  page_number?: number
  preview_text: string
}

export interface DeepAnalysisViewResponse {
  document: DocumentResponse
  active_version: DocumentVersionResponse
  flag_summary: DocumentFlagSummary
  flags: AuditFlagResponse[]
  chunk_count: number
  chunk_preview: DocumentChunkPreviewResponse[]
  obligation_count: number
  obligations: ObligationResponse[]
}

// Error Types
export interface ValidationError {
  loc: (string | number)[]
  msg: string
  type: string
  input?: unknown
  ctx?: Record<string, unknown>
}

export interface HTTPValidationError {
  detail: ValidationError[]
}
