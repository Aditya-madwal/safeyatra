// Panel shown when a road is clicked: its risk and the factors behind it

import { Ban, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api'
import { FACTOR_LABELS } from '../constants'
import { Notice, RiskIndicator, Skeleton } from './ui.jsx'

const HIGHWAY_LABEL = {
  trunk: 'National highway', primary: 'Main road', secondary: 'District road',
  tertiary: 'Link road', unclassified: 'Village road', residential: 'Street',
}

function Detail({ label, value }) {
  if (value === null || value === undefined || value === false || value === '') return null
  return (
    <div className="flex justify-between gap-3 py-1.5">
      <dt className="text-base-content/55">{label}</dt>
      <dd className="tabular text-right">{value}</dd>
    </div>
  )
}

export default function SegmentDetails({ id, onClose }) {
  const [seg, setSeg] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    setSeg(null)
    setError(null)
    api(`/segments/${id}`).then(setSeg).catch((e) => setError(e.message))
  }, [id])

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const kind = seg && (HIGHWAY_LABEL[(seg.highway || '').replace('_link', '')] || 'Road')

  return (
    <aside aria-label="Road details"
      className="animate-in absolute right-3 bottom-4 z-[600] flex max-h-[calc(100%-5.5rem)] w-[330px] max-w-[calc(100%-1.5rem)] flex-col overflow-hidden rounded-lg border border-base-300 bg-base-100 shadow-lg">
      <div className="flex items-start justify-between gap-3 border-b border-base-300 px-4 py-3">
        <div className="min-w-0">
          <p className="text-xs text-base-content/55">{kind || 'Road segment'}</p>
          <h3 className="truncate text-[15px] font-semibold">
            {seg ? (seg.name || seg.ref || 'Unnamed road') : <Skeleton className="mt-1 h-4 w-40" />}
          </h3>
        </div>
        <button type="button" onClick={onClose} aria-label="Close road details"
          className="grid size-7 shrink-0 place-items-center rounded text-base-content/50 transition-colors hover:bg-base-200 hover:text-base-content">
          <X className="size-4" />
        </button>
      </div>

      <div className="overflow-y-auto px-4 py-4 text-[13px]">
        {error && <Notice tone="error">{error}</Notice>}
        {!seg && !error && (
          <div className="space-y-3">
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-5/6" />
            <Skeleton className="h-3 w-4/6" />
          </div>
        )}
        {seg && (
          <div className="space-y-5">
            <div>
              <div className="flex items-baseline gap-3">
                <span className="tabular text-[28px] leading-none font-semibold tracking-tight">{seg.risk_now.toFixed(2)}</span>
                <RiskIndicator cls={seg.risk_class_now} />
              </div>
              <p className="mt-1.5 text-xs text-base-content/55">
                Risk score from 0 to 1
                {seg.risk_now !== seg.static_risk && <> · normally {seg.static_risk.toFixed(2)}</>}
              </p>
            </div>

            {seg.closed && (
              <Notice tone="error" icon={Ban}>This road is closed and is skipped when planning routes.</Notice>
            )}

            <div>
              <h4 className="section-label mb-2">Why</h4>
              <ul className="space-y-1">
                {seg.reasons.map((r) => (
                  <li key={r} className="flex items-center gap-2">
                    <span className="size-1 rounded-full bg-base-content/40" aria-hidden />
                    <span className="first-letter:uppercase">{r}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="section-label mb-2">Risk factors</h4>
              <div className="space-y-2.5">
                {seg.factors.map((f) => (
                  <div key={f.factor}>
                    <div className="mb-1 flex justify-between text-xs">
                      <span>
                        {FACTOR_LABELS[f.factor] || f.factor}
                        {f.factor === 'susceptibility' && seg.susc_source && (
                          <span className="text-base-content/45"> · {seg.susc_source}</span>
                        )}
                      </span>
                      <span className="tabular text-base-content/50">{Math.round(f.value * 100)} · {Math.round(f.weight * 100)}% weight</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-base-200">
                      <div className="h-full rounded-full bg-primary/70" style={{ width: `${f.value * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="section-label mb-1">Details</h4>
              <dl className="divide-y divide-base-300/70">
                <Detail label="Length" value={`${Math.round(seg.length_m)} m`} />
                <Detail label="Elevation" value={seg.elev_min_m != null && `${Math.round(seg.elev_min_m)}–${Math.round(seg.elev_max_m)} m`} />
                <Detail label="Hillside slope" value={seg.cross_slope_deg != null && `${seg.cross_slope_deg}°`} />
                <Detail label="Bends" value={`${Math.round(seg.curvature_deg_per_km)}°/km · ${seg.sharp_turns} sharp`} />
                <Detail label="Landslides within 500 m" value={String(seg.landslides_within_500m)} />
                <Detail label="Nearest river" value={seg.dist_to_river_m != null && `${Math.round(seg.dist_to_river_m)} m`} />
                <Detail label="Stream crossings" value={seg.stream_crossings ? String(seg.stream_crossings) : null} />
                <Detail label="Nearest hospital" value={seg.nearest_hospital_m != null && `${(seg.nearest_hospital_m / 1000).toFixed(1)} km`} />
                <Detail label="Rain effect" value={seg.rain_factor ? `+${Math.round(seg.rain_factor * 100)}% on landslide risk` : null} />
              </dl>
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}
