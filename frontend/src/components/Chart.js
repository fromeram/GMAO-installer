// Chart.js
// Componente que muestra un gráfico de líneas utilizando react-chartjs-2 y Chart.js.
// Se carga la información del gráfico mediante el endpoint /api/chart-data

import React, { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Legend,
  Tooltip,
  Title,
} from "chart.js";
import { fetchWithAuth } from "../apiConfig";

// Registrar los componentes necesarios de Chart.js
ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Legend, Tooltip, Title);

const Chart = () => {
  const [chartData, setChartData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchChartData = async () => {
      try {
        const data = await fetchWithAuth("/chart-data");
        setChartData({
          labels: data.labels,
          datasets: data.datasets,
        });
      } catch (err) {
        console.error("Error al cargar datos del gráfico:", err);
        setError("No se pudieron cargar los datos del gráfico.");
      }
    };
    fetchChartData();
  }, []);

  if (error) return <p className="text-red-500">{error}</p>;
  if (!chartData) return <p>Cargando gráfico...</p>;

  const options = {
    responsive: true,
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: "Órdenes de Trabajo" },
    },
  };

  return (
    <div className="max-w-lg mx-auto">
      <Line data={chartData} options={options} />
    </div>
  );
};

export default Chart;
