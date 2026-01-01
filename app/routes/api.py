"""API routes for the Inflation Tracker application."""
from flask import Blueprint, jsonify, request
from app.services.inflation_service import InflationService
from app.services.crypto_service import CryptoService
from app.services.metals_service import MetalsService
from app.services.forex_service import ForexService
from app.utils.calculations import (
    normalize_to_base,
    calculate_real_return,
    adjust_for_inflation,
    calculate_cagr,
    calculate_total_return
)

api_bp = Blueprint('api', __name__)


# ==================== INFLATION ENDPOINTS ====================

@api_bp.route('/inflation', methods=['GET'])
def get_inflation():
    """Get historical CPI data."""
    start_date = request.args.get('start', '1913-01-01')
    end_date = request.args.get('end', None)
    
    cpi_data = InflationService.get_cpi_data(start_date, end_date)
    return jsonify(cpi_data)


@api_bp.route('/inflation/rates', methods=['GET'])
def get_inflation_rates():
    """Get year-over-year inflation rates."""
    cpi_data = InflationService.get_cpi_data()
    rates = InflationService.calculate_inflation_rate(cpi_data)
    return jsonify(rates)


@api_bp.route('/inflation/purchasing-power', methods=['GET'])
def get_purchasing_power():
    """Get purchasing power of $100 over time."""
    base_year = request.args.get('base_year', 1913, type=int)
    cpi_data = InflationService.get_cpi_data()
    purchasing_power = InflationService.calculate_purchasing_power(cpi_data, base_year)
    return jsonify(purchasing_power)


@api_bp.route('/inflation/cumulative', methods=['GET'])
def get_cumulative_inflation():
    """Get cumulative inflation since base year."""
    base_year = request.args.get('base_year', 1913, type=int)
    cpi_data = InflationService.get_cpi_data()
    cumulative = InflationService.calculate_cumulative_inflation(cpi_data, base_year)
    return jsonify(cumulative)


@api_bp.route('/inflation/adjust', methods=['GET'])
def adjust_for_inflation_endpoint():
    """Adjust an amount for inflation between two years."""
    amount = request.args.get('amount', 100, type=float)
    from_year = request.args.get('from_year', 1913, type=int)
    to_year = request.args.get('to_year', 2024, type=int)
    
    cpi_data = InflationService.get_cpi_data()
    result = adjust_for_inflation(amount, from_year, to_year, cpi_data)
    return jsonify(result)


# ==================== CRYPTO ENDPOINTS ====================

@api_bp.route('/crypto/<symbol>', methods=['GET'])
def get_crypto_price(symbol):
    """Get current cryptocurrency price."""
    price_data = CryptoService.get_current_price(symbol)
    return jsonify(price_data)


@api_bp.route('/crypto/<symbol>/history', methods=['GET'])
def get_crypto_history(symbol):
    """Get historical cryptocurrency prices."""
    days = request.args.get('days', 365, type=int)
    include_all = request.args.get('all', 'false').lower() == 'true'
    
    if include_all:
        history = CryptoService.get_all_historical_data(symbol)
    else:
        history = CryptoService.get_historical_data(symbol, days)
    
    return jsonify(history)


@api_bp.route('/crypto', methods=['GET'])
def list_cryptos():
    """List available cryptocurrencies."""
    return jsonify(CryptoService.get_available_cryptos())


# ==================== METALS ENDPOINTS ====================

@api_bp.route('/metals/<metal>', methods=['GET'])
def get_metal_price(metal):
    """Get current precious metal price."""
    price_data = MetalsService.get_current_price(metal)
    return jsonify(price_data)


@api_bp.route('/metals/<metal>/history', methods=['GET'])
def get_metal_history(metal):
    """Get historical precious metal prices."""
    history = MetalsService.get_historical_data(metal)
    return jsonify(history)


@api_bp.route('/metals', methods=['GET'])
def list_metals():
    """List available precious metals."""
    return jsonify(MetalsService.get_available_metals())


