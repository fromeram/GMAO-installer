import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  DatePicker,
  message,
  Typography,
  Radio,
  Space,
  Tag,
  Divider,
  Tooltip,
  Row,
  Col,
} from 'antd';
import {
  PlusOutlined,
  CheckSquareOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  DeleteOutlined,
  EditOutlined,
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import { useLocation, useNavigate } from 'react-router-dom'; // Importar hooks de router
import '../styles/CommonPage.css';
import moment from 'moment';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

// --- Funciones auxiliares para la conversión de tiempo ---
const convertHoursToBestUnit = (hours) => {
  if (hours === null || hours === undefined) return { value: 24, unit: 'horas' };
  if (hours > 0 && hours % (24 * 7) === 0) return { value: hours / (24 * 7), unit: 'semanas' };
  if (hours > 0 && hours % 24 === 0) return { value: hours / 24, unit: 'dias' };
  return { value: hours, unit: 'horas' };
};

const convertUnitToHours = (value, unit) => {
  if (!value) return 24; // Default
  switch (unit) {
    case 'dias':
      return value * 24;
    case 'semanas':
      return value * 24 * 7;
    case 'horas':
    default:
      return value;
  }
};


const MantenimientoPreventivo = () => {
  const { currentUser } = useAuth();
  const [maintenances, setMaintenances] = useState([]);
  const [allPlans, setAllPlans] = useState([]);
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [assignmentType, setAssignmentType] = useState('user');
  const [taskLists, setTaskLists] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [editingMaintenance, setEditingMaintenance] = useState(null);
  const [searchText, setSearchText] = useState('');

  // Hooks de router
  const location = useLocation();
  const navigate = useNavigate();

  const userRole = currentUser?.role?.nombre || currentUser?.role || '';
  const canCreateOrEdit = ['Administrador', 'Jefe de Mantenimiento'].includes(userRole);
  const canGenerateOrders = ['Administrador', 'Jefe de Mantenimiento'].includes(userRole);
  const canDelete = ['Administrador', 'Jefe de Mantenimiento'].includes(userRole);

  const getColumns = () => {
    const baseColumns = [
      { title: 'ID', dataIndex: 'id', key: 'id', width: 60, sorter: (a, b) => a.id - b.id },
      { title: 'Título', dataIndex: 'title', key: 'title', sorter: (a, b) => a.title.localeCompare(b.title) },
      { title: 'Máquina', dataIndex: 'maquina_nombre', key: 'maquina_nombre', sorter: (a, b) => a.maquina_nombre.localeCompare(b.maquina_nombre) },
      { title: 'Frecuencia', dataIndex: 'frecuencia', key: 'frecuencia' },
      {
        title: 'Lista de Tareas',
        key: 'task_list',
        width: 200,
        render: (_, record) => {
          const taskList = record.task_list || record.taskList || record.task_list_info;
          if (taskList && taskList.name) {
            return (
              <div>
                <Tag color="blue" icon={<CheckSquareOutlined />}>{taskList.name}</Tag>
                <br />
                <Text type="secondary" style={{ fontSize: '11px' }}>{taskList.description || 'Sin descripción'}</Text>
                {taskList.steps_count && (
                  <div style={{ fontSize: '10px', color: '#888' }}>
                    {taskList.steps_count} pasos • {taskList.total_estimated_minutes || 0} min
                  </div>
                )}
              </div>
            );
          } else if (record.task_list_id) {
            return <Tag color="processing" icon={<CheckSquareOutlined />}>Lista ID: {record.task_list_id}</Tag>;
          } else {
            return <Tag color="default">Sin lista de tareas</Tag>;
          }
        },
      },
      {
        title: 'Próximo Mantenimiento',
        dataIndex: 'next_maintenance_date',
        key: 'next_maintenance_date',
        sorter: (a, b) => new Date(a.next_maintenance_date) - new Date(b.next_maintenance_date),
        render: (date) => {
          if (!date) return 'No programado';
          const fechaMantenimiento = new Date(date);
          const ahora = new Date();
          const esVencido = fechaMantenimiento < ahora;
          return (
            <span style={{ color: esVencido ? '#ff4d4f' : 'inherit' }}>
              {fechaMantenimiento.toLocaleDateString('es-ES')}
              {esVencido && ' ⚠️'}
            </span>
          );
        },
      },
      {
        title: 'Asignado a',
        key: 'assigned',
        render: (_, record) => {
          if (record.assigned_user) {
            return <Tag color="green">{record.assigned_user.username}</Tag>;
          } else if (record.assigned_role) {
            return <Tag color="orange">{record.assigned_role.nombre}</Tag>;
          }
          return <Tag color="default">Sin asignar</Tag>;
        },
      }
    ];

    if (canCreateOrEdit || canGenerateOrders || canDelete) {
      baseColumns.push({
        title: 'Acciones',
        key: 'actions',
        width: 150,
        fixed: 'right',
        render: (_, record) => (
          <Space>
            {canCreateOrEdit && (
              <Tooltip title="Editar mantenimiento">
                <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
              </Tooltip>
            )}
            {canGenerateOrders && (
              <Tooltip title="Generar orden de trabajo">
                <Button size="small" icon={<PlayCircleOutlined />} onClick={() => handleGenerateOrder(record)} />
              </Tooltip>
            )}
            {canDelete && (
              <Tooltip title="Eliminar mantenimiento">
                <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} />
              </Tooltip>
            )}
             <Tooltip title="Vista previa de la orden">
              <Button size="small" icon={<EyeOutlined />} onClick={() => handlePreviewOrder(record)} disabled={!record.task_list_id && !record.task_list} />
            </Tooltip>
          </Space>
        ),
      });
    }
    return baseColumns;
  };

  const fetchMaintenanceData = async () => {
    try {
      setLoading(true);
      const maintenanceData = await fetchWithAuth('/mantenimiento-preventivo?include_task_list_details=true');
      setMaintenances(maintenanceData);
      setAllPlans(maintenanceData); // Guardar la lista completa para búsquedas

      const [machinesData, usersData, rolesData, taskListsData] = await Promise.all([
        fetchWithAuth('/maquinas'),
        fetchWithAuth('/users'),
        fetchWithAuth('/roles'),
        canCreateOrEdit ? fetchWithAuth('/task-lists/for-maintenance') : Promise.resolve([])
      ]);
      
      setMachines(machinesData);
      setUsers(usersData);
      setRoles(rolesData);
      setTaskLists(taskListsData || []);
    } catch (error) {
      message.error('Error al cargar los datos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMaintenanceData();
  }, []);
  
  // ✅ NUEVO: Lógica para manejar la edición desde el Plan Anual
  useEffect(() => {
    // Se ejecuta si location.state tiene la instrucción y si ya hemos cargado los planes
    if (location.state?.editPlanId && allPlans.length > 0) {
      const planToEdit = allPlans.find(p => String(p.id) === String(location.state.editPlanId));
      if (planToEdit) {
        handleEdit(planToEdit); // Llama a la función que ya tienes para abrir el modal
        
        // Limpia el estado de la navegación para que no se vuelva a abrir al recargar
        navigate(location.pathname, { replace: true, state: {} });
      }
    }
  }, [location.state, allPlans, navigate]); // Depende de estas variables

  const handleEdit = (record) => {
    setEditingMaintenance(record);
    const notificationTime = convertHoursToBestUnit(record.notification_interval);
    form.setFieldsValue({
      ...record,
      fechaInicio: record.fechaInicio ? moment(record.fechaInicio) : null,
      assigned_user_id: record.assigned_user?.id,
      assigned_role_id: record.assigned_role?.id,
      notification_value: notificationTime.value,
      notification_unit: notificationTime.unit,
    });
    if (record.assigned_user) setAssignmentType('user');
    else if (record.assigned_role) setAssignmentType('role');
    setModalVisible(true);
  };
  
  const handleCreate = () => {
    setEditingMaintenance(null);
    form.resetFields();
    form.setFieldsValue({ notification_value: 1, notification_unit: 'dias' });
    setAssignmentType('user');
    setModalVisible(true);
  };

  const handleSave = (values) => {
    const hours = convertUnitToHours(values.notification_value, values.notification_unit);
    const payload = {
        ...values,
        notification_interval: hours,
        fechaInicio: values.fechaInicio.format('YYYY-MM-DD'),
        task_list_id: values.task_list_id || null,
    };
    delete payload.notification_value;
    delete payload.notification_unit;
    if (editingMaintenance) handleUpdate(payload);
    else handleSubmit(payload);
  };

  const handleSubmit = async (payload) => {
    setSubmitting(true);
    try {
      const response = await fetchWithAuth('/mantenimiento-preventivo', { method: 'POST', body: JSON.stringify(payload) });
      if (response.success) {
        message.success('Mantenimiento creado correctamente');
        handleModalCancel();
        fetchMaintenanceData();
      } else { message.error(response.detail || 'Error al crear'); }
    } catch (error) { message.error(error.message || 'Error al crear el mantenimiento');
    } finally { setSubmitting(false); }
  };
  
  const handleUpdate = async (payload) => {
    setSubmitting(true);
    try {
      const response = await fetchWithAuth(`/mantenimiento-preventivo/${editingMaintenance.id}`, { method: 'PUT', body: JSON.stringify(payload) });
      if (response.success) {
        message.success('Mantenimiento actualizado correctamente');
        handleModalCancel();
        fetchMaintenanceData();
      } else { message.error(response.detail || 'Error al actualizar'); }
    } catch (error) { message.error(error.message || 'Error al actualizar el mantenimiento');
    } finally { setSubmitting(false); }
  };

  const handlePreviewOrder = async (maintenance) => {
    try {
      const response = await fetchWithAuth(`/maintenance/${maintenance.id}/preview-order`);
      Modal.info({
        title: `Vista Previa: ${maintenance.title}`,
        width: 800,
        content: (
          <div>
            <Divider>Información del Mantenimiento</Divider>
            <p><strong>Máquina:</strong> {response.maintenance.machine_name}</p>
            <p><strong>Frecuencia:</strong> {response.maintenance.frequency}</p>
            {response.task_list && (
              <>
                <Divider>Lista de Tareas: {response.task_list.name}</Divider>
                <p><strong>Total de pasos:</strong> {response.task_list.steps_count}</p>
                <p><strong>Tiempo estimado:</strong> {response.task_list.total_estimated_minutes} minutos</p>
                <ol>{response.task_list.steps.map(step => <li key={step.order}>{step.description}</li>)}</ol>
              </>
            )}
            <Divider>Orden de Trabajo Generada</Divider>
            <p><strong>Título:</strong> {response.preview_order.title}</p>
            <div style={{ maxHeight: '200px', overflow: 'auto', backgroundColor: '#f5f5f5', padding: '10px' }}>
              <pre style={{ fontSize: '12px', margin: 0 }}>{response.preview_order.details}</pre>
            </div>
          </div>
        ),
      });
    } catch (error) { message.error('Error al cargar vista previa'); }
  };

  const handleGenerateOrder = async (maintenance) => {
    if (!canGenerateOrders) return message.error('No tienes permisos.');
    try {
      const response = await fetchWithAuth(`/maintenance/generate-order/${maintenance.id}`, { method: 'POST' });
      if (response.success) {
        message.success(response.message);
        Modal.success({
          title: 'Orden Generada Exitosamente',
          content: (<div><p><strong>Número:</strong> {response.work_order.order_number}</p><p><strong>Título:</strong> {response.work_order.title}</p></div>),
        });
        fetchMaintenanceData();
      } else { message.error(response.detail || 'Error al generar orden'); }
    } catch (error) { message.error(error.message || 'Error al generar orden'); }
  };

  const handleDelete = async (id) => {
    if (!canDelete) return message.error('No tienes permisos.');
    Modal.confirm({
      title: '¿Eliminar este mantenimiento?',
      content: 'Esta acción no se puede deshacer.',
      okText: 'Sí, eliminar', okType: 'danger', cancelText: 'No',
      onOk: async () => {
        try {
          await fetchWithAuth(`/mantenimiento-preventivo/${id}`, { method: 'DELETE' });
          message.success('Mantenimiento eliminado');
          fetchMaintenanceData();
        } catch (error) { message.error('Error al eliminar'); }
      }
    });
  };

  const handleModalCancel = () => {
    setModalVisible(false);
    setEditingMaintenance(null);
    form.resetFields();
  };
  
  const filteredMaintenances = maintenances.filter(m =>
    (m.title && m.title.toLowerCase().includes(searchText.toLowerCase())) ||
    (m.maquina_nombre && m.maquina_nombre.toLowerCase().includes(searchText.toLowerCase()))
  );

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2} className="page-title">Mantenimiento Preventivo</Title>
      </div>
      <Card className="form-container">
        
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          {canCreateOrEdit ? (
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
              Nuevo Mantenimiento
            </Button>
          ) : <div />}
          <Input.Search
            placeholder="Buscar por título o máquina..."
            onChange={e => setSearchText(e.target.value)}
            style={{ width: 300 }}
            allowClear
          />
        </div>

        <Table
          columns={getColumns()}
          dataSource={filteredMaintenances}
          loading={loading}
          rowKey="id"
          pagination={{ pageSize: 10, showSizeChanger: true, showQuickJumper: true, showTotal: (total, range) => `${range[0]}-${range[1]} de ${total}` }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {canCreateOrEdit && (
        <Modal
          title={editingMaintenance ? "Editar Mantenimiento Preventivo" : "Nuevo Mantenimiento Preventivo"}
          open={modalVisible}
          onCancel={handleModalCancel}
          footer={null}
          width={800}
          destroyOnClose
        >
          <Form form={form} layout="vertical" onFinish={handleSave}>
            <Form.Item name="title" label="Título" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="description" label="Descripción" rules={[{ required: true }]}>
              <TextArea rows={3} />
            </Form.Item>
            <Form.Item name="maquina_id" label="Máquina" rules={[{ required: true }]}>
              <Select showSearch filterOption={(input, option) => option.label.toLowerCase().includes(input.toLowerCase())}>
                {machines.map(machine => (
                  <Option key={machine.id} value={machine.id} label={`${machine.nombre} - ${machine.marca} ${machine.modelo}`}>
                    {machine.nombre} - {machine.marca} {machine.modelo}
                  </Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item name="task_list_id" label="Lista de Tareas (Opcional)">
              <Select allowClear>
                {taskLists.map(tl => <Option key={tl.id} value={tl.id}>{tl.name}</Option>)}
              </Select>
            </Form.Item>
            <Form.Item name="frecuencia" label="Frecuencia" rules={[{ required: true }]}>
              <Select>
                <Option value="Diario">Diario</Option>
                <Option value="Semanal">Semanal</Option>
                <Option value="Mensual">Mensual</Option>
                <Option value="Trimestral">Trimestral</Option>
                <Option value="Semestral">Semestral</Option>
                <Option value="Anual">Anual</Option>
              </Select>
            </Form.Item>
            <Form.Item name="fechaInicio" label="Fecha de Inicio" rules={[{ required: true }]}>
              <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
            </Form.Item>
            
            <Form.Item label="Antelación de Notificación" required>
              <Input.Group compact>
                <Form.Item name="notification_value" noStyle rules={[{ required: true, message: '¡Valor requerido!' }]}>
                  <InputNumber min={1} style={{ width: 'calc(100% - 120px)' }} />
                </Form.Item>
                <Form.Item name="notification_unit" noStyle rules={[{ required: true, message: '¡Unidad requerida!' }]}>
                  <Select style={{ width: '120px' }}>
                    <Option value="horas">Horas</Option>
                    <Option value="dias">Días</Option>
                    <Option value="semanas">Semanas</Option>
                  </Select>
                </Form.Item>
              </Input.Group>
            </Form.Item>

            <Divider>Asignación</Divider>
            <Form.Item label="Asignar a">
              <Radio.Group value={assignmentType} onChange={e => { setAssignmentType(e.target.value); form.setFieldsValue({ assigned_user_id: undefined, assigned_role_id: undefined }); }}>
                <Radio.Button value="user">Usuario</Radio.Button>
                <Radio.Button value="role">Rol</Radio.Button>
              </Radio.Group>
            </Form.Item>
            {assignmentType === 'user' ? (
              <Form.Item name="assigned_user_id" label="Usuario" rules={[{ required: true }]}>
                <Select>{users.map(u => <Option key={u.id} value={u.id}>{u.username}</Option>)}</Select>
              </Form.Item>
            ) : (
              <Form.Item name="assigned_role_id" label="Rol" rules={[{ required: true }]}>
                <Select>{roles.map(r => <Option key={r.id} value={r.id}>{r.nombre}</Option>)}</Select>
              </Form.Item>
            )}
            <Form.Item style={{ marginTop: 24, textAlign: 'right' }}>
              <Space>
                <Button onClick={handleModalCancel}>Cancelar</Button>
                <Button type="primary" htmlType="submit" loading={submitting}>
                  {editingMaintenance ? 'Guardar Cambios' : 'Crear Mantenimiento'}
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>
      )}
    </div>
  );
};

export default MantenimientoPreventivo;