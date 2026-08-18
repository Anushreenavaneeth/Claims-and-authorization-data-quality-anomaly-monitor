import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import api from '../services/api';
import { AuthUser } from '../types/auth';

interface AuthContextValue {
  isAuthenticated: boolean;
  user: AuthUser | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function loadPersistedUser(): { user: AuthUser | null; token: string | null } {
  try {
    const token = localStorage.getItem('access_token');
    const raw = localStorage.getItem('auth_user');
    if (token && raw) return { token, user: JSON.parse(raw) as AuthUser };
  } catch {
    // corrupted storage — clear it
    localStorage.removeItem('access_token');
    localStorage.removeItem('auth_user');
  }
  return { user: null, token: null };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const persisted = loadPersistedUser();
  const [user, setUser] = useState<AuthUser | null>(persisted.user);
  const [isAuthenticated, setIsAuthenticated] = useState(!!persisted.token);

  const login = useCallback(async (email: string, password: string) => {
    const resp = await api.post('/auth/login', { email, password });
    const { access_token, user: authUser } = resp.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('auth_user', JSON.stringify(authUser));
    setUser(authUser);
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('auth_user');
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
