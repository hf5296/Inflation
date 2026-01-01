"""Calculation utilities for inflation adjustments and data normalization."""
from typing import Dict, List, Tuple, Optional
from datetime import datetime


def normalize_to_base(dates: List[str], values: List[float], base_date: Optional[str] = None) -> Dict:
    """
    Normalize a series of values to a base date (default: first date).
    All values are expressed as percentage of the base value.
    
    Args:
        dates: List of date strings
        values: List of corresponding values
        base_date: Optional base date to normalize to (default: first date)
        
    Returns:
        Dict with dates and normalized values (base = 100)
    """
    if not dates or not values:
        return {'dates': [], 'values': [], 'base_value': None, 'base_date': None}
    
    # Filter out None values
    valid_pairs = [(d, v) for d, v in zip(dates, values) if v is not None and v != 0]
    if not valid_pairs:
        return {'dates': dates, 'values': [None] * len(dates), 'base_value': None, 'base_date': None}
    
    valid_dates, valid_values = zip(*valid_pairs)
    valid_dates = list(valid_dates)
    valid_values = list(valid_values)
    
    # Find base value
    base_value = valid_values[0]
    base_idx = 0
    
    if base_date:
        base_year = base_date[:4]
        for i, date in enumerate(valid_dates):
            if date.startswith(base_year):
                base_value = valid_values[i]
                base_idx = i
                break
    
    # Check for zero base value
    if base_value is None or base_value == 0:
        base_value = valid_values[0] if valid_values[0] != 0 else 1
    
    # Normalize
    normalized = [(v / base_value) * 100 if v is not None else None for v in valid_values]
    
    return {
        'dates': valid_dates,
        'values': [round(v, 2) if v is not None else None for v in normalized],
        'base_value': base_value,
        'base_date': valid_dates[base_idx]
    }


def calculate_real_return(
    asset_dates: List[str],
    asset_values: List[float],
    cpi_dates: List[str],
    cpi_values: List[float]
) -> Dict:
    """
    Calculate inflation-adjusted (real) returns for an asset.
    
    Args:
        asset_dates: Dates for asset prices
        asset_values: Asset price values
        cpi_dates: Dates for CPI values
        cpi_values: CPI values
        
    Returns:
        Dict with dates and real (inflation-adjusted) values
    """
    if not asset_dates or not asset_values:
        return {'dates': [], 'values': []}
    
    # Create CPI lookup by year
    cpi_by_year = {}
    for i, date in enumerate(cpi_dates):
        year = int(date.split('-')[0])
        cpi_by_year[year] = cpi_values[i]
    
    # Get the latest CPI for current dollar adjustment
    latest_cpi = max(cpi_values)
    
    # Adjust asset values for inflation
    real_values = []
    valid_dates = []
    
    for i, date in enumerate(asset_dates):
        year = int(date.split('-')[0])
        cpi = cpi_by_year.get(year)
        
        if cpi:
            # Adjust to current dollars
            real_value = asset_values[i] * (latest_cpi / cpi)
            real_values.append(round(real_value, 2))
            valid_dates.append(date)
    
    return {
        'dates': valid_dates,
        'values': real_values,
        'adjusted_to': 'Current Dollars'
    }


def align_time_series(series_list: List[Dict]) -> List[Dict]:
    """
    Align multiple time series to common dates.
    
    Args:
        series_list: List of dicts with 'dates' and 'values' keys
        
    Returns:
        List of aligned series with common dates
    """
    if not series_list:
        return []
    
    # Find common date range
    all_dates = set()
    for series in series_list:
        if series.get('dates'):
            all_dates.update(series['dates'])
    
    common_dates = sorted(list(all_dates))
    
    aligned = []
    for series in series_list:
        if not series.get('dates'):
            aligned.append(series)
            continue
        
        # Create lookup
        date_to_value = dict(zip(series['dates'], series['values']))
        
        # Interpolate or fill missing values
        new_values = []
        last_value = None
        
        for date in common_dates:
            if date in date_to_value:
                last_value = date_to_value[date]
                new_values.append(last_value)
            elif last_value is not None:
                new_values.append(last_value)  # Forward fill
            else:
                new_values.append(None)
        
        aligned_series = {**series, 'dates': common_dates, 'values': new_values}
        aligned.append(aligned_series)
    
    return aligned


