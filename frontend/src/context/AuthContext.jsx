import { createContext, useCallback, useContext, useMemo, useState } from 'react';

const AuthContext = createContext(null);
const STORAGE_KEY = 'cmh_auth';
const USERS_KEY = 'cmh_users';

function loadUsers() {
  try {
    const raw = localStorage.getItem(USERS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveUsers(users) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

function createToken(user) {
  const payload = {
    sub: user.email,
    name: user.name,
    exp: Date.now() + 7 * 24 * 60 * 60 * 1000,
  };
  return btoa(JSON.stringify(payload));
}

function parseToken(token) {
  try {
    const payload = JSON.parse(atob(token));
    if (!payload.exp || payload.exp < Date.now()) return null;
    return payload;
  } catch {
    return null;
  }
}

function loadSession() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const { token } = JSON.parse(raw);
    const payload = parseToken(token);
    if (!payload) return null;
    return { token, email: payload.sub, name: payload.name };
  } catch {
    return null;
  }
}

function ensureDemoUser() {
  const users = loadUsers();
  if (!users.length) {
    saveUsers([{ name: 'Ops Admin', email: 'admin@checkmyhits.io', password: 'admin123' }]);
  }
}

export function AuthProvider({ children }) {
  ensureDemoUser();
  const [user, setUser] = useState(() => loadSession());

  const login = useCallback(async (email, password) => {
    const users = loadUsers();
    const found = users.find((u) => u.email === email && u.password === password);
    if (!found) {
      throw new Error('Invalid email or password');
    }
    const token = createToken(found);
    const session = { token, email: found.email, name: found.name };
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ token }));
    setUser(session);
    return session;
  }, []);

  const register = useCallback(async (name, email, password) => {
    const users = loadUsers();
    if (users.some((u) => u.email === email)) {
      throw new Error('An account with this email already exists');
    }
    const entry = { name, email, password };
    saveUsers([...users, entry]);
    const token = createToken(entry);
    const session = { token, email: entry.email, name: entry.name };
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ token }));
    setUser(session);
    return session;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
    }),
    [user, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
