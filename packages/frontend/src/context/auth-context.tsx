import { api, ApiError, User } from "@/lib/api-client";
import React, {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";
import { toast } from "sonner";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (
    username: string,
    email: string,
    password: string
  ) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state on mount
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    const token = localStorage.getItem("auth_token");
    const savedUser = localStorage.getItem("user");

    if (token && savedUser) {
      try {
        // Parse saved user
        const parsedUser = JSON.parse(savedUser) as User;
        setUser(parsedUser);

        // Verify token is still valid by fetching current user
        await refreshUser();
      } catch (error) {
        console.warn("Failed to initialize auth from stored data:", error);
        logout();
      }
    }

    setIsLoading(false);
  };

  const login = async (username: string, password: string): Promise<void> => {
    try {
      setIsLoading(true);

      // Login and get token
      const tokenResponse = await api.auth.login(username, password);

      // Store token
      localStorage.setItem("auth_token", tokenResponse.access_token);

      // Fetch user data
      const userData = await api.auth.getCurrentUser();

      // Store user data
      localStorage.setItem("user", JSON.stringify(userData));
      setUser(userData);

      toast.success("Logged in successfully", {
        description: `Welcome back, ${userData.username}!`,
      });
    } catch (error) {
      const apiError = error as ApiError;
      toast.error("Login failed", {
        description:
          apiError.detail || "Please check your credentials and try again.",
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (
    username: string,
    email: string,
    password: string
  ): Promise<void> => {
    try {
      setIsLoading(true);

      // Register user
      const userData = await api.auth.register(username, email, password);

      // Auto-login after successful registration
      await login(username, password);

      toast.success("Account created successfully", {
        description: `Welcome to RepoChat, ${userData.username}!`,
      });
    } catch (error) {
      const apiError = error as ApiError;
      toast.error("Registration failed", {
        description:
          apiError.detail || "Please try again with different credentials.",
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user");
    setUser(null);

    toast.info("Logged out successfully", {
      description: "You have been signed out of your account.",
    });
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const userData = await api.auth.getCurrentUser();
      localStorage.setItem("user", JSON.stringify(userData));
      setUser(userData);
    } catch (error) {
      console.warn("Failed to refresh user data:", error);
      logout();
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
