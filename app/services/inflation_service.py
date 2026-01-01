"""Inflation/CPI data service using FRED API."""
import requests
from datetime import datetime
from typing import Dict, List, Optional
from config import Config
from app.services.cache_service import cached


class InflationService:
    """Service for fetching and processing US inflation data from FRED."""
    
    # FRED series ID for CPI-U (Consumer Price Index for All Urban Consumers)
    CPI_SERIES = 'CPIAUCNS'
    
    @classmethod
    @cached(ttl=3600)  # Cache for 1 hour
    def get_cpi_data(cls, start_date: str = '1913-01-01', end_date: Optional[str] = None) -> Dict:
        """
        Fetch historical CPI data from FRED API.
        
        Args:
            start_date: Start date in YYYY-MM-DD format (default: 1913-01-01)
            end_date: End date in YYYY-MM-DD format (default: today)
            
        Returns:
            Dict with dates and CPI values
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        api_key = Config.FRED_API_KEY
        
        if not api_key:
            # Return fallback data if no API key
            return cls._get_fallback_cpi_data()
        
        url = f"{Config.FRED_BASE_URL}/series/observations"
        params = {
            'series_id': cls.CPI_SERIES,
            'api_key': api_key,
            'file_type': 'json',
            'observation_start': start_date,
            'observation_end': end_date,
            'frequency': 'a',  # Annual frequency
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            observations = data.get('observations', [])
            
            result = {
                'dates': [],
                'values': [],
                'source': 'FRED API'
            }
            
            for obs in observations:
                if obs['value'] != '.':
                    result['dates'].append(obs['date'])
                    result['values'].append(float(obs['value']))
            
            return result
            
        except Exception as e:
            print(f"Error fetching FRED data: {e}")
            return cls._get_fallback_cpi_data()
    
    @classmethod
    def _get_fallback_cpi_data(cls) -> Dict:
        """
        Return embedded historical CPI data as fallback.
        This data covers key years from 1913 to present.
        """
        # Historical CPI-U data (annual averages) - Base period: 1982-84=100
        historical_cpi = {
            1913: 9.9, 1914: 10.0, 1915: 10.1, 1916: 10.9, 1917: 12.8, 1918: 15.0,
            1919: 17.3, 1920: 20.0, 1921: 17.9, 1922: 16.8, 1923: 17.1, 1924: 17.1,
            1925: 17.5, 1926: 17.7, 1927: 17.4, 1928: 17.2, 1929: 17.2, 1930: 16.7,
            1931: 15.2, 1932: 13.6, 1933: 12.9, 1934: 13.4, 1935: 13.7, 1936: 13.9,
            1937: 14.4, 1938: 14.1, 1939: 13.9, 1940: 14.0, 1941: 14.7, 1942: 16.3,
            1943: 17.3, 1944: 17.6, 1945: 18.0, 1946: 19.5, 1947: 22.3, 1948: 24.0,
            1949: 23.8, 1950: 24.1, 1951: 26.0, 1952: 26.6, 1953: 26.8, 1954: 26.9,
            1955: 26.8, 1956: 27.2, 1957: 28.1, 1958: 28.9, 1959: 29.2, 1960: 29.6,
            1961: 29.9, 1962: 30.3, 1963: 30.6, 1964: 31.0, 1965: 31.5, 1966: 32.5,
            1967: 33.4, 1968: 34.8, 1969: 36.7, 1970: 38.8, 1971: 40.5, 1972: 41.8,
            1973: 44.4, 1974: 49.3, 1975: 53.8, 1976: 56.9, 1977: 60.6, 1978: 65.2,
            1979: 72.6, 1980: 82.4, 1981: 90.9, 1982: 96.5, 1983: 99.6, 1984: 103.9,
            1985: 107.6, 1986: 109.6, 1987: 113.6, 1988: 118.3, 1989: 124.0, 1990: 130.7,
            1991: 136.2, 1992: 140.3, 1993: 144.5, 1994: 148.2, 1995: 152.4, 1996: 156.9,
            1997: 160.5, 1998: 163.0, 1999: 166.6, 2000: 172.2, 2001: 177.1, 2002: 179.9,
            2003: 184.0, 2004: 188.9, 2005: 195.3, 2006: 201.6, 2007: 207.3, 2008: 215.3,
            2009: 214.5, 2010: 218.1, 2011: 224.9, 2012: 229.6, 2013: 233.0, 2014: 236.7,
            2015: 237.0, 2016: 240.0, 2017: 245.1, 2018: 251.1, 2019: 255.7, 2020: 258.8,
            2021: 271.0, 2022: 292.7, 2023: 304.7, 2024: 315.5
        }
        
        dates = [f"{year}-01-01" for year in sorted(historical_cpi.keys())]
        values = [historical_cpi[year] for year in sorted(historical_cpi.keys())]
        
        return {
            'dates': dates,
            'values': values,
            'source': 'Embedded Historical Data'
        }
    
    @classmethod
    def calculate_inflation_rate(cls, cpi_data: Dict) -> Dict:
        """
        Calculate year-over-year inflation rates from CPI data.
        
        Args:
            cpi_data: Dict with dates and CPI values
            
        Returns:
            Dict with dates and inflation rates (as percentages)
        """
        dates = cpi_data['dates']
        values = cpi_data['values']
        
        inflation_rates = []
        inflation_dates = []
        
        for i in range(1, len(values)):
            rate = ((values[i] - values[i-1]) / values[i-1]) * 100
            inflation_rates.append(round(rate, 2))
            inflation_dates.append(dates[i])
        
        return {
            'dates': inflation_dates,
            'rates': inflation_rates,
            'source': cpi_data.get('source', 'Unknown')
        }
    
    @classmethod
    def calculate_purchasing_power(cls, cpi_data: Dict, base_year: int = 1913) -> Dict:
        """
        Calculate the purchasing power of $1 over time relative to a base year.
        
        Args:
            cpi_data: Dict with dates and CPI values
            base_year: Year to use as base (default: 1913)
            
        Returns:
            Dict with dates and purchasing power values
        """
        dates = cpi_data['dates']
        values = cpi_data['values']
        
        # Find the CPI value for the base year
        base_cpi = None
        base_index = None
        for i, date in enumerate(dates):
            year = int(date.split('-')[0])
            if year == base_year:
                base_cpi = values[i]
                base_index = i
                break
        
        if base_cpi is None:
            # Use first available year as base
            base_cpi = values[0]
        
        purchasing_power = []
        for value in values:
            pp = (base_cpi / value) * 100  # $100 in base year is worth...
            purchasing_power.append(round(pp, 2))
        
        return {
            'dates': dates,
            'values': purchasing_power,
            'base_year': base_year,
            'description': f'Purchasing power of $100 from {base_year}',
            'source': cpi_data.get('source', 'Unknown')
        }
    
    @classmethod
    def calculate_cumulative_inflation(cls, cpi_data: Dict, base_year: int = 1913) -> Dict:
        """
        Calculate cumulative inflation since a base year.
        
        Args:
            cpi_data: Dict with dates and CPI values
            base_year: Year to use as base (default: 1913)
            
        Returns:
            Dict with dates and cumulative inflation percentages
        """
        dates = cpi_data['dates']
        values = cpi_data['values']
        
        # Find the CPI value for the base year
        base_cpi = None
        for i, date in enumerate(dates):
            year = int(date.split('-')[0])
            if year == base_year:
                base_cpi = values[i]
                break
        
        if base_cpi is None:
            base_cpi = values[0]
        
        cumulative = []
        for value in values:
            cum = ((value - base_cpi) / base_cpi) * 100
            cumulative.append(round(cum, 2))
        
        return {
            'dates': dates,
            'values': cumulative,
            'base_year': base_year,
            'description': f'Cumulative inflation since {base_year} (%)',
            'source': cpi_data.get('source', 'Unknown')
        }
