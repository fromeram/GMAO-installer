// Ordenes.js - CON GESTIÓN DE MÚLTIPLES TÉCNICOS Y CHECKLIST RESTAURADO
import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Modal, Form, Input, Select, message, Space, Spin, Alert, Typography, Popconfirm, Tooltip, Tag, AutoComplete } from 'antd';
import { DeleteOutlined, EditOutlined, PlusOutlined, SearchOutlined, FileExcelOutlined, EyeOutlined, ToolOutlined, CheckSquareOutlined, SettingOutlined } from '@ant-design/icons';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { fetchWithAuth } from '../apiConfig';
import WorkOrderForm from './WorkOrderForm';
import FormatChangeForm from '../components/FormatChangeForm';
import InteractiveTaskListChecklist from './InteractiveTaskListChecklist';
import WorkOrderDetailModal from '../components/WorkOrderDetailModal';
import TechnicianManager, { TechnicianSummary } from '../components/TechnicianManager';
import * as XLSX from 'xlsx';

const { Title, Text } = Typography;
const { Option } = Select;

// Función auxiliar para formatear fechas
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

const formatDateForExport = (dateString) => {
    if (!dateString) return '';
    try {
        return new Date(dateString).toLocaleString('sv-SE', {
             year: 'numeric', month: '2-digit', day: '2-digit',
             hour: '2-digit', minute: '2-digit'
        });
    } catch (e) {
        return dateString;
    }
};

const getStatusColor = (status) => {
    const colors = { 'Pendiente': 'gold', 'En curso': 'blue', 'En revisión': 'purple', 'Cerrada': 'green' };
    return colors[status] || 'default';
};

const getTypeColor = (type) => {
    const typeColors = { 'Preventivo': 'green', 'Correctivo': 'red', 'Inspección': 'blue', 'Mejora': 'cyan', 'Modificación': 'purple', 'Seguridad': 'orange' };
    return typeColors[type] || 'default';
};

