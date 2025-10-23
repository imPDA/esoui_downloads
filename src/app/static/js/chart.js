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
    yaxis2: {
        title: 'Downloads/h',
        overlaying: 'y',
        side: 'right',
        gridcolor: '#4a4e56',
        linecolor: '#4a4e56',
        zerolinecolor: '#4a4e56',
        showgrid: false,
        hoverformat: '.2f',
        fixedrange: true,
        anchor: 'free',
        position: 1, // Position on the right side (0 to 1)
        // Remove any association with the first y-axis
        scaleanchor: undefined,
        scaleratio: undefined,
        constrain: undefined,
        // Allow independent autoranging
        autorange: true,
        visible: false,
        color: '#00FF99',
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
        x: 1.07,
        y: 1,
        yanchor: 'top',
        xanchor: 'middle',
        yanchor: 'top',
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
    yaxis2: {
        title: 'Downloads/h',
        overlaying: 'y',
        side: 'right',
        gridcolor: '#e0e6ed',
        linecolor: '#e0e6ed',
        zerolinecolor: '#e0e6ed',
        showgrid: false,
        hoverformat: '.2f',
        fixedrange: true,
        anchor: 'free',
        position: 1, // Position on the right side (0 to 1)
        // Remove any association with the first y-axis
        scaleanchor: undefined,
        scaleratio: undefined,
        constrain: undefined,
        // Allow independent autoranging
        autorange: true,
        visible: false,
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

function updateChart() {
    if (typeof data !== 'undefined') {
        data.forEach((item, index) => {
            item.type = 'scattergl';
            item.mode = 'lines';
            item.line = { 
                color: colors[index % colors.length],
                width: 2,
            };
            item.visible = index < 8 ? true : 'legendonly';
        });

        Plotly.addTraces('download-chart', data)
    }

    if (typeof download_speed !== 'undefined') {
        const speedTrace = {
            ...download_speed,
            name: 'Download Speed',
            type: 'scattergl',
            mode: 'lines',
            // mode: 'markers',
            line: {
                // shape: 'spline',
                // color: '#ff6699',
                color: '#00FF99',
                width: 1,
                dash: 'dot',
                // smoothing: 1.3,
            },
            // marker: {
            //     size: 3,
            //     color: '#00FF99',
            // },
            yaxis: 'y2',
            visible: true,
            opacity: 0.5,
        };
        Plotly.addTraces('download-chart', speedTrace, 0);
        Plotly.relayout('download-chart', {
            'yaxis2.visible': true,
        });
    }

    if (versionShapes.length > 0) {
        Plotly.relayout('download-chart', {
            shapes: versionShapes,
            annotations: versionAnnotations,
        });
    };
}

document.addEventListener('DOMContentLoaded', (event) => {
    const themeToggle = document.getElementById('theme-toggle');
    Plotly.newPlot('download-chart', [], {...themeToggle.checked ? lightLayout : darkLayout}, 
    {
        responsive: true,
        scrollZoom: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtons: [
            ['zoom2d', 'pan2d', 'resetScale2d'],
        ]
    });

    themeToggle.addEventListener('change', function() {
        console.log(this.checked);
        console.log(this.checked ? lightLayout : darkLayout);
        Plotly.relayout('download-chart', {...this.checked ? lightLayout : darkLayout});
    });

    // window.addEventListener('resize', function() {
    //     Plotly.Plots.resize('download-chart');
    // });

    // document.getElementById('toggle-legend').addEventListener('click', function() {
    //     showlegend = !showlegend;
    //     Plotly.update('download-chart', {}, {showlegend: showlegend});
    // });

    updateChart();
});