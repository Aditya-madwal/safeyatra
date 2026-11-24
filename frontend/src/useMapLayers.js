// Loads every map layer once. reloadRisk() re-fetches the parts that change
// (road risk colours, closures, user reports) e.g. after a report or rain update.

import { useCallback, useEffect, useState } from 'react'
import { api } from './api'

export function useMapLayers() {
  const [layers, setLayers] = useState({})
  const [error, setError] = useState(null)

  const reloadRisk = useCallback(async () => {
    try {
      const [segments, reports] = await Promise.all([api('/segments'), api('/reports/recent')])
      setLayers((l) => ({
        ...l,
        segments: { data: segments, version: (l.segments?.version || 0) + 1 },
        reports,
      }))
    } catch (err) {
      setError(err.message)
    }
  }, [])

  useEffect(() => {
    reloadRisk()
    Promise.all([api('/boundary'), api('/landslides'), api('/rivers'), api('/pois')])
      .then(([boundary, landslides, rivers, pois]) =>
        setLayers((l) => ({ ...l, boundary, landslides, rivers, pois })))
      .catch((err) => setError(err.message))
  }, [reloadRisk])

  return { layers, error, reloadRisk }
}
