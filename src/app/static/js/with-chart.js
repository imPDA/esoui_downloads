let chart;

const colors = [
    '#4e80fe', '#22c55e', '#f43f5e', '#f59e0b', '#8b5cf6',
    '#ec4899', '#06b6d4', '#84cc16', '#ef4444', '#14b8a6',
    '#a855f7', '#f97316', '#10b981', '#6366f1', '#64748b'
];

const chartConfig = {
    type: 'scatter',
    data: { datasets: [] },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'nearest',
            intersect: false,
            axis: 'x'
        },
        plugins: {
            legend: {
                position: 'right',
                labels: {
                    boxWidth: 30,
                    usePointStyle: true,
                    font: { size: 12 },
                    color: '#e0e0e0'
                }
            },
            tooltip: {
                mode: 'nearest',
                intersect: false,
                callbacks: {
                    title: function(context) {
                        const date = new Date(context[0].raw.x);
                        return formatDateTime(date);
                    },
                    label: function(context) {
                        const label = context.dataset.label || '';
                        const value = context.raw.y;
                        return `${label}: ${value.toLocaleString()}`;
                    }
                }
            },
            zoom: {
                pan: {
                    enabled: true,
                    mode: 'xy',
                    modifierKey: null
                },
                zoom: {
                    wheel: { enabled: true },
                    pinch: { enabled: true },
                    mode: 'xy',
                    drag: { enabled: false }
                }
            }
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    parser: 'yyyy-MM-dd\'T\'HH:mm:ss',
                    tooltipFormat: 'MMM dd, yyyy HH:mm',
                    displayFormats: {
                        millisecond: 'HH:mm:ss',
                        second: 'HH:mm:ss',
                        minute: 'MMM dd HH:mm',
                        hour: 'MMM dd HH:mm',
                        day: 'MMM dd',
                        week: 'MMM dd',
                        month: 'MMM yyyy',
                        quarter: 'MMM yyyy',
                        year: 'yyyy'
                    }
                },
                title: { display: true, text: 'Time' },
                grid: { color: '#4a4e56' },
                ticks: { color: '#e0e0e0' }
            },
            y: {
                title: { display: true, text: 'Downloads' },
                grid: { color: '#4a4e56' },
                min: 0,
                ticks: {
                    color: '#e0e0e0',
                    callback: function(value) {
                        if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M';
                        if (value >= 1000) return (value / 1000).toFixed(1) + 'K';
                        return value;
                    }
                }
            }
        }
    }
};

const darkTheme = {
    color: '#e0e0e0',
    gridColor: '#4a4e56',
    bgColor: '#3a3e46'
};

const lightTheme = {
    color: '#34415b',
    gridColor: '#e0e6ed',
    bgColor: '#ffffff'
};

function updateChart(chartData) {
    const datasets = chartData.map((item, index) => {
        return {
            label: item.name,
            data: item.x.map((timestamp, i) => ({
                x: timestamp,
                y: item.y[i]
            })),
            borderColor: colors[index % colors.length],
            backgroundColor: colors[index % colors.length],
            pointBackgroundColor: colors[index % colors.length],
            pointBorderColor: colors[index % colors.length],
            pointRadius: 1,
            pointHoverRadius: 3,
            pointBorderWidth: 0.5,
            showLine: true,
            lineTension: 0.4,
            borderWidth: 1.5,
            fill: false,
            hidden: index >= 8
        };
    });

    if (chart) {
        chart.data.datasets = datasets;
        chart.update();
    } else {
        const canvas = document.getElementById('download-chart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        chartConfig.data.datasets = datasets;
        chart = new Chart(ctx, chartConfig);
    }

    const themeToggle = document.getElementById('theme-toggle');
    const currentTheme = themeToggle?.checked ? 'light' : 'dark';
    applyTheme(currentTheme);
}

function applyTheme(theme) {
    if (!chart) return;
    const isDark = theme === 'dark';
    const themeConfig = isDark ? darkTheme : lightTheme;
    
    chart.options.scales.x.grid.color = themeConfig.gridColor;
    chart.options.scales.x.ticks.color = themeConfig.color;
    chart.options.scales.y.grid.color = themeConfig.gridColor;
    chart.options.scales.y.ticks.color = themeConfig.color;
    chart.options.plugins.legend.labels.color = themeConfig.color;
    
    chart.options.plugins.tooltip.backgroundColor = isDark ? '#2a2e36' : '#ffffff';
    chart.options.plugins.tooltip.titleColor = themeConfig.color;
    chart.options.plugins.tooltip.bodyColor = themeConfig.color;
    chart.options.plugins.tooltip.borderColor = themeConfig.gridColor;
    
    chart.update();
}

function formatDateTime(date) {
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}

document.addEventListener('DOMContentLoaded', (event) => {
    const canvas = document.getElementById('download-chart');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        chart = new Chart(ctx, {
            type: 'scatter',
            data: { datasets: [] },
            options: chartConfig.options
        });
    }
    
    const themeToggle = document.getElementById('theme-toggle');
    const themeText = document.querySelector('.theme-text');

    if (themeToggle && themeText) {
        themeToggle.addEventListener('change', function() {
            if (this.checked) {
                document.body.classList.add('light-theme');
                themeText.textContent = 'Light Mode';
                applyTheme('light');
            } else {
                document.body.classList.remove('light-theme');
                themeText.textContent = 'Dark Mode';
                applyTheme('dark');
            }
        });
    }

    if (themeToggle) {
        const initialTheme = themeToggle.checked ? 'light' : 'dark';
        applyTheme(initialTheme);
    }
    
    if (typeof data !== 'undefined') {
        updateChart(data);
    }
});