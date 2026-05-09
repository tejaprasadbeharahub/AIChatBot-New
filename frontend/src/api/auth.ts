import type { Token } from '../types/auth'
import { API_BASE_URL } from '../lib/api'

const TOKEN_KEY = 'amzur_access_token'

type GoogleCredentialResponse = {
  credential?: string
}

type GoogleButtonConfiguration = {
  theme?: 'outline' | 'filled_blue' | 'filled_black'
  size?: 'large' | 'medium' | 'small'
  text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin'
  shape?: 'rectangular' | 'pill' | 'circle' | 'square'
  width?: string
}

type GoogleIdApi = {
  initialize: (options: { client_id: string; callback: (response: GoogleCredentialResponse) => void }) => void
  renderButton: (parent: HTMLElement, options: GoogleButtonConfiguration) => void
}

declare global {
  interface Window {
    google?: {
      accounts?: {
        id?: {
          initialize: GoogleIdApi['initialize']
          renderButton: GoogleIdApi['renderButton']
        }
      }
    }
  }
}

let googleScriptPromise: Promise<void> | null = null

function ensureGoogleScript(): Promise<void> {
  if (window.google?.accounts?.id) {
    return Promise.resolve()
  }
  if (googleScriptPromise) {
    return googleScriptPromise
  }

  googleScriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load Google Identity script'))
    document.head.appendChild(script)
  })

  return googleScriptPromise
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export function storeToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export async function login(email: string, password: string): Promise<Token> {
  const body = new URLSearchParams()
  body.set('username', email)
  body.set('password', password)

  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
  })

  if (!response.ok) {
    let detail = `Login failed: ${response.status}`
    try {
      const err = (await response.json()) as { detail?: string }
      if (err?.detail) detail = err.detail
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }

  const token = (await response.json()) as Token
  storeToken(token.access_token)
  return token
}

export async function register(email: string, password: string): Promise<Token> {
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) {
    let detail = `Registration failed: ${response.status}`
    try {
      const err = (await response.json()) as { detail?: string }
      if (err?.detail) detail = err.detail
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }

  const payload = (await response.json()) as { token: Token }
  storeToken(payload.token.access_token)
  return payload.token
}

export async function googleLogin(token: string): Promise<Token> {
  const response = await fetch(`${API_BASE_URL}/api/auth/google/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token }),
  })

  if (!response.ok) {
    let detail = `Google login failed: ${response.status}`
    try {
      const err = (await response.json()) as { detail?: string }
      if (err?.detail) detail = err.detail
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }

  const payload = (await response.json()) as Token
  storeToken(payload.access_token)
  return payload
}

type RenderGoogleButtonOptions = {
  clientId: string
  container: HTMLElement
  onCredential: (token: string) => void | Promise<void>
  onError?: (message: string) => void
}

export async function renderGoogleSignInButton({ clientId, container, onCredential, onError }: RenderGoogleButtonOptions): Promise<void> {
  if (!clientId) {
    throw new Error('VITE_GOOGLE_CLIENT_ID is not configured')
  }

  await ensureGoogleScript()

  const api: GoogleIdApi | undefined = window.google?.accounts?.id
  if (!api) {
    throw new Error('Google Identity API is unavailable')
  }

  container.innerHTML = ''

  api.initialize({
    client_id: clientId,
    callback: (response) => {
      if (response.credential) {
        void onCredential(response.credential)
        return
      }
      onError?.('Google did not return a credential token')
    },
  })

  api.renderButton(container, {
    theme: 'outline',
    size: 'large',
    text: 'continue_with',
    shape: 'rectangular',
    width: '320',
  })
}
