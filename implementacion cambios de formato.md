
# 📋 Historial de Implementación - Órdenes de Cambio de Formato

## 🎯 Objetivo del Proyecto

Implementar funcionalidad específica para gestionar **Cambios de Formato** que permita:
- Crear una sola orden para cambios que afecten múltiples máquinas
- Documentar formatos origen/destino y máquinas afectadas
- Medir eficiencia de setup y tiempos de cambio
- Generar reportes específicos para análisis de mejora

## 📊 Contexto Inicial

**Problema identificado:**
- Los cambios de formato (frecuentes en planta y sección clasificación) requieren múltiples OTs
- No es práctico crear una OT por cada máquina tocada en un cambio global
- La solución actual de "máquina GENERAL" no es realista ni auditable

**Solución propuesta:**
- Nuevos tipos de trabajo específicos para cambios de formato
- Selección múltiple de máquinas en una sola orden
- Campos específicos para documentar formatos y tiempos

## 🚀 Plan de Implementación

### **Fase 1: Backend (Estimado: 1 semana)**
- [ ] Modificar modelo WorkOrder con nuevos campos
- [ ] Crear modelo Format para maestros de datos
- [ ] Nuevos endpoints para gestión de formatos
- [ ] Lógica para órdenes multi-máquina

### **Fase 2: Frontend (Estimado: 1 semana)**  
- [ ] Formulario específico para cambios de formato
- [ ] Selector múltiple de máquinas por sección
- [ ] Vista detallada de órdenes de formato
- [ ] Dashboard específico para métricas de setup

### **Fase 3: Reportes y Optimización (Estimado: 0.5 semanas)**
- [ ] Reportes de eficiencia de cambios
- [ ] Templates para cambios frecuentes
- [ ] Alertas y KPIs específicos

---

## 📅 Seguimiento de Progreso

### **[01 Jun 2025] - Inicio del Proyecto**

**Estado:** 🏁 **INICIADO**

**Actividades realizadas:**
- ✅ Análisis del problema y definición de solución
- ✅ Creación de plan de implementación
- ✅ Definición de estructura de datos necesaria

**Archivos recibidos:**
- ✅ `src/models/work_order.py` - Modelo base existente
- ✅ `src/models/base.py` - Configuración SQLAlchemy
- ✅ `src/routes.py` - Endpoints existentes
- ✅ Historial de implementación creado

### **[01 Jun 2025] - Fase 1 Backend Completada**

**Estado:** ✅ **BACKEND IMPLEMENTADO**

**Actividades realizadas:**
- ✅ Modificado modelo WorkOrder con nuevos campos de formato
- ✅ Creado modelo Format para maestros de datos
- ✅ Añadidos nuevos tipos de trabajo: "Cambio de Formato", "Setup de Línea", "Cambio Global de Planta"
- ✅ Implementados endpoints CRUD para gestión de formatos
- ✅ Creados endpoints específicos para órdenes de cambio de formato
- ✅ Implementados reportes de eficiencia y dashboard de formatos
- ✅ Creada migración de base de datos completa

**Archivos creados/modificados:**
- 📝 `work_order.py` - Mejorado con campos de cambio de formato
- 📝 `routes.py` - Nuevos endpoints para formatos (15 endpoints añadidos)
- 📝 `migration_format_changes.sql` - Migración de BD completa

**Funcionalidades implementadas:**
- 🔧 CRUD completo de formatos maestros
- 🔧 Creación de órdenes multi-máquina para cambios de formato
- 🔧 Actualización específica de órdenes de formato con métricas de setup
- 🔧 Reportes de eficiencia y análisis de cambios
- 🔧 Dashboard específico para métricas de cambios de formato
- 🔧 Audit trail completo para todas las operaciones

**Próximos pasos:**
1. Ejecutar migración de base de datos
2. Implementar frontend - formularios específicos
3. Crear componentes React para selección multi-máquina
4. Implementar dashboard frontend

---

## 💾 Estructura de Datos Planificada

