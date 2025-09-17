let showlegend = true;

let versionShapes = [];
let versionAnnotations = [];

const darkLayout = {
    plot_bgcolor: '#3a3e46',
    paper_bgcolor: '#3a3e46',
    font: { color: '#e0e0e0' },
    
    hovermode: 'x unified',

    xaxis: {
        gridcolor: '#4a4e56',
        linecolor: '#4a4e56',
        zerolinecolor: '#4a4e56',
        title: 'Time',
    },
    yaxis: {
        gridcolor: '#4a4e56',
        linecolor: '#4a4e56',
        zerolinecolor: '#4a4e56',
        title: 'Downloads',
        hoverformat: '.3s',
    },
    // legend: {
    //     x: 0,
    //     y: 1.1,
    //     orientation: 'h',
    //     bgcolor: 'rgba(0,0,0,0)',
    //     font: { size: 14 },
    // }
    legend: {
        orientation: 'v',
        y: 0.5,
        yanchor: 'middle',
        font: {
            size: 12
        },
        itemwidth: 30,
        itemsizing: 'constant',
        tracegroupgap: 5
    }
};

const lightLayout = {
    plot_bgcolor: '#ffffff',
    paper_bgcolor: '#ffffff',
    font: { color: '#34415b' },
    xaxis: {
        gridcolor: '#e0e6ed',
        linecolor: '#e0e6ed',
        zerolinecolor: '#e0e6ed',
        title: 'Time',
    },
    yaxis: {
        gridcolor: '#e0e6ed',
        linecolor: '#e0e6ed',
        zerolinecolor: '#e0e6ed',
        title: 'Downloads',
        hoverformat: '.3s',
    },
    hovermode: 'x unified',
    // legend: {
    //     x: 0,
    //     y: 1.1,
    //     orientation: 'h',
    //     bgcolor: 'rgba(0,0,0,0)',
    //     font: { size: 14 },
    // }
    legend: {
        orientation: 'v',
        y: 0.5,
        yanchor: 'middle',
        font: {
            size: 12
        },
        itemwidth: 30,
        itemsizing: 'constant',
        tracegroupgap: 5
    }
};

const colors = [
    '#4e80fe', // blue
    '#22c55e', // green
    '#f43f5e', // rose
    '#f59e0b', // amber
    '#8b5cf6', // violet
    '#ec4899', // pink
    '#06b6d4', // cyan
    '#84cc16', // lime
    '#ef4444', // red
    '#14b8a6', // teal
    '#a855f7', // purple
    '#f97316', // orange
    '#10b981', // emerald
    '#6366f1', // indigo
    '#64748b', // slate
];

function updateChart(data) {
    data.forEach((item, index) => {
        item.type = 'scattergl';
        item.mode = 'lines';
        item.line = { 
            color: colors[index % colors.length],
            width: 2,
        };
        item.visible = index < 8 ? true : 'legendonly';
    });

    Plotly.newPlot('download-chart', data,
    { 
        ...currentLayout,
        shapes: versionShapes,
        annotations: versionAnnotations,
    },
    {
        responsive: true,
        scrollZoom: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtons: [
            ['zoom2d', 'pan2d', 'resetScale2d'],
        ]
    })
}

document.addEventListener('DOMContentLoaded', (event) => {
    Plotly.newPlot('download-chart', [], { ...darkLayout }, 
    {
        responsive: true,
        scrollZoom: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtons: [
            ['zoom2d', 'pan2d', 'resetScale2d'],
        ]
    });

    // document.getElementById('download-chart').on('plotly_hover', function(data) {
    //     console.log('Plotly hover');

    //     const allPoints = data.points;
        
    //     const hoverData = allPoints.map(point => ({
    //         label: point.x,
    //         value: point.y,
    //         trace: point.data.name || `Trace ${point.curveNumber}`
    //     })).sort((a, b) => b.value - a.value);
        
    //     const sortedText = hoverData.map(item => 
    //         `<b>${item.trace}</b> - ${item.label}: ${item.value}`
    //     ).join('<br>');
        
    //     const annotations = hoverData.map((item, i) => ({
    //         x: item.x,
    //         y: item.y,
    //         text: sortedText,
    //         showarrow: false,
    //         xref: 'paper',
    //         yref: 'paper',
    //         xanchor: 'left',
    //         yanchor: 'bottom'
    //     }));
        
    //     Plotly.relayout('download-chart', {annotations});
    // });

    const themeToggle = document.getElementById('theme-toggle');

    themeToggle.addEventListener('change', function() {
        if (this.checked) {
            currentLayout = lightLayout;
        } else {
            currentLayout = darkLayout;
        }

        Plotly.relayout('download-chart', currentLayout);
    });

    window.addEventListener('resize', function() {
        Plotly.Plots.resize('download-chart');
    });

    // document.getElementById('toggle-legend').addEventListener('click', function() {
    //     showlegend = !showlegend;
    //     Plotly.update('download-chart', {}, {showlegend: showlegend});
    // });

    currentLayout = themeToggle.checked ? lightLayout : darkLayout;
    updateChart(data);
});