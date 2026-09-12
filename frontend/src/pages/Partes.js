// src/pages/Partes.js (CORREGIDO - con restricciones de permisos por rol y paginación corregida)
import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Typography, 
  DatePicker, 
  Button, 
  Space, 
  Alert, 
  Tag, 
  Modal,
  Tooltip,
  Row,
  Col,
  message
} from 'antd';
import { 
  CalendarOutlined, 
  FileExcelOutlined, 
  EyeOutlined, 
  ToolOutlined,
  UserOutlined,
  ClockCircleOutlined,
  EditOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { fetchWithAuth } from '../apiConfig';
import dayjs from 'dayjs';
import * as XLSX from 'xlsx';
import '../styles/CommonPage.css';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const Partes = () => {
  const [workOrders, setWorkOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [dateRange, setDateRange] = useState(null);
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  // Estados para modal de detalle
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedOrderDetail, setSelectedOrderDetail] = useState(null);

  // 🔧 ESTADO PARA PAGINACIÓN
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 15,
    showSizeChanger: true,
    showQuickJumper: true,
    pageSizeOptions: ['10', '15', '30', '50', '100'],
    showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} partes`,
  });

  // 🔧 FUNCIÓN PARA MANEJAR CAMBIOS EN LA PAGINACIÓN
  const handleTableChange = (pag, filters, sorter) => {
    console.log('Cambio en paginación partes:', pag);
    setPagination({
      ...pagination,
      current: pag.current,
      pageSize: pag.pageSize,
    });
  };

  // ✅ AÑADIR: Función para verificar permisos
  const canEditOrder = (order) => {
    if (!currentUser || !order) return false;
    
    const userRole = currentUser.role;
    const isAdminOrMaintenance = ["Administrador", "Jefe de Mantenimiento"].includes(userRole);
    const isJefeSeccion = userRole === "Jefe de Sección";
    const isMecanico = userRole === "Mecánico";
    
    // Admin y Jefe de Mantenimiento pueden editar cualquier orden
    if (isAdminOrMaintenance) return true;
    
    // Jefe de Sección puede editar órdenes de su sección que no estén cerradas
    if (isJefeSeccion && order.section_id === currentUser.section_id && order.status !== 'Cerrada') {
      return true;
    }
    
    // Mecánicos solo pueden editar sus propias órdenes asignadas que no estén cerradas
    if (isMecanico && order.assigned_to_id === currentUser.id && order.status !== 'Cerrada') {
      return true;
    }
    
    return false;
  };

  const fetchWorkOrders = async (date = null, range = null) => {
    setLoading(true);
    try {
      let dateParam = '';
      if (range && range.length === 2) {
        const startDate = range[0].format('YYYY-MM-DD');
        const endDate = range[1].format('YYYY-MM-DD');
        dateParam = `start=${startDate}&end=${endDate}`;
      } else if (date) {
        dateParam = `fecha=${date.format('YYYY-MM-DD')}`;
      } else {
        dateParam = `fecha=${dayjs().format('YYYY-MM-DD')}`;
      }
      
      const data = await fetchWithAuth(`/partes?${dateParam}`);
      setWorkOrders(data || []);
    } catch (error) {
      console.error('Error al cargar partes de trabajo:', error);
      setWorkOrders([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkOrders(selectedDate);
  }, [selectedDate]);

  const handleDateChange = (date) => {
    setSelectedDate(date);
    setDateRange(null);
    // 🔧 RESETEAR PAGINACIÓN AL CAMBIAR FECHA
    setPagination({
      ...pagination,
      current: 1
    });
    if (date) {
      fetchWorkOrders(date);
    }
  };

  const handleRangeChange = (dates) => {
    setDateRange(dates);
    setSelectedDate(null);
    // 🔧 RESETEAR PAGINACIÓN AL CAMBIAR RANGO
    setPagination({
      ...pagination,
      current: 1
    });
    if (dates && dates.length === 2) {
      fetchWorkOrders(null, dates);
    }
  };

  const showOrderDetail = (order) => {
    setSelectedOrderDetail(order);
    setDetailModalVisible(true);
  };

  // ✅ AÑADIR: Función para manejar edición con validación
  const handleEditOrder = (order) => {
    if (!canEditOrder(order)) {
      if (order.status === 'Cerrada') {
        message.warning('No puedes editar una orden que ya está cerrada');
      } else {
        message.warning('No tienes permisos para editar esta orden');
      }
      return;
    }
    
    // Cerrar modal de detalle y ir a órdenes con el ID para editar
    setDetailModalVisible(false);
    navigate('/ordenes', { 
      state: { 
        editOrderId: order.id,
        fromPartes: true 
      } 
    });
  };

  const handleExportExcel = () => {
    if (workOrders.length === 0) {
      message.warning("No hay datos para exportar.");
      return;
    }

    const dataToExport = workOrders.map(order => ({
      'ID': order.id,
      'Título': order.title,
      'Tipo': order.work_type,
      'Estado': order.status,
      'Sección': order.section,
      'Línea': order.line,
      'Máquina': order.machine,
      'Operario': order.operator,
      'Fecha Creación': order.created_at ? new Date(order.created_at).toLocaleString('es-ES') : ''
    }));

    try {
      const worksheet = XLSX.utils.json_to_sheet(dataToExport);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "PartesTorabajo");
      
      const fileName = dateRange && dateRange.length === 2 
        ? `Partes_${dateRange[0].format('YYYY-MM-DD')}_${dateRange[1].format('YYYY-MM-DD')}.xlsx`
        : `Partes_${selectedDate ? selectedDate.format('YYYY-MM-DD') : dayjs().format('YYYY-MM-DD')}.xlsx`;
      
      XLSX.writeFile(workbook, fileName);
      message.success('Exportación completada');
    } catch (error) {
      console.error("Error al exportar:", error);
      message.error('Error al exportar los datos');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      return new Date(dateString).toLocaleString('es-ES', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit'
      });
    } catch (e) {
      return dateString;
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

  const getTypeColor = (type) => {
    const typeColors = { 
      'Preventivo': 'green', 
      'Correctivo': 'red', 
      'Inspección': 'blue', 
      'Mejora': 'cyan', 
      'Modificación': 'purple', 
      'Seguridad': 'orange' 
    };
    return typeColors[type] || 'default';
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      render: (text, record) => (
        <Button 
          type="link" 
          size="small" 
          onClick={() => showOrderDetail(record)}
          style={{ padding: 0, fontWeight: 'bold', color: '#1890ff' }}
        >
          #{text}
        </Button>
      )
    },
    {
      title: 'Título/Descripción',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (text, record) => (
        <Tooltip title={`Ver detalles completos de la orden`}>
          <Button 
            type="link" 
            size="small"
            onClick={() => showOrderDetail(record)}
            style={{ padding: 0, textAlign: 'left', height: 'auto', whiteSpace: 'normal' }}
          >
            {text}
          </Button>
        </Tooltip>
      )
    },
    {
      title: 'Tipo',
      dataIndex: 'work_type',
      key: 'work_type',
      width: 120,
      render: (type) => <Tag color={getTypeColor(type)}>{type}</Tag>
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => <Tag color={getStatusColor(status)}>{status}</Tag>
    },
    {
      title: 'Sección',
      dataIndex: 'section',
      key: 'section',
      width: 120,
      ellipsis: true
    },
    {
      title: 'Línea',
      dataIndex: 'line',
      key: 'line',
      width: 120,
      ellipsis: true
    },
    {
      title: 'Máquina',
      dataIndex: 'machine',
      key: 'machine',
      width: 150,
      ellipsis: true,
      render: (text, record) => {
        const machineId = record.machine_id;
        
        return text ? (
          <Tooltip title={`Ver detalles de la máquina: ${text}`}>
            <Button 
              type="link" 
              size="small" 
              icon={<ToolOutlined />}
              onClick={() => {
                if (machineId) {
                  navigate(`/maquinas/${machineId}/detail`);
                } else {
                  message.info('ID de máquina no disponible');
                }
              }}
              style={{ padding: 0 }}
            >
              {text}
            </Button>
          </Tooltip>
        ) : '-';
      }
    },
    {
      title: 'Operario',
      dataIndex: 'operator',
      key: 'operator',
      width: 120,
      ellipsis: true,
      render: (text) => (
        <span>
          <UserOutlined style={{ marginRight: 4, color: '#666' }} />
          {text}
        </span>
      )
    },
    {
      title: 'Fecha Creación',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date) => (
        <span>
          <ClockCircleOutlined style={{ marginRight: 4, color: '#666' }} />
          {formatDate(date)}
        </span>
      ),
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
      defaultSortOrder: 'descend'
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 120,
      align: 'center',
      render: (_, record) => {
        const canEdit = canEditOrder(record);
        
        return (
          <Space>
            <Tooltip title="Ver detalles completos">
              <Button 
                type="default" 
                icon={<EyeOutlined />} 
                onClick={() => showOrderDetail(record)} 
                size="small"
              />
            </Tooltip>
            {/* ✅ CORREGIDO: Solo mostrar botón editar si tiene permisos */}
            {canEdit ? (
              <Tooltip title="Editar orden">
                <Button 
                  type="primary" 
                  icon={<EditOutlined />}
                  size="small"
                  onClick={() => handleEditOrder(record)}
                />
              </Tooltip>
            ) : (
              <Tooltip title={
                record.status === 'Cerrada' 
                  ? "La orden está cerrada" 
                  : "Sin permisos para editar"
              }>
                <Button 
                  type="default"
                  icon={<EditOutlined />}
                  size="small"
                  disabled
                />
              </Tooltip>
            )}
          </Space>
        );
      }
    }
  ];

  const getDateRangeText = () => {
    if (dateRange && dateRange.length === 2) {
      return `${dateRange[0].format('DD/MM/YYYY')} - ${dateRange[1].format('DD/MM/YYYY')}`;
    } else if (selectedDate) {
      return selectedDate.format('DD/MM/YYYY');
    }
    return dayjs().format('DD/MM/YYYY');
  };

  return (
    <div className="page-container">
      <div className="page-header" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={2} className="page-title" style={{ marginBottom: 0 }}>
            Partes de Trabajo
          </Title>
          <Button 
            type="primary" 
            icon={<FileExcelOutlined />} 
            onClick={handleExportExcel}
            disabled={loading || workOrders.length === 0}
            ghost
          >
            Exportar Excel
          </Button>
        </div>
      </div>

      {/* Controles de filtrado por fecha */}
      <Card 
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <CalendarOutlined />
            <span>Filtrar por Fecha</span>
          </div>
        } 
        size="small" 
        style={{ marginBottom: 20 }}
      >
        <Row gutter={16} align="middle">
          <Col xs={24} sm={12} md={8}>
            <div style={{ marginBottom: 8 }}>
              <Text strong>Fecha Específica:</Text>
            </div>
            <DatePicker
              value={selectedDate}
              onChange={handleDateChange}
              format="DD/MM/YYYY"
              placeholder="Seleccionar fecha"
              style={{ width: '100%' }}
              allowClear={false}
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <div style={{ marginBottom: 8 }}>
              <Text strong>Rango de Fechas:</Text>
            </div>
            <RangePicker
              value={dateRange}
              onChange={handleRangeChange}
              format="DD/MM/YYYY"
              placeholder={['Fecha inicio', 'Fecha fin']}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={24} md={8}>
            <div style={{ marginBottom: 8 }}>
              <Text strong>Período Activo:</Text>
            </div>
            <Alert
              message={getDateRangeText()}
              type="info"
              showIcon
              style={{ textAlign: 'center' }}
            />
          </Col>
        </Row>
      </Card>

      {/* Tabla de resultados */}
      <Card 
        title={`Partes de Trabajo - ${getDateRangeText()} (${workOrders.length} registros)`}
        className="table-container"
      >
        {/* 🔧 TABLA CON PAGINACIÓN CORREGIDA */}
        <Table
          columns={columns}
          dataSource={workOrders}
          loading={loading}
          rowKey="id"
          scroll={{ x: 'max-content' }}
          pagination={pagination}
          onChange={handleTableChange}
          size="small"
          bordered
        />
      </Card>

      {/* ✅ MODAL DE DETALLE CORREGIDO - Con restricciones en botones */}
      <Modal
        title={`Detalle del Parte de Trabajo - ID #${selectedOrderDetail?.id || 'N/A'}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        width={900}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            Cerrar
          </Button>,
          <Button 
            key="view-orders" 
            onClick={() => {
              setDetailModalVisible(false);
              navigate('/ordenes');
            }}
          >
            Ver Todas las Órdenes
          </Button>,
          // ✅ CORREGIDO: Solo mostrar botón editar si tiene permisos
          ...(selectedOrderDetail && canEditOrder(selectedOrderDetail) ? [
            <Button 
              key="edit" 
              type="primary" 
              icon={<EditOutlined />}
              onClick={() => handleEditOrder(selectedOrderDetail)}
            >
              Editar Orden
            </Button>
          ] : [])
        ]}
      >
        {selectedOrderDetail && (
          <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
            {/* ✅ AÑADIR: Alerta si no puede editar */}
            {selectedOrderDetail.status === 'Cerrada' && (
              <Alert
                message="Orden Cerrada"
                description="Esta orden de trabajo ya está cerrada y no puede ser modificada."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}
            
            {!canEditOrder(selectedOrderDetail) && selectedOrderDetail.status !== 'Cerrada' && (
              <Alert
                message="Sin Permisos de Edición"
                description="No tienes permisos para editar esta orden de trabajo."
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            {/* Información básica */}
            <div style={{ marginBottom: 20 }}>
              <h3>Información Básica del Trabajo</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div><strong>ID del Trabajo:</strong> #{selectedOrderDetail.id}</div>
                <div><strong>Estado:</strong> <Tag color={getStatusColor(selectedOrderDetail.status)}>{selectedOrderDetail.status}</Tag></div>
                <div><strong>Tipo de Trabajo:</strong> <Tag color={getTypeColor(selectedOrderDetail.work_type)}>{selectedOrderDetail.work_type}</Tag></div>
                <div><strong>Fecha de Creación:</strong> {formatDate(selectedOrderDetail.created_at)}</div>
                <div><strong>Operario Reportante:</strong> {selectedOrderDetail.operator}</div>
                <div><strong>Duración Estimada:</strong> Por determinar</div>
              </div>
            </div>

            {/* Resto del contenido del modal (sin cambios) */}
            <div style={{ marginBottom: 20 }}>
              <h3>Ubicación del Trabajo</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
                <div><strong>Sección:</strong> {selectedOrderDetail.section}</div>
                <div><strong>Línea de Producción:</strong> {selectedOrderDetail.line}</div>
                <div>
                  <strong>Máquina/Equipo:</strong> 
                  {selectedOrderDetail.machine && selectedOrderDetail.machine_id ? (
                    <Button 
                      type="link" 
                      size="small"
                      onClick={() => {
                        setDetailModalVisible(false);
                        navigate(`/maquinas/${selectedOrderDetail.machine_id}/detail`);
                      }}
                      style={{ padding: 0, marginLeft: 4 }}
                    >
                      {selectedOrderDetail.machine}
                    </Button>
                  ) : (
                    <span style={{ marginLeft: 4 }}>{selectedOrderDetail.machine || 'No especificado'}</span>
                  )}
                </div>
              </div>
            </div>

            <div style={{ marginBottom: 20 }}>
              <h3>Descripción del Trabajo</h3>
              <div style={{ marginBottom: 12 }}>
                <strong>Título del Trabajo:</strong>
                <div style={{ marginTop: 4, padding: 8, backgroundColor: '#f5f5f5', borderRadius: 4 }}>
                  {selectedOrderDetail.title}
                </div>
              </div>
            </div>

            <div style={{ marginBottom: 20 }}>
              <h3>Estado y Seguimiento</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <strong>Estado Actual:</strong> 
                  <Tag color={getStatusColor(selectedOrderDetail.status)} style={{ marginLeft: 8 }}>
                    {selectedOrderDetail.status}
                  </Tag>
                </div>
                <div>
                  <strong>Prioridad:</strong> 
                  <span style={{ marginLeft: 8 }}>
                    {selectedOrderDetail.work_type === 'Correctivo' ? 'Alta' : 
                     selectedOrderDetail.work_type === 'Preventivo' ? 'Media' : 'Normal'}
                  </span>
                </div>
              </div>
            </div>

            <div style={{ marginBottom: 20 }}>
              <h3>Información de Gestión</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div><strong>Reportado por:</strong> {selectedOrderDetail.operator}</div>
                <div><strong>Fecha de Reporte:</strong> {formatDate(selectedOrderDetail.created_at)}</div>
              </div>
            </div>

            {/* Información de auditoría ISO */}
            <div style={{ marginTop: 30, padding: 16, backgroundColor: '#f6ffed', borderRadius: 4, border: '1px solid #b7eb8f' }}>
              <h4 style={{ color: '#389e0d', marginBottom: 8 }}>📋 Información para Auditoría ISO</h4>
              <div style={{ fontSize: '12px', color: '#666' }}>
                <div><strong>ID Único del Parte:</strong> {selectedOrderDetail.id}</div>
                <div><strong>Trazabilidad:</strong> Reportado por {selectedOrderDetail.operator} el {formatDate(selectedOrderDetail.created_at)}</div>
                <div><strong>Estado de Seguimiento:</strong> {selectedOrderDetail.status === 'Cerrada' ? '✅ Trabajo completado' : '⏳ En seguimiento'}</div>
                <div><strong>Área de Responsabilidad:</strong> {selectedOrderDetail.section} - {selectedOrderDetail.line}</div>
                <div><strong>Equipo Involucrado:</strong> {selectedOrderDetail.machine || 'No especificado'}</div>
                <div><strong>Tipo de Intervención:</strong> {selectedOrderDetail.work_type}</div>
                <div><strong>Evidencia Documental:</strong> Registro digital completo disponible</div>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Partes;