def calculate_cagr(start_value: float, end_value: float, years: float) -> float:
    """
    Calculate Compound Annual Growth Rate.
    
    Args:
        start_value: Initial value
        end_value: Final value
        years: Number of years
        
    Returns:
        CAGR as a percentage
    """
    if start_value <= 0 or years <= 0:
        return 0.0
    
    cagr = ((end_value / start_value) ** (1 / years) - 1) * 100
    return round(cagr, 2)


def calculate_total_return(values: List[float]) -> float:
    """
    Calculate total return from a series of values.
    
    Args:
        values: List of values
        
    Returns:
        Total return as a percentage
    """
    if not values or len(values) < 2:
        return 0.0
    
    total_return = ((values[-1] - values[0]) / values[0]) * 100
    return round(total_return, 2)


def adjust_for_inflation(
    amount: float,
    from_year: int,
    to_year: int,
    cpi_data: Dict
) -> Dict:
    """
    Adjust an amount for inflation between two years.
    
    Args:
        amount: Dollar amount to adjust
        from_year: Year of the original amount
        to_year: Year to adjust to
        cpi_data: Dict with CPI dates and values
        
    Returns:
        Dict with adjusted amount and details
    """
    # Create CPI lookup by year
    cpi_by_year = {}
    for i, date in enumerate(cpi_data['dates']):
        year = int(date.split('-')[0])
        cpi_by_year[year] = cpi_data['values'][i]
    
    from_cpi = cpi_by_year.get(from_year)
    to_cpi = cpi_by_year.get(to_year)
    
    if not from_cpi or not to_cpi:
        return {
            'error': f'CPI data not available for {from_year} or {to_year}',
            'original_amount': amount,
            'from_year': from_year,
            'to_year': to_year
        }
    
    adjusted = amount * (to_cpi / from_cpi)
    inflation_factor = to_cpi / from_cpi
    cumulative_inflation = ((to_cpi - from_cpi) / from_cpi) * 100
    
    return {
        'original_amount': amount,
        'adjusted_amount': round(adjusted, 2),
        'from_year': from_year,
        'to_year': to_year,
        'from_cpi': from_cpi,
        'to_cpi': to_cpi,
        'inflation_factor': round(inflation_factor, 4),
        'cumulative_inflation_percent': round(cumulative_inflation, 2)
    }


def get_year_from_date(date_str: str) -> int:
    """Extract year from date string."""
    return int(date_str.split('-')[0])


def interpolate_annual_to_monthly(annual_dates: List[str], annual_values: List[float]) -> Tuple[List[str], List[float]]:
    """
    Interpolate annual data to monthly frequency.
    Simple linear interpolation between years.
    
    Args:
        annual_dates: List of annual date strings (YYYY-MM-DD)
        annual_values: List of annual values
        
    Returns:
        Tuple of (monthly_dates, monthly_values)
    """
    if len(annual_dates) < 2:
        return annual_dates, annual_values
    
    monthly_dates = []
    monthly_values = []
    
    for i in range(len(annual_dates) - 1):
        year1 = get_year_from_date(annual_dates[i])
        year2 = get_year_from_date(annual_dates[i + 1])
        value1 = annual_values[i]
        value2 = annual_values[i + 1]
        
        # Generate monthly values
        months_between = (year2 - year1) * 12
        value_step = (value2 - value1) / months_between
        
        for m in range(months_between):
            year = year1 + m // 12
            month = (m % 12) + 1
            monthly_dates.append(f"{year}-{month:02d}-01")
            monthly_values.append(round(value1 + value_step * m, 2))
    
    # Add the last value
    monthly_dates.append(annual_dates[-1])
    monthly_values.append(annual_values[-1])
    
    return monthly_dates, monthly_values
