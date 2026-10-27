import axios from "axios";

export const TOKEN_KEY = "sales_auth_token";
export const EMAIL_KEY = "sales_auth_email";

const client = axios.create({ baseURL: "/api" });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let handleUnauthorized = () => {};

/** Registered by AuthContext so an expired token logs the user out. */
export function setUnauthorizedHandler(handler) {
  handleUnauthorized = handler;
}

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLoginRequest = error.config?.url?.includes("/login");
    if (error.response?.status === 401 && !isLoginRequest) handleUnauthorized();
    return Promise.reject(error);
  },
);

/** Turn an axios error into a readable message (FastAPI returns `detail` as a string or a list). */
export function getErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) return detail.map((d) => d.msg).join("; ");
  return fallback;
}

export default client;
