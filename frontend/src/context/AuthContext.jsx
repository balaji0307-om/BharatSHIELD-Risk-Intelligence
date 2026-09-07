import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [merchantId, setMerchantId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('bharatshield_token') || sessionStorage.getItem('bharatshield_token');
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const me = await authAPI.getMe();
        setUser(me);
        setMerchantId(me.merchant_id || 'MER_razorpay_001');
      } catch (err) {
        // Token expired or revoked — clear invalid state
        localStorage.removeItem('bharatshield_token');
        sessionStorage.removeItem('bharatshield_token');
        setUser(null);
        setMerchantId(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const handleLogin = (authData, rememberMe = false) => {
    const storage = rememberMe ? localStorage : sessionStorage;
    storage.setItem('bharatshield_token', authData.access_token);
    if (authData.refresh_token) {
      storage.setItem('bharatshield_refresh_token', authData.refresh_token);
    }
    setUser({
      email: authData.email,
      merchant_id: authData.merchant_id,
    });
    setMerchantId(authData.merchant_id);
  };

  const handleLogout = async () => {
    await authAPI.logout();
    setUser(null);
    setMerchantId(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        merchantId,
        isAuthenticated: !!user,
        isLoading,
        login: handleLogin,
        logout: handleLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
};
