import { Check, Inbox, MapPin, Route, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import { SignInPrompt, useAppAuth } from '../auth.jsx'
import PageLayout from '../components/PageLayout.jsx'
import RiskMap, { Pin } from '../components/RiskMap.jsx'
import { ConfirmDialog, EmptyState, Notice, Segmented, Skeleton, Tabs, useToast } from '../components/ui.jsx'
import { useMapLayers } from '../useMapLayers'

const STATUS = {
  pending: { label: 'In review', color: '#a8742a' },
  verified: { label: 'Verified', color: '#2f7d55' },
  rejected: { label: 'Rejected', color: '#a1a1aa' },
}
const GSI_OPTIONS = [
  { value: 'none', label: 'None' }, { value: 'low', label: 'Low' },
  { value: 'moderate', label: 'Moderate' }, { value: 'high', label: 'High' },
]
const RAIN_OPTIONS = [
  { value: 'live', label: 'Live' }, { value: 'moderate', label: 'Moderate' }, { value: 'heavy', label: 'Heavy' },
]

function useAdminApi() {
  const { getToken } = useAppAuth()
  return useCallback(async (path, opts = {}) => api(path, { ...opts, token: await getToken() }), [getToken])
}

function StatusLabel({ status }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs">
      <span className="size-1.5 rounded-full" style={{ background: STATUS[status].color }} aria-hidden />
      {STATUS[status].label}
    </span>
  )
}

function ReportsTab({ onChange, onFocus }) {
  const call = useAdminApi()
  const toast = useToast()
  const [status, setStatus] = useState('pending')
  const [reports, setReports] = useState(null)
  const [error, setError] = useState(null)
  const [confirm, setConfirm] = useState(null) // report to verify

  const load = useCallback(() => {
    setReports(null)
    call(`/admin/reports${status === 'all' ? '' : `?status=${status}`}`).then(setReports).catch((e) => setError(e.message))
  }, [call, status])
  useEffect(load, [load])

  const review = async (r, newStatus) => {
    try {
      await call(`/admin/reports/${r.id}`, { method: 'PATCH', body: { status: newStatus } })
      toast(newStatus === 'verified' ? `Report #${r.id} verified. The road is now closed for routing.`
        : newStatus === 'rejected' ? `Report #${r.id} rejected.` : `Report #${r.id} moved back to review.`)
      load()
      onChange()
    } catch (e) {
      toast(e.message, 'error')
    }
  }

  return (
    <div className="space-y-4">
      <Segmented label="Filter reports" value={status} onChange={setStatus} options={[
        { value: 'pending', label: 'In review' }, { value: 'verified', label: 'Verified' },
        { value: 'rejected', label: 'Rejected' }, { value: 'all', label: 'All' },
      ]} />
      {error && <Notice tone="error">{error}</Notice>}
      {!reports && !error && <div className="space-y-2"><Skeleton className="h-20" /><Skeleton className="h-20" /></div>}
      {reports?.length === 0 && (
        <EmptyState icon={Inbox} title={status === 'pending' ? 'Nothing to review' : 'No reports here'}>
          {status === 'pending' ? 'New blockage reports from travellers will appear here.' : 'Try another filter.'}
        </EmptyState>
      )}
      <ul className="divide-y divide-base-300">
        {reports?.map((r) => (
          <li key={r.id} className="py-4 first:pt-0">
            <div className="flex items-start gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-[13px] font-medium capitalize">{r.type.replace('_', ' ')}</span>
                  <span className="tabular text-xs text-base-content/40">#{r.id}</span>
                </div>
                <p className="mt-0.5 text-xs text-base-content/50">
                  {r.user_name || 'Traveller'} · {new Date(r.created_at).toLocaleString()}
                </p>
              </div>
              <StatusLabel status={r.status} />
            </div>
            {r.description && <p className="mt-2 text-[13px] leading-5">{r.description}</p>}
            {r.photo && (
              <a href={`/api/uploads/${r.photo}`} target="_blank" rel="noreferrer" className="mt-2 block w-fit">
                <img src={`/api/uploads/${r.photo}`} alt={`Photo for report ${r.id}`}
                  className="max-h-32 rounded-md border border-base-300" />
              </a>
            )}
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {r.status !== 'verified' && (
                <button type="button" className="btn btn-primary btn-xs h-7 px-2.5" onClick={() => setConfirm(r)}>
                  <Check className="size-3.5" /> Verify
                </button>
              )}
              {r.status !== 'rejected' && (
                <button type="button" className="btn btn-outline-subtle btn-xs h-7 px-2.5" onClick={() => review(r, 'rejected')}>
                  {r.status === 'verified' ? 'Reject and reopen road' : 'Reject'}
                </button>
              )}
              <button type="button" className="btn btn-ghost btn-xs h-7 px-2 text-base-content/60"
                onClick={() => onFocus({ center: [r.lat, r.lon], zoom: 15 })}>
                <MapPin className="size-3.5" /> Show on map
              </button>
            </div>
          </li>
        ))}
      </ul>
      <ConfirmDialog open={Boolean(confirm)} title="Verify this report?" confirmLabel="Verify and close road"
        onCancel={() => setConfirm(null)}
        onConfirm={() => { review(confirm, 'verified'); setConfirm(null) }}>
        The road at this location will be closed and routes will avoid it until the report is rejected.
      </ConfirmDialog>
    </div>
  )
}

