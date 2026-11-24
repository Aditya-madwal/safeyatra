// Small helper for calling the FastAPI backend (Vite forwards /api to port 8000)

import { useCallback, useEffect, useState } from 'react'

export async function api(path, { token, method = 'GET', body, form } = {}) {
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}`
  let payload
  if (form) {
    payload = form // FormData: the browser sets the content type
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  let res
  try {
    res = await fetch(`/api${path}`, { method, headers, body: payload })
  } catch {
    throw new Error('Cannot reach the SafeYatra server. Is the backend running?')
  }
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = data?.detail
    const message = typeof detail === 'string' ? detail
      : Array.isArray(detail) ? detail.map((d) => d.msg).join(', ')
      : `Request failed (${res.status})`
    throw new Error(message)
  }
  return data
}

// Load data once when a component mounts; reload() fetches again
export function useApi(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const load = useCallback(() => {
    setState((s) => ({ ...s, loading: true }))
    api(path)
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => setState({ data: null, error, loading: false }))
  }, [path])
  useEffect(load, [load])
  return { ...state, reload: load }
}
