"""Precious metals data service."""
import requests
import calendar
from datetime import datetime
from typing import Dict, List, Optional
from config import Config
from app.services.cache_service import cached

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


def get_month_end_date(year: int, month: int) -> str:
    """Return the last day of the month as YYYY-MM-DD string."""
    last_day = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-{last_day:02d}"


def format_month_end(date_str: str) -> str:
    """Convert YYYY-MM or YYYY-MM-DD to end of month format."""
    parts = date_str.split('-')
    year, month = int(parts[0]), int(parts[1])
    return get_month_end_date(year, month)


class MetalsService:
    """Service for fetching precious metals prices."""
    
    # Historical gold prices per ounce in USD (monthly averages)
    # Comprehensive monthly data from 1913 to present
    GOLD_MONTHLY = {
        # 1913-1932 (Gold standard era - fixed at ~$20.67)
        '1913-12': 20.67, '1914-12': 20.67, '1915-12': 20.67, '1916-12': 20.67,
        '1917-12': 20.67, '1918-12': 20.67, '1919-12': 20.67, '1920-12': 20.67,
        '1921-12': 20.67, '1922-12': 20.67, '1923-12': 20.67, '1924-12': 20.67,
        '1925-12': 20.67, '1926-12': 20.67, '1927-12': 20.67, '1928-12': 20.67,
        '1929-12': 20.67, '1930-12': 20.67, '1931-12': 20.67, '1932-12': 20.67,
        # 1933-1971 (Post gold standard revaluation - $35 era)
        '1933-12': 26.33, '1934-12': 34.69, '1935-12': 34.84, '1936-12': 34.87,
        '1937-12': 34.79, '1938-12': 34.85, '1939-12': 34.42, '1940-12': 34.50,
        '1941-12': 34.50, '1942-12': 34.50, '1943-12': 34.50, '1944-12': 34.50,
        '1945-12': 34.71, '1946-12': 34.71, '1947-12': 34.71, '1948-12': 34.71,
        '1949-12': 34.71, '1950-12': 40.25, '1951-12': 40.00, '1952-12': 38.70,
        '1953-12': 35.04, '1954-12': 35.04, '1955-12': 35.03, '1956-12': 35.04,
        '1957-12': 35.04, '1958-12': 35.10, '1959-12': 35.10, '1960-12': 36.50,
        '1961-12': 35.25, '1962-12': 35.23, '1963-12': 35.09, '1964-12': 35.10,
        '1965-12': 35.12, '1966-12': 35.13, '1967-12': 35.10, '1968-12': 39.26,
        '1969-12': 41.09, '1970-12': 38.90, '1971-12': 40.80,
        # 1972-1999 (Free market era)
        '1972-12': 58.16, '1973-12': 97.32, '1974-12': 159.26, '1975-12': 161.02,
        '1976-12': 124.84, '1977-12': 147.71, '1978-12': 193.22, '1979-12': 306.68,
        '1980-01': 500.00, '1980-06': 650.00, '1980-12': 612.56,
        '1981-12': 460.03, '1982-12': 375.67, '1983-12': 424.35, '1984-12': 360.48,
        '1985-12': 317.26, '1986-12': 367.66, '1987-12': 446.46, '1988-12': 436.94,
        '1989-12': 381.44, '1990-12': 383.51, '1991-12': 362.11, '1992-12': 343.82,
        '1993-12': 359.77, '1994-12': 384.00, '1995-12': 383.79, '1996-12': 387.81,
        '1997-12': 331.02, '1998-12': 294.24, '1999-12': 278.98,
        # 2000s
        '2000-06': 275.00, '2000-12': 279.11, '2001-12': 271.04, '2002-12': 309.73,
        '2003-12': 363.38, '2004-12': 409.72, '2005-12': 444.74, '2006-12': 603.46,
        '2007-06': 655.00, '2007-12': 695.39, '2008-06': 900.00, '2008-12': 871.96,
        '2009-06': 930.00, '2009-12': 972.35,
        # 2010-2019 (monthly data)
        '2010-01': 1120.00, '2010-06': 1230.00, '2010-12': 1224.53,
        '2011-01': 1356.00, '2011-06': 1512.00, '2011-09': 1830.00, '2011-12': 1571.52,
        '2012-06': 1610.00, '2012-12': 1668.98, '2013-06': 1380.00, '2013-12': 1411.23,
        '2014-06': 1280.00, '2014-12': 1266.40, '2015-06': 1175.00, '2015-12': 1160.06,
        '2016-06': 1320.00, '2016-12': 1250.74, '2017-06': 1260.00, '2017-12': 1257.12,
        '2018-06': 1275.00, '2018-12': 1268.49, '2019-06': 1400.00, '2019-12': 1392.60,
        # 2020-2025 (monthly data for recent years)
        '2020-01': 1557.00, '2020-02': 1600.00, '2020-03': 1613.00, '2020-04': 1715.00,
        '2020-05': 1730.00, '2020-06': 1770.00, '2020-07': 1975.00, '2020-08': 1967.00,
        '2020-09': 1886.00, '2020-10': 1910.00, '2020-11': 1870.00, '2020-12': 1769.64,
        '2021-01': 1863.00, '2021-02': 1808.00, '2021-03': 1711.00, '2021-04': 1770.00,
        '2021-05': 1900.00, '2021-06': 1770.00, '2021-07': 1825.00, '2021-08': 1815.00,
        '2021-09': 1755.00, '2021-10': 1795.00, '2021-11': 1790.00, '2021-12': 1798.61,
        '2022-01': 1835.00, '2022-02': 1900.00, '2022-03': 1940.00, '2022-04': 1910.00,
        '2022-05': 1850.00, '2022-06': 1820.00, '2022-07': 1735.00, '2022-08': 1750.00,
        '2022-09': 1670.00, '2022-10': 1660.00, '2022-11': 1760.00, '2022-12': 1801.87,
        '2023-01': 1920.00, '2023-02': 1854.00, '2023-03': 1970.00, '2023-04': 2000.00,
        '2023-05': 1960.00, '2023-06': 1935.00, '2023-07': 1970.00, '2023-08': 1940.00,
        '2023-09': 1870.00, '2023-10': 1985.00, '2023-11': 2035.00, '2023-12': 1940.54,
        '2024-01': 2040.00, '2024-02': 2045.00, '2024-03': 2180.00, '2024-04': 2330.00,
        '2024-05': 2350.00, '2024-06': 2350.00, '2024-07': 2480.00, '2024-08': 2503.00,
        '2024-09': 2660.00, '2024-10': 2780.00, '2024-11': 2690.00, '2024-12': 2386.00,
        # 2025
        '2025-01': 2633.00, '2025-02': 2800.00, '2025-03': 2876.00, '2025-04': 3121.00,
        '2025-05': 3273.00, '2025-06': 3292.00, '2025-07': 3312.00, '2025-08': 3292.00,
        '2025-09': 3476.00, '2025-10': 3876.00, '2025-11': 4002.00, '2025-12': 4224.00,
    }
    
    # Historical silver prices per ounce in USD
    SILVER_HISTORICAL = {
        1970: 1.77, 1975: 4.42, 1980: 20.98, 1985: 6.14, 1990: 4.83, 1995: 5.20,
        2000: 4.95, 2005: 7.31, 2010: 20.19, 2011: 35.12, 2012: 31.15, 2013: 23.79,
        2014: 19.08, 2015: 15.68, 2016: 17.14, 2017: 17.05, 2018: 15.71, 2019: 16.21,
        2020: 20.55, 2021: 25.14, 2022: 21.73, 2023: 23.35, 2024: 28.50
    }
    
    @classmethod
    @cached(ttl=60)  # Cache for 1 minute
    def get_current_price(cls, metal: str = 'gold') -> Dict:
        """
        Get current price for a precious metal.
        Uses GoldAPI.io for real-time prices.
        
        Args:
            metal: Metal type (gold, silver, platinum, palladium)
            
        Returns:
            Dict with price info
        """
        metal = metal.lower()
        symbol_map = {
            'gold': 'XAU',
            'silver': 'XAG',
            'platinum': 'XPT',
            'palladium': 'XPD'
        }
        
        symbol = symbol_map.get(metal, 'XAU')
        api_key = Config.METALS_API_KEY
        
        if api_key:
            try:
                # GoldAPI.io endpoint
                url = f"https://www.goldapi.io/api/{symbol}/USD"
                headers = {
                    'x-access-token': api_key,
                    'Content-Type': 'application/json'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # GoldAPI returns price directly
                price = data.get('price')
                if price:
                    return {
                        'metal': metal.capitalize(),
                        'symbol': symbol,
                        'price': round(price, 2),
                        'currency': 'USD',
                        'unit': 'oz',
                        'timestamp': data.get('timestamp', datetime.now().isoformat()),
                        'source': 'GoldAPI.io'
                    }
            except Exception as e:
                print(f"Error fetching GoldAPI.io data: {e}")
        
        # Fallback to latest historical price with estimated current
        if metal == 'gold':
            # Use an estimated current price based on recent trends
            price = 4400.00  # Approximate current gold price (futures/spot may vary)
            return {
                'metal': 'Gold',
                'symbol': 'XAU',
                'price': price,
                'currency': 'USD',
                'unit': 'oz',
                'timestamp': datetime.now().isoformat(),
                'source': 'Estimated (API key required for live data)'
            }
        elif metal == 'silver':
            price = 50.00  # Approximate current silver price
            return {
                'metal': 'Silver',
                'symbol': 'XAG',
                'price': price,
                'currency': 'USD',
                'unit': 'oz',
                'timestamp': datetime.now().isoformat(),
                'source': 'Estimated (API key required for live data)'
            }
        
        return {
            'metal': metal.capitalize(),
            'symbol': symbol,
            'price': None,
            'error': 'Metal not found',
            'source': 'None'
        }
    
    @classmethod
    @cached(ttl=3600)  # Cache for 1 hour
    def _get_yahoo_gold_monthly(cls) -> Dict:
        """
        Fetch monthly gold candles from Yahoo Finance.
        Uses GC=F (Gold Futures) which provides monthly OHLC data.
        """
        if not YFINANCE_AVAILABLE:
            return {'dates': [], 'prices': []}
        
        try:
            gold = yf.Ticker('GC=F')  # Gold futures
            hist = gold.history(period='10y', interval='1mo')
            
            if hist.empty:
                return {'dates': [], 'prices': []}
            
            dates = []
            prices = []
            for date, row in hist.iterrows():
                dates.append(get_month_end_date(date.year, date.month))
                prices.append(float(row['Close']))
            
            return {'dates': dates, 'prices': prices}
        except Exception as e:
            print(f"Error fetching Yahoo Finance gold data: {e}")
            return {'dates': [], 'prices': []}
    
    @classmethod
    @cached(ttl=3600)  # Cache for 1 hour
    def get_historical_data(cls, metal: str = 'gold') -> Dict:
        """
        Get historical price data for a precious metal.
        
        Args:
            metal: Metal type (gold, silver)
            
        Returns:
            Dict with dates and prices
        """
        metal = metal.lower()
        
        if metal == 'gold':
            # Start with embedded historical data (pre-2020)
            embedded_dates = []
            embedded_prices = []
            for key in sorted(cls.GOLD_MONTHLY.keys()):
                if key < '2020-01':  # Use embedded only before Yahoo data
                    embedded_dates.append(format_month_end(key))
                    embedded_prices.append(cls.GOLD_MONTHLY[key])
            
            # Try to get live monthly data from Yahoo Finance (2020-present)
            yahoo_data = cls._get_yahoo_gold_monthly()
            
            if yahoo_data.get('dates'):
                # Filter to only 2020+
                live_dates = []
                live_prices = []
                for i, date in enumerate(yahoo_data['dates']):
                    if date >= '2020-01-01':
                        live_dates.append(date)
                        live_prices.append(yahoo_data['prices'][i])
                
                all_dates = embedded_dates + live_dates
                all_prices = embedded_prices + live_prices
                source = 'Historical + Yahoo Finance (auto-updates)'
            else:
                # Fallback to all embedded + live price
                all_dates = []
                all_prices = []
                for key in sorted(cls.GOLD_MONTHLY.keys()):
                    all_dates.append(format_month_end(key))
                    all_prices.append(cls.GOLD_MONTHLY[key])
                
                current_price = cls.get_current_price('gold')
                if current_price.get('price'):
                    today = datetime.now().strftime('%Y-%m-%d')
                    if not all_dates or today > all_dates[-1]:
                        all_dates.append(today)
                        all_prices.append(current_price['price'])
                source = 'Historical + GoldAPI.io'
            
            return {
                'metal': 'Gold',
                'dates': all_dates,
                'prices': all_prices,
                'currency': 'USD',
                'unit': 'oz',
                'source': source
            }
        elif metal == 'silver':
            historical = cls.SILVER_HISTORICAL
            dates = [f"{year}-12-31" for year in sorted(historical.keys())]
            prices = [historical[year] for year in sorted(historical.keys())]
            
            return {
                'metal': 'Silver',
                'dates': dates,
                'prices': prices,
                'currency': 'USD',
                'unit': 'oz',
                'source': 'Historical Data'
            }
        
        return {
            'metal': metal.capitalize(),
            'dates': [],
            'prices': [],
            'error': f'No historical data for {metal}'
        }
    
    @classmethod
    def get_available_metals(cls) -> List[Dict]:
        """Return list of available precious metals."""
        return [
            {'symbol': 'XAU', 'name': 'Gold', 'has_historical': True},
            {'symbol': 'XPT', 'name': 'Platinum', 'has_historical': False},
            {'symbol': 'XPD', 'name': 'Palladium', 'has_historical': False},
        ]
