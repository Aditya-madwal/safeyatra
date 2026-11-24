import { ArrowRight, ArrowUpDown, ChevronDown, ChevronUp, CloudRain, MousePointerClick, TriangleAlert } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { api, useApi } from '../api'
import Legend from '../components/Legend.jsx'
import PlaceSearch from '../components/PlaceSearch.jsx'
import RiskMap from '../components/RiskMap.jsx'
import RouteResults from '../components/RouteResults.jsx'
import SegmentDetails from '../components/SegmentDetails.jsx'
import { Notice, RiskIndicator, SectionHeader, Segmented, Skeleton } from '../components/ui.jsx'
import { RISK_CLASSES, RISK_COLORS, SAFETY_STEPS } from '../constants'
import { useMapLayers } from '../useMapLayers'

const SUGGESTED = [
  ['Karnaprayag', 'Gopeshwar'], ['Gopeshwar', 'Joshimath'],
  ['Karnaprayag', 'Badrinath'], ['Chamoli', 'Tharali'],
]

const SAFETY_HELP = {
  0: 'Shortest distance. Risk is ignored.',
  2: 'Skips the worst stretches when the detour is small.',
  5: 'Prefers safer roads for a moderate detour.',
  10: 'Avoids risky roads even if the detour is long.',
}

function Marker({ label, color }) {
  return (
    <span className="grid size-[18px] shrink-0 place-items-center rounded-full text-[10px] font-semibold text-white"
      style={{ background: color }} aria-hidden>{label}</span>
  )
}

