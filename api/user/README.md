# User Chat Widget

This folder contains the isolated user-side chat widget for the project.

## What it uses

- Existing backend chat endpoint: `/api/chat`
- Separate Flask blueprint: `user/`
- Separate assets for user-only UI

## Preview route

- `/user/`

## Real app integration

If your real application is served by this Flask app, the simplest integration is:

```html
<script>
  window.FintechUserChatWidgetConfig = {
    apiEndpoint: "/api/chat",
    logoUrl: "/static/fintech-logo.png"
  };
</script>
<script src="/user/static/user-chat.js" defer></script>
```

The script auto-loads its own CSS, so the extra `<link>` tag is optional.

If the real application is on another origin, use absolute backend URLs:

```html
<script>
  window.FintechUserChatWidgetConfig = {
    apiEndpoint: "https://your-backend.example.com/api/chat",
    logoUrl: "https://your-backend.example.com/static/fintech-logo.png",
    stylesheetUrl: "https://your-backend.example.com/user/static/user-chat.css"
  };
</script>
<script src="https://your-backend.example.com/user/static/user-chat.js" defer></script>
```

## Cross-origin setup

For external sites, configure:

- `WIDGET_ALLOWED_ORIGINS=*` for open embedding
- or `WIDGET_ALLOWED_ORIGINS=https://your-app.example.com,https://another-app.example.com`

The backend now responds to widget CORS preflight requests on `/api/chat`.
