from typing import Any

from supabase import ClientOptions, create_client
from utils.config import Config


class LazySupabaseClient:
    """Create the network client only when a database operation is requested."""

    def __init__(self) -> None:
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
                raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be configured.")
            self._client = create_client(
                Config.SUPABASE_URL,
                Config.SUPABASE_KEY,
                options=ClientOptions(postgrest_client_timeout=Config.SUPABASE_TIMEOUT_SECONDS),
            )
        return self._client

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_client(), name)


supabase = LazySupabaseClient()