// Shown before a route is searched: suggestions, district risk, weather
function Overview({ onSuggest }) {
  const stats = useApi('/stats')
  const weather = useApi('/weather')
  const km = stats.data?.km_by_class
  const total = stats.data?.total_km || 1
  const w = weather.data

  return (
    <div className="space-y-7">
      <section>
        <SectionHeader title="Suggested routes" />
        <ul className="-mx-2">
          {SUGGESTED.map(([a, b]) => (
            <li key={a + b}>
              <button type="button" onClick={() => onSuggest(a, b)}
                className="group flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-[13px] transition-colors hover:bg-base-200">
                <span>{a}</span>
                <ArrowRight className="size-3.5 text-base-content/35" />
                <span className="flex-1">{b}</span>
                <span className="text-xs text-base-content/0 transition-colors group-hover:text-base-content/50">Plan</span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <SectionHeader title="Road risk across Chamoli" />
        {!km ? (
          <div className="space-y-2"><Skeleton className="h-2 w-full" /><Skeleton className="h-16 w-full" /></div>
        ) : (
          <>
            <div className="flex h-2 overflow-hidden rounded-full bg-base-200" role="img"
              aria-label={RISK_CLASSES.map((c) => `${c.replace('_', ' ')} ${Math.round(km[c])} km`).join(', ')}>
              {RISK_CLASSES.map((c) => (
                <div key={c} style={{ width: `${(km[c] / total) * 100}%`, background: RISK_COLORS[c] }} />
              ))}
            </div>
            <dl className="tabular mt-3 grid grid-cols-2 gap-x-6 gap-y-1.5 text-[13px]">
              {RISK_CLASSES.map((c) => (
                <div key={c} className="flex justify-between">
                  <dt><RiskIndicator cls={c} /></dt>
                  <dd className="text-base-content/70">{Math.round(km[c]).toLocaleString()} km</dd>
                </div>
              ))}
            </dl>
            <p className="mt-3 text-xs text-base-content/50">
              {Math.round(total).toLocaleString()} km of road · {stats.data.landslides} past landslides
              {stats.data.closed_km > 0 && ` · ${stats.data.closed_km} km closed`}
            </p>
          </>
        )}
      </section>

      <section>
        <SectionHeader title="Weather" action={
          w?.simulated && <span className="text-xs text-warning">Demo scenario</span>
        } />
        {!w ? <Skeleton className="h-40 w-full" /> : (
          <>
            {w.gsi_alert !== 'none' && (
              <Notice tone="error" icon={TriangleAlert} className="mb-3">
                GSI landslide warning for Chamoli is <b className="font-semibold capitalize">{w.gsi_alert}</b>.
              </Notice>
            )}
            {w.alerts.length > 0 && (
              <Notice tone="warning" icon={CloudRain} className="mb-3">
                Heavy rain is raising landslide risk near {w.alerts.map((a) => a.town).join(', ')}.
              </Notice>
            )}
            <table className="tabular w-full text-[13px]">
              <thead>
                <tr className="text-left text-xs text-base-content/50">
                  <th className="pb-1.5 font-normal" scope="col">Town</th>
                  <th className="pb-1.5 text-right font-normal" scope="col">Next 24 h</th>
                  <th className="pb-1.5 text-right font-normal" scope="col">Past 72 h</th>
                </tr>
              </thead>
              <tbody>
                {w.towns.map((t) => (
                  <tr key={t.point_id} className="border-t border-base-300/70">
                    <td className="py-1.5">
                      <span className="flex items-center gap-2">
                        {t.rain_factor > 0 && <CloudRain className="size-3.5 text-warning" aria-label="Rain alert" />}
                        {t.name}
                      </span>
                    </td>
                    <td className="py-1.5 text-right">{t.rain_next_24h_mm} mm</td>
                    <td className="py-1.5 text-right text-base-content/60">{t.rain_past_72h_mm} mm</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-2 text-[11px] text-base-content/45">Open-Meteo · refreshed hourly</p>
          </>
        )}
      </section>

      <p className="flex items-center gap-2 text-xs text-base-content/55">
        <MousePointerClick className="size-4 shrink-0" />
        Click any road on the map to see why it is risky.
      </p>
    </div>
  )
}

export default function MapPage() {
  const { layers, error: layerError, reloadRisk } = useMapLayers()
  const [from, setFrom] = useState(null)
  const [to, setTo] = useState(null)
  const [safety, setSafety] = useState(5)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [pickMode, setPickMode] = useState(null) // 'from' | 'to' | null
  const [focus, setFocus] = useState(null)
  const [selected, setSelected] = useState(null)
  const [sheetOpen, setSheetOpen] = useState(false) // mobile bottom sheet

  // road colours follow weather / reports: refresh every 10 minutes
  useEffect(() => {
    const t = setInterval(reloadRisk, 10 * 60 * 1000)
    return () => clearInterval(t)
  }, [reloadRisk])

  // Esc cancels picking a point on the map
  useEffect(() => {
    if (!pickMode) return
    const onKey = (e) => e.key === 'Escape' && setPickMode(null)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [pickMode])

  const findRoute = async (a = from, b = to, lam = safety) => {
    if (!a || !b) return
    setLoading(true)
    setError(null)
    try {
      const r = await api(`/route?from=${a.lat},${a.lon}&to=${b.lat},${b.lon}&safety=${lam}`)
      setResult(r)
      setSelected(null)
      const c = r.safe_route.geometry.coordinates
      const lats = c.map((p) => p[1]), lons = c.map((p) => p[0])
      setFocus({ bounds: [[Math.min(...lats), Math.min(...lons)], [Math.max(...lats), Math.max(...lons)]] })
    } catch (err) {
      setError(err.message)
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  // changing the preference re-plans the shown route
  const changeSafety = (lam) => {
    setSafety(lam)
    if (result) findRoute(from, to, lam)
  }

  const onMapClick = async (latlng) => {
    if (!pickMode) return
    const point = { name: `${latlng.lat.toFixed(4)}, ${latlng.lng.toFixed(4)}`, kind: 'map', lat: latlng.lat, lon: latlng.lng }
    const which = pickMode
    setPickMode(null)
    try {
      const near = await api(`/places/nearest?lat=${latlng.lat}&lon=${latlng.lng}`)
      if (near.distance_m < 1500) point.name = `Near ${near.name}`
    } catch { /* keep the coordinates as the label */ }
    if (which === 'from') setFrom(point)
    else setTo(point)
  }

  const plan = useCallback(async (a, b, lam) => {
    try {
      const [[pa], [pb]] = await Promise.all([
        api(`/places?q=${encodeURIComponent(a)}&limit=1`), api(`/places?q=${encodeURIComponent(b)}&limit=1`)])
      if (!pa || !pb) throw new Error('Place not found')
      setFrom(pa)
      setTo(pb)
      findRoute(pa, pb, lam)
    } catch (err) {
      setError(err.message)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // shareable links: /?from=Karnaprayag&to=Gopeshwar&safety=10
  useEffect(() => {
    const q = new URLSearchParams(window.location.search)
    if (q.get('from') && q.get('to')) {
      const lam = q.get('safety') !== null ? Number(q.get('safety')) : 5
      setSafety(lam)
      plan(q.get('from'), q.get('to'), lam)
    }
  }, [plan])

  const swap = () => {
    setFrom(to)
    setTo(from)
    if (result) findRoute(to, from, safety)
  }

  const clear = () => {
    setResult(null)
    setFrom(null)
    setTo(null)
    setError(null)
  }

  const route = result && {
    safe: result.safe_route, shortest: result.shortest_route, same: result.comparison.same_route,
  }

  return (
    <div className="relative flex h-full">
      <aside className={`absolute inset-x-0 bottom-0 z-[800] flex flex-col rounded-t-xl border-t border-base-300 bg-base-100 shadow-[0_-6px_24px_rgb(0_0_0/0.08)] transition-[height] duration-200 ${
        sheetOpen ? 'h-[85%]' : 'h-[48%]'} lg:static lg:z-auto lg:h-full lg:w-[380px] lg:shrink-0 lg:rounded-none lg:border-t-0 lg:border-r lg:shadow-none`}>
        <button type="button" onClick={() => setSheetOpen(!sheetOpen)} aria-label={sheetOpen ? 'Collapse panel' : 'Expand panel'}
          className="flex h-6 w-full shrink-0 items-center justify-center text-base-content/35 lg:hidden">
          {sheetOpen ? <ChevronDown className="size-4" /> : <ChevronUp className="size-4" />}
        </button>

        <div className="shrink-0 space-y-4 border-b border-base-300 px-4 pt-1 pb-4 lg:pt-4">
          <div className="flex items-center gap-2">
            <div className="flex-1 space-y-2">
              <PlaceSearch label="Starting point" marker={<Marker label="A" color="#2f7d55" />} value={from} onChange={setFrom}
                picking={pickMode === 'from'} onPick={() => setPickMode(pickMode === 'from' ? null : 'from')} />
              <PlaceSearch label="Destination" marker={<Marker label="B" color="#b4413a" />} value={to} onChange={setTo}
                picking={pickMode === 'to'} onPick={() => setPickMode(pickMode === 'to' ? null : 'to')} />
            </div>
            <button type="button" onClick={swap} disabled={!from && !to} aria-label="Swap start and destination"
              className="grid size-8 place-items-center rounded-md text-base-content/50 transition-colors hover:bg-base-200 hover:text-base-content disabled:opacity-40">
              <ArrowUpDown className="size-4" />
            </button>
          </div>

          <div>
            <div className="mb-2 flex items-baseline justify-between">
              <span className="text-[13px] font-medium">Route preference</span>
            </div>
            <Segmented label="Route preference" options={SAFETY_STEPS} value={safety} onChange={changeSafety} />
            <p className="mt-1.5 text-xs text-base-content/55">{SAFETY_HELP[safety]}</p>
          </div>

          <div className="flex gap-2">
            <button type="button" className="btn btn-primary btn-sm h-9 flex-1" disabled={!from || !to || loading}
              onClick={() => findRoute()}>
              {loading && <span className="loading loading-spinner loading-xs" />}
              {loading ? 'Planning…' : 'Find route'}
            </button>
            {(result || from || to) && (
              <button type="button" className="btn btn-sm btn-outline-subtle h-9" onClick={clear}>Clear</button>
            )}
          </div>
          {error && <Notice tone="error" icon={TriangleAlert}>{error}</Notice>}
          {layerError && <Notice tone="error" icon={TriangleAlert}>{layerError}</Notice>}
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5">
          {result
            ? <RouteResults result={result} from={from} to={to} onFocus={setFocus} />
            : <Overview onSuggest={(a, b) => plan(a, b, safety)} />}
        </div>
      </aside>

      <section className="absolute inset-0 lg:relative lg:flex-1" aria-label="Map">
        <RiskMap layers={layers} route={route} pickMode={pickMode} focus={focus}
          from={from && [from.lat, from.lon]} to={to && [to.lat, to.lon]}
          onMapClick={onMapClick} onSegmentClick={setSelected} />
        <Legend />
        {pickMode && (
          <div className="animate-in absolute top-3 left-1/2 z-[700] -translate-x-1/2 rounded-md border border-base-300 bg-base-100 px-3 py-2 text-[13px] shadow-sm">
            Click on the map to set the {pickMode === 'from' ? 'starting point' : 'destination'}
            <span className="ml-2 text-base-content/45">Esc to cancel</span>
          </div>
        )}
        {!layers.segments && !layerError && (
          <div className="absolute top-3 left-1/2 z-[700] flex -translate-x-1/2 items-center gap-2 rounded-md border border-base-300 bg-base-100 px-3 py-2 text-[13px] shadow-sm">
            <span className="loading loading-spinner loading-xs text-primary" />
            Loading road network
          </div>
        )}
        {selected && <SegmentDetails id={selected} onClose={() => setSelected(null)} />}
      </section>
    </div>
  )
}
