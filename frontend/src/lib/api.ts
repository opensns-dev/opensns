import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

export function getToken() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") {
    return;
  }

  if (token) {
    window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
    return;
  }

  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setRefreshToken(token: string | null) {
  if (typeof window === "undefined") {
    return;
  }

  if (token) {
    window.localStorage.setItem(REFRESH_TOKEN_KEY, token);
    return;
  }

  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function removeToken() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = getToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const path = window.location.pathname;
      const requestUrl = String(error.config?.url || "");
      const publicPrefixes = ["/login", "/register", "/forgot-password", "/auth/", "/onboarding", "/pricing", "/terms", "/privacy", "/refund", "/contact"];

      if (requestUrl.includes("/auth/me")) {
        return Promise.reject(error);
      }

      removeToken();

      if (
        path !== "/" &&
        !publicPrefixes.some((prefix) => path.startsWith(prefix))
      ) {
        window.location.href = "/login/";
      }
    }
    return Promise.reject(error);
  }
);

export const logout = async () => {
  try {
    await api.post("/auth/logout");
  } finally {
    removeToken();
  }
};
