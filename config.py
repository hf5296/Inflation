"""Configuration management for the Inflation Tracker application."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # API Keys
    FRED_API_KEY = os.getenv('FRED_API_KEY', '')
    METALS_API_KEY = os.getenv('METALS_API_KEY', '')
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
    
    # API URLs
    FRED_BASE_URL = 'https://api.stlouisfed.org/fred'
    BINANCE_BASE_URL = 'https://api.binance.com/api/v3'
    METALS_API_BASE_URL = 'https://metals-api.com/api'
    ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co/query'
    
    # Cache settings (in seconds)
    CACHE_TIMEOUT_REALTIME = 60  # 1 minute for real-time data
    CACHE_TIMEOUT_HISTORICAL = 3600  # 1 hour for historical data
