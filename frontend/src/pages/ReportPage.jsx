import { Ban, Construction, ImagePlus, LocateFixed, MapPin, MessageSquare, Mountain, Waves, X } from 'lucide-react'
import { useCallback, useEffect, useId, useState } from 'react'
import { api } from '../api'
import { SignInPrompt, useAppAuth } from '../auth.jsx'
import PageLayout from '../components/PageLayout.jsx'
import RiskMap, { Pin } from '../components/RiskMap.jsx'
import { Notice, SectionHeader, Skeleton, useToast } from '../components/ui.jsx'
import { useMapLayers } from '../useMapLayers'

const TYPES = [
  { value: 'landslide', label: 'Landslide', icon: Mountain },
  { value: 'debris', label: 'Debris or rockfall', icon: Construction },
  { value: 'road_blocked', label: 'Road blocked', icon: Ban },
  { value: 'flooding', label: 'Flooding or washout', icon: Waves },
  { value: 'other', label: 'Something else', icon: MessageSquare },
]
const STATUS = {
  pending: { label: 'In review', color: '#a8742a' },
  verified: { label: 'Verified', color: '#2f7d55' },
  rejected: { label: 'Not confirmed', color: '#a1a1aa' },
}
const MAX_DESC = 500

function Field({ label, htmlFor, hint, children }) {
  return (
    <div>
      <label htmlFor={htmlFor} className="mb-1.5 block text-[13px] font-medium">{label}</label>
      {children}
      {hint && <p className="mt-1.5 text-xs text-base-content/50">{hint}</p>}
    </div>
  )
}

