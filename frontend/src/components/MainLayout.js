// src/components/MainLayout.js (Versión completa actualizada con acceso corregido a gamificación)
import React, { useState, useEffect } from 'react';
import { Layout, Button, Typography, Dropdown, Avatar, Menu, Drawer } from 'antd';
import { 
  MenuOutlined,
  ArrowLeftOutlined, 
  UserOutlined, 
  LogoutOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from './Sidebar';
import AlertsSidebar from './AlertsSidebar';
import '../styles/MainLayout.css';
import NotificationCenter from './NotificationCenter';
import LicenseManager from './LicenseManager';

const { Content, Header } = Layout;
const { Title } = Typography;

const MainLayout = ({ children }) => {
  // Estado para controlar el ancho de la ventana
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // ===================================================
  // ✅ DEFINICIÓN DE PERMISOS POR ROL CORREGIDA
  // ===================================================
  const rolePermissions = {
    'Administrador': ['all'], // Acceso total
    'Jefe de Mantenimiento': ['all'], // Acceso total
    'Jefe Sección': [
      'dashboard', 'info-planta', 'maquinas', 'ordenes', 'partes', 'inventario', 
      'productos', 'usuarios', 'calendario-turnos', 'calendario-vacaciones', 
      'backlog-mantenimiento', 'reporte-inventario', 'comparar-precios', 
      'mantenimiento', 'audit-trail', 'secciones', 'almacenes', 'proveedores',
      'gestion-patrones', 'gestion-codigos', 'documentos', 'scheduler-admin',
      'bajo-stock', 'gamification', 'formatos', 'cambios-formato', 'reportes-formato',
      'communications'
    ],
    'Mecánico': [
      // ✅ CORREGIDO: Mecánicos ahora SÍ pueden ver gamificación
      'dashboard', 'maquinas', 'ordenes', 'partes', 'calendario-turnos', 'calendario-vacaciones', 'gamification', 'cambios-formato', 'mantenimiento', 'communications'
    ],
    // ✅ NUEVOS ROLES CON PERMISOS ESPECÍFICOS INCLUYENDO GAMIFICACIÓN
    'Calidad': [
      'dashboard', 'maquinas', 'ordenes', 'partes', 'inventario', 'calendario-turnos', 'calendario-vacaciones',
      'reporte-inventario', 'comparar-precios', 'bajo-stock', 'gamification', 'cambios-formato', 'reportes-formato', 'communications'
    ],
    'Contabilidad': [
      'dashboard', 'maquinas', 'ordenes', 'partes', 'inventario', 'calendario-turnos', 'calendario-vacaciones',
      'reporte-inventario', 'comparar-precios', 'bajo-stock', 'gamification', 'reportes-formato', 'communications'
  ]};

  // Función para verificar permisos
  const hasPermission = (permission) => {
    if (!currentUser || !currentUser.role) return false;
    
    const userRole = typeof currentUser.role === 'string' 
      ? currentUser.role 
      : currentUser.role.nombre || currentUser.role;
    
    const permissions = rolePermissions[userRole] || [];
    
    return permissions.includes('all') || permissions.includes(permission);
  };
  
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

  // Función para manejar el cierre de sesión
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Controles para el drawer
  const showDrawer = () => {
    setDrawerVisible(true);
  };
  
  const closeDrawer = () => {
    setDrawerVisible(false);
  };

  // Menú de usuario mejorado
  const userMenu = (
    <Menu>
      <Menu.Item key="user-info" disabled style={{ 
        cursor: 'default',
        backgroundColor: '#f5f5f5',
        borderBottom: '1px solid #d9d9d9',
        marginBottom: '4px'
      }}>
        <div style={{ textAlign: 'center', padding: '4px 0' }}>
          <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
            {currentUser?.username || 'Usuario'}
          </div>
          <div style={{ fontSize: '12px', color: '#666', marginTop: '2px' }}>
            {currentUser?.role?.nombre || 
             (typeof currentUser?.role === 'string' ? currentUser.role : 'Sin rol asignado')}
          </div>
        </div>
      </Menu.Item>
      <Menu.Item 
        key="logout" 
        onClick={handleLogout}
        style={{ 
          backgroundColor: '#f6ffed',
          border: '1px solid #b7eb8f',
          borderRadius: '4px',
          margin: '4px',
          color: '#389e0d',
          fontWeight: '500'
        }}
        icon={<LogoutOutlined style={{ color: '#52c41a' }} />}
      >
        <span style={{ color: '#389e0d' }}>Cerrar Sesión</span>
      </Menu.Item>
    </Menu>
  );

  // ===================================================
  // ✅ TÍTULOS DE PÁGINA ACTUALIZADOS
  // ===================================================
  const getPageTitle = () => {
    const titles = {
      '/': 'Dashboard',
      '/info-planta': 'Información de Planta',
      '/mantenimiento': 'Mantenimiento',
      '/mantenimiento/preventivo': 'Mantenimiento Preventivo',
      '/maquinas': 'Gestión de Máquinas',
      '/maquinas/qr': 'Generador QR',
      '/maquinas/scan': 'Escáner QR',
      '/ordenes': 'Órdenes de Trabajo',
      '/secciones': 'Secciones y Líneas',
      '/inventario': 'Inventario',
      '/productos': 'Productos',
      '/inventario/bajo-stock': 'Productos Bajo Mínimos',
      '/documentos': 'Documentos',
      '/listas-tareas': 'Listas de Tareas Estándar',
      '/backlog-mantenimiento': 'Backlog de Mantenimiento',
      '/scheduler-admin': 'Administración del Scheduler',
      '/partes': 'Gestión de Partes',
      '/proveedores': 'Proveedores',
      '/comparar-precios': 'Comparar Precios',
      '/gestion-codigos': 'Gestión de Códigos',
      '/usuarios': 'Gestión de Usuarios',
      '/almacenes': 'Gestión de Almacenes',
      '/calendario-turnos': 'Calendario de Turnos',
      '/calendario-vacaciones': 'Calendario de Vacaciones',
      '/gestion-patrones': 'Gestión de Patrones de Turno',
      '/reporte-inventario': 'Reporte de Inventario',
      '/audit-trail': 'Registro de Auditoría',
      '/gamification': 'Gamificación', 
      '/gamification-admin': 'Administración Gamificación', 
      '/formatos': 'Gestión de Formatos',
      '/cambios-formato': 'Órdenes de Cambio de Formato', 
      '/reportes-formato': 'Reportes de Cambios de Formato'
    };
    
    // Comprobaciones para rutas dinámicas
    if (location.pathname.match(/^\/maquinas\/\d+\/detail/)) {
      return 'Detalle de Máquina';
    }
    if (location.pathname.match(/^\/maquinas\/\d+\/bom/)) {
      return 'BOM de Máquina';
    }
    if (location.pathname.match(/^\/maquinas\/\d+\/history/)) {
      return 'Historial de Máquina';
    }
    if (location.pathname.match(/^\/productos\/\d+/)) {
      return 'Detalle de Producto';
    }
    if (location.pathname.match(/^\/listas-tareas\/\d+\/pasos/)) {
      return 'Pasos de Lista de Tareas';
    }
    if (location.pathname.match(/^\/documentos\/.*\/\d+/)) {
      return 'Documentos Asociados';
    }
    
    return titles[location.pathname] || 'GMAO System';
  };


  return (
    <Layout style={{ 
      minHeight: '100vh', 
      width: '100%', 
      maxWidth: '100%',
      overflow: 'visible'
    }}>
      {/* En pantallas grandes, mostrar el sidebar normal */}
      {!isMobile && (
        <div style={{ 
          width: 200, 
          background: 'white', 
          height: '100vh', 
          position: 'fixed', 
          overflowY: 'auto', 
          zIndex: 10 
        }}>
          <Sidebar hasPermission={hasPermission} />
        </div>
      )}
      
      {/* En pantallas móviles, mostrar drawer para el sidebar */}
      {isMobile && (
        <Drawer
          placement="left"
          closable={true}
          onClose={closeDrawer}
          open={drawerVisible}
          bodyStyle={{ padding: 0 }}
          width={250}
        >
          <Sidebar hasPermission={hasPermission} />
        </Drawer>
      )}
      
      {/* Contenido principal con margen ajustado según tamaño */}
      <Layout style={{ 
        marginLeft: isMobile ? 0 : 200, 
        transition: 'margin-left 0.3s',
        width: isMobile ? '100vw' : 'auto',
        maxWidth: isMobile ? '100vw' : 'auto',
        overflow: 'hidden'
      }}>
        {/* Header adaptativo */}
        <Header style={{
          padding: isMobile ? '0 8px' : '0 24px',
          background: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: isMobile ? '48px' : '56px',
          boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
          position: 'sticky',
          top: 0,
          zIndex: 9,
          width: '100%'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center',
            maxWidth: isMobile ? 'calc(100% - 40px)' : 'auto'
          }}>
            {/* Botón hamburguesa en móvil */}
            {isMobile && (
              <Button 
                type="text" 
                icon={<MenuOutlined />} 
                onClick={showDrawer}
                style={{ marginRight: '4px', padding: '4px' }}
                size="small"
              />
            )}
            
            {/* Botón volver (solo si no estamos en dashboard) */}
            {location.pathname !== '/' && (
              <Button 
                icon={<ArrowLeftOutlined />} 
                onClick={() => navigate('/')}
                style={{ marginRight: isMobile ? '4px' : '16px' }}
                size="small"
              >
                {!isMobile && "Volver"}
              </Button>
            )}
            
            {/* Título con tamaño adaptativo */}
            <Title 
              level={5} 
              style={{ 
                margin: 0, 
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                fontSize: isMobile ? '14px' : '18px'
              }}
            >
              {getPageTitle()}
            </Title>
          </div>
          
          {/* Perfil usuario mejorado */}
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <LicenseManager isMobile={isMobile} />
            {!isMobile && <AlertsSidebar />}
            <Dropdown overlay={userMenu} trigger={['click']} placement="bottomRight">
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                cursor: 'pointer',
                padding: '4px 8px',
                borderRadius: '6px',
                backgroundColor: '#f0f2f5',
                border: '1px solid #d9d9d9',
                transition: 'all 0.3s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#e6f7ff';
                e.currentTarget.style.borderColor = '#91d5ff';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#f0f2f5';
                e.currentTarget.style.borderColor = '#d9d9d9';
              }}>
                <Avatar 
                  icon={<UserOutlined />} 
                  size="small" 
                  className="user-avatar-green"
                  style={{ 
                    backgroundColor: '#52c41a !important',
                    marginRight: !isMobile ? '8px' : '0'
                  }} 
                />
                {!isMobile && (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                    <span style={{ fontSize: '12px', fontWeight: '500', color: '#262626' }}>
                      {currentUser?.username || 'Usuario'}
                    </span>
                    <span style={{ fontSize: '10px', color: '#8c8c8c' }}>
                      Cerrar sesión ↓
                    </span>
                  </div>
                )}
              </div>
            </Dropdown>
          </div>
        </Header>
        
        {/* Contenido principal con padding adaptativo */}
        <Content style={{
          padding: isMobile ? '5px' : '24px',
          background: '#f0f2f5',
          minHeight: 'calc(100vh - 48px)',
          width: '100%',
          maxWidth: '100%',
          overflow: 'visible'
        }}>
          {children}
        </Content>
        {/* Sistema de notificaciones prominente */}
      <NotificationCenter />
      </Layout>
    </Layout>
  );
};

export default MainLayout;