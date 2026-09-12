// frontend/src/pages/Gamification.js - ARCHIVO COMPLETO MEJORADO
import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Progress,
  Avatar,
  Table,
  Tag,
  Statistic,
  Timeline,
  Badge,
  Tooltip,
  Space,
  Typography,
  Divider,
  Button,
  Modal,
  notification,
  Select
} from 'antd';
import {
  TrophyOutlined,
  StarOutlined,
  FireOutlined,
  CrownOutlined,
  RocketOutlined,
  TargetOutlined,
  GiftOutlined,
  ThunderboltOutlined,
  CheckSquareOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Gamification.css';

const { Title, Text } = Typography;
const { Option } = Select;

const Gamification = () => {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [achievements, setAchievements] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('all');
  const [achievementModalVisible, setAchievementModalVisible] = useState(false);
  const [selectedAchievement, setSelectedAchievement] = useState(null);
  const { currentUser } = useAuth();

  useEffect(() => {
    loadGamificationData();
  }, []);

  const loadGamificationData = async () => {
    setLoading(true);
    try {
      const [dashboardRes, leaderboardRes, achievementsRes] = await Promise.all([
        fetchWithAuth('/gamification/stats/dashboard'),
        fetchWithAuth(`/gamification/leaderboard/enhanced?period=${selectedPeriod}`), // ← NUEVO ENDPOINT
        fetchWithAuth('/gamification/achievements')
      ]);

      setDashboardData(dashboardRes);
      setLeaderboard(leaderboardRes);
      setAchievements(achievementsRes);
    } catch (error) {
      console.error('Error loading gamification data:', error);
      notification.error({
        message: 'Error',
        description: 'No se pudo cargar la información de gamificación'
      });
    } finally {
      setLoading(false);
    }
  };

  const getRankIcon = (position) => {
    if (position === 1) return <CrownOutlined style={{ color: '#FFD700', fontSize: 20 }} />;
    if (position === 2) return <CrownOutlined style={{ color: '#C0C0C0', fontSize: 18 }} />;
    if (position === 3) return <CrownOutlined style={{ color: '#CD7F32', fontSize: 16 }} />;
    return <span style={{ fontWeight: 'bold', fontSize: 16 }}>#{position}</span>;
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

  const showAchievementDetails = (achievement) => {
    setSelectedAchievement(achievement);
    setAchievementModalVisible(true);
  };

  // ✅ NUEVA FUNCIÓN para mostrar logros de un usuario
  const showUserAchievements = async (userId, username) => {
    try {
      const response = await fetchWithAuth(`/gamification/achievements/showcase/${userId}`);
      
      Modal.info({
        title: `Logros de ${username}`,
        width: 800,
        content: (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>Nivel:</Text> {response.user.level} | 
              <Text strong> Puntos:</Text> {response.user.total_points.toLocaleString()} | 
              <Text strong> Logros:</Text> {response.stats.total_achievements}
            </div>
            
            <div style={{ marginBottom: 16 }}>
              <Text strong>Progreso de Colección:</Text> {response.stats.completion_rate}%
              <Progress 
                percent={response.stats.completion_rate} 
                size="small" 
                strokeColor="#52c41a"
                style={{ marginTop: 4 }}
              />
            </div>

            <Divider />
            
            <Row gutter={[12, 12]}>
              {response.achievements.map((achievement) => (
                <Col key={achievement.id} xs={24} sm={12} md={8} lg={6}>
                  <Card
                    size="small"
                    style={{
                      textAlign: 'center',
                      borderColor: getRarityColor(achievement.rarity),
                      backgroundColor: `${getRarityColor(achievement.rarity)}10`
                    }}
                  >
                    <div style={{ fontSize: 24, marginBottom: 8 }}>
                      {achievement.icon}
                    </div>
                    <div style={{ fontSize: 12, fontWeight: 'bold', marginBottom: 4 }}>
                      {achievement.name}
                    </div>
                    <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 8 }}>
                      {achievement.description}
                    </Text>
                    <div>
                      <Tag color={getRarityColor(achievement.rarity)} size="small">
                        {achievement.rarity.toUpperCase()}
                      </Tag>
                      <Tag color="green" size="small">
                        {achievement.points} pts
                      </Tag>
                    </div>
                    {achievement.earned_at && (
                      <Text type="secondary" style={{ fontSize: 10, display: 'block', marginTop: 4 }}>
                        Obtenido: {new Date(achievement.earned_at).toLocaleDateString()}
                      </Text>
                    )}
                  </Card>
                </Col>
              ))}
            </Row>

            {response.achievements.length === 0 && (
              <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
                Este usuario aún no tiene logros
              </div>
            )}
          </div>
        ),
      });
    } catch (error) {
      notification.error({
        message: 'Error',
        description: 'No se pudieron cargar los logros del usuario'
      });
    }
  };

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <div>Cargando información de gamificación...</div>
      </div>
    );
  }

  return (
    <div className="gamification-container" style={{ padding: 24 }}>
      <Title level={2}>
        <TrophyOutlined /> Gamificación - Mi Progreso
      </Title>

      {/* Estadísticas Principales */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card className="stat-card level-card" style={{ textAlign: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ marginRight: 16 }}>
                <StarOutlined style={{ fontSize: 32, color: '#faad14' }} />
              </div>
              <div>
                <Statistic
                  title="Nivel"
                  value={dashboardData?.user_stats?.level || 1}
                  suffix={`/ ${dashboardData?.user_stats?.level + 1 || 2}`}
                />
                <Progress
                  percent={
                    dashboardData?.user_stats?.xp_to_next_level > 0
                      ? Math.max(0, 100 - (dashboardData.user_stats.xp_to_next_level / 
                          (dashboardData.user_stats.next_level_xp - 
                           (dashboardData.user_stats.next_level_xp - dashboardData.user_stats.xp_to_next_level))) * 100)
                      : 100
                  }
                  size="small"
                  strokeColor="#faad14"
                />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card style={{ textAlign: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ marginRight: 16 }}>
                <GiftOutlined style={{ fontSize: 32, color: '#52c41a' }} />
              </div>
              <div>
                <Statistic
                  title="Puntos Totales"
                  value={dashboardData?.user_stats?.total_points || 0}
                  valueStyle={{ color: '#52c41a' }}
                />
                <Text type="secondary">
                  +{dashboardData?.weekly_stats?.points_earned || 0} esta semana
                </Text>
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card style={{ textAlign: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ marginRight: 16 }}>
                <RocketOutlined style={{ fontSize: 32, color: '#1890ff' }} />
              </div>
              <div>
                <Statistic
                  title="Ranking"
                  value={dashboardData?.user_stats?.rank_position || 0}
                  prefix="#"
                  valueStyle={{ color: '#1890ff' }}
                />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card style={{ textAlign: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ marginRight: 16 }}>
                <FireOutlined style={{ fontSize: 32, color: '#ff4d4f' }} />
              </div>
              <div>
                <Statistic
                  title="Racha Actual"
                  value={dashboardData?.user_stats?.current_streak || 0}
                  suffix="días"
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        {/* Panel de Logros */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <TrophyOutlined />
                <span>Mis Logros</span>
                <Badge count={achievements.filter(a => a.earned_at).length} />
              </Space>
            }
            extra={
              <Button size="small" onClick={() => setAchievementModalVisible(true)}>
                Ver todos
              </Button>
            }
          >
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(60px, 1fr))', gap: 8 }}>
              {achievements.slice(0, 12).map((achievement) => (
                <Tooltip
                  key={achievement.id}
                  title={
                    <div>
                      <div style={{ fontWeight: 'bold' }}>{achievement.name}</div>
                      <div>{achievement.description}</div>
                      <div style={{ color: getRarityColor(achievement.rarity) }}>
                        {achievement.rarity.toUpperCase()} • {achievement.points} pts
                      </div>
                    </div>
                  }
                >
                  <div
                    style={{
                      width: 60,
                      height: 60,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRadius: 8,
                      border: `2px solid ${achievement.earned_at ? getRarityColor(achievement.rarity) : '#d9d9d9'}`,
                      backgroundColor: achievement.earned_at ? 'rgba(255,255,255,0.9)' : '#f5f5f5',
                      cursor: 'pointer',
                      transition: 'all 0.3s ease',
                      opacity: achievement.earned_at ? 1 : 0.6,
                      fontSize: 24
                    }}
                    onClick={() => showAchievementDetails(achievement)}
                    onMouseEnter={(e) => {
                      if (achievement.earned_at) {
                        e.target.style.transform = 'scale(1.1)';
                        e.target.style.boxShadow = `0 4px 12px ${getRarityColor(achievement.rarity)}40`;
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.transform = 'scale(1)';
                      e.target.style.boxShadow = 'none';
                    }}
                  >
                    {achievement.earned_at ? achievement.icon : '🔒'}
                  </div>
                </Tooltip>
              ))}
            </div>

            {/* Logros Recientes */}
            {dashboardData?.recent_achievements?.length > 0 && (
              <>
                <Divider />
                <Title level={5}>🎉 Logros Recientes</Title>
                <Timeline size="small">
                  {dashboardData.recent_achievements.map((achievement, index) => (
                    <Timeline.Item key={index}>
                      <Text>
                        <span style={{ fontSize: 16 }}>{achievement.icon}</span>{' '}
                        <strong>{achievement.name}</strong>{' '}
                        <Tag color={getRarityColor(achievement.rarity)}>
                          +{achievement.points} pts
                        </Tag>
                      </Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {new Date(achievement.earned_at).toLocaleDateString()}
                      </Text>
                    </Timeline.Item>
                  ))}
                </Timeline>
              </>
            )}
          </Card>
        </Col>

        {/* ✅ RANKING MEJORADO CON LOGROS */}
        <Col xs={24} lg={12}>
          <Row gutter={[0, 16]}>
            {/* Ranking con Logros Visuales */}
            <Col span={24}>
              <Card
                title={
                  <Space>
                    <CrownOutlined />
                    <span>Top Técnicos con Logros</span>
                  </Space>
                }
                size="small"
                extra={
                  <Space>
                    <Select 
                      value={selectedPeriod} 
                      onChange={(value) => {
                        setSelectedPeriod(value);
                        loadGamificationData();
                      }}
                      size="small"
                      style={{ width: 120 }}
                    >
                      <Option value="all">General</Option>
                      <Option value="monthly">Mensual</Option>
                      <Option value="weekly">Semanal</Option>
                    </Select>
                  </Space>
                }
              >
                <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                  {leaderboard.leaderboard?.slice(0, 10).map((user, index) => (
                    <div 
                      key={user.user_id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        padding: '12px 8px',
                        marginBottom: 8,
                        backgroundColor: user.user_id === currentUser?.id ? '#e6f7ff' : 
                                        index < 3 ? '#fffbe6' : '#fafafa',
                        borderRadius: 8,
                        border: user.user_id === currentUser?.id ? '2px solid #1890ff' : 
                               index < 3 ? '1px solid #faad14' : '1px solid #d9d9d9',
                        cursor: 'pointer',
                        transition: 'all 0.3s ease'
                      }}
                      onClick={() => showUserAchievements(user.user_id, user.username)}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-2px)';
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    >
                      {/* Posición y Avatar */}
                      <div style={{ minWidth: 60, textAlign: 'center' }}>
                        {getRankIcon(user.position)}
                        <Avatar 
                          size={32} 
                          style={{ 
                            backgroundColor: index < 3 ? '#faad14' : '#1890ff',
                            marginTop: 4
                          }}
                        >
                          {user.username[0].toUpperCase()}
                        </Avatar>
                      </div>

                      {/* Info del Usuario */}
                      <div style={{ flex: 1, marginLeft: 12 }}>
                        <div style={{ 
                          fontWeight: 'bold', 
                          fontSize: 14,
                          color: user.user_id === currentUser?.id ? '#1890ff' : 'inherit'
                        }}>
                          {user.username}
                          {user.user_id === currentUser?.id && ' (Tú)'}
                        </div>
                        
                        <Space size={4} style={{ marginTop: 2 }}>
                          <Tag color="green" size="small">
                            {user.points.toLocaleString()} pts
                          </Tag>
                          <Tag color="gold" size="small">
                            Nv.{user.level}
                          </Tag>
                          {user.current_streak > 0 && (
                            <Tag color="red" size="small">
                              <FireOutlined /> {user.current_streak}d
                            </Tag>
                          )}
                        </Space>

                        {/* Logros del Usuario */}
                        <div style={{ marginTop: 6 }}>
                          <Space size={2} wrap>
                            {user.achievements?.slice(0, 4).map((achievement) => (
                              <Tooltip
                                key={achievement.id}
                                title={
                                  <div>
                                    <div style={{ fontWeight: 'bold' }}>{achievement.name}</div>
                                    <div style={{ fontSize: 12 }}>{achievement.description}</div>
                                    <Tag color={getRarityColor(achievement.rarity)} size="small">
                                      {achievement.rarity.toUpperCase()} • {achievement.points} pts
                                    </Tag>
                                  </div>
                                }
                              >
                                <div
                                  style={{
                                    fontSize: 16,
                                    padding: '2px 4px',
                                    borderRadius: 4,
                                    border: `1px solid ${getRarityColor(achievement.rarity)}`,
                                    backgroundColor: 'rgba(255,255,255,0.8)',
                                    display: 'inline-block',
                                    marginRight: 2
                                  }}
                                >
                                  {achievement.icon}
                                </div>
                              </Tooltip>
                            ))}
                            {user.total_achievements > 4 && (
                              <Tag size="small" style={{ fontSize: 10 }}>
                                +{user.total_achievements - 4}
                              </Tag>
                            )}
                          </Space>
                        </div>
                      </div>

                      {/* Indicador de posición */}
                      <div style={{ minWidth: 30, textAlign: 'center' }}>
                        {index < 3 && (
                          <div style={{ 
                            fontSize: 10, 
                            color: '#faad14', 
                            fontWeight: 'bold' 
                          }}>
                            TOP {index + 1}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Resumen del ranking */}
                <Divider style={{ margin: '12px 0' }} />
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Tu posición: #{leaderboard.current_user_position} de {leaderboard.total_participants} técnicos
                  </Text>
                </div>
              </Card>
            </Col>

            {/* Actividad Reciente */}
            <Col span={24}>
              <Card
                title={
                  <Space>
                    <ThunderboltOutlined />
                    <span>Actividad Reciente</span>
                  </Space>
                }
                size="small"
              >
                <Timeline size="small">
                  {dashboardData?.recent_activities?.slice(0, 8).map((activity, index) => (
                    <Timeline.Item key={index}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text ellipsis style={{ maxWidth: '200px' }}>
                          {activity.reason}
                        </Text>
                        <Tag color={activity.type === 'gain' ? 'green' : 'red'}>
                          {activity.type === 'gain' ? '+' : ''}{activity.points}
                        </Tag>
                      </div>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {new Date(activity.created_at).toLocaleString()}
                      </Text>
                    </Timeline.Item>
                  ))}
                </Timeline>
              </Card>
            </Col>
          </Row>
        </Col>
      </Row>

      {/* Modal de Logros */}
      <Modal
        title="Todos los Logros"
        open={achievementModalVisible}
        onCancel={() => setAchievementModalVisible(false)}
        footer={null}
        width={800}
      >
        <Row gutter={[16, 16]}>
          {achievements.map((achievement) => (
            <Col key={achievement.id} xs={24} sm={12} md={8} lg={6}>
              <Card
                size="small"
                style={{
                  textAlign: 'center',
                  borderColor: achievement.earned_at ? getRarityColor(achievement.rarity) : '#d9d9d9',
                  opacity: achievement.earned_at ? 1 : 0.6
                }}
              >
                <div style={{ fontSize: 32, marginBottom: 8 }}>
                  {achievement.earned_at ? achievement.icon : '🔒'}
                </div>
                <Title level={5} style={{ margin: 0, fontSize: 14 }}>
                  {achievement.name}
                </Title>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {achievement.description}
                </Text>
                <div style={{ marginTop: 8 }}>
                  <Tag color={getRarityColor(achievement.rarity)} size="small">
                    {achievement.rarity.toUpperCase()}
                  </Tag>
                  <Tag color="green" size="small">
                    {achievement.points} pts
                  </Tag>
                </div>
                {achievement.earned_at && (
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    Obtenido: {new Date(achievement.earned_at).toLocaleDateString()}
                  </Text>
                )}
              </Card>
            </Col>
          ))}
        </Row>
      </Modal>
    </div>
  );
};

export default Gamification;