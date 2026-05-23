import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { api, type User } from "@/lib/api"

interface AuthState {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Check the existing session on first load.
  useEffect(() => {
    let cancelled = false
    api.me()
      .then((u) => { if (!cancelled) setUser(u) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  async function login(username: string, password: string) {
    const u = await api.login(username, password)
    setUser(u)
  }

  async function logout() {
    try { await api.logout() } finally { setUser(null) }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider")
  return ctx
}