export default function ReportPage() {
  const { isSignedIn, isLoaded, getToken, user } = useAppAuth()
  const { layers, reloadRisk } = useMapLayers()
  const toast = useToast()
  const [point, setPoint] = useState(null)
  const [type, setType] = useState('landslide')
  const [description, setDescription] = useState('')
  const [photo, setPhoto] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [mine, setMine] = useState(null)
  const [focus, setFocus] = useState(null)
  const ids = { desc: useId(), photo: useId() }

  const loadMine = useCallback(async () => {
    if (!isSignedIn) return
    try {
      setMine(await api('/reports/mine', { token: await getToken() }))
    } catch { setMine([]) }
  }, [isSignedIn, getToken])

  useEffect(() => { loadMine() }, [loadMine])

  const locate = () => {
    if (!navigator.geolocation) return setError('Location is not available in this browser.')
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const p = [pos.coords.latitude, pos.coords.longitude]
        setPoint(p)
        setFocus({ center: p, zoom: 15 })
      },
      () => setError('Could not get your location. Click on the map instead.'),
    )
  }

  const submit = async (e) => {
    e.preventDefault()
    if (!point) return
    setBusy(true)
    setError(null)
    const form = new FormData()
    form.append('type', type)
    form.append('lat', point[0])
    form.append('lon', point[1])
    form.append('description', description)
    form.append('user_name', user?.fullName || user?.username || '')
    if (photo) form.append('photo', photo)
    try {
      await api('/reports', { method: 'POST', form, token: await getToken() })
      toast('Report sent. It is now on the map and will be reviewed by an admin.')
      setPoint(null)
      setDescription('')
      setPhoto(null)
      loadMine()
      reloadRisk()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  let panel
  if (!isLoaded) panel = <div className="space-y-3"><Skeleton className="h-9" /><Skeleton className="h-40" /></div>
  else if (!isSignedIn) {
    panel = <SignInPrompt title="Sign in to report" text="Reports help other travellers avoid blocked roads. You need an account so admins can follow up." />
  } else {
    panel = (
      <div className="space-y-8">
        <form onSubmit={submit} className="space-y-5" noValidate>
          <Field label="Location" hint="Click on the road where you saw the problem.">
            <div className="flex gap-2">
              <div className={`flex h-9 flex-1 items-center gap-2 rounded-md border px-2.5 text-[13px] ${
                point ? 'border-base-300' : 'border-dashed border-base-300 text-base-content/45'}`}>
                <MapPin className="size-4 shrink-0 text-base-content/40" />
                <span className="tabular truncate">{point ? `${point[0].toFixed(5)}, ${point[1].toFixed(5)}` : 'Not selected'}</span>
              </div>
              <button type="button" className="btn btn-sm btn-outline-subtle h-9" onClick={locate}>
                <LocateFixed className="size-4" /> My location
              </button>
            </div>
          </Field>

          <fieldset>
            <legend className="mb-1.5 text-[13px] font-medium">What did you see?</legend>
            <div className="divide-y divide-base-300 overflow-hidden rounded-md border border-base-300">
              {TYPES.map((t) => (
                <label key={t.value}
                  className={`flex cursor-pointer items-center gap-3 px-3 py-2.5 text-[13px] transition-colors ${
                    type === t.value ? 'bg-base-200' : 'hover:bg-base-200/60'}`}>
                  <t.icon className="size-4 text-base-content/50" />
                  <span className="flex-1">{t.label}</span>
                  <input type="radio" name="type" value={t.value} checked={type === t.value}
                    onChange={() => setType(t.value)} className="radio radio-xs radio-primary" />
                </label>
              ))}
            </div>
          </fieldset>

          <Field label="Details" htmlFor={ids.desc} hint={`${description.length}/${MAX_DESC}`}>
            <textarea id={ids.desc} rows={3} maxLength={MAX_DESC} value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Which lanes are blocked, is anyone clearing it, how long it might take"
              className="textarea w-full resize-none text-[13px]" />
          </Field>

          <Field label="Photo" htmlFor={ids.photo} hint="Optional · JPG, PNG or WebP up to 5 MB">
            {photo ? (
              <div className="flex h-9 items-center gap-2 rounded-md border border-base-300 px-2.5 text-[13px]">
                <ImagePlus className="size-4 text-base-content/40" />
                <span className="flex-1 truncate">{photo.name}</span>
                <button type="button" onClick={() => setPhoto(null)} aria-label="Remove photo"
                  className="text-base-content/45 hover:text-base-content"><X className="size-4" /></button>
              </div>
            ) : (
              <label htmlFor={ids.photo}
                className="flex h-16 cursor-pointer items-center justify-center gap-2 rounded-md border border-dashed border-base-300 text-[13px] text-base-content/55 transition-colors hover:bg-base-200/60">
                <ImagePlus className="size-4" /> Add a photo
                <input id={ids.photo} type="file" accept="image/jpeg,image/png,image/webp" className="sr-only"
                  onChange={(e) => setPhoto(e.target.files[0] || null)} />
              </label>
            )}
          </Field>

          {error && <Notice tone="error">{error}</Notice>}
          <button type="submit" className="btn btn-primary btn-sm h-9 w-full" disabled={!point || busy}>
            {busy && <span className="loading loading-spinner loading-xs" />}
            {busy ? 'Sending…' : 'Send report'}
          </button>
          {!point && <p className="-mt-2 text-center text-xs text-base-content/45">Select a location to send the report.</p>}
        </form>

        <section>
          <SectionHeader title="Your reports" />
          {mine === null && <Skeleton className="h-12" />}
          {mine?.length === 0 && <p className="text-[13px] text-base-content/55">You have not sent any reports yet.</p>}
          {mine?.length > 0 && (
            <ul className="-mx-2">
              {mine.map((r) => (
                <li key={r.id}>
                  <button type="button" onClick={() => setFocus({ center: [r.lat, r.lon], zoom: 15 })}
                    className="flex w-full items-center gap-3 rounded-md px-2 py-2 text-left transition-colors hover:bg-base-200">
                    <span className="min-w-0 flex-1">
                      <span className="block text-[13px] capitalize">{r.type.replace('_', ' ')}</span>
                      <span className="block text-xs text-base-content/50">{new Date(r.created_at).toLocaleString()}</span>
                    </span>
                    <span className="flex items-center gap-1.5 text-xs">
                      <span className="size-1.5 rounded-full" style={{ background: STATUS[r.status].color }} aria-hidden />
                      {STATUS[r.status].label}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    )
  }

  return (
    <PageLayout
      title="Report a blockage"
      subtitle="Tell other travellers about landslides and blocked roads."
      panel={panel}
      map={
        <RiskMap layers={layers} focus={focus} pickMode={isSignedIn ? 'report' : null}
          onMapClick={(ll) => isSignedIn && setPoint([ll.lat, ll.lng])}>
          <Pin position={point} label="!" color="#e07b28" />
        </RiskMap>
      }
    />
  )
}
