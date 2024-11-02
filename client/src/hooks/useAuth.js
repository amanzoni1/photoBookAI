// client/src/hooks/useAuth.js
import { useState, useEffect, createContext, useContext, useCallback } from 'react';
import axios from '../utils/axiosConfig';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
  
    // Define logout first
    const logout = useCallback(async () => {
      try {
        const response = await axios.post('/api/auth/logout');
        if (response.status === 200) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error('Logout error:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setIsAuthenticated(false);
        throw error;
      }
    }, []);
  
    const isTokenExpired = useCallback((token) => {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.exp * 1000 < Date.now();
      } catch {
        return true;
      }
    }, []);
  
    const refreshAuth = useCallback(async () => {
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');
  
        const response = await axios.post('/api/auth/refresh', {
          refresh_token: refreshToken
        });
  
        const { access_token, new_refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        if (new_refresh_token) {
          localStorage.setItem('refresh_token', new_refresh_token);
        }
  
        setIsAuthenticated(true);
        return access_token;
      } catch (error) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setIsAuthenticated(false);
        throw error;
      }
    }, []);
  
    // Initial auth check
    useEffect(() => {
      const initializeAuth = async () => {
        try {
          const accessToken = localStorage.getItem('access_token');
          const refreshToken = localStorage.getItem('refresh_token');
  
          if (accessToken && refreshToken) {
            if (isTokenExpired(accessToken)) {
              await refreshAuth();
            } else {
              setIsAuthenticated(true);
            }
          }
        } catch (error) {
          console.error('Auth initialization failed:', error);
        } finally {
          setIsLoading(false);
        }
      };
  
      initializeAuth();
    }, [refreshAuth, isTokenExpired]);
  
    // Visibility change handler
    useEffect(() => {
      const handleVisibilityChange = async () => {
        if (document.visibilityState === 'visible' && isAuthenticated) {
          const accessToken = localStorage.getItem('access_token');
          if (accessToken && isTokenExpired(accessToken)) {
            try {
              await refreshAuth();
            } catch (error) {
              console.error('Token refresh failed:', error);
            }
          }
        }
      };
  
      document.addEventListener('visibilitychange', handleVisibilityChange);
      return () => {
        document.removeEventListener('visibilitychange', handleVisibilityChange);
      };
    }, [refreshAuth, isAuthenticated, isTokenExpired]);
  
    const login = useCallback(async (credentials) => {
      try {
        const response = await axios.post('/api/auth/login', credentials);
        const { access_token, refresh_token } = response.data;
  
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        setIsAuthenticated(true);
  
        return response.data;
      } catch (error) {
        throw error?.response?.data || error;
      }
    }, []);
  
    const value = {
      isAuthenticated,
      isLoading,
      login,
      logout,
      refreshAuth
    };
  
    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
  };

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};