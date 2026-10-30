import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { AuthUser, LoginCredentials } from '../types/api';
import { loginApi, getCurrentUserApi, logoutApi, TOKEN_STORAGE_KEY, USER_STORAGE_KEY } from '../services/api';

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  sessionExpiredMessage: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  clearSessionMessage: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(() => {
    try {
      const stored = localStorage.getItem(USER_STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  });

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [sessionExpiredMessage, setSessionExpiredMessage] = useState<string | null>(null);

  // Validate existing token with backend on initial load
  useEffect(() => {
    let mounted = true;
    const verifyExistingAuth = async () => {
      const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY);
      if (!storedToken) {
        if (mounted) setIsLoading(false);
        return;
      }

      try {
        const currentUser = await getCurrentUserApi();
        if (mounted) {
          setUser(currentUser);
          localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(currentUser));
        }
      } catch (err) {
        // Token invalid or expired
        if (mounted) {
          localStorage.removeItem(TOKEN_STORAGE_KEY);
          localStorage.removeItem(USER_STORAGE_KEY);
          setUser(null);
          setToken(null);
          setSessionExpiredMessage('Your previous session has expired. Please sign in again.');
        }
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    verifyExistingAuth();

    // Listen for custom session expiration events from api interceptor
    const handleAuthExpired = (event: Event) => {
      const customEv = event as CustomEvent<string>;
      setUser(null);
      setToken(null);
      setSessionExpiredMessage(customEv.detail || 'Session expired. Please log in.');
    };

    window.addEventListener('auth:expired', handleAuthExpired);
    return () => {
      mounted = false;
      window.removeEventListener('auth:expired', handleAuthExpired);
    };
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    setSessionExpiredMessage(null);
    const response = await loginApi(credentials);
    localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(response.user));
    setToken(response.access_token);
    setUser(response.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      if (token) {
        await logoutApi();
      }
    } catch {
      // Best-effort logout API call
    } finally {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      localStorage.removeItem(USER_STORAGE_KEY);
      setToken(null);
      setUser(null);
    }
  }, [token]);

  const clearSessionMessage = useCallback(() => {
    setSessionExpiredMessage(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        sessionExpiredMessage,
        login,
        logout,
        clearSessionMessage
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
