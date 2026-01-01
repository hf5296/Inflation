"""Forex currency data service using Alpha Vantage API."""
import requests
from datetime import datetime
from typing import Dict, List, Optional
from config import Config
from app.services.cache_service import cached


class ForexService:
    """Service for fetching forex/currency exchange rate data."""
    
    # Supported currency pairs
    CURRENCIES = {
        'USD': 'US Dollar',
        'EUR': 'Euro',
        'GBP': 'British Pound',
        'JPY': 'Japanese Yen',
        'CHF': 'Swiss Franc',
        'CAD': 'Canadian Dollar',
        'AUD': 'Australian Dollar',
        'NZD': 'New Zealand Dollar',
        'CNY': 'Chinese Yuan',
        'INR': 'Indian Rupee',
    }
    
    # Historical exchange rates (USD to currency, annual averages)
    # This provides fallback data when API is unavailable
    HISTORICAL_RATES = {
        'JPY': {  # USD to JPY
            1970: 358.0, 1975: 297.0, 1980: 227.0, 1985: 239.0, 1990: 145.0,
            1995: 94.0, 2000: 108.0, 2005: 110.0, 2010: 88.0, 2015: 121.0,
            2020: 107.0, 2021: 110.0, 2022: 131.0, 2023: 141.0, 2024: 151.0
        },
        'EUR': {  # USD to EUR (post-1999)
            2000: 1.08, 2005: 0.80, 2010: 0.75, 2015: 0.90, 2020: 0.88,
            2021: 0.85, 2022: 0.95, 2023: 0.92, 2024: 0.93
        },
        'GBP': {  # USD to GBP
            1970: 0.42, 1975: 0.50, 1980: 0.43, 1985: 0.77, 1990: 0.56,
            1995: 0.63, 2000: 0.66, 2005: 0.55, 2010: 0.65, 2015: 0.65,
            2020: 0.78, 2021: 0.73, 2022: 0.81, 2023: 0.80, 2024: 0.79
        }
    }
    
    @classmethod
    @cached(ttl=300)  # Cache for 5 minutes
    def get_exchange_rate(cls, from_currency: str = 'USD', to_currency: str = 'EUR') -> Dict:
        """
        Get current exchange rate between two currencies.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Dict with exchange rate info
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        api_key = Config.ALPHA_VANTAGE_API_KEY
        
        if api_key:
            try:
                url = Config.ALPHA_VANTAGE_BASE_URL
                response = requests.get(url, params={
                    'function': 'CURRENCY_EXCHANGE_RATE',
                    'from_currency': from_currency,
                    'to_currency': to_currency,
                    'apikey': api_key
                }, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                rate_data = data.get('Realtime Currency Exchange Rate', {})
                if rate_data:
                    return {
                        'from': from_currency,
                        'to': to_currency,
                        'rate': float(rate_data.get('5. Exchange Rate', 0)),
                        'timestamp': rate_data.get('6. Last Refreshed'),
                        'source': 'Alpha Vantage'
                    }
            except Exception as e:
                print(f"Error fetching Alpha Vantage data: {e}")
        
        # Fallback to estimated rates
        estimated_rates = {
            ('USD', 'EUR'): 0.93,
            ('USD', 'GBP'): 0.79,
            ('USD', 'JPY'): 151.0,
            ('USD', 'CHF'): 0.88,
            ('USD', 'CAD'): 1.36,
            ('USD', 'AUD'): 1.55,
            ('EUR', 'USD'): 1.08,
            ('GBP', 'USD'): 1.27,
            ('JPY', 'USD'): 0.0066,
        }
        
        rate = estimated_rates.get((from_currency, to_currency))
        if rate:
            return {
                'from': from_currency,
                'to': to_currency,
                'rate': rate,
                'timestamp': datetime.now().isoformat(),
                'source': 'Estimated (API key required for live data)'
            }
        
        return {
            'from': from_currency,
            'to': to_currency,
            'rate': None,
            'error': 'Exchange rate not available',
            'source': 'None'
        }
    
    @classmethod
    @cached(ttl=3600)  # Cache for 1 hour
    def get_historical_rates(cls, from_currency: str = 'USD', to_currency: str = 'JPY') -> Dict:
        """
        Get historical exchange rate data.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Dict with dates and rates
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        api_key = Config.ALPHA_VANTAGE_API_KEY
        
        if api_key:
            try:
                url = Config.ALPHA_VANTAGE_BASE_URL
                response = requests.get(url, params={
                    'function': 'FX_MONTHLY',
                    'from_symbol': from_currency,
                    'to_symbol': to_currency,
                    'apikey': api_key,
                    'datatype': 'json'
                }, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                time_series = data.get('Time Series FX (Monthly)', {})
                if time_series:
                    dates = []
                    rates = []
                    for date in sorted(time_series.keys()):
                        dates.append(date)
                        rates.append(float(time_series[date]['4. close']))
                    
                    return {
                        'from': from_currency,
                        'to': to_currency,
                        'dates': dates,
                        'rates': rates,
                        'source': 'Alpha Vantage'
                    }
            except Exception as e:
                print(f"Error fetching Alpha Vantage historical data: {e}")
        
        # Fallback to embedded historical data
        if from_currency == 'USD' and to_currency in cls.HISTORICAL_RATES:
            historical = cls.HISTORICAL_RATES[to_currency]
            dates = [f"{year}-12-31" for year in sorted(historical.keys())]
            rates = [historical[year] for year in sorted(historical.keys())]
            
            return {
                'from': from_currency,
                'to': to_currency,
                'dates': dates,
                'rates': rates,
                'source': 'Historical Data'
            }
        
        return {
            'from': from_currency,
            'to': to_currency,
            'dates': [],
            'rates': [],
            'error': 'Historical data not available for this pair',
            'source': 'None'
        }
    
    @classmethod
    def get_available_currencies(cls) -> List[Dict]:
        """Return list of available currencies."""
        return [
            {'code': code, 'name': name}
            for code, name in cls.CURRENCIES.items()
        ]
    
    @classmethod
    def convert_amount(cls, amount: float, from_currency: str, to_currency: str) -> Dict:
        """
        Convert an amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Dict with conversion result
        """
        rate_info = cls.get_exchange_rate(from_currency, to_currency)
        
        if rate_info.get('rate'):
            converted = amount * rate_info['rate']
            return {
                'original_amount': amount,
                'original_currency': from_currency,
                'converted_amount': round(converted, 2),
                'converted_currency': to_currency,
                'rate': rate_info['rate'],
                'source': rate_info['source']
            }
        
        return {
            'error': 'Conversion not available',
            **rate_info
        }
