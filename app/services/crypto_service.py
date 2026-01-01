"""Cryptocurrency data service using Binance API."""
import requests
import calendar
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config import Config
from app.services.cache_service import cached


def get_month_end_date(year: int, month: int) -> str:
    """Return the last day of the month as YYYY-MM-DD string."""
    last_day = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-{last_day:02d}"


def format_month_end(date_str: str) -> str:
    """Convert YYYY-MM or YYYY-MM-DD to end of month format."""
    parts = date_str.split('-')
    year, month = int(parts[0]), int(parts[1])
    return get_month_end_date(year, month)


class CryptoService:
    """Service for fetching cryptocurrency data from Binance API."""
    
    # Mapping of common names to Binance symbols
    SYMBOL_MAP = {
        'bitcoin': 'BTCUSDT',
        'btc': 'BTCUSDT',
        'monero': 'XMRUSDT',
        'xmr': 'XMRUSDT',
        'solana': 'SOLUSDT',
        'sol': 'SOLUSDT',
        'ripple': 'XRPUSDT',
        'xrp': 'XRPUSDT',
        'cardano': 'ADAUSDT',
        'ada': 'ADAUSDT',
        'dogecoin': 'DOGEUSDT',
        'doge': 'DOGEUSDT',
    }
    
    # Bitcoin monthly price data in USD (end of month prices)
    # Comprehensive data from 2009 to present
    BTC_MONTHLY = {
        # 2009-2012 (early years, sparse data)
        '2009-12': 0.001, '2010-06': 0.08, '2010-12': 0.30,
        '2011-06': 15.00, '2011-12': 4.70, '2012-06': 6.50, '2012-12': 13.50,
        # 2013
        '2013-01': 13.50, '2013-02': 28.00, '2013-03': 92.00, '2013-04': 139.00,
        '2013-05': 129.00, '2013-06': 97.00, '2013-07': 105.00, '2013-08': 120.00,
        '2013-09': 140.00, '2013-10': 198.00, '2013-11': 1075.00, '2013-12': 760.00,
        # 2014
        '2014-01': 800.00, '2014-02': 550.00, '2014-03': 450.00, '2014-04': 450.00,
        '2014-05': 630.00, '2014-06': 640.00, '2014-07': 590.00, '2014-08': 510.00,
        '2014-09': 390.00, '2014-10': 340.00, '2014-11': 375.00, '2014-12': 320.00,
        # 2015
        '2015-01': 220.00, '2015-02': 255.00, '2015-03': 245.00, '2015-04': 235.00,
        '2015-05': 235.00, '2015-06': 265.00, '2015-07': 285.00, '2015-08': 230.00,
        '2015-09': 235.00, '2015-10': 315.00, '2015-11': 375.00, '2015-12': 430.00,
        # 2016
        '2016-01': 380.00, '2016-02': 435.00, '2016-03': 415.00, '2016-04': 450.00,
        '2016-05': 530.00, '2016-06': 670.00, '2016-07': 625.00, '2016-08': 575.00,
        '2016-09': 605.00, '2016-10': 700.00, '2016-11': 740.00, '2016-12': 965.00,
        # 2017 (bull run)
        '2017-01': 970.00, '2017-02': 1190.00, '2017-03': 1080.00, '2017-04': 1350.00,
        '2017-05': 2300.00, '2017-06': 2500.00, '2017-07': 2875.00, '2017-08': 4700.00,
        '2017-09': 4340.00, '2017-10': 6130.00, '2017-11': 10400.00, '2017-12': 13880.00,
        # 2018 (bear market)
        '2018-01': 10200.00, '2018-02': 10700.00, '2018-03': 7000.00, '2018-04': 9300.00,
        '2018-05': 7500.00, '2018-06': 6400.00, '2018-07': 8200.00, '2018-08': 7000.00,
        '2018-09': 6600.00, '2018-10': 6300.00, '2018-11': 4000.00, '2018-12': 3742.00,
        # 2019
        '2019-01': 3400.00, '2019-02': 3800.00, '2019-03': 4100.00, '2019-04': 5300.00,
        '2019-05': 8550.00, '2019-06': 10800.00, '2019-07': 9600.00, '2019-08': 9600.00,
        '2019-09': 8300.00, '2019-10': 9200.00, '2019-11': 7550.00, '2019-12': 7200.00,
        # 2020
        '2020-01': 9350.00, '2020-02': 8600.00, '2020-03': 6400.00, '2020-04': 8800.00,
        '2020-05': 9450.00, '2020-06': 9150.00, '2020-07': 11350.00, '2020-08': 11650.00,
        '2020-09': 10800.00, '2020-10': 13800.00, '2020-11': 19700.00, '2020-12': 29000.00,
        # 2021
        '2021-01': 33100.00, '2021-02': 45200.00, '2021-03': 58800.00, '2021-04': 57700.00,
        '2021-05': 37300.00, '2021-06': 35000.00, '2021-07': 41500.00, '2021-08': 47100.00,
        '2021-09': 43800.00, '2021-10': 61300.00, '2021-11': 57000.00, '2021-12': 46300.00,
        # 2022
        '2022-01': 38500.00, '2022-02': 43200.00, '2022-03': 45500.00, '2022-04': 37600.00,
        '2022-05': 31800.00, '2022-06': 19900.00, '2022-07': 23300.00, '2022-08': 20000.00,
        '2022-09': 19400.00, '2022-10': 20500.00, '2022-11': 17150.00, '2022-12': 16500.00,
        # 2023
        '2023-01': 23100.00, '2023-02': 23500.00, '2023-03': 28450.00, '2023-04': 29250.00,
        '2023-05': 27200.00, '2023-06': 30450.00, '2023-07': 29200.00, '2023-08': 26000.00,
        '2023-09': 27000.00, '2023-10': 34500.00, '2023-11': 37700.00, '2023-12': 42500.00,
        # 2024
        '2024-01': 42600.00, '2024-02': 62000.00, '2024-03': 71300.00, '2024-04': 60700.00,
        '2024-05': 67500.00, '2024-06': 62700.00, '2024-07': 64600.00, '2024-08': 58900.00,
        '2024-09': 63300.00, '2024-10': 70200.00, '2024-11': 96400.00, '2024-12': 93500.00,
    }
    
    # Monero monthly price data in USD (end of month prices)
    # From launch in 2014 to present
    XMR_MONTHLY = {
        # 2014 (launched April 2014)
        '2014-05': 2.50, '2014-06': 2.20, '2014-07': 1.80, '2014-08': 1.50,
        '2014-09': 1.20, '2014-10': 0.80, '2014-11': 0.70, '2014-12': 0.50,
        # 2015
        '2015-01': 0.45, '2015-02': 0.40, '2015-03': 0.38, '2015-04': 0.45,
        '2015-05': 0.50, '2015-06': 0.55, '2015-07': 0.50, '2015-08': 0.48,
        '2015-09': 0.50, '2015-10': 0.48, '2015-11': 0.45, '2015-12': 0.50,
        # 2016
        '2016-01': 0.45, '2016-02': 0.50, '2016-03': 0.70, '2016-04': 1.20,
        '2016-05': 2.50, '2016-06': 2.80, '2016-07': 2.20, '2016-08': 5.00,
        '2016-09': 8.50, '2016-10': 9.00, '2016-11': 8.00, '2016-12': 12.00,
        # 2017 (bull run)
        '2017-01': 13.00, '2017-02': 14.00, '2017-03': 19.00, '2017-04': 28.00,
        '2017-05': 52.00, '2017-06': 45.00, '2017-07': 50.00, '2017-08': 140.00,
        '2017-09': 95.00, '2017-10': 90.00, '2017-11': 195.00, '2017-12': 350.00,
        # 2018 (bear market)
        '2018-01': 310.00, '2018-02': 260.00, '2018-03': 190.00, '2018-04': 210.00,
        '2018-05': 165.00, '2018-06': 135.00, '2018-07': 140.00, '2018-08': 95.00,
        '2018-09': 115.00, '2018-10': 105.00, '2018-11': 60.00, '2018-12': 45.00,
        # 2019
        '2019-01': 45.00, '2019-02': 48.00, '2019-03': 54.00, '2019-04': 68.00,
        '2019-05': 92.00, '2019-06': 95.00, '2019-07': 85.00, '2019-08': 75.00,
        '2019-09': 58.00, '2019-10': 60.00, '2019-11': 55.00, '2019-12': 48.00,
        # 2020
        '2020-01': 65.00, '2020-02': 72.00, '2020-03': 45.00, '2020-04': 62.00,
        '2020-05': 65.00, '2020-06': 68.00, '2020-07': 78.00, '2020-08': 95.00,
        '2020-09': 95.00, '2020-10': 125.00, '2020-11': 135.00, '2020-12': 155.00,
        # 2021
        '2021-01': 165.00, '2021-02': 240.00, '2021-03': 245.00, '2021-04': 380.00,
        '2021-05': 310.00, '2021-06': 225.00, '2021-07': 245.00, '2021-08': 310.00,
        '2021-09': 265.00, '2021-10': 290.00, '2021-11': 265.00, '2021-12': 215.00,
        # 2022
        '2022-01': 185.00, '2022-02': 175.00, '2022-03': 215.00, '2022-04': 230.00,
        '2022-05': 190.00, '2022-06': 120.00, '2022-07': 155.00, '2022-08': 155.00,
        '2022-09': 145.00, '2022-10': 150.00, '2022-11': 140.00, '2022-12': 145.00,
        # 2023
        '2023-01': 170.00, '2023-02': 160.00, '2023-03': 155.00, '2023-04': 160.00,
        '2023-05': 150.00, '2023-06': 165.00, '2023-07': 165.00, '2023-08': 145.00,
        '2023-09': 150.00, '2023-10': 165.00, '2023-11': 170.00, '2023-12': 175.00,
        # 2024
        '2024-01': 165.00, '2024-02': 130.00, '2024-03': 140.00, '2024-04': 135.00,
        '2024-05': 165.00, '2024-06': 160.00, '2024-07': 165.00, '2024-08': 175.00,
        '2024-09': 180.00, '2024-10': 185.00, '2024-11': 210.00, '2024-12': 437.00,
    }
    
    @classmethod
    def _get_binance_symbol(cls, symbol: str) -> str:
        """Convert common name to Binance trading pair."""
        return cls.SYMBOL_MAP.get(symbol.lower(), symbol.upper() + 'USDT')
    
    @classmethod
    @cached(ttl=60)  # Cache for 1 minute
    def get_current_price(cls, symbol: str = 'bitcoin') -> Dict:
        """
        Get current price for a cryptocurrency.
        Uses CoinGecko for Monero (delisted from Binance), Binance for others.
        
        Args:
            symbol: Cryptocurrency symbol or name (e.g., 'bitcoin', 'BTC')
            
        Returns:
            Dict with price info
        """
        symbol_lower = symbol.lower()
        
        # Use CoinGecko for Monero (Binance delisted XMR in Feb 2024)
        if symbol_lower in ['monero', 'xmr']:
            return cls._get_coingecko_price('monero', 'XMR')
        
        # Use Binance for other cryptos
        binance_symbol = cls._get_binance_symbol(symbol)
        url = f"{Config.BINANCE_BASE_URL}/ticker/price"
        
        try:
            response = requests.get(url, params={'symbol': binance_symbol}, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'symbol': symbol.upper(),
                'price': float(data['price']),
                'currency': 'USD',
                'timestamp': datetime.now().isoformat(),
                'source': 'Binance API'
            }
            
        except Exception as e:
            print(f"Error fetching Binance price: {e}")
            return {
                'symbol': symbol.upper(),
                'price': None,
                'error': str(e),
                'source': 'Binance API'
            }
    
    @classmethod
    def _get_coingecko_price(cls, coin_id: str, symbol: str) -> Dict:
        """
        Get price from CoinGecko API (free, no key needed).
        Used for coins not available on Binance like Monero.
        """
        url = "https://api.coingecko.com/api/v3/simple/price"
        try:
            response = requests.get(url, params={
                'ids': coin_id,
                'vs_currencies': 'usd'
            }, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            price = data.get(coin_id, {}).get('usd')
            if price:
                return {
                    'symbol': symbol,
                    'price': price,
                    'currency': 'USD',
                    'timestamp': datetime.now().isoformat(),
                    'source': 'CoinGecko API'
                }
        except Exception as e:
            print(f"Error fetching CoinGecko price: {e}")
        
        return {
            'symbol': symbol,
            'price': None,
            'error': 'Failed to fetch price',
            'source': 'CoinGecko API'
        }
    
    @classmethod
    @cached(ttl=300)  # Cache for 5 minutes
    def get_historical_data(cls, symbol: str = 'bitcoin', days: int = 365) -> Dict:
        """
        Get historical price data for a cryptocurrency.
        
        Args:
            symbol: Cryptocurrency symbol or name
            days: Number of days of history (max ~1000 from Binance)
            
        Returns:
            Dict with dates and prices
        """
        binance_symbol = cls._get_binance_symbol(symbol)
        url = f"{Config.BINANCE_BASE_URL}/klines"
        
        # Calculate start time
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        try:
            response = requests.get(url, params={
                'symbol': binance_symbol,
                'interval': '1d',  # Daily candles
                'startTime': start_time,
                'endTime': end_time,
                'limit': min(days, 1000)
            }, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            dates = []
            prices = []
            
            for candle in data:
                # Candle format: [open_time, open, high, low, close, volume, ...]
                timestamp = candle[0] / 1000
                date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                close_price = float(candle[4])
                
                dates.append(date)
                prices.append(close_price)
            
            return {
                'symbol': symbol.upper(),
                'dates': dates,
                'prices': prices,
                'currency': 'USD',
                'source': 'Binance API'
            }
            
        except Exception as e:
            print(f"Error fetching Binance historical data: {e}")
            return {
                'symbol': symbol.upper(),
                'dates': [],
                'prices': [],
                'error': str(e),
                'source': 'Binance API'
            }
    
    @classmethod
    def _get_coingecko_historical(cls, coin_id: str, symbol: str, days: int = 365) -> Dict:
        """
        Get historical data from CoinGecko API.
        Used for coins not available on Binance like Monero.
        """
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        try:
            response = requests.get(url, params={
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            dates = []
            prices = []
            
            for point in data.get('prices', []):
                timestamp = point[0] / 1000
                date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                price = point[1]
                dates.append(date)
                prices.append(price)
            
            return {
                'symbol': symbol,
                'dates': dates,
                'prices': prices,
                'currency': 'USD',
                'source': 'CoinGecko API'
            }
        except Exception as e:
            print(f"Error fetching CoinGecko historical data: {e}")
            return {
                'symbol': symbol,
                'dates': [],
                'prices': [],
                'error': str(e),
                'source': 'CoinGecko API'
            }
    
    @classmethod
    def _get_binance_monthly(cls, symbol: str) -> Dict:
        """
        Fetch monthly candles from Binance API.
        Returns all available monthly data (goes back to 2017).
        """
        binance_symbol = cls._get_binance_symbol(symbol)
        url = f"{Config.BINANCE_BASE_URL}/klines"
        
        try:
            response = requests.get(url, params={
                'symbol': binance_symbol,
                'interval': '1M',  # Monthly candles
                'limit': 100  # Get all available months
            }, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            dates = []
            prices = []
            
            for candle in data:
                timestamp = candle[0] / 1000
                dt = datetime.fromtimestamp(timestamp)
                date = get_month_end_date(dt.year, dt.month)
                close_price = float(candle[4])
                dates.append(date)
                prices.append(close_price)
            
            return {'dates': dates, 'prices': prices}
        except Exception as e:
            print(f"Error fetching Binance monthly data: {e}")
            return {'dates': [], 'prices': []}
        
    @classmethod
    def _get_kraken_monthly(cls, pair: str = 'XMRUSD') -> Dict:
        """
        Fetch monthly-ish candles from Kraken API for XMR.
        Kraken provides 2-week candles which we'll use to approximate monthly.
        """
        try:
            response = requests.get('https://api.kraken.com/0/public/OHLC', params={
                'pair': pair,
                'interval': 21600  # 2-week candles (21600 minutes)
            }, timeout=15)
            data = response.json()
            
            if 'result' not in data:
                return {'dates': [], 'prices': []}
            
            # Kraken uses different key names
            result_key = list(data['result'].keys())[0]
            candles = data['result'][result_key]
            
            # Convert to monthly by taking first candle of each month
            monthly_data = {}
            for candle in candles:
                date = datetime.fromtimestamp(candle[0])
                month_key = date.strftime('%Y-%m')
                if month_key not in monthly_data:
                    monthly_data[month_key] = float(candle[4])  # Close price
            
            dates = [f"{k}-01" for k in sorted(monthly_data.keys())]
            prices = [monthly_data[k] for k in sorted(monthly_data.keys())]
            
            return {'dates': dates, 'prices': prices}
        except Exception as e:
            print(f"Error fetching Kraken data: {e}")
            return {'dates': [], 'prices': []}
    
    @classmethod
    def get_all_historical_data(cls, symbol: str = 'bitcoin') -> Dict:
        """
        Get complete historical data by merging:
        1. Embedded data (pre-2017 for BTC, pre-2024 for XMR)
        2. LIVE monthly candles from APIs (Binance for BTC, Kraken for XMR)
        """
        symbol_lower = symbol.lower()
        
        # === MONERO: Merge embedded (pre-2024) + Kraken (2024-present) ===
        if symbol_lower in ['monero', 'xmr']:
            # Start with embedded pre-2024 data
            embedded_dates = []
            embedded_prices = []
            for key in sorted(cls.XMR_MONTHLY.keys()):
                if key < '2024-01':  # Use embedded only before 2024
                    embedded_dates.append(format_month_end(key))
                    embedded_prices.append(cls.XMR_MONTHLY[key])
            
            # Fetch live data from Kraken (2024-present)
            kraken_data = cls._get_kraken_monthly('XMRUSD')
            
            if kraken_data.get('dates'):
                # Filter Kraken data to only 2024+
                live_dates = []
                live_prices = []
                for i, date in enumerate(kraken_data['dates']):
                    if date >= '2024-01-01':
                        live_dates.append(date)
                        live_prices.append(kraken_data['prices'][i])
                
                all_dates = embedded_dates + live_dates
                all_prices = embedded_prices + live_prices
            else:
                # Fallback to embedded + current price
                all_dates = []
                all_prices = []
                for key in sorted(cls.XMR_MONTHLY.keys()):
                    all_dates.append(format_month_end(key))
                    all_prices.append(cls.XMR_MONTHLY[key])
                
                current = cls.get_current_price('monero')
                if current.get('price'):
                    today = datetime.now().strftime('%Y-%m-%d')
                    if not all_dates or today > all_dates[-1]:
                        all_dates.append(today)
                        all_prices.append(current['price'])
            
            return {
                'symbol': 'XMR',
                'dates': all_dates,
                'prices': all_prices,
                'currency': 'USD',
                'source': 'Historical + Kraken (auto-updates)'
            }
        
        # === BITCOIN: Merge embedded (pre-2017) + Binance monthly (2017-present) ===
        if symbol_lower in ['bitcoin', 'btc']:
            # Start with embedded pre-2017 data
            embedded_dates = []
            embedded_prices = []
            for key in sorted(cls.BTC_MONTHLY.keys()):
                if key < '2017-08':  # Use embedded only before Binance era
                    embedded_dates.append(format_month_end(key))
                    embedded_prices.append(cls.BTC_MONTHLY[key])
            
            # Fetch live monthly data from Binance (2017-present, including 2025!)
            binance_data = cls._get_binance_monthly('bitcoin')
            
            if binance_data.get('dates'):
                # Merge: embedded + binance
                all_dates = embedded_dates + binance_data['dates']
                all_prices = embedded_prices + binance_data['prices']
            else:
                # Fallback to embedded if API fails
                all_dates = []
                all_prices = []
                for key in sorted(cls.BTC_MONTHLY.keys()):
                    all_dates.append(format_month_end(key))
                    all_prices.append(cls.BTC_MONTHLY[key])
            
            # Ensure dates and prices have same length
            min_len = min(len(all_dates), len(all_prices))
            all_dates = all_dates[:min_len]
            all_prices = all_prices[:min_len]
            
            return {
                'symbol': 'BTC',
                'dates': all_dates,
                'prices': all_prices,
                'currency': 'USD',
                'source': 'Historical + Binance Monthly (auto-updates)'
            }
        
        # For other cryptos, try Binance directly
        return cls.get_historical_data(symbol, days=365)
    
    @classmethod
    def get_available_cryptos(cls) -> List[Dict]:
        """Return list of available cryptocurrencies."""
        return [
            {'symbol': 'BTC', 'name': 'Bitcoin', 'has_historical': True},
            {'symbol': 'XMR', 'name': 'Monero', 'has_historical': True},
            {'symbol': 'SOL', 'name': 'Solana', 'has_historical': False},
            {'symbol': 'XRP', 'name': 'Ripple', 'has_historical': False},
            {'symbol': 'ADA', 'name': 'Cardano', 'has_historical': False},
            {'symbol': 'DOGE', 'name': 'Dogecoin', 'has_historical': False},
        ]