### **Modelo WorkOrder (Modificaciones)**
```python
# Nuevos campos a añadir
format_change_type = Column(String(50))     # "Individual", "Línea", "Global"  
affected_machines = Column(JSON)            # Lista de IDs de máquinas afectadas
format_from = Column(String(100))           # Formato anterior
format_to = Column(String(100))             # Formato nuevo  
setup_duration = Column(Float)              # Duración real del setup
production_loss_hours = Column(Float)       # Horas de producción perdidas
```

### **Nuevo Modelo Format**
```python
class Format(Base):
    __tablename__ = "formats"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    estimated_setup_time = Column(Float)      # Tiempo estimado en horas
    machines_requiring_adjustment = Column(JSON)  # IDs de máquinas que requieren ajuste
    tools_materials_needed = Column(JSON)     # Herramientas/materiales necesarios
    created_at = Column(DateTime, default=datetime.utcnow)
```

### **Nuevos Tipos de Trabajo**
```python
WORK_TYPES = [
    "Preventivo",
    "Correctivo", 
    "Inspección",
    "Mejora",
    "Modificación",
    "Seguridad",
    "Cambio de Formato",        # NUEVO
    "Setup de Línea",           # NUEVO  
    "Cambio Global de Planta"   # NUEVO
]
```

---

## 🔧 Funcionalidades a Implementar

### **Backend**
- [ ] Migración de base de datos para nuevos campos
- [ ] Endpoints CRUD para modelo Format
- [ ] Endpoint para crear órdenes de formato con múltiples máquinas
- [ ] Lógica de validación para selección de máquinas
- [ ] Endpoints para reportes de eficiencia

### **Frontend**
- [ ] Componente FormularioFormatChange
- [ ] Selector múltiple de máquinas agrupado por sección  
- [ ] Vista detallada específica para órdenes de formato
- [ ] Dashboard con métricas de setup y cambios
- [ ] Reportes de eficiencia y tiempos

### **Reportes Específicos**
- [ ] Eficiencia de cambios por tipo de formato
- [ ] Análisis de tiempos de setup vs estimados
- [ ] Top formatos más frecuentes
- [ ] Costos de pérdida de producción por cambios

---

## 📝 Notas y Decisiones Técnicas

### **Decisiones de Diseño:**
- Usar campo JSON para `affected_machines` permite flexibilidad sin complicar el modelo
- Mantener compatibilidad con órdenes existentes (campos opcionales)
- Crear modelo Format separado para reutilización y maestros de datos

### **Consideraciones:**
- Las órdenes de formato pueden no tener `machine_id` individual (usar `affected_machines`)
- Necesario validar que al menos una máquina esté seleccionada en órdenes de formato
- Los reportes deben considerar tanto órdenes individuales como multi-máquina

---

## 🎯 Criterios de Éxito

1. **Funcionalidad:** Poder crear una orden que afecte múltiples máquinas
2. **Trazabilidad:** Saber exactamente qué máquinas se modificaron en cada cambio
3. **Métricas:** Medir eficiencia real vs estimada de cambios de formato
4. **Usabilidad:** Proceso más rápido que crear múltiples órdenes individuales
5. **Reportes:** Datos útiles para optimizar procesos de cambio

---

*Este archivo se actualizará conforme avance la implementación. Cada modificación incluirá fecha, cambios realizados y próximos pasos.*


// 1. Actualizar App.js - Añadir las nuevas rutas
// Añadir estas imports y rutas en tu App.js existente:

import FormatManager from './pages/FormatManager';
import FormatChangesList from './pages/FormatChangesList';
import FormatReports from './pages/FormatReports';

// Dentro de las rutas de tu App.js, añadir:
/*
<Route path="/formatos" element={<FormatManager />} />
<Route path="/cambios-formato" element={<FormatChangesList />} />
<Route path="/reportes-formato" element={<FormatReports />} />
*/

// 2. Actualizar AppLayout.js - Añadir elementos de menú
// En tu AppLayout.js, añadir estos elementos al menú:

