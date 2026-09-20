// src/pages/FormatChangesList.js - Lista de Órdenes de Cambio de Formato (CORREGIDA)
import React, { useState, useEffect } from 'react';
import { 
  Table, Button, Modal, message, Space, Tag, Card, Typography, 
  Select, DatePicker, Progress, Tooltip, Alert, Statistic, Row, Col 
} from 'antd';
import { 
  PlusOutlined, EditOutlined, EyeOutlined, SettingOutlined,
  ClockCircleOutlined, ToolOutlined, GlobalOutlined, 
  ApartmentOutlined, CheckCircleOutlined, ExclamationCircleOutlined 
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import FormatChangeForm from '../components/FormatChangeForm';
import dayjs from 'dayjs';
import FormatOrderUpdateModal from '../components/FormatOrderUpdateModal';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const FormatChangesList = () => {
  const [orders, setOrders] = useState([]);
  const [filteredOrders, setFilteredOrders] = useState([]);
  const [sections, setSections] = useState([]);
  const [users, setUsers] = useState([]);
  const [machines, setMachines] = useState([]); // ✅ AÑADIR estado para máquinas
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingOrder, setEditingOrder] = useState(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const { currentUser } = useAuth();
  const [updateModalVisible, setUpdateModalVisible] = useState(false);
  const [updatingOrder, setUpdatingOrder] = useState(null);

  // Estados para filtros
  const [filters, setFilters] = useState({
    status: 'all',
    changeType: 'all',
    section: 'all',
    dateRange: null
  });

  // Estados para métricas
  const [metrics, setMetrics] = useState({
    total: 0,
    pending: 0,
    completed: 0,
    avgEfficiency: 0
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    applyFilters();
    calculateMetrics();
  }, [orders, filters]);

  const loadData = async () => {
    try {
      const [ordersData, sectionsData, usersData, machinesData] = await Promise.all([
        fetchWithAuth('/ordenes'), // Todas las órdenes - filtraremos las de formato
        fetchWithAuth('/secciones'),
        fetchWithAuth('/users'),
        fetchWithAuth('/maquinas') // ✅ CARGAR datos de máquinas
      ]);
      
      // Filtrar solo órdenes de cambio de formato
      const formatOrders = (ordersData || []).filter(order => 
        ['Cambio de Formato', 'Setup de Línea', 'Cambio Global de Planta'].includes(order.work_type)
      );
      
      setOrders(formatOrders);
      setSections(sectionsData || []);
      setUsers(usersData || []);
      setMachines(machinesData || []); // ✅ GUARDAR datos de máquinas
    } catch (error) {
      console.error('Error cargando datos:', error);
      message.error('Error al cargar los datos');
    } finally {
      setLoading(false);
    }
  };

  // ✅ FUNCIÓN AUXILIAR para obtener nombres de máquinas por IDs
  const getMachineNames = (machineIds) => {
    if (!machineIds || !Array.isArray(machineIds) || machineIds.length === 0) {
      return [];
    }
    
    return machineIds.map(id => {
      const machine = machines.find(m => m.id === id);
      return machine ? machine.nombre : `Máquina #${id}`;
    });
  };

  // ✅ FUNCIÓN AUXILIAR para obtener nombre de una máquina por ID
  const getMachineName = (machineId) => {
    if (!machineId) return null;
    const machine = machines.find(m => m.id === machineId);
    return machine ? machine.nombre : `Máquina #${machineId}`;
  };

  const applyFilters = () => {
    let filtered = [...orders];

    // Filtro por estado
    if (filters.status !== 'all') {
      filtered = filtered.filter(order => order.status === filters.status);
    }

    // Filtro por tipo de cambio
    if (filters.changeType !== 'all') {
      filtered = filtered.filter(order => order.format_change_type === filters.changeType);
    }

    // Filtro por sección
    if (filters.section !== 'all') {
      filtered = filtered.filter(order => order.section_id === parseInt(filters.section));
    }

    // Filtro por rango de fechas
    if (filters.dateRange && filters.dateRange.length === 2) {
      const [start, end] = filters.dateRange;
      filtered = filtered.filter(order => {
        const orderDate = dayjs(order.created_at);
        return orderDate.isAfter(start) && orderDate.isBefore(end.add(1, 'day'));
      });
    }

    setFilteredOrders(filtered);
  };

  const calculateMetrics = () => {
    const total = filteredOrders.length;
    const pending = filteredOrders.filter(o => ['Pendiente', 'En curso'].includes(o.status)).length;
    const completed = filteredOrders.filter(o => o.status === 'Cerrada').length;
    
    // Calcular eficiencia promedio para órdenes completadas
    const completedWithEfficiency = filteredOrders.filter(o => 
      o.status === 'Cerrada' && o.setup_efficiency
    );
    const avgEfficiency = completedWithEfficiency.length > 0
      ? completedWithEfficiency.reduce((sum, o) => sum + o.setup_efficiency, 0) / completedWithEfficiency.length
      : 0;

    setMetrics({ total, pending, completed, avgEfficiency });
  };

  const handleSubmit = async (orderData) => {
    try {
      const url = editingOrder 
        ? `/work-orders/${editingOrder.id}/format-change`
        : '/work-orders/format-change';
      const method = editingOrder ? 'PUT' : 'POST';

      await fetchWithAuth(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
      });

      message.success(`Orden ${editingOrder ? 'actualizada' : 'creada'} correctamente`);
      setModalVisible(false);
      setEditingOrder(null);
      loadData();
    } catch (error) {
      console.error('Error:', error);
      message.error(error.message || 'Error al guardar la orden');
    }
  };


  const handleOrderUpdate = async (orderId, updateData) => {
  try {
    await fetchWithAuth(`/work-orders/${orderId}/format-change`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updateData)
    });
    
    message.success('Orden actualizada correctamente');
    setUpdateModalVisible(false);
    setUpdatingOrder(null);
    loadData(); // Recargar datos para ver los cambios
  } catch (error) {
    console.error('Error:', error);
    message.error('Error al actualizar la orden');
  }
};

  const showDetail = (order) => {
    setSelectedOrder(order);
    setDetailModalVisible(true);
  };

  const getChangeTypeIcon = (type) => {
    switch (type) {
      case 'Individual': return <ToolOutlined />;
      case 'Línea': return <ApartmentOutlined />;
      case 'Global': return <GlobalOutlined />;
      default: return <SettingOutlined />;
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'Pendiente': 'gold',
      'En curso': 'blue',
      'En revisión': 'purple',
      'Cerrada': 'green'
    };
    return colors[status] || 'default';
  };

  const getEfficiencyColor = (efficiency) => {
    if (efficiency >= 100) return 'success';
    if (efficiency >= 80) return 'normal';
    if (efficiency >= 60) return 'exception';
    return 'exception';
  };

  const columns = [
    {
      title: 'Orden',
      dataIndex: 'order_number',
      key: 'order_number',
      fixed: 'left',
      width: 120,
      render: (text, record) => (
        <Button 
          type="link" 
          onClick={() => showDetail(record)}
          style={{ padding: 0, fontWeight: 'bold' }}
        >
          {text || `FC-${record.id}`}
        </Button>
      )
    },
    {
      title: 'Título',
      dataIndex: 'title',
      key: 'title',
      width: 250,
      ellipsis: true
    },
    {
      title: 'Tipo de Cambio',
      dataIndex: 'format_change_type',
      key: 'format_change_type',
      width: 150,
      render: (type) => (
        <Tag icon={getChangeTypeIcon(type)} color="blue">
          {type || 'No especificado'}
        </Tag>
      )
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => (
        <Tag color={getStatusColor(status)}>{status}</Tag>
      )
    },
    {
      title: 'Formatos',
      key: 'formats',
      width: 200,
      render: (_, record) => (
        <div>
          {record.format_from_name && (
            <div><Text type="secondary">De:</Text> {record.format_from_name}</div>
          )}
          {record.format_to_name && (
            <div><Text type="secondary">A:</Text> {record.format_to_name}</div>
          )}
          {!record.format_from_name && !record.format_to_name && (
            <Text type="secondary">Sin especificar</Text>
          )}
        </div>
      )
    },
    {
      title: 'Máquinas', // ✅ COLUMNA MEJORADA
      key: 'machines',
      width: 200,
      render: (_, record) => {
        if (record.affected_machines && record.affected_machines.length > 0) {
          const machineNames = getMachineNames(record.affected_machines);
          return (
            <div>
              <Tag color="cyan">
                {record.affected_machines.length} máquinas
              </Tag>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                {machineNames.join(', ')}
              </div>
            </div>
          );
        } else if (record.machine_id) {
          const machineName = getMachineName(record.machine_id);
          return (
            <div>
              <Tag color="blue">1 máquina</Tag>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                {machineName}
              </div>
            </div>
          );
        } else {
          return <Text type="secondary">Sin especificar</Text>;
        }
      }
    },
    {
      title: 'Tiempo Setup',
      key: 'setup_time',
      width: 150,
      render: (_, record) => (
        <div>
          {record.estimated_setup_duration && (
            <div>
              <ClockCircleOutlined /> Est: {record.estimated_setup_duration}h
            </div>
          )}
          {record.setup_duration && (
            <div>
              <CheckCircleOutlined style={{ color: 'green' }} /> Real: {record.setup_duration}h
            </div>
          )}
        </div>
      )
    },
    {
      title: 'Eficiencia',
      key: 'efficiency',
      width: 120,
      render: (_, record) => {
        if (!record.setup_efficiency) return '-';
        
        return (
          <Progress
            type="circle"
            size={50}
            percent={Math.min(record.setup_efficiency, 150)}
            status={getEfficiencyColor(record.setup_efficiency)}
            format={() => `${record.setup_efficiency.toFixed(0)}%`}
          />
        );
      }
    },
    {
      title: 'Sección',
      dataIndex: ['section', 'nombre'],
      key: 'section',
      width: 120,
      ellipsis: true
    },
    {
      title: 'Técnico',
      dataIndex: ['assigned_to', 'username'],
      key: 'assigned_to',
      width: 120,
      ellipsis: true
    },
    {
      title: 'Fecha',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date) => dayjs(date).format('DD/MM/YYYY')
    },
    {
      title: 'Acciones',
      key: 'actions',
      fixed: 'right',
      width: 120,
      render: (_, record) => (
        <Space>
          <Tooltip title="Ver detalles">
            <Button 
              icon={<EyeOutlined />} 
              onClick={() => showDetail(record)}
              size="small"
            />
          </Tooltip>
          <Tooltip title="Editar">
            <Button 
              icon={<EditOutlined />} 
              onClick={() => {
                setEditingOrder(record);
                setModalVisible(true);
              }}
              size="small"
              type="primary"
            />
          </Tooltip>
          {/* ✅ AGREGAR ESTE NUEVO BOTÓN */}
          <Tooltip title="Completar/Actualizar">
            <Button 
              icon={<CheckCircleOutlined />}
              onClick={() => {
                setUpdatingOrder(record);
                setUpdateModalVisible(true);
              }}
              size="small"
              type={record.status === 'Cerrada' ? 'default' : 'primary'}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>Órdenes de Cambio de Formato</Title>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={() => {
            setEditingOrder(null);
            setModalVisible(true);
          }}
        >
          Nueva Orden de Formato
        </Button>
      </div>

      {/* Métricas */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic 
              title="Total de Órdenes" 
              value={metrics.total} 
              prefix={<SettingOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="Pendientes" 
              value={metrics.pending} 
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="Completadas" 
              value={metrics.completed} 
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="Eficiencia Promedio" 
              value={metrics.avgEfficiency} 
              precision={1}
              suffix="%" 
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: metrics.avgEfficiency >= 100 ? '#52c41a' : '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Filtros */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col span={4}>
            <Text strong>Filtros:</Text>
          </Col>
          <Col span={4}>
            <Select
              style={{ width: '100%' }}
              placeholder="Estado"
              value={filters.status}
              onChange={(value) => setFilters({...filters, status: value})}
            >
              <Option value="all">Todos los estados</Option>
              <Option value="Pendiente">Pendiente</Option>
              <Option value="En curso">En curso</Option>
              <Option value="En revisión">En revisión</Option>
              <Option value="Cerrada">Cerrada</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              style={{ width: '100%' }}
              placeholder="Tipo de cambio"
              value={filters.changeType}
              onChange={(value) => setFilters({...filters, changeType: value})}
            >
              <Option value="all">Todos los tipos</Option>
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
            >
              <Option value="all">Todas las secciones</Option>
              {sections.map(section => (
                <Option key={section.id} value={section.id.toString()}>
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
              onChange={(dates) => setFilters({...filters, dateRange: dates})}
            />
          </Col>
          <Col span={2}>
            <Button 
              onClick={() => setFilters({
                status: 'all',
                changeType: 'all', 
                section: 'all',
                dateRange: null
              })}
            >
              Limpiar
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Tabla */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredOrders}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1800 }}
          pagination={{ 
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `Total: ${total} órdenes`
          }}
        />
      </Card>

      {/* Modal de Formulario */}
      <Modal
        title={editingOrder ? 'Editar Orden de Cambio' : 'Nueva Orden de Cambio de Formato'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingOrder(null);
        }}
        footer={null}
        width={1200}
        destroyOnClose
      >
        {modalVisible && (
          <FormatChangeForm
            sections={sections}
            users={users}
            machines={machines} // ✅ PASAR máquinas al formulario
            onSubmit={handleSubmit}
            preloadedData={editingOrder}
          />
        )}
      </Modal>

      {/* Modal de Detalle MEJORADO */}
      <Modal
        title={`Detalle de Orden de Cambio - ${selectedOrder?.order_number || selectedOrder?.id}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            Cerrar
          </Button>,
          <Button 
            key="edit" 
            type="primary" 
            icon={<EditOutlined />}
            onClick={() => {
              setDetailModalVisible(false);
              setEditingOrder(selectedOrder);
              setModalVisible(true);
            }}
          >
            Editar
          </Button>
        ]}
        width={800}
      >
        {selectedOrder && (
          <div>
            {/* Información básica */}
            <Card title="Información Básica" size="small" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Text strong>Título:</Text> {selectedOrder.title}
                </Col>
                <Col span={12}>
                  <Text strong>Tipo:</Text> {selectedOrder.work_type}
                </Col>
                <Col span={12} style={{ marginTop: 8 }}>
                  <Text strong>Tipo de Cambio:</Text> 
                  <Tag icon={getChangeTypeIcon(selectedOrder.format_change_type)} color="blue" style={{ marginLeft: 8 }}>
                    {selectedOrder.format_change_type}
                  </Tag>
                </Col>
                <Col span={12} style={{ marginTop: 8 }}>
                  <Text strong>Estado:</Text> 
                  <Tag color={getStatusColor(selectedOrder.status)} style={{ marginLeft: 8 }}>
                    {selectedOrder.status}
                  </Tag>
                </Col>
              </Row>
            </Card>

            {/* Formatos */}
            {(selectedOrder.format_from_name || selectedOrder.format_to_name) && (
              <Card title="Formatos" size="small" style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                  <Col span={12}>
                    <Text strong>Formato Origen:</Text><br />
                    {selectedOrder.format_from_name || 'No especificado'}
                  </Col>
                  <Col span={12}>
                    <Text strong>Formato Destino:</Text><br />
                    {selectedOrder.format_to_name || 'No especificado'}
                  </Col>
                </Row>
              </Card>
            )}

            {/* Tiempos y Eficiencia */}
            <Card title="Tiempos y Eficiencia" size="small" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Text strong>Tiempo Estimado:</Text><br />
                  {selectedOrder.estimated_setup_duration ? `${selectedOrder.estimated_setup_duration} horas` : 'No especificado'}
                </Col>
                <Col span={8}>
                  <Text strong>Tiempo Real:</Text><br />
                  {selectedOrder.setup_duration ? `${selectedOrder.setup_duration} horas` : 'Pendiente'}
                </Col>
                <Col span={8}>
                  <Text strong>Eficiencia:</Text><br />
                  {selectedOrder.setup_efficiency ? (
                    <Progress
                      percent={Math.min(selectedOrder.setup_efficiency, 150)}
                      status={getEfficiencyColor(selectedOrder.setup_efficiency)}
                      format={() => `${selectedOrder.setup_efficiency.toFixed(1)}%`}
                    />
                  ) : 'Pendiente'}
                </Col>
              </Row>
            </Card>

            {/* Máquinas Afectadas - MEJORADO */}
            <Card title="Máquinas Afectadas" size="small" style={{ marginBottom: 16 }}>
              {selectedOrder.affected_machines && selectedOrder.affected_machines.length > 0 ? (
                <div>
                  <Text>Total de máquinas: </Text>
                  <Tag color="cyan">{selectedOrder.affected_machines.length}</Tag>
                  <br />
                  <div style={{ marginTop: 8 }}>
                    <Text strong>Máquinas:</Text>
                    <div style={{ marginTop: 4 }}>
                      {getMachineNames(selectedOrder.affected_machines).map((name, index) => (
                        <Tag key={index} color="blue" style={{ marginBottom: 4 }}>
                          {name}
                        </Tag>
                      ))}
                    </div>
                  </div>
                </div>
              ) : selectedOrder.machine_id ? (
                <div>
                  <Text>Máquina individual: </Text>
                  <Tag color="blue">{getMachineName(selectedOrder.machine_id)}</Tag>
                </div>
              ) : (
                <Text type="secondary">No se especificaron máquinas</Text>
              )}
            </Card>

            {/* Notas */}
            {(selectedOrder.setup_notes || selectedOrder.details) && (
              <Card title="Notas" size="small">
                {selectedOrder.details && (
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>Descripción:</Text>
                    <div>{selectedOrder.details}</div>
                  </div>
                )}
                {selectedOrder.setup_notes && (
                  <div>
                    <Text strong>Notas del Setup:</Text>
                    <div>{selectedOrder.setup_notes}</div>
                  </div>
                )}
              </Card>
            )}
          </div>
        )}
      </Modal>
      {/* NUEVO MODAL DE ACTUALIZACIÓN */}
      <FormatOrderUpdateModal
        visible={updateModalVisible}
        onCancel={() => {
          setUpdateModalVisible(false);
          setUpdatingOrder(null);
        }}
        onSubmit={handleOrderUpdate}
        order={updatingOrder}
      />
    </div>
  );
};

export default FormatChangesList;