import React from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

// Registro explícito de las escalas y componentes
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const data = {
    labels: ['Enero', 'Febrero', 'Marzo', 'Abril'],
    datasets: [
        {
            label: 'Correctivos',
            data: [12, 19, 3, 5],
            backgroundColor: 'rgba(255, 99, 132, 0.5)',
        },
        {
            label: 'Preventivos',
            data: [2, 3, 20, 3],
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
        },
    ],
};

const options = {
    responsive: true,
    plugins: {
        legend: {
            position: 'top',
        },
        title: {
            display: true,
            text: 'Mantenimiento Correctivo vs Preventivo',
        },
    },
    scales: {
        x: {
            type: 'category', // Escala de categoría
        },
        y: {
            beginAtZero: true,
        },
    },
};

const ChartComponent = () => {
    return <Bar data={data} options={options} />;
};

export default ChartComponent;
