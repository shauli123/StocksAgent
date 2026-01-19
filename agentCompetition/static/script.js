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
    // Manual trigger (optional, since background thread is running)
    try {
        const response = await fetch('/api/trade');
        const result = await response.json();
        alert(`Manual Trade Cycle Complete! Executed ${result.trades_executed} trades.`);
        fetchStats();
    } catch (error) {
        console.error('Error triggering trade:', error);
    }
}

function updateLeaderboard(agents) {
    const tbody = document.querySelector('#leaderboard-table tbody');
    tbody.innerHTML = '';

    // Convert to array and sort by portfolio value
    const sortedAgents = Object.entries(agents).sort((a, b) => b[1].portfolio_value - a[1].portfolio_value);

    sortedAgents.forEach(([name, agent], index) => {
        const initial = 10000;
        const returnPct = ((agent.portfolio_value - initial) / initial) * 100;
        const revenue = agent.revenue || 0;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>#${index + 1}</td>
            <td>
                <span style="color: ${agent.color}; font-weight: bold;">${name}</span>
                <br><small style="color: #aaa;">${agent.description}</small>
            </td>
            <td>$${agent.portfolio_value.toFixed(2)}</td>
            <td style="color: ${returnPct >= 0 ? '#2ecc71' : '#e74c3c'}">
                ${returnPct >= 0 ? '+' : ''}${returnPct.toFixed(2)}%
            </td>
            <td style="color: ${revenue >= 0 ? '#2ecc71' : '#e74c3c'}">
                $${revenue.toFixed(2)}
            </td>
            <td>$${agent.cash.toFixed(2)}</td>
        `;
        tbody.appendChild(tr);
    });
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
// Poll every 5 seconds for UI updates
setInterval(fetchStats, 5000);

// Client-side Auto-Trader (Pings /api/trade every 10 seconds while tab is open)
// This bypasses Vercel's Hobby cron limits for the active user.
setInterval(async () => {
    try {
        await fetch('/api/trade');
        console.log("Background trade cycle triggered by client.");
    } catch (e) {
        console.error("Client-side trade trigger failed:", e);
    }
}, 10000);
