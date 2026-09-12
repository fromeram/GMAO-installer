// frontend/src/pages/GamificationSetup.js
import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Switch,
  Statistic,
  Table,
  Space,
  message,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  Divider,
  Alert,
  Progress
} from 'antd';
import {
  TrophyOutlined,
  SettingOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  DatabaseOutlined,
  UserOutlined,
  GiftOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';

const { Option } = Select;

const GamificationSetup = () => {
  const [loading, setLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [users, setUsers] = useState([]);
  const [achievements, setAchievements] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [setupProgress, setSetupProgress] = useState(0);
  const [form] = Form.useForm();

  useEffect(() => {
    loadSystemStatus();
    loadUsers();
    loadAchievements();
  }, []);

  const loadSystemStatus = async () => {
    try {
      const response = await fetchWithAuth('/gamification/admin/system-status');
      setSystemStatus(response);
    } catch (error) {
      console.error('Error loading system status:', error);
      // Si falla, asumir que no está inicializado
      setSystemStatus({
        initialized: false,
        enabled: false,
        total_users: 0,
        users_with_profile: 0,
        total_achievements: 0
      });
    }
  };

  const loadUsers = async () => {
    try {
      const response = await fetchWithAuth('/users');
      setUsers(response);
    } catch (error) {
      message.error('Error cargando usuarios');
    }
  };

  const loadAchievements = async () => {
    try {
      const response = await fetchWithAuth('/gamification/achievements');
      setAchievements(response);
    } catch (error) {
      console.error('Error loading achievements');
    }
  };

  const initializeSystem = async () => {
    setLoading(true);
    setSetupProgress(0);
    try {
      // Paso 1: Inicializar logros
      setSetupProgress(25);
      await fetchWithAuth('/gamification/admin/initialize-achievements', {
        method: 'POST'
      });

      // Paso 2: Crear perfiles de usuario
      setSetupProgress(50);
      await fetchWithAuth('/gamification/admin/initialize-user-profiles', {
        method: 'POST'
      });

      // Paso 3: Activar sistema
      setSetupProgress(75);
      await fetchWithAuth('/gamification/admin/enable-system', {
        method: 'POST'
      });

      setSetupProgress(100);
      message.success('¡Sistema de gamificación inicializado correctamente!');
      
      setTimeout(() => {
        loadSystemStatus();
        loadAchievements();
        setSetupProgress(0);
      }, 1000);

    } catch (error) {
      message.error('Error inicializando el sistema');
      console.error(error);
      setSetupProgress(0);
    } finally {
      setLoading(false);
    }
  };

  const toggleSystemStatus = async (enabled) => {
    try {
      await fetchWithAuth('/gamification/admin/toggle-system', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })
      });

      message.success(`Sistema ${enabled ? 'activado' : 'desactivado'} correctamente`);
      loadSystemStatus();
    } catch (error) {
      message.error('Error cambiando estado del sistema');
    }
  };

  const resetUserPoints = async (userId) => {
    try {
      await fetchWithAuth('/gamification/admin/reset-user-points', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });

      message.success('Puntos reiniciados correctamente');
    } catch (error) {
      message.error('Error reiniciando puntos');
    }
  };

  const awardManualPoints = async (values) => {
    try {
      await fetchWithAuth('/gamification/admin/award-points', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      });

      message.success('Puntos otorgados correctamente');
      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error('Error otorgando puntos');
    }
  };

  const userColumns = [
    {
      title: 'Usuario',
      dataIndex: 'username',
      key: 'username',
      render: (username) => (
        <Space>
          <UserOutlined />
          {username}
        </Space>
      )
    },
    {
      title: 'Perfil Gamificación',
      key: 'has_profile',
      render: (_, record) => (
        systemStatus?.users_with_profile > 0 ? '✅ Activo' : '❌ Sin perfil'
      )
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={<GiftOutlined />}
            onClick={() => {
              form.setFieldsValue({ user_id: record.id });
              setModalVisible(true);
            }}
          >
            Otorgar Puntos
          </Button>
          <Button
            size="small"
            danger
            onClick={() => resetUserPoints(record.id)}
          >
            Reset Puntos
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2>
                <SettingOutlined /> Administración de Gamificación
              </h2>
              
              {systemStatus?.initialized && (
                <Space>
                  <span>Sistema:</span>
                  <Switch
                    checked={systemStatus?.enabled}
                    onChange={toggleSystemStatus}
                    checkedChildren="Activo"
                    unCheckedChildren="Inactivo"
                    loading={loading}
                  />
                </Space>
              )}
            </div>

            {setupProgress > 0 && (
              <div style={{ marginBottom: 16 }}>
                <Progress 
                  percent={setupProgress} 
                  status="active"
                  format={() => `Inicializando... ${setupProgress}%`}
                />
              </div>
            )}

            {!systemStatus?.initialized ? (
              <Alert
                message="Sistema de Gamificación No Inicializado"
                description="El sistema de gamificación no ha sido configurado. Haz clic en 'Inicializar Sistema' para comenzar."
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
                action={
                  <Button 
                    type="primary" 
                    icon={<PlayCircleOutlined />}
                    onClick={initializeSystem}
                    loading={loading}
                  >
                    Inicializar Sistema
                  </Button>
                }
              />
            ) : (
              <Alert
                message={`Sistema ${systemStatus?.enabled ? 'Activo' : 'Inactivo'}`}
                description={`El sistema de gamificación está ${systemStatus?.enabled ? 'funcionando correctamente' : 'desactivado temporalmente'}.`}
                type={systemStatus?.enabled ? "success" : "info"}
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}
          </Card>
        </Col>

        {/* Estadísticas del Sistema */}
        <Col span={24}>
          <Row gutter={[16, 16]}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Usuarios Totales"
                  value={systemStatus?.total_users || 0}
                  prefix={<UserOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Usuarios con Perfil"
                  value={systemStatus?.users_with_profile || 0}
                  prefix={<DatabaseOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Logros Disponibles"
                  value={achievements.length}
                  prefix={<TrophyOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Puntos Otorgados"
                  value={systemStatus?.total_points_awarded || 0}
                  prefix={<GiftOutlined />}
                />
              </Card>
            </Col>
          </Row>
        </Col>

        {/* Gestión de Usuarios */}
        <Col span={24}>
          <Card
            title="Gestión de Usuarios"
            extra={
              <Button
                type="primary"
                icon={<GiftOutlined />}
                onClick={() => setModalVisible(true)}
              >
                Otorgar Puntos
              </Button>
            }
          >
            <Table
              columns={userColumns}
              dataSource={users}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </Col>

        {/* Gestión de Logros */}
        <Col span={24}>
          <Card title="Logros del Sistema">
            <Row gutter={[16, 16]}>
              {achievements.slice(0, 12).map((achievement) => (
                <Col key={achievement.id} xs={24} sm={12} md={8} lg={6}>
                  <Card size="small" style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 24, marginBottom: 8 }}>
                      {achievement.icon}
                    </div>
                    <div style={{ fontWeight: 'bold', fontSize: 12 }}>
                      {achievement.name}
                    </div>
                    <div style={{ fontSize: 10, color: '#666' }}>
                      {achievement.points} pts
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
            {achievements.length > 12 && (
              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <Button type="link">Ver todos los logros ({achievements.length})</Button>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* Modal para otorgar puntos */}
      <Modal
        title="Otorgar Puntos Manualmente"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form
          form={form}
          onFinish={awardManualPoints}
          layout="vertical"
        >
          <Form.Item
            name="user_id"
            label="Usuario"
            rules={[{ required: true, message: 'Selecciona un usuario' }]}
          >
            <Select placeholder="Seleccionar usuario">
              {users.map(user => (
                <Option key={user.id} value={user.id}>
                  {user.username}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="points"
            label="Puntos"
            rules={[{ required: true, message: 'Ingresa la cantidad de puntos' }]}
          >
            <InputNumber
              min={-1000}
              max={10000}
              placeholder="Cantidad de puntos"
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item
            name="reason"
            label="Motivo"
            rules={[{ required: true, message: 'Ingresa el motivo' }]}
          >
            <Input.TextArea
              placeholder="Describe el motivo para otorgar estos puntos"
              rows={3}
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Otorgar Puntos
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                Cancelar
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default GamificationSetup;