function ClosuresTab({ points, setPoints, onChange }) {
  const call = useAdminApi()
  const toast = useToast()
  const [closures, setClosures] = useState(null)
  const [form, setForm] = useState({ name: '', reason: '', start_date: '', end_date: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [toRemove, setToRemove] = useState(null)

  const load = useCallback(() => {
    call('/admin/closures').then(setClosures).catch((e) => setError(e.message))
  }, [call])
  useEffect(load, [load])

  const add = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const c = await call('/admin/closures', {
        method: 'POST',
        body: {
          ...form, start_date: form.start_date || null, end_date: form.end_date || null,
          start: { lat: points.start[0], lon: points.start[1] }, end: { lat: points.end[0], lon: points.end[1] },
        },
      })
      toast(`"${c.name}" added · ${c.segment_ids.length} road pieces closed.`)
      setForm({ name: '', reason: '', start_date: '', end_date: '' })
      setPoints({ start: null, end: null })
      load()
      onChange()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const remove = async (c) => {
    try {
      await call(`/admin/closures/${c.id}`, { method: 'DELETE' })
      toast(`"${c.name}" removed. The road is open again.`)
      load()
      onChange()
    } catch (e) {
      toast(e.message, 'error')
    }
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  const step = !points.start ? 1 : !points.end ? 2 : 3

  return (
    <div className="space-y-8">
      <form onSubmit={add} className="space-y-4">
        <div>
          <h3 className="text-[13px] font-medium">New closure</h3>
          <ol className="mt-2 space-y-1 text-[13px]">
            {['Click where the closed road starts', 'Click where it ends', 'Name it and choose dates'].map((s, i) => (
              <li key={s} className={`flex items-center gap-2 ${step === i + 1 ? 'text-base-content' : 'text-base-content/45'}`}>
                <span className={`grid size-5 place-items-center rounded-full text-[11px] font-medium ${
                  step > i + 1 ? 'bg-success/15 text-success' : step === i + 1 ? 'bg-primary text-primary-content' : 'bg-base-200'}`}>
                  {step > i + 1 ? <Check className="size-3" /> : i + 1}
                </span>
                {s}
              </li>
            ))}
          </ol>
        </div>
        <label className="block">
          <span className="mb-1.5 block text-[13px] font-medium">Name</span>
          <input className="input input-sm h-9 w-full text-[13px]" placeholder="Joshimath to Malari, winter snow"
            value={form.name} onChange={set('name')} required minLength={2} />
        </label>
        <label className="block">
          <span className="mb-1.5 block text-[13px] font-medium">Reason <span className="font-normal text-base-content/45">(optional)</span></span>
          <input className="input input-sm h-9 w-full text-[13px]" placeholder="Snow, repair work, bridge damage"
            value={form.reason} onChange={set('reason')} />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            <span className="mb-1.5 block text-[13px] font-medium">From</span>
            <input type="date" className="input input-sm h-9 w-full text-[13px]" value={form.start_date} onChange={set('start_date')} />
          </label>
          <label className="block">
            <span className="mb-1.5 block text-[13px] font-medium">Until</span>
            <input type="date" className="input input-sm h-9 w-full text-[13px]" value={form.end_date} onChange={set('end_date')} />
          </label>
        </div>
        <p className="text-xs text-base-content/50">Leave the dates empty to close the road now, until you remove the closure.</p>
        {error && <Notice tone="error">{error}</Notice>}
        <div className="flex gap-2">
          <button type="submit" className="btn btn-primary btn-sm h-9 flex-1" disabled={step < 3 || !form.name.trim() || busy}>
            {busy && <span className="loading loading-spinner loading-xs" />} Close road
          </button>
          {(points.start || points.end) && (
            <button type="button" className="btn btn-outline-subtle btn-sm h-9" onClick={() => setPoints({ start: null, end: null })}>
              Reset points
            </button>
          )}
        </div>
      </form>

      <section>
        <h3 className="section-label mb-2">All closures</h3>
        {!closures && <Skeleton className="h-14" />}
        {closures?.length === 0 && <p className="text-[13px] text-base-content/55">No closures yet.</p>}
        <ul className="divide-y divide-base-300">
          {closures?.map((c) => (
            <li key={c.id} className="flex items-start gap-3 py-3">
              <Route className="mt-0.5 size-4 shrink-0 text-base-content/40" />
              <div className="min-w-0 flex-1">
                <p className="text-[13px] font-medium">{c.name}</p>
                <p className="mt-0.5 text-xs text-base-content/50">
                  {[c.reason, `${c.segment_ids.length} road pieces`,
                    (c.start_date || c.end_date) && `${c.start_date || 'now'} to ${c.end_date || 'until removed'}`]
                    .filter(Boolean).join(' · ')}
                </p>
              </div>
              <span className={`text-xs ${c.active ? 'font-medium' : 'text-base-content/45'}`}>{c.active ? 'Active' : 'Scheduled'}</span>
              <button type="button" onClick={() => setToRemove(c)} aria-label={`Remove ${c.name}`}
                className="grid size-7 place-items-center rounded text-base-content/40 transition-colors hover:bg-error/10 hover:text-error">
                <Trash2 className="size-4" />
              </button>
            </li>
          ))}
        </ul>
      </section>
      <ConfirmDialog open={Boolean(toRemove)} title="Remove this closure?" confirmLabel="Remove closure" destructive
        onCancel={() => setToRemove(null)}
        onConfirm={() => { remove(toRemove); setToRemove(null) }}>
        {toRemove?.name} will open again and routes may use it immediately.
      </ConfirmDialog>
    </div>
  )
}

function SettingRow({ title, description, children }) {
  return (
    <div className="space-y-3 py-5 first:pt-0">
      <div>
        <h3 className="text-[13px] font-medium">{title}</h3>
        <p className="mt-0.5 text-xs leading-5 text-base-content/55">{description}</p>
      </div>
      {children}
    </div>
  )
}

function SettingsTab({ onChange }) {
  const call = useAdminApi()
  const toast = useToast()
  const [settings, setSettings] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => { call('/admin/settings').then(setSettings).catch((e) => setError(e.message)) }, [call])

  const save = async (patch, message) => {
    try {
      setSettings(await call('/admin/settings', { method: 'PUT', body: patch }))
      toast(message)
      onChange()
    } catch (e) {
      toast(e.message, 'error')
    }
  }

  if (error) return <Notice tone="error">{error}</Notice>
  if (!settings) return <div className="space-y-3"><Skeleton className="h-16" /><Skeleton className="h-16" /></div>
  return (
    <div className="divide-y divide-base-300">
      <SettingRow title="GSI landslide forecast"
        description="Copy today's level for Chamoli from the GSI bulletin (bhusanket.gsi.gov.in, issued during the monsoon). Higher levels raise landslide risk on every road.">
        <Segmented label="GSI alert level" options={GSI_OPTIONS} value={settings.gsi_alert}
          onChange={(v) => save({ gsi_alert: v }, `GSI alert set to ${v}.`)} />
      </SettingRow>
      <SettingRow title="Rain"
        description="Live uses Open-Meteo forecasts. Moderate and Heavy simulate a monsoon day so you can show how rain changes risk and routes in the dry season.">
        <Segmented label="Rain scenario" options={RAIN_OPTIONS} value={settings.rain_scenario}
          onChange={(v) => save({ rain_scenario: v }, v === 'live' ? 'Using live weather.' : `Demo scenario: ${v} rain.`)} />
      </SettingRow>
    </div>
  )
}

export default function AdminPage() {
  const { isLoaded, isSignedIn, me } = useAppAuth()
  const { layers, reloadRisk } = useMapLayers()
  const [tab, setTab] = useState('reports')
  const [points, setPoints] = useState({ start: null, end: null })
  const [focus, setFocus] = useState(null)

  const onMapClick = (ll) => {
    if (tab !== 'closures') return
    const p = [ll.lat, ll.lng]
    setPoints((cur) => (!cur.start || cur.end ? { start: p, end: null } : { ...cur, end: p }))
  }

  let panel
  if (!isLoaded || (isSignedIn && !me)) panel = <div className="space-y-3"><Skeleton className="h-8" /><Skeleton className="h-32" /></div>
  else if (!isSignedIn) panel = <SignInPrompt title="Admins only" text="Sign in with an admin account to review reports and manage closures." />
  else if (me.error) panel = <Notice tone="error">{me.error}</Notice>
  else if (!me.is_admin) {
    panel = (
      <div className="space-y-3 text-[13px]">
        <p>This account does not have admin access.</p>
        <p className="text-base-content/60">
          To give it access, add this user id to <code className="font-mono text-xs">ADMIN_USER_IDS</code> in
          the <code className="font-mono text-xs">.env</code> file and restart the backend.
        </p>
        <code className="block rounded-md border border-base-300 bg-base-200 px-3 py-2 font-mono text-xs select-all">{me.user_id}</code>
      </div>
    )
  } else {
    panel = (
      <div className="space-y-5">
        <Tabs value={tab} onChange={setTab} tabs={[
          { value: 'reports', label: 'Reports' }, { value: 'closures', label: 'Closures' }, { value: 'settings', label: 'Live settings' },
        ]} />
        {tab === 'reports' && <ReportsTab onChange={reloadRisk} onFocus={setFocus} />}
        {tab === 'closures' && <ClosuresTab points={points} setPoints={setPoints} onChange={reloadRisk} />}
        {tab === 'settings' && <SettingsTab onChange={reloadRisk} />}
      </div>
    )
  }

  return (
    <PageLayout title="Admin" subtitle="Review reports, close roads and set live conditions." width="lg:w-[420px]"
      panel={panel}
      map={
        <RiskMap layers={layers} focus={focus} onMapClick={onMapClick} pickMode={tab === 'closures' ? 'closure' : null}>
          <Pin position={points.start} label="1" color="#27272a" />
          <Pin position={points.end} label="2" color="#27272a" />
        </RiskMap>
      }
    />
  )
}
