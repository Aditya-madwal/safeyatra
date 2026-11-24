// Clerk sign-in, wrapped so the app still works when no Clerk key is set yet.
// Components use useAppAuth() instead of Clerk's hooks directly.

import { ClerkProvider, Show, SignInButton, UserButton, useAuth, useUser } from '@clerk/react'
import { LockKeyhole } from 'lucide-react'
import { createContext, useContext, useEffect, useState } from 'react'
import { api } from './api'
import { EmptyState } from './components/ui.jsx'

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
export const authEnabled = Boolean(PUBLISHABLE_KEY)

const signedOut = {
  enabled: false, isLoaded: true, isSignedIn: false, user: null, me: null,
  getToken: async () => null,
}
const AuthContext = createContext(signedOut)

function ClerkBridge({ children }) {
  const { isLoaded, isSignedIn, getToken } = useAuth()
  const { user } = useUser()
  const [me, setMe] = useState(null) // { user_id, is_admin } from our backend

  useEffect(() => {
    if (!isSignedIn) {
      setMe(null)
      return
    }
    getToken()
      .then((token) => api('/me', { token }))
      .then(setMe)
      .catch((err) => setMe({ error: err.message }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSignedIn])

  const value = { enabled: true, isLoaded, isSignedIn: Boolean(isSignedIn), user, me, getToken }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function AuthProvider({ children }) {
  if (!authEnabled) {
    return <AuthContext.Provider value={signedOut}>{children}</AuthContext.Provider>
  }
  return (
    <ClerkProvider publishableKey={PUBLISHABLE_KEY} afterSignOutUrl="/" appearance={clerkAppearance}>
      <ClerkBridge>{children}</ClerkBridge>
    </ClerkProvider>
  )
}

// match Clerk's sign-in modal and user menu to the app's look
const clerkAppearance = {
  variables: {
    colorPrimary: '#2c4a6b',
    fontFamily: '"Inter Variable", ui-sans-serif, system-ui, sans-serif',
    borderRadius: '0.5rem',
    fontSize: '14px',
  },
  elements: {
    userButtonAvatarBox: { width: '28px', height: '28px' },
  },
}

export const useAppAuth = () => useContext(AuthContext)

export function AuthButtons() {
  if (!authEnabled) {
    return (
      <span className="hidden text-xs text-base-content/50 sm:inline" title="Add VITE_CLERK_PUBLISHABLE_KEY to .env">
        Sign-in not set up
      </span>
    )
  }
  return (
    <>
      <Show when="signed-out">
        <SignInButton mode="modal">
          <button type="button" className="btn btn-sm btn-outline-subtle">Sign in</button>
        </SignInButton>
      </Show>
      <Show when="signed-in">
        <div className="flex size-8 items-center justify-center"><UserButton /></div>
      </Show>
    </>
  )
}

// Shown on pages that need an account
export function SignInPrompt({ title, text }) {
  if (!authEnabled) {
    return (
      <EmptyState icon={LockKeyhole} title="Sign-in is not set up">
        Add the Clerk publishable key as VITE_CLERK_PUBLISHABLE_KEY in the .env file, then restart the frontend.
      </EmptyState>
    )
  }
  return (
    <EmptyState icon={LockKeyhole} title={title} action={
      <SignInButton mode="modal">
        <button type="button" className="btn btn-sm btn-primary">Sign in to continue</button>
      </SignInButton>
    }>
      {text}
    </EmptyState>
  )
}
