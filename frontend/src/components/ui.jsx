// Small reusable pieces of the design system

import { CircleCheck, CircleX, Moon, Sun, X } from 'lucide-react'
import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { RISK_COLORS, RISK_LABELS } from '../constants'

export function Logo({ className = 'size-7' }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden>
      <rect width="32" height="32" rx="7" className="fill-primary" />
      <path d="M5 23l7-10 4 5 3-4 8 9z" fill="#fff" opacity=".92" />
      <path d="M8 26c5-3 11-3 16 0" stroke="#d3a35a" strokeWidth="2" fill="none" strokeLinecap="round" />
    </svg>
  )
}

// Colour is never the only signal: a dot plus the class name
export function RiskIndicator({ cls, value, className = '' }) {
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap ${className}`}>
      <span className="size-2 shrink-0 rounded-full" style={{ background: RISK_COLORS[cls] }} aria-hidden />
      <span>{RISK_LABELS[cls]}</span>
      {value !== undefined && <span className="tabular text-base-content/50">{value.toFixed(2)}</span>}
    </span>
  )
}

export function SectionHeader({ title, action, className = '' }) {
  return (
    <div className={`mb-2 flex items-center justify-between ${className}`}>
      <h3 className="section-label">{title}</h3>
      {action}
    </div>
  )
}

export function Segmented({ options, value, onChange, label }) {
  return (
    <div role="radiogroup" aria-label={label}
      className="grid rounded-md border border-base-300 bg-base-200 p-0.5"
      style={{ gridTemplateColumns: `repeat(${options.length}, minmax(0, 1fr))` }}>
      {options.map((o) => {
        const active = o.value === value
        return (
          <button key={o.value} type="button" role="radio" aria-checked={active}
            onClick={() => onChange(o.value)}
            className={`h-8 rounded-[5px] text-[13px] font-medium transition-colors ${
              active ? 'bg-base-100 text-base-content shadow-[0_1px_2px_rgb(0_0_0/0.08)]'
                : 'text-base-content/60 hover:text-base-content'}`}>
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

export function Tabs({ tabs, value, onChange }) {
  return (
    <div role="tablist" className="flex gap-4 border-b border-base-300">
      {tabs.map((t) => {
        const active = t.value === value
        return (
          <button key={t.value} role="tab" type="button" aria-selected={active} onClick={() => onChange(t.value)}
            className={`-mb-px flex h-9 items-center gap-1.5 border-b-2 text-[13px] font-medium transition-colors ${
              active ? 'border-primary text-base-content' : 'border-transparent text-base-content/55 hover:text-base-content'}`}>
            {t.label}
            {t.count !== undefined && (
              <span className={`tabular rounded px-1 text-[11px] ${active ? 'bg-base-300' : 'bg-base-200'}`}>{t.count}</span>
            )}
          </button>
        )
      })}
    </div>
  )
}

export function EmptyState({ icon: Icon, title, children, action }) {
  return (
    <div className="flex flex-col items-center px-6 py-10 text-center">
      {Icon && (
        <div className="mb-3 grid size-10 place-items-center rounded-lg border border-base-300 bg-base-200">
          <Icon className="size-5 text-base-content/60" />
        </div>
      )}
      <p className="font-medium">{title}</p>
      {children && <p className="mt-1 max-w-xs text-[13px] text-base-content/60">{children}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function Skeleton({ className = 'h-4 w-full' }) {
  return <div className={`skeleton ${className}`} />
}

export function Notice({ tone = 'info', icon: Icon, children, className = '' }) {
  const tones = {
    info: 'border-base-300 bg-base-200 text-base-content',
    warning: 'border-warning/25 bg-warning/8 text-base-content',
    error: 'border-error/25 bg-error/8 text-base-content',
    success: 'border-success/25 bg-success/8 text-base-content',
  }
  const iconTone = { info: 'text-base-content/55', warning: 'text-warning', error: 'text-error', success: 'text-success' }
  return (
    <div role={tone === 'error' ? 'alert' : 'status'}
      className={`flex gap-2.5 rounded-md border px-3 py-2.5 text-[13px] leading-5 ${tones[tone]} ${className}`}>
      {Icon && <Icon className={`mt-0.5 size-4 shrink-0 ${iconTone[tone]}`} />}
      <div className="min-w-0">{children}</div>
    </div>
  )
}

// ---- confirmation dialog (native <dialog>, so focus and Esc work) ----
export function ConfirmDialog({ open, title, children, confirmLabel = 'Confirm', destructive, onConfirm, onCancel }) {
  const ref = useRef(null)
  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (open && !d.open) d.showModal()
    if (!open && d.open) d.close()
  }, [open])
  return (
    <dialog ref={ref} className="modal" onClose={onCancel}>
      <div className="modal-box max-w-sm rounded-lg border border-base-300 p-5 shadow-xl">
        <h3 className="text-[15px] font-semibold">{title}</h3>
        <div className="mt-2 text-[13px] text-base-content/70">{children}</div>
        <div className="mt-5 flex justify-end gap-2">
          <button type="button" className="btn btn-sm btn-outline-subtle" onClick={onCancel}>Cancel</button>
          <button type="button" className={`btn btn-sm ${destructive ? 'btn-error' : 'btn-primary'}`} onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
      <form method="dialog" className="modal-backdrop bg-black/30"><button aria-label="Close">close</button></form>
    </dialog>
  )
}

// ---- toasts: short confirmation that an action worked (or did not) ----
const ToastContext = createContext(() => {})
export const useToast = () => useContext(ToastContext)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const remove = useCallback((id) => setToasts((t) => t.filter((x) => x.id !== id)), [])
  const show = useCallback((message, tone = 'success') => {
    const id = Math.random().toString(36).slice(2)
    setToasts((t) => [...t, { id, message, tone }])
    setTimeout(() => remove(id), 4000)
  }, [remove])
  return (
    <ToastContext.Provider value={show}>
      {children}
      <div className="pointer-events-none fixed right-4 bottom-4 z-[2000] flex w-[min(360px,calc(100vw-2rem))] flex-col gap-2"
        aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id}
            className="animate-in pointer-events-auto flex items-start gap-2.5 rounded-lg border border-base-300 bg-base-100 px-3.5 py-3 text-[13px] shadow-lg">
            {t.tone === 'error'
              ? <CircleX className="mt-0.5 size-4 shrink-0 text-error" />
              : <CircleCheck className="mt-0.5 size-4 shrink-0 text-success" />}
            <span className="flex-1">{t.message}</span>
            <button type="button" onClick={() => remove(t.id)} aria-label="Dismiss"
              className="text-base-content/40 hover:text-base-content">
              <X className="size-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

// ---- light / dark theme (follows the system until the user chooses) ----
function systemDark() {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches
}

export function useTheme() {
  const [theme, setTheme] = useState(() => {
    const t = document.documentElement.getAttribute('data-theme')
    return t || (systemDark() ? 'safeyatra-dark' : 'safeyatra')
  })
  const toggle = () => {
    const next = theme === 'safeyatra-dark' ? 'safeyatra' : 'safeyatra-dark'
    document.documentElement.setAttribute('data-theme', next)
    try { localStorage.setItem('safeyatra-theme', next) } catch { /* private mode */ }
    setTheme(next)
    window.dispatchEvent(new CustomEvent('safeyatra-theme', { detail: next }))
  }
  return { dark: theme === 'safeyatra-dark', toggle }
}

export function useIsDark() {
  const [dark, setDark] = useState(() => {
    const t = document.documentElement.getAttribute('data-theme')
    return t ? t === 'safeyatra-dark' : systemDark()
  })
  useEffect(() => {
    const onChange = (e) => setDark(e.detail === 'safeyatra-dark')
    window.addEventListener('safeyatra-theme', onChange)
    return () => window.removeEventListener('safeyatra-theme', onChange)
  }, [])
  return dark
}

export function ThemeToggle() {
  const { dark, toggle } = useTheme()
  return (
    <button type="button" onClick={toggle} className="btn btn-ghost btn-sm btn-square text-base-content/70"
      aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'} title={dark ? 'Light theme' : 'Dark theme'}>
      {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
    </button>
  )
}
