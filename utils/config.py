API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
API_BASE_URL = "http://api.example.com/v1"

FALLBACK_MODELS = [
    "gpt-4o-mini",
]

API_FALLBACK_BASE_URLS = []

RETRY_BASE_DELAY = 2.0
RETRY_BACKOFF_FACTOR = 1.8
RETRY_MAX_DELAY = 20.0
RETRY_JITTER_LOW = 0.5
RETRY_JITTER_HIGH = 1.5
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
RETRYABLE_ERROR_SUBSTRINGS = [
    "upstream load saturated",
    "saturated",
    "rate limit",
    "overloaded",
    "model_not_found",
]

TOTAL_ROUNDS = 30
KEY_ROUNDS = list(range(1, TOTAL_ROUNDS + 1))
SERVERS = ['A', 'B', 'C']

PROFILES_FILE = "big5_user_profiles.json"

OUTPUT_DIR = "output/Multi-server_time_50agents_9visible"

ACTIONS_LOG_CSV = "logs_actions.csv"
STANCE_CHANGES_CSV = "logs_stance_changes.csv"
SATISFACTION_CSV = "logs_satisfaction.csv"
MIGRATIONS_CSV = "logs_migrations.csv"
DRAMATIC_STANCE_CHANGES_CSV = "logs_dramatic_stance_changes.csv"
MEMORY_COMPRESSION_CSV = "logs_memory_compression.csv"
TOKEN_USAGE_CSV = "logs_token_usage.csv"

SATISFACTION_HISTORY_JSON = "satisfaction_history.json"
FINAL_STATISTICS_TXT = "final_statistics.txt"
FINAL_PROFILES_JSON = "final_user_profiles.json"
NETWORK_GRAPH_PREFIX = "social_network_round_"
NETWORK_ANALYSIS_PREFIX = "network_analysis_round_"
NETWORK_STATE_PREFIX = "network_state_round_"

MAX_MEMORY_ITEMS = 100
MAX_REFLECTION_MEMORIES = 20
MAX_RELEVANT_MEMORIES = 5
MAX_FOLLOWING_POSTS = 3
MAX_SERVER_POSTS = 6
MAX_POST_CONTENT_LENGTH = 50
MAX_STANCE_HISTORY = 20
MAX_TOKEN_COUNT = 10000
MAX_DISPLAY_TOKEN_COUNT = 5000