const Ordenes = () => {
  const [sections, setSections] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [workOrders, setWorkOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingOrder, setEditingOrder] = useState(null);
  const { currentUser } = useAuth();
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const location = useLocation();

  // Estados para modal de formato
  const [formatModalVisible, setFormatModalVisible] = useState(false);
  const [editingFormatOrder, setEditingFormatOrder] = useState(null);
  const [machines, setMachines] = useState([]);
  const [users, setUsers] = useState([]);

  // Estados para búsqueda
  const [searchText, setSearchText] = useState('');
  const [searchOptions, setSearchOptions] = useState([]);
  const [filteredOrders, setFilteredOrders] = useState([]);

  // Estados para modal de detalle
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedOrderDetail, setSelectedOrderDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // ⭐ Estados para checklist RESTAURADOS
  const [checklistModalVisible, setChecklistModalVisible] = useState(false);
  const [selectedOrderForChecklist, setSelectedOrderForChecklist] = useState(null);
  const [orderTaskList, setOrderTaskList] = useState(null);
  const [checklistLoading, setChecklistLoading] = useState(false);

  // Estado para paginación
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    showSizeChanger: true,
    showQuickJumper: true,
    pageSizeOptions: ['10', '20', '50', '100'],
    showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} órdenes`,
  });

  // Función para verificar permisos de edición
  const canEditOrder = (order) => {
    if (!currentUser || !order) return false;
    
    const userRole = currentUser.role;
    const isAdminOrMaintenance = ["Administrador", "Jefe de Mantenimiento"].includes(userRole);
    const isJefeSeccion = userRole === "Jefe de Sección";
    const isMecanico = userRole === "Mecánico";
    
    if (isAdminOrMaintenance) return true;
    
    if (isJefeSeccion && order.section_id === currentUser.section_id && order.status !== 'Cerrada') {
      return true;
    }
    
    if (isMecanico && order.assigned_to_id === currentUser.id && order.status !== 'Cerrada') {
      return true;
    }
    
    return false;
  };

  const canEdit = currentUser && ["Administrador", "Jefe de Mantenimiento"].includes(currentUser.role);

  // ⭐ FUNCIÓN PARA MOSTRAR MODAL DE CHECKLIST RESTAURADA
  const showChecklistModal = async (order) => {
    if (!order.has_checklist) {
      message.warning('Esta orden no tiene un checklist asociado');
      return;
    }

    try {
      setChecklistLoading(true);
      setSelectedOrderForChecklist(order);
      
      // Cargar datos del checklist desde el backend
      const response = await fetchWithAuth(`/work-orders/${order.id}/checklist-data`);      
      if (response.task_list) {
        setOrderTaskList(response.task_list);
        setChecklistModalVisible(true);
      } else {
        message.error('No se pudo cargar el checklist');
      }
    } catch (error) {
      console.error('Error cargando checklist:', error);
      message.error('Error al cargar el checklist');
    } finally {
      setChecklistLoading(false);
    }
  };

  // ⭐ FUNCIÓN MODIFICADA PARA CARGAR DATOS CON TÉCNICOS Y CHECKLIST
  const loadData = async () => {
    setLoading(true);
    try {
      const [sectionsData, productsData, ordersData, usersData, machinesData] = await Promise.all([
        fetchWithAuth('/secciones'),
        fetchWithAuth('/productos'),
        fetchWithAuth('/ordenes?include_technicians=true'), // ⭐ INCLUIR TÉCNICOS
        fetchWithAuth('/users'),
        fetchWithAuth('/maquinas')
      ]);
      
      console.log("Ordenes cargadas:", ordersData);
      setSections(sectionsData || []);
      setInventory(productsData || []);
      setUsers(usersData || []);
      setMachines(machinesData || []);
      
      // Normalización de datos
      const sectionsMap = new Map((sectionsData || []).map(s => [s.id, s]));
      const linesMap = new Map((sectionsData || []).flatMap(s => s.lines || []).map(l => [l.id, l]));

      // ⭐ PROCESAR DATOS DE ÓRDENES PARA INCLUIR INFORMACIÓN DE CHECKLIST
      const ordersWithKeys = (ordersData || []).map(order => {
          const sectionObject = sectionsMap.get(order.section_id);
          const lineObject = linesMap.get(order.line_id);

          return {
              ...order,
              key: order.id,
              section: sectionObject || order.section || null,
              line: lineObject || order.line || null,
              machine: order.machine_obj?.nombre || order.machine?.nombre || order.machine,
              affected_machines: order.affected_machines || [],
              format_change_type: order.format_change_type || null,
              technicians: order.technicians || [], // ⭐ ASEGURAR ARRAY DE TÉCNICOS
              has_checklist: order.has_checklist || false // ⭐ INFORMACIÓN DE SI TIENE CHECKLIST
          };
      });
      
      setWorkOrders(ordersWithKeys);
      setFilteredOrders(ordersWithKeys);
      setError(null);
    } catch (err) {
      console.error('Error al cargar datos:', err);
      setError('Error al cargar los datos. Intente recargar la página.');
    } finally {
      setLoading(false);
    }
  };

  // ⭐ FUNCIÓN PARA ACTUALIZAR CUANDO SE MODIFIQUEN TÉCNICOS
  const handleTechnicianUpdate = async () => {
    // Recargar datos para reflejar cambios
    await loadData();
    
    // Si hay una orden seleccionada, recargar sus detalles también
    if (selectedOrderDetail) {
      try {
        const response = await fetchWithAuth(`/ordenes/${selectedOrderDetail.id}?include_technicians=true`);
        setSelectedOrderDetail({
          ...response,
          technicians: response.technicians || []
        });
      } catch (error) {
        console.error('Error actualizando detalles:', error);
      }
    }
  };

  // ⭐ FUNCIÓN PARA MOSTRAR DETALLES DE ORDEN CON TÉCNICOS
  const showOrderDetail = async (order) => {
    try {
      setDetailLoading(true);
      
      // Cargar detalles completos incluyendo técnicos
      const response = await fetchWithAuth(`/ordenes/${order.id}?include_technicians=true`);
      
      setSelectedOrderDetail({
        ...response,
        technicians: response.technicians || []
      });
      setDetailModalVisible(true);
      
    } catch (error) {
      console.error('Error cargando detalles:', error);
      message.error('Error al cargar los detalles de la orden');
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    if (currentUser) {
      loadData();
    }
  }, [currentUser]);

  // Handler para cambio de estado directo
  const handleStatusChange = async (orderId, newStatus) => {
    console.log('handleStatusChange llamado con:', orderId, newStatus);
    setLoading(true);
    try {
        const response = await fetchWithAuth(`/ordenes/${orderId}`, {
            method: 'PUT', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify({ status: newStatus })
        });
        
        console.log('Respuesta de la actualización de estado:', response);
        if (response && response.id) {
             message.success(`Estado actualizado a ${newStatus}`); 
             await loadData();
        } else { 
            throw new Error(response?.detail || response?.message || 'Error actualizando estado.'); 
        }
    } catch (error) {
        console.error('Error al actualizar estado:', error);
        message.error(error.message || 'Error al actualizar estado.');
    } finally {
        setLoading(false);
    }
  };

  // Handler para Crear/Actualizar ORDEN NORMAL
  const handleSubmit = async (orderDataFromForm) => {
    setLoading(true);
    const isEditing = !!editingOrder;
    const endpoint = isEditing ? `/ordenes/${editingOrder.id}` : '/ordenes';
    const method = isEditing ? 'PUT' : 'POST';

    try {
      const response = await fetchWithAuth(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderDataFromForm)
      });

      message.success(`Orden ${isEditing ? 'actualizada' : 'creada'} correctamente`);
      setModalVisible(false);
      setEditingOrder(null);
      await loadData();
    } catch (error) {
      console.error('Error:', error);
      message.error(error.message || 'Error al guardar la orden');
    } finally {
      setLoading(false);
    }
  };

  // Handler para Crear/Actualizar ORDEN DE FORMATO
  const handleFormatSubmit = async (orderDataFromForm) => {
    setLoading(true);
    try {
      const url = editingFormatOrder 
        ? `/work-orders/${editingFormatOrder.id}/format-change`
        : '/work-orders/format-change';
      const method = editingFormatOrder ? 'PUT' : 'POST';

      await fetchWithAuth(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderDataFromForm)
      });

      message.success(`Orden de formato ${editingFormatOrder ? 'actualizada' : 'creada'} correctamente`);
      setFormatModalVisible(false);
      setEditingFormatOrder(null);
      await loadData();
    } catch (error) {
      console.error('Error:', error);
      message.error(error.message || 'Error al guardar la orden de formato');
    } finally {
      setLoading(false);
    }
  };

  // Handler para editar orden
  const handleEditOrder = (order) => {
    setEditingOrder(order);
    setModalVisible(true);
  };

  // Handler para eliminar orden
  const handleDeleteOrder = async (orderId) => {
    try {
      await fetchWithAuth(`/ordenes/${orderId}`, { method: 'DELETE' });
      message.success('Orden eliminada correctamente');
      await loadData();
    } catch (error) {
      message.error(error.message || 'Error al eliminar la orden');
    }
  };

  // Función para manejar búsqueda
  const handleSearch = value => {
    setSearchText(value);
    
    setPagination({
      ...pagination,
      current: 1
    });
    
    if (!value) {
      setFilteredOrders(workOrders);
      setSearchOptions([]);
      return;
    }
    
    const matchingOrders = workOrders.filter(order => 
      (order.title && order.title.toLowerCase().includes(value.toLowerCase())) ||
      (order.details && order.details.toLowerCase().includes(value.toLowerCase())) ||
      (order.work_type && order.work_type.toLowerCase().includes(value.toLowerCase())) ||
      (order.order_number && order.order_number.toLowerCase().includes(value.toLowerCase())) ||
      (order.machine?.nombre && order.machine.nombre.toLowerCase().includes(value.toLowerCase())) ||
      (order.section?.nombre && order.section.nombre.toLowerCase().includes(value.toLowerCase()))
    );
    
    setFilteredOrders(matchingOrders);
    
    const options = matchingOrders.slice(0, 10).map(order => ({
      value: order.title || '',
      label: (
        <div>
          <strong>{order.order_number || 'Sin número'}</strong> - {order.title || 'Sin título'} ({order.machine?.nombre || 'Sin máquina'})
        </div>
      )
    }));
    
    setSearchOptions(options);
  };

  // Función para exportar a Excel
  const exportToExcel = () => {
    try {
        message.loading({ content: 'Generando archivo Excel...', key: 'exportExcel' });

        const dataForExport = filteredOrders.map(order => ({
            'Nº Orden': order.order_number || `OT-${order.id}`,
            'Título': order.title || 'Sin título',
            'Tipo': order.work_type || 'No especificado',
            'Estado': order.status || 'Desconocido',
            'Sección': order.section?.nombre || order.section || 'Sin sección',
            'Línea': order.line?.nombre || order.line || 'Sin línea',
            'Máquina': order.machine?.nombre || order.machine || 'Sin máquina',
            'Repuesto': order.repuesto?.product_name || 'Ninguno', // ⭐ AÑADIDA COLUMNA REPUESTO
            'Operario': order.operator || 'No asignado',
            'Fecha Creación': formatDateForExport(order.created_at),
            'Fecha Finalización': formatDateForExport(order.finished_at),
            'Técnico Asignado': order.assigned_to?.username || 'No asignado',
            'Equipo Técnicos': order.technicians?.map(t => `${t.username} (${t.role})`).join(', ') || 'Ninguno',
            'Tiene Checklist': order.has_checklist ? 'Sí' : 'No',
            'Detalles': order.details || 'Sin detalles'
        }));

        const worksheet = XLSX.utils.json_to_sheet(dataForExport);
        const columnWidths = Object.keys(dataForExport[0] || {}).map(key => ({
            wch: key.includes('Detalles') ? 50 : key.includes('Fecha') ? 18 : key.includes('Título') ? 35 : 15
        }));
        worksheet['!cols'] = columnWidths;

        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, "OrdenesDeTrabajo");
        XLSX.writeFile(workbook, "Historial_Ordenes_Trabajo.xlsx");

        message.success({ content: 'Exportación a Excel completada.', key: 'exportExcel', duration: 3 });
    } catch (error) {
        console.error("Error al generar Excel:", error);
        message.error({ content: 'Error al generar el archivo Excel.', key: 'exportExcel', duration: 3 });
    }
  };

  // ⭐ DEFINICIÓN DE COLUMNAS CON TÉCNICOS Y CHECKLIST
  const columns = [
    { 
      title: 'Nº Orden', 
      dataIndex: 'order_number', 
      key: 'order_number', 
      width: 120, 
      fixed: 'left',
      render: (text, record) => (
        <Button 
          type="link" 
          size="small" 
          onClick={() => showOrderDetail(record)}
          style={{ padding: 0, fontWeight: 'bold', color: '#1890ff' }}
        >
          {text || `OT-${record.id}`}
        </Button>
      )
    }, 
    { 
      title: 'Descripción', 
      dataIndex: 'title', 
      key: 'title', 
      ellipsis: true, 
      width: 250,
      render: (text, record) => (
        <Tooltip title={`${text}\n\nDetalles: ${record.details || 'Sin detalles'}`}>
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
      width: 150,
      render: (status, record) => {
          const isAdminOrMaintenance = ["Administrador", "Jefe de Mantenimiento"].includes(currentUser?.role);
          const canEditStatus = isAdminOrMaintenance || record.status !== 'Cerrada';
          return (
            <Select 
              value={status} 
              style={{ width: '100%' }} 
              onChange={(newStatus) => handleStatusChange(record.id, newStatus)}
              disabled={!canEditStatus}
              size="small"
            >
              <Option value="Pendiente">
                <Tag color="gold">Pendiente</Tag>
              </Option>
              <Option value="En curso">
                <Tag color="blue">En curso</Tag>
              </Option>
              <Option value="En revisión">
                <Tag color="purple">En revisión</Tag>
              </Option>
              <Option value="Cerrada">
                <Tag color="green">Cerrada</Tag>
              </Option>
            </Select>
          );
      }
    },
    // ⭐ COLUMNA DEL USUARIO CREADOR RESTAURADA
    {
      title: '👤 Creada por',
      key: 'created_by',
      width: 130,
      render: (_, record) => {
        const createdBy = record.created_by?.username || record.assigned_to?.username || 'No asignado';
        return (
          <Tooltip title={`Creada por: ${createdBy}`}>
            <Text style={{ fontSize: '12px' }}>{createdBy}</Text>
          </Tooltip>
        );
      },
    },
    // ⭐ COLUMNA DE TÉCNICOS - SOLO VISUAL, CLIC ABRE MODAL
    {
      title: '👥 Equipo', 
      key: 'technicians',
      width: 180,
      render: (_, record) => {
        const activeTechs = (record.technicians || []).filter(t => t.is_active !== false);
        return (
          <div 
            style={{ cursor: 'pointer' }}
            onClick={() => showOrderDetail(record)}
          >
            <TechnicianSummary 
              technicians={activeTechs} 
              showDetails={false}
            />
          </div>
        );
      },
    },
    { 
      title: 'Sección', 
      dataIndex: 'section', 
      key: 'section', 
      width: 120,
      render: (section) => section?.nombre || section || 'Sin sección'
    },
    { 
      title: 'Línea', 
      dataIndex: 'line', 
      key: 'line', 
      width: 100,
      render: (line) => line?.nombre || line || 'Sin línea'
    },
    { 
      title: 'Máquina', 
      dataIndex: 'machine', 
      key: 'machine', 
      width: 140,
      render: (machine, record) => {
        const machineName = machine?.nombre || machine || 'Sin máquina';
        const machineId = record.machine?.id || record.machine_id;
        
        return machineId ? (
          <Button 
            type="link" 
            size="small"
            onClick={() => navigate(`/maquinas/${machineId}`)}
            style={{ padding: 0, fontSize: '12px' }}
          >
            {machineName}
          </Button>
        ) : (
          <Text style={{ fontSize: '12px' }}>{machineName}</Text>
        );
      }
    },
    // ⭐ COLUMNA DE REPUESTO AÑADIDA - SOLO ESTE ES EL CAMBIO
    { 
      title: 'Repuesto', 
      dataIndex: 'repuesto', 
      key: 'repuesto', 
      width: 140,
      render: (repuesto) => {
        if (!repuesto) return <Text style={{ color: '#999', fontSize: '12px' }}>Ninguno</Text>;
        
        return (
          <Tooltip title={`Repuesto: ${repuesto.product_name || 'Sin nombre'}`}>
            <Text style={{ fontSize: '12px' }}>
              {repuesto.product_name || 'Sin nombre'}
            </Text>
          </Tooltip>
        );
      }
    },
    { 
      title: 'Fecha', 
      dataIndex: 'created_at', 
      key: 'created_at', 
      width: 130,
      render: (date) => (
        <Text style={{ fontSize: '11px' }}>{formatDate(date)}</Text>
      )
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 150, // ⭐ AUMENTAR ANCHO PARA ACOMODAR EL BOTÓN CHECKLIST
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="Ver detalles">
            <Button 
              icon={<EyeOutlined />} 
              size="small" 
              onClick={() => showOrderDetail(record)}
            />
          </Tooltip>
          
          {/* ⭐ BOTÓN CHECKLIST RESTAURADO */}
          <Tooltip title={record.has_checklist ? "Abrir checklist" : "Sin checklist disponible"}>
            <Button 
              icon={<CheckSquareOutlined />} 
              size="small" 
              disabled={!record.has_checklist} // ⭐ OPACO SI NO TIENE CHECKLIST
              onClick={() => showChecklistModal(record)}
              style={{
                opacity: record.has_checklist ? 1 : 0.3 // ⭐ VISUAL DE DESHABILITADO
              }}
            />
          </Tooltip>
          
          {canEditOrder(record) && (
            <Tooltip title="Editar">
              <Button 
                icon={<EditOutlined />} 
                size="small" 
                onClick={() => handleEditOrder(record)}
              />
            </Tooltip>
          )}
          
          {canEdit && (
            <Tooltip title="Eliminar">
              <Popconfirm
                title="¿Estás seguro de eliminar esta orden?"
                onConfirm={() => handleDeleteOrder(record.id)}
                okText="Sí"
                cancelText="No"
              >
                <Button 
                  icon={<DeleteOutlined />} 
                  size="small" 
                  danger
                />
              </Popconfirm>
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <p>Cargando órdenes de trabajo...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Error al cargar datos"
        description={error}
        type="error"
        showIcon
        action={
          <Button size="small" onClick={loadData}>
            Reintentar
          </Button>
        }
      />
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <Title level={2}>📋 Órdenes de Trabajo</Title>
        
        <Space>
          <Button
            icon={<FileExcelOutlined />}
            onClick={exportToExcel}
          >
            Exportar Excel
          </Button>
          
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingOrder(null);
              setModalVisible(true);
            }}
          >
            Nueva Orden
          </Button>
          
          {canEdit && (
            <Button
              icon={<SettingOutlined />}
              onClick={() => {
                setEditingFormatOrder(null);
                setFormatModalVisible(true);
              }}
            >
              Orden de Formato
            </Button>
          )}
        </Space>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <AutoComplete
          style={{ width: '100%', maxWidth: '400px' }}
          placeholder="Buscar por título, tipo, máquina, sección..."
          onSearch={handleSearch}
          onSelect={handleSearch}
          options={searchOptions}
        >
          <Input
            prefix={<SearchOutlined />}
            allowClear
            value={searchText}
            onChange={(e) => handleSearch(e.target.value)}
          />
        </AutoComplete>
      </div>

      <Table
        columns={columns}
        dataSource={filteredOrders}
        loading={loading}
        pagination={{
          ...pagination,
          total: filteredOrders.length,
          onChange: (page, pageSize) => {
            setPagination({ ...pagination, current: page, pageSize });
          },
          onShowSizeChange: (current, size) => {
            setPagination({ ...pagination, current: 1, pageSize: size });
          },
        }}
        scroll={{ x: 1600 }} // ⭐ AUMENTADO PARA ACOMODAR EL BOTÓN CHECKLIST
        size="small"
      />

      {/* Modal para crear/editar orden normal */}
      <Modal
        title={editingOrder ? "Editar Orden de Trabajo" : "Nueva Orden de Trabajo"}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingOrder(null);
        }}
        footer={null}
        width={900}
        destroyOnClose
      >
        <WorkOrderForm
          onSubmit={handleSubmit}
          preloadedData={editingOrder}
          sections={sections}
          inventory={inventory}
          onCancel={() => {
            setModalVisible(false);
            setEditingOrder(null);
          }}
        />
      </Modal>

      {/* Modal para crear/editar orden de formato */}
      <Modal
        title={editingFormatOrder ? "Editar Orden de Formato" : "Nueva Orden de Formato"}
        open={formatModalVisible}
        onCancel={() => {
          setFormatModalVisible(false);
          setEditingFormatOrder(null);
        }}
        footer={null}
        width={800}
        destroyOnClose
      >
        <FormatChangeForm
          onSubmit={handleFormatSubmit}
          preloadedData={editingFormatOrder}
          machines={machines}
          users={users}
          onCancel={() => {
            setFormatModalVisible(false);
            setEditingFormatOrder(null);
          }}
        />
      </Modal>

      {/* ⭐ MODAL DE DETALLES CON GESTIÓN DE TÉCNICOS */}
      {detailModalVisible && selectedOrderDetail && (
        <WorkOrderDetailModal
          visible={detailModalVisible}
          onCancel={() => {
            setDetailModalVisible(false);
            setSelectedOrderDetail(null);
          }}
          orderDetail={selectedOrderDetail}
          onEdit={canEditOrder(selectedOrderDetail) ? () => handleEditOrder(selectedOrderDetail) : null}
          onTechnicianUpdate={handleTechnicianUpdate}
        />
      )}

      {/* ⭐ MODAL DE CHECKLIST RESTAURADO */}
      {checklistModalVisible && selectedOrderForChecklist && orderTaskList && (
        <InteractiveTaskListChecklist
          visible={checklistModalVisible}
          onCancel={() => {
            setChecklistModalVisible(false);
            setSelectedOrderForChecklist(null);
            setOrderTaskList(null);
          }}
          workOrder={selectedOrderForChecklist}
          taskList={orderTaskList}
          onUpdate={loadData}
        />
      )}
    </div>
  );
};

export default Ordenes;