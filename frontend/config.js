// Runtime configuration for the static frontend.
// Point apiBaseUrl at the backend (no trailing slash). Leave "" only if a reverse
// proxy serves the backend's /api/* paths from the same origin as this frontend.
window.APP_CONFIG = {
  apiBaseUrl: "http://localhost:5000",
};

window.apiUrl = function (path) {
  return String(window.APP_CONFIG.apiBaseUrl || "").replace(/\/+$/, "") + path;
};
