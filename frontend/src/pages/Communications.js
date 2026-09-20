// src/pages/Communications.js - VERSIÓN FINAL Y COMPLETA
import React, { useState, useEffect } from 'react';
import { 
  Card, Button, Modal, Form, Input, Select, Table, Tag, Space, 
  message, Tabs, Alert, Tooltip, Typography, Badge, Empty, Popconfirm, 
  Radio, Divider, List
} from 'antd';
import { 
  PlusOutlined, MessageOutlined, BulbOutlined, ToolOutlined, QuestionCircleOutlined,
  ExclamationCircleOutlined, CheckCircleOutlined, ClockCircleOutlined, EyeOutlined,
  DeleteOutlined, SendOutlined, UsergroupAddOutlined, UserOutlined, TeamOutlined,
  ArrowUpOutlined, ArrowDownOutlined, SoundOutlined,  UndoOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { fetchWithAuth } from '../apiConfig';

const { Option } = Select;
const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

// Mapeo de tipos con iconos y colores
const TYPE_CONFIG = {
  'Sugerencia': { icon: <BulbOutlined />, color: 'blue' },
  'Pedido de Material': { icon: <ToolOutlined />, color: 'orange' },
  'Queja/Problema': { icon: <ExclamationCircleOutlined />, color: 'red' },
  'Consulta': { icon: <QuestionCircleOutlined />, color: 'purple' },
  'Otro': { icon: <MessageOutlined />, color: 'default' },
  // NUEVOS TIPOS PARA ADMIN
  'Mensaje Administrativo': { icon: <SendOutlined />, color: 'green' },
  'Asignación de Tarea': { icon: <UserOutlined />, color: 'cyan' },
  'Comunicado': { icon: <SoundOutlined />, color: 'magenta' }
};

// Mapeo de estados
const STATUS_CONFIG = {
  'Pendiente': { color: 'gold', icon: <ClockCircleOutlined /> },
  'Revisado': { color: 'blue', icon: <EyeOutlined /> },
  'En Proceso': { color: 'orange', icon: <ClockCircleOutlined /> },
  'Resuelto': { color: 'green', icon: <CheckCircleOutlined /> },
  'Rechazado': { color: 'red', icon: <ExclamationCircleOutlined /> },
  'Leído': { color: 'green', icon: <CheckCircleOutlined /> }
};

// Mapeo de direcciones
const DIRECTION_CONFIG = {
  'Operario a Admin': { icon: <ArrowUpOutlined />, color: 'blue', label: 'Enviado' },
  'Admin a Operario': { icon: <ArrowDownOutlined />, color: 'green', label: 'Recibido' },
  'Difusión': { icon: <SoundOutlined />, color: 'purple', label: 'Difusión' }
};

const Communications = () => {
  const { currentUser } = useAuth();
  const [form] = Form.useForm();
  const [adminForm] = Form.useForm();
  
  // Estados principales
  const [communications, setCommunications] = useState([]);
  const [machines, setMachines] = useState([]);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [availableRoles, setAvailableRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Modales
  const [modalVisible, setModalVisible] = useState(false);
  const [adminModalVisible, setAdminModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedCommunication, setSelectedCommunication] = useState(null);
  
  // Estados para filtros
  const [filterStatus, setFilterStatus] = useState(null);
  const [filterType, setFilterType] = useState(null);
  const [filterDirection, setFilterDirection] = useState(null);
  
  // Estado para el formulario de admin
  const [targetType, setTargetType] = useState('user'); // 'user', 'role', 'department'
  const [replyingTo, setReplyingTo] = useState(null);

  const isAdmin = currentUser?.role === 'Administrador' || currentUser?.role === 'Jefe de Mantenimiento';

  // Cargar datos iniciales
  useEffect(() => {
    loadCommunications();
    loadMachines();
    if (isAdmin) {
      loadAvailableUsers();
      loadAvailableRoles();
    }
  }, []);

  const loadCommunications = async () => {
    setLoading(true);
    try {
      const endpoint = isAdmin ? '/communications/admin/all' : '/communications/my-messages';
      const params = new URLSearchParams();
      
      if (filterStatus) params.append('status_filter', filterStatus);
      if (filterType) params.append('type_filter', filterType);
      if (filterDirection) params.append('direction_filter', filterDirection);
      
      const response = await fetchWithAuth(`${endpoint}?${params.toString()}`);
      setCommunications(response || []);
    } catch (error) {
      console.error('Error cargando comunicaciones:', error);
      message.error('Error al cargar las comunicaciones');
    } finally {
      setLoading(false);
    }
  };

  const loadMachines = async () => {
    try {
      const response = await fetchWithAuth('/maquinas');
      setMachines(response || []);
    } catch (error) {
      console.error('Error cargando máquinas:', error);
    }
  };

  const loadAvailableUsers = async () => {
    try {
      const response = await fetchWithAuth('/communications/admin/available-users');
      setAvailableUsers(response || []);
    } catch (error) {
      console.error('Error cargando usuarios:', error);
    }
  };

  const loadAvailableRoles = async () => {
    try {
      const response = await fetchWithAuth('/communications/admin/available-roles');
      setAvailableRoles(response || []);
    } catch (error) {
      console.error('Error cargando roles:', error);
    }
  };

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const payload = { ...values };
      if (replyingTo) {
        payload.parent_communication_id = replyingTo.id;
        payload.type = replyingTo.type;
        payload.subject = `Re: ${replyingTo.subject}`;
      }
      
      // 🔍 DEBUG: Ver qué se está enviando
      console.log('🔍 DEBUG Frontend - Payload a enviar:', payload);
      console.log('🔍 DEBUG Frontend - Valores del form:', values);
      
      await fetchWithAuth('/communications/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      message.success(replyingTo ? 'Respuesta enviada correctamente' : 'Tu mensaje ha sido enviado correctamente');
      setModalVisible(false);
      form.resetFields();
      setReplyingTo(null);
      loadCommunications();
      if (detailModalVisible) {
        setDetailModalVisible(false);
      }
    } catch (error) {
      console.error('Error enviando comunicación:', error);
      message.error('Error al enviar el mensaje');
    } finally {
      setLoading(false);
    }
  };

  const handleAdminSubmit = async (values) => {
    setLoading(true);
    try {
      const payload = {
        type: values.type,
        subject: values.subject,
        message: values.message,
        priority: values.priority,
        machine_id: values.machine_id,
        requires_response: values.requires_response || false
      };

      if (targetType === 'user') {
        payload.target_user_id = values.target_user_id;
      } else if (targetType === 'role') {
        payload.target_role_id = values.target_role_id;
      } else if (targetType === 'department') {
        payload.target_department = values.target_department;
      }

      await fetchWithAuth('/communications/admin/send-message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      message.success('Mensaje enviado correctamente');
      setAdminModalVisible(false);
      adminForm.resetFields();
      setTargetType('user');
      loadCommunications();
    } catch (error) {
      console.error('Error enviando mensaje administrativo:', error);
      message.error('Error al enviar el mensaje');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateCommunication = async (id, updateData) => {
    setLoading(true);
    try {
      await fetchWithAuth(`/communications/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData)
      });
      
      message.success('Comunicación actualizada correctamente');
      loadCommunications();
      setDetailModalVisible(false);
    } catch (error) {
      console.error('Error actualizando comunicación:', error);
      message.error('Error al actualizar la comunicación');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCommunication = async (id) => {
    setLoading(true);
    try {
      await fetchWithAuth(`/communications/${id}`, {
        method: 'DELETE'
      });
      
      message.success('Comunicación eliminada correctamente');
      loadCommunications();
    } catch (error) {
      console.error('Error eliminando comunicación:', error);
      message.error('Error al eliminar la comunicación');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
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
    return `Hace ${days} días`;
  };
  
  const handleStartReply = (communicationToReply) => {
    setReplyingTo(communicationToReply);
    setDetailModalVisible(false);
    setModalVisible(true);
  };

  useEffect(() => {
    loadCommunications();
  }, [filterStatus, filterType, filterDirection]);

  const columns = [
    {
      title: 'Dirección',
      dataIndex: 'direction',
      key: 'direction',
      width: 80,
      render: (direction) => {
        const config = DIRECTION_CONFIG[direction] || { icon: <MessageOutlined />, color: 'default', label: direction };
        return (
          <Tooltip title={direction}>
            <Tag color={config.color} icon={config.icon}>
              {config.label}
            </Tag>
          </Tooltip>
        );
      }
    },
    {
      title: 'Tipo',
      dataIndex: 'type',
      key: 'type',
      width: 150,
      render: (type) => {
        const config = TYPE_CONFIG[type] || TYPE_CONFIG['Otro'];
        return (
          <Tag color={config.color} icon={config.icon}>
            {type}
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
          <Button 
            type="link" 
            onClick={() => {
              setSelectedCommunication(record);
              setDetailModalVisible(true);
            }}
            style={{ padding: 0, textAlign: 'left', height: 'auto' }}
          >
            {text}
          </Button>
          {record.requires_response && (
            <Tag color="orange" size="small" style={{ marginLeft: 8 }}>
              Requiere respuesta
            </Tag>
          )}
        </div>
      )
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => {
        const config = STATUS_CONFIG[status] || STATUS_CONFIG['Pendiente'];
        return (
          <Tag color={config.color} icon={config.icon}>
            {status}
          </Tag>
        );
      }
    },
    {
      title: 'Prioridad',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority) => {
        const colors = {
          'Urgente': 'red',
          'Alta': 'orange',
          'Normal': 'blue',
          'Baja': 'gray'
        };
        return <Tag color={colors[priority]}>{priority}</Tag>;
      }
    },
    ...(isAdmin ? [{
      title: 'Participantes',
      key: 'participants',
      width: 150,
      render: (_, record) => {
        if (record.direction === 'Operario a Admin') {
          return (
            <div>
              <Text style={{ fontSize: '12px' }}>
                De: {record.created_by_name || 'Usuario'}
              </Text>
            </div>
          );
        } else if (record.direction === 'Admin a Operario') {
          return (
            <div>
              <Text style={{ fontSize: '12px' }}>
                Para: {record.assigned_to_name || 'Usuario'}
              </Text>
              <br />
              <Text style={{ fontSize: '11px', color: '#666' }}>
                De: {record.created_by_name}
              </Text>
            </div>
          );
        } else { // Difusión
          return (
            <div>
              <Text style={{ fontSize: '12px' }}>
                Para: {record.target_role_name || record.target_department || 'Múltiples'}
              </Text>
              <br />
              <Text style={{ fontSize: '11px', color: '#666' }}>
                De: {record.created_by_name}
              </Text>
            </div>
          );
        }
      }
    }] : [{
      title: 'De/Para',
      key: 'participants',
      width: 120,
      render: (_, record) => {
        if (record.direction === 'Operario a Admin') {
          return <Text style={{ fontSize: '12px' }}>Para: Administración</Text>;
        } else if (record.direction === 'Admin a Operario') {
          return <Text style={{ fontSize: '12px' }}>De: {record.created_by_name}</Text>;
        } else {
          return <Text style={{ fontSize: '12px' }}>Difusión</Text>;
        }
      }
    }]),
    {
      title: 'Fecha',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date) => (
        <Tooltip title={formatDate(date)}>
          {getDaysAgo(date)}
        </Tooltip>
      )
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            icon={<EyeOutlined />}
            size="small"
            onClick={() => {
              setSelectedCommunication(record);
              setDetailModalVisible(true);
            }}
          />
          {isAdmin && (
            <Popconfirm
              title="¿Eliminar esta comunicación?"
              onConfirm={() => handleDeleteCommunication(record.id)}
              okText="Sí"
              cancelText="No"
            >
              <Button
                type="primary"
                danger
                icon={<DeleteOutlined />}
                size="small"
              />
            </Popconfirm>
          )}
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '20px' 
      }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            {isAdmin ? 'Gestión de Comunicaciones' : 'Mis Comunicaciones'}
          </Title>
          <Text type="secondary">
            {isAdmin 
              ? 'Gestiona todas las comunicaciones y envía mensajes a operarios' 
              : 'Envía sugerencias, pedidos de material y consultas a la administración'
            }
          </Text>
        </div>
        
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalVisible(true)}
          >
            Nueva Comunicación
          </Button>
          {isAdmin && (
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={() => setAdminModalVisible(true)}
              style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
            >
              Enviar Mensaje
            </Button>
          )}
        </Space>
      </div>

      {!isAdmin && (
        <Alert
          message="Sistema de Comunicación Bidireccional"
          description="Este es tu canal directo con la administración. También recibirás mensajes importantes de los administradores aquí."
          type="info"
          showIcon
          style={{ marginBottom: '20px' }}
        />
      )}

      <Card size="small" style={{ marginBottom: '20px' }}>
        <Space wrap>
          <span>Filtros:</span>
          <Select
            placeholder="Dirección"
            allowClear
            style={{ width: 150 }}
            value={filterDirection}
            onChange={setFilterDirection}
          >
            <Option value="Operario a Admin">Enviados</Option>
            <Option value="Admin a Operario">Recibidos</Option>
            <Option value="Difusión">Difusión</Option>
          </Select>
          <Select
            placeholder="Estado"
            allowClear
            style={{ width: 150 }}
            value={filterStatus}
            onChange={setFilterStatus}
          >
            <Option value="Pendiente">Pendiente</Option>
            <Option value="Revisado">Revisado</Option>
            <Option value="En Proceso">En Proceso</Option>
            <Option value="Resuelto">Resuelto</Option>
            <Option value="Rechazado">Rechazado</Option>
            <Option value="Leído">Leído</Option>
          </Select>
          
          <Select
            placeholder="Tipo"
            allowClear
            style={{ width: 180 }}
            value={filterType}
            onChange={setFilterType}
          >
            <Option value="Sugerencia">Sugerencia</Option>
            <Option value="Pedido de Material">Pedido de Material</Option>
            <Option value="Queja/Problema">Queja/Problema</Option>
            <Option value="Consulta">Consulta</Option>
            <Option value="Mensaje Administrativo">Mensaje Administrativo</Option>
            <Option value="Asignación de Tarea">Asignación de Tarea</Option>
            <Option value="Comunicado">Comunicado</Option>
            <Option value="Otro">Otro</Option>
          </Select>
          
          <Button onClick={() => {
            setFilterStatus(null);
            setFilterType(null);
            setFilterDirection(null);
          }}>
            Limpiar Filtros
          </Button>
        </Space>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={communications}
          rowKey="id"
          loading={loading}
          locale={{
            emptyText: (
              <Empty
                description={
                  isAdmin 
                    ? "No hay comunicaciones registradas"
                    : "No tienes comunicaciones aún"
                }
              />
            )
          }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} de ${total} comunicaciones`
          }}
        />
      </Card>
      {isAdmin && (
        <Modal
          title="Enviar Mensaje Administrativo"
          open={adminModalVisible}
          onCancel={() => {
            setAdminModalVisible(false);
            adminForm.resetFields();
            setTargetType('user');
          }}
          footer={null}
          width={800}
        >
          <Form
            form={adminForm}
            layout="vertical"
            onFinish={handleAdminSubmit}
            initialValues={{
              priority: 'Normal',
              requires_response: false
            }}
          >
            <Alert
              message="Envío de Mensaje Administrativo"
              description="Envía mensajes directos a operarios específicos, roles completos o departamentos."
              type="success"
              showIcon
              style={{ marginBottom: '20px' }}
            />

            {/* Selector de tipo de destinatario */}
            <Form.Item label="Destinatario">
              <Radio.Group 
                value={targetType} 
                onChange={(e) => setTargetType(e.target.value)}
                style={{ marginBottom: '16px' }}
              >
                <Radio.Button value="user">
                  <UserOutlined /> Usuario Específico
                </Radio.Button>
                <Radio.Button value="role">
                  <TeamOutlined /> Rol Completo
                </Radio.Button>
                <Radio.Button value="department">
                  <UsergroupAddOutlined /> Departamento
                </Radio.Button>
              </Radio.Group>
            </Form.Item>

            {/* Campos condicionales según el tipo de destinatario */}
            {targetType === 'user' && (
              <Form.Item
                name="target_user_id"
                label="Usuario Destinatario"
                rules={[{ required: true, message: 'Selecciona un usuario' }]}
              >
                <Select
                  placeholder="Seleccionar usuario"
                  showSearch
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                  }
                >
                  {availableUsers.map(user => (
                    <Option key={user.id} value={user.id}>
                      {user.username} - {user.role_name} 
                      {user.department && ` (${user.department})`}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            )}

            {targetType === 'role' && (
              <Form.Item
                name="target_role_id"
                label="Rol Destinatario"
                rules={[{ required: true, message: 'Selecciona un rol' }]}
              >
                <Select placeholder="Seleccionar rol">
                  {availableRoles.map(role => (
                    <Option key={role.id} value={role.id}>
                      {role.nombre} ({role.user_count} usuarios)
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            )}

            {targetType === 'department' && (
              <Form.Item
                name="target_department"
                label="Departamento Destinatario"
                rules={[{ required: true, message: 'Escribe el nombre del departamento' }]}
              >
                <Input placeholder="Ej: Producción, Mantenimiento, etc." />
              </Form.Item>
            )}

            <Divider />

            <Form.Item
              name="type"
              label="Tipo de Mensaje"
              rules={[{ required: true, message: 'Selecciona el tipo de mensaje' }]}
            >
              <Select placeholder="¿Qué tipo de mensaje envías?">
                <Option value="Mensaje Administrativo">
                  <SendOutlined /> Mensaje Administrativo
                </Option>
                <Option value="Asignación de Tarea">
                  <UserOutlined /> Asignación de Tarea
                </Option>
                <Option value="Comunicado">
                  <SoundOutlined /> Comunicado General
                </Option>
                <Option value="Consulta">
                  <QuestionCircleOutlined /> Consulta
                </Option>
                <Option value="Otro">
                  <MessageOutlined /> Otro
                </Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="subject"
              label="Asunto"
              rules={[
                { required: true, message: 'Escribe un asunto' },
                { min: 5, message: 'El asunto debe tener al menos 5 caracteres' },
                { max: 200, message: 'El asunto no puede exceder 200 caracteres' }
              ]}
            >
              <Input placeholder="Ej: Nueva política de seguridad" />
            </Form.Item>

            <Form.Item
              name="message"
              label="Mensaje"
              rules={[
                { required: true, message: 'Escribe tu mensaje' },
                { min: 10, message: 'El mensaje debe tener al menos 10 caracteres' }
              ]}
            >
              <TextArea
                rows={6}
                placeholder="Escribe el mensaje que quieres enviar..."
              />
            </Form.Item>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
              <Form.Item
                name="priority"
                label="Prioridad"
              >
                <Select>
                  <Option value="Baja">Baja</Option>
                  <Option value="Normal">Normal</Option>
                  <Option value="Alta">Alta</Option>
                  <Option value="Urgente">Urgente</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="machine_id"
                label="Máquina Relacionada"
              >
                <Select
                  placeholder="Opcional"
                  allowClear
                  showSearch
                  optionFilterProp="children"
                >
                  {machines.map(machine => (
                    <Option key={machine.id} value={machine.id}>
                      {machine.nombre}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="requires_response"
                valuePropName="checked"
                label=" "
              >
                <label style={{ display: 'flex', alignItems: 'center', paddingTop: '8px' }}>
                  <input type="checkbox" style={{ marginRight: '8px' }} />
                  Requiere respuesta
                </label>
              </Form.Item>
            </div>

            <div style={{ textAlign: 'right', marginTop: '20px' }}>
              <Space>
                <Button onClick={() => {
                  setAdminModalVisible(false);
                  adminForm.resetFields();
                  setTargetType('user');
                }}>
                  Cancelar
                </Button>
                <Button type="primary" htmlType="submit" loading={loading}>
                  Enviar Mensaje
                </Button>
              </Space>
            </div>
          </Form>
        </Modal>
      )}

      <Modal
        title={replyingTo ? `Responder a: "${replyingTo.subject}"` : "Nueva Comunicación"}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setReplyingTo(null);
        }}
        footer={null}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            priority: 'Normal',
            is_anonymous: false
          }}
        >
          {replyingTo ? (
            <Alert
              message={`Estás respondiendo al mensaje sobre "${replyingTo.subject}".`}
              description="Tu respuesta será visible en el hilo de la conversación."
              type="info"
              showIcon
              style={{ marginBottom: '20px' }}
            />
          ) : (
            <Alert
              message="Comunicación Privada"
              description="Tu mensaje será enviado directamente a los administradores y jefes de mantenimiento. Es completamente privado y confidencial."
              type="info"
              showIcon
              style={{ marginBottom: '20px' }}
            />
          )}

          {!replyingTo && (
            <>
              <Form.Item
                name="type"
                label="Tipo de Comunicación"
                rules={[{ required: true, message: 'Selecciona el tipo de comunicación' }]}
              >
                <Select placeholder="¿Qué tipo de mensaje quieres enviar?">
                  <Option value="Sugerencia"><BulbOutlined /> Sugerencia de Mejora</Option>
                  <Option value="Pedido de Material"><ToolOutlined /> Pedido de Material</Option>
                  <Option value="Queja/Problema"><ExclamationCircleOutlined /> Queja o Problema</Option>
                  <Option value="Consulta"><QuestionCircleOutlined /> Consulta General</Option>
                  <Option value="Otro"><MessageOutlined /> Otro</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="subject"
                label="Asunto"
                rules={[{ required: true, message: 'Escribe un asunto' }, { min: 5, message: 'El asunto debe tener al menos 5 caracteres' }, { max: 200, message: 'El asunto no puede exceder 200 caracteres' }]}
              >
                <Input placeholder="Ej: Solicitud de repuestos para máquina X" />
              </Form.Item>
            </>
          )}

          <Form.Item
            name="message"
            label={replyingTo ? "Tu Respuesta" : "Mensaje"}
            rules={[{ required: true, message: 'Escribe tu mensaje' }, { min: 10, message: 'El mensaje debe tener al menos 10 caracteres' }]}
          >
            <TextArea
              rows={5}
              placeholder="Describe detalladamente tu sugerencia, pedido o consulta..."
            />
          </Form.Item>

          {!replyingTo && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <Form.Item
                  name="priority"
                  label="Prioridad"
                >
                  <Select>
                    <Option value="Baja">Baja</Option>
                    <Option value="Normal">Normal</Option>
                    <Option value="Alta">Alta</Option>
                    <Option value="Urgente">Urgente</Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  name="machine_id"
                  label="Máquina Relacionada (Opcional)"
                >
                  <Select
                    placeholder="Seleccionar máquina"
                    allowClear
                    showSearch
                    optionFilterProp="children"
                  >
                    {machines.map(machine => (
                      <Option key={machine.id} value={machine.id}>
                        {machine.nombre}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </div>

              <Form.Item
                name="is_anonymous"
                valuePropName="checked"
              >
                <label>
                  <input type="checkbox" style={{ marginRight: '8px' }} />
                  Enviar de forma anónima
                </label>
              </Form.Item>
            </>
          )}

          <div style={{ textAlign: 'right', marginTop: '20px' }}>
            <Space>
              <Button onClick={() => {
                setModalVisible(false);
                form.resetFields();
                setReplyingTo(null);
              }}>
                Cancelar
              </Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                {replyingTo ? "Enviar Respuesta" : "Enviar Comunicación"}
              </Button>
            </Space>
          </div>
        </Form>
      </Modal>

      {isAdmin && (
        <Modal
          title="Enviar Mensaje Administrativo"
          open={adminModalVisible}
          onCancel={() => {
            setAdminModalVisible(false);
            adminForm.resetFields();
            setTargetType('user');
          }}
          footer={null}
          width={800}
        >
          <Form
            form={adminForm}
            layout="vertical"
            onFinish={handleAdminSubmit}
            initialValues={{
              priority: 'Normal',
              requires_response: false
            }}
          >
            <Alert
              message="Envío de Mensaje Administrativo"
              description="Envía mensajes directos a operarios específicos, roles completos o departamentos."
              type="success"
              showIcon
              style={{ marginBottom: '20px' }}
            />

            <Form.Item label="Destinatario">
              <Radio.Group 
                value={targetType} 
                onChange={(e) => setTargetType(e.target.value)}
                style={{ marginBottom: '16px' }}
              >
                <Radio.Button value="user"><UserOutlined /> Usuario Específico</Radio.Button>
                <Radio.Button value="role"><TeamOutlined /> Rol Completo</Radio.Button>
                <Radio.Button value="department"><UsergroupAddOutlined /> Departamento</Radio.Button>
              </Radio.Group>
            </Form.Item>

            {targetType === 'user' && (
              <Form.Item
                name="target_user_id"
                label="Usuario Destinatario"
                rules={[{ required: true, message: 'Selecciona un usuario' }]}
              >
                <Select
                  placeholder="Seleccionar usuario"
                  showSearch
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                  }
                >
                  {availableUsers.map(user => (
                    <Option key={user.id} value={user.id}>
                      {user.username} - {user.role_name} 
                      {user.department && ` (${user.department})`}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            )}

            {targetType === 'role' && (
              <Form.Item name="target_role_id" label="Rol Destinatario" rules={[{ required: true, message: 'Selecciona un rol' }]}>
                <Select placeholder="Seleccionar rol">
                  {availableRoles.map(role => (
                    <Option key={role.id} value={role.id}>
                      {role.nombre} ({role.user_count} usuarios)
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            )}

            {targetType === 'department' && (
              <Form.Item name="target_department" label="Departamento Destinatario" rules={[{ required: true, message: 'Escribe el nombre del departamento' }]}>
                <Input placeholder="Ej: Producción, Mantenimiento, etc." />
              </Form.Item>
            )}

            <Divider />

            <Form.Item name="type" label="Tipo de Mensaje" rules={[{ required: true, message: 'Selecciona el tipo de mensaje' }]}>
              <Select placeholder="¿Qué tipo de mensaje envías?">
                <Option value="Mensaje Administrativo"><SendOutlined /> Mensaje Administrativo</Option>
                <Option value="Asignación de Tarea"><UserOutlined /> Asignación de Tarea</Option>
                <Option value="Comunicado"><SoundOutlined /> Comunicado General</Option>
                <Option value="Consulta"><QuestionCircleOutlined /> Consulta</Option>
                <Option value="Otro"><MessageOutlined /> Otro</Option>
              </Select>
            </Form.Item>

            <Form.Item name="subject" label="Asunto" rules={[{ required: true, message: 'Escribe un asunto' }, { min: 5 }, { max: 200 }]}>
              <Input placeholder="Ej: Nueva política de seguridad" />
            </Form.Item>

            <Form.Item name="message" label="Mensaje" rules={[{ required: true, message: 'Escribe tu mensaje' }, { min: 10 }]}>
              <TextArea rows={6} placeholder="Escribe el mensaje que quieres enviar..." />
            </Form.Item>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
              <Form.Item name="priority" label="Prioridad">
                <Select>
                  <Option value="Baja">Baja</Option>
                  <Option value="Normal">Normal</Option>
                  <Option value="Alta">Alta</Option>
                  <Option value="Urgente">Urgente</Option>
                </Select>
              </Form.Item>
              <Form.Item name="machine_id" label="Máquina Relacionada">
                <Select placeholder="Opcional" allowClear showSearch optionFilterProp="children">
                  {machines.map(machine => (
                    <Option key={machine.id} value={machine.id}>{machine.nombre}</Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item name="requires_response" valuePropName="checked" label=" ">
                <label style={{ display: 'flex', alignItems: 'center', paddingTop: '8px' }}>
                  <input type="checkbox" style={{ marginRight: '8px' }} />
                  Requiere respuesta
                </label>
              </Form.Item>
            </div>

            <div style={{ textAlign: 'right', marginTop: '20px' }}>
              <Space>
                <Button onClick={() => {
                  setAdminModalVisible(false);
                  adminForm.resetFields();
                  setTargetType('user');
                }}>
                  Cancelar
                </Button>
                <Button type="primary" htmlType="submit" loading={loading}>
                  Enviar Mensaje
                </Button>
              </Space>
            </div>
          </Form>
        </Modal>
      )}

      <Modal
        title={`Comunicación #${selectedCommunication?.id || ''}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        width={800}
        footer={null}
      >
        {selectedCommunication && (
          <CommunicationDetail
            communication={selectedCommunication}
            isAdmin={isAdmin}
            onUpdate={handleUpdateCommunication}
            onReply={handleStartReply}
            loading={loading}
          />
        )}
      </Modal>
    </div>
  );
};

const CommunicationDetail = ({ communication, isAdmin, onUpdate, onReply, loading }) => {
  const [form] = Form.useForm();
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    if (isAdmin && communication) {
      form.setFieldsValue({
        status: communication.status,
        admin_response: communication.admin_response || '',
        admin_notes: communication.admin_notes || '',
        priority: communication.priority
      });
    }
  }, [communication, form, isAdmin]);

  const handleSubmit = async (values) => {
    await onUpdate(communication.id, values);
    setEditing(false);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const directionConfig = DIRECTION_CONFIG[communication.direction] || { 
    icon: <MessageOutlined />, 
    color: 'default', 
    label: communication.direction 
  };

  return (
    <div>
      <Card size="small" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div><Text strong>Dirección:</Text><div><Tag color={directionConfig.color} icon={directionConfig.icon}>{communication.direction}</Tag></div></div>
          <div><Text strong>Tipo:</Text><div>{(() => { const config = TYPE_CONFIG[communication.type] || TYPE_CONFIG['Otro']; return (<Tag color={config.color} icon={config.icon}>{communication.type}</Tag>); })()}</div></div>
          <div><Text strong>Estado:</Text><div>{(() => { const config = STATUS_CONFIG[communication.status] || STATUS_CONFIG['Pendiente']; return (<Tag color={config.color} icon={config.icon}>{communication.status}</Tag>); })()}</div></div>
          <div><Text strong>Prioridad:</Text><div><Tag color={communication.priority === 'Urgente' ? 'red' : communication.priority === 'Alta' ? 'orange' : communication.priority === 'Normal' ? 'blue' : 'gray'}>{communication.priority}</Tag></div></div>
          <div><Text strong>Fecha de Creación:</Text><div>{formatDate(communication.created_at)}</div></div>
          {communication.read_at && (<div><Text strong>Leído:</Text><div>{formatDate(communication.read_at)}</div></div>)}
        </div>

        <Divider />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div><Text strong>Enviado por:</Text><div>{communication.created_by_name || 'Usuario'}</div></div>
          {communication.direction === 'Admin a Operario' && communication.assigned_to_name && (<div><Text strong>Destinatario:</Text><div>{communication.assigned_to_name}</div></div>)}
          {communication.direction === 'Difusión' && (<div><Text strong>Dirigido a:</Text><div>{communication.target_role_name && `Rol: ${communication.target_role_name}`}{communication.target_department && `Departamento: ${communication.target_department}`}</div></div>)}
          {communication.department && (<div><Text strong>Departamento:</Text><div>{communication.department}</div></div>)}
          {communication.machine_name && (<div><Text strong>Máquina:</Text><div>{communication.machine_name}</div></div>)}
        </div>

        {communication.requires_response && (
          <div style={{ marginTop: '12px' }}><Alert message="Requiere Respuesta" description="Este mensaje requiere una respuesta del destinatario." type="warning" showIcon size="small" /></div>
        )}
      </Card>

      <Card title="Mensaje" size="small" style={{ marginBottom: '16px' }}>
        <Title level={5}>{communication.subject}</Title>
        <Paragraph>{communication.message}</Paragraph>
      </Card>
      
      {communication.admin_response && (
        <Card title="Respuesta de la Administración" size="small" style={{ marginBottom: '16px' }}>
          <Paragraph>{communication.admin_response}</Paragraph>
          {communication.reviewed_at && (<Text type="secondary">Respondido el {formatDate(communication.reviewed_at)}</Text>)}
        </Card>
      )}

      {communication.replies && communication.replies.length > 0 && (
        <Card title="Historial de la Conversación" size="small" style={{ marginBottom: '16px' }}>
          <List
            itemLayout="horizontal"
            dataSource={communication.replies}
            renderItem={reply => (
              <List.Item>
                <List.Item.Meta
                  title={<span>{reply.created_by_name || 'Usuario'} <Text type="secondary" style={{fontWeight: 'normal'}}>- {formatDate(reply.created_at)}</Text></span>}
                  description={reply.message}
                />
              </List.Item>
            )}
          />
        </Card>
      )}

      {!isAdmin && ['Admin a Operario', 'Difusión'].includes(communication.direction) && (
        <Button type="primary" icon={<UndoOutlined/>} onClick={() => onReply(communication)} style={{marginTop: 16}}>
          Responder
        </Button>
      )}

      {isAdmin && (
        <Card 
          title="Panel de Administración" 
          size="small"
          extra={<Button type={editing ? "default" : "primary"} onClick={() => setEditing(!editing)}>{editing ? 'Cancelar' : 'Editar'}</Button>}
        >
          {editing ? (
            <Form form={form} layout="vertical" onFinish={handleSubmit}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <Form.Item name="status" label="Estado"><Select><Option value="Pendiente">Pendiente</Option><Option value="Revisado">Revisado</Option><Option value="En Proceso">En Proceso</Option><Option value="Resuelto">Resuelto</Option><Option value="Rechazado">Rechazado</Option><Option value="Leído">Leído</Option></Select></Form.Item>
                <Form.Item name="priority" label="Prioridad"><Select><Option value="Baja">Baja</Option><Option value="Normal">Normal</Option><Option value="Alta">Alta</Option><Option value="Urgente">Urgente</Option></Select></Form.Item>
              </div>
              <Form.Item name="admin_response" label="Respuesta al Usuario"><TextArea rows={3} placeholder="Escribe aquí la respuesta que verá el usuario..."/></Form.Item>
              <Form.Item name="admin_notes" label="Notas Privadas (Solo Admin)"><TextArea rows={2} placeholder="Notas internas que solo verán otros administradores..."/></Form.Item>
              <div style={{ textAlign: 'right' }}><Space><Button onClick={() => setEditing(false)}>Cancelar</Button><Button type="primary" htmlType="submit" loading={loading}>Guardar Cambios</Button></Space></div>
            </Form>
          ) : (
            <div>
              {communication.admin_notes && (<div style={{ marginBottom: '12px' }}><Text strong>Notas Privadas:</Text><Paragraph>{communication.admin_notes}</Paragraph></div>)}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '12px', color: '#666' }}>
                {communication.reviewed_at && (<div>Revisado: {formatDate(communication.reviewed_at)}</div>)}
                {communication.resolved_at && (<div>Resuelto: {formatDate(communication.resolved_at)}</div>)}
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default Communications;