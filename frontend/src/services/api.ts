let csrf = ''
export function setCsrf(value: string) { csrf = value }
export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, { method, credentials: 'include', headers: { 'Content-Type': 'application/json', ...(method !== 'GET' ? { 'X-CSRF-Token': csrf } : {}) }, body: body === undefined ? undefined : JSON.stringify(body) })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(typeof data.detail === 'string' ? data.detail : `Request failed (${response.status}). Check the fields and retry.`)
  }
  return response.json()
}
export function safeUrl(value?: string | null) {
  try { const u = new URL(value || ''); return ['https:', 'http:'].includes(u.protocol) ? u.href : undefined } catch { return undefined }
}
