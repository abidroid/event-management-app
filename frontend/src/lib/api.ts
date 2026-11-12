/**
 * Typed functions for every backend endpoint.
 *
 * The types mirror the schemas in the backend's /openapi.json. Every request
 * goes through `request()`, so the base URL, the Bearer header and error
 * handling live in one place.
 */

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"
const TOKEN_KEY = "access_token"

// ---------- Types (from /openapi.json) ----------

/** UserRead: an account, never including the password. */
export interface User {
  id: number
  email: string
  full_name: string
  created_at: string
}

/** UserCreate: body for POST /auth/register. */
export interface UserCreate {
  email: string
  full_name: string
  password: string
}

/** Token: returned by POST /auth/login. */
export interface Token {
  access_token: string
  token_type: "bearer"
}

/** EventRead: an event plus its live sign-up numbers. Dates are ISO strings. */
export interface Event {
  id: number
  title: string
  description: string | null
  event_date: string
  location: string
  max_capacity: number
  created_by: number
  created_at: string
  updated_at: string
  registered_count: number
  seats_left: number
}

/** EventCreate: body for POST /events. */
export interface EventCreate {
  title: string
  description?: string | null
  event_date: string
  location: string
  max_capacity: number
}

/** EventUpdate: body for PUT /events/{id}; only the fields sent change. */
export type EventUpdate = Partial<EventCreate>

/** RegistrationRead: one sign-up with the registrant's name and email. */
export interface Registration {
  id: number
  event_id: number
  registered_at: string
  user: { full_name: string; email: string }
}

/** Query parameters for GET /events. */
export interface EventFilters {
  skip: number
  limit: number
  title?: string
  date?: string
}

// ---------- Token storage and error handling ----------

/** Read, save and clear the JWT in localStorage so it survives a page reload. */
export const tokenStorage = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (token: string): void => localStorage.setItem(TOKEN_KEY, token),
  clear: (): void => localStorage.removeItem(TOKEN_KEY),
}

/** An error response from the API, carrying its status and `detail` message. */
export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

// AuthContext registers what to do when the token is rejected (log out and
// go to /login). Kept as a callback so this file does not depend on React.
let onUnauthorized: () => void = () => {}

/** Set the function `request()` calls when an authenticated call returns 401. */
export function setUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler
}

/**
 * Turn an error body into one readable sentence.
 *
 * Handled errors send `{"detail": "message"}`; validation errors (422) send
 * `{"detail": [{loc, msg}, ...]}`, so the first one is shown with its field.
 */
function readDetail(body: unknown, fallback: string): string {
  if (typeof body !== "object" || body === null || !("detail" in body)) {
    return fallback
  }
  const detail = (body as { detail: unknown }).detail
  if (typeof detail === "string") return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { loc?: unknown[]; msg?: string }
    const field = first.loc?.at(-1)
    return field ? `${String(field)}: ${first.msg}` : (first.msg ?? fallback)
  }
  return fallback
}

/**
 * Send a request to the API and return the parsed JSON body.
 *
 * Adds the Bearer token when one is stored. Throws `ApiError` for any non-2xx
 * response; a 401 on anything except login also triggers the logout handler.
 */
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const token = tokenStorage.get()
  if (token) headers.set("Authorization", `Bearer ${token}`)
  if (typeof init.body === "string") headers.set("Content-Type", "application/json")

  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, { ...init, headers })
  } catch {
    throw new ApiError(0, "Cannot reach the API. Is the backend running?")
  }

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null)
    // A 401 from login just means a wrong password, not an expired session.
    if (response.status === 401 && path !== "/auth/login") onUnauthorized()
    throw new ApiError(response.status, readDetail(body, response.statusText))
  }
  // 204 No Content has no body to parse.
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

/** Build a query string, skipping empty values. */
function toQuery(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") query.set(key, String(value))
  }
  return query.toString()
}

// ---------- Auth ----------

/** POST /auth/register: create an account. */
export function register(data: UserCreate): Promise<User> {
  return request("/auth/register", { method: "POST", body: JSON.stringify(data) })
}

/** POST /auth/login: exchange email and password for a token (OAuth2 form). */
export function login(email: string, password: string): Promise<Token> {
  // OAuth2PasswordRequestForm expects form fields, with the email as `username`.
  const form = new URLSearchParams({ username: email, password })
  return request("/auth/login", { method: "POST", body: form })
}

/** GET /auth/me: the logged-in user. */
export function getMe(): Promise<User> {
  return request("/auth/me")
}

// ---------- Events ----------

/** GET /events: one page of events, optionally filtered by title and date. */
export function listEvents(filters: EventFilters): Promise<Event[]> {
  return request(`/events?${toQuery({ ...filters })}`)
}

/** GET /events/{id}: one event. */
export function getEvent(id: number): Promise<Event> {
  return request(`/events/${id}`)
}

/** POST /events: create an event. */
export function createEvent(data: EventCreate): Promise<Event> {
  return request("/events", { method: "POST", body: JSON.stringify(data) })
}

/** PUT /events/{id}: change an event. */
export function updateEvent(id: number, data: EventUpdate): Promise<Event> {
  return request(`/events/${id}`, { method: "PUT", body: JSON.stringify(data) })
}

/** DELETE /events/{id}: delete an event and its registrations. */
export function deleteEvent(id: number): Promise<void> {
  return request(`/events/${id}`, { method: "DELETE" })
}

// ---------- Registrations ----------

/** POST /events/{id}/registrations: register the logged-in user. */
export function registerForEvent(eventId: number): Promise<Registration> {
  return request(`/events/${eventId}/registrations`, { method: "POST" })
}

/** GET /events/{id}/registrations: one page of an event's registrations. */
export function listRegistrations(
  eventId: number,
  skip: number,
  limit: number,
): Promise<Registration[]> {
  return request(`/events/${eventId}/registrations?${toQuery({ skip, limit })}`)
}

/** DELETE /registrations/{id}: cancel one of the logged-in user's registrations. */
export function cancelRegistration(registrationId: number): Promise<void> {
  return request(`/registrations/${registrationId}`, { method: "DELETE" })
}
