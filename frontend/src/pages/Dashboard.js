// src/pages/Dashboard.js (versión corregida - Arreglado error de bajo stock)
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Row, Col, Statistic, Typography, Spin, Alert, Button, Table, Progress, Tag, Space, Divider } from 'antd';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title as ChartTitle,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { Pie } from 'react-chartjs-2';
import { 
  WarningOutlined, ClockCircleOutlined, ToolOutlined, 
  CheckCircleOutlined, ArrowUpOutlined, ArrowDownOutlined 
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { Link } from 'react-router-dom';
import '../styles/CommonPage.css';
import FormatChangesWidget from '../components/FormatChangesWidget';

// Registrar componentes Chart.js necesarios
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  ChartTitle,
  Tooltip,
  Legend
);

const { Title, Text } = Typography;

// Componente para el Widget de Bajo Stock (corregido)
const LowStockWidget = () => {
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchLowStockCount = async () => {
      try {
        // RUTA CORREGIDA: sin /api/ prefix y sin parámetro limit
        const data = await fetchWithAuth('/inventory/low-stock');
        setCount(data.length);
      } catch (error) {
        console.error("Error fetching low stock count:", error);
        setCount(0); // En caso de error, establecemos a 0
      } finally {
        setLoading(false);
      }
    };
    
    fetchLowStockCount();
  }, []);
  
  return (
    <Card className="form-container">
      <Statistic
        title="Productos Bajo Mínimos"
        value={count}
        valueStyle={{ color: count > 0 ? '#ff4d4f' : '#52c41a' }}
        prefix={<WarningOutlined />}
        loading={loading}
      />
      {count > 0 && (
        <Button 
          type="link" 
          onClick={() => navigate('/inventario/bajo-stock')}
          style={{ padding: 0, marginTop: 8 }}
        >
          Ver detalles
        </Button>
      )}
    </Card>
  );
};

const Dashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Estados para datos ampliados
  const [stats, setStats] = useState({
    sections: [],
    totalMaintenance: 0,
    pendingMaintenance: 0,
    // Nuevos estados para métricas
    pendingOrders: 0,
    completedOrders: 0,
    lowStockItems: 0,
    ongoingOrders: 0,
    mtbfAvg: 0,
    mttrAvg: 0,
    availabilityAvg: 0,
    completedOrdersTrend: 0
  });
  
  // Nuevos estados para tablas y gráficos
  const [pendingTasks, setPendingTasks] = useState([]);
  const [maintenanceHistory, setMaintenanceHistory] = useState([]);
  const [lowStockProducts, setLowStockProducts] = useState([]);
  const [maintenanceByMonth, setMaintenanceByMonth] = useState([]);
  const [maintenanceByType, setMaintenanceByType] = useState([]);
  const [sectionsData, setSectionsData] = useState([]);

  // Función para cargar datos ampliada
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Mantener compatibilidad con el Dashboard original
      const sectionsResponse = await fetchWithAuth('/sections-data');
      
      if (!Array.isArray(sectionsResponse)) {
        throw new Error('Formato de datos inválido');
      }

      // Datos originales
      const sectionsData = {
        sections: sectionsResponse,
        totalMaintenance: sectionsResponse.reduce((acc, curr) => acc + curr.preventive + curr.corrective, 0),
        pendingMaintenance: sectionsResponse.reduce((acc, curr) => acc + (curr.pending || 0), 0)
      };
      
      // Nuevos endpoints para datos mejorados - CORREGIDOS PARA EVITAR ERRORES 404
      // Usamos Promise.allSettled para que si uno falla no afecte a los otros
      const resultsArray = await Promise.allSettled([
        fetchWithAuth('/dashboard/stats').catch(() => ({})),
        fetchWithAuth('/dashboard/pending-tasks').catch(() => []),
        fetchWithAuth('/dashboard/maintenance-history').catch(() => []),
        fetchWithAuth('/inventory/low-stock').catch(() => []), // CORREGIDA esta ruta sin limit=5
        fetchWithAuth('/dashboard/maintenance-by-month').catch(() => []),
        fetchWithAuth('/dashboard/maintenance-by-type').catch(() => [])
      ]);
      
      // Extraer resultados, tomando valor o fallback si hubo error
      const [
        dashboardStats,
        pendingTasksData,
        maintenanceHistoryData,
        lowStockData,
        maintenanceByMonthData,
        maintenanceByTypeData
      ] = resultsArray.map(result => 
        result.status === 'fulfilled' ? result.value : (result.reason?.fallback || [])
      );
      
      // Filtrar para solo mostrar los primeros 5 productos bajo mínimos en la tabla
      const top5LowStock = Array.isArray(lowStockData) ? lowStockData.slice(0, 5) : [];
      
      // Actualizar estados
      setStats({
        ...sectionsData,
        pendingOrders: dashboardStats?.pendingOrders || sectionsData.pendingMaintenance,
        completedOrders: dashboardStats?.completedOrders || 0,
        lowStockItems: Array.isArray(lowStockData) ? lowStockData.length : 0, // Corregido para contar correctamente
        ongoingOrders: dashboardStats?.ongoingOrders || 0,
        mtbfAvg: dashboardStats?.mtbfAvg || 0,
        mttrAvg: dashboardStats?.mttrAvg || 0,
        availabilityAvg: dashboardStats?.availabilityAvg || 0,
        completedOrdersTrend: dashboardStats?.completedOrdersTrend || 0
      });
      
      setPendingTasks(pendingTasksData || []);
      setMaintenanceHistory(maintenanceHistoryData || []);
      setLowStockProducts(top5LowStock); // Solo los primeros 5
      setMaintenanceByMonth(maintenanceByMonthData || []);
      setMaintenanceByType(maintenanceByTypeData || []);
      setSectionsData(sectionsResponse || []);
      
      setError(null);
    } catch (error) {
      console.error('Error:', error);
      setError(error.message);
      
      if (error.message.includes('401')) {
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!sessionStorage.getItem('access_token')) {
      navigate('/login');
      return;
    }
    fetchDashboardData();
  }, [navigate]);

  // Columnas para tabla de tareas pendientes
  const pendingTasksColumns = [
    {
      title: 'Tarea',
      dataIndex: 'title',
      key: 'title',
      render: (text, record) => (
        <Link to={`/ordenes/${record.id}`}>{text}</Link>
      )
    },
    {
      title: 'Tipo',
      dataIndex: 'work_type',
      key: 'work_type',
      render: type => {
        const colors = {
          'Preventivo': 'green',
          'Correctivo': 'red',
          'Inspección': 'blue',
          'Mejora': 'cyan'
        };
        return <Tag color={colors[type] || 'default'}>{type}</Tag>;
      }
    },
    {
      title: 'Máquina',
      dataIndex: ['machine_obj', 'nombre'],
      key: 'machine',
      render: (text, record) => record.machine_obj?.nombre || '-'
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      render: status => {
        const colors = {
          'Pendiente': 'gold',
          'En curso': 'blue',
          'En revisión': 'purple'
        };
        return <Tag color={colors[status] || 'default'}>{status}</Tag>;
      }
    }
  ];
  
  // Columnas para tabla de productos bajo mínimos
  const lowStockColumns = [
    {
      title: 'Producto',
      dataIndex: 'product_name', // Corregido, algunas APIs usan product_name y otras nombre
      key: 'nombre',
      render: (text, record) => (
        <Link to={`/productos/${record.id}`}>{text || record.nombre}</Link>
      )
    },
    {
      title: 'Stock',
      dataIndex: 'cantidad',
      key: 'cantidad', 
      render: (text, record) => text || record.quantity || 0
    },
    {
      title: 'Mínimo',
      dataIndex: 'stock_minimo',
      key: 'stock_minimo',
      render: (text, record) => text || record.min_stock || 0
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, record) => {
        const cantidad = record.cantidad || record.quantity || 0;
        const minimo = record.stock_minimo || record.min_stock || 1;
        const ratio = cantidad / minimo;
        let color = 'green';
        if (ratio <= 0.5) color = 'red';
        else if (ratio <= 0.75) color = 'orange';
        
        return (
          <Progress 
            percent={Math.min(100, ratio * 100)} 
            size="small" 
            status={ratio <= 0.5 ? "exception" : "active"}
            strokeColor={color}
          />
        );
      }
    }
  ];
  
  // Columnas historial de mantenimiento (últimas OTs)
  const maintenanceHistoryColumns = [
    {
      title: 'Orden',
      dataIndex: 'order_number',
      key: 'order_number',
      render: (text, record) => (
        <Link to={`/ordenes/${record.id}`}>{text || `OT-${record.id}`}</Link>
      )
    },
    {
      title: 'Tipo',
      dataIndex: 'work_type',
      key: 'work_type',
      render: type => {
        const colors = {
          'Preventivo': 'green',
          'Correctivo': 'red',
          'Inspección': 'blue',
          'Mejora': 'cyan'
        };
        return <Tag color={colors[type] || 'default'}>{type}</Tag>;
      }
    },
    {
      title: 'Máquina',
      dataIndex: ['machine_obj', 'nombre'],
      key: 'machine',
      render: (text, record) => record.machine_obj?.nombre || '-'
    },
    {
      title: 'Fecha Cierre',
      dataIndex: 'finished_at',
      key: 'finished_at',
      render: date => date ? new Date(date).toLocaleDateString() : '-'
    }
  ];
  
  // Datos para gráficos
  const maintenanceTypeData = {
    labels: maintenanceByType.map(item => item.name),
    datasets: [
      {
        data: maintenanceByType.map(item => item.value),
        backgroundColor: [
          '#52c41a', // Preventivo
          '#ff4d4f', // Correctivo
          '#1890ff', // Inspección
          '#faad14', // Otros
          '#722ed1'  // Extra
        ],
        borderWidth: 1,
      },
    ],
  };

  const maintenanceMonthlyData = {
    labels: maintenanceByMonth.map(item => item.month),
    datasets: [
      {
        label: 'Preventivo',
        data: maintenanceByMonth.map(item => item.preventivo),
        backgroundColor: '#52c41a',
      },
      {
        label: 'Correctivo',
        data: maintenanceByMonth.map(item => item.correctivo),
        backgroundColor: '#ff4d4f',
      },
      {
        label: 'Inspección',
        data: maintenanceByMonth.map(item => item.inspeccion),
        backgroundColor: '#1890ff',
      },
      {
        label: 'Otros',
        data: maintenanceByMonth.map(item => item.otros),
        backgroundColor: '#faad14',
      },
    ],
  };

  const sectionBarData = {
    labels: sectionsData.map(section => section.nombre),
    datasets: [
      {
        label: 'Preventivo',
        data: sectionsData.map(section => section.preventive),
        backgroundColor: '#52c41a',
      },
      {
        label: 'Correctivo',
        data: sectionsData.map(section => section.corrective),
        backgroundColor: '#ff4d4f',
      },
    ],
  };
  
  if (loading) {
    return (
      <div className="page-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <Spin size="large" tip="Cargando datos del dashboard..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
        />
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2} className="page-title">Panel de Control</Title>
      </div>

      {/* Primera fila: KPIs principales */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card className="form-container">
            <Statistic
              title="Órdenes Pendientes"
              value={stats.pendingOrders || stats.pendingMaintenance}
              valueStyle={{ color: '#faad14' }}
              prefix={<ClockCircleOutlined />}
            />
            <div style={{ marginTop: 8 }}>
              <Link to="/ordenes?status=Pendiente">
                <Button type="link" size="small">Ver detalles</Button>
              </Link>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card className="form-container">
            <Statistic
              title="Órdenes en Curso"
              value={stats.ongoingOrders || 0}
              valueStyle={{ color: '#1890ff' }}
              prefix={<ToolOutlined />}
            />
            <div style={{ marginTop: 8 }}>
              <Link to="/ordenes?status=En%20curso">
                <Button type="link" size="small">Ver detalles</Button>
              </Link>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <LowStockWidget />
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card className="form-container">
            <Statistic
              title="Órdenes Completadas (Mes)"
              value={stats.completedOrders || 0}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
              suffix={
                stats.completedOrdersTrend ? (
                  <span style={{ fontSize: '60%', marginLeft: 8 }}>
                    {stats.completedOrdersTrend > 0 ? (
                      <span style={{ color: '#52c41a' }}>
                        <ArrowUpOutlined /> {stats.completedOrdersTrend}%
                      </span>
                    ) : (
                      <span style={{ color: '#ff4d4f' }}>
                        <ArrowDownOutlined /> {Math.abs(stats.completedOrdersTrend)}%
                      </span>
                    )}
                  </span>
                ) : null
              }
            />
            <div style={{ marginTop: 8 }}>
              <Link to="/ordenes?status=Cerrada">
                <Button type="link" size="small">Ver detalles</Button>
              </Link>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Segunda fila: KPIs de métricas */}
      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        <Col xs={24} sm={8}>
          <Card className="form-container">
            <Statistic
              title="MTBF Promedio"
              value={stats.mtbfAvg || 0}
              precision={1}
              valueStyle={{ color: '#1890ff' }}
              suffix="horas"
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              Tiempo Medio Entre Fallos
            </Text>
          </Card>
        </Col>
        
        <Col xs={24} sm={8}>
          <Card className="form-container">
            <Statistic
              title="MTTR Promedio"
              value={stats.mttrAvg || 0}
              precision={1}
              valueStyle={{ color: (stats.mttrAvg && stats.mttrAvg < 4) ? '#52c41a' : '#ff4d4f' }}
              suffix="horas"
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              Tiempo Medio Para Reparar
            </Text>
          </Card>
        </Col>
        
        <Col xs={24} sm={8}>
          <Card className="form-container">
            <Statistic
              title="Disponibilidad Promedio"
              value={stats.availabilityAvg || 0}
              precision={2}
              valueStyle={{ color: (stats.availabilityAvg && stats.availabilityAvg > 90) ? '#52c41a' : '#faad14' }}
              suffix="%"
            />
            <Progress 
              percent={stats.availabilityAvg || 0} 
              size="small"
              status={(stats.availabilityAvg && stats.availabilityAvg > 90) ? "success" : "active"}
              strokeColor={(stats.availabilityAvg && stats.availabilityAvg > 90) ? '#52c41a' : ((stats.availabilityAvg && stats.availabilityAvg > 75) ? '#faad14' : '#ff4d4f')}
            />
          </Card>
        </Col>
      </Row>

      {/* ✅ NUEVA FILA: Widgets adicionales - AÑADIR AQUÍ */}
      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        <Col xs={24} lg={8}>
          <FormatChangesWidget />
        </Col>
        
        {/* Aquí puedes añadir más widgets en el futuro */}
        <Col xs={24} lg={8}>
          {/* Espacio para otro widget */}
        </Col>
        
        <Col xs={24} lg={8}>
          {/* Espacio para otro widget */}
        </Col>
      </Row>

      {/* Gráfico de barras por mes */}
      {maintenanceByMonth.length > 0 && (
        <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
          <Col span={24}>
            <Card title="Órdenes de Trabajo por Mes" className="form-container">
              <div style={{ height: 300 }}>
                <Bar 
                  data={maintenanceMonthlyData} 
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
              </div>
            </Card>
          </Col>
        </Row>
      )}

      {/* Tablas de pendientes y productos bajo mínimos */}
      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        <Col xs={24} lg={16}>
          <Card 
            title="Órdenes Pendientes" 
            extra={<Link to="/ordenes?status=Pendiente">Ver todas</Link>}
            className="form-container"
          >
            <Table
              columns={pendingTasksColumns}
              dataSource={pendingTasks}
              rowKey="id"
              pagination={{ pageSize: 5 }}
              size="small"
              locale={{ emptyText: "No hay órdenes pendientes actualmente" }}
            />
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card 
            title="Productos Bajo Stock Mínimo" 
            extra={<Link to="/inventario/bajo-stock">Ver todos</Link>}
            className="form-container"
          >
            <Table
              columns={lowStockColumns}
              dataSource={lowStockProducts}
              rowKey="id"
              pagination={{ pageSize: 5 }}
              size="small"
              locale={{ emptyText: "No hay productos bajo mínimos" }}
            />
          </Card>
        </Col>
      </Row>

      {/* Gráficos de análisis */}
      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        <Col xs={24} md={12}>
          <Card title="Mantenimiento por Tipo" className="form-container">
            <div style={{ height: 300, display: 'flex', justifyContent: 'center' }}>
              {maintenanceByType.length > 0 ? (
                <Pie 
                  data={maintenanceTypeData} 
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
              ) : (
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <Text type="secondary">No hay datos suficientes</Text>
                </div>
              )}
            </div>
          </Card>
        </Col>
        
        <Col xs={24} md={12}>
          <Card title="Órdenes por Sección" className="form-container">
            <div style={{ height: 300 }}>
              <Bar 
                data={sectionBarData} 
                options={{
                  indexAxis: 'y',
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    x: {
                      beginAtZero: true
                    }
                  }
                }}
              />
            </div>
          </Card>
        </Col>
      </Row>

      {/* Historial reciente */}
      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        <Col span={24}>
          <Card 
            title="Últimas Órdenes Completadas" 
            extra={<Link to="/ordenes?status=Cerrada">Ver historial completo</Link>}
            className="form-container"
          >
            <Table
              columns={maintenanceHistoryColumns}
              dataSource={maintenanceHistory}
              rowKey="id"
              pagination={{ pageSize: 5 }}
              size="small"
              locale={{ emptyText: "No hay órdenes completadas recientemente" }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;