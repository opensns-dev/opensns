import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const path = window.location.pathname;
      if (
        path !== "/" &&
        !path.startsWith("/login") &&
        !path.startsWith("/register") &&
        !path.startsWith("/auth/") &&
        !path.startsWith("/onboarding")
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
  } catch {
  }
};
