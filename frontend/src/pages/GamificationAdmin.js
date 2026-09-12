// frontend/src/pages/GamificationAdmin.js
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
  Space,
  message,
  Statistic,
  Row,
  Col,
  Tag,
  Chart
} from 'antd';
import {
  TrophyOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  GiftOutlined,
  UserOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';

const { Option } = Select;

const GamificationAdmin = () => {
  const [loading, setLoading] = useState(false);
  const [adminStats, setAdminStats] = useState(null);
  const [achievements, setAchievements] = useState([]);
  const [users, setUsers] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [statsRes, achievementsRes, usersRes] = await Promise.all([
        fetchWithAuth('/gamification/admin/stats'),
        fetchWithAuth('/gamification/achievements'),
        fetchWithAuth('/users')
      ]);

      setAdminStats(statsRes);
      setAchievements(achievementsRes);
      setUsers(usersRes);
    } catch (error) {
      message.error('Error cargando datos administrativos');
    } finally {
      setLoading(false);
    }
  };

  const awardManualPoints = async (values) => {
    try {
      await fetchWithAuth('/gamification/admin/award-points', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: values.user_id,
          points: values.points,
          reason: values.reason
        })
      });

      message.success('Puntos otorgados correctamente');
      setModalVisible(false);
      form.resetFields();
      loadAdminData();
    } catch (error) {
      message.error('Error otorgando puntos');
    }
  };

  // Columnas para tabla de usuarios
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
      title: 'Puntos Totales',
      dataIndex: 'total_points',
      key: 'total_points',
      render: (points) => (
        <Tag color="green">{points?.toLocaleString() || 0}</Tag>
      ),
      sorter: (a, b) => (a.total_points || 0) - (b.total_points || 0)
    },
    {
      title: 'Nivel',
      dataIndex: 'level',
      key: 'level',
      render: (level) => (
        <Tag color="gold">{level || 1}</Tag>
      )
    },
    {
      title: 'Logros',
      dataIndex: 'achievements_count',
      key: 'achievements_count',
      render: (count) => (
        <Tag color="purple">{count || 0}</Tag>
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
              setSelectedUser(record);
              setModalVisible(true);
            }}
          >
            Otorgar Puntos
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <h2>
        <TrophyOutlined /> Administración de Gamificación
      </h2>

      {/* Estadísticas Generales */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Usuarios Activos"
              value={adminStats?.overview?.total_users || 0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Puntos Totales Otorgados"
              value={adminStats?.overview?.total_points_awarded || 0}
              prefix={<GiftOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Logros Desbloqueados"
              value={adminStats?.overview?.total_achievements_earned || 0}
              prefix={<TrophyOutlined />}
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
      </Row>

      {/* Tabla de Usuarios */}
      <Card
        title="Gestión de Usuarios"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setSelectedUser(null);
              setModalVisible(true);
            }}
          >
            Otorgar Puntos
          </Button>
        }
      >
        <Table
          columns={userColumns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Modal para otorgar puntos */}
      <Modal
        title={selectedUser ? `Otorgar Puntos a ${selectedUser.username}` : 'Otorgar Puntos'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form
          form={form}
          onFinish={awardManualPoints}
          layout="vertical"
          initialValues={selectedUser ? { user_id: selectedUser.id } : {}}
        >
          <Form.Item
            name="user_id"
            label="Usuario"
            rules={[{ required: true, message: 'Selecciona un usuario' }]}
          >
            <Select
              placeholder="Seleccionar usuario"
              disabled={!!selectedUser}
              showSearch
              filterOption={(input, option) =>
                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
              }
            >
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
              placeholder="Cantidad de puntos (puede ser negativo)"
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

export default GamificationAdmin;