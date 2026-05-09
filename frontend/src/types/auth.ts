export type User = {
  id: string
  email: string
  is_active: boolean
  created_at: string
}

export type Token = {
  access_token: string
  token_type: string
}
