import apiClient, { api } from "@/lib/api-client";
import React, { createContext, useContext, useEffect, useState } from "react";

// Define the API base URL
const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

// API interfaces
interface User {
  id: string; // This will be a UUID string from the backend
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
}

interface RegisterData {
  username: string;
  email: string;
  password: string;
}

interface LoginData {
  username: string;
  password: string;
}

interface AuthToken {
  access_token: string;
  token_type: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (loginData: LoginData) => Promise<void>;
  register: (registerData: RegisterData) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Create provider component
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      setIsLoading(true);
      const token = localStorage.getItem("auth_token");

      if (token) {
        try {
          // Fetch user data to validate token
          const userData = await api.get<User>("/auth/me");
          // Ensure the id is a string (in case it's a UUID object)
          if (userData && typeof userData.id !== "string") {
            userData.id = String(userData.id);
          }
          setUser(userData);
        } catch (err) {
          console.error("Error fetching user data, clearing token:", err);
          localStorage.removeItem("auth_token");
          setUser(null);
        }
      }

      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  // Configure axios to use the token for all requests
  useEffect(() => {
    const token = localStorage.getItem("auth_token");

    if (token) {
      apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
    } else {
      delete apiClient.defaults.headers.common.Authorization;
    }
  }, [user]);

  // Login function
  const login = async (loginData: LoginData) => {
    setIsLoading(true);
    setError(null);

    try {
      // Call the login API
      const authToken = await api.post<AuthToken>(
        "/auth/login/json",
        loginData
      );

      // Store the token
      localStorage.setItem("auth_token", authToken.access_token);

      // Set auth header for subsequent requests
      apiClient.defaults.headers.common.Authorization = `Bearer ${authToken.access_token}`;

      // Fetch user data
      const userData = await api.get<User>("/auth/me");
      // Ensure the id is a string
      if (userData && typeof userData.id !== "string") {
        userData.id = String(userData.id);
      }
      setUser(userData);
    } catch (err: unknown) {
      console.error("Login failed:", err);
      const error = err as { response?: { data?: { detail?: string } } };
      setError(
        error.response?.data?.detail || "Login failed. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Register function
  const register = async (registerData: RegisterData) => {
    setIsLoading(true);
    setError(null);

    try {
      // Call the register API
      await api.post<User>("/auth/register", registerData);

      // Auto-login after successful registration
      await login({
        username: registerData.username,
        password: registerData.password,
      });
    } catch (err: unknown) {
      console.error("Registration failed:", err);
      const error = err as { response?: { data?: { detail?: string } } };
      setError(
        error.response?.data?.detail || "Registration failed. Please try again."
      );
      setIsLoading(false);
    }
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem("auth_token");
    delete apiClient.defaults.headers.common.Authorization;
    setUser(null);
  };

  // Clear error
  const clearError = () => {
    setError(null);
  };

  // Create context value
  const contextValue: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    register,
    logout,
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
}

// Create a hook for using the auth context
export function useAuth() {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}
