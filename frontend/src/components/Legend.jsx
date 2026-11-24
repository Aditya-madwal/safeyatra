import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { RISK_CLASSES, RISK_COLORS, RISK_LABELS } from '../constants'

function Line({ color, dashed }) {
  return dashed
    ? <span className="inline-block w-4 border-t-2 border-dashed border-base-content/80" aria-hidden />
    : <span className="inline-block h-[3px] w-4 rounded-full" style={{ background: color }} aria-hidden />
}

export default function Legend() {
  const [open, setOpen] = useState(true)
  return (
    <div className="absolute bottom-6 left-3 z-[500] hidden w-44 rounded-lg border border-base-300 bg-base-100 text-xs shadow-sm sm:block">
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open}
        className="flex w-full items-center justify-between px-3 py-2 font-medium">
        Legend
        {open ? <ChevronDown className="size-3.5 text-base-content/50" /> : <ChevronUp className="size-3.5 text-base-content/50" />}
      </button>
      {open && (
        <div className="space-y-1.5 border-t border-base-300 px-3 pt-2 pb-2.5 text-base-content/75">
          <div className="text-[11px] text-base-content/50">Road risk</div>
          {RISK_CLASSES.map((c) => (
            <div key={c} className="flex items-center gap-2"><Line color={RISK_COLORS[c]} />{RISK_LABELS[c]}</div>
          ))}
          <div className="flex items-center gap-2"><Line dashed />Closed</div>
          <div className="pt-1 text-[11px] text-base-content/50">Past landslides</div>
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full" style={{ background: '#7a5a9e' }} aria-hidden />NASA catalogue
          </div>
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full" style={{ background: '#a3456f' }} aria-hidden />News reports
          </div>
        </div>
      )}
    </div>
  )
}
