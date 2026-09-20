// src/pages/AIDashboard.js - VERSIÓN FINAL, COMPLETA Y 100% REAL
import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Alert,
  Table,
  Progress,
  Badge,
  Button,
  Spin,
  Typography,
  List,
  Avatar,
  Tooltip,
  Select,
  DatePicker,
  Space,
  Divider,
  Modal,
  Tag
} from 'antd';
import {
  RobotOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  ReloadOutlined,
  EyeOutlined,
  ToolOutlined,
  LineChartOutlined,
  AlertOutlined,
  BulbOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  BarElement
} from 'chart.js';
import { api } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';

// Función helper para mostrar tiempo relativo
const timeAgo = (date) => {
  if (!date) return 'Nunca';
  const now = new Date();
  const diff = now - new Date(date);
  const minutes = Math.floor(diff / 60000);
  
  if (minutes < 1) return 'ahora mismo';
  if (minutes < 60) return `hace ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `hace ${hours} h`;
  const days = Math.floor(hours / 24);
  return `hace ${days} días`;
};

// Registrar componentes de Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  BarElement
);

const { Title: AntTitle, Text, Paragraph } = Typography;
const { Option } = Select;

const AIDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [riskMatrix, setRiskMatrix] = useState(null);
  const [selectedSection, setSelectedSection] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedMachine, setSelectedMachine] = useState(null);
  const [triggeringAnalysis, setTriggeringAnalysis] = useState({});
  
  const { currentUser } = useAuth();

  // ✅ --- ESTA ES LA FUNCIÓN CORREGIDA Y DEFINITIVA ---
  const loadDashboardData = async () => {
    try {
        setLoading(true);

        const params = new URLSearchParams();
        if (selectedSection) {
            params.append('section_id', selectedSection);
        }
        params.append('days', '30');

        // Llamamos a los endpoints del backend que preparan los datos REALES
        const [overviewRes, riskMatrixRes] = await Promise.all([
            api.get(`/ai/dashboard/overview?${params.toString()}`),
            api.get(`/ai/dashboard/machine-risk-matrix?${params.toString()}`)
        ]);

        console.log('✅ [REAL] Datos de Overview cargados:', overviewRes.data);
        console.log('✅ [REAL] Matriz de Riesgo cargada:', riskMatrixRes.data);
        
        // Guardamos los datos directamente, sin inventar nada en el frontend
        setDashboardData(overviewRes.data);
        setRiskMatrix(riskMatrixRes.data); 

    } catch (error) {
        console.error('Error cargando datos del dashboard IA:', error);
        Modal.error({
            title: 'Error de Carga',
            content: 'No se pudieron cargar los datos del dashboard. Por favor, comprueba la conexión con el servidor y recarga la página.'
        });
    } finally {
        setLoading(false);
    }
  };

  // Disparar análisis de máquina específica
  const triggerMachineAnalysis = async (machineId) => {
    try {
      setTriggeringAnalysis(prev => ({ ...prev, [machineId]: true }));
      
      const response = await api.post(`/ai/dashboard/trigger-analysis/${machineId}`);
      
      Modal.success({
        title: 'Análisis Iniciado',
        content: response.data.message,
        onOk: () => {
          setTimeout(loadDashboardData, 3000);
        }
      });
      
    } catch (error) {
      console.error('Error disparando análisis:', error);
      Modal.error({
        title: 'Error',
        content: 'No se pudo iniciar el análisis de IA'
      });
    } finally {
      setTriggeringAnalysis(prev => ({ ...prev, [machineId]: false }));
    }
  };

  // Función para manejar la apertura del modal
  const handleShowMachineDetails = (record) => {
    console.log('🔍 Mostrando detalles de máquina:', record);
    
    // El objeto 'record' ahora viene directamente del backend con datos reales
    const machineDetails = {
      machine_id: record.machine_id,
      machine_name: record.machine_name,
      section: record.section,
      criticality: record.criticality,
      risk_level: record.risk_level,
      failure_probability: record.failure_probability,
      confidence: record.confidence,
      predicted_date: record.predicted_date,
      components_at_risk: record.components_at_risk || [],
      recent_failures: record.recent_failures || 0,
      avg_downtime_hours: record.avg_downtime_hours || 0,
      last_prediction: record.last_prediction,
      machine: {
        id: record.machine_id,
        name: record.machine_name,
        section: record.section
      }
    };
    
    setSelectedMachine(machineDetails);
    setModalVisible(true);
  };

  useEffect(() => {
    loadDashboardData();
  }, [selectedSection]);

  // Configuración de gráficos
  const riskChartData = {
    labels: ['Crítico', 'Alto', 'Medio', 'Bajo'],
    datasets: [{
      data: riskMatrix ? [
        riskMatrix.risk_statistics.critical,
        riskMatrix.risk_statistics.high,
        riskMatrix.risk_statistics.medium,
        riskMatrix.risk_statistics.low
      ] : [0, 0, 0, 0],
      backgroundColor: ['#ff4d4f', '#fa8c16', '#fadb14', '#52c41a'],
      borderWidth: 2,
      borderColor: '#fff'
    }]
  };

  const predictionTrendData = {
    labels: dashboardData?.prediction_trends?.daily_predictions?.map(d => 
      new Date(d.date).toLocaleDateString()
    ) || [],
    datasets: [{
      label: 'Predicciones Generadas',
      data: dashboardData?.prediction_trends?.daily_predictions?.map(d => d.predictions_count) || [],
      borderColor: '#1890ff',
      backgroundColor: 'rgba(24, 144, 255, 0.1)',
      tension: 0.4
    }]
  };

  // Columnas para tabla de máquinas en riesgo
  const riskColumns = [
    {
      title: 'Máquina',
      dataIndex: 'machine_name',
      key: 'machine_name',
      render: (text, record) => (
        <div>
          <strong>{record.machine_name || 'N/A'}</strong>
          <br />
          <Text type="secondary">{record.section || 'N/A'}</Text>
        </div>
      )
    },
    {
      title: 'Riesgo',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (risk) => {
        const colors = {
          critical: 'red',
          high: 'orange',
          medium: 'gold',
          low: 'green'
        };
        const labels = {
          critical: 'Crítico',
          high: 'Alto',
          medium: 'Medio',
          low: 'Bajo'
        };
        return <Tag color={colors[risk]}>{labels[risk] || 'N/A'}</Tag>;
      }
    },
    {
      title: 'Probabilidad',
      dataIndex: 'failure_probability',
      key: 'probability',
      render: (prob) => prob ? (
        <Progress 
          percent={Math.round(prob)} 
          size="small"
          status={prob > 80 ? 'exception' : prob > 60 ? 'active' : 'success'}
        />
      ) : 'N/A'
    },
    {
      title: 'Fecha Predicha',
      dataIndex: 'predicted_date',
      key: 'predicted_date',
      render: (date) => date ? (
        <Tooltip title={new Date(date).toLocaleString()}>
          {timeAgo(date)}
        </Tooltip>
      ) : 'N/A'
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => handleShowMachineDetails(record)}
          >
            Detalles
          </Button>
          <Button 
            size="small" 
            icon={<ReloadOutlined />}
            loading={triggeringAnalysis[record.machine_id]}
            onClick={() => triggerMachineAnalysis(record.machine_id)}
          >
            Analizar
          </Button>
        </Space>
      )
    }
  ];

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={{ padding: '0' }}>
      <Card style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <AntTitle level={2} style={{ margin: 0 }}>
              <RobotOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              Dashboard de Inteligencia Artificial
            </AntTitle>
            <Paragraph type="secondary" style={{ margin: 0 }}>
              Análisis predictivo basado en datos reales de tu planta
            </Paragraph>
          </Col>
          <Col>
            <Space>
              <Select
                placeholder="Filtrar por sección"
                style={{ width: 200 }}
                allowClear
                value={selectedSection}
                onChange={setSelectedSection}
              >
                <Option value={1}>Prensas</Option>
                <Option value={2}>Mantenimiento</Option>
                <Option value={4}>Esmaltadoras</Option>
                <Option value={5}>Clasificacion</Option>
                <Option value={6}>RECTIFICADORAS</Option>
                <Option value={7}>Hornos</Option>
                <Option value={8}>Diseño</Option>
              </Select>
              <Button 
                icon={<ReloadOutlined />} 
                onClick={loadDashboardData}
                loading={loading}
              >
                Actualizar
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Máquinas Monitoreadas"
              value={dashboardData?.overview?.total_machines_monitored || 0}
              prefix={<SettingOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Alertas de Alto Riesgo"
              value={dashboardData?.overview?.high_risk_machines || 0}
              prefix={<WarningOutlined style={{ color: '#fa541c' }} />}
              valueStyle={{ color: '#fa541c' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Precisión del Modelo IA"
              value={dashboardData?.overview?.ai_accuracy_percent || 0}
              suffix="%"
              prefix={<TrophyOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
              precision={1}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Predicciones (últimos 7 días)"
              value={dashboardData?.overview?.predictions_last_week || 0}
              prefix={<LineChartOutlined style={{ color: '#722ed1' }} />}
            />
          </Card>
        </Col>
      </Row>

      {dashboardData?.high_risk_alerts?.length > 0 && (
        <Alert
          message="🚨 Alertas de Alto Riesgo (Datos Reales de IA)"
          description={
            <div style={{ marginTop: 8 }}>
              {dashboardData.high_risk_alerts.map(alert => (
                <Tag 
                  key={alert.machine_id} 
                  color="red" 
                  style={{ marginBottom: 4, padding: '4px 8px', fontSize: '13px' }}
                >
                  <strong>{alert.machine_name}:</strong> {Math.round(alert.probability)}% de riesgo
                </Tag>
              ))}
            </div>
          }
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Card title="Distribución de Riesgo" extra={<AlertOutlined />}>
            <div style={{ height: 300, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <Doughnut 
                data={riskChartData} 
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { position: 'bottom' } }
                }}
              />
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          <Card title="Tendencia de Predicciones" extra={<LineChartOutlined />}>
            <div style={{ height: 300 }}>
              <Line 
                data={predictionTrendData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } },
                  scales: { y: { beginAtZero: true } }
                }}
              />
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={16}>
          <Card title="Máquinas en Riesgo (según IA)" extra={<WarningOutlined />}>
            <Table
              columns={riskColumns}
              dataSource={riskMatrix?.risk_matrix || []}
              rowKey={record => record.machine_id}
              pagination={{ pageSize: 5 }}
              size="small"
              loading={loading}
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="Acciones Recomendadas por IA" extra={<BulbOutlined />}>
            <List
              dataSource={dashboardData?.recommended_actions?.slice(0, 5) || []}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Avatar icon={<ToolOutlined />} size="small" />}
                    title={item.machine_name}
                    description={
                      <div>
                        {(Array.isArray(item.actions) ? item.actions : []).slice(0, 2).map((action, idx) => (
                          <div key={idx} style={{ fontSize: '12px' }}>• {action}</div>
                        ))}
                        <Badge 
                          color={item.priority === 'high' ? 'red' : 'orange'} 
                          text={item.priority === 'high' ? 'Alta' : 'Media'} 
                        />
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      <Modal
        title={`Análisis Real - ${selectedMachine?.machine_name || 'N/A'}`}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setModalVisible(false)}>
            Cerrar
          </Button>,
          <Button 
            key="analyze" 
            type="primary" 
            icon={<ReloadOutlined />}
            loading={triggeringAnalysis[selectedMachine?.machine_id]}
            onClick={() => {
              if (selectedMachine?.machine_id) {
                triggerMachineAnalysis(selectedMachine.machine_id);
                setModalVisible(false);
              }
            }}
          >
            Nuevo Análisis
          </Button>
        ]}
        width={600}
      >
        {selectedMachine ? (
          <div>
            <Divider orientation="left">Información General</Divider>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>Máquina:</Text> {selectedMachine.machine_name || 'N/A'}
              </Col>
              <Col span={12}>
                <Text strong>Sección:</Text> {selectedMachine.section || 'N/A'}
              </Col>
            </Row>
            <Row gutter={16} style={{ marginTop: 8 }}>
              <Col span={12}>
                <Text strong>Criticidad:</Text> {selectedMachine.criticality || 'N/A'}
              </Col>
              <Col span={12}>
                <Text strong>Nivel de Riesgo:</Text> 
                <Tag color={
                  selectedMachine.risk_level === 'critical' ? 'red' :
                  selectedMachine.risk_level === 'high' ? 'orange' :
                  selectedMachine.risk_level === 'medium' ? 'yellow' : 'green'
                } style={{ marginLeft: 8 }}>
                  {selectedMachine.risk_level === 'critical' ? 'Crítico' :
                   selectedMachine.risk_level === 'high' ? 'Alto' :
                   selectedMachine.risk_level === 'medium' ? 'Medio' : 'Bajo'}
                </Tag>
              </Col>
            </Row>
            
            <Divider orientation="left">Predicción Actual de IA</Divider>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>Probabilidad de Fallo:</Text> 
                <Progress 
                  percent={Math.round(selectedMachine.failure_probability || 0)} 
                  size="small" 
                  style={{ marginLeft: 8 }}
                  status={
                    (selectedMachine.failure_probability || 0) > 80 ? 'exception' :
                    (selectedMachine.failure_probability || 0) > 60 ? 'active' : 'success'
                  }
                />
              </Col>
              <Col span={12}>
                <Text strong>Confianza:</Text> {selectedMachine.confidence || 'N/A'}%
              </Col>
            </Row>
            <Row gutter={16} style={{ marginTop: 8 }}>
              <Col span={24}>
                <Text strong>Fecha Predicha:</Text> {
                  selectedMachine.predicted_date ? 
                    new Date(selectedMachine.predicted_date).toLocaleDateString() :
                    'N/A'
                }
              </Col>
            </Row>

            {selectedMachine.components_at_risk?.length > 0 && (
              <>
                <Divider orientation="left">Componentes en Riesgo</Divider>
                <div>
                  {selectedMachine.components_at_risk.map((component, idx) => (
                    <Tag key={idx} color="orange" style={{ marginBottom: 4 }}>
                      {component}
                    </Tag>
                  ))}
                </div>
              </>
            )}

            <Divider orientation="left">Historial Reciente (Datos Reales)</Divider>
            <List size="small">
              <List.Item>
                <Text strong>Fallos recientes (90 días):</Text> {selectedMachine.recent_failures || 0}
              </List.Item>
              <List.Item>
                <Text strong>Promedio Horas Parada:</Text> {selectedMachine.avg_downtime_hours || 0}h
              </List.Item>
              <List.Item>
                <Text strong>Última predicción IA:</Text> {timeAgo(selectedMachine.last_prediction)}
              </List.Item>
            </List>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Text type="secondary">Cargando detalles de la máquina...</Text>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AIDashboard;