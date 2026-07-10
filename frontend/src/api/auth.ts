import { apiFetch } from './client'
import type { TokenResponse, User } from './types'

// Exchange a Google ID token for our backend JWT + user.
export function loginWithGoogle(googleIdToken: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>('/auth/google', {
    method: 'POST',
    body: JSON.stringify({ token: googleIdToken }),
  })
}

// Fetch the current user for a stored JWT (used to restore sessions).
export function fetchMe(): Promise<User> {
  return apiFetch<User>('/auth/me')
}
