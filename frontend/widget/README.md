# User Chat Widget

Embeddable chat widget. It is static (JS + CSS) and talks to the backend only over HTTP (`/api/chat`, `/api/feedback`).

## Embedding

Load `config.js` (sets the backend URL), then the widget script. The widget loads its own CSS.

```html
<script src="https://your-frontend.example.com/config.js"></script>
<script src="https://your-frontend.example.com/widget/user-chat.js" defer></script>
```

To override individual options instead of using `config.js`:

```html
<script>
  window.FintechUserChatWidgetConfig = {
    apiEndpoint: "https://your-backend.example.com/api/chat",
    logoUrl: "https://your-frontend.example.com/assets/fintech-logo.png",
    stylesheetUrl: "https://your-frontend.example.com/widget/user-chat.css"
  };
</script>
<script src="https://your-frontend.example.com/widget/user-chat.js" defer></script>
```

## Cross-origin setup

The backend must allow the embedding origin. Set `WIDGET_ALLOWED_ORIGINS` in `backend/.env`:

- `*` for open embedding
- or a comma-separated list, e.g. `https://your-app.example.com,https://another-app.example.com`
