/**
 * Inflation Tracker Dashboard
 * Main JavaScript for chart rendering and data fetching
 */

// API base URL
const API_BASE = '/api';

// Color palette for charts
const COLORS = {
    bitcoin: '#f7931a',
    monero: '#ff6600',
    gold: '#ffd700',
    inflation: '#ef4444',
    cpi: '#6366f1',
    purchasingPower: '#10b981',
    gridLines: 'rgba(255, 255, 255, 0.06)',
    text: '#94a3b8',
    background: '#1a1a25'
};

// Chart configuration
const chartConfig = {
    responsive: true,
    displayModeBar: 'hover',  // Only show toolbar when hovering over chart
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
    displaylogo: false,
    scrollZoom: false  // Disabled - allows normal page scrolling
};

const chartLayout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: {
        family: 'Inter, sans-serif',
        color: COLORS.text
    },
    margin: { t: 40, r: 20, b: 60, l: 60 },
    xaxis: {
        gridcolor: COLORS.gridLines,
        linecolor: COLORS.gridLines,
        tickfont: { size: 11 }
    },
    yaxis: {
        gridcolor: COLORS.gridLines,
        linecolor: COLORS.gridLines,
        tickfont: { size: 11 }
    },
    hovermode: 'x unified',
    legend: {
        orientation: 'h',
        yanchor: 'bottom',
        y: 1.02,
        xanchor: 'right',
        x: 1,
        font: { size: 11 }
    }
};

