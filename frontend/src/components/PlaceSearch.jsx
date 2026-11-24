// Place input with suggestions from /api/places (arrow keys + Enter work),
// plus a button to pick the point on the map instead.

import { Crosshair, MapPin } from 'lucide-react'
import { useEffect, useId, useState } from 'react'
import { api } from '../api'

const KIND_LABEL = { town: 'Town', village: 'Village', hamlet: 'Hamlet', locality: 'Locality', map: 'Map point' }

export default function PlaceSearch({ label, marker, value, onChange, picking, onPick }) {
  const [text, setText] = useState(value?.name || '')
  const [results, setResults] = useState([])
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const listId = useId()

  useEffect(() => setText(value?.name || ''), [value])

  useEffect(() => {
    if (!open) return
    const timer = setTimeout(() => {
      api(`/places?q=${encodeURIComponent(text)}&limit=8`)
        .then((r) => { setResults(r); setActive(0) })
        .catch(() => setResults([]))
    }, 150)
    return () => clearTimeout(timer)
  }, [text, open])

  const choose = (place) => {
    onChange(place)
    setText(place.name)
    setOpen(false)
  }

  const onKeyDown = (e) => {
    if (!open || !results.length) return
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive((a) => (a + 1) % results.length) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((a) => (a - 1 + results.length) % results.length) }
    else if (e.key === 'Enter') { e.preventDefault(); choose(results[active]) }
    else if (e.key === 'Escape') setOpen(false)
  }

  return (
    <div className="relative">
      <div className={`flex h-9 items-center gap-2 rounded-md border bg-base-100 pr-1 pl-2.5 transition-shadow ${
        picking ? 'border-primary/60 ring-3 ring-primary/15' : 'border-base-300 focus-within:border-primary/50 focus-within:ring-3 focus-within:ring-primary/15'}`}>
        {marker}
        <input
          type="text" value={text} aria-label={label} placeholder={picking ? 'Click on the map…' : label}
          role="combobox" aria-expanded={open && results.length > 0} aria-controls={listId} aria-autocomplete="list"
          onChange={(e) => { setText(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)} onKeyDown={onKeyDown}
          onBlur={() => setTimeout(() => setOpen(false), 120)}
          className="min-w-0 flex-1 bg-transparent text-[13px] outline-none placeholder:text-base-content/40"
        />
        <button type="button" onClick={onPick} aria-pressed={picking}
          className={`grid size-7 place-items-center rounded transition-colors ${
            picking ? 'bg-primary/10 text-primary' : 'text-base-content/45 hover:bg-base-200 hover:text-base-content'}`}
          title="Pick on the map" aria-label={`Pick ${label.toLowerCase()} on the map`}>
          <Crosshair className="size-4" />
        </button>
      </div>
      {open && results.length > 0 && (
        <ul id={listId} role="listbox"
          className="animate-in absolute top-full right-0 left-0 z-[1000] mt-1 max-h-72 overflow-y-auto rounded-md border border-base-300 bg-base-100 p-1 shadow-lg">
          {results.map((p, i) => (
            <li key={`${p.name}-${p.lat}`} role="option" aria-selected={i === active}>
              <button type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => choose(p)}
                onMouseEnter={() => setActive(i)}
                className={`flex w-full items-center gap-2.5 rounded px-2 py-1.5 text-left text-[13px] ${i === active ? 'bg-base-200' : ''}`}>
                <MapPin className="size-3.5 shrink-0 text-base-content/40" />
                <span className="flex-1 truncate">{p.name}</span>
                <span className="text-[11px] text-base-content/45">{KIND_LABEL[p.kind] || p.kind}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
