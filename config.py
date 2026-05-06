import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ConfigError(Exception):
    """Configuration error exception."""
    pass

def get_required_env(key: str) -> str:
    """Get a required environment variable, raise error if not found."""
    value = os.getenv(key)
    if value is None:
        raise ConfigError(f"Required environment variable '{key}' is not set")
    return value

class Config:
    """Application configuration class."""

    def __init__(self):
        # API Keys
        self.action_api_key = get_required_env("ACTION_API_KEY")
        self.api_base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

        # OpenAI Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.sharp_api_key = os.getenv("SHARP_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")

        # Default Settings
        self.default_ticker = os.getenv("DEFAULT_TICKER", "NVDA")
        self.default_watchlist_str = os.getenv("DEFAULT_WATCHLIST", "AAPL,NVDA,TSLA,SPY,QQQ")
        self.default_watchlist = [ticker.strip() for ticker in self.default_watchlist_str.split(",")]
        self.default_period = os.getenv("DEFAULT_PERIOD", "1mo")
        self.default_interval = os.getenv("DEFAULT_INTERVAL", "1d")

        # Sports Betting Defaults
        self.default_sport = os.getenv("DEFAULT_SPORT", "basketball")
        self.default_league = os.getenv("DEFAULT_LEAGUE", "nba")

        # Request Configuration
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "20"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # File paths
        self.app_log_file = "app.log"
        self.data_dir = "data"
        self.stock_log_file = os.path.join(self.data_dir, "stock_log.csv")
        self.analysis_log_file = os.path.join(self.data_dir, "analysis_log.csv")
        self.bets_file = os.path.join(self.data_dir, "bets.csv")

def load_config() -> Config:
    """Load and return application configuration."""
    return Config()

# Global config instance for backward compatibility
config = load_config()