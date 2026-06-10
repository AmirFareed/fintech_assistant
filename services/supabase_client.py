from supabase import ClientOptions, create_client
from config import Config

supabase = create_client(
    Config.SUPABASE_URL,
    Config.SUPABASE_KEY,
    options=ClientOptions(postgrest_client_timeout=Config.SUPABASE_TIMEOUT_SECONDS),
)
