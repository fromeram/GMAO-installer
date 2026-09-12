// frontend/src/pages/AuditTrail.js - VERSIÓN COMPLETA CON LIMPIEZA Y ORDENAMIENTO POR FECHA
import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Card, 
  Typography, 
  Space, 
  Tag, 
  DatePicker, 
  Select, 
  Button, 
  Modal,
  Descriptions,
  Alert,
  Spin,
  Row,
  Col,
  Statistic,
  message
} from 'antd';
import { 
  EyeOutlined, 
  FilterOutlined, 
  ReloadOutlined,
  UserOutlined,
  ClockCircleOutlined,
  SecurityScanOutlined,
  DeleteOutlined,
  WarningOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import dayjs from 'dayjs';
import { useAuth } from '../contexts/AuthContext';
import '../styles/CommonPage.css';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

// COMPONENTE DE LIMPIEZA DE AUDIT TRAIL
const AuditCleanupPanel = ({ onRefresh }) => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);

  // Cargar estadísticas
  const loadStats = async () => {
    setStatsLoading(true);
    try {
      const response = await fetchWithAuth('/audit-trail/storage-stats');
      setStats(response);
    } catch (error) {
      console.error('Error cargando estadísticas:', error);
      message.error('Error cargando estadísticas');
    } finally {
      setStatsLoading(false);
    }
  };

  // Limpieza general
  const handleGeneralCleanup = (days, dryRun = true) => {
    Modal.confirm({
      title: `${dryRun ? 'Vista Previa' : 'Confirmar'} Limpieza General`,
      content: `¿${dryRun ? 'Ver qué se eliminaría' : 'Eliminar realmente'} registros más antiguos que ${days} días?`,
      icon: <WarningOutlined />,
      okText: dryRun ? 'Ver Vista Previa' : 'Sí, Eliminar',
      okType: dryRun ? 'default' : 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        setLoading(true);
        try {
          const response = await fetchWithAuth(
            `/audit-trail/cleanup?days=${days}&dry_run=${dryRun}`, 
            { method: 'DELETE' }
          );
          
          if (response.success) {
            if (dryRun) {
              Modal.info({
                title: 'Vista Previa de Limpieza',
                content: (
                  <div>
                    <p>{response.message}</p>
                    <p>Registros a eliminar: <strong>{response.would_delete_count}</strong></p>
                    {Object.keys(response.module_stats || {}).length > 0 && (
                      <div>
                        <p>Por módulo:</p>
                        <ul>
                          {Object.entries(response.module_stats).map(([module, count]) => (
                            <li key={module}>{module}: {count}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ),
                onOk: () => {
                  Modal.confirm({
                    title: '¿Proceder con la eliminación?',
                    content: '¿Quieres eliminar estos registros ahora?',
                    okText: 'Sí, Eliminar',
                    okType: 'danger',
                    onOk: () => handleGeneralCleanup(days, false)
                  });
                }
              });
            } else {
              message.success(response.message);
              onRefresh();
              loadStats();
            }
          } else {
            message.error(response.error || 'Error en la limpieza');
          }
        } catch (error) {
          console.error('Error ejecutando limpieza:', error);
          message.error('Error ejecutando limpieza');
        } finally {
          setLoading(false);
        }
      }
    });
  };

  // Limpieza de LOGIN logs
  const handleLoginCleanup = (days, dryRun = true) => {
    Modal.confirm({
      title: `${dryRun ? 'Vista Previa' : 'Confirmar'} Limpieza de LOGIN`,
      content: `¿${dryRun ? 'Ver qué se eliminaría' : 'Eliminar realmente'} registros de LOGIN/LOGIN_FAILED más antiguos que ${days} días?`,
      icon: <WarningOutlined />,
      okText: dryRun ? 'Ver Vista Previa' : 'Sí, Eliminar',
      okType: dryRun ? 'default' : 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        setLoading(true);
        try {
          // Construir la URL correctamente para múltiples parámetros actions
          const actions = ['LOGIN', 'LOGIN_FAILED'];
          const actionsParams = actions.map(action => `actions=${action}`).join('&');
          const url = `/audit-trail/cleanup-by-action?${actionsParams}&days=${days}&dry_run=${dryRun}`;
          
          const response = await fetchWithAuth(url, { method: 'DELETE' });
          
          if (response.success) {
            if (dryRun) {
              Modal.info({
                title: 'Vista Previa de Limpieza LOGIN',
                content: (
                  <div>
                    <p>{response.message}</p>
                    <p>Registros a eliminar: <strong>{response.would_delete_count}</strong></p>
                  </div>
                ),
                onOk: () => {
                  Modal.confirm({
                    title: '¿Proceder con la eliminación?',
                    content: '¿Quieres eliminar estos registros de LOGIN ahora?',
                    okText: 'Sí, Eliminar',
                    okType: 'danger',
                    onOk: () => handleLoginCleanup(days, false)
                  });
                }
              });
            } else {
              message.success(response.message);
              onRefresh();
              loadStats();
            }
          } else {
            message.error(response.error || 'Error en la limpieza');
          }
        } catch (error) {
          console.error('Error ejecutando limpieza de LOGIN:', error);
          message.error('Error ejecutando limpieza de LOGIN');
        } finally {
          setLoading(false);
        }
      }
    });
  };

  useEffect(() => {
    loadStats();
  }, []);

  return (
    <Card 
      title={
        <Space>
          <DatabaseOutlined />
          <span>Gestión de Almacenamiento - Audit Trail</span>
        </Space>
      }
      size="small" 
      style={{ marginBottom: 16 }}
      extra={
        <Button 
          size="small" 
          onClick={loadStats} 
          loading={statsLoading}
        >
          Actualizar
        </Button>
      }
    >
      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Statistic 
              title="Total Registros" 
              value={stats.total_records} 
              prefix={<DatabaseOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Últimos 30 días" 
              value={stats.age_distribution.last_30_days}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="90-365 días" 
              value={stats.age_distribution['90_to_365_days']}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Más de 1 año" 
              value={stats.age_distribution.older_than_365_days}
              valueStyle={{ color: '#cf1322' }}
            />
          </Col>
        </Row>
      )}
      
      <Space wrap>
  <Button 
    icon={<DeleteOutlined />}
    onClick={() => handleLoginCleanup(1)}
    loading={loading}
    size="small"
  >
    LOGIN (1 día)
  </Button>
  
  <Button 
    icon={<DeleteOutlined />}
    onClick={() => handleLoginCleanup(3)}
    loading={loading}
    size="small"
  >
    LOGIN (3 días)
  </Button>
  
  <Button 
    icon={<DeleteOutlined />}
    onClick={() => handleLoginCleanup(7)}
    loading={loading}
    size="small"
  >
    LOGIN (1 semana)
  </Button>
  
  <Button 
    icon={<DeleteOutlined />}
    onClick={() => handleLoginCleanup(30)}
    loading={loading}
  >
    LOGIN (1 mes)
  </Button>
  
  <Button 
    icon={<DeleteOutlined />}
    onClick={() => handleGeneralCleanup(30)}
    loading={loading}
    type="primary"
  >
    General (1 mes)
  </Button>
  
  <Button 
    icon={<DeleteOutlined />}
    onClick={() => handleGeneralCleanup(90)}
    loading={loading}
  >
    General (3 meses)
  </Button>
  
  <Button 
    icon={<DeleteOutlined />}
    onClick={() => handleGeneralCleanup(365)}
    loading={loading}
    type="primary"
    danger
  >
    General (1 año)
  </Button>
</Space>
      
      {stats?.recommendations?.suggested_cleanup && (
        <Alert
          message="Recomendación"
          description={stats.recommendations.suggested_cleanup}
          type="info"
          showIcon
          style={{ marginTop: 16 }}
        />
      )}
    </Card>
  );
};

// COMPONENTE PRINCIPAL AUDIT TRAIL
const AuditTrail = () => {
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [selectedLog, setSelectedLog] = useState(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [filters, setFilters] = useState({
    entity_type: null,
    action: null,
    module: null,
    severity: null,
    user_id: null,
    start_date: null,
    end_date: null
  });

  const { currentUser } = useAuth();

  // Opciones para filtros
  const entityTypes = ['WorkOrder', 'Machine', 'User', 'Inventory', 'Maintenance', 'Supplier'];
  const actions = ['CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'COMPLETE', 'STATUS_CHANGE', 'EXPORT'];
  const modules = ['maintenance', 'assets', 'users', 'inventory', 'documents', 'authentication'];
  const severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

  // Cargar datos
  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      
      Object.keys(filters).forEach(key => {
        if (filters[key] !== null && filters[key] !== undefined) {
          if (key === 'start_date' || key === 'end_date') {
            params.append(key, filters[key]);
          } else {
            params.append(key, filters[key]);
          }
        }
      });

      const [logsResponse, statsResponse] = await Promise.all([
        fetchWithAuth(`/audit-trail?${params.toString()}`),
        fetchWithAuth('/audit-trail/stats?days=7')
      ]);

      // Ordenar por fecha más reciente primero
      const sortedLogs = (logsResponse || []).sort((a, b) => 
        new Date(b.timestamp) - new Date(a.timestamp)
      );

      setAuditLogs(sortedLogs);
      setStats(statsResponse);
    } catch (error) {
      console.error('Error cargando audit trail:', error);
      message.error('Error cargando datos del audit trail');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  // Aplicar filtros
  const applyFilters = () => {
    fetchAuditLogs();
  };

  // Limpiar filtros
  const clearFilters = () => {
    setFilters({
      entity_type: null,
      action: null,
      module: null,
      severity: null,
      user_id: null,
      start_date: null,
      end_date: null
    });
    setTimeout(() => fetchAuditLogs(), 100);
  };

  // Ver detalles de un log
  const viewDetails = async (logId) => {
    try {
      const details = await fetchWithAuth(`/audit-trail/${logId}`);
      setSelectedLog(details);
      setDetailModalVisible(true);
    } catch (error) {
      console.error('Error cargando detalles:', error);
      message.error('Error cargando detalles del registro');
    }
  };

  // Formatear timestamp
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    
    // Formatear usando las opciones de localización españolas
    return new Intl.DateTimeFormat('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZone: 'Europe/Madrid' // Forzar zona horaria de Madrid
    }).format(date);
  };


  // Obtener color por severidad
  const getSeverityColor = (severity) => {
    const colors = {
      'LOW': 'green',
      'MEDIUM': 'blue',
      'HIGH': 'orange',
      'CRITICAL': 'red'
    };
    return colors[severity] || 'default';
  };

  // Obtener icono por acción
  const getActionIcon = (action) => {
    const icons = {
      'CREATE': '➕',
      'UPDATE': '✏️',
      'DELETE': '🗑️',
      'LOGIN': '🔐',
      'COMPLETE': '✅',
      'STATUS_CHANGE': '🔄',
      'EXPORT': '📄'
    };
    return icons[action] || '📝';
  };

  // Columnas de la tabla
  const columns = [
    {
      title: 'Fecha/Hora',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 150,
      defaultSortOrder: 'descend',
      render: (timestamp) => (
        <div>
          <div>{dayjs(timestamp).format('DD/MM/YYYY')}</div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {dayjs(timestamp).format('HH:mm:ss')}
          </Text>
        </div>
      ),
      sorter: (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
    },
    {
      title: 'Usuario',
      dataIndex: 'user_name',
      key: 'user_name',
      width: 120,
      render: (user_name, record) => (
        <div>
          <UserOutlined /> {user_name}
          {record.user_role && (
            <div>
              <Tag size="small" color="blue">{record.user_role}</Tag>
            </div>
          )}
        </div>
      )
    },
    {
      title: 'Acción',
      dataIndex: 'action',
      key: 'action',
      width: 100,
      render: (action) => (
        <Tag color="purple">
          {getActionIcon(action)} {action}
        </Tag>
      )
    },
    {
      title: 'Entidad',
      key: 'entity',
      width: 150,
      render: (_, record) => (
        <div>
          <Text strong>{record.entity_type}</Text>
          {record.entity_id && (
            <div>
              <Text type="secondary">ID: {record.entity_id}</Text>
            </div>
          )}
        </div>
      )
    },
    {
      title: 'Descripción',
      dataIndex: 'changes_summary',
      key: 'changes_summary',
      ellipsis: true,
      render: (summary) => (
        <Text>{summary || 'Sin descripción'}</Text>
      )
    },
    {
      title: 'Módulo',
      dataIndex: 'module',
      key: 'module',
      width: 100,
    },
    {
      title: 'Severidad',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity) => (
        <Tag color={getSeverityColor(severity)}>
          {severity}
        </Tag>
      )
    },
    {
      title: 'IP',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 120,
      render: (ip) => (
        <Text code style={{ fontSize: '11px' }}>
          {ip || 'N/A'}
        </Text>
      )
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Button 
          type="link" 
          icon={<EyeOutlined />} 
          onClick={() => viewDetails(record.id)}
          size="small"
        >
          Ver
        </Button>
      )
    }
  ];

  return (
    <div className="page-container">
      <Title level={2} className="page-title">
        <SecurityScanOutlined /> Audit Trail - Registro de Auditoría
      </Title>

      {/* Panel de limpieza - Solo para Administradores */}
      {currentUser?.role === 'Administrador' && (
        <AuditCleanupPanel onRefresh={fetchAuditLogs} />
      )}

      {/* Estadísticas rápidas */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card size="small">
              <Statistic 
                title="Total Acciones (7 días)" 
                value={stats.total_actions} 
                prefix={<ClockCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic 
                title="Usuarios Activos" 
                value={stats.top_users?.length || 0} 
                prefix={<UserOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic 
                title="Acciones Críticas" 
                value={stats.actions_by_severity?.find(s => s.severity === 'CRITICAL')?.count || 0}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic 
                title="Módulos Activos" 
                value={stats.actions_by_module?.length || 0}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Filtros */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Title level={4}>
          <FilterOutlined /> Filtros
        </Title>
        
        <Row gutter={16}>
          <Col span={4}>
            <Select
              placeholder="Tipo Entidad"
              value={filters.entity_type}
              onChange={(value) => setFilters({...filters, entity_type: value})}
              allowClear
              style={{ width: '100%' }}
            >
              {entityTypes.map(type => (
                <Option key={type} value={type}>{type}</Option>
              ))}
            </Select>
          </Col>
          
          <Col span={4}>
            <Select
              placeholder="Acción"
              value={filters.action}
              onChange={(value) => setFilters({...filters, action: value})}
              allowClear
              style={{ width: '100%' }}
            >
              {actions.map(action => (
                <Option key={action} value={action}>{action}</Option>
              ))}
            </Select>
          </Col>
          
          <Col span={4}>
            <Select
              placeholder="Módulo"
              value={filters.module}
              onChange={(value) => setFilters({...filters, module: value})}
              allowClear
              style={{ width: '100%' }}
            >
              {modules.map(module => (
                <Option key={module} value={module}>{module}</Option>
              ))}
            </Select>
          </Col>
          
          <Col span={4}>
            <Select
              placeholder="Severidad"
              value={filters.severity}
              onChange={(value) => setFilters({...filters, severity: value})}
              allowClear
              style={{ width: '100%' }}
            >
              {severities.map(severity => (
                <Option key={severity} value={severity}>{severity}</Option>
              ))}
            </Select>
          </Col>
          
          <Col span={6}>
            <RangePicker
              placeholder={['Fecha inicio', 'Fecha fin']}
              onChange={(dates, dateStrings) => {
                setFilters({
                  ...filters,
                  start_date: dateStrings[0] || null,
                  end_date: dateStrings[1] || null
                });
              }}
              style={{ width: '100%' }}
            />
          </Col>
          
          <Col span={2}>
            <Space>
              <Button type="primary" onClick={applyFilters}>
                Aplicar
              </Button>
              <Button onClick={clearFilters}>
                Limpiar
              </Button>
              <Button icon={<ReloadOutlined />} onClick={fetchAuditLogs} />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Tabla de audit logs */}
      <Card>
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={auditLogs}
            rowKey="id"
            pagination={{
              pageSize: 50,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                `${range[0]}-${range[1]} de ${total} registros`
            }}
            size="small"
            scroll={{ x: 1200 }}
          />
        </Spin>
      </Card>

      {/* Modal de detalles */}
      <Modal
        title="Detalles del Registro de Auditoría"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedLog && (
          <div>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="ID">{selectedLog.id}</Descriptions.Item>
              <Descriptions.Item label="Acción">
                <Tag color="purple">{selectedLog.action}</Tag>
              </Descriptions.Item>
              
              <Descriptions.Item label="Usuario">{selectedLog.user_name}</Descriptions.Item>
              <Descriptions.Item label="Rol">{selectedLog.user_role}</Descriptions.Item>
              
              <Descriptions.Item label="Entidad">{selectedLog.entity_type}</Descriptions.Item>
              <Descriptions.Item label="ID Entidad">{selectedLog.entity_id}</Descriptions.Item>
              
              <Descriptions.Item label="Fecha/Hora" span={2}>
                {formatTimestamp(selectedLog.timestamp)}
              </Descriptions.Item>
              
              <Descriptions.Item label="IP">{selectedLog.ip_address}</Descriptions.Item>
              <Descriptions.Item label="Severidad">
                <Tag color={getSeverityColor(selectedLog.severity)}>
                  {selectedLog.severity}
                </Tag>
              </Descriptions.Item>
              
              <Descriptions.Item label="Módulo">{selectedLog.module}</Descriptions.Item>
              <Descriptions.Item label="Sesión">{selectedLog.session_id}</Descriptions.Item>
            </Descriptions>

            {selectedLog.changes_summary && (
              <Alert
                message="Resumen de Cambios"
                description={selectedLog.changes_summary}
                type="info"
                style={{ margin: '16px 0' }}
              />
            )}

            {selectedLog.notes && (
              <Alert
                message="Notas"
                description={selectedLog.notes}
                type="warning"
                style={{ margin: '16px 0' }}
              />
            )}

            {selectedLog.old_values && (
              <div style={{ marginTop: 16 }}>
                <Title level={5}>Valores Anteriores:</Title>
                <pre style={{ background: '#f5f5f5', padding: 8, fontSize: '12px' }}>
                  {JSON.stringify(selectedLog.old_values, null, 2)}
                </pre>
              </div>
            )}

            {selectedLog.new_values && (
              <div style={{ marginTop: 16 }}>
                <Title level={5}>Valores Nuevos:</Title>
                <pre style={{ background: '#f5f5f5', padding: 8, fontSize: '12px' }}>
                  {JSON.stringify(selectedLog.new_values, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AuditTrail;