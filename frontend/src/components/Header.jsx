import { CloudRain, Megaphone, Route, ShieldCheck, Sun } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useApi } from '../api'
import { AuthButtons, useAppAuth } from '../auth.jsx'
import { Logo, ThemeToggle } from './ui.jsx'

function NavItem({ to, icon: Icon, children, end }) {
  return (
    <NavLink to={to} end={end}
      className={({ isActive }) =>
        `flex h-8 items-center gap-2 rounded-md px-2.5 text-[13px] font-medium transition-colors ${
          isActive ? 'bg-base-200 text-base-content' : 'text-base-content/60 hover:bg-base-200/60 hover:text-base-content'}`}>
      <Icon className="size-4" />
      <span className="hidden sm:inline">{children}</span>
    </NavLink>
  )
}

// Small live indicator: is rain raising risk anywhere right now?
function WeatherStatus() {
  const { data } = useApi('/weather')
  if (!data) return null
  const alerts = data.alerts.filter((a) => a.message.toLowerCase().includes('rain')).length
  const Icon = alerts ? CloudRain : Sun
  return (
    <div className="hidden items-center gap-1.5 rounded-md border border-base-300 px-2 py-1 text-xs text-base-content/70 md:flex"
      title={data.simulated ? 'Demo rain scenario set by an admin' : 'Live weather from Open-Meteo'}>
      <Icon className={`size-3.5 ${alerts ? 'text-warning' : ''}`} />
      {alerts ? `Rain alert · ${alerts} ${alerts === 1 ? 'town' : 'towns'}` : 'No rain alerts'}
      {data.simulated && <span className="text-warning">· demo</span>}
    </div>
  )
}

export default function Header() {
  const { isSignedIn } = useAppAuth()
  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-base-300 bg-base-100 px-3 sm:px-4">
      <NavLink to="/" className="flex items-center gap-2.5 rounded-md pr-1" aria-label="SafeYatra home">
        <Logo />
        <span className="hidden leading-tight min-[420px]:block">
          <span className="block text-[15px] font-semibold tracking-tight">SafeYatra</span>
          <span className="block text-[11px] text-base-content/50">Chamoli, Uttarakhand</span>
        </span>
      </NavLink>
      <div className="mx-1 hidden h-5 w-px bg-base-300 sm:block" />
      <nav className="flex min-w-0 flex-1 items-center gap-1" aria-label="Main">
        <NavItem to="/" end icon={Route}>Plan route</NavItem>
        <NavItem to="/report" icon={Megaphone}>Report</NavItem>
        {/* any signed-in user sees it; the page itself checks admin rights */}
        {isSignedIn && <NavItem to="/admin" icon={ShieldCheck}>Admin</NavItem>}
      </nav>
      <WeatherStatus />
      <ThemeToggle />
      <AuthButtons />
    </header>
  )
}
