// src/pages/Usuarios.js
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
    Typography, Breadcrumb, Button, Table, Space, message, Spin, Alert,
    Popconfirm, Modal, Form, Input, Select, InputNumber, DatePicker, Tooltip, Row, Col, Statistic, Card, Tag
} from 'antd';
import {
    EditOutlined, DeleteOutlined, PlusOutlined, UserSwitchOutlined,
    FileExcelOutlined
} from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Usuarios.css';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

const Usuarios = () => {
  const [usuarios, setUsuarios] = useState([]);
  const [roles, setRoles] = useState([]);
  const [secciones, setSecciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [isSubmittingUser, setIsSubmittingUser] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  // Estados para Modal Asignación Turno
  const [isAssignModalVisible, setIsAssignModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [patterns, setPatterns] = useState([]);
  const [currentAssignment, setCurrentAssignment] = useState(null);
  const [loadingModal, setLoadingModal] = useState(false);
  const [assignmentForm] = Form.useForm();

  const { currentUser } = useAuth();

  // Determinar si el usuario puede gestionar usuarios
  const canManageUsers = useMemo(() => {
    console.log("Datos del usuario:", currentUser);
    // Forzar permisos para todos los usuarios (solución temporal)
    // return true; 

    if (!currentUser) return false;
    
    // Verificar si el usuario tiene rol de administrador
    // Comprobar varias posibles propiedades donde podría estar el rol
    return currentUser.role === "Administrador" ||
           currentUser.role === "administrador" ||
           currentUser.role_name === "Administrador" ||
           currentUser.id === 1; // Generalmente el ID 1 es el administrador
  }, [currentUser]);

  console.log("¿Puede gestionar usuarios?", canManageUsers);

  // Carga de Datos (incluye patterns)
  const loadData = useCallback(async () => {
    setLoading(true); 
    setError(null);
    try {
      // Verificar si tenemos token de autenticación
      const token = sessionStorage.getItem('access_token');
      if (!token) {
        console.log("No hay token de autenticación, redirigiendo al login");
        navigate('/login');
        return;
      }

      const [usersData, rolesData, seccionesData, patternsData] = await Promise.all([
        fetchWithAuth('/users'), 
        fetchWithAuth('/roles'), 
        fetchWithAuth('/secciones'), 
        fetchWithAuth('/shift-patterns')
      ]);
      
      console.log("Datos de usuarios cargados:", usersData);
      
      setUsuarios((usersData || []).map(u => ({...u, key: u.id})));
      setRoles(rolesData || []); 
      setSecciones(seccionesData || []); 
      setPatterns(patternsData || []);
    } catch (error) { 
      console.error("Error cargando datos:", error);
      message.error(`Error cargando datos: ${error.message}`); 
      setError('Error al cargar datos.'); 
    } finally { 
      setLoading(false); 
    }
  }, [navigate]);

  useEffect(() => {
    console.log("Usuarios.js: Ejecutando useEffect. Valor de currentUser:", currentUser);
    
    // Llamar a loadData una vez que sabemos que hay un usuario autenticado
    if (currentUser) {
      loadData();
    } else {
      // Si no hay usuario, podemos intentar verificar si hay un token
      const token = sessionStorage.getItem('access_token');
      if (token) {
        // Si hay token pero no usuario, probablemente estamos esperando la autenticación
        console.log("Hay token pero no usuario, esperando autenticación...");
      } else {
        // No hay token, redirigir al login
        navigate('/login');
      }
    }
  }, [currentUser, loadData, navigate]);

  // Función para manejar la edición de un usuario
  const handleEditUser = (record) => {
    setEditingUser(record);
    form.setFieldsValue({
      username: record.username,
      role_id: record.role_id,
      section_id: record.section_id || null
    });
    setModalVisible(true);
  };

  // Función para manejar la creación de un nuevo usuario
  const handleAddUser = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  // Función para manejar la eliminación de un usuario
  const handleDeleteUser = async (userId) => {
    try {
      await fetchWithAuth(`/users/${userId}`, {
        method: 'DELETE'
      });
      message.success('Usuario eliminado correctamente');
      loadData();
    } catch (error) {
      message.error(`Error al eliminar usuario: ${error.message}`);
    }
  };

  const handleUserFormSubmit = async (values) => {
    setIsSubmittingUser(true);
    const isEditing = !!editingUser;
    const url = isEditing ? `/users/${editingUser.id}` : '/users';
    const method = isEditing ? 'PUT' : 'POST';
    let payload = { ...values };
    if (isEditing) { delete payload.password; payload.section_id = payload.section_id || null; }
    else { payload.section_id = payload.section_id || null; }
    console.log(`Enviando ${method} a ${url}`, payload);
    try { 
      await fetchWithAuth(url, { 
        method, 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify(payload) 
      });
      message.success(`Usuario ${isEditing ? 'actualizado' : 'creado'}.`); 
      setModalVisible(false); 
      setEditingUser(null); 
      form.resetFields(); 
      loadData();
    } catch (error) { 
      console.error('Error guardando usuario:', error); 
      message.error(error.message || `Error ${isEditing ? 'actualizando' : 'creando'}.`); 
    }
    finally { 
      setIsSubmittingUser(false); 
    }
  };

  // --- Funciones Modal Asignación Turno ---
  const fetchCurrentAssignment = useCallback(async (userId) => {
    setLoadingModal(true); 
    setCurrentAssignment(null); 
    assignmentForm.resetFields(); 
    assignmentForm.setFieldsValue({ reference_date: dayjs('2024-01-01') });
    try { 
      const data = await fetchWithAuth(`/users/${userId}/shift-assignment`); 
      setCurrentAssignment(data); 
      assignmentForm.setFieldsValue({ 
        pattern_id: data.pattern_id, 
        reference_date: dayjs(data.reference_date), 
        offset_days: data.offset_days 
      }); 
    }
    catch (err) { 
      if (err.status !== 404) { 
        message.error(`Error cargando asignación: ${err.message}`); 
      } 
    }
    finally { 
      setLoadingModal(false); 
    }
  }, [assignmentForm]);

  const showAssignModal = (user) => {
    setSelectedUser(user); 
    fetchCurrentAssignment(user.id); 
    setIsAssignModalVisible(true);
  };

  const handleAssignOk = async () => {
    setLoadingModal(true);
    try { 
      const values = await assignmentForm.validateFields(); 
      const assignmentData = { 
        user_id: selectedUser.id, 
        pattern_id: values.pattern_id, 
        reference_date: values.reference_date.format('YYYY-MM-DD'), 
        offset_days: values.offset_days 
      };
      await fetchWithAuth('/shift-assignments', { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify(assignmentData) 
      });
      message.success(`Turno asignado a ${selectedUser.username}`); 
      setIsAssignModalVisible(false); 
      setSelectedUser(null);
    } catch (errorInfo) { 
      message.error(errorInfo?.message || 'Error al asignar'); 
    }
    finally { 
      setLoadingModal(false); 
    }
  };

  const handleAssignCancel = () => {
    setIsAssignModalVisible(false); 
    setSelectedUser(null); 
    setCurrentAssignment(null); 
    assignmentForm.resetFields();
  };

  // --- Columnas ---
  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: 'Usuario', dataIndex: 'username', key: 'username' },
    { title: 'Rol', dataIndex: 'role', key: 'role', render: (role) => <Tag color="blue">{role || 'Sin Rol'}</Tag> },
    { title: 'Sección', dataIndex: 'section', key: 'section', render: (section) => section || '-' },
    { 
      title: 'Acciones', 
      key: 'acciones', 
      width: 180, 
      align: 'center',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="Editar Usuario">
            <Button 
              icon={<EditOutlined />} 
              onClick={() => handleEditUser(record)} 
              size="small" 
              disabled={!canManageUsers} 
            />
          </Tooltip>
          <Tooltip title="Asignar/Ver Turno">
            <Button 
              icon={<UserSwitchOutlined />} 
              onClick={() => showAssignModal(record)} 
              size="small" 
            />
          </Tooltip>
          <Tooltip title="Eliminar Usuario">
            <Popconfirm 
              title={`¿Eliminar a ${record.username}?`} 
              onConfirm={() => handleDeleteUser(record.id)} 
              okText="Sí" 
              cancelText="No" 
              okType="danger" 
              disabled={currentUser?.id === record.id || !canManageUsers}
            >
              <Button 
                icon={<DeleteOutlined />} 
                danger 
                size="small" 
                disabled={currentUser?.id === record.id || !canManageUsers} 
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} className="page-title" style={{ marginBottom: 0 }}>Gestión de Usuarios</Title>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={handleAddUser} 
          disabled={!canManageUsers}
        > 
          Nuevo Usuario 
        </Button>
      </div>

      {error && (
        <Alert 
          message="Error" 
          description={error} 
          type="error" 
          showIcon 
          closable 
          style={{marginBottom: 16}} 
          onClose={() => setError(null)} 
        />
      )}

      <Card className="table-container" style={{marginTop: 16}}>
        <Spin spinning={loading}>
          <Table 
            columns={columns} 
            dataSource={usuarios} 
            rowKey="key" 
            pagination={{ pageSize: 10 }} 
            size="small" 
            bordered 
          />
        </Spin>
      </Card>

      {/* Modal Crear/Editar Usuario */}
      <Modal
        title={editingUser ? `Editar Usuario: ${editingUser.username}` : "Nuevo Usuario"}
        open={modalVisible}
        onCancel={() => { setModalVisible(false); setEditingUser(null); form.resetFields(); }}
        footer={null} 
        destroyOnClose 
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleUserFormSubmit}>
          <Form.Item name="username" label="Nombre de Usuario" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          {!editingUser && (
            <Form.Item name="password" label="Contraseña" rules={[{ required: true }]}>
              <Input.Password />
            </Form.Item>
          )}
          <Form.Item name="role_id" label="Rol" rules={[{ required: true }]}>
            <Select>
              {roles.map(role => (
                <Option key={role.id} value={role.id}>{role.nombre}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="section_id" label="Sección (Opcional)">
            <Select allowClear>
              {secciones.map(section => (
                <Option key={section.id} value={section.id}>{section.nombre}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={() => { setModalVisible(false); setEditingUser(null); form.resetFields(); }}>
                Cancelar
              </Button>
              <Button type="primary" htmlType="submit" loading={isSubmittingUser}>
                {editingUser ? 'Actualizar Usuario' : 'Crear Usuario'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Modal Asignar Turno */}
      <Modal 
        title={`Asignar Turno a ${selectedUser?.username || ''}`} 
        open={isAssignModalVisible} 
        onOk={handleAssignOk} 
        onCancel={handleAssignCancel} 
        confirmLoading={loadingModal} 
        destroyOnClose 
        width={600} 
        okText="Guardar Asignación" 
        cancelText="Cancelar"
      >
        <Spin spinning={loadingModal}>
          <Form 
            form={assignmentForm} 
            layout="vertical" 
            name="assign_shift_form" 
            initialValues={{ reference_date: dayjs('2024-01-01') }}
          >
            <Form.Item name="pattern_id" label="Patrón de Turno" rules={[{ required: true }]}>
              <Select placeholder="Selecciona" loading={patterns.length === 0} allowClear>
                {patterns.map(pattern => (
                  <Option key={pattern.id} value={pattern.id}>
                    {pattern.name} ({pattern.cycle_length_days} días)
                  </Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item 
              name="reference_date" 
              label="Fecha Referencia" 
              tooltip="Fecha ancla (01/01/2024)." 
              rules={[{ required: true }]}
            >
              <DatePicker format="YYYY-MM-DD" disabled style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item 
              name="offset_days" 
              label="Días Desfase (Offset)" 
              rules={[{ required: true }, {type: 'integer', min: 0}]} 
              tooltip="Día del ciclo (índice 0) en Fecha Ref."
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
            {currentAssignment && (
              <Alert 
                type="info" 
                showIcon 
                message="Asignación Actual" 
                description={
                  <>
                    Patrón: {patterns.find(p => p.id === currentAssignment.pattern_id)?.name || '?'}
                    <br/>
                    Offset: {currentAssignment.offset_days}
                    <br/>
                    Fecha Ref: {currentAssignment.reference_date}
                  </>
                } 
                style={{ marginBottom: 16 }}
              />
            )}
          </Form>
        </Spin>
      </Modal>
    </div>
  );
};

export default Usuarios;