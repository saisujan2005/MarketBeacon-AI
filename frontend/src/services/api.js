import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Request Interceptor: Automatically inject Access Token if present
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("accessToken");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Automatically refresh token on 401 Unauthorized
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    const status = error.response ? error.response.status : null;
    
    // Ignore if not a 401 or if it's already a retry or if we're hitting login/register
    if (
      !error.response ||
      status !== 401 ||
      originalRequest._retry ||
      (originalRequest.url && (originalRequest.url.includes("/api/auth/login") || originalRequest.url.includes("/api/auth/register")))
    ) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then((token) => {
          originalRequest.headers["Authorization"] = `Bearer ${token}`;
          return api(originalRequest);
        })
        .catch((err) => {
          return Promise.reject(err);
        });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    const refreshToken = localStorage.getItem("refreshToken");
    if (!refreshToken) {
      isRefreshing = false;
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("user");
      window.dispatchEvent(new Event("auth-logout"));
      return Promise.reject(error);
    }

    try {
      // Use clean axios call to avoid request interceptor loops
      const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
        refresh_token: refreshToken,
      });

      const { access_token, refresh_token: new_refresh_token } = response.data;
      localStorage.setItem("accessToken", access_token);
      localStorage.setItem("refreshToken", new_refresh_token);

      api.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
      originalRequest.headers["Authorization"] = `Bearer ${access_token}`;

      processQueue(null, access_token);
      isRefreshing = false;
      return api(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      isRefreshing = false;
      
      const refreshStatus = refreshError.response ? refreshError.response.status : null;
      
      // LOG OUT ONLY ON 401 or 403 (expired/invalid refresh token)
      if (refreshStatus === 401 || refreshStatus === 403) {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        localStorage.removeItem("user");
        window.dispatchEvent(new Event("auth-logout"));
      }
      
      return Promise.reject(refreshError);
    }
  }
);

export default api;