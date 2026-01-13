import createClient, { type Middleware } from 'openapi-fetch'
import type { paths } from './schema'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003'

/**
 * Custom event dispatched when a 401 response is received.
 * The AuthContext listens for this to trigger sign-out.
 */
export const AUTH_UNAUTHORIZED_EVENT = 'auth:unauthorized'

/**
 * Auth middleware that injects the Bearer token from localStorage
 * and handles 401 responses by dispatching an event.
 */
const authMiddleware: Middleware = {
  async onRequest({ request }) {
    const token = localStorage.getItem('auth_token')
    if (token) {
      request.headers.set('Authorization', `Bearer ${token}`)
    }
    return request
  },
  async onResponse({ response }) {
    if (response.status === 401) {
      window.dispatchEvent(new CustomEvent(AUTH_UNAUTHORIZED_EVENT))
    }
    return response
  },
}

/**
 * Typed API client for the Registry Review backend.
 * Automatically includes auth token and handles 401 responses.
 */
export const api = createClient<paths>({ baseUrl: API_URL })
api.use(authMiddleware)

export type { paths }
