// src/components/Sidebar.js (ACTUALIZADO con bienvenida al usuario)
import React from 'react';
import { Menu } from 'antd';
import { Link } from 'react-router-dom';
import {
  DashboardOutlined,
  ApartmentOutlined,
  SettingOutlined,
  ToolOutlined,
  FileTextOutlined,
  InboxOutlined,
  UserOutlined,
  CalendarOutlined,
  FileExcelOutlined,
  QrcodeOutlined,
  ScanOutlined,
  FileSearchOutlined,
  UnorderedListOutlined,
  ProfileOutlined,
  HistoryOutlined,
  ClockCircleOutlined,
  ShoppingOutlined,
  DollarOutlined,
  WarningOutlined,
  AuditOutlined,
  TrophyOutlined,
  ScheduleOutlined,
  TeamOutlined,
  DatabaseOutlined,
  BarChartOutlined,
  RobotOutlined,
  MessageOutlined,
  LineChartOutlined,
  AlertOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { SubMenu } = Menu;

const Sidebar = ({ hasPermission }) => {
  const { currentUser } = useAuth();

  // Función auxiliar para filtrar items del menú que tienen permisos
  const filterMenuItems = (items) => {
    return items
      .filter(item => {
        // Si el item tiene la propiedad 'show', evaluarla
        if (typeof item.show === 'boolean') {
          return item.show;
        }
        // Si el item tiene 'permission', verificar el permiso
        if (item.permission) {
          return hasPermission(item.permission);
        }
        // Si es un submenú, verificar si tiene hijos válidos
        if (item.children) {
          const validChildren = filterMenuItems(item.children);
          return validChildren.length > 0;
        }
        return true;
      })
      .map(item => {
        // Si tiene hijos, filtrarlos también
        if (item.children) {
          return {
            ...item,
            children: filterMenuItems(item.children)
          };
        }
        return item;
      });
  };

  // ===================================================
  // ✅ FUNCIÓN ESPECIAL PARA PERMISOS DE IA
  // ===================================================
  const canAccessAI = () => {
    // TODOS los usuarios pueden ver funciones básicas de IA
    return currentUser && currentUser.role;
  };

  const canAccessAIAdmin = () => {
    // Solo administradores y jefes pueden ver configuración avanzada
    if (!currentUser || !currentUser.role) return false;
    
    const userRole = typeof currentUser.role === 'string' 
      ? currentUser.role 
      : currentUser.role.nombre || currentUser.role;
    
    return userRole === 'Administrador' || userRole === 'Jefe de Mantenimiento';
  };

  // ===================================================
  // ✅ FUNCIÓN PARA OBTENER EL NOMBRE DEL USUARIO
  // ===================================================
  const getUserDisplayName = () => {
    if (!currentUser) return 'Usuario';
    
    // Si tiene nombre completo
    if (currentUser.nombre) {
      const firstName = currentUser.nombre.split(' ')[0]; // Primer nombre
      return firstName;
    }
    
    // Si solo tiene username
    if (currentUser.username) {
      return currentUser.username;
    }
    
    return 'Usuario';
  };

  const getUserRole = () => {
    if (!currentUser || !currentUser.role) return '';
    
    const userRole = typeof currentUser.role === 'string' 
      ? currentUser.role 
      : currentUser.role.nombre || currentUser.role;
    
    return userRole;
  };

  // ===================================================
  // ✅ ESTRUCTURA DE MENÚ ACTUALIZADA CON IA
  // ===================================================
  const menuItems = [
    {
      key: '1',
      icon: <DashboardOutlined />,
      label: <Link to="/">Dashboard</Link>,
      permission: 'dashboard'
    },
    {
      key: '2',
      icon: <ApartmentOutlined />,
      label: <Link to="/info-planta">Info Planta</Link>,
      permission: 'info-planta'
    },
    // ✅ NUEVA SECCIÓN DE COMUNICACIONES
    {
      key: 'communications-group',
      icon: <MessageOutlined />,
      label: 'Comunicaciones',
      show: currentUser && currentUser.role, // Todos los usuarios pueden comunicarse
      children: [
        {
          key: 'my-communications',
          icon: <MessageOutlined />,
          label: <Link to="/communications">Mis Comunicaciones</Link>,
          show: currentUser && currentUser.role
        },
        {
          key: 'communication-admin',
          icon: <AuditOutlined />,
          label: <Link to="/communication-admin">Admin Comunicaciones</Link>,
          show: canAccessAIAdmin() // Solo admins y jefes
        }
      ]
    },
    // ✅ ===============================================
    // ✅ NUEVA SECCIÓN DE IA - POSICIÓN PROMINENTE
    // ✅ ===============================================
    {
      key: 'ai-group',
      icon: <RobotOutlined />,
      label: 'Inteligencia Artificial',
      show: canAccessAI(),
      children: [
        {
          key: 'ai-dashboard',
          icon: <LineChartOutlined />,
          label: <Link to="/ai-dashboard">Dashboard IA</Link>,
          show: canAccessAI()
        },
        {
          key: 'ai-chat',
          icon: <MessageOutlined />,
          label: <Link to="/ai-chat">Chat IA</Link>,
          show: canAccessAI()
        },
        {
          key: 'ai-predictions',
          icon: <AlertOutlined />,
          label: <Link to="/ai-predictions">Predicciones</Link>,
          show: canAccessAI()
        },
        {
          key: 'ai-admin',
          icon: <SettingOutlined />,
          label: <Link to="/ai-admin">Configuración IA</Link>,
          show: canAccessAIAdmin()
        }
      ]
    },
    // ✅ ===============================================
    // ✅ FIN SECCIÓN IA
    // ✅ ===============================================
    {
      key: 'maquinas-group',
      icon: <SettingOutlined />,
      label: 'Máquinas',
      permission: 'maquinas',
      children: [
        {
          key: '3',
          icon: <SettingOutlined />,
          label: <Link to="/maquinas">Gestión Máquinas</Link>,
          permission: 'maquinas'
        },
        {
          key: 'qr-group',
          icon: <QrcodeOutlined />,
          label: 'Códigos QR',
          permission: 'maquinas',
          children: [
            {
              key: 'qr-generate',
              icon: <QrcodeOutlined />,
              label: <Link to="/maquinas/qr">Generar QR</Link>,
              permission: 'maquinas'
            },
            {
              key: 'qr-scan',
              icon: <ScanOutlined />,
              label: <Link to="/maquinas/scan">Escanear QR</Link>,
              permission: 'maquinas'
            }
          ]
        }
      ]
    },
    {
      key: 'mantenimiento-group',
      icon: <ToolOutlined />,
      label: 'Mantenimiento',
      permission: 'mantenimiento',
      children: [
        {
          key: '4',
          icon: <HistoryOutlined />,
          label: <Link to="/mantenimiento">Historial</Link>,
          permission: 'mantenimiento'
        },
        {
          key: 'plan-anual',
          icon: <CalendarOutlined />,
          label: <Link to="/plan-anual">Plan Anual</Link>,
          permission: 'mantenimiento'
        },
        {
          key: 'mantenimiento-legal', // Nueva clave
          icon: <AuditOutlined />, // Icono de auditoría
          label: <Link to="/mantenimiento/legal">Legal</Link>,
          permission: 'mantenimiento' // O un permiso específico
        },
        {
          key: '5',
          icon: <ClockCircleOutlined />,
          label: <Link to="/mantenimiento/preventivo">Preventivo</Link>,
          permission: 'mantenimiento'
        },
        {
          key: 'task-lists',
          icon: <UnorderedListOutlined />,
          label: <Link to="/listas-tareas">Listas de Tareas</Link>,
          permission: 'mantenimiento'
        },
        {
          key: 'maintenance-backlog',
          icon: <ProfileOutlined />,
          label: <Link to="/backlog-mantenimiento">Backlog</Link>,
          permission: 'backlog-mantenimiento'
        }
      ]
    },
    {
      key: 'formatos-group',
      icon: <SettingOutlined />,
      label: 'Cambios de Formato',
      permission: 'cambios-formato',
      children: [
        {
          key: 'formatos-maestros',
          icon: <DatabaseOutlined />,
          label: <Link to="/formatos">Gestión de Formatos</Link>,
          permission: 'formatos'
        },
        {
          key: 'ordenes-formato',
          icon: <ToolOutlined />,
          label: <Link to="/cambios-formato">Órdenes de Cambio</Link>,
          permission: 'cambios-formato'
        },
        {
          key: 'reportes-formato',
          icon: <BarChartOutlined />,
          label: <Link to="/reportes-formato">Reportes y Análisis</Link>,
          permission: 'reportes-formato'
        }
      ]
    },
    {
      key: '6',
      icon: <FileTextOutlined />,
      label: <Link to="/ordenes">Órdenes de Trabajo</Link>,
      permission: 'ordenes'
    },
    {
      key: '7',
      icon: <FileTextOutlined />,
      label: <Link to="/partes">Partes</Link>,
      permission: 'partes'
    },
    {
      key: 'inventario-group',
      icon: <InboxOutlined />,
      label: 'Inventario',
      permission: 'inventario',
      children: [
        {
          key: '8',
          icon: <InboxOutlined />,
          label: <Link to="/inventario">Consultar Stock</Link>,
          permission: 'inventario'
        },
        {
          key: 'productos',
          icon: <ShoppingOutlined />,
          label: <Link to="/productos">Gestión Productos</Link>,
          permission: 'productos'
        },
        {
          key: 'inventory-report',
          icon: <FileExcelOutlined />,
          label: <Link to="/reporte-inventario">Reporte Inventario</Link>,
          permission: 'reporte-inventario'
        },
        {
          key: 'low-stock',
          icon: <WarningOutlined />,
          label: <Link to="/inventario/bajo-stock">Stock Bajo</Link>,
          permission: 'bajo-stock'
        },
        {
          key: 'price-compare',
          icon: <DollarOutlined />,
          label: <Link to="/comparar-precios">Comparar Precios</Link>,
          permission: 'comparar-precios'
        }
      ]
    },
    {
      key: 'administracion-group',
      icon: <UserOutlined />,
      label: 'Administración',
      permission: 'usuarios',
      children: [
        {
          key: '9',
          icon: <TeamOutlined />,
          label: <Link to="/usuarios">Usuarios</Link>,
          permission: 'usuarios'
        },
        {
          key: '10',
          icon: <ApartmentOutlined />,
          label: <Link to="/secciones">Secciones</Link>,
          permission: 'secciones'
        },
        {
          key: '11',
          icon: <InboxOutlined />,
          label: <Link to="/almacenes">Almacenes</Link>,
          permission: 'almacenes'
        },
        {
          key: 'suppliers',
          icon: <ShoppingOutlined />,
          label: <Link to="/proveedores">Proveedores</Link>,
          permission: 'proveedores'
        },
        {
          key: 'shift-patterns',
          icon: <ScheduleOutlined />,
          label: <Link to="/gestion-patrones">Patrones Turno</Link>,
          permission: 'gestion-patrones'
        },
        {
          key: 'failure-codes',
          icon: <FileTextOutlined />,
          label: <Link to="/gestion-codigos">Códigos FCR</Link>,
          permission: 'gestion-codigos'
        }
      ]
    },
    {
      key: 'calendario-group',
      icon: <CalendarOutlined />,
      label: 'Calendarios',
      permission: 'calendario-turnos',
      children: [
        {
          key: 'calendario-turnos',
          icon: <CalendarOutlined />,
          label: <Link to="/calendario-turnos">Turnos</Link>,
          permission: 'calendario-turnos'
        },
        {
          key: 'calendario-vacaciones',
          icon: <CalendarOutlined />,
          label: <Link to="/calendario-vacaciones">Vacaciones</Link>,
          permission: 'calendario-vacaciones'
        }
      ]
    },
    {
      key: 'sistema-group',
      icon: <SettingOutlined />,
      label: 'Sistema',
      permission: 'documentos',
      children: [
        {
          key: 'documentos',
          icon: <FileSearchOutlined />,
          label: <Link to="/documentos">Documentos</Link>,
          permission: 'documentos'
        },
        {
          key: 'audit-trail',
          icon: <AuditOutlined />,
          label: <Link to="/audit-trail">Registro Auditoría</Link>,
          permission: 'audit-trail'
        },
        {
          key: 'scheduler-admin',
          icon: <ScheduleOutlined />,
          label: <Link to="/scheduler-admin">Tareas Automáticas</Link>,
          permission: 'scheduler-admin'
        }
      ]
    },
    // ✅ GAMIFICACIÓN SEPARADA (mantener como estaba)
    {
      key: 'gamification-main',
      icon: <TrophyOutlined />,
      label: <Link to="/gamification">Gamificación</Link>,
      show: currentUser && currentUser.role // Todos los usuarios pueden ver
    },
    {
      key: 'gamification-admin',
      icon: <TrophyOutlined />,
      label: <Link to="/gamification-admin">Admin Gamificación</Link>,
      show: canAccessAIAdmin() // Solo admins
    }
  ];

  // Filtrar elementos del menú según permisos
  const visibleMenuItems = filterMenuItems(menuItems);

  // ===================================================
  // ✅ RENDERIZADO RECURSIVO DEL MENÚ
  // ===================================================
  const renderMenuItems = (items) => {
    return items.map(item => {
      if (item.children && item.children.length > 0) {
        return (
          <SubMenu 
            key={item.key} 
            icon={item.icon} 
            title={item.label?.props?.children || item.label}
          >
            {renderMenuItems(item.children)}
          </SubMenu>
        );
      }
      return (
        <Menu.Item key={item.key} icon={item.icon}>
          {item.label}
        </Menu.Item>
      );
    });
  };


  return (
    <div style={{ height: '100vh', overflowY: 'auto' }}>
      {/* ===================================================
          ✅ LOGO Y BIENVENIDA AL USUARIO (MEJORADO)
          ================================================= */}
      <div style={{
        borderBottom: '1px solid #f0f0f0',
        background: '#001529',
        paddingBottom: '12px'
      }}>
        {/* Logo del sistema */}
        <div style={{
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          paddingTop: '8px'
        }}>
          <div style={{ 
            color: 'white', 
            fontSize: '16px', 
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center'
          }}>
            <RobotOutlined style={{ marginRight: 8, color: '#52c41a' }} />
            GMAO System
          </div>
        </div>

        {/* ✅ NUEVA SECCIÓN: Bienvenida al usuario */}
        {currentUser && (
          <div style={{
            textAlign: 'center',
            paddingTop: '8px',
            paddingLeft: '12px',
            paddingRight: '12px'
          }}>
            {/* Mensaje de bienvenida */}
            <div style={{
              color: '#52c41a',
              fontSize: '12px',
              fontWeight: '500',
              marginBottom: '4px'
            }}>
              ¡Bienvenido!
            </div>
            
            {/* Nombre del usuario */}
            <div style={{
              color: 'white',
              fontSize: '14px',
              fontWeight: 'bold',
              marginBottom: '2px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {getUserDisplayName()}
            </div>
            
            {/* Rol del usuario */}
            <div style={{
              color: '#8c8c8c',
              fontSize: '10px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {getUserRole()}
            </div>
          </div>
        )}
      </div>

      {/* Menú principal */}
      <Menu
        mode="inline"
        defaultSelectedKeys={['1']}
        defaultOpenKeys={['ai-group', 'maquinas-group', 'inventario-group']} // ✅ Abrir IA por defecto
        style={{ height: 'calc(100vh - 120px)', borderRight: 0 }} // ✅ Ajustado para dar espacio a la bienvenida
      >
        {renderMenuItems(visibleMenuItems)}
      </Menu>

      
      
    </div>
  );
};

export default Sidebar;