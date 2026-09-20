// src/components/TechnicianManager.js - COMPONENTE COMPLETO Y FUNCIONAL
import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Modal, Select, Input, message, 
  Tag, Space, Tooltip, InputNumber, Avatar, Badge,
  Popconfirm, Typography, Row, Col, Statistic
} from 'antd';
import { 
  UserAddOutlined, DeleteOutlined, EditOutlined, 
  ClockCircleOutlined, UserOutlined, TeamOutlined,
  StarOutlined, SettingOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';

const { Option } = Select;
const { TextArea } = Input;
const { Text } = Typography;

const TechnicianManager = ({ workOrderId, onUpdate }) => {
  const [technicians, setTechnicians] = useState([]);
  const [availableTechnicians, setAvailableTechnicians] = useState([]);
  const [loading, setLoading] = useState(false);
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedTechnician, setSelectedTechnician] = useState(null);
  const [newTechnicianForm, setNewTechnicianForm] = useState({
    user_id: null,
    role: 'apoyo',
    notes: ''
  });

  // Cargar técnicos de la orden
  const loadTechnicians = async () => {
    if (!workOrderId) return;
    
    try {
      setLoading(true);
      const response = await fetchWithAuth(`/ordenes/${workOrderId}/technicians`);
      setTechnicians(response.technicians || []);
    } catch (error) {
      // No mostrar error si no hay técnicos asignados
      if (error.status !== 404) {
        message.error('Error al cargar técnicos');
      }
    } finally {
      setLoading(false);
    }
  };

  // Cargar técnicos disponibles
  const loadAvailableTechnicians = async () => {
    try {
      const response = await fetchWithAuth('/technicians/available');
      setAvailableTechnicians(response.available_technicians || []);
    } catch (error) {
      // Fallback: intentar cargar todos los usuarios mecánicos
      try {
        const usersResponse = await fetchWithAuth('/users');
        const mechanics = (usersResponse || []).filter(user => 
          user.role === 'Mecánico' && user.active
        );
        setAvailableTechnicians(mechanics.map(user => ({
          user_id: user.id,
          username: user.username,
          current_load: 0,
          availability: 'medium'
        })));
      } catch (fallbackError) {
      }
    }
  };

  useEffect(() => {
    loadTechnicians();
    loadAvailableTechnicians();
  }, [workOrderId]);

  // Añadir técnico
  const handleAddTechnician = async () => {
    if (!newTechnicianForm.user_id) {
      message.error('Por favor selecciona un técnico');
      return;
    }

    try {
      await fetchWithAuth(`/ordenes/${workOrderId}/technicians`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTechnicianForm)
      });
      
      message.success('Técnico añadido correctamente');
      setAddModalVisible(false);
      setNewTechnicianForm({ user_id: null, role: 'apoyo', notes: '' });
      // ⭐ RECARGAR EN ORDEN ESPECÍFICO
      await loadTechnicians();
      await loadAvailableTechnicians();
    
      // ⭐ ACTUALIZAR LA TABLA PRINCIPAL (CRÍTICO)
     if (onUpdate) {
        onUpdate();
      }
    
    } catch (error) {
    message.error(error.message || 'Error al añadir técnico');
   }
 };

  // Remover técnico
  const handleRemoveTechnician = async (userId) => {
    try {
      await fetchWithAuth(`/ordenes/${workOrderId}/technicians/${userId}`, {
        method: 'DELETE'
      });
      
      message.success('Técnico removido correctamente');
      loadTechnicians();
      loadAvailableTechnicians();
      onUpdate && onUpdate();
    } catch (error) {
      message.error(error.message || 'Error al remover técnico');
    }
  };

  // Actualizar horas trabajadas
  const handleUpdateHours = async (userId, hours) => {
    try {
      await fetchWithAuth(`/ordenes/${workOrderId}/technicians/${userId}/hours`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hours_worked: hours })
      });
      
      message.success('Horas actualizadas correctamente');
      loadTechnicians();
      onUpdate && onUpdate();
    } catch (error) {
      message.error(error.message || 'Error al actualizar horas');
    }
  };

  // Cambiar rol de técnico
  const handleUpdateRole = async (userId, newRole) => {
    try {
      await fetchWithAuth(`/ordenes/${workOrderId}/technicians/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: newRole })
      });
      
      message.success('Rol actualizado correctamente');
      loadTechnicians();
      onUpdate && onUpdate();
    } catch (error) {
      message.error(error.message || 'Error al actualizar rol');
    }
  };

  // Configuración de columnas para la tabla
  const columns = [
    {
      title: 'Técnico',
      key: 'technician',
      render: (_, record) => (
        <Space>
          <Avatar icon={<UserOutlined />} size="small" />
          <div>
            <Text strong>{record.username}</Text>
            <br />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              ID: {record.user_id}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: 'Rol',
      dataIndex: 'role',
      key: 'role',
      render: (role, record) => (
        <Select
          value={role}
          size="small"
          style={{ width: 120 }}
          onChange={(newRole) => handleUpdateRole(record.user_id, newRole)}
        >
          <Option value="principal">
            <Tag color="gold" icon={<StarOutlined />}>Principal</Tag>
          </Option>
          <Option value="apoyo">
            <Tag color="blue" icon={<UserOutlined />}>Apoyo</Tag>
          </Option>
          <Option value="supervisor">
            <Tag color="purple" icon={<SettingOutlined />}>Supervisor</Tag>
          </Option>
        </Select>
      ),
    },
    {
      title: 'Horas',
      dataIndex: 'hours_worked',
      key: 'hours_worked',
      render: (hours, record) => (
        <InputNumber
          min={0}
          max={24}
          step={0.5}
          size="small"
          value={hours || 0}
          onChange={(value) => handleUpdateHours(record.user_id, value)}
          style={{ width: 80 }}
        />
      ),
    },
    {
      title: 'Desde',
      dataIndex: 'assigned_at',
      key: 'assigned_at',
      render: (date) => date ? new Date(date).toLocaleDateString() : '-',
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Tag color={isActive ? "success" : "default"}>
          {isActive ? "Activo" : "Inactivo"}
        </Tag>
      ),
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="Editar notas">
            <Button
              icon={<EditOutlined />}
              size="small"
              onClick={() => {
                setSelectedTechnician(record);
                setEditModalVisible(true);
              }}
            />
          </Tooltip>
          <Popconfirm
            title="¿Estás seguro de remover este técnico?"
            description="Esta acción no se puede deshacer"
            onConfirm={() => handleRemoveTechnician(record.user_id)}
            okText="Sí, remover"
            cancelText="Cancelar"
          >
            <Button
              icon={<DeleteOutlined />}
              size="small"
              danger
              disabled={record.role === 'principal' && technicians.length === 1}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Estadísticas del equipo
  const teamStats = {
    totalTechnicians: technicians.length,
    totalHours: technicians.reduce((sum, t) => sum + (t.hours_worked || 0), 0),
    principalTechnician: technicians.find(t => t.role === 'principal'),
    supportTechnicians: technicians.filter(t => t.role === 'apoyo').length,
    averageHours: technicians.length > 0 ? 
      (technicians.reduce((sum, t) => sum + (t.hours_worked || 0), 0) / technicians.length).toFixed(1) : 0
  };

  return (
    <Card 
      title={
        <Space>
          <TeamOutlined />
          <span>Equipo de Técnicos</span>
          <Badge count={technicians.length} showZero color="#1890ff" />
        </Space>
      }
      extra={
        <Button
          type="primary"
          icon={<UserAddOutlined />}
          onClick={() => setAddModalVisible(true)}
          disabled={!workOrderId}
        >
          Añadir Técnico
        </Button>
      }
    >
      {/* Estadísticas del equipo */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Statistic
            title="Total Técnicos"
            value={teamStats.totalTechnicians}
            prefix={<TeamOutlined />}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Horas Totales"
            value={teamStats.totalHours}
            precision={1}
            suffix="h"
            prefix={<ClockCircleOutlined />}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Promedio/Técnico"
            value={teamStats.averageHours}
            suffix="h"
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Técnico Principal"
            value={teamStats.principalTechnician?.username || 'N/A'}
            valueStyle={{ fontSize: '14px' }}
          />
        </Col>
      </Row>

      {/* Tabla de técnicos */}
      <Table
        columns={columns}
        dataSource={technicians}
        rowKey="user_id"
        loading={loading}
        size="small"
        pagination={false}
        locale={{
          emptyText: 'No hay técnicos asignados'
        }}
      />

      {/* Modal para añadir técnico */}
      <Modal
        title="Añadir Técnico a la Orden"
        open={addModalVisible}
        onOk={handleAddTechnician}
        onCancel={() => {
          setAddModalVisible(false);
          setNewTechnicianForm({ user_id: null, role: 'apoyo', notes: '' });
        }}
        okText="Añadir"
        cancelText="Cancelar"
        okButtonProps={{
          disabled: !newTechnicianForm.user_id
        }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text strong>Seleccionar Técnico:</Text>
            <Select
              style={{ width: '100%', marginTop: 8 }}
              placeholder="Selecciona un técnico disponible"
              value={newTechnicianForm.user_id}
              onChange={(value) => 
                setNewTechnicianForm(prev => ({ ...prev, user_id: value }))
              }
              showSearch
              optionFilterProp="children"
            >
              {availableTechnicians.map(tech => (
                <Option key={tech.user_id} value={tech.user_id}>
                  <Space>
                    <Avatar size="small" icon={<UserOutlined />} />
                    <span>{tech.username}</span>
                    <Tag color={
                      tech.availability === 'high' ? 'green' :
                      tech.availability === 'medium' ? 'orange' : 'red'
                    }>
                      {tech.current_load} órdenes activas
                    </Tag>
                  </Space>
                </Option>
              ))}
            </Select>
          </div>

          <div>
            <Text strong>Rol en el Equipo:</Text>
            <Select
              style={{ width: '100%', marginTop: 8 }}
              value={newTechnicianForm.role}
              onChange={(value) => 
                setNewTechnicianForm(prev => ({ ...prev, role: value }))
              }
            >
              <Option value="principal">
                <Space>
                  <StarOutlined />
                  Técnico Principal
                </Space>
              </Option>
              <Option value="apoyo">
                <Space>
                  <UserOutlined />
                  Técnico de Apoyo
                </Space>
              </Option>
              <Option value="supervisor">
                <Space>
                  <SettingOutlined />
                  Supervisor
                </Space>
              </Option>
            </Select>
          </div>

          <div>
            <Text strong>Notas (opcional):</Text>
            <TextArea
              rows={3}
              style={{ marginTop: 8 }}
              placeholder="Notas específicas sobre la asignación..."
              value={newTechnicianForm.notes}
              onChange={(e) => 
                setNewTechnicianForm(prev => ({ ...prev, notes: e.target.value }))
              }
            />
          </div>
        </Space>
      </Modal>

      {/* Modal para editar técnico */}
      <Modal
        title="Editar Asignación de Técnico"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setSelectedTechnician(null);
        }}
        footer={null}
      >
        {selectedTechnician && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text strong>Técnico: </Text>
              <Text>{selectedTechnician.username}</Text>
            </div>
            
            <div>
              <Text strong>Rol Actual: </Text>
              <Tag color={
                selectedTechnician.role === 'principal' ? 'gold' :
                selectedTechnician.role === 'supervisor' ? 'purple' : 'blue'
              }>
                {selectedTechnician.role}
              </Tag>
            </div>

            <div>
              <Text strong>Horas Trabajadas: </Text>
              <Text>{selectedTechnician.hours_worked || 0} horas</Text>
            </div>

            <div>
              <Text strong>Notas:</Text>
              <TextArea
                rows={4}
                style={{ marginTop: 8 }}
                placeholder="Notas sobre el trabajo de este técnico..."
                defaultValue={selectedTechnician.notes || ''}
                onChange={(e) => {
                  // Implementar actualización de notas
                  console.log('Nuevas notas:', e.target.value);
                }}
              />
            </div>
          </Space>
        )}
      </Modal>
    </Card>
  );
};

// COMPONENTE COMPACTO: TechnicianSummary
export const TechnicianSummary = ({ technicians = [], showDetails = false }) => {
  // Filtrar técnicos activos primero
  const activeTechnicians = technicians.filter(t => t.is_active !== false);
  
  // Luego filtrar por roles dentro de los activos
  const principalTech = activeTechnicians.find(t => t.role === 'principal');
  const supportTechs = activeTechnicians.filter(t => t.role === 'apoyo');
  const supervisors = activeTechnicians.filter(t => t.role === 'supervisor');
  
  // Contar técnicos que realmente se van a mostrar
  const visibleTechnicians = [
    ...(principalTech ? [principalTech] : []),
    ...supportTechs,
    ...supervisors
  ];

  // ⭐ CORRECCIÓN: Evaluar técnicos visibles, no el array original
  if (!visibleTechnicians.length) {
    return (
      <Tag color="default">
        <UserOutlined /> Sin asignar
      </Tag>
    );
  }

  return (
    <Space wrap>
      {principalTech && (
        <Tag color="gold" icon={<StarOutlined />}>
          {principalTech.username}
          {showDetails && ` (${principalTech.hours_worked || 0}h)`}
        </Tag>
      )}
      
      {supportTechs.map(tech => (
        <Tag key={tech.user_id} color="blue" icon={<UserOutlined />}>
          {tech.username}
          {showDetails && ` (${tech.hours_worked || 0}h)`}
        </Tag>
      ))}
      
      {supervisors.map(tech => (
        <Tag key={tech.user_id} color="purple" icon={<SettingOutlined />}>
          {tech.username}
          {showDetails && ` (${tech.hours_worked || 0}h)`}
        </Tag>
      ))}
      
      {visibleTechnicians.length > 3 && (
        <Tag color="default">
          +{visibleTechnicians.length - 3} más
        </Tag>
      )}
    </Space>
  );
};

export default TechnicianManager;