// frontend/src/components/RecentActivityWidget.js
import React, { useState, useEffect } from 'react';
import { Card, List, Avatar, Typography, Tag, Space, Button, Empty } from 'antd';
import { 
  UserOutlined, 
  ClockCircleOutlined, 
  EyeOutlined,
  ReloadOutlined 
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { Link } from 'react-router-dom';

dayjs.extend(relativeTime);

const { Text, Title } = Typography;

const RecentActivityWidget = ({ limit = 10 }) => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);

  // Cargar actividad reciente
  const fetchRecentActivity = async () => {
    setLoading(true);
    try {
      const response = await fetchWithAuth(`/audit-trail/recent-activity?limit=${limit}`);
      setActivities(response);
    } catch (error) {
      console.error('Error cargando actividad reciente:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecentActivity();
    
    // Actualizar cada 30 segundos
    const interval = setInterval(fetchRecentActivity, 30000);
    return () => clearInterval(interval);
  }, [limit]);

  // Obtener avatar basado en severidad
  const getSeverityAvatar = (severity, severityIcon) => {
    const colors = {
      'LOW': '#52c41a',
      'MEDIUM': '#1890ff', 
      'HIGH': '#fa8c16',
      'CRITICAL': '#f5222d'
    };
    
    return (
      <Avatar 
        style={{ 
          backgroundColor: colors[severity] || '#d9d9d9',
          fontSize: '12px'
        }}
        size="small"
      >
        {severityIcon}
      </Avatar>
    );
  };

  // Obtener color del módulo
  const getModuleColor = (module) => {
    const colors = {
      'maintenance': 'blue',
      'assets': 'green',
      'users': 'purple',
      'inventory': 'orange',
      'documents': 'cyan'
    };
    return colors[module] || 'default';
  };

  return (
    <Card
      title={
        <Space>
          <ClockCircleOutlined />
          <span>Actividad Reciente</span>
        </Space>
      }
      size="small"
      extra={
        <Space>
          <Button 
            type="text" 
            icon={<ReloadOutlined />} 
            onClick={fetchRecentActivity}
            loading={loading}
            size="small"
          />
          <Link to="/audit-trail">
            <Button type="link" icon={<EyeOutlined />} size="small">
              Ver Todo
            </Button>
          </Link>
        </Space>
      }
      style={{ height: '400px' }}
      bodyStyle={{ padding: '8px', height: '340px', overflowY: 'auto' }}
    >
      {activities.length === 0 && !loading ? (
        <Empty 
          description="No hay actividad reciente" 
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          style={{ marginTop: '60px' }}
        />
      ) : (
        <List
          loading={loading}
          dataSource={activities}
          renderItem={(activity) => (
            <List.Item style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
              <List.Item.Meta
                avatar={getSeverityAvatar(activity.severity, activity.severity_icon)}
                title={
                  <div style={{ fontSize: '13px' }}>
                    <Space size="small">
                      <Text strong style={{ fontSize: '12px' }}>
                        {activity.user_name}
                      </Text>
                      <Tag 
                        color={getModuleColor(activity.module)} 
                        size="small"
                        style={{ fontSize: '10px', padding: '0 4px' }}
                      >
                        {activity.module}
                      </Tag>
                    </Space>
                  </div>
                }
                description={
                  <div>
                    <Text 
                      style={{ 
                        fontSize: '12px', 
                        display: 'block',
                        lineHeight: '1.3',
                        marginBottom: '4px'
                      }}
                    >
                      {activity.summary}
                    </Text>
                    <Text 
                      type="secondary" 
                      style={{ fontSize: '11px' }}
                    >
                      <ClockCircleOutlined style={{ fontSize: '10px', marginRight: '2px' }} />
                      {dayjs(activity.timestamp).fromNow()}
                    </Text>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      )}
    </Card>
  );
};

export default RecentActivityWidget;