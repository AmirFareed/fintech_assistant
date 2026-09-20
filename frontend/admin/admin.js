// Shared admin shell: auth guard, sidebar/topbar, API helper.
// Each admin page provides <template id="page-content"> and sets <body data-page data-title>.
(function () {
  const TOKEN_KEY = "fintech_admin_token";

  const getToken = () => { try { return localStorage.getItem(TOKEN_KEY); } catch { return null; } };
  const setToken = (t) => { try { localStorage.setItem(TOKEN_KEY, t); } catch {} };
  const clearToken = () => { try { localStorage.removeItem(TOKEN_KEY); } catch {} };

  function logout() {
    clearToken();
    window.location.href = "login.html";
  }

  async function api(path, options = {}) {
    const headers = Object.assign({}, options.headers);
    const token = getToken();
    if (token) headers.Authorization = "Bearer " + token;
    const res = await fetch(window.apiUrl(path), Object.assign({}, options, { headers }));
    if (res.status === 401 && !options.noAuthRedirect) {
      logout();
      throw new Error("Session expired");
    }
    let data = null;
    try { data = await res.json(); } catch {}
    if (!res.ok) throw new Error((data && data.error) || "Request failed (" + res.status + ")");
    return data;
  }

  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const truncate = (v, n) => { const s = String(v ?? ""); return s.length > n ? s.slice(0, n - 1) + "…" : s; };
  const fmtTime = (v) => (v ? String(v).slice(0, 16).replace("T", " ") : "—");
  const resultBadge = (v) =>
    v === true ? '<span class="badge-found">Found</span>'
    : v === false ? '<span class="badge-not-found">Not Found</span>'
    : '<span class="badge-unknown">—</span>';

  function pagination(page, totalPages) {
    if (totalPages <= 1) return "";
    return '<div class="pagination">' +
      (page > 1 ? '<button class="page-btn" data-page="' + (page - 1) + '">← Prev</button>' : "") +
      '<span class="page-info">Page ' + page + " of " + totalPages + "</span>" +
      (page < totalPages ? '<button class="page-btn" data-page="' + (page + 1) + '">Next →</button>' : "") +
      "</div>";
  }

  const icon = (d) => '<svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.9" viewBox="0 0 24 24">' + d + "</svg>";
  const NAV = [
    ["dashboard", "Dashboard", "dashboard.html", '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>'],
    ["queries", "User Queries", "queries.html", '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'],
    ["feedback", "Feedback", "feedback.html", '<path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>'],
    ["knowledge", "Knowledge Base", "knowledge.html", '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>'],
    ["test", "Test Chatbot", "test.html", '<path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>'],
  ];

  function mountShell() {
    const page = document.body.dataset.page;
    const title = document.body.dataset.title || "Admin";
    const content = document.getElementById("page-content");
    const nav = NAV.map(([key, label, href, svg]) =>
      '<a href="' + href + '" class="nav-item' + (key === page ? " active" : "") + '"><span class="nav-icon">' + icon(svg) + "</span>" + label + "</a>"
    ).join("");

    document.title = title + " — FinTech Admin Panel";
    document.body.insertAdjacentHTML("afterbegin", `
<div class="app-shell">
  <aside class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <div class="logo-wrap"><img src="../assets/logo-wide.png" alt="FinTech" class="brand-logo"></div>
      <div class="logo-text-wrap"><span class="logo-tagline">Admin Panel</span></div>
    </div>
    <nav class="sidebar-nav"><p class="nav-label">Navigation</p>${nav}</nav>
    <div class="sidebar-footer">
      <a href="../index.html" target="_blank" class="nav-item"><span class="nav-icon">${icon('<path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>')}</span>User Portal</a>
      <a href="#" id="logoutLink" class="nav-item nav-logout"><span class="nav-icon">${icon('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>')}</span>Logout</a>
      <div class="user-pill" style="margin-top: 6px;">
        <div class="user-avatar-icon">A</div>
        <div class="user-info"><span class="user-name">Administrator</span><span class="user-role">Admin Access</span></div>
        <div class="online-dot"></div>
      </div>
    </div>
  </aside>
  <div class="sidebar-backdrop" id="sidebarBackdrop"></div>
  <main class="chat-main">
    <header class="topbar">
      <div class="topbar-left">
        <button class="mobile-menu-btn" id="menuBtn" aria-label="Toggle menu">
          <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
        </button>
        <div class="topbar-brand">
          <img src="../assets/fintech-logo.png" alt="FinTech Admin" class="topbar-logo">
          <div><div class="topbar-title">${esc(title)}</div>
            <div class="topbar-status"><span class="status-dot"></span><span class="status-text">FinTech Admin Panel</span></div></div>
        </div>
      </div>
      <div class="topbar-actions"><span class="admin-badge">Admin</span></div>
    </header>
    <div class="admin-content" id="adminContent"></div>
  </main>
</div>`);

    document.getElementById("adminContent").appendChild(content.content.cloneNode(true));

    const sidebar = document.getElementById("sidebar");
    const backdrop = document.getElementById("sidebarBackdrop");
    document.getElementById("menuBtn").addEventListener("click", () => {
      sidebar.classList.toggle("open");
      backdrop.classList.toggle("visible");
    });
    backdrop.addEventListener("click", () => {
      sidebar.classList.remove("open");
      backdrop.classList.remove("visible");
    });
    document.getElementById("logoutLink").addEventListener("click", (e) => { e.preventDefault(); logout(); });
  }

  window.Admin = { api, esc, truncate, fmtTime, resultBadge, pagination, getToken, setToken, logout };

  if (document.body.dataset.page === "login") return;
  if (!getToken()) { window.location.replace("login.html"); return; }
  mountShell();
  window.Admin.mounted = true;
})();
