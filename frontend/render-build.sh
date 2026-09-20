#!/bin/sh
# Render build step: bake the backend URL (API_BASE_URL env var) into config.js.
set -eu

if [ -z "${API_BASE_URL:-}" ]; then
  echo "API_BASE_URL is not set. Set it in the Render dashboard (e.g. https://chat.1-2-3-4.sslip.io)." >&2
  exit 1
fi

API_BASE_URL="${API_BASE_URL%/}"

cat > config.js <<EOF
// Generated at build time by render-build.sh
window.APP_CONFIG = {
  apiBaseUrl: "${API_BASE_URL}",
};

window.apiUrl = function (path) {
  return String(window.APP_CONFIG.apiBaseUrl || "").replace(/\/+\$/, "") + path;
};
EOF

echo "config.js written for ${API_BASE_URL}"
