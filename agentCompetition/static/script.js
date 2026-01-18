let chart;

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        updateLeaderboard(data.agents);
        updateChart(data.history, data.agents);
        updateTrades(data.trades);
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function triggerTrade() {
    const btn = document.getElementById('trade-btn');
    btn.disabled = true;
    btn.innerText = 'Trading...';

    try {
        const response = await fetch('/api/trade');
        const result = await response.json();
        alert(`Trade Cycle Complete! Executed ${result.trades_executed} trades.`);
        fetchStats();
    } catch (error) {
        console.error('Error triggering trade:', error);
        alert('Error triggering trade');
    } finally {
        btn.disabled = false;
        btn.innerText = 'Trigger Trade Cycle';
    }
}
function updateChart(history, agents) {
    const ctx = document.getElementById('portfolioChart').getContext('2d');

    // Extract labels (dates) from the first agent that has history
    const firstAgent = Object.keys(history)[0];
    if (!firstAgent) return;

    const labels = history[firstAgent].map(h => new Date(h.date).toLocaleDateString());

    const datasets = Object.entries(history).map(([name, data]) => {
        return {
            label: name,
            data: data.map(h => h.value),
            borderColor: agents[name].color,
            backgroundColor: 'transparent',
            borderWidth: 2,
            tension: 0.4
        };
    });

    if (chart) {
        chart.data.labels = labels;
        chart.data.datasets = datasets;
        chart.update();
    } else {
        chart = new Chart(ctx, {
            type: 'line',
            data: { labels, datasets },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#fff' } }
                },
                scales: {
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#aaa' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#aaa' }
                    }
                }
            }
        });
    }
}

function updateTrades(trades) {
    const list = document.getElementById('trades-list');
    list.innerHTML = '';

    // Show last 20 trades
    trades.slice().reverse().slice(0, 20).forEach(trade => {
        const div = document.createElement('div');
        div.className = 'trade-item';
        div.innerHTML = `
            <span>
                <span style="font-weight: bold;">${trade.agent}</span>: 
                <span class="${trade.action === 'BUY' ? 'trade-buy' : 'trade-sell'}">${trade.action}</span> 
                ${trade.shares} ${trade.symbol} @ $${trade.price.toFixed(2)}
            </span>
            <small style="color: #aaa;">${new Date(trade.date).toLocaleTimeString()}</small>
        `;
        list.appendChild(div);
    });
}

// Initial Load
fetchStats();
// Poll every 5 seconds
setInterval(fetchStats, 5000);
