// frontend/src/api/client.js
import { Platform } from "react-native";

// On Android Emulator, localhost points to the device itself.
// 10.0.2.2 reaches the host computer's localhost.
const DEFAULT_URL = Platform.OS === "android" ? "http://10.0.2.2:8000" : "http://localhost:8000";
export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || DEFAULT_URL;

/**
 * Universal API Client with automatic Bearer token injection
 */
export async function apiRequest(endpoint, { method = "GET", body = null, token = null } = {}) {
  const headers = {
    "Accept": "application/json",
  };

  if (body && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const config = {
    method,
    headers,
  };

  if (body) {
    config.body = body instanceof FormData ? body : JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

  if (!response.ok) {
    let errorDetail = "API request failed";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch (_) {
      errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    }
    const error = new Error(errorDetail);
    error.status = response.status;
    throw error;
  }

  // If response is empty or 204 No Content
  if (response.status === 204) return null;

  try {
    return await response.json();
  } catch (_) {
    return null;
  }
}

export const api = {
  get: (endpoint, token) => apiRequest(endpoint, { method: "GET", token }),
  post: (endpoint, body, token) => apiRequest(endpoint, { method: "POST", body, token }),
  put: (endpoint, body, token) => apiRequest(endpoint, { method: "PUT", body, token }),
  delete: (endpoint, token) => apiRequest(endpoint, { method: "DELETE", token }),
};