const formatosMenuItems = [
  {
    key: 'formatos-submenu',
    icon: <SettingOutlined />,
    label: 'Cambios de Formato',
    children: [
      {
        key: '/formatos',
        icon: <DatabaseOutlined />,
        label: 'Gestión de Formatos',
      },
      {
        key: '/cambios-formato',
        icon: <ToolOutlined />,
        label: 'Órdenes de Cambio',
      },
      {
        key: '/reportes-formato',
        icon: <BarChartOutlined />,
        label: 'Reportes y Análisis',
      }
    ]
  }
];

// 3. Control de permisos por rol
// En tu función de generación de menú, añadir esta lógica:

const getMenuItems = (userRole) => {
  const baseItems = [
    // ... otros elementos del menú existentes
  ];

  // Solo mostrar funcionalidad de formatos para ciertos roles
  if (['Administrador', 'Jefe de Mantenimiento', 'Jefe de Sección'].includes(userRole)) {
    baseItems.push({
      key: 'formatos-submenu',
      icon: <SettingOutlined />,
      label: 'Cambios de Formato',
      children: [
        // Solo admin y jefe mantenimiento pueden gestionar formatos maestros
        ...((['Administrador', 'Jefe de Mantenimiento'].includes(userRole)) ? [{
          key: '/formatos',
          icon: <DatabaseOutlined />,
          label: 'Gestión de Formatos',
        }] : []),
        {
          key: '/cambios-formato',
          icon: <ToolOutlined />,
          label: 'Órdenes de Cambio',
        },
        {
          key: '/reportes-formato',
          icon: <BarChartOutlined />,
          label: 'Reportes y Análisis',
        }
      ]
    });
  }

  return baseItems;
};

// 4. Ejemplo completo de integración en AppLayout.js

import React, { useState } from 'react';
import { Layout, Menu } from 'antd';
import { 
  DashboardOutlined, ToolOutlined, DatabaseOutlined, BarChartOutlined,
  SettingOutlined, UserOutlined, ScheduleOutlined, FileTextOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const { Sider } = Layout;

const AppLayout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentUser } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  const getMenuItems = (userRole) => {
    const baseItems = [
      {
        key: '/dashboard',
        icon: <DashboardOutlined />,
        label: 'Dashboard',
      },
      {
        key: 'mantenimiento-submenu',
        icon: <ToolOutlined />,
        label: 'Mantenimiento',
        children: [
          {
            key: '/ordenes',
            label: 'Órdenes de Trabajo',
          },
          {
            key: '/backlog',
            label: 'Backlog',
          },
          {
            key: '/partes',
            label: 'Partes Diarios',
          }
        ]
      },
      {
        key: '/maquinas',
        icon: <SettingOutlined />,
        label: 'Máquinas',
      }
    ];

    // Añadir funcionalidad de cambios de formato
    if (['Administrador', 'Jefe de Mantenimiento', 'Jefe de Sección'].includes(userRole)) {
      baseItems.push({
        key: 'formatos-submenu',
        icon: <SettingOutlined />,
        label: 'Cambios de Formato',
        children: [
          // Solo admin y jefe mantenimiento pueden gestionar formatos maestros
          ...((['Administrador', 'Jefe de Mantenimiento'].includes(userRole)) ? [{
            key: '/formatos',
            icon: <DatabaseOutlined />,
            label: 'Gestión de Formatos',
          }] : []),
          {
            key: '/cambios-formato',
            icon: <ToolOutlined />,
            label: 'Órdenes de Cambio',
          },
          {
            key: '/reportes-formato',
            icon: <BarChartOutlined />,
            label: 'Reportes y Análisis',
          }
        ]
      });
    }

    // Añadir otros elementos según rol...
    if (['Administrador', 'Jefe de Mantenimiento', 'Jefe de Sección', 'Calidad', 'Contabilidad'].includes(userRole)) {
      baseItems.push({
        key: '/inventario',
        icon: <DatabaseOutlined />,
        label: 'Inventario',
      });
    }

    return baseItems;
  };

  const menuItems = getMenuItems(currentUser?.role);

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={setCollapsed}
        theme="dark"
      >
        <div style={{ 
          height: 64, 
          margin: 16, 
          background: 'rgba(255, 255, 255, 0.2)',
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold'
        }}>
          {collapsed ? 'GMAO' : 'GMAO Sistema'}
        </div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          mode="inline"
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        {children}
      </Layout>
    </Layout>
  );
};

