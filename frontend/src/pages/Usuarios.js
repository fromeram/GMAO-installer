import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Table, Button, Modal, Form, Input, Select, Space, Typography, message, 
  Popconfirm, Tag, Tooltip, Card, Row, Col, Divider, Alert, Switch, DatePicker
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, KeyOutlined, UserSwitchOutlined,
  PlayCircleOutlined, StopOutlined, CalculatorOutlined, ReloadOutlined,
  ClearOutlined, WarningOutlined, UserDeleteOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import '../styles/CommonPage.css';
import dayjs from 'dayjs';

const { Title } = Typography;
const { Option } = Select;

// Componente para el indicador de fortaleza de contraseña
const PasswordStrengthIndicator = ({ password }) => {
  const getStrength = (pwd) => {
    if (!pwd) return { score: 0, text: '', color: '' };
    
    let score = 0;
    const checks = {
      length: pwd.length >= 8,
      lowercase: /[a-z]/.test(pwd),
      uppercase: /[A-Z]/.test(pwd),
      numbers: /\d/.test(pwd),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(pwd)
    };
    
    score = Object.values(checks).filter(Boolean).length;
    
    const levels = [
      { score: 0, text: 'Sin contraseña', color: '#d9d9d9' },
      { score: 1, text: 'Muy débil', color: '#ff4d4f' },
      { score: 2, text: 'Débil', color: '#ff7a45' },
      { score: 3, text: 'Regular', color: '#ffa940' },
      { score: 4, text: 'Fuerte', color: '#73d13d' },
      { score: 5, text: 'Muy fuerte', color: '#52c41a' }
    ];
    
    return levels[score];
  };

  const strength = getStrength(password);
  
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ 
        height: 6, 
        backgroundColor: '#f0f0f0', 
        borderRadius: 3, 
        overflow: 'hidden',
        marginBottom: 4
      }}>
        <div style={{ 
          height: '100%', 
          width: `${(strength.score / 5) * 100}%`, 
          backgroundColor: strength.color, 
          transition: 'all 0.3s'
        }} />
      </div>
      <div style={{ fontSize: 12, color: strength.color, fontWeight: 500 }}>
        {strength.text}
      </div>
      {password && (
        <div style={{ fontSize: 11, color: '#666', marginTop: 4 }}>
          <ul style={{ margin: 0, paddingLeft: 16 }}>
            <li style={{ color: password.length >= 8 ? '#52c41a' : '#ff4d4f' }}>
              {password.length >= 8 ? '✓' : '✗'} Mínimo 8 caracteres
            </li>
            <li style={{ color: /[a-z]/.test(password) ? '#52c41a' : '#ff4d4f' }}>
              {/[a-z]/.test(password) ? '✓' : '✗'} Letras minúsculas
            </li>
            <li style={{ color: /[A-Z]/.test(password) ? '#52c41a' : '#ff4d4f' }}>
              {/[A-Z]/.test(password) ? '✓' : '✗'} Letras mayúsculas
            </li>
            <li style={{ color: /\d/.test(password) ? '#52c41a' : '#ff4d4f' }}>
              {/\d/.test(password) ? '✓' : '✗'} Números
            </li>
            <li style={{ color: /[!@#$%^&*(),.?":{}|<>]/.test(password) ? '#52c41a' : '#ff4d4f' }}>
              {/[!@#$%^&*(),.?":{}|<>]/.test(password) ? '✓' : '✗'} Caracteres especiales
            </li>
          </ul>
        </div>
      )}
    </div>
  );
};

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

  // ✅ NUEVOS ESTADOS PARA LIMPIEZA
  const [cleanupModalVisible, setCleanupModalVisible] = useState(false);
  const [inactiveUserRequests, setInactiveUserRequests] = useState([]);
  const [loadingCleanup, setLoadingCleanup] = useState(false);
  const [cleanupStats, setCleanupStats] = useState({
    totalRequests: 0,
    inactiveUsers: 0
  });

  // Estados para Modal Asignación Turno
  const [isAssignModalVisible, setIsAssignModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [patterns, setPatterns] = useState([]);
  const [currentAssignment, setCurrentAssignment] = useState(null);
  const [loadingModal, setLoadingModal] = useState(false);
  const [assignmentForm] = Form.useForm();
  
  // Estados para el calculador de offset
  const [startDate, setStartDate] = useState(dayjs());
  const [startPosition, setStartPosition] = useState(0);
  const [calculatingOffset, setCalculatingOffset] = useState(false);
  const [selectedPattern, setSelectedPattern] = useState(null);

  // Estados para cambio de contraseña
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [userToChangePassword, setUserToChangePassword] = useState(null);
  const [changingPassword, setChangingPassword] = useState(false);
  const [passwordForm] = Form.useForm();
  const [passwordValue, setPasswordValue] = useState('');
  const [confirmPasswordValue, setConfirmPasswordValue] = useState('');

  // Estados para filtros y gestión de estado
  const [showInactive, setShowInactive] = useState(true);

  const { currentUser } = useAuth();

  // Determinar si el usuario puede gestionar usuarios
  const canManageUsers = useMemo(() => {
    console.log("Datos del usuario:", currentUser);
    
    if (!currentUser) return false;
    
    // Verificar si el usuario tiene rol de administrador
    return currentUser.role === "Administrador" ||
           currentUser.role === "administrador" ||
           currentUser.role_name === "Administrador" ||
           currentUser.id === 1;
  }, [currentUser]);

  console.log("¿Puede gestionar usuarios?", canManageUsers);

  // ✅ FUNCIÓN MODIFICADA DE CARGA DE DATOS - INCLUIR USUARIOS INACTIVOS
  const loadData = useCallback(async () => {
    setLoading(true); 
    setError(null);
    try {
      const token = sessionStorage.getItem('access_token');
      if (!token) {
        console.log("No hay token de autenticación, redirigiendo al login");
        navigate('/login');
        return;
      }

      // ✅ MODIFICACIÓN: Añadir parámetro para incluir usuarios inactivos
      const [usersData, rolesData, seccionesData, patternsData] = await Promise.all([
        fetchWithAuth('/users?include_inactive=true'), // ✅ CAMBIO AQUÍ
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
    
    if (currentUser) {
      loadData();
    } else {
      const token = sessionStorage.getItem('access_token');
      if (token) {
        console.log("Hay token pero no usuario, esperando autenticación...");
      } else {
        navigate('/login');
      }
    }
  }, [currentUser, loadData, navigate]);

  // ✅ NUEVAS FUNCIONES PARA LIMPIEZA
  const fetchInactiveUserRequests = async () => {
    try {
      setLoadingCleanup(true);
      const response = await fetchWithAuth('/vacation-requests/inactive-users');
      
      const requests = response.inactive_user_requests || [];
      setInactiveUserRequests(requests);
      
      // Calcular estadísticas
      const uniqueUsers = new Set(requests.map(req => req.user_id));
      setCleanupStats({
        totalRequests: requests.length,
        inactiveUsers: uniqueUsers.size
      });
      
    } catch (error) {
      console.error('Error:', error);
      message.error('Error al cargar solicitudes de usuarios inactivos');
    } finally {
      setLoadingCleanup(false);
    }
  };

  const handleCleanupAll = async () => {
    Modal.confirm({
      title: '⚠️ ¿Confirmar limpieza masiva?',
      content: (
        <div>
          <p>Esta acción eliminará <strong>TODAS</strong> las solicitudes de vacaciones pendientes de usuarios inactivos.</p>
          <Alert 
            message="Esta acción no se puede deshacer" 
            type="warning" 
            showIcon 
            style={{ margin: '10px 0' }}
          />
          <p>
            Total a eliminar: <strong>{cleanupStats.totalRequests} solicitudes</strong> de <strong>{cleanupStats.inactiveUsers} usuarios inactivos</strong>
          </p>
        </div>
      ),
      okText: 'Sí, limpiar todo',
      cancelText: 'Cancelar',
      okType: 'danger',
      width: 500,
      onOk: async () => {
        try {
          setLoadingCleanup(true);
          const response = await fetchWithAuth('/vacation-requests/cleanup-inactive-users', {
            method: 'DELETE'
          });
          
          message.success(`✅ Limpieza completada: ${response.deleted_count} solicitudes eliminadas`);
          
          // Recargar datos
          fetchInactiveUserRequests();
          
        } catch (error) {
          console.error('Error:', error);
          message.error('Error durante la limpieza');
        } finally {
          setLoadingCleanup(false);
        }
      }
    });
  };

  const handleDeleteIndividualRequest = async (requestId, username) => {
    try {
      await fetchWithAuth(`/vacation-requests/${requestId}`, {
        method: 'DELETE'
      });
      
      message.success(`Solicitud de ${username} eliminada`);
      fetchInactiveUserRequests(); // Recargar
      
    } catch (error) {
      console.error('Error:', error);
      message.error('Error al eliminar la solicitud');
    }
  };

  const openCleanupModal = () => {
    setCleanupModalVisible(true);
    fetchInactiveUserRequests();
  };

  // ✅ FUNCIÓN PARA ACTIVAR/DESACTIVAR USUARIOS
  const handleToggleUserStatus = async (userId, currentStatus, username) => {
    try {
      const newStatus = !currentStatus;
      const action = newStatus ? 'activar' : 'desactivar';
      
      const confirmed = await new Promise((resolve) => {
        Modal.confirm({
          title: `¿Confirmar ${action} usuario?`,
          content: `¿Está seguro de que desea ${action} al usuario "${username}"?`,
          okText: `Sí, ${action}`,
          cancelText: 'Cancelar',
          okButtonProps: { danger: !newStatus },
          onOk: () => resolve(true),
          onCancel: () => resolve(false)
        });
      });

      if (!confirmed) return;

      const endpoint = newStatus ? 
        `/users/${userId}/activate` : 
        `/users/${userId}/deactivate`;

      await fetchWithAuth(endpoint, {
        method: 'PUT'
      });

      message.success(`Usuario ${newStatus ? 'activado' : 'desactivado'} correctamente`);
      
      // Recargar lista de usuarios
      loadData();
      
    } catch (error) {
      console.error('Error cambiando estado del usuario:', error);
      // Usar currentStatus para determinar la acción que se intentó
      const attemptedAction = !currentStatus ? 'activar' : 'desactivar';
      message.error(`Error al ${attemptedAction} usuario: ${error.message || 'Error desconocido'}`);
    }
  };

  // ✅ FUNCIÓN PARA MOSTRAR MODAL DE CAMBIO DE CONTRASEÑA
  const showPasswordModal = (user) => {
    setUserToChangePassword(user);
    setPasswordModalVisible(true);
    setPasswordValue('');
    setConfirmPasswordValue('');
    passwordForm.resetFields();
  };

  // ✅ FUNCIÓN PARA CAMBIAR CONTRASEÑA
  const handlePasswordChange = async (values) => {
    setChangingPassword(true);
    
    try {
      const response = await fetchWithAuth(`/users/${userToChangePassword.id}/change-password`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          new_password: values.new_password,
          confirm_password: values.confirm_password
        })
      });

      if (response.success) {
        message.success({
          content: `Contraseña cambiada correctamente para ${userToChangePassword.username}`,
          duration: 5,
          style: {
            marginTop: '20vh',
          }
        });
        setPasswordModalVisible(false);
        setUserToChangePassword(null);
        setPasswordValue('');
        setConfirmPasswordValue('');
        passwordForm.resetFields();
      } else {
        message.error('Error al cambiar la contraseña');
      }
    } catch (error) {
      console.error('Error cambiando contraseña:', error);
      message.error(`Error al cambiar contraseña: ${error.message}`);
    } finally {
      setChangingPassword(false);
    }
  };

  // ✅ FUNCIÓN PARA CANCELAR CAMBIO DE CONTRASEÑA
  const handlePasswordCancel = () => {
    setPasswordModalVisible(false);
    setUserToChangePassword(null);
    setPasswordValue('');
    setConfirmPasswordValue('');
    passwordForm.resetFields();
  };

  // Funciones existentes...
  const calculateOffset = useCallback(async () => {
    if (!selectedPattern || !startDate) {
      message.error('Selecciona un patrón y una fecha de inicio');
      return;
    }

    setCalculatingOffset(true);
    
    try {
      const pattern = patterns.find(p => p.id === selectedPattern.id);
      if (!pattern) {
        throw new Error('Patrón no encontrado');
      }

      const cycleLength = pattern.cycle_length_days;
      if (cycleLength <= 0) {
        throw new Error('Longitud de ciclo inválida');
      }

      console.log("=== CALCULANDO OFFSET ===");
      console.log("Fecha objetivo:", startDate.format('YYYY-MM-DD'));
      console.log("Posición deseada:", startPosition);
      console.log("Patrón:", pattern.name);
      console.log("Secuencia:", pattern.pattern_sequence);
      console.log("Longitud de ciclo:", cycleLength);

      const today = dayjs().startOf('day');
      const startDateStartOfDay = startDate.startOf('day');
      const daysDifference = startDateStartOfDay.diff(today, 'day');
      
      console.log("Diferencia en días desde hoy:", daysDifference);

      const calculatedOffset = (startPosition - (daysDifference % cycleLength) + cycleLength) % cycleLength;
      
      console.log("Offset calculado:", calculatedOffset);
      
      const testDate = startDateStartOfDay.add(calculatedOffset, 'day');
      const testCycleDay = ((daysDifference + calculatedOffset) % cycleLength + cycleLength) % cycleLength;
      console.log("- Test: Offset aplicado dará posición:", testCycleDay);
      console.log("- Test: Fecha resultante:", testDate.format('YYYY-MM-DD'));
      
      assignmentForm.setFieldsValue({
        offset_days: calculatedOffset
      });
      
      message.success(`Offset calculado: ${calculatedOffset}`);
    } catch (error) {
      console.error('Error calculando offset:', error);
      message.error(`Error calculando offset: ${error.message}`);
    } finally {
      setCalculatingOffset(false);
    }
  }, [assignmentForm, patterns, startDate, startPosition]);

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

  // Función para manejar la eliminación de un usuario (solo usuarios inactivos)
  const handleDeleteUser = async (userId) => {
    try {
      await fetchWithAuth(`/users/${userId}`, {
        method: 'DELETE'
      });
      message.success('Usuario eliminado permanentemente');
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
    if (isEditing) { 
      delete payload.password; 
      payload.section_id = payload.section_id || null; 
    } else { 
      payload.section_id = payload.section_id || null; 
    }
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
      message.error(error.message || `Error ${isEditing ? 'actualizando' : 'creando'} usuario.`); 
    } finally { 
      setIsSubmittingUser(false); 
    }
  };

  // Otras funciones de gestión de turnos...
  const showAssignModal = async (user) => {
    setSelectedUser(user);
    setIsAssignModalVisible(true);
    setLoadingModal(true);
    setCurrentAssignment(null);

    try {
      const response = await fetchWithAuth(`/shift-assignments/user/${user.id}`);
      if (response && response.assignment) {
        setCurrentAssignment(response.assignment);
        assignmentForm.setFieldsValue({
          pattern_id: response.assignment.pattern.id,
          offset_days: response.assignment.offset_days
        });
        setSelectedPattern(response.assignment.pattern);
      } else {
        assignmentForm.resetFields();
        setSelectedPattern(null);
      }
    } catch (error) {
      if (error.message.includes('404')) {
        console.log(`Usuario ${user.username} no tiene asignación de turno`);
        assignmentForm.resetFields();
        setSelectedPattern(null);
      } else {
        console.error('Error cargando asignación:', error);
        message.error(`Error cargando asignación: ${error.message}`);
      }
    } finally {
      setLoadingModal(false);
    }
  };

  const handleAssignSubmit = async (values) => {
    try {
      setLoadingModal(true);
      const url = currentAssignment 
        ? `/shift-assignments/${currentAssignment.id}`
        : '/shift-assignments';
      
      const method = currentAssignment ? 'PUT' : 'POST';
      const payload = currentAssignment 
        ? { pattern_id: values.pattern_id, offset_days: values.offset_days }
        : { ...values, user_id: selectedUser.id };

      await fetchWithAuth(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      message.success(`Asignación de turno ${currentAssignment ? 'actualizada' : 'creada'} correctamente`);
      setIsAssignModalVisible(false);
      setSelectedUser(null);
      setCurrentAssignment(null);
      assignmentForm.resetFields();
    } catch (error) {
      console.error('Error guardando asignación:', error);
      message.error(`Error al ${currentAssignment ? 'actualizar' : 'crear'} asignación: ${error.message}`);
    } finally {
      setLoadingModal(false);
    }
  };

  const handleDeleteAssignment = async (userId, username) => {
    try {
      const confirmed = await new Promise((resolve) => {
        Modal.confirm({
          title: 'Confirmar eliminación',
          content: `Esta acción eliminará la asignación de turno de ${username || 'usuario'}. 
Esta acción no puede deshacerse.`,
          okText: 'Sí, eliminar',
          cancelText: 'Cancelar',
          okButtonProps: { danger: true },
          onOk: () => resolve(true),
          onCancel: () => resolve(false)
        });
      });

      if (!confirmed) return;

      await fetchWithAuth(`/shift-assignments/user/${userId}`, {
        method: 'DELETE',
      });

      message.success(`Asignación de turno de ${username || 'usuario'} eliminada correctamente`);
      
      if (selectedUser && selectedUser.id === userId) {
        setCurrentAssignment(null);
      }
    } catch (error) {
      console.error('Error eliminando asignación de turno:', error);
      message.error(`Error al eliminar la asignación: ${error.message || 'Error desconocido'}`);
    }
  };

  const handlePatternChange = (patternId) => {
    const pattern = patterns.find(p => p.id === patternId);
    setSelectedPattern(pattern);
    setStartPosition(0);
  };

  // ✅ FUNCIÓN PARA FILTRAR USUARIOS
  const filteredUsuarios = usuarios.filter(user => {
    if (showInactive) return true;
    return user.active;
  });

  // ✅ COLUMNAS PARA LA TABLA DE LIMPIEZA
  const cleanupColumns = [
    {
      title: 'Usuario',
      dataIndex: 'username',
      key: 'username',
      render: (username, record) => (
        <Space>
          <UserDeleteOutlined style={{ color: '#ff4d4f' }} />
          <span>{username}</span>
          <Tag color="error" size="small">INACTIVO</Tag>
        </Space>
      )
    },
    {
      title: 'Fechas Solicitadas',
      key: 'dates',
      render: (_, record) => (
        <div>
          <div><strong>Inicio:</strong> {record.start_date}</div>
          <div><strong>Fin:</strong> {record.end_date}</div>
        </div>
      )
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color="gold">{status}</Tag>
      )
    },
    {
      title: 'Creada',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleDateString()
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Button
          icon={<DeleteOutlined />}
          danger
          size="small"
          onClick={() => handleDeleteIndividualRequest(record.id, record.username)}
          title="Eliminar esta solicitud"
        />
      )
    }
  ];

  // ✅ COLUMNAS MODIFICADAS CON ESTADO Y CONTROLES
  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: 'Usuario', dataIndex: 'username', key: 'username' },
    { title: 'Rol', dataIndex: 'role', key: 'role', render: (role) => <Tag color="blue">{role || 'Sin Rol'}</Tag> },
    { title: 'Sección', dataIndex: 'section', key: 'section', render: (section) => section || '-' },
    {
      title: 'Estado',
      dataIndex: 'active',
      key: 'active',
      width: 100,
      render: (active, record) => (
        <Tag color={active ? 'success' : 'error'}>
          {active ? 'Activo' : 'Inactivo'}
        </Tag>
      )
    },
    { 
      title: 'Acciones', 
      key: 'acciones', 
      width: 320,
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
          <Tooltip title="Cambiar Contraseña">
            <Button 
              icon={<KeyOutlined />} 
              onClick={() => showPasswordModal(record)} 
              size="small" 
              disabled={!canManageUsers}
              className="password-change-btn"
              style={{ color: '#ff7a00', borderColor: '#ff7a00' }}
            />
          </Tooltip>
          <Tooltip title="Asignar/Ver Turno">
            <Button 
              icon={<UserSwitchOutlined />} 
              onClick={() => showAssignModal(record)} 
              size="small" 
            />
          </Tooltip>
          {/* ✅ NUEVO: Botón para activar/desactivar */}
          <Tooltip title={record.active ? 'Desactivar Usuario' : 'Activar Usuario'}>
            <Button 
              icon={record.active ? <StopOutlined /> : <PlayCircleOutlined />}
              onClick={() => handleToggleUserStatus(record.id, record.active, record.username)}
              size="small" 
              disabled={currentUser?.id === record.id || !canManageUsers}
              danger={record.active}
              type={record.active ? 'default' : 'primary'}
            />
          </Tooltip>
          {/* Botón de eliminar solo para usuarios inactivos */}
          <Tooltip title="Eliminar Usuario Permanentemente">
            <Popconfirm 
              title={`¿Eliminar permanentemente al usuario ${record.username}?`}
              description="Esta acción no se puede deshacer. Se recomienda desactivar en lugar de eliminar."
              onConfirm={() => handleDeleteUser(record.id)} 
              okText="Sí, eliminar" 
              cancelText="Cancelar" 
              okType="danger" 
              disabled={currentUser?.id === record.id || !canManageUsers || record.active}
            >
              <Button 
                icon={<DeleteOutlined />}
                danger 
                size="small" 
                disabled={currentUser?.id === record.id || !canManageUsers || record.active}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  if (loading) {
    return (
      <div className="common-page">
        <Card>
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <div style={{ fontSize: '18px', marginBottom: '16px' }}>Cargando usuarios...</div>
          </div>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="common-page">
        <Card>
          <Alert message="Error" description={error} type="error" showIcon />
        </Card>
      </div>
    );
  }

  return (
    <div className="common-page">
      <style>{`
        .user-inactive-row {
          background-color: #fff2f0;
          opacity: 0.7;
        }
        .user-inactive-row:hover {
          background-color: #ffebe8 !important;
          opacity: 1;
        }
        .password-change-btn {
          border-color: #ff7a00;
          color: #ff7a00;
        }
        .password-change-btn:hover {
          border-color: #ff9c3a;
          color: #ff9c3a;
        }
      `}</style>
      
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Title level={2}>Gestión de Usuarios</Title>
          
          {/* ✅ CONTROLES DE FILTRO Y ACCIONES CON LIMPIEZA */}
          <Space style={{ marginBottom: 16 }}>
            <Switch
              checked={showInactive}
              onChange={setShowInactive}
              checkedChildren="Mostrar inactivos"
              unCheckedChildren="Solo activos"
            />
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={handleAddUser}
              disabled={!canManageUsers}
            >
              Nuevo Usuario
            </Button>
            <Button 
              icon={<ReloadOutlined />}
              onClick={loadData}
              loading={loading}
            >
              Recargar
            </Button>
            {/* ✅ NUEVO BOTÓN DE LIMPIEZA */}
            <Button 
              icon={<ClearOutlined />}
              onClick={openCleanupModal}
              disabled={!canManageUsers}
              style={{ color: '#fa8c16', borderColor: '#fa8c16' }}
            >
              Limpieza
            </Button>
          </Space>

          {/* Mostrar estadísticas */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card size="small">
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                    {usuarios.filter(u => u.active).length}
                  </div>
                  <div style={{ color: '#666' }}>Usuarios Activos</div>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff4d4f' }}>
                    {usuarios.filter(u => !u.active).length}
                  </div>
                  <div style={{ color: '#666' }}>Usuarios Inactivos</div>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                    {usuarios.length}
                  </div>
                  <div style={{ color: '#666' }}>Total Usuarios</div>
                </div>
              </Card>
            </Col>
          </Row>
        </div>

        <Table
          columns={columns}
          dataSource={filteredUsuarios}
          rowKey="id"
          loading={loading}
          pagination={{ 
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} usuarios`
          }}
          size="small"
          rowClassName={(record) => record.active ? '' : 'user-inactive-row'}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* Modal para crear/editar usuario */}
      <Modal
        title={editingUser ? 'Editar Usuario' : 'Crear Usuario'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingUser(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUserFormSubmit}
        >
          <Form.Item
            name="username"
            label="Nombre de Usuario"
            rules={[
              { required: true, message: 'El nombre de usuario es obligatorio' },
              { min: 3, message: 'Mínimo 3 caracteres' },
              { max: 50, message: 'Máximo 50 caracteres' }
            ]}
          >
            <Input placeholder="Nombre de usuario" />
          </Form.Item>

          {!editingUser && (
            <Form.Item
              name="password"
              label="Contraseña"
              rules={[
                { required: true, message: 'La contraseña es obligatoria' },
                { min: 8, message: 'Mínimo 8 caracteres' },
                {
                  pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>])/,
                  message: 'Debe contener al menos: 1 minúscula, 1 mayúscula, 1 número y 1 carácter especial'
                }
              ]}
            >
              <Input.Password
                placeholder="Contraseña"
                onChange={(e) => setPasswordValue(e.target.value)}
              />
            </Form.Item>
          )}

          {!editingUser && passwordValue && (
            <PasswordStrengthIndicator password={passwordValue} />
          )}

          <Form.Item
            name="role_id"
            label="Rol"
            rules={[{ required: true, message: 'Seleccione un rol' }]}
          >
            <Select placeholder="Seleccionar rol">
              {roles.map(role => (
                <Option key={role.id} value={role.id}>
                  {role.nombre}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="section_id"
            label="Sección (Opcional)"
          >
            <Select placeholder="Seleccionar sección" allowClear>
              {secciones.map(seccion => (
                <Option key={seccion.id} value={seccion.id}>
                  {seccion.nombre}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={isSubmittingUser}
              >
                {editingUser ? 'Actualizar' : 'Crear'} Usuario
              </Button>
              <Button
                onClick={() => {
                  setModalVisible(false);
                  setEditingUser(null);
                  form.resetFields();
                }}
              >
                Cancelar
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* ✅ MODAL PARA CAMBIO DE CONTRASEÑA */}
      <Modal
        title={`Cambiar Contraseña - ${userToChangePassword?.username}`}
        open={passwordModalVisible}
        onCancel={handlePasswordCancel}
        footer={null}
        width={500}
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handlePasswordChange}
        >
          <Alert
            message="Cambio de Contraseña"
            description={`Está cambiando la contraseña para el usuario "${userToChangePassword?.username}". La nueva contraseña debe cumplir con los requisitos de seguridad.`}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form.Item
            name="new_password"
            label="Nueva Contraseña"
            rules={[
              { required: true, message: 'La nueva contraseña es obligatoria' },
              { min: 8, message: 'Mínimo 8 caracteres' },
              {
                pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>])/,
                message: 'Debe contener al menos: 1 minúscula, 1 mayúscula, 1 número y 1 carácter especial'
              }
            ]}
          >
            <Input.Password
              placeholder="Nueva contraseña"
              onChange={(e) => setPasswordValue(e.target.value)}
            />
          </Form.Item>

          {passwordValue && (
            <PasswordStrengthIndicator password={passwordValue} />
          )}

          <Form.Item
            name="confirm_password"
            label="Confirmar Contraseña"
            dependencies={['new_password']}
            rules={[
              { required: true, message: 'Confirme la nueva contraseña' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Las contraseñas no coinciden'));
                },
              }),
            ]}
          >
            <Input.Password
              placeholder="Confirmar contraseña"
              onChange={(e) => setConfirmPasswordValue(e.target.value)}
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={changingPassword}
                danger
              >
                Cambiar Contraseña
              </Button>
              <Button onClick={handlePasswordCancel}>
                Cancelar
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* ✅ MODAL PARA LIMPIEZA DE SOLICITUDES */}
      <Modal
        title="🧹 Limpieza de Solicitudes - Usuarios Inactivos"
        open={cleanupModalVisible}
        onCancel={() => {
          setCleanupModalVisible(false);
          setInactiveUserRequests([]);
        }}
        footer={null}
        width={900}
      >
        <div style={{ marginBottom: 16 }}>
          {/* Estadísticas */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Card size="small" style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#faad14' }}>
                  {cleanupStats.totalRequests}
                </div>
                <div style={{ color: '#666', fontSize: '12px' }}>Solicitudes Pendientes</div>
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small" style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#ff4d4f' }}>
                  {cleanupStats.inactiveUsers}
                </div>
                <div style={{ color: '#666', fontSize: '12px' }}>Usuarios Inactivos</div>
              </Card>
            </Col>
            <Col span={8}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={fetchInactiveUserRequests}
                  loading={loadingCleanup}
                  size="small"
                  style={{ width: '100%' }}
                >
                  Recargar
                </Button>
                <Button 
                  type="primary"
                  danger
                  icon={<ClearOutlined />}
                  onClick={handleCleanupAll}
                  disabled={cleanupStats.totalRequests === 0}
                  loading={loadingCleanup}
                  size="small"
                  style={{ width: '100%' }}
                >
                  Limpiar Todo
                </Button>
              </Space>
            </Col>
          </Row>

          {/* Alerta informativa */}
          {cleanupStats.totalRequests > 0 ? (
            <Alert
              message="⚠️ Problema detectado"
              description={
                <div>
                  Se encontraron <strong>{cleanupStats.totalRequests} solicitudes de vacaciones pendientes</strong> de usuarios que están inactivos. 
                  Esto causa notificaciones persistentes que no se pueden gestionar desde el calendario normal.
                  <br /><br />
                  <strong>Recomendación:</strong> Utilizar "Limpiar Todo" para eliminar todas las solicitudes de usuarios inactivos de una vez.
                </div>
              }
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
          ) : (
            <Alert
              message="✅ Sistema limpio"
              description="No hay solicitudes de usuarios inactivos que requieran limpieza."
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}
        </div>

        {/* Tabla de solicitudes */}
        <Table
          columns={cleanupColumns}
          dataSource={inactiveUserRequests}
          rowKey="id"
          loading={loadingCleanup}
          pagination={{ 
            pageSize: 8,
            showSizeChanger: false,
            showTotal: (total) => `Total: ${total} solicitudes`
          }}
          locale={{
            emptyText: cleanupStats.totalRequests === 0 ? 
              '✅ No hay solicitudes de usuarios inactivos' : 
              'Cargando...'
          }}
          size="small"
        />

        {/* Información adicional */}
        <Alert
          message="💡 Prevención futura"
          description={
            <div>
              <p><strong>Para evitar este problema en el futuro:</strong></p>
              <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                <li>Los usuarios inactivos ya no podrán hacer login (solución aplicada)</li>
                <li>Use "Desactivar" en lugar de "Eliminar" usuarios</li>
                <li>Revise periódicamente usuarios inactivos con solicitudes pendientes</li>
              </ul>
            </div>
          }
          type="info"
          showIcon
          style={{ marginTop: 16 }}
        />
      </Modal>

      {/* Modal para asignación de turnos */}
      <Modal
        title={`Asignación de Turno - ${selectedUser?.username}`}
        open={isAssignModalVisible}
        onCancel={() => {
          setIsAssignModalVisible(false);
          setSelectedUser(null);
          setCurrentAssignment(null);
          assignmentForm.resetFields();
        }}
        footer={null}
        width={700}
      >
        <div style={{ marginBottom: 16 }}>
          {currentAssignment ? (
            <Alert
              message="Asignación Existente"
              description={`El usuario ${selectedUser?.username} tiene asignado el patrón "${currentAssignment.pattern?.name}" con offset ${currentAssignment.offset_days} días.`}
              type="info"
              showIcon
            />
          ) : (
            <Alert
              message="Sin Asignación"
              description={`El usuario ${selectedUser?.username} no tiene asignación de turno.`}
              type="warning"
              showIcon
            />
          )}
        </div>

        <Form
          form={assignmentForm}
          layout="vertical"
          onFinish={handleAssignSubmit}
        >
          <Form.Item
            name="pattern_id"
            label="Patrón de Turno"
            rules={[{ required: true, message: 'Seleccione un patrón' }]}
          >
            <Select 
              placeholder="Seleccionar patrón"
              onChange={handlePatternChange}
            >
              {patterns.map(pattern => (
                <Option key={pattern.id} value={pattern.id}>
                  {pattern.name} - {pattern.pattern_sequence} ({pattern.cycle_length_days} días)
                </Option>
              ))}
            </Select>
          </Form.Item>

          {selectedPattern && (
            <>
              <Divider>Calculadora de Offset</Divider>
              <Row gutter={16}>
                <Col span={8}>
                  <div style={{ marginBottom: 8 }}>
                    <strong>Fecha de Inicio:</strong>
                  </div>
                  <DatePicker
                    value={startDate}
                    onChange={setStartDate}
                    style={{ width: '100%' }}
                  />
                </Col>
                <Col span={8}>
                  <div style={{ marginBottom: 8 }}>
                    <strong>Posición Deseada:</strong>
                  </div>
                  <Select
                    value={startPosition}
                    onChange={setStartPosition}
                    style={{ width: '100%' }}
                  >
                    {selectedPattern.pattern_sequence.split('').map((code, index) => (
                      <Option key={index} value={index}>
                        Posición {index}: {code}
                      </Option>
                    ))}
                  </Select>
                </Col>
                <Col span={8}>
                  <div style={{ marginBottom: 8 }}>
                    <strong>Calcular:</strong>
                  </div>
                  <Button
                    icon={<CalculatorOutlined />}
                    onClick={calculateOffset}
                    loading={calculatingOffset}
                    style={{ width: '100%' }}
                  >
                    Calcular Offset
                  </Button>
                </Col>
              </Row>
            </>
          )}

          <Form.Item
            name="offset_days"
            label="Offset (días)"
            rules={[
              { required: true, message: 'El offset es obligatorio' },
              { type: 'number', min: 0, message: 'Debe ser mayor o igual a 0' }
            ]}
          >
            <Input
              type="number"
              placeholder="Días de offset"
              min={0}
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={loadingModal}
              >
                {currentAssignment ? 'Actualizar' : 'Asignar'} Turno
              </Button>
              
              {currentAssignment && (
                <Button
                  danger
                  onClick={() => handleDeleteAssignment(selectedUser.id, selectedUser.username)}
                  loading={loadingModal}
                >
                  Eliminar Asignación
                </Button>
              )}
              
              <Button
                onClick={() => {
                  setIsAssignModalVisible(false);
                  setSelectedUser(null);
                  setCurrentAssignment(null);
                  assignmentForm.resetFields();
                }}
              >
                Cancelar
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Usuarios;