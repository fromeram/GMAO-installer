// frontend/src/components/EnhancedLeaderboard.js
// Reemplazar tu componente de ranking actual con este código

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Avatar,
  Tag,
  Space,
  Tooltip,
  Badge,
  Typography,
  Row,
  Col,
  Select,
  Button,
  Modal,
  Progress
} from 'antd';
import {
  CrownOutlined,
  TrophyOutlined,
  StarOutlined,
  FireOutlined,
  UserOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import './EnhancedLeaderboard.css'; // Estilos CSS separados

const { Text, Title } = Typography;
const { Option } = Select;

const EnhancedLeaderboard = () => {
  const [leaderboardData, setLeaderboardData] = useState([]);
  const [period, setPeriod] = useState('all');
  const [loading, setLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userModalVisible, setUserModalVisible] = useState(false);

  useEffect(() => {
    loadLeaderboardData();
  }, [period]);

  const loadLeaderboardData = async () => {
    setLoading(true);
    try {
      const response = await fetchWithAuth(`/gamification/leaderboard/enhanced?period=${period}`);
      setLeaderboardData(response.leaderboard || []);
    } catch (error) {
      console.error('Error loading enhanced leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRarityColor = (rarity) => {
    const colors = {
      common: '#8c8c8c',
      rare: '#1890ff',
      epic: '#722ed1',
      legendary: '#fa8c16'
    };
    return colors[rarity] || '#8c8c8c';
  };

  const getRarityGlow = (rarity) => {
    const glows = {
      common: 'none',
      rare: '0 0 8px rgba(24, 144, 255, 0.3)',
      epic: '0 0 12px rgba(114, 46, 209, 0.4)',
      legendary: '0 0 16px rgba(250, 140, 22, 0.5)'
    };
    return glows[rarity] || 'none';
  };

  const getRankIcon = (position) => {
    if (position === 1) return '👑';
    if (position === 2) return '🥈';
    if (position === 3) return '🥉';
    return `#${position}`;
  };

  const showUserAchievements = async (userId, username) => {
    try {
      const response = await fetchWithAuth(`/gamification/achievements/showcase/${userId}`);
      setSelectedUser({ ...response, username });
      setUserModalVisible(true);
    } catch (error) {
      console.error('Error loading user achievements:', error);
    }
  };

  const renderAchievementBadges = (achievements, limit = 5) => {
    if (!achievements || achievements.length === 0) {
      return (
        <div className="no-achievements">
          <span>Sin logros aún</span>
        </div>
      );
    }

    // Ordenar por rareza y mostrar los más raros primero
    const rarityOrder = { legendary: 4, epic: 3, rare: 2, common: 1 };
    const sortedAchievements = achievements
      .sort((a, b) => rarityOrder[b.rarity] - rarityOrder[a.rarity])
      .slice(0, limit);

    return (
      <div className="achievement-badges">
        {sortedAchievements.map((achievement) => (
          <Tooltip
            key={achievement.id}
            title={
              <div>
                <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
                  {achievement.name}
                </div>
                <div style={{ marginBottom: 4 }}>
                  {achievement.description}
                </div>
                <div>
                  <Tag color={getRarityColor(achievement.rarity)} size="small">
                    {achievement.rarity.toUpperCase()}
                  </Tag>
                  <Tag color="green" size="small">
                    +{achievement.points} pts
                  </Tag>
                </div>
              </div>
            }
            placement="top"
          >
            <div
              className="achievement-badge"
              style={{
                borderColor: getRarityColor(achievement.rarity),
                boxShadow: getRarityGlow(achievement.rarity)
              }}
            >
              <span className="achievement-icon">{achievement.icon}</span>
            </div>
          </Tooltip>
        ))}
        {achievements.length > limit && (
          <div className="more-achievements">
            <Tag color="default" size="small">
              +{achievements.length - limit}
            </Tag>
          </div>
        )}
      </div>
    );
  };

  const columns = [
    {
      title: 'Pos',
      dataIndex: 'position',
      key: 'position',
      width: 80,
      align: 'center',
      render: (position, record) => (
        <div className="position-cell">
          <div className={`rank-icon ${position <= 3 ? 'top-three' : ''}`}>
            {getRankIcon(position)}
          </div>
          {position <= 3 && (
            <div className="rank-label">
              {position === 1 ? 'ORO' : position === 2 ? 'PLATA' : 'BRONCE'}
            </div>
          )}
        </div>
      )
    },
    {
      title: 'Técnico',
      key: 'user',
      width: 250,
      render: (_, record) => (
        <div className="user-cell">
          <Avatar 
            size={40} 
            className={`user-avatar ${record.position <= 3 ? 'top-performer' : ''}`}
          >
            {record.username[0].toUpperCase()}
          </Avatar>
          <div className="user-info">
            <div className="username">{record.username}</div>
            <div className="user-tags">
              <Tag color="gold" size="small">Nivel {record.level}</Tag>
              {record.current_streak > 0 && (
                <Tag color="red" size="small">
                  🔥 {record.current_streak}d
                </Tag>
              )}
            </div>
          </div>
        </div>
      )
    },
    {
      title: 'Puntuación',
      dataIndex: 'points',
      key: 'points',
      width: 120,
      align: 'center',
      render: (points, record) => (
        <div className="points-cell">
          <div className={`points-value ${record.position <= 3 ? 'top-score' : ''}`}>
            {points.toLocaleString()}
          </div>
          <div className="points-label">puntos</div>
        </div>
      )
    },
    {
      title: 'Logros Destacados',
      key: 'achievements',
      width: 300,
      render: (_, record) => (
        <div className="achievements-cell">
          {renderAchievementBadges(record.achievements, 4)}
          <div className="achievements-summary">
            🏆 {record.total_achievements} logros totales
          </div>
        </div>
      )
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 100,
      align: 'center',
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          onClick={() => showUserAchievements(record.user_id, record.username)}
        >
          Ver Logros
        </Button>
      )
    }
  ];

  return (
    <div className="enhanced-leaderboard">
      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Card className="leaderboard-card">
            <div className="leaderboard-header">
              <Title level={3} className="leaderboard-title">
                🏆 Ranking de Técnicos
              </Title>
              <Space>
                <Select
                  value={period}
                  onChange={setPeriod}
                  style={{ width: 150 }}
                >
                  <Option value="all">Todo el tiempo</Option>
                  <Option value="monthly">Este mes</Option>
                  <Option value="weekly">Esta semana</Option>
                </Select>
                <Button type="primary" onClick={loadLeaderboardData}>
                  Actualizar
                </Button>
              </Space>
            </div>

            {/* Podium de los 3 primeros */}
            <div className="podium-section">
              <Row gutter={[16, 16]}>
                {leaderboardData.slice(0, 3).map((user, index) => (
                  <Col key={user.user_id} span={8}>
                    <Card className={`podium-card position-${index + 1}`}>
                      <div className="podium-rank">
                        {getRankIcon(user.position)}
                      </div>
                      <Avatar size={60} className="podium-avatar">
                        {user.username[0]}
                      </Avatar>
                      <Title level={5} className="podium-username">
                        {user.username}
                      </Title>
                      <div className="podium-points">
                        {user.points.toLocaleString()}
                      </div>
                      <div className="podium-achievements">
                        {renderAchievementBadges(user.achievements, 3)}
                      </div>
                      <Tag color="gold">Nivel {user.level}</Tag>
                    </Card>
                  </Col>
                ))}
              </Row>
            </div>

            {/* Tabla completa */}
            <Table
              columns={columns}
              dataSource={leaderboardData}
              rowKey="user_id"
              pagination={false}
              loading={loading}
              size="middle"
              className="leaderboard-table"
              rowClassName={(record, index) => {
                if (record.position <= 3) return 'top-three-row';
                return '';
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Modal de logros del usuario */}
      <Modal
        title={`Logros de ${selectedUser?.username || ''}`}
        open={userModalVisible}
        onCancel={() => setUserModalVisible(false)}
        footer={null}
        width={800}
        className="user-achievements-modal"
      >
        {selectedUser && (
          <div>
            <div className="user-stats-summary">
              <Space size="large">
                <div>
                  <Text strong>Nivel:</Text> {selectedUser.user.level}
                </div>
                <div>
                  <Text strong>Puntos:</Text> {selectedUser.user.total_points.toLocaleString()}
                </div>
                <div>
                  <Text strong>Logros:</Text> {selectedUser.stats.total_achievements}
                </div>
              </Space>
            </div>
            
            <div className="completion-progress">
              <Text strong>Progreso de Colección: {selectedUser.stats.completion_rate}%</Text>
              <Progress 
                percent={selectedUser.stats.completion_rate} 
                strokeColor="#52c41a"
                style={{ marginTop: 8 }}
              />
            </div>

            <div className="achievements-grid">
              <Row gutter={[12, 12]}>
                {selectedUser.achievements.map((achievement) => (
                  <Col key={achievement.id} xs={12} sm={8} md={6}>
                    <Card
                      size="small"
                      className="achievement-card-modal"
                      style={{
                        borderColor: getRarityColor(achievement.rarity),
                        backgroundColor: `${getRarityColor(achievement.rarity)}10`
                      }}
                    >
                      <div className="achievement-icon-large">
                        {achievement.icon}
                      </div>
                      <div className="achievement-name">
                        {achievement.name}
                      </div>
                      <div className="achievement-description">
                        {achievement.description}
                      </div>
                      <Space>
                        <Tag color={getRarityColor(achievement.rarity)} size="small">
                          {achievement.rarity.toUpperCase()}
                        </Tag>
                        <Tag color="green" size="small">
                          {achievement.points} pts
                        </Tag>
                      </Space>
                    </Card>
                  </Col>
                ))}
              </Row>

              {selectedUser.achievements.length === 0 && (
                <div className="no-achievements-message">
                  Este usuario aún no tiene logros
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default EnhancedLeaderboard;