// Utility functions
function formatCurrency(value, decimals = 2) {
    if (value === null || value === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

function formatPercent(value, decimals = 2) {
    if (value === null || value === undefined) return 'N/A';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(decimals)}%`;
}

function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        return null;
    }
}

async function postAPI(endpoint, data) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        return null;
    }
}

// Dashboard data loading
async function loadDashboardData() {
    showLoading('dashboard');

    const data = await fetchAPI('/dashboard');

    if (data) {
        updatePriceTickers(data.current_prices);
        updateInflationStats(data.inflation);
        renderInflationChart(data.historical_data);
        renderPurchasingPowerChart(data.historical_data.purchasing_power);
    }

    hideLoading('dashboard');
}

function updatePriceTickers(prices) {
    // Bitcoin
    if (prices.bitcoin?.price) {
        const btcEl = document.getElementById('btc-price');
        if (btcEl) btcEl.textContent = formatCurrency(prices.bitcoin.price, 0);
    }

    // Monero
    if (prices.monero?.price) {
        const xmrEl = document.getElementById('xmr-price');
        if (xmrEl) xmrEl.textContent = formatCurrency(prices.monero.price, 0);
    }

    // Gold
    if (prices.gold?.price) {
        const goldEl = document.getElementById('gold-price');
        if (goldEl) goldEl.textContent = formatCurrency(prices.gold.price, 0);
    }
}

function updateInflationStats(inflation) {
    // Current inflation rate
    const currentRateEl = document.getElementById('current-inflation');
    if (currentRateEl && inflation.current_rate !== null) {
        currentRateEl.textContent = formatPercent(inflation.current_rate);
        currentRateEl.className = inflation.current_rate > 0 ? 'stat-value negative' : 'stat-value positive';
    }

    // Total inflation since 1913
    const totalEl = document.getElementById('total-inflation');
    if (totalEl && inflation.total_since_1913 !== null) {
        totalEl.textContent = formatPercent(inflation.total_since_1913);
    }

    // Purchasing power of $1
    const ppEl = document.getElementById('purchasing-power-value');
    if (ppEl && inflation.purchasing_power_of_1913_dollar !== null) {
        ppEl.textContent = formatCurrency(inflation.purchasing_power_of_1913_dollar / 100, 2);
    }

    // Latest CPI
    const cpiEl = document.getElementById('latest-cpi');
    if (cpiEl && inflation.latest_cpi !== null) {
        cpiEl.textContent = formatNumber(inflation.latest_cpi, 1);
    }
}

function renderInflationChart(data) {
    const container = document.getElementById('inflation-chart');
    if (!container || !data.inflation_rates) return;

    // Store data for tab filtering
    inflationRatesData = data.inflation_rates;

    const trace = {
        x: data.inflation_rates.dates,
        y: data.inflation_rates.rates,
        type: 'scatter',
        mode: 'lines',
        name: 'Inflation Rate',
        line: {
            color: COLORS.inflation,
            width: 2
        },
        fill: 'tozeroy',
        fillcolor: 'rgba(239, 68, 68, 0.1)'
    };

    const layout = {
        ...chartLayout,
        title: {
            text: 'US Annual Inflation Rate (1914-Present)',
            font: { size: 14, color: '#f8fafc' }
        },
        yaxis: {
            ...chartLayout.yaxis,
            title: 'Inflation Rate (%)',
            ticksuffix: '%'
        },
        xaxis: {
            ...chartLayout.xaxis,
            title: 'Year'
        }
    };

    Plotly.newPlot(container, [trace], layout, chartConfig);
}

// Store reference to full inflation data for filtering
let inflationRatesData = null;

function renderInflationChartFiltered(years) {
    const container = document.getElementById('inflation-chart');
    if (!container || !inflationRatesData) return;

    let dates = inflationRatesData.dates;
    let rates = inflationRatesData.rates;

    // Filter by years if specified
    if (years) {
        const currentYear = new Date().getFullYear();
        const cutoffYear = currentYear - years;
        const filteredDates = [];
        const filteredRates = [];

        for (let i = 0; i < dates.length; i++) {
            const year = parseInt(dates[i].split('-')[0]);
            if (year >= cutoffYear) {
                filteredDates.push(dates[i]);
                filteredRates.push(rates[i]);
            }
        }
        dates = filteredDates;
        rates = filteredRates;
    }

    const trace = {
        x: dates,
        y: rates,
        type: 'scatter',
        mode: 'lines',
        name: 'Inflation Rate',
        line: {
            color: COLORS.inflation,
            width: 2
        },
        fill: 'tozeroy',
        fillcolor: 'rgba(239, 68, 68, 0.1)'
    };

    const titleText = years
        ? `US Annual Inflation Rate (Last ${years} Years)`
        : 'US Annual Inflation Rate (1914-Present)';

    const layout = {
        ...chartLayout,
        title: {
            text: titleText,
            font: { size: 14, color: '#f8fafc' }
        },
        yaxis: {
            ...chartLayout.yaxis,
            title: 'Inflation Rate (%)',
            ticksuffix: '%'
        },
        xaxis: {
            ...chartLayout.xaxis,
            title: 'Year'
        }
    };

    Plotly.newPlot(container, [trace], layout, chartConfig);
}

function renderPurchasingPowerChart(data) {
    const container = document.getElementById('purchasing-power-chart');
    if (!container || !data) return;

    const trace = {
        x: data.dates,
        y: data.values,
        type: 'scatter',
        mode: 'lines',
        name: 'Purchasing Power of $100',
        line: {
            color: COLORS.purchasingPower,
            width: 2
        },
        fill: 'tozeroy',
        fillcolor: 'rgba(16, 185, 129, 0.1)'
    };

    const layout = {
        ...chartLayout,
        title: {
            text: 'Purchasing Power of $100 (1913 Dollars)',
            font: { size: 14, color: '#f8fafc' }
        },
        yaxis: {
            ...chartLayout.yaxis,
            title: 'Value in 1913 Dollars',
            tickprefix: '$'
        },
        xaxis: {
            ...chartLayout.xaxis,
            title: 'Year'
        }
    };

    Plotly.newPlot(container, [trace], layout, chartConfig);
}

// Asset comparison functions
let selectedAssets = [];

function toggleAsset(type, symbol, name) {
    const key = `${type}:${symbol}`;
    const index = selectedAssets.findIndex(a => `${a.type}:${a.symbol}` === key);

    if (index > -1) {
        selectedAssets.splice(index, 1);
    } else {
        if (selectedAssets.length >= 5) {
            alert('Maximum 5 assets can be compared at once');
            return;
        }
        selectedAssets.push({ type, symbol, name });
    }

    updateAssetChips();
    if (selectedAssets.length > 0) {
        loadComparisonChart();
    }
}

function updateAssetChips() {
    document.querySelectorAll('.asset-chip').forEach(chip => {
        const type = chip.dataset.type;
        const symbol = chip.dataset.symbol;
        const key = `${type}:${symbol}`;
        const isSelected = selectedAssets.some(a => `${a.type}:${a.symbol}` === key);
        chip.classList.toggle('selected', isSelected);
    });
}

async function loadComparisonChart() {
    const container = document.getElementById('comparison-chart');
    if (!container) return;

    showLoading('comparison');

    const baseYear = parseInt(document.getElementById('base-year')?.value || '2010');

    const data = await postAPI('/compare', {
        assets: selectedAssets,
        base_year: baseYear,
        normalize: true
    });

    if (data?.assets?.length > 0) {
        renderComparisonChart(data.assets, baseYear);
        updateComparisonTable(data.assets);
    }

    hideLoading('comparison');
}

function renderComparisonChart(assets, baseYear) {
    const container = document.getElementById('comparison-chart');
    if (!container) return;

    const colorMap = {
        'crypto:bitcoin': COLORS.bitcoin,
        'crypto:ethereum': COLORS.ethereum,
        'crypto:monero': '#ff6600',
        'metal:gold': COLORS.gold,
        'metal:silver': COLORS.silver,
        'inflation:cpi': COLORS.cpi,
        'inflation:cumulative': COLORS.inflation,
        'inflation:purchasing_power': COLORS.purchasingPower
    };

    const traces = assets.map((asset, i) => {
        const key = `${asset.type}:${asset.name.toLowerCase().split(' ')[0]}`;
        const color = colorMap[key] || getDefaultColor(i);

        return {
            x: asset.dates,
            y: asset.normalized_values || asset.values,  // Use normalized index
            type: 'scatter',
            mode: 'lines',
            name: asset.name,
            line: {
                color: color,
                width: 2
            }
        };
    });

    const layout = {
        ...chartLayout,
        title: {
            text: `Asset Comparison (Index)`,
            font: { size: 14, color: '#f8fafc' }
        },
        yaxis: {
            ...chartLayout.yaxis,
            title: 'Index (Base = 100)',
            type: 'log'  // Log scale for better comparison
        },
        xaxis: {
            ...chartLayout.xaxis,
            title: 'Year'
        }
    };

    Plotly.newPlot(container, traces, layout, chartConfig);
}

function updateComparisonTable(assets) {
    const tbody = document.getElementById('comparison-tbody');
    if (!tbody) return;

    tbody.innerHTML = assets.map(asset => {
        // Calculate actual years from first to last date
        let yearsRange = 'N/A';
        if (asset.dates && asset.dates.length >= 2) {
            const firstYear = parseInt(asset.dates[0].split('-')[0]);
            const lastYear = parseInt(asset.dates[asset.dates.length - 1].split('-')[0]);
            yearsRange = `${firstYear}-${lastYear} (${lastYear - firstYear} yrs)`;
        }

        return `
        <tr>
            <td><strong>${asset.name}</strong></td>
            <td>${asset.source || 'N/A'}</td>
            <td class="${asset.total_return >= 0 ? 'positive' : 'negative'}">
                ${formatPercent(asset.total_return)}
            </td>
            <td>${formatPercent(asset.cagr)}</td>
            <td>${yearsRange}</td>
        </tr>
    `}).join('');
}

function getDefaultColor(index) {
    const colors = ['#6366f1', '#8b5cf6', '#a855f7', '#ec4899', '#14b8a6'];
    return colors[index % colors.length];
}

// Loading states
function showLoading(section) {
    const el = document.getElementById(`${section}-loading`);
    if (el) el.classList.remove('hidden');
}

function hideLoading(section) {
    const el = document.getElementById(`${section}-loading`);
    if (el) el.classList.add('hidden');
}

// Inflation calculator
async function calculateInflation() {
    const amount = parseFloat(document.getElementById('calc-amount')?.value || 100);
    const fromYear = parseInt(document.getElementById('calc-from-year')?.value || 1913);
    const toYear = parseInt(document.getElementById('calc-to-year')?.value || 2024);

    const data = await fetchAPI(`/inflation/adjust?amount=${amount}&from_year=${fromYear}&to_year=${toYear}`);

    if (data && !data.error) {
        const resultEl = document.getElementById('calc-result');
        if (resultEl) {
            // Calculate purchasing power (what old money is worth now)
            // If $100 in 1913 = $3000 equivalent today, then purchasing power = 100/3000 * 100 = $3.33
            const purchasingPower = (amount / data.adjusted_amount) * amount;

            resultEl.innerHTML = `
                <div class="grid grid-2 gap-md">
                    <div class="card stat-card animate-fade-in">
                        <div class="stat-value negative">${formatCurrency(purchasingPower)}</div>
                        <div class="stat-label">Purchasing Power Today</div>
                        <div class="stat-hint">
                            ${formatCurrency(amount)} from ${fromYear} only buys what ${formatCurrency(purchasingPower)} buys in ${toYear}
                        </div>
                    </div>
                    <div class="card stat-card animate-fade-in">
                        <div class="stat-value">${formatCurrency(data.adjusted_amount)}</div>
                        <div class="stat-label">Equivalent Amount Today</div>
                        <div class="stat-hint">
                            You'd need ${formatCurrency(data.adjusted_amount)} in ${toYear} to match ${formatCurrency(amount)} in ${fromYear}
                        </div>
                    </div>
                </div>
                <div class="text-muted mt-sm text-center" style="font-size: 0.8rem;">
                    📉 Total inflation: ${formatPercent(data.cumulative_inflation_percent)} over ${toYear - fromYear} years
                </div>
            `;
        }
    }
}

// Load individual asset charts
async function loadBitcoinChart() {
    const container = document.getElementById('btc-chart');
    if (!container) return;

    const data = await fetchAPI('/crypto/bitcoin/history?all=true');

    if (data?.dates?.length > 0) {
        const trace = {
            x: data.dates,
            y: data.prices,
            type: 'scatter',
            mode: 'lines',
            name: 'Bitcoin',
            line: {
                color: COLORS.bitcoin,
                width: 2
            },
            fill: 'tozeroy',
            fillcolor: 'rgba(247, 147, 26, 0.1)'
        };

        const layout = {
            ...chartLayout,
            title: {
                text: 'Bitcoin Price History (USD)',
                font: { size: 14, color: '#f8fafc' }
            },
            yaxis: {
                ...chartLayout.yaxis,
                title: 'Price (USD)',
                tickprefix: '$',
                type: 'log'
            }
        };

        Plotly.newPlot(container, [trace], layout, chartConfig);
    }
}

async function loadGoldChart() {
    const container = document.getElementById('gold-chart');
    if (!container) return;

    const data = await fetchAPI('/metals/gold/history');

    if (data?.dates?.length > 0) {
        const trace = {
            x: data.dates,
            y: data.prices,
            type: 'scatter',
            mode: 'lines',
            name: 'Gold',
            line: {
                color: COLORS.gold,
                width: 2
            },
            fill: 'tozeroy',
            fillcolor: 'rgba(255, 215, 0, 0.1)'
        };

        const layout = {
            ...chartLayout,
            title: {
                text: 'Gold Price History (USD/oz)',
                font: { size: 14, color: '#f8fafc' }
            },
            yaxis: {
                ...chartLayout.yaxis,
                title: 'Price (USD/oz)',
                tickprefix: '$'
            }
        };

        Plotly.newPlot(container, [trace], layout, chartConfig);
    }
}

async function loadMoneroChart() {
    const container = document.getElementById('xmr-chart');
    if (!container) return;

    const data = await fetchAPI('/crypto/monero/history?all=true');

    if (data?.dates?.length > 0) {
        const trace = {
            x: data.dates,
            y: data.prices,
            type: 'scatter',
            mode: 'lines',
            name: 'Monero',
            line: {
                color: COLORS.monero,
                width: 2
            },
            fill: 'tozeroy',
            fillcolor: 'rgba(255, 102, 0, 0.1)'
        };

        const layout = {
            ...chartLayout,
            title: {
                text: 'Monero Price History (USD)',
                font: { size: 14, color: '#f8fafc' }
            },
            yaxis: {
                ...chartLayout.yaxis,
                title: 'Price (USD)',
                tickprefix: '$'
            }
        };

        Plotly.newPlot(container, [trace], layout, chartConfig);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check which page we're on
    const path = window.location.pathname;

    if (path === '/' || path === '/index.html' || path === '') {
        loadDashboardData();
        loadBitcoinChart();
        loadMoneroChart();
        loadGoldChart();

        // Set up inflation chart tab buttons
        const tabs = document.querySelectorAll('.card-header .tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                // Remove active from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                // Add active to clicked tab
                e.target.classList.add('active');

                // Filter data based on tab
                const text = e.target.textContent.trim();
                let years = null;
                if (text === 'Last 50 Years') years = 50;
                else if (text === 'Last 20 Years') years = 20;

                // Re-render inflation chart with filter
                renderInflationChartFiltered(years);
            });
        });
    }

    if (path === '/compare') {
        // Default selected assets
        selectedAssets = [
            { type: 'crypto', symbol: 'bitcoin', name: 'Bitcoin' },
            { type: 'metal', symbol: 'gold', name: 'Gold' },
            { type: 'inflation', symbol: 'cumulative', name: 'Cumulative Inflation' }
        ];
        updateAssetChips();
        loadComparisonChart();
    }

    // Auto-refresh prices every 60 seconds
    setInterval(() => {
        if (path === '/' || path === '/index.html' || path === '') {
            loadDashboardData();
        }
    }, 60000);
});

// Export functions for use in HTML
window.toggleAsset = toggleAsset;
window.loadComparisonChart = loadComparisonChart;
window.calculateInflation = calculateInflation;
window.calculateAssetGrowth = calculateAssetGrowth;

// Calculate asset investment growth
async function calculateAssetGrowth() {
    const amount = parseFloat(document.getElementById('asset-amount')?.value || 100);
    const asset = document.getElementById('asset-type')?.value || 'bitcoin';
    const fromYear = parseInt(document.getElementById('asset-from-year')?.value || 2015);
    const toYear = 2024;  // Use latest CPI year (FRED releases data with ~1 year lag)

    // Get asset data
    let assetData;
    if (asset === 'bitcoin' || asset === 'monero') {
        assetData = await fetchAPI(`/crypto/${asset}/history?all=true`);
    } else if (asset === 'gold') {
        assetData = await fetchAPI(`/metals/${asset}/history`);
    }

    // Get inflation data
    const inflationData = await fetchAPI(`/inflation/adjust?amount=${amount}&from_year=${fromYear}&to_year=${toYear}`);

    if (!assetData?.dates?.length) {
        document.getElementById('asset-calc-result').innerHTML = `
            <div class="card stat-card"><div class="stat-label">No data available for ${asset}</div></div>
        `;
        return;
    }

    // Find prices for from year and latest
    const fromYearStr = String(fromYear);
    let startPrice = null, startDate = null;
    let endPrice = null, endDate = null;

    for (let i = 0; i < assetData.dates.length; i++) {
        if (assetData.dates[i].startsWith(fromYearStr) && startPrice === null) {
            startPrice = assetData.prices[i];
            startDate = assetData.dates[i];
        }
        endPrice = assetData.prices[i];
        endDate = assetData.dates[i];
    }

    if (!startPrice) {
        document.getElementById('asset-calc-result').innerHTML = `
            <div class="card stat-card"><div class="stat-label">No ${asset} data for ${fromYear}. Try a later year.</div></div>
        `;
        return;
    }

    // Calculate growth
    const assetValue = (amount / startPrice) * endPrice;
    // Cash purchasing power: $100 from 2015, if equivalent today is $130, then PP = 100*100/130 = $76.92
    const cashValue = inflationData?.adjusted_amount ? (amount * amount) / inflationData.adjusted_amount : amount;
    const assetGain = ((assetValue - amount) / amount) * 100;

    // Render result
    const resultEl = document.getElementById('asset-calc-result');
    const assetNames = { bitcoin: 'Bitcoin', monero: 'Monero', gold: 'Gold' };

    resultEl.innerHTML = `
        <div class="grid grid-3 gap-md">
            <div class="card stat-card animate-fade-in">
                <div class="stat-value ${assetGain >= 0 ? 'positive' : 'negative'}">${formatCurrency(assetValue)}</div>
                <div class="stat-label">${assetNames[asset]} Value Today</div>
                <div class="stat-hint">${formatCurrency(amount)} invested in ${fromYear}</div>
            </div>
            <div class="card stat-card animate-fade-in">
                <div class="stat-value negative">${formatCurrency(cashValue)}</div>
                <div class="stat-label">Cash Value Today</div>
                <div class="stat-hint">If kept as cash (inflation adjusted)</div>
            </div>
            <div class="card stat-card animate-fade-in">
                <div class="stat-value ${assetGain >= 0 ? 'positive' : 'negative'}">${formatPercent(assetGain)}</div>
                <div class="stat-label">Total Return</div>
                <div class="stat-hint">${assetNames[asset]} growth since ${fromYear}</div>
            </div>
        </div>
    `;

    // Render comparison chart
    const chartEl = document.getElementById('asset-calc-chart');
    chartEl.style.display = 'block';

    // Get CPI data for accurate inflation calculation
    const cpiData = await fetchAPI('/inflation');
    const cpiByYear = {};
    if (cpiData?.dates) {
        for (let i = 0; i < cpiData.dates.length; i++) {
            const year = parseInt(cpiData.dates[i].split('-')[0]);
            cpiByYear[year] = cpiData.values[i];
        }
    }
    const startCpi = cpiByYear[fromYear] || 100;

    // Build chart data from start year to now
    const chartDates = [];
    const assetValues = [];
    const cashValues = [];

    for (let i = 0; i < assetData.dates.length; i++) {
        if (assetData.dates[i] >= startDate) {
            const currentYear = parseInt(assetData.dates[i].split('-')[0]);
            // Only include data up to 2024 (latest CPI year)
            if (currentYear > 2024) continue;

            chartDates.push(assetData.dates[i]);
            assetValues.push((amount / startPrice) * assetData.prices[i]);

            // Use actual CPI data for cash purchasing power
            const currentCpi = cpiByYear[currentYear] || cpiByYear[2024] || startCpi;
            const inflationFactor = currentCpi / startCpi;
            cashValues.push(amount / inflationFactor);
        }
    }

    const traces = [
        {
            x: chartDates,
            y: assetValues,
            type: 'scatter',
            mode: 'lines',
            name: assetNames[asset],
            line: { color: asset === 'bitcoin' ? COLORS.bitcoin : asset === 'gold' ? COLORS.gold : '#ff6600', width: 2 }
        },
        {
            x: chartDates,
            y: cashValues,
            type: 'scatter',
            mode: 'lines',
            name: 'Cash (inflation adjusted)',
            line: { color: '#888', width: 2, dash: 'dot' }
        }
    ];

    const layout = {
        ...chartLayout,
        title: { text: `${formatCurrency(amount)} Investment: ${assetNames[asset]} vs Cash`, font: { size: 14, color: '#f8fafc' } },
        yaxis: { ...chartLayout.yaxis, title: 'Value ($)', tickprefix: '$' },
        showlegend: true,
        legend: { orientation: 'h', y: -0.15 }
    };

    Plotly.newPlot(chartEl, traces, layout, chartConfig);
}
