import { useEffect, useState } from 'react'
import { api } from '../services/api'
export function useApi<T>(path: string) {
  const [data, setData] = useState<T>()
  const [error, setError] = useState('')
  const [version, setVersion] = useState(0)
  useEffect(() => {
    let active = true
    setData(undefined); setError('')
    api<T>(path).then(value => { if (active) setData(value) }).catch(e => { if (active) setError(e.message) })
    return () => { active = false }
  }, [path, version])
  return { data, error, reload: () => setVersion(v => v + 1) }
}