# ==================== FOREX ENDPOINTS ====================

@api_bp.route('/forex/<from_currency>/<to_currency>', methods=['GET'])
def get_forex_rate(from_currency, to_currency):
    """Get current exchange rate between two currencies."""
    rate_data = ForexService.get_exchange_rate(from_currency, to_currency)
    return jsonify(rate_data)


@api_bp.route('/forex/<from_currency>/<to_currency>/history', methods=['GET'])
def get_forex_history(from_currency, to_currency):
    """Get historical exchange rates."""
    history = ForexService.get_historical_rates(from_currency, to_currency)
    return jsonify(history)


@api_bp.route('/forex/convert', methods=['GET'])
def convert_currency():
    """Convert an amount between currencies."""
    amount = request.args.get('amount', 100, type=float)
    from_currency = request.args.get('from', 'USD')
    to_currency = request.args.get('to', 'EUR')
    
    result = ForexService.convert_amount(amount, from_currency, to_currency)
    return jsonify(result)


@api_bp.route('/currencies', methods=['GET'])
def list_currencies():
    """List available currencies."""
    return jsonify(ForexService.get_available_currencies())


# ==================== COMPARISON ENDPOINTS ====================

@api_bp.route('/compare', methods=['POST'])
def compare_assets():
    """
    Compare multiple assets over time.
    
    Request body:
    {
        "assets": [
            {"type": "crypto", "symbol": "bitcoin"},
            {"type": "metal", "symbol": "gold"},
            {"type": "inflation", "symbol": "cpi"}
        ],
        "base_year": 2010,
        "normalize": true
    }
    """
    data = request.get_json()
    assets = data.get('assets', [])
    base_year = data.get('base_year')
    normalize = data.get('normalize', True)
    
    results = []
    
    for asset in assets:
        asset_type = asset.get('type', '').lower()
        symbol = asset.get('symbol', '')
        
        series = None
        
        if asset_type == 'crypto':
            history = CryptoService.get_all_historical_data(symbol)
            if history.get('dates'):
                series = {
                    'name': f"{symbol.upper()} Price",
                    'type': 'crypto',
                    'dates': history['dates'],
                    'values': history['prices'],
                    'source': history.get('source', 'Binance')
                }
        
        elif asset_type == 'metal':
            history = MetalsService.get_historical_data(symbol)
            if history.get('dates'):
                series = {
                    'name': f"{symbol.capitalize()} Price",
                    'type': 'metal',
                    'dates': history['dates'],
                    'values': history['prices'],
                    'source': history.get('source', 'Historical')
                }
        
        elif asset_type == 'inflation' or asset_type == 'cpi':
            cpi_data = InflationService.get_cpi_data()
            if cpi_data.get('dates'):
                if symbol == 'cumulative':
                    cum = InflationService.calculate_cumulative_inflation(cpi_data, base_year or 1913)
                    series = {
                        'name': 'Cumulative Inflation',
                        'type': 'inflation',
                        'dates': cum['dates'],
                        'values': cum['values'],
                        'source': cpi_data.get('source', 'FRED')
                    }
                elif symbol == 'purchasing_power':
                    pp = InflationService.calculate_purchasing_power(cpi_data, base_year or 1913)
                    series = {
                        'name': 'Purchasing Power',
                        'type': 'inflation',
                        'dates': pp['dates'],
                        'values': pp['values'],
                        'source': cpi_data.get('source', 'FRED')
                    }
                else:
                    series = {
                        'name': 'CPI Index',
                        'type': 'inflation',
                        'dates': cpi_data['dates'],
                        'values': cpi_data['values'],
                        'source': cpi_data.get('source', 'FRED')
                    }
        
        elif asset_type == 'forex':
            parts = symbol.split('/')
            if len(parts) == 2:
                history = ForexService.get_historical_rates(parts[0], parts[1])
                if history.get('dates'):
                    series = {
                        'name': f"{parts[0]}/{parts[1]} Rate",
                        'type': 'forex',
                        'dates': history['dates'],
                        'values': history['rates'],
                        'source': history.get('source', 'Historical')
                    }
        
        if series:
            if normalize and series.get('values'):
                base_date = f"{base_year}-01-01" if base_year else None
                normalized = normalize_to_base(series['dates'], series['values'], base_date)
                series['normalized_values'] = normalized['values']
                series['base_value'] = normalized['base_value']
                series['base_date'] = normalized['base_date']
            
            # Calculate returns
            if series.get('values') and len(series['values']) >= 2:
                series['total_return'] = calculate_total_return(series['values'])
                years = len(series['values'])
                if years > 1:
                    series['cagr'] = calculate_cagr(
                        series['values'][0],
                        series['values'][-1],
                        years
                    )
            
            results.append(series)
    
    # Find the latest start date among all assets (common date range)
    if results:
        latest_start_date = None
        for asset in results:
            if asset.get('dates') and len(asset['dates']) > 0:
                first_date = asset['dates'][0]
                if latest_start_date is None or first_date > latest_start_date:
                    latest_start_date = first_date
        
        # Trim all assets to start from the latest start date
        if latest_start_date:
            for asset in results:
                if asset.get('dates'):
                    new_dates = []
                    new_values = []
                    new_normalized = []
                    norm_values = asset.get('normalized_values', [])
                    for i, d in enumerate(asset['dates']):
                        if d >= latest_start_date:
                            new_dates.append(d)
                            if i < len(asset['values']):
                                new_values.append(asset['values'][i])
                            if i < len(norm_values):
                                new_normalized.append(norm_values[i])
                    asset['dates'] = new_dates
                    asset['values'] = new_values
                    if new_normalized:
                        asset['normalized_values'] = new_normalized
                    asset['common_start_date'] = latest_start_date
    
    return jsonify({
        'assets': results,
        'base_year': base_year,
        'normalized': normalize,
        'common_start_date': latest_start_date if results else None
    })


