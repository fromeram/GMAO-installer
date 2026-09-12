// src/pages/FormatReports.js - Dashboard y Reportes de Cambios de Formato
import React, { useState, useEffect } from 'react';
import { 
  Card, Row, Col, Statistic, Typography, Select, DatePicker, 
  Table, Progress, Tag, Space, Alert, Button, Spin 
} from 'antd';
import { 
  BarChartOutlined, TrophyOutlined, ClockCircleOutlined, 
  SettingOutlined, GlobalOutlined, ApartmentOutlined, ToolOutlined,
  RiseOutlined, FallOutlined, FileExcelOutlined 
} from '@ant-design/icons';
import { Bar, Pie, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title as ChartTitle,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
} from 'chart.js';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import dayjs from 'dayjs';
import * as XLSX from 'xlsx';

// Registrar componentes de Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  LineElement,
  ChartTitle,
  Tooltip,
  Legend
);

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const FormatReports = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [efficiencyData, setEfficiencyData] = useState(null);
  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(true);
  const { currentUser } = useAuth();

  // Estados para filtros
  const [filters, setFilters] = useState({
    days: 30,
    section: null,
    changeType: null,
    dateRange: null
  });

  useEffect(() => {
    loadData();
    loadSections();
  }, []);

  useEffect(() => {
    loadData();
  }, [filters]);

  const loadSections = async () => {
    try {
      const sectionsData = await fetchWithAuth('/secciones');
      setSections(sectionsData || []);
    } catch (error) {
      console.error('Error cargando secciones:', error);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      // Construir parámetros de query
      const params = new URLSearchParams();
      if (filters.days) params.append('days', filters.days);
      if (filters.section) params.append('section_id', filters.section);
      if (filters.changeType) params.append('format_change_type', filters.changeType);
      if (filters.dateRange) {
        params.append('start_date', filters.dateRange[0].format('YYYY-MM-DD'));
        params.append('end_date', filters.dateRange[1].format('YYYY-MM-DD'));
      }

      const [dashboard, summary, efficiency] = await Promise.all([
        fetchWithAuth(`/dashboard/format-changes?${params}`),
        fetchWithAuth(`/reports/format-changes/summary?${params}`),
        fetchWithAuth('/reports/format-changes/efficiency?limit=20')
      ]);

      setDashboardData(dashboard);
      setSummaryData(summary);
      setEfficiencyData(efficiency);
    } catch (error) {
      console.error('Error cargando datos de reportes:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportToExcel = () => {
    if (!efficiencyData || !efficiencyData.data) return;

    const dataToExport = efficiencyData.data.map(item => ({
      'Orden': item.order_number,
      'Título': item.title,
      'Tipo de Cambio': item.format_change_type,
      'Formato Origen': item.format_from || 'No especificado',
      'Formato Destino': item.format_to || 'No especificado',
      'Tiempo Estimado (h)': item.estimated_duration,
      'Tiempo Real (h)': item.actual_duration,
      'Eficiencia (%)': item.efficiency,
      'Pérdida Producción (h)': item.production_loss || 0,
      'Sección': item.section,
      'Técnico': item.assigned_to,
      'Fecha Finalización': item.finished_at ? dayjs(item.finished_at).format('DD/MM/YYYY') : ''
    }));

    const worksheet = XLSX.utils.json_to_sheet(dataToExport);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Eficiencia_Cambios_Formato");
    XLSX.writeFile(workbook, "Reporte_Eficiencia_Cambios_Formato.xlsx");
  };

  // Datos para gráficos
  const getChartData = () => {
    if (!dashboardData) return {};

    // Gráfico de tendencia semanal
    const weeklyTrendData = {
      labels: dashboardData.weekly_trend?.map(w => `Sem ${dayjs(w.week).format('DD/MM')}`) || [],
      datasets: [
        {
          label: 'Total de Cambios',
          data: dashboardData.weekly_trend?.map(w => w.total_changes) || [],
          backgroundColor: 'rgba(54, 162, 235, 0.5)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        },
        {
          label: 'Cambios Completados',
          data: dashboardData.weekly_trend?.map(w => w.completed_changes) || [],
          backgroundColor: 'rgba(75, 192, 192, 0.5)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1
        }
      ]
    };

    // Gráfico de tipos de cambio
    const typeDistributionData = {
      labels: ['Cambios Globales', 'Cambios de Línea', 'Cambios Individuales'],
      datasets: [{
        data: [
          dashboardData.kpis?.global_changes || 0,
          dashboardData.kpis?.line_changes || 0,
          dashboardData.kpis?.individual_changes || 0
        ],
        backgroundColor: [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 205, 86, 0.8)'
        ],
        borderWidth: 1
      }]
    };

    return { weeklyTrendData, typeDistributionData };
  };

  const { weeklyTrendData, typeDistributionData } = getChartData();

  const getEfficiencyColor = (efficiency) => {
    if (efficiency >= 100) return 'success';
    if (efficiency >= 80) return 'normal';
    if (efficiency >= 60) return 'exception';
    return 'exception';
  };

  const getChangeTypeIcon = (type) => {
    switch (type) {
      case 'Individual': return <ToolOutlined />;
      case 'Línea': return <ApartmentOutlined />;
      case 'Global': return <GlobalOutlined />;
      default: return <SettingOutlined />;
    }
  };

  const efficiencyColumns = [
    {
      title: 'Orden',
      dataIndex: 'order_number',
      key: 'order_number',
      width: 100
    },
    {
      title: 'Título',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      ellipsis: true
    },
    {
      title: 'Tipo',
      dataIndex: 'format_change_type',
      key: 'format_change_type',
      width: 120,
      render: (type) => (
        <Tag icon={getChangeTypeIcon(type)} color="blue">
          {type}
        </Tag>
      )
    },
    {
      title: 'Cambio',
      key: 'format_change',
      width: 200,
      render: (_, record) => (
        <div>
          <div><Text type="secondary">De:</Text> {record.format_from || 'No especificado'}</div>
          <div><Text type="secondary">A:</Text> {record.format_to || 'No especificado'}</div>
        </div>
      )
    },
    {
      title: 'Tiempo (h)',
      key: 'times',
      width: 120,
      render: (_, record) => (
        <div>
          <div>Est: {record.estimated_duration}</div>
          <div>Real: {record.actual_duration}</div>
        </div>
      )
    },
    {
      title: 'Eficiencia',
      dataIndex: 'efficiency',
      key: 'efficiency',
      width: 100,
      render: (efficiency) => (
        <Progress
          type="circle"
          size={50}
          percent={Math.min(efficiency, 150)}
          status={getEfficiencyColor(efficiency)}
          format={() => `${efficiency.toFixed(0)}%`}
        />
      )
    },
    {
      title: 'Sección',
      dataIndex: 'section',
      key: 'section',
      width: 100,
      ellipsis: true
    },
    {
      title: 'Fecha',
      dataIndex: 'finished_at',
      key: 'finished_at',
      width: 100,
      render: (date) => date ? dayjs(date).format('DD/MM/YY') : '-'
    }
  ];

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" tip="Cargando reportes..." />
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>📊 Reportes de Cambios de Formato</Title>
        <Button 
          type="primary" 
          icon={<FileExcelOutlined />} 
          onClick={exportToExcel}
          disabled={!efficiencyData?.data?.length}
        >
          Exportar Excel
        </Button>
      </div>

      {/* Filtros */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col span={3}>
            <Text strong>Filtros:</Text>
          </Col>
          <Col span={4}>
            <Select
              style={{ width: '100%' }}
              placeholder="Periodo"
              value={filters.days}
              onChange={(value) => setFilters({...filters, days: value, dateRange: null})}
            >
              <Option value={7}>Últimos 7 días</Option>
              <Option value={30}>Últimos 30 días</Option>
              <Option value={90}>Últimos 90 días</Option>
              <Option value={365}>Último año</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              style={{ width: '100%' }}
              placeholder="Tipo de cambio"
              value={filters.changeType}
              onChange={(value) => setFilters({...filters, changeType: value})}
              allowClear
            >
              <Option value="Individual">Individual</Option>
              <Option value="Línea">Línea</Option>
              <Option value="Global">Global</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              style={{ width: '100%' }}
              placeholder="Sección"
              value={filters.section}
              onChange={(value) => setFilters({...filters, section: value})}
              allowClear
            >
              {sections.map(section => (
                <Option key={section.id} value={section.id}>
                  {section.nombre}
                </Option>
              ))}
            </Select>
          </Col>
          <Col span={6}>
            <RangePicker
              style={{ width: '100%' }}
              placeholder={['Fecha inicio', 'Fecha fin']}
              value={filters.dateRange}
              onChange={(dates) => setFilters({...filters, dateRange: dates, days: null})}
            />
          </Col>
          <Col span={3}>
            <Button 
              onClick={() => setFilters({
                days: 30,
                section: null,
                changeType: null,
                dateRange: null
              })}
            >
              Limpiar
            </Button>
          </Col>
        </Row>
      </Card>

      {/* KPIs Principales */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic 
              title="Total de Cambios"
              value={dashboardData?.kpis?.total_changes || 0}
              prefix={<SettingOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="Tasa de Completación"
              value={dashboardData?.kpis?.completion_rate || 0}
              precision={1}
              suffix="%"
              prefix={<TrophyOutlined />}
              valueStyle={{ 
                color: (dashboardData?.kpis?.completion_rate || 0) >= 80 ? '#52c41a' : '#faad14' 
              }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="Eficiencia Promedio"
              value={dashboardData?.kpis?.average_efficiency || 0}
              precision={1}
              suffix="%"
              prefix={
                (dashboardData?.kpis?.average_efficiency || 0) >= 100 ? 
                <RiseOutlined /> : <FallOutlined />
              }
              valueStyle={{ 
                color: (dashboardData?.kpis?.average_efficiency || 0) >= 100 ? '#52c41a' : '#ff4d4f' 
              }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="Pérdida de Producción"
              value={dashboardData?.total_production_loss || 0}
              precision={1}
              suffix=" hrs"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Tiempos Promedio por Tipo */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic 
              title="Setup Global Promedio"
              value={dashboardData?.average_setup_times?.global_hours || 0}
              precision={1}
              suffix=" hrs"
              prefix={<GlobalOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic 
              title="Setup Línea Promedio"
              value={dashboardData?.average_setup_times?.line_hours || 0}
              precision={1}
              suffix=" hrs"
              prefix={<ApartmentOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic 
              title="Setup Individual Promedio"
              value={dashboardData?.average_setup_times?.individual_hours || 0}
              precision={1}
              suffix=" hrs"
              prefix={<ToolOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Gráficos */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Card title="📈 Tendencia Semanal" style={{ height: 400 }}>
            {weeklyTrendData && (
              <Bar 
                data={weeklyTrendData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    y: {
                      beginAtZero: true
                    }
                  }
                }}
              />
            )}
          </Card>
        </Col>
        <Col span={8}>
          <Card title="🥧 Distribución por Tipo" style={{ height: 400 }}>
            {typeDistributionData && (
              <Pie 
                data={typeDistributionData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom'
                    }
                  }
                }}
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* Cambios Más Frecuentes */}
      {summaryData?.top_format_combinations?.length > 0 && (
        <Card title="🔄 Cambios de Formato Más Frecuentes" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            {summaryData.top_format_combinations.slice(0, 5).map((combo, index) => (
              <Col span={4.8} key={index}>
                <Card size="small" style={{ textAlign: 'center' }}>
                  <Text strong>{combo.combination}</Text>
                  <br />
                  <Text type="secondary">{combo.count} veces</Text>
                  <br />
                  <Text type="secondary">⏱️ {combo.avg_duration_hours}h promedio</Text>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* Tabla de Eficiencia */}
      <Card title="🏆 Top 20 - Eficiencia de Cambios" style={{ marginBottom: 24 }}>
        {efficiencyData?.statistics && (
          <Alert
            message={`Análisis de ${efficiencyData.statistics.total_analyzed} cambios completados`}
            description={
              <Space split={<span>|</span>}>
                <span>Eficiencia promedio: <strong>{efficiencyData.statistics.avg_efficiency}%</strong></span>
                <span>Mejor: <strong>{efficiencyData.statistics.best_efficiency?.efficiency.toFixed(1)}%</strong></span>
                <span>Peor: <strong>{efficiencyData.statistics.worst_efficiency?.efficiency.toFixed(1)}%</strong></span>
                {efficiencyData.statistics.total_time_saved > 0 && (
                  <span style={{ color: '#52c41a' }}>
                    Tiempo ahorrado: <strong>{efficiencyData.statistics.total_time_saved.toFixed(1)}h</strong>
                  </span>
                )}
                {efficiencyData.statistics.total_time_lost > 0 && (
                  <span style={{ color: '#ff4d4f' }}>
                    Tiempo perdido: <strong>{efficiencyData.statistics.total_time_lost.toFixed(1)}h</strong>
                  </span>
                )}
              </Space>
            }
            type="info"
            style={{ marginBottom: 16 }}
          />
        )}
        
        <Table
          columns={efficiencyColumns}
          dataSource={efficiencyData?.data || []}
          rowKey="order_id"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* Resumen por Tipo de Cambio */}
      {summaryData?.by_type && (
        <Card title="📊 Resumen por Tipo de Cambio">
          <Row gutter={16}>
            {Object.entries(summaryData.by_type).map(([type, data]) => (
              <Col span={8} key={type}>
                <Card size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      {getChangeTypeIcon(type)}
                      <Text strong style={{ marginLeft: 8 }}>{type}</Text>
                    </div>
                    <Statistic 
                      title="Total"
                      value={data.count}
                      valueStyle={{ fontSize: 16 }}
                    />
                    <Statistic 
                      title="Completados"
                      value={data.completed}
                      valueStyle={{ fontSize: 16 }}
                    />
                    <Statistic 
                      title="Duración Promedio"
                      value={data.avg_duration}
                      precision={1}
                      suffix=" hrs"
                      valueStyle={{ fontSize: 16 }}
                    />
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}
    </div>
  );
};

export default FormatReports;