// Panel + map layout: side panel on desktop, bottom sheet on phones

import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

export default function PageLayout({ title, subtitle, panel, map, width = 'lg:w-[380px]' }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="relative flex h-full">
      <aside className={`absolute inset-x-0 bottom-0 z-[800] flex flex-col rounded-t-xl border-t border-base-300 bg-base-100 shadow-[0_-6px_24px_rgb(0_0_0/0.08)] transition-[height] duration-200 ${
        open ? 'h-[85%]' : 'h-[55%]'} lg:static lg:z-auto lg:h-full ${width} lg:shrink-0 lg:rounded-none lg:border-t-0 lg:border-r lg:shadow-none`}>
        <button type="button" onClick={() => setOpen(!open)} aria-label={open ? 'Collapse panel' : 'Expand panel'}
          className="flex h-6 w-full shrink-0 items-center justify-center text-base-content/35 lg:hidden">
          {open ? <ChevronDown className="size-4" /> : <ChevronUp className="size-4" />}
        </button>
        <div className="shrink-0 border-b border-base-300 px-4 pt-1 pb-3.5 lg:pt-4">
          <h1 className="text-[15px] font-semibold">{title}</h1>
          {subtitle && <p className="mt-0.5 text-[13px] text-base-content/55">{subtitle}</p>}
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5">{panel}</div>
      </aside>
      <section className="absolute inset-0 lg:relative lg:flex-1" aria-label="Map">{map}</section>
    </div>
  )
}
