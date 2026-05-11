import React, { createContext, useContext, useEffect, useState } from 'react';
import { authAPI, getToken, getUser, removeToken, removeUser, saveToken, saveUser } from '../services/api';

interface AuthContextType {
  user: any;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser]     = useState<any>(null);
  const [token, setToken]   = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Restore session on app start
  useEffect(() => {
    (async () => {
      try {
        const t = await getToken();
        if (t) {
          const me = await authAPI.me();   // validates token with backend
          setToken(t);
          setUser(me);
        }
      } catch {
        await removeToken();
        await removeUser();
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await authAPI.login(email, password);
    await saveToken(res.token);
    const me = await authAPI.me();
    await saveUser(me);
    setToken(res.token);
    setUser(me);
  };

  const logout = async () => {
    await removeToken();
    await removeUser();
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
