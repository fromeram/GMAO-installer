// src/components/AlertsSidebar.js (Versión Completa con Comunicaciones Integradas)
import React, { useState, useEffect } from 'react';
import { 
  Drawer, 
  List, 
  Badge, 
  Button, 
  Space, 
  Tag, 
  Typography, 
  Spin, 
  Empty, 
  message, 
  Divider,
  Card
} from 'antd';
import { 
  BellOutlined, 
  CheckOutlined, 
  InfoCircleOutlined, 
  WarningOutlined, 
  CloseCircleOutlined,
  MessageOutlined,
  SendOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { Link } from 'react-router-dom';

const { Text, Paragraph } = Typography;

const AlertsSidebar = () => {
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [unreadMessagesCount, setUnreadMessagesCount] = useState(0);
  const [resolvingId, setResolvingId] = useState(null);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  // Detectar tamaño de pantalla para modo responsivo
  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  // Determinar si estamos en modo móvil
  const isMobile = windowWidth < 768;

  useEffect(() => {
    // Al cargar el componente, comprobar si hay alertas pendientes
    checkForAlerts();
    
    // Configurar intervalo para comprobar periódicamente nuevas alertas
    const intervalId = setInterval(checkForAlerts, 60000); // Cada minuto
    
    return () => clearInterval(intervalId);
  }, []);

  const checkForAlerts = async () => {
    try {
      // Cargar alertas tradicionales
      const unresolvedAlerts = await fetchWithAuth('/alerts?unresolved_only=true');
      
      // NUEVO: Cargar mensajes no leídos
      const messagesResponse = await fetchWithAuth('/communications/unread-count');
      const unreadMessages = messagesResponse.unread_count || 0;
      
      // Configurar estados
      setAlerts(unresolvedAlerts || []);
      setUnreadMessagesCount(unreadMessages);
      
      // Combinar contadores para el badge principal
      const totalUnread = (unresolvedAlerts?.length || 0) + unreadMessages;
      setUnreadCount(totalUnread);
      
    } catch (error) {
      console.error("Error checking alerts:", error);
    }
  };

  const loadAlerts = async () => {
    setLoading(true);
    try {
      // Cargar alertas tradicionales
      const unresolvedAlerts = await fetchWithAuth('/alerts?unresolved_only=true');
      
      // Cargar mensajes no leídos
      const messagesResponse = await fetchWithAuth('/communications/unread-count');
      const unreadMessages = messagesResponse.unread_count || 0;
      
      setAlerts(unresolvedAlerts || []);
      setUnreadMessagesCount(unreadMessages);
      
      // Combinar contadores
      const totalUnread = (unresolvedAlerts?.length || 0) + unreadMessages;
      setUnreadCount(totalUnread);
      
    } catch (error) {
      console.error("Error loading alerts:", error);
      message.error("No se pudieron cargar las alertas");
    } finally {
      setLoading(false);
    }
  };

  const resolveAlert = async (alertId) => {
    setResolvingId(alertId);
    try {
      await fetchWithAuth(`/alerts/${alertId}/resolve`, {
        method: 'PUT'
      });
      message.success("Alerta marcada como resuelta");
      loadAlerts();
    } catch (error) {
      console.error("Error resolving alert:", error);
      message.error("No se pudo resolver la alerta");
    } finally {
      setResolvingId(null);
    }
  };

  const showDrawer = () => {
    setVisible(true);
    loadAlerts();
  };

  const onClose = () => {
    setVisible(false);
  };

  const getAlertIcon = (severity) => {
    switch (severity) {
      case 'info':
        return <InfoCircleOutlined style={{ color: '#1890ff' }} />;
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />;
      case 'danger':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <InfoCircleOutlined style={{ color: '#1890ff' }} />;
    }
  };

  const getEntityLink = (entityType, entityId) => {
    if (!entityType || !entityId) return null;
    
    switch (entityType) {
      case 'work_order':
        return <Link to={`/ordenes/${entityId}`}>Ver Orden</Link>;
      case 'machine':
        return <Link to={`/maquinas/${entityId}/detail`}>Ver Máquina</Link>;
      case 'inventory':
        return <Link to={`/productos/${entityId}`}>Ver Producto</Link>;
      case 'maintenance':
        return <Link to={`/mantenimiento/preventivo`}>Ver Mantenimiento</Link>;
      case 'backlog':
        return <Link to={`/backlog-mantenimiento`}>Ver Backlog</Link>;
      case 'communication':
        return <Link to={`/communications`}>Ver Comunicaciones</Link>;
      default:
        return null;
    }
  };

  // Crear alertas virtuales para mensajes no leídos
  const createMessageAlerts = () => {
    if (unreadMessagesCount === 0) return [];
    
    return [{
      id: 'unread-messages-virtual',
      type: 'MESSAGE',
      message: `Tienes ${unreadMessagesCount} mensaje${unreadMessagesCount > 1 ? 's' : ''} sin leer`,
      severity: 'info',
      created_at: new Date().toISOString(),
      entity_type: 'communication',
      entity_id: null,
      isVirtual: true // Marcador para distinguir alertas virtuales
    }];
  };

  // Combinar alertas reales con alertas virtuales de mensajes
  const allAlerts = [...createMessageAlerts(), ...alerts];

  return (
    <>
      <Badge count={unreadCount} size="small">
        <Button
          type="text"
          icon={<BellOutlined style={{ fontSize: isMobile ? '16px' : '20px' }} />}
          onClick={showDrawer}
          style={{ padding: isMobile ? '4px' : '8px' }}
          size={isMobile ? "small" : "middle"}
        />
      </Badge>
      
      <Drawer
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <BellOutlined style={{ marginRight: '8px' }} />
            <span>Notificaciones</span>
            <Badge 
              count={unreadCount} 
              style={{ marginLeft: '12px' }}
              showZero
            />
          </div>
        }
        placement="right"
        onClose={onClose}
        open={visible}
        width={isMobile ? "80vw" : 400}
        extra={
          <Button type="text" onClick={loadAlerts} loading={loading} size={isMobile ? "small" : "middle"}>
            Actualizar
          </Button>
        }
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: isMobile ? '20px 0' : '40px 0' }}>
            <Spin size={isMobile ? "small" : "default"} />
            <div style={{ marginTop: isMobile ? '8px' : '16px', fontSize: isMobile ? '12px' : '14px' }}>
              Cargando notificaciones...
            </div>
          </div>
        ) : (
          <>
            {/* NUEVA SECCIÓN: Resumen de Comunicaciones */}
            {unreadMessagesCount > 0 && (
              <>
                <Card 
                  size="small" 
                  style={{ 
                    marginBottom: '16px',
                    background: '#f6ffed',
                    border: '1px solid #b7eb8f'
                  }}
                >
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between' 
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <MessageOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
                      <div>
                        <Text strong style={{ color: '#389e0d' }}>
                          {unreadMessagesCount} Mensaje{unreadMessagesCount > 1 ? 's' : ''} Nuevo{unreadMessagesCount > 1 ? 's' : ''}
                        </Text>
                        <br />
                        <Text style={{ fontSize: '12px', color: '#666' }}>
                          Comunicaciones sin leer
                        </Text>
                      </div>
                    </div>
                    <Link to="/communications" onClick={onClose}>
                      <Button 
                        type="primary" 
                        size="small" 
                        icon={<EyeOutlined />}
                        style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
                      >
                        Ver
                      </Button>
                    </Link>
                  </div>
                </Card>
                <Divider style={{ margin: '12px 0' }} />
              </>
            )}

            {/* Botón de acceso rápido a comunicaciones */}
            <div style={{ marginBottom: '16px' }}>
              <Link to="/communications" onClick={onClose}>
                <Button 
                  block 
                  icon={<MessageOutlined />}
                  style={{ 
                    height: '40px',
                    borderColor: '#52c41a',
                    color: '#52c41a'
                  }}
                >
                  Ir a Comunicaciones
                </Button>
              </Link>
            </div>

            <Divider style={{ margin: '12px 0' }} />

            {/* Lista de alertas del sistema */}
            {allAlerts.length === 0 ? (
              <Empty 
                description="No hay notificaciones pendientes" 
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ) : (
              <List
                dataSource={allAlerts}
                renderItem={(alert) => (
                  <List.Item
                    key={alert.id}
                    actions={[
                      // Solo mostrar botón resolver para alertas reales (no virtuales)
                      !alert.isVirtual && (
                        <Button 
                          type="text" 
                          icon={<CheckOutlined />} 
                          onClick={() => resolveAlert(alert.id)}
                          loading={resolvingId === alert.id}
                          size={isMobile ? "small" : "middle"}
                        >
                          {!isMobile && "Resolver"}
                        </Button>
                      )
                    ].filter(Boolean)} // Filtrar elementos falsy
                    style={{ 
                      padding: isMobile ? '8px 0' : '12px 0',
                      backgroundColor: alert.isVirtual ? '#f6ffed' : 'transparent',
                      borderRadius: alert.isVirtual ? '6px' : '0',
                      marginBottom: alert.isVirtual ? '8px' : '0'
                    }}
                  >
                    <List.Item.Meta
                      avatar={
                        alert.isVirtual ? 
                          <MessageOutlined style={{ color: '#52c41a', fontSize: '16px' }} /> :
                          getAlertIcon(alert.severity)
                      }
                      title={
                        <div style={{ fontSize: isMobile ? '12px' : '14px' }}>
                          <Tag color={
                            alert.isVirtual ? 'green' : (
                              alert.severity === 'danger' ? 'red' : 
                              alert.severity === 'warning' ? 'orange' : 'blue'
                            )
                          }>
                            {alert.isVirtual ? 'MENSAJE' : alert.type}
                          </Tag>
                          <Text style={{ marginLeft: '8px', fontSize: isMobile ? '10px' : '12px' }}>
                            {new Date(alert.created_at).toLocaleString()}
                          </Text>
                        </div>
                      }
                      description={
                        <>
                          <Paragraph style={{ 
                            fontSize: isMobile ? '12px' : '14px', 
                            marginBottom: '4px',
                            color: alert.isVirtual ? '#389e0d' : 'inherit',
                            fontWeight: alert.isVirtual ? '500' : 'normal'
                          }}>
                            {alert.message}
                          </Paragraph>
                          <Space>
                            {getEntityLink(alert.entity_type, alert.entity_id)}
                          </Space>
                        </>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </>
        )}
      </Drawer>
    </>
  );
};

export default AlertsSidebar;