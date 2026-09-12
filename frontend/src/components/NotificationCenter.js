// src/components/NotificationCenter.js
import React, { useState, useEffect, useRef } from 'react';
import {
  Modal, Badge, Button, Card, Empty, Tabs, Tag, Space,
  Typography, List, Avatar, Tooltip, notification, Row, Col,
  Divider, Alert
} from 'antd';
import {
  BellOutlined, ClockCircleOutlined, ToolOutlined,
  MessageOutlined, CheckCircleOutlined, ExclamationCircleOutlined,
  CalendarOutlined, UserOutlined, CloseOutlined, EyeOutlined,
  WarningOutlined, InfoCircleOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/es';

dayjs.extend(relativeTime);
dayjs.locale('es');

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

const NotificationCenter = () => {
  const [visible, setVisible] = useState(false);
  const [notifications, setNotifications] = useState({
    maintenance: [],
    communications: [],
    alerts: [],
    vacations: []
  });
  const [loading, setLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  
  // ✅ CAMBIO PRINCIPAL: Controlar notificación por sesión del usuario
  const [hasShownInitialNotification, setHasShownInitialNotification] = useState(false);
  
  // ✅ NUEVO: Guardar hash de notificaciones para detectar cambios reales
  const [lastNotificationHash, setLastNotificationHash] = useState('');
  
  const initialNotificationClose = useRef(null);
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  // ✅ FUNCIÓN PARA CREAR HASH DE NOTIFICACIONES
  const createNotificationHash = (notificationData) => {
    const hashData = {
      maintenance: notificationData.maintenance.map(n => n.id),
      communications: notificationData.communications.map(n => n.id),
      alerts: notificationData.alerts.map(n => n.id),
      vacations: notificationData.vacations.map(n => n.id)
    };
    return JSON.stringify(hashData);
  };

  // Cargar notificaciones
  const loadNotifications = async () => {
    if (!currentUser) return;

    setLoading(true);
    try {
      // Cargar mantenimientos preventivos pendientes
      let maintenanceResponse = [];
      try {
        maintenanceResponse = await fetchWithAuth('/mantenimiento-preventivo/pending');
      } catch (error) {
        console.log('Error cargando mantenimientos:', error);
        maintenanceResponse = [];
      }

      // Cargar el conteo de comunicaciones no leídas
      let unreadCommsCount = 0;
      try {
        const countResponse = await fetchWithAuth('/communications/unread-count');
        unreadCommsCount = countResponse.count || 0;
      } catch (error) {
        console.log('Error cargando conteo de comunicaciones:', error);
      }

      // Cargar alertas del sistema
      let alertsResponse = [];
      try {
        const alertsData = await fetchWithAuth('/alerts?unresolved_only=true');
        alertsResponse = alertsData.alerts || alertsData || [];
      } catch (error) {
        console.log('Error cargando alertas:', error);
        alertsResponse = [];
      }

      // Cargar vacaciones pendientes
      let vacationsResponse = [];
      try {
        vacationsResponse = await fetchWithAuth('/api/vacaciones/pending');
      } catch (error) {
        console.log('Error cargando vacaciones:', error);
        vacationsResponse = [];
      }

      // Procesar mantenimientos
      const maintenanceNotifications = Array.isArray(maintenanceResponse)
        ? maintenanceResponse.map(item => ({
            id: `maint-${item.id}`,
            type: 'maintenance',
            title: item.title,
            description: `Mantenimiento programado para máquina: ${item.machine_name || item.maquina_nombre}`,
            date: item.next_maintenance_date,
            severity: getDaysDifference(item.next_maintenance_date) <= 1 ? 'high' : 'medium',
            actions: [
              {
                label: 'Ver Detalles',
                action: () => {
                  closeInitialNotification();
                  setVisible(false);
                  navigate('/mantenimiento/preventivo');
                },
                type: 'primary'
              }
            ],
            metadata: {
              machine: item.machine_name || item.maquina_nombre,
              frequency: item.frecuencia,
              assignedTo: item.assigned_user?.username || item.assigned_role?.nombre
            }
          }))
        : [];

      // Crear notificación simple para comunicaciones no leídas
      const communicationNotifications = unreadCommsCount > 0 ? [{
        id: 'comm-unread',
        type: 'communication',
        title: `${unreadCommsCount} comunicaciones no leídas`,
        description: 'Tienes mensajes pendientes de leer',
        date: new Date().toISOString(),
        severity: 'low',
        actions: [
          {
            label: 'Ver Comunicaciones',
            action: () => {
              closeInitialNotification();
              setVisible(false);
              navigate('/communications');
            },
            type: 'primary'
          }
        ],
        metadata: {
          count: unreadCommsCount
        }
      }] : [];

      // Procesar alertas
      const systemAlerts = Array.isArray(alertsResponse)
        ? alertsResponse.filter(alert => !alert.resolved).map(alert => ({
            id: `alert-${alert.id}`,
            type: 'alert',
            title: getAlertTitle(alert.type),
            description: alert.message,
            date: alert.created_at,
            severity: alert.severity === 'danger' ? 'high' : alert.severity === 'warning' ? 'medium' : 'low',
            actions: [
              {
                label: 'Ver',
                action: () => {
                  closeInitialNotification();
                  handleViewAlert(alert);
                },
                type: 'default'
              }
            ],
            metadata: {
              entityType: alert.entity_type,
              entityId: alert.entity_id
            }
          }))
        : [];

      // Procesar vacaciones
      const vacationNotifications = Array.isArray(vacationsResponse)
        ? vacationsResponse.map(vacation => ({
            id: `vacation-${vacation.id}`,
            type: 'vacation',
            title: getVacationTitle(vacation.notification_type, vacation),
            description: getVacationDescription(vacation),
            date: vacation.fecha_solicitud,
            severity: getVacationSeverity(vacation.notification_type),
            actions: [
              {
                label: 'Ver Detalles',
                action: () => {
                  closeInitialNotification();
                  setVisible(false);
                  navigate('/calendario-vacaciones');
                },
                type: 'primary'
              }
            ],
            metadata: {
              estado: vacation.estado,
              solicitante: vacation.solicitante ? 
                `${vacation.solicitante.nombre} ${vacation.solicitante.apellidos}` : 
                'Usuario',
              fechas: `${vacation.fecha_inicio} - ${vacation.fecha_fin}`,
              tipo: vacation.notification_type
            }
          }))
        : [];

      const allNotifications = {
        maintenance: maintenanceNotifications,
        communications: communicationNotifications,
        alerts: systemAlerts,
        vacations: vacationNotifications
      };

      setNotifications(allNotifications);

      const totalUnread = maintenanceNotifications.length +
                         communicationNotifications.length +
                         systemAlerts.length +
                         vacationNotifications.length;

      setUnreadCount(totalUnread);

      // ✅ LÓGICA MEJORADA: Solo mostrar notificación si hay cambios reales
      const currentHash = createNotificationHash(allNotifications);
      const userId = currentUser?.id;
      
      // Solo mostrar notificación inicial si:
      // 1. No se ha mostrado antes en esta sesión para este usuario
      // 2. Hay notificaciones pendientes
      // 3. Tenemos un usuario válido
      if (!hasShownInitialNotification && totalUnread > 0 && userId) {
        console.log('🔔 Mostrando notificación inicial - usuario con notificaciones pendientes');
        setHasShownInitialNotification(true);
        sessionStorage.setItem(`hasShownInitialNotification_${userId}`, 'true');
        showInitialNotification(totalUnread);
      }
      
      // Actualizar hash para este usuario
      if (currentHash !== lastNotificationHash && userId) {
        setLastNotificationHash(currentHash);
        sessionStorage.setItem(`lastNotificationHash_${userId}`, currentHash);
      }

    } catch (error) {
      console.error('Error cargando notificaciones:', error);
      notification.error({
        message: 'Error',
        description: 'No se pudieron cargar las notificaciones'
      });
    } finally {
      setLoading(false);
    }
  };

  // ✅ FUNCIÓN MEJORADA PARA CERRAR NOTIFICACIÓN INICIAL
  const closeInitialNotification = () => {
    if (initialNotificationClose.current) {
      initialNotificationClose.current();
      initialNotificationClose.current = null;
    }
    notification.destroy(); // Destruir todas las notificaciones de antd
  };

  // Mostrar notificación inicial grande
  const showInitialNotification = (count) => {
    // ✅ CERRAR CUALQUIER NOTIFICACIÓN PREVIA ANTES DE MOSTRAR NUEVA
    closeInitialNotification();
    
    const closeFunc = notification.open({
      message: (
        <Space>
          <ExclamationCircleOutlined style={{ fontSize: '24px', color: '#ff4d4f' }} />
          <span style={{ fontSize: '18px', fontWeight: 'bold' }}>
            ¡Tienes {count} notificaciones pendientes!
          </span>
        </Space>
      ),
      description: (
        <div>
          <Paragraph>
            Hay tareas importantes que requieren tu atención.
            Haz clic en el botón de notificaciones para revisarlas.
          </Paragraph>
          <Button
            type="primary"
            onClick={() => {
              closeInitialNotification();
              setVisible(true);
            }}
            icon={<BellOutlined />}
          >
            Ver Notificaciones
          </Button>
        </div>
      ),
      duration: 0, // No se cierra automáticamente
      placement: 'topRight',
      style: {
        width: 400,
        marginTop: 48,
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
      },
      className: 'initial-notification-popup'
    });
    initialNotificationClose.current = closeFunc;
  };

  // ✅ FUNCIÓN PARA RESETEAR ESTADO DE NOTIFICACIONES
  const resetNotificationState = () => {
    const userId = currentUser?.id;
    if (userId) {
      setHasShownInitialNotification(false);
      sessionStorage.removeItem(`hasShownInitialNotification_${userId}`);
      sessionStorage.removeItem(`lastNotificationHash_${userId}`);
      setLastNotificationHash('');
    }
  };

  // Utilidades
  const getDaysDifference = (date) => {
    const today = dayjs();
    const targetDate = dayjs(date);
    return targetDate.diff(today, 'day');
  };

  const getAlertTitle = (type) => {
    const titles = {
      maintenance: 'Alerta de Mantenimiento',
      stock: 'Alerta de Inventario',
      system: 'Alerta del Sistema',
      work_order: 'Alerta de Orden de Trabajo'
    };
    return titles[type] || 'Alerta';
  };

  // Funciones para vacaciones
  const getVacationTitle = (notificationType, vacation) => {
    switch(notificationType) {
      case 'nueva_solicitud':
        return 'Nueva solicitud de vacaciones';
      case 'solicitud_aprobada':
        return 'Solicitud de vacaciones aprobada';
      case 'solicitud_rechazada':
        return 'Solicitud de vacaciones rechazada';
      case 'vacaciones_proximamente':
        return 'Vacaciones próximas a empezar';
      default:
        return 'Notificación de vacaciones';
    }
  };

  const getVacationDescription = (vacation) => {
    const solicitante = vacation.solicitante ? 
      `${vacation.solicitante.nombre} ${vacation.solicitante.apellidos}` : 
      'Usuario';
    
    switch(vacation.notification_type) {
      case 'nueva_solicitud':
        return `${solicitante} ha solicitado vacaciones del ${vacation.fecha_inicio} al ${vacation.fecha_fin}`;
      case 'solicitud_aprobada':
        return `Tu solicitud de vacaciones del ${vacation.fecha_inicio} al ${vacation.fecha_fin} ha sido aprobada`;
      case 'solicitud_rechazada':
        return `Tu solicitud de vacaciones del ${vacation.fecha_inicio} al ${vacation.fecha_fin} ha sido rechazada`;
      case 'vacaciones_proximamente':
        return `Tus vacaciones empiezan pronto: ${vacation.fecha_inicio} al ${vacation.fecha_fin}`;
      default:
        return `Vacaciones del ${vacation.fecha_inicio} al ${vacation.fecha_fin}`;
    }
  };

  const getVacationSeverity = (notificationType) => {
    switch(notificationType) {
      case 'nueva_solicitud':
        return 'medium';
      case 'solicitud_rechazada':
        return 'high';
      case 'vacaciones_proximamente':
        return 'high';
      default:
        return 'low';
    }
  };

  const getSeverityIcon = (severity) => {
    switch(severity) {
      case 'high':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'medium':
        return <WarningOutlined style={{ color: '#faad14' }} />;
      default:
        return <InfoCircleOutlined style={{ color: '#1890ff' }} />;
    }
  };

  const getSeverityColor = (severity) => {
    switch(severity) {
      case 'high':
        return '#ff4d4f';
      case 'medium':
        return '#faad14';
      default:
        return '#1890ff';
    }
  };

  // Handlers
  const handleViewAlert = (alert) => {
    setVisible(false);

    if (alert.entity_type === 'machine' && alert.entity_id) {
      navigate(`/maquinas/${alert.entity_id}/detail`);
    } else if (alert.entity_type === 'inventory') {
      navigate('/inventario/bajo-stock');
    } else if (alert.entity_type === 'work_order' && alert.entity_id) {
      navigate('/ordenes');
    }
  };

  // Efectos
  useEffect(() => {
    if (currentUser) {
      // ✅ NUEVO: Resetear estado si cambia el usuario (nuevo login)
      const userId = currentUser.id;
      const currentStoredUserId = sessionStorage.getItem('currentUserId');
      
      if (currentStoredUserId !== String(userId)) {
        // Es un nuevo login, resetear notificaciones
        console.log('🔄 Nuevo login detectado, reseteando notificaciones');
        sessionStorage.setItem('currentUserId', String(userId));
        setHasShownInitialNotification(false);
        sessionStorage.removeItem(`hasShownInitialNotification_${userId}`);
      } else {
        // Cargar estado existente para este usuario
        const hasShown = sessionStorage.getItem(`hasShownInitialNotification_${userId}`) === 'true';
        const lastHash = sessionStorage.getItem(`lastNotificationHash_${userId}`) || '';
        setHasShownInitialNotification(hasShown);
        setLastNotificationHash(lastHash);
      }
      
      loadNotifications();
      const interval = setInterval(loadNotifications, 5 * 60 * 1000);
      
      return () => {
        clearInterval(interval);
        closeInitialNotification();
      };
    }
  }, [currentUser]);

  // ✅ NUEVO: Limpiar al cerrar el modal
  useEffect(() => {
    if (!visible) {
      closeInitialNotification();
    }
  }, [visible]);

  // ✅ NUEVO: Cleanup al desmontar
  useEffect(() => {
    return () => {
      closeInitialNotification();
    };
  }, []);

  // Renderizar item de notificación
  const renderNotificationItem = (notif) => (
    <Card
      key={notif.id}
      hoverable
      style={{
        marginBottom: 12,
        borderLeft: `4px solid ${getSeverityColor(notif.severity)}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
      }}
    >
      <Row gutter={16} align="middle">
        <Col span={2}>
          <Avatar
            size="large"
            icon={getNotificationIcon(notif.type)}
            style={{ backgroundColor: getNotificationColor(notif.type) }}
          />
        </Col>
        <Col span={16}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Space>
              {getSeverityIcon(notif.severity)}
              <Title level={5} style={{ margin: 0 }}>{notif.title}</Title>
            </Space>
            <Paragraph style={{ margin: 0 }} ellipsis={{ rows: 2 }}>
              {notif.description}
            </Paragraph>
            <Space wrap>
              {notif.metadata && Object.entries(notif.metadata).map(([key, value]) => (
                value && (
                  <Tag key={key} color="blue">
                    {key}: {value}
                  </Tag>
                )
              ))}
              <Text type="secondary" style={{ fontSize: '12px' }}>
                <ClockCircleOutlined /> {dayjs(notif.date).fromNow()}
              </Text>
            </Space>
          </Space>
        </Col>
        <Col span={6} style={{ textAlign: 'right' }}>
          <Space direction="vertical">
            {notif.actions?.map((action, index) => (
              <Button
                key={index}
                type={action.type || 'default'}
                size="small"
                onClick={action.action}
                icon={action.icon}
              >
                {action.label}
              </Button>
            ))}
          </Space>
        </Col>
      </Row>
    </Card>
  );

  const getNotificationIcon = (type) => {
    switch(type) {
      case 'maintenance':
        return <ToolOutlined />;
      case 'communication':
        return <MessageOutlined />;
      case 'alert':
        return <ExclamationCircleOutlined />;
      case 'vacation':
        return <CalendarOutlined />;
      default:
        return <BellOutlined />;
    }
  };

  const getNotificationColor = (type) => {
    switch(type) {
      case 'maintenance':
        return '#1890ff';
      case 'communication':
        return '#52c41a';
      case 'alert':
        return '#ff4d4f';
      case 'vacation':
        return '#722ed1';
      default:
        return '#666';
    }
  };

  const getTabBadgeCount = (tab) => {
    return notifications[tab]?.length || 0;
  };

  // Render principal
  return (
    <>
      <Button
        type="text"
        icon={<Badge count={unreadCount} size="small"><BellOutlined /></Badge>}
        onClick={() => setVisible(true)}
        style={{ fontSize: '16px' }}
      />



      <Modal
        title={
          <Space>
            <BellOutlined />
            <span>Centro de Notificaciones</span>
            <Badge count={unreadCount} />
          </Space>
        }
        open={visible}
        onCancel={() => setVisible(false)}
        footer={null}
        width={800}
        style={{ top: 20 }}
      >
        {unreadCount === 0 ? (
          <Empty description="No hay notificaciones pendientes" />
        ) : (
          <Tabs defaultActiveKey="all">
            <TabPane
              tab={
                <Badge count={unreadCount} offset={[10, 0]}>
                  <span>Todas</span>
                </Badge>
              }
              key="all"
            >
              <List
                loading={loading}
                dataSource={[
                  ...notifications.maintenance,
                  ...notifications.communications,
                  ...notifications.alerts,
                  ...notifications.vacations
                ].sort((a, b) => dayjs(b.date).valueOf() - dayjs(a.date).valueOf())}
                renderItem={renderNotificationItem}
              />
            </TabPane>

            <TabPane
              tab={
                <Badge count={getTabBadgeCount('maintenance')} offset={[10, 0]}>
                  <span><ToolOutlined /> Mantenimiento</span>
                </Badge>
              }
              key="maintenance"
            >
              <List
                loading={loading}
                dataSource={notifications.maintenance}
                renderItem={renderNotificationItem}
                locale={{ emptyText: 'No hay mantenimientos pendientes' }}
              />
            </TabPane>

            <TabPane
              tab={
                <Badge count={getTabBadgeCount('communications')} offset={[10, 0]}>
                  <span><MessageOutlined /> Comunicaciones</span>
                </Badge>
              }
              key="communications"
            >
              <List
                loading={loading}
                dataSource={notifications.communications}
                renderItem={renderNotificationItem}
                locale={{ emptyText: 'No hay comunicaciones nuevas' }}
              />
            </TabPane>

            <TabPane
              tab={
                <Badge count={getTabBadgeCount('alerts')} offset={[10, 0]}>
                  <span><ExclamationCircleOutlined /> Alertas</span>
                </Badge>
              }
              key="alerts"
            >
              <List
                loading={loading}
                dataSource={notifications.alerts}
                renderItem={renderNotificationItem}
                locale={{ emptyText: 'No hay alertas activas' }}
              />
            </TabPane>

            <TabPane
              tab={
                <Badge count={getTabBadgeCount('vacations')} offset={[10, 0]}>
                  <span><CalendarOutlined /> Vacaciones</span>
                </Badge>
              }
              key="vacations"
            >
              <List
                loading={loading}
                dataSource={notifications.vacations}
                renderItem={renderNotificationItem}
                locale={{ emptyText: 'No hay notificaciones de vacaciones' }}
              />
            </TabPane>
          </Tabs>
        )}
      </Modal>
    </>
  );
};

export default NotificationCenter;