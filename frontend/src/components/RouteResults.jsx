import {
  AlertTriangle, ChevronRight, CloudRain, Fuel, Hospital, Info, Phone, Shield, ShieldCheck, Stethoscope,
} from 'lucide-react'
import { useState } from 'react'
import { EMERGENCY_NUMBERS, RISK_CLASSES, RISK_COLORS, fmtKm, fmtTime, riskClass } from '../constants'
import { EmptyState, Notice, RiskIndicator, Tabs } from './ui.jsx'

const HELP_ICONS = { hospital: Hospital, clinic: Stethoscope, police: Shield, fuel: Fuel }
const HELP_LABELS = { hospital: 'Hospital', clinic: 'Clinic', police: 'Police', fuel: 'Fuel' }

function Swatch({ dashed }) {
  return dashed
    ? <span className="inline-block w-4 border-t-2 border-dashed border-base-content/45" aria-hidden />
    : <span className="inline-block h-[3px] w-4 rounded-full bg-primary" aria-hidden />
}

// Side-by-side comparison, in a table so the numbers line up
function Comparison({ safe, shortest, same }) {
  const rows = [
    ['Distance', (r) => fmtKm(r.distance_km)],
    ['Travel time', (r) => fmtTime(r.est_time_min)],
    ['Average risk', (r) => <RiskIndicator cls={r.risk_class} value={r.route_risk_avg} />],
    ['High-risk road', (r) => `${r.high_risk_km.toFixed(1)} km`],
  ]
  return (
    <table className="tabular w-full text-[13px]">
      <thead>
        <tr className="text-left text-xs text-base-content/55">
          <th className="w-[34%] pb-2 font-normal" scope="col"><span className="sr-only">Measure</span></th>
          <th className="pb-2 font-medium text-base-content" scope="col">
            <span className="flex items-center gap-2"><Swatch />Recommended</span>
          </th>
          {!same && (
            <th className="pb-2 font-medium" scope="col">
              <span className="flex items-center gap-2"><Swatch dashed />Shortest</span>
            </th>
          )}
        </tr>
      </thead>
      <tbody>
        {rows.map(([label, fn]) => (
          <tr key={label} className="border-t border-base-300/70">
            <th scope="row" className="py-2 text-left font-normal text-base-content/60">{label}</th>
            <td className="py-2 font-medium">{fn(safe)}</td>
            {!same && <td className="py-2 text-base-content/70">{fn(shortest)}</td>}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

// Elevation line with the risk of each stretch as a strip underneath
function Profile({ profile }) {
  const W = 360, H = 120, L = 34, R = 6, T = 6, STRIP = 8, GAP = 6
  const chartBottom = H - STRIP - GAP - 14
  const maxKm = profile[profile.length - 1].km || 1
  const elevs = profile.map((p) => p.elev_m ?? 0)
  const lo = Math.min(...elevs), hi = Math.max(...elevs)
  const x = (km) => L + (km / maxKm) * (W - L - R)
  const y = (e) => T + (1 - (e - lo) / (hi - lo || 1)) * (chartBottom - T)
  const line = profile.map((p, i) => `${i ? 'L' : 'M'}${x(p.km).toFixed(1)},${y(p.elev_m ?? lo).toFixed(1)}`).join('')
  const stripY = chartBottom + GAP
  return (
    <figure>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img"
        aria-label={`Elevation profile from ${Math.round(lo)} to ${Math.round(hi)} metres over ${maxKm.toFixed(0)} km, with risk along the route`}>
        <g className="fill-base-content/45" fontSize="10">
          <text x={L - 6} y={T + 4} textAnchor="end">{Math.round(hi)}</text>
          <text x={L - 6} y={chartBottom} textAnchor="end">{Math.round(lo)}</text>
          <text x={L} y={H - 1}>0 km</text>
          <text x={W - R} y={H - 1} textAnchor="end">{maxKm.toFixed(0)} km</text>
        </g>
        <line x1={L} x2={W - R} y1={chartBottom} y2={chartBottom} className="stroke-base-300" />
        <path d={`${line}L${x(maxKm)},${chartBottom}L${x(0)},${chartBottom}Z`} className="fill-primary/10" />
        <path d={line} fill="none" className="stroke-primary" strokeWidth="1.5" strokeLinejoin="round" />
        {profile.slice(0, -1).map((p, i) => (
          <rect key={i} x={x(p.km)} y={stripY} height={STRIP}
            width={Math.max(x(profile[i + 1].km) - x(p.km), 0.5)} fill={RISK_COLORS[riskClass(p.risk)]} />
        ))}
      </svg>
      <figcaption className="mt-1 text-[11px] text-base-content/50">
        Elevation (m) along the route. The strip below shows risk at each point.
      </figcaption>
    </figure>
  )
}

function Overview({ route }) {
  const total = route.distance_km || 1
  return (
    <div className="space-y-5">
      <Profile profile={route.profile} />
      <div>
        <div className="mb-2 text-xs text-base-content/55">Route by risk level</div>
        <div className="flex h-2 overflow-hidden rounded-full bg-base-200">
          {RISK_CLASSES.map((c) => (
            <div key={c} style={{ width: `${(route.km_by_class[c] / total) * 100}%`, background: RISK_COLORS[c] }} />
          ))}
        </div>
        <dl className="tabular mt-3 grid grid-cols-2 gap-x-6 gap-y-1.5 text-[13px]">
          {RISK_CLASSES.map((c) => (
            <div key={c} className="flex justify-between">
              <dt><RiskIndicator cls={c} /></dt>
              <dd className="text-base-content/70">{route.km_by_class[c].toFixed(1)} km</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  )
}

function Hazards({ stretches, onFocus }) {
  if (!stretches.length) {
    return <EmptyState icon={ShieldCheck} title="No high-risk stretches">This route has no high or very high risk sections.</EmptyState>
  }
  return (
    <ul className="-mx-2">
      {stretches.map((h, i) => (
        <li key={i}>
          <button type="button" onClick={() => onFocus({ center: [h.location[1], h.location[0]], zoom: 15 })}
            className="group flex w-full items-start gap-3 rounded-md px-2 py-2.5 text-left transition-colors hover:bg-base-200">
            <span className="tabular w-[76px] shrink-0 pt-px text-[13px] font-medium">km {h.start_km}–{h.end_km}</span>
            <span className="min-w-0 flex-1">
              <RiskIndicator cls={h.risk_class} className="text-[13px]" />
              <span className="mt-0.5 block text-xs text-base-content/55 first-letter:uppercase">{h.reasons.join(', ')}</span>
            </span>
            <ChevronRight className="mt-0.5 size-4 shrink-0 text-base-content/30 transition-colors group-hover:text-base-content/60" />
          </button>
        </li>
      ))}
    </ul>
  )
}

function Help({ help, onFocus }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {EMERGENCY_NUMBERS.map((e) => (
          <a key={e.number} href={`tel:${e.number}`}
            className="inline-flex h-8 items-center gap-1.5 rounded-md border border-base-300 px-2.5 text-[13px] transition-colors hover:bg-base-200">
            <Phone className="size-3.5 text-base-content/50" />
            <span className="tabular font-medium">{e.number}</span>
            <span className="text-base-content/55">{e.label}</span>
          </a>
        ))}
      </div>
      {help.length === 0 ? (
        <p className="text-[13px] text-base-content/60">No hospitals, police or fuel within 1.5 km of this route.</p>
      ) : (
        <ul className="-mx-2">
          {help.map((h, i) => {
            const Icon = HELP_ICONS[h.category]
            return (
              <li key={i}>
                <button type="button" onClick={() => onFocus({ center: [h.lat, h.lon], zoom: 15 })}
                  className="flex w-full items-center gap-3 rounded-md px-2 py-2 text-left transition-colors hover:bg-base-200">
                  <Icon className="size-4 shrink-0 text-base-content/45" />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[13px]">{h.name}</span>
                    <span className="block text-xs text-base-content/50">
                      {HELP_LABELS[h.category]} · {h.dist_from_route_m} m off route
                    </span>
                  </span>
                  <span className="tabular shrink-0 text-xs text-base-content/55">km {h.at_km}</span>
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}

export default function RouteResults({ result, from, to, onFocus }) {
  const { safe_route: safe, shortest_route: shortest, comparison: cmp } = result
  const [tab, setTab] = useState('overview')

  return (
    <div className="animate-in space-y-5">
      <div>
        <p className="text-xs text-base-content/55">Route</p>
        <h2 className="text-[15px] font-semibold">{from?.name} <span className="text-base-content/40">to</span> {to?.name}</h2>
      </div>

      {(result.gsi_alert !== 'none' || result.weather_alerts.length > 0) && (
        <div className="space-y-2">
          {result.gsi_alert !== 'none' && (
            <Notice tone="error" icon={AlertTriangle}>
              GSI landslide warning for Chamoli is <b className="font-semibold capitalize">{result.gsi_alert}</b>.
            </Notice>
          )}
          {result.weather_alerts.map((a, i) => (
            <Notice key={i} tone="warning" icon={CloudRain}>
              {a.message}{result.simulated_weather && <span className="text-base-content/55"> Demo scenario.</span>}
            </Notice>
          ))}
        </div>
      )}

      <Comparison safe={safe} shortest={shortest} same={cmp.same_route} />

      {cmp.same_route ? (
        <Notice icon={Info}>
          Only one practical road connects these places, so the safest and shortest routes are the
          same. Take extra care on the stretches listed under Hazards.
        </Notice>
      ) : (
        <Notice tone="success" icon={ShieldCheck}>
          {cmp.high_risk_km_reduction_pct > 0 ? (
            <>The recommended route has <b className="font-semibold">{cmp.high_risk_km_reduction_pct}% less high-risk road</b>,
              for {cmp.extra_km.toFixed(1)} km and {fmtTime(Math.max(cmp.extra_min, 0))} extra.</>
          ) : (
            <>The recommended route lowers average risk by {cmp.risk_reduction_pct}% for {cmp.extra_km.toFixed(1)} km extra.</>
          )}
        </Notice>
      )}

      <div>
        <Tabs value={tab} onChange={setTab} tabs={[
          { value: 'overview', label: 'Overview' },
          { value: 'hazards', label: 'Hazards', count: safe.hazard_stretches.length },
          { value: 'help', label: 'Help nearby', count: result.nearest_help.length },
        ]} />
        <div className="pt-4">
          {tab === 'overview' && <Overview route={safe} />}
          {tab === 'hazards' && <Hazards stretches={safe.hazard_stretches} onFocus={onFocus} />}
          {tab === 'help' && <Help help={result.nearest_help} onFocus={onFocus} />}
        </div>
      </div>
      <p className="text-[11px] text-base-content/45">Travel times use typical hill-road speeds (15–35 km/h).</p>
    </div>
  )
}
