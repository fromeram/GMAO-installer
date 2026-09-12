// src/components/FormatChangesWidget.js - Widget para Dashboard
import React, { useState, useEffect } from 'react';
import { Card, Statistic, Button, Row, Col, Typography } from 'antd';
import { SettingOutlined, ToolOutlined, GlobalOutlined, ApartmentOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { fetchWithAuth } from '../apiConfig';

const { Text } = Typography;

const FormatChangesWidget = () => {
  const [formatStats, setFormatStats] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadFormatStats();
  }, []);

  const loadFormatStats = async () => {
    try {
      const data = await fetchWithAuth('/dashboard/format-changes?days=30');
      setFormatStats(data);
    } catch (error) {
      console.error('Error loading format stats:', error);
      setFormatStats({
        kpis: { total_changes: 0, average_efficiency: 0, completion_rate: 0 }
      });
    } finally {
      setLoading(false);
    }
  };

  if (!formatStats && !loading) return null;

  return (
    <Card 
      title="Cambios de Formato (30 días)" 
      size="small"
      extra={
        <Link to="/reportes-formato">
          <Button type="link" size="small">Ver reportes</Button>
        </Link>
      }
    >
      <Row gutter={8}>
        <Col span={8}>
          <Statistic
            title="Total"
            value={formatStats?.kpis?.total_changes || 0}
            prefix={<SettingOutlined />}
            valueStyle={{ fontSize: '16px' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Eficiencia"
            value={formatStats?.kpis?.average_efficiency || 0}
            precision={1}
            suffix="%"
            valueStyle={{ 
              fontSize: '16px',
              color: (formatStats?.kpis?.average_efficiency || 0) >= 100 ? '#52c41a' : '#faad14'
            }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Completados"
            value={formatStats?.kpis?.completion_rate || 0}
            precision={0}
            suffix="%"
            valueStyle={{ 
              fontSize: '16px',
              color: (formatStats?.kpis?.completion_rate || 0) >= 80 ? '#52c41a' : '#ff4d4f'
            }}
          />
        </Col>
      </Row>
      
      {formatStats?.kpis && (
        <div style={{ marginTop: 12, fontSize: '12px' }}>
          <Row gutter={4}>
            <Col span={8}>
              <Text type="secondary">
                <GlobalOutlined /> {formatStats.kpis.global_changes || 0} Globales
              </Text>
            </Col>
            <Col span={8}>
              <Text type="secondary">
                <ApartmentOutlined /> {formatStats.kpis.line_changes || 0} Línea
              </Text>
            </Col>
            <Col span={8}>
              <Text type="secondary">
                <ToolOutlined /> {formatStats.kpis.individual_changes || 0} Individual
              </Text>
            </Col>
          </Row>
        </div>
      )}
    </Card>
  );
};

export default FormatChangesWidget;