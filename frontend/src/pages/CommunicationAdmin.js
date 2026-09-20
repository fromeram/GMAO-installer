// src/pages/CommunicationAdmin.js - VERSIÓN CORREGIDA
import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Table, 
  Tag, 
  Progress, 
  Alert, 
  Select, 
  Space,
  Typography,
  Tooltip,
  Badge,
  Button,
  List
} from 'antd';
import { 
  MessageOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  BulbOutlined,
  ToolOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { fetchWithAuth } from '../apiConfig';

const { Title, Text } = Typography;
const { Option } = Select;

const CommunicationAdmin = () => {
  const { currentUser } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentCommunications, setRecentCommunications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState(30);
  const [typeFilter, setTypeFilter] = useState(null);

  // Verificar permisos
  const isAdmin = currentUser?.role === 'Administrador' || currentUser?.role === 'Jefe de Mantenimiento';

  useEffect(() => {
    if (isAdmin) {
      loadStats();
      loadRecentCommunications();
    }
  }, [timeRange, isAdmin]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await fetchWithAuth(`/communications/admin/stats?days=${timeRange}`);
      setStats(response);
    } catch (error) {
      console.error('Error cargando estadísticas:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRecentCommunications = async () => {
    try {
      const params = new URLSearchParams();
      params.append('limit', '20');
      if (typeFilter) params.append('type_filter', typeFilter);
      
      const response = await fetchWithAuth(`/communications/admin/all?${params.toString()}`);
      setRecentCommunications(response || []);
    } catch (error) {
      console.error('Error cargando comunicaciones recientes:', error);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('es-ES', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getDaysAgo = (dateString) => {
    const days = Math.floor((new Date() - new Date(dateString)) / (1000 * 60 * 60 * 24));
    if (days === 0) return 'Hoy';
    if (days === 1) return 'Ayer';
    return `${days}d`;
  };

  // Configuración de tipos y estados
  const TYPE_CONFIG = {
    'Sugerencia': { icon: <BulbOutlined />, color: 'blue' },
    'Pedido de Material': { icon: <ToolOutlined />, color: 'orange' },
    'Queja/Problema': { icon: <ExclamationCircleOutlined />, color: 'red' },
    'Consulta': { icon: <QuestionCircleOutlined />, color: 'purple' },
    'Otro': { icon: <MessageOutlined />, color: 'default' }
  };

  const STATUS_CONFIG = {
    'Pendiente': { color: 'gold', icon: <ClockCircleOutlined /> },
    'Revisado': { color: 'blue' },
    'En Proceso': { color: 'orange' },
    'Resuelto': { color: 'green', icon: <CheckCircleOutlined /> },
    'Rechazado': { color: 'red' }
  };

  // Calcular métricas
  const getResolutionRate = () => {
    if (!stats) return 0;
    const total = stats.total_communications;
    if (total === 0) return 0;
    return Math.round((stats.resolved_count / total) * 100);
  };

  const getPendingRate = () => {
    if (!stats) return 0;
    const total = stats.total_communications;
    if (total === 0) return 0;
    return Math.round((stats.pending_count / total) * 100);
  };

  // Preparar datos para listas
  const getTypeDistribution = () => {
    if (!stats?.by_type) return [];
    return Object.entries(stats.by_type).map(([type, count]) => ({
      type,
      count,
      percentage: stats.total_communications > 0 ? Math.round((count / stats.total_communications) * 100) : 0
    }));
  };

  const getPriorityDistribution = () => {
    if (!stats?.by_priority) return [];
    return Object.entries(stats.by_priority).map(([priority, count]) => ({
      priority,
      count,
      percentage: stats.total_communications > 0 ? Math.round((count / stats.total_communications) * 100) : 0
    }));
  };

  // Columnas para la tabla
  const columns = [
    {
      title: 'Tipo',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type) => {
        const config = TYPE_CONFIG[type] || TYPE_CONFIG['Otro'];
        return (
          <Tag color={config.color} icon={config.icon} style={{ fontSize: '11px' }}>
            {type.split(' ')[0]}
          </Tag>
        );
      }
    },
    {
      title: 'Asunto',
      dataIndex: 'subject',
      key: 'subject',
      ellipsis: true,
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 500, fontSize: '13px' }}>{text}</div>
          <Text type="secondary" style={{ fontSize: '11px' }}>
            por {record.is_anonymous ? 'Anónimo' : (record.created_by_name || 'Usuario')}
          </Text>
        </div>
      )
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const config = STATUS_CONFIG[status];
        return (
          <Tag color={config.color} style={{ fontSize: '10px' }}>
            {status}
          </Tag>
        );
      }
    },
    {
      title: 'Prioridad',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority) => {
        const colors = {
          'Urgente': 'red',
          'Alta': 'orange',
          'Normal': 'blue',
          'Baja': 'gray'
        };
        return (
          <Tag color={colors[priority]} style={{ fontSize: '10px' }}>
            {priority}
          </Tag>
        );
      }
    },
    {
      title: 'Tiempo',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 60,
      render: (date) => (
        <Tooltip title={formatDate(date)}>
          <Text style={{ fontSize: '11px' }}>{getDaysAgo(date)}</Text>
        </Tooltip>
      )
    }
  ];

  if (!isAdmin) {
    return (
      <Alert
        message="Acceso Restringido"
        description="No tienes permisos para ver este dashboard administrativo."
        type="error"
        showIcon
      />
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '24px' 
      }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            Dashboard de Comunicaciones
          </Title>
          <Text type="secondary">
            Gestión y análisis de comunicaciones de operarios
          </Text>
        </div>
        
        <Space>
          <Select
            value={timeRange}
            onChange={setTimeRange}
            style={{ width: 120 }}
          >
            <Option value={7}>7 días</Option>
            <Option value={30}>30 días</Option>
            <Option value={90}>90 días</Option>
            <Option value={365}>1 año</Option>
          </Select>
          
          <Button 
            type="primary" 
            onClick={() => window.location.href = '/communications'}
          >
            Ver Todas
          </Button>
        </Space>
      </div>

      {/* Estadísticas principales */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Comunicaciones"
              value={stats?.total_communications || 0}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ marginTop: '8px' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                Últimos {timeRange} días
              </Text>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Pendientes"
              value={stats?.pending_count || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
              suffix={
                <span style={{ fontSize: '12px', color: '#666' }}>
                  ({getPendingRate()}%)
                </span>
              }
            />
            {stats?.oldest_pending_days > 0 && (
              <Text type="secondary" style={{ fontSize: '11px' }}>
                La más antigua: {stats.oldest_pending_days} días
              </Text>
            )}
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="En Proceso"
              value={stats?.in_progress_count || 0}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Resueltas"
              value={stats?.resolved_count || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={
                <span style={{ fontSize: '12px', color: '#666' }}>
                  ({getResolutionRate()}%)
                </span>
              }
            />
            {stats?.avg_resolution_time_days > 0 && (
              <Text type="secondary" style={{ fontSize: '11px' }}>
                Promedio: {stats.avg_resolution_time_days} días
              </Text>
            )}
          </Card>
        </Col>
      </Row>

      {/* Alertas importantes */}
      {stats?.pending_count > 10 && (
        <Alert
          message="Muchas Comunicaciones Pendientes"
          description={`Hay ${stats.pending_count} comunicaciones pendientes de revisión.`}
          type="warning"
          showIcon
          style={{ marginBottom: '16px' }}
        />
      )}

      <Row gutter={[16, 16]}>
        {/* Distribución por tipos */}
        <Col xs={24} lg={8}>
          <Card title="Comunicaciones por Tipo" size="small">
            <List
              size="small"
              dataSource={getTypeDistribution()}
              renderItem={(item) => (
                <List.Item>
                  <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      {TYPE_CONFIG[item.type]?.icon}
                      <span style={{ marginLeft: 8 }}>{item.type}</span>
                    </div>
                    <div>
                      <Badge count={item.count} style={{ backgroundColor: '#52c41a' }} />
                      <Text type="secondary" style={{ marginLeft: 8, fontSize: '11px' }}>
                        ({item.percentage}%)
                      </Text>
                    </div>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>

        {/* Distribución por prioridades */}
        <Col xs={24} lg={8}>
          <Card title="Distribución por Prioridad" size="small">
            <List
              size="small"
              dataSource={getPriorityDistribution()}
              renderItem={(item) => (
                <List.Item>
                  <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <span style={{ 
                        width: 12, 
                        height: 12, 
                        borderRadius: '50%', 
                        marginRight: 8,
                        backgroundColor: {
                          'Urgente': '#ff4d4f',
                          'Alta': '#fa8c16',
                          'Normal': '#1890ff',
                          'Baja': '#8c8c8c'
                        }[item.priority] || '#1890ff'
                      }} />
                      {item.priority}
                    </div>
                    <div>
                      <Badge count={item.count} style={{ backgroundColor: '#52c41a' }} />
                      <Text type="secondary" style={{ marginLeft: 8, fontSize: '11px' }}>
                        ({item.percentage}%)
                      </Text>
                    </div>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>

        {/* Métricas de rendimiento */}
        <Col xs={24} lg={8}>
          <Card title="Rendimiento del Equipo" size="small">
            <div style={{ marginBottom: '16px' }}>
              <Text strong>Tasa de Resolución</Text>
              <Progress 
                percent={getResolutionRate()} 
                strokeColor={getResolutionRate() > 80 ? '#52c41a' : getResolutionRate() > 60 ? '#faad14' : '#ff4d4f'}
                size="small"
              />
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <Text strong>Tiempo Promedio de Resolución</Text>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#1890ff' }}>
                {stats?.avg_resolution_time_days || 0} días
              </div>
            </div>

            <div>
              <Text strong>Comunicación más antigua</Text>
              <div style={{ 
                fontSize: '16px', 
                fontWeight: 'bold', 
                color: stats?.oldest_pending_days > 7 ? '#ff4d4f' : '#52c41a' 
              }}>
                {stats?.oldest_pending_days || 0} días
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Tabla de comunicaciones recientes */}
      <Card 
        title="Comunicaciones Recientes" 
        size="small" 
        style={{ marginTop: '16px' }}
        extra={
          <Space>
            <Select
              placeholder="Filtrar por tipo"
              allowClear
              style={{ width: 150 }}
              value={typeFilter}
              onChange={setTypeFilter}
              size="small"
            >
              <Option value="Sugerencia">Sugerencia</Option>
              <Option value="Pedido de Material">Pedido Material</Option>
              <Option value="Queja/Problema">Queja/Problema</Option>
              <Option value="Consulta">Consulta</Option>
              <Option value="Otro">Otro</Option>
            </Select>
            
            <Button 
              size="small" 
              onClick={loadRecentCommunications}
            >
              Actualizar
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={recentCommunications}
          rowKey="id"
          loading={loading}
          size="small"
          pagination={{
            pageSize: 10,
            size: 'small',
            showSizeChanger: false
          }}
          scroll={{ x: 600 }}
        />
      </Card>

      {/* Acciones rápidas */}
      <Card title="Acciones Rápidas" size="small" style={{ marginTop: '16px' }}>
        <Space wrap>
          <Button type="primary">Ver Pendientes</Button>
          <Button>Ver Urgentes</Button>
          <Button>Pedidos de Material</Button>
          <Button>Sugerencias</Button>
        </Space>
      </Card>
    </div>
  );
};

export default CommunicationAdmin;