# ==================== DASHBOARD DATA ====================

@api_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get all data needed for the main dashboard."""
    # Get current prices
    btc_price = CryptoService.get_current_price('bitcoin')
    xmr_price = CryptoService.get_current_price('monero')
    gold_price = MetalsService.get_current_price('gold')
    
    # Get inflation data
    cpi_data = InflationService.get_cpi_data()
    inflation_rates = InflationService.calculate_inflation_rate(cpi_data)
    purchasing_power = InflationService.calculate_purchasing_power(cpi_data, 1913)
    
    # Calculate current year's inflation (approximate)
    current_inflation = inflation_rates['rates'][-1] if inflation_rates['rates'] else None
    
    # Calculate total inflation since 1913
    cumulative = InflationService.calculate_cumulative_inflation(cpi_data, 1913)
    total_inflation = cumulative['values'][-1] if cumulative['values'] else None
    
    return jsonify({
        'current_prices': {
            'bitcoin': btc_price,
            'monero': xmr_price,
            'gold': gold_price
        },
        'inflation': {
            'current_rate': current_inflation,
            'total_since_1913': total_inflation,
            'latest_cpi': cpi_data['values'][-1] if cpi_data['values'] else None,
            'purchasing_power_of_1913_dollar': purchasing_power['values'][-1] if purchasing_power['values'] else None
        },
        'historical_data': {
            'cpi': cpi_data,
            'purchasing_power': purchasing_power,
            'inflation_rates': inflation_rates
        }
    })


@api_bp.route('/assets', methods=['GET'])
def list_all_assets():
    """List all available assets for comparison."""
    return jsonify({
        'cryptocurrencies': CryptoService.get_available_cryptos(),
        'metals': MetalsService.get_available_metals(),
        'currencies': ForexService.get_available_currencies(),
        'inflation_metrics': [
            {'symbol': 'cpi', 'name': 'Consumer Price Index'},
            {'symbol': 'cumulative', 'name': 'Cumulative Inflation'},
            {'symbol': 'purchasing_power', 'name': 'Purchasing Power'}
        ]
    })
