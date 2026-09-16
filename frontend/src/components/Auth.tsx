import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, setCsrf } from '../services/api'
import type { Session } from '../types'
const Context = createContext<{ session?: Session; error: string; refresh: () => Promise<void> }>({ error: '', refresh: async () => {} })
export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session>()
  const [error, setError] = useState('')
  async function refresh() { try { const data = await api<Session>('/auth/me'); setCsrf(data.csrf); setSession(data); setError('') } catch (e) { setError((e as Error).message) } }
  useEffect(() => { void refresh() }, [])
  return <Context.Provider value={{ session, error, refresh }}>{children}</Context.Provider>
}
export const useAuth = () => useContext(Context)