export default AppLayout;

// 5. Ejemplo de integración en WorkOrderForm.js
// Para añadir los nuevos tipos de trabajo en el formulario existente:

// En WorkOrderForm.js, actualizar la lista de tipos permitidos:
const allowedWorkTypes = isSimplifiedForm 
  ? ['Preventivo', 'Correctivo', 'Inspección', 'Mejora', 'Modificación', 'Seguridad', 'Cambio de Formato', 'Setup de Línea', 'Cambio Global de Planta']
  : ['Preventivo', 'Correctivo', 'Inspección', 'Mejora', 'Modificación', 'Seguridad', 'Cambio de Formato', 'Setup de Línea', 'Cambio Global de Planta'];

// Y en el Select de work_type:
<Select disabled={preloadedData && !canEditOrder()}>
  {allowedWorkTypes.map(type => (
    <Option key={type} value={type}>
      {type === 'Cambio de Formato' && <ToolOutlined style={{ marginRight: 4 }} />}
      {type === 'Setup de Línea' && <ApartmentOutlined style={{ marginRight: 4 }} />}
      {type === 'Cambio Global de Planta' && <GlobalOutlined style={{ marginRight: 4 }} />}
      {type}
    </Option>
  ))}
</Select>

// 6. Dashboard - Añadir widget para cambios de formato
// En Dashboard.js, añadir una nueva card:

const FormatChangesWidget = () => {
  const [formatStats, setFormatStats] = useState(null);
  
  useEffect(() => {
    const loadFormatStats = async () => {
      try {
        const data = await fetchWithAuth('/dashboard/format-changes?days=30');
        setFormatStats(data);
      } catch (error) {
        console.error('Error loading format stats:', error);
      }
    };
    loadFormatStats();
  }, []);

  if (!formatStats) return null;

  return (
    <Card>
      <Statistic
        title="Cambios de Formato (30d)"
        value={formatStats.kpis?.total_changes || 0}
        prefix={<SettingOutlined />}
        valueStyle={{ color: '#1890ff' }}
      />
      <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
        Eficiencia: {formatStats.kpis?.average_efficiency?.toFixed(1) || 0}%
      </div>
      <Link to="/reportes-formato">
        <Button type="link" size="small" style={{ padding: 0 }}>
          Ver reportes
        </Button>
      </Link>
    </Card>
  );
};

// Luego añadir el widget en el dashboard:
// <Col xs={24} sm={12} md={6}>
//   <FormatChangesWidget />
// </Col>


📦 Componentes Creados
1. FormatManager.js - Gestión de Formatos Maestros

CRUD completo para formatos maestros
Solo accesible para Administradores y Jefes de Mantenimiento
Gestión de máquinas asociadas y herramientas necesarias
Activar/desactivar formatos

2. FormatChangeForm.js - Formulario para Órdenes de Cambio

Formulario especializado para crear órdenes de cambio de formato
Soporte para 3 tipos: Individual, Línea, Global
Selección inteligente de máquinas (una o múltiples)
Integración con formatos maestros
Cálculo automático de tiempos estimados

3. FormatChangesList.js - Lista de Órdenes de Cambio

Vista completa de todas las órdenes de cambio de formato
Filtros avanzados (estado, tipo, sección, fechas)
Métricas en tiempo real
Modal de detalles completo
Indicadores de eficiencia visuales

4. FormatReports.js - Dashboard y Reportes

KPIs específicos para cambios de formato
Gráficos de tendencias y distribución
Top de eficiencia
Análisis de cambios más frecuentes
Exportación a Excel

5. Actualizaciones de Navegación

Integración en el menú principal
Control de permisos por rol
Rutas para todos los componentes
Widget para el dashboard principal

🔧 Pasos para Implementar
1. Crear los archivos:
