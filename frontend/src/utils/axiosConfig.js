// utils/axiosConfig.js — Global axios configuration with request cancellation
import axios from "axios";

// Configure base URL for backend
axios.defaults.baseURL = "http://127.0.0.1:8081";
axios.defaults.timeout = 90000; // 90 second timeout for Ollama

// Store for tracking all active requests
const activeRequests = new Map();

// Request interceptor - track all outgoing requests
axios.interceptors.request.use(
  (config) => {
    // Create cancel token for this request
    const source = axios.CancelToken.source();
    config.cancelToken = source.token;

    // Store the cancel function with request ID
    const requestId = `${config.method}-${config.url}-${Date.now()}`;
    activeRequests.set(requestId, source);

    // Attach request ID to config for cleanup in response interceptor
    config.requestId = requestId;

    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor - cleanup completed requests
axios.interceptors.response.use(
  (response) => {
    // Remove from active requests on success
    if (response.config.requestId) {
      activeRequests.delete(response.config.requestId);
    }
    return response;
  },
  (error) => {
    // Remove from active requests on error
    if (error.config?.requestId) {
      activeRequests.delete(error.config.requestId);
    }
    return Promise.reject(error);
  },
);

/**
 * Cancel all active axios requests
 * Called during session restart to prevent stale context contamination
 */
export function cancelAllRequests(reason = "Session restart") {
  console.log(
    `[AXIOS] Cancelling ${activeRequests.size} active requests: ${reason}`,
  );

  activeRequests.forEach((source, requestId) => {
    try {
      source.cancel(reason);
    } catch (err) {
      console.warn(`[AXIOS] Failed to cancel request ${requestId}:`, err);
    }
  });

  activeRequests.clear();
  console.log("[AXIOS] All requests cancelled");
}

/**
 * Get count of active requests (for debugging)
 */
export function getActiveRequestCount() {
  return activeRequests.size;
}

export default axios;
