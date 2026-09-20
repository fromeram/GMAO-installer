// src/components/MobileLayout.js
import React from 'react';
import { Layout, Button, Typography } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Header, Content } = Layout;
const { Title } = Typography;

const MobileLayout = ({ children, title, showBack = true, onBack }) => {
  const navigate = useNavigate();
  
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate(-1);
    }
  };
  
  return (
    <Layout style={{ 
      height: '100vh', 
      width: '100vw', 
      overflow: 'hidden',
      background: '#f0f2f5'
    }}>
      <Header style={{
        height: '48px',
        padding: '0 8px',
        display: 'flex',
        alignItems: 'center',
        background: '#fff',
        boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
        position: 'sticky',
        top: 0,
        zIndex: 10
      }}>
        {showBack && (
          <Button 
            type="text" 
            icon={<ArrowLeftOutlined />} 
            onClick={handleBack}
            size="small"
            style={{ marginRight: '8px' }}
          />
        )}
        <Title level={5} style={{ margin: 0, fontSize: '16px' }}>
          {title}
        </Title>
      </Header>
      
      <Content style={{
        padding: '8px',
        overflowY: 'auto',
        height: 'calc(100vh - 48px)',
        width: '100vw'
      }}>
        {children}
      </Content>
    </Layout>
  );
};

export default MobileLayout;