# 📈 Inflation Tracker

A comprehensive Python-based dashboard to track US inflation from 1913 to present and compare it against various assets including Bitcoin, Gold, currencies, and more.

![Dashboard Preview](https://via.placeholder.com/800x400?text=Inflation+Tracker+Dashboard)

## ✨ Features

- **📊 US Inflation Data**: Historical CPI data from 1913 to present
- **💰 Real-time Prices**: Live Bitcoin, Ethereum, Gold, and Silver prices
- **📉 Interactive Charts**: Zoomable, pannable Plotly.js charts
- **🔄 Asset Comparison**: Compare any combination of assets normalized to a base year
- **🧮 Inflation Calculator**: Calculate the inflation-adjusted value of any amount
- **🌙 Modern Dark UI**: Premium glassmorphism design with smooth animations

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd "/Users/hishamfadhel/Library/CloudStorage/GoogleDrive-hfadhel140802@gmail.com/My Drive/Inflation"
   ```

2. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```

3. **Create your environment file** (optional but recommended):
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and add your API keys (see API Keys section below).

4. **Run the application**:
   ```bash
   python run.py
   ```

5. **Open in browser**:
   Navigate to [http://localhost:5000](http://localhost:5000)

## 🔑 API Keys

The application works without API keys using embedded historical data, but for real-time data, you'll need:

| API | Purpose | Get Key | Required? |
|-----|---------|---------|-----------|
| **FRED API** | US CPI/Inflation data | [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html) | Optional |
| **Metals-API** | Gold, Silver prices | [metals-api.com](https://metals-api.com/) | Optional |
| **Alpha Vantage** | Forex rates | [alphavantage.co](https://www.alphavantage.co/support/#api-key) | Optional |
| **Binance** | Crypto prices | Not needed (public API) | N/A |

### Setting Up API Keys

Create a `.env` file in the project root:

```env
FRED_API_KEY=your_fred_api_key_here
METALS_API_KEY=your_metals_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
```

## 📁 Project Structure

```
Inflation/
├── run.py                    # Application entry point
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── .env                      # Your API keys (gitignored)
│
├── app/
│   ├── __init__.py           # Flask app factory
│   │
│   ├── routes/
│   │   ├── api.py            # REST API endpoints
│   │   └── views.py          # Page routes
│   │
│   ├── services/
│   │   ├── inflation_service.py  # FRED/CPI data
│   │   ├── crypto_service.py     # Binance integration
│   │   ├── metals_service.py     # Precious metals
│   │   ├── forex_service.py      # Currency exchange
│   │   └── cache_service.py      # Response caching
│   │
│   ├── utils/
│   │   └── calculations.py   # Inflation calculations
│   │
│   ├── static/
│   │   ├── css/style.css     # Dark theme styles
│   │   └── js/dashboard.js   # Frontend logic
│   │
│   └── templates/
│       ├── base.html         # Base template
│       ├── index.html        # Dashboard page
│       └── compare.html      # Comparison page
│
└── venv/                     # Virtual environment
```

## 🔌 API Endpoints

### Inflation
| Endpoint | Description |
|----------|-------------|
| `GET /api/inflation` | Historical CPI data |
| `GET /api/inflation/rates` | Year-over-year inflation rates |
| `GET /api/inflation/purchasing-power` | Purchasing power over time |
| `GET /api/inflation/adjust` | Inflation calculator |

### Crypto
| Endpoint | Description |
|----------|-------------|
| `GET /api/crypto/<symbol>` | Current price (e.g., `/api/crypto/bitcoin`) |
| `GET /api/crypto/<symbol>/history` | Historical prices |

### Metals
| Endpoint | Description |
|----------|-------------|
| `GET /api/metals/<metal>` | Current price (gold, silver) |
| `GET /api/metals/<metal>/history` | Historical prices |

### Forex
| Endpoint | Description |
|----------|-------------|
| `GET /api/forex/<from>/<to>` | Exchange rate |
| `GET /api/forex/convert` | Currency conversion |

### Comparison
| Endpoint | Description |
|----------|-------------|
| `POST /api/compare` | Compare multiple assets |
| `GET /api/dashboard` | All dashboard data |
| `GET /api/assets` | List available assets |

## 📊 Data Sources

- **Inflation/CPI**: Bureau of Labor Statistics via FRED API (1913-present)
- **Bitcoin**: Binance API (2017-present) + embedded historical (2009-2016)
- **Gold**: Embedded historical data (1913-present)
- **Silver**: Embedded historical data (1970-present)
- **Forex**: Alpha Vantage API + embedded historical data

## 🛠 Development

### Running in Development Mode

```bash
source venv/bin/activate
FLASK_DEBUG=True python run.py
```

### Installing New Dependencies

```bash
pip install <package-name>
pip freeze > requirements.txt
```

## 📝 License

This project is for educational purposes. API usage is subject to the terms of each provider.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Add more asset data
- Improve the UI

---

**Built with ❤️ using Flask & Plotly.js**
