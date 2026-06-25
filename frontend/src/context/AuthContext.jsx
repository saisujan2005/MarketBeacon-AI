import { createContext, useContext, useState, useEffect } from "react";
import api from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check login status on load
  useEffect(() => {
    async function checkAuth() {
      const accessToken = localStorage.getItem("accessToken");
      const refreshToken = localStorage.getItem("refreshToken");
      
      if (accessToken || refreshToken) {
        try {
          const res = await api.get("/api/auth/me");
          setUser(res.data);
          localStorage.setItem("user", JSON.stringify(res.data));
        } catch (err) {
          console.error("Session check failed", err);
          
          const currentAccessToken = localStorage.getItem("accessToken");
          const currentRefreshToken = localStorage.getItem("refreshToken");
          
          if (!currentAccessToken && !currentRefreshToken) {
            setUser(null);
          } else {
            // Keep the cached session on transient failures!
            const cachedUserStr = localStorage.getItem("user");
            if (cachedUserStr) {
              try {
                const cachedUser = JSON.parse(cachedUserStr);
                setUser(cachedUser);
              } catch (e) {
                console.error("Failed to parse cached user", e);
                setUser(null);
              }
            } else {
              setUser(null);
            }
          }
        }
      } else {
        setUser(null);
      }
      setLoading(false);
    }
    
    checkAuth();

    // Listen to global logout events from api interceptor
    const handleLogoutEvent = () => {
      setUser(null);
    };
    window.addEventListener("auth-logout", handleLogoutEvent);
    return () => window.removeEventListener("auth-logout", handleLogoutEvent);
  }, []);

  const login = async (email, password, rememberMe = false) => {
    const res = await api.post("/api/auth/login", { email, password, remember_me: rememberMe });
    const { access_token, refresh_token, user: userData } = res.data;
    
    localStorage.setItem("accessToken", access_token);
    localStorage.setItem("refreshToken", refresh_token);
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const register = async (fullName, email, password, confirmPassword) => {
    const res = await api.post("/api/auth/register", {
      full_name: fullName,
      email,
      password,
      confirm_password: confirmPassword,
    });
    const { access_token, refresh_token, user: userData } = res.data;
    
    localStorage.setItem("accessToken", access_token);
    localStorage.setItem("refreshToken", refresh_token);
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const logout = async (allDevices = false) => {
    try {
      await api.post("/api/auth/logout", { all_devices: allDevices });
    } catch (e) {
      console.warn("Logout endpoint error, clearing local state anyway");
    } finally {
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("user");
      setUser(null);
    }
  };

  const updateProfile = async (profileData) => {
    const res = await api.put("/api/auth/profile", profileData);
    setUser(res.data);
    localStorage.setItem("user", JSON.stringify(res.data));
    return res.data;
  };

  const updatePreferences = async (prefData) => {
    const res = await api.put("/api/auth/preferences", prefData);
    // Update local user's preferences block
    const updatedUser = {
      ...user,
      preferences: res.data.preferences
    };
    setUser(updatedUser);
    localStorage.setItem("user", JSON.stringify(updatedUser));
    return res.data;
  };

  const updatePassword = async (pwdData) => {
    await api.put("/api/auth/password", pwdData);
  };

  const deleteAccount = async () => {
    await api.delete("/api/auth/account");
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("user");
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const res = await api.get("/api/auth/me");
      setUser(res.data);
      localStorage.setItem("user", JSON.stringify(res.data));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        updateProfile,
        updatePreferences,
        updatePassword,
        deleteAccount,
        refreshUser
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
