// src/pages/MantenimientoLegal.js - VERSIÓN ULTRA PROFESIONAL ISO 9001

import React, { useState, useEffect } from 'react';
import { 
  Table, Button, Modal, Card, Typography, Space, Tooltip, message, Popconfirm,
  Form, Input, Select, DatePicker, InputNumber, Divider, Row, Col, Alert,
  Tag, Badge, Upload, List, Avatar, Statistic, Collapse, Progress, Timeline,
  Descriptions, Steps, notification, Dropdown, Menu
} from 'antd';
import { 
  PlusOutlined, FilePdfOutlined, EditOutlined, DeleteOutlined, ExclamationCircleOutlined,
  CalendarOutlined, SafetyCertificateOutlined, FileTextOutlined, 
  WarningOutlined, CheckCircleOutlined, ClockCircleOutlined,
  UploadOutlined, LinkOutlined, EyeOutlined, DownloadOutlined, InboxOutlined,
  HistoryOutlined, PrinterOutlined, FileExcelOutlined, BellOutlined,
  CertificateOutlined, AuditOutlined, EnvironmentOutlined, ToolOutlined,
  ThunderboltOutlined, FireOutlined, CarOutlined, ExperimentOutlined,
  MoreOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import DocumentAttachmentManager from '../components/DocumentAttachmentManager';
import dayjs from 'dayjs';
import { ExportButton } from '../components/ExportButton';
import { useAuth } from '../contexts/AuthContext';
import { LockOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;
const { Panel } = Collapse;
const { Step } = Steps;

// ========================================
// CONFIGURACIÓN PROFESIONAL PARA FÁBRICA DE AZULEJOS
// ========================================

const CATEGORIAS_MANTENIMIENTO_LEGAL = {
  "Instalaciones Eléctricas": {
    icon: <ThunderboltOutlined />,
    color: "gold",
    descripcion: "REBT - Reglamento Electrotécnico Baja Tensión",
    normativa: "RD 842/2002",
    organismos: ["OCA", "Empresa Instaladora Autorizada"],
    criticidad: "ALTA"
  },
  "Equipos a Presión": {
    icon: <ExperimentOutlined />,
    color: "volcano",
    descripcion: "REP - Reglamento Equipos a Presión",
    normativa: "RD 2060/2008",
    organismos: ["OCA", "Empresa Instaladora"],
    criticidad: "CRÍTICA"
  },
  "Protección Contraincendios": {
    icon: <FireOutlined />,
    color: "red",
    descripcion: "RIPCI - Reglamento Instalaciones Protección Contraincendios",
    normativa: "RD 513/2017",
    organismos: ["Empresa Mantenedora Autorizada"],
    criticidad: "CRÍTICA"
  },
  "Productos Químicos": {
    icon: <ExperimentOutlined />,
    color: "purple",
    descripcion: "APQ - Almacenamiento Productos Químicos",
    normativa: "RD 656/2017",
    organismos: ["OCA", "Técnico Competente"],
    criticidad: "ALTA"
  },
  "Equipos de Trabajo": {
    icon: <CarOutlined />,
    color: "blue",
    descripcion: "Carretillas, Puentes Grúa, Equipos Elevadores",
    normativa: "RD 1215/1997",
    organismos: ["Empresa Especializada", "OCA"],
    criticidad: "ALTA"
  },
  "Medio Ambiente": {
    icon: <EnvironmentOutlined />,
    color: "green",
    descripcion: "Emisiones, Residuos, Vertidos",
    normativa: "Ley 7/2022",
    organismos: ["Laboratorio Acreditado ENAC"],
    criticidad: "MEDIA"
  },
  "Calibración y Metrología": {
    icon: <AuditOutlined />,
    color: "cyan",
    descripcion: "Equipos de Medida y Ensayo",
    normativa: "ISO/IEC 17025",
    organismos: ["Laboratorio ENAC"],
    criticidad: "MEDIA"
  }
};

const PLANTILLAS_PREDEFINIDAS = {
  // INSTALACIONES ELÉCTRICAS

  "inspeccion_electrica_baja": {
    categoria: "Instalaciones Eléctricas",
    titulo: "Inspección Periódica Instalación Eléctrica BT",
    descripcion: "Inspección Trienal obligatoria para instalaciones industriales >100kW según REBT",
    frecuencia: "Trienal",
    organismos: ["OCA"],
    equipos_tipicos: ["Cuadros eléctricos", "Transformadores", "Grupos electrógenos", "SAI"],
    documentos_requeridos: ["Certificado OCA", "Memoria técnica", "Esquemas unifilares"],
    nivel_criticidad: "ALTA"
  },
  "inspeccion_electrica_alta": {
    categoria: "Instalaciones Eléctricas",
    titulo: "Inspección Periódica Instalación Eléctrica AT - Centro Transformación",
    descripcion: "Inspección Trienal obligatoria para Centros de Transformación según RD 337/2014",
    frecuencia: "Trienal",
    organismos: ["OCA"],
    equipos_tipicos: ["Centro de Transformación", "Transformadores AT/BT", "Celdas AT", "Equipos protección"],
    documentos_requeridos: ["Certificado OCA", "Informe técnico", "Acta inspección", "Esquemas unifilares AT"],
    nivel_criticidad: "CRÍTICA"
  },
  "revision_electrica_anual": {
    categoria: "Instalaciones Eléctricas", 
    titulo: "Revisión Anual Instalación Eléctrica",
    descripcion: "Termografías, medidas de aislamiento, revisión de protecciones",
    frecuencia: "Anual",
    organismos: ["Empresa Instaladora Autorizada"],
    equipos_tipicos: ["Cuadros eléctricos", "Motores", "Luminarias"],
    documentos_requeridos: ["Informe termográfico", "Medidas eléctricas", "Lista verificación"],
    nivel_criticidad: "MEDIA"
  },
  
  // EQUIPOS A PRESIÓN
  "inspeccion_compresores_nivel_b": {
    categoria: "Equipos a Presión",
    titulo: "Inspección Nivel B - Compresores",
    descripcion: "Inspección periódica OCA cada 8 años según REP",
    frecuencia: "Cada 8 años",
    organismos: ["OCA"],
    equipos_tipicos: ["Compresores de aire", "Calderines", "Depósitos presión"],
    documentos_requeridos: ["Certificado OCA", "Libro registro", "Placa identificación"],
    nivel_criticidad: "CRÍTICA"
  },
  "inspeccion_compresores_nivel_a": {
    categoria: "Equipos a Presión",
    titulo: "Inspección Nivel A - Compresores",
    descripcion: "Inspección en servicio cada 4 años",
    frecuencia: "Cada 4 años",
    organismos: ["Empresa Instaladora"],
    equipos_tipicos: ["Compresores de aire", "Calderines"],
    documentos_requeridos: ["Acta inspección", "Medidas presión", "Estado válvulas"],
    nivel_criticidad: "ALTA"
  },

  // PROTECCIÓN CONTRAINCENDIOS
  "mantenimiento_extintores": {
    categoria: "Protección Contraincendios",
    titulo: "Mantenimiento Extintores",
    descripcion: "Revisión anual y retimbrado quinquenal según RIPCI",
    frecuencia: "Anual",
    organismos: ["Empresa Mantenedora Autorizada"],
    equipos_tipicos: ["Extintores polvo", "Extintores CO2", "Extintores espuma"],
    documentos_requeridos: ["Contrato mantenimiento", "Actas revisión", "Etiquetas identificación"],
    nivel_criticidad: "CRÍTICA"
  },
  "revision_bies": {
    categoria: "Protección Contraincendios",
    titulo: "Revisión BIEs (Bocas Incendio Equipadas)",
    descripcion: "Mantenimiento trimestral y anual según RIPCI",
    frecuencia: "Trimestral",
    organismos: ["Empresa Mantenedora Autorizada"],
    equipos_tipicos: ["BIEs 25mm", "BIEs 45mm", "Mangueras", "Lanzas"],
    documentos_requeridos: ["Registro mantenimiento", "Pruebas presión", "Estado mangueras"],
    nivel_criticidad: "CRÍTICA"
  },

  // PRODUCTOS QUÍMICOS
  "inspeccion_apq": {
    categoria: "Productos Químicos",
    titulo: "Inspección APQ - Almacenamiento Productos Químicos",
    descripcion: "Inspección periódica instalaciones almacenamiento según APQ",
    frecuencia: "Quinquenal",
    organismos: ["OCA"],
    equipos_tipicos: ["Depósitos esmaltes", "Cubetos retención", "Sistemas ventilación"],
    documentos_requeridos: ["Certificado OCA", "Pruebas estanqueidad", "Plan emergencia"],
    nivel_criticidad: "ALTA"
  },

  // EQUIPOS DE TRABAJO
  "inspeccion_carretillas": {
    categoria: "Equipos de Trabajo",
    titulo: "Inspección Anual Carretillas Elevadoras",
    descripcion: "Revisión obligatoria anual según RD 1215/1997",
    frecuencia: "Anual",
    organismos: ["Empresa Especializada"],
    equipos_tipicos: ["Carretillas eléctricas", "Carretillas diésel", "Transpaletas"],
    documentos_requeridos: ["Certificado inspección", "Libro mantenimiento", "Manual instrucciones"],
    nivel_criticidad: "ALTA"
  },
  "inspeccion_puentes_grua": {
    categoria: "Equipos de Trabajo",
    titulo: "Inspección Puentes Grúa",
    descripcion: "Inspección anual equipos elevadores según RD 1215/1997",
    frecuencia: "Anual",
    organismos: ["OCA", "Empresa Especializada"],
    equipos_tipicos: ["Puentes grúa", "Polipastos", "Cables elevación"],
    documentos_requeridos: ["Certificado inspección", "Pruebas carga", "Estado cables"],
    nivel_criticidad: "CRÍTICA"
  },

  // CALIBRACIÓN
  "calibracion_bascula": {
    categoria: "Calibración y Metrología",
    titulo: "Calibración Básculas Industriales",
    descripcion: "Calibración anual por laboratorio ENAC",
    frecuencia: "Anual",
    organismos: ["Laboratorio ENAC"],
    equipos_tipicos: ["Básculas camión", "Básculas proceso", "Dinamómetros"],
    documentos_requeridos: ["Certificado calibración", "Trazabilidad ENAC", "Incertidumbres"],
    nivel_criticidad: "MEDIA"
  },
  "calibracion_termometros": {
    categoria: "Calibración y Metrología",
    titulo: "Calibración Termómetros Hornos",
    descripción: "Calibración anual equipos temperatura hornos cerámicos",
    frecuencia: "Anual",
    organismos: ["Laboratorio ENAC"],
    equipos_tipicos: ["Termómetros hornos", "Pirómetros", "Termopares"],
    documentos_requeridos: ["Certificado calibración", "Curvas temperatura", "Trazabilidad"],
    nivel_criticidad: "ALTA"
  }
};

const ORGANISMOS_CERTIFICADORES = [
  { value: "APPLUS+", label: "APPLUS+ (OCA)", tipo: "OCA", especialidades: ["Eléctrico", "Presión", "APQ"] },
  { value: "SGS", label: "SGS (OCA)", tipo: "OCA", especialidades: ["Todas"] },
  { value: "TÜV SÜD", label: "TÜV SÜD (OCA)", tipo: "OCA", especialidades: ["Eléctrico", "Presión"] },
  { value: "Bureau Veritas", label: "Bureau Veritas (OCA)", tipo: "OCA", especialidades: ["Todas"] },
  { value: "ECA", label: "ECA (OCA)", tipo: "OCA", especialidades: ["Eléctrico", "Presión"] },
  { value: "AENOR", label: "AENOR", tipo: "Certificación", especialidades: ["ISO", "Calidad"] },
  { value: "Laboratorio ENAC", label: "Laboratorio Acreditado ENAC", tipo: "Calibración", especialidades: ["Metrología"] },
  { value: "Empresa Autorizada", label: "Empresa Mantenedora Autorizada", tipo: "Mantenimiento", especialidades: ["Contraincendios"] }
];

const FRECUENCIAS_LEGALES = [
  { value: "Trimestral", label: "Trimestral", meses: 3, descripcion: "Cada 3 meses" },
  { value: "Semestral", label: "Semestral", meses: 6, descripcion: "Cada 6 meses" },
  { value: "Anual", label: "Anual", meses: 12, descripcion: "Cada año" },
  { value: "Bianual", label: "Bianual", meses: 24, descripcion: "Cada 2 años" },
  { value: "Trienal", label: "Trienal", meses: 36, descripcion: "Cada 3 años" }, 
  { value: "Cada 4 años", label: "Cada 4 años", meses: 48, descripcion: "Cada 4 años" },
  { value: "Quinquenal", label: "Quinquenal", meses: 60, descripcion: "Cada 5 años" },
  { value: "Cada 8 años", label: "Cada 8 años", meses: 96, descripcion: "Cada 8 años" },
  { value: "Cada 16 años", label: "Cada 16 años", meses: 192, descripcion: "Cada 16 años" }
];

const MantenimientoLegal = () => {
  // Estados principales
  const { currentUser } = useAuth();
  const isMechanic = currentUser?.role === 'Mecánico';
  const canManageOrEdit = currentUser?.role === 'Administrador' || 
                          currentUser?.role === 'Jefe de Mantenimiento' || 
                          currentUser?.role === 'Calidad' || 
                          currentUser?.role === 'Contabilidad';
  const [legalMaintenances, setLegalMaintenances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Estados para modales
  const [isCreateModalVisible, setIsCreateModalVisible] = useState(false);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [isDocModalVisible, setIsDocModalVisible] = useState(false);
  const [isDetailModalVisible, setIsDetailModalVisible] = useState(false);
  const [selectedMaintenance, setSelectedMaintenance] = useState(null);

  // Estados para formularios
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();
  const [machines, setMachines] = useState([]);
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);

  // Estados para plantillas
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [showTemplates, setShowTemplates] = useState(false);

  // Estados para documentos con enlaces en formulario
  const [documentsWithLinks, setDocumentsWithLinks] = useState([]);

  // Cargar datos iniciales
  useEffect(() => {
    fetchData();
    loadMachines();
    loadUsers();
    loadRoles();
    checkVencimientos();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
        const data = await fetchWithAuth('/api/mantenimiento-legal');
        console.log('Datos recibidos del backend:', data); // Para debugging
        
        // ✅ Asegurar que todos los campos estén disponibles
        const enrichedData = data.map(item => ({
        ...item,
        // Asegurar que todos los campos necesarios estén presentes
        maquina_id: item.maquina_id || item.machine_id,
        tipo_regulacion: item.tipo_regulacion || null,
        organismo_certificador: item.organismo_certificador || null,
        numero_certificado: item.numero_certificado || null,
        normativa_aplicable: item.normativa_aplicable || null,
        notification_interval: item.notification_interval || 30,
        assigned_role_id: item.assigned_role_id || null,
        assigned_user_id: item.assigned_user_id || null
        }));
        
        setLegalMaintenances(enrichedData || []);
    } catch (error) {
        message.error("Error al cargar los mantenimientos legales");
        console.error('Error fetching legal maintenances:', error);
    } finally {
        setLoading(false);
    }
    };

  const debugMaintenance = (record) => {
    console.log('=== DEBUG MANTENIMIENTO ===');
    console.log('ID:', record.id);
    console.log('Title:', record.title);
    console.log('Description:', record.description);
    console.log('Machine ID:', record.maquina_id);
    console.log('Frequency:', record.frecuencia);
    console.log('Next Date:', record.next_maintenance_date);
    console.log('Notification Interval:', record.notification_interval);
    console.log('Assigned Role ID:', record.assigned_role_id);
    console.log('Assigned User ID:', record.assigned_user_id);
    console.log('Tipo Regulacion:', record.tipo_regulacion);
    console.log('Organismo:', record.organismo_certificador);
    console.log('Numero Certificado:', record.numero_certificado);
    console.log('Normativa:', record.normativa_aplicable);
    console.log('=========================');
    };


  const loadMachines = async () => {
    try {
      const data = await fetchWithAuth('/maquinas');
      setMachines(data || []);
    } catch (error) {
      console.error('Error loading machines:', error);
    }
  };

  const loadUsers = async () => {
    try {
      const data = await fetchWithAuth('/users');
      setUsers(data || []);
    } catch (error) {
      console.error('Error loading users:', error);
    }
  };

  const loadRoles = async () => {
    try {
      const data = await fetchWithAuth('/roles');
      setRoles(data || []);
    } catch (error) {
      console.error('Error loading roles:', error);
    }
  };

  // Función para verificar vencimientos y enviar notificaciones
  const checkVencimientos = () => {
    const proximosVencimientos = legalMaintenances.filter(m => {
      const status = getExpirationStatus(m.next_maintenance_date);
      return status.status === 'warning' || status.status === 'expired';
    });

    if (proximosVencimientos.length > 0) {
      notification.warning({
        message: 'Mantenimientos Legales Próximos a Vencer',
        description: `Hay ${proximosVencimientos.length} mantenimientos que requieren atención inmediata`,
        duration: 10,
        icon: <WarningOutlined style={{ color: '#faad14' }} />
      });
    }
  };

  // Funciones de gestión
  const handleCreate = () => {
    if (isMechanic) {
        message.warning('No tienes permisos para crear mantenimientos legales');
        return;
    }
    
    createForm.resetFields();
    setSelectedTemplate(null);
    setDocumentsWithLinks([]);
    setShowTemplates(true);
    setIsCreateModalVisible(true);
    };

  const handleUseTemplate = (templateKey) => {
    const template = PLANTILLAS_PREDEFINIDAS[templateKey];
    if (template) {
      createForm.setFieldsValue({
        title: template.titulo,
        description: template.descripcion,
        tipo_regulacion: template.categoria,
        frecuencia: template.frecuencia,
        normativa_aplicable: template.normativa || CATEGORIAS_MANTENIMIENTO_LEGAL[template.categoria]?.normativa,
        organismo_certificador: template.organismos[0]
      });
      setSelectedTemplate(template);
      setShowTemplates(false);
    }
  };

  const handleEdit = (record) => {
    if (isMechanic) {
        message.warning('No tienes permisos para editar mantenimientos legales');
        return;
    }
    
    console.log('Record completo para editar:', record); // Para debugging
    
    setSelectedMaintenance(record);
    
    // ✅ Cargar TODOS los campos correctamente
    editForm.setFieldsValue({
        title: record.title,
        description: record.description,
        maquina_id: record.maquina_id,
        frecuencia: record.frecuencia,
        fechaInicio: record.next_maintenance_date ? dayjs(record.next_maintenance_date) : null,
        notification_interval: record.notification_interval || 30,
        assigned_role_id: record.assigned_role_id,
        assigned_user_id: record.assigned_user_id,
        tipo_regulacion: record.tipo_regulacion,
        organismo_certificador: record.organismo_certificador,
        numero_certificado: record.numero_certificado,
        normativa_aplicable: record.normativa_aplicable
    });
    
    setIsEditModalVisible(true);
    };

  const handleSubmitEdit = async () => {
    try {
      setSubmitting(true);
      const values = await editForm.validateFields();
      
      const payload = {
        title: values.title,
        description: values.description,
        maquina_id: values.maquina_id,
        frecuencia: values.frecuencia,
        fechaInicio: values.fechaInicio.format('YYYY-MM-DD'),
        notification_interval: values.notification_interval || 30,
        assigned_role_id: values.assigned_role_id,
        assigned_user_id: values.assigned_user_id,
        tipo_regulacion: values.tipo_regulacion,
        organismo_certificador: values.organismo_certificador,
        numero_certificado: values.numero_certificado,
        normativa_aplicable: values.normativa_aplicable
      };

      await fetchWithAuth(`/api/mantenimiento-legal/${selectedMaintenance.id}`, {
        method: 'PUT',
        body: JSON.stringify(payload)
      });

      message.success('Mantenimiento legal actualizado correctamente');
      setIsEditModalVisible(false);
      await fetchData();
    } catch (error) {
      console.error('Error updating legal maintenance:', error);
      message.error(`Error al actualizar mantenimiento legal: ${error.message || 'Error desconocido'}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitCreate = async () => {
    try {
      setSubmitting(true);
      const values = await createForm.validateFields();
      
      const payload = {
        title: values.title,
        description: values.description,
        maquina_id: values.maquina_id,
        frecuencia: values.frecuencia,
        fechaInicio: values.fechaInicio.format('YYYY-MM-DD'),
        notification_interval: values.notification_interval || 30,
        assigned_role_id: values.assigned_role_id,
        assigned_user_id: values.assigned_user_id,
        tipo_regulacion: values.tipo_regulacion,
        organismo_certificador: values.organismo_certificador,
        numero_certificado: values.numero_certificado,
        normativa_aplicable: values.normativa_aplicable
      };

      const response = await fetchWithAuth('/api/mantenimiento-legal', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      message.success('Mantenimiento legal creado correctamente');
      setIsCreateModalVisible(false);
      await fetchData();
      
      // Mostrar notificación sobre la importancia de subir documentos
      notification.info({
        message: 'Documentación Requerida',
        description: 'Recuerde subir los certificados y documentos oficiales para mantener la trazabilidad ISO 9001',
        duration: 8,
        icon: <FileTextOutlined style={{ color: '#1890ff' }} />
      });

    } catch (error) {
      console.error('Error creating legal maintenance:', error);
      message.error(`Error al crear mantenimiento legal: ${error.message || 'Error desconocido'}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (maintenanceId) => {
    if (isMechanic) {
        message.warning('No tienes permisos para eliminar mantenimientos legales');
        return;
    }
    
    setDeletingId(maintenanceId);
    try {
        await fetchWithAuth(`/api/mantenimiento-legal/${maintenanceId}`, {
        method: 'DELETE'
        });
        
        message.success('Mantenimiento legal eliminado correctamente');
        await fetchData();
    } catch (error) {
        console.error('Error deleting legal maintenance:', error);
        message.error(`Error al eliminar mantenimiento legal: ${error.message || 'Error desconocido'}`);
    } finally {
        setDeletingId(null);
    }
    };


  const handleOpenDocs = (record) => {
    setSelectedMaintenance(record);
    setIsDocModalVisible(true);
  };

  const handleViewDetail = (record) => {
    setSelectedMaintenance(record);
    setIsDetailModalVisible(true);
  };

  // Función para obtener el estado de vencimiento con más detalle
  const getExpirationStatus = (nextDate) => {
    if (!nextDate) return { status: 'unknown', color: 'default', text: 'Sin fecha', level: 0 };
    
    const today = dayjs();
    const expDate = dayjs(nextDate);
    const daysToExpire = expDate.diff(today, 'day');
    
    if (daysToExpire < 0) {
      return { 
        status: 'expired', 
        color: 'red', 
        text: `VENCIDO hace ${Math.abs(daysToExpire)} días`,
        level: 4,
        action: 'RENOVAR INMEDIATAMENTE'
      };
    } else if (daysToExpire <= 15) {
      return { 
        status: 'critical', 
        color: 'red', 
        text: `${daysToExpire} días restantes`,
        level: 3,
        action: 'ACCIÓN INMEDIATA'
      };
    } else if (daysToExpire <= 30) {
      return { 
        status: 'warning', 
        color: 'orange', 
        text: `${daysToExpire} días restantes`,
        level: 2,
        action: 'PLANIFICAR RENOVACIÓN'
      };
    } else if (daysToExpire <= 90) {
      return { 
        status: 'notice', 
        color: 'gold', 
        text: `${daysToExpire} días restantes`,
        level: 1,
        action: 'MONITOREAR'
      };
    } else {
      return { 
        status: 'ok', 
        color: 'green', 
        text: `${daysToExpire} días restantes`,
        level: 0,
        action: 'VIGENTE'
      };
    }
  };

  // Estadísticas avanzadas
  const getAdvancedStats = () => {
    const stats = {
      total: legalMaintenances.length,
      vencidos: 0,
      proximos: 0,
      criticos: 0,
      vigentes: 0,
      porCategoria: {}
    };

    legalMaintenances.forEach(m => {
      const status = getExpirationStatus(m.next_maintenance_date);
      
      if (status.status === 'expired') stats.vencidos++;
      else if (status.status === 'critical') stats.criticos++;
      else if (status.status === 'warning') stats.proximos++;
      else stats.vigentes++;

      // Agrupar por categoría
      const categoria = m.tipo_regulacion || 'Sin categoría';
      stats.porCategoria[categoria] = (stats.porCategoria[categoria] || 0) + 1;
    });

    return stats;
  };

  // Componente del formulario profesional con plantillas
  const renderMaintenanceForm = (form, isEdit = false) => (
    <Form form={form} layout="vertical" requiredMark={false}>
      
      {/* SELECTOR DE PLANTILLAS */}
      {!isEdit && showTemplates && (
        <Card title="Seleccionar Plantilla Predefinida" style={{ marginBottom: 24 }}>
          <Alert
            message="Plantillas Basadas en Normativa Española"
            description="Seleccione una plantilla predefinida según la normativa aplicable para fábricas cerámicas"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <Row gutter={[16, 16]}>
            {Object.entries(PLANTILLAS_PREDEFINIDAS).map(([key, template]) => (
              <Col span={8} key={key}>
                <Card
                  hoverable
                  size="small"
                  onClick={() => handleUseTemplate(key)}
                  style={{ 
                    border: template.nivel_criticidad === 'CRÍTICA' ? '2px solid #ff4d4f' : 
                           template.nivel_criticidad === 'ALTA' ? '2px solid #faad14' : '1px solid #d9d9d9'
                  }}
                >
                  <Card.Meta
                    avatar={CATEGORIAS_MANTENIMIENTO_LEGAL[template.categoria]?.icon}
                    title={<Text strong style={{ fontSize: '12px' }}>{template.titulo}</Text>}
                    description={
                      <div>
                        <Tag color={CATEGORIAS_MANTENIMIENTO_LEGAL[template.categoria]?.color} size="small">
                          {template.categoria}
                        </Tag>
                        <div style={{ fontSize: '11px', marginTop: 4 }}>
                          Frecuencia: {template.frecuencia}
                        </div>
                        <div style={{ fontSize: '11px' }}>
                          Organismo: {template.organismos[0]}
                        </div>
                      </div>
                    }
                  />
                </Card>
              </Col>
            ))}
          </Row>
          
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Button onClick={() => setShowTemplates(false)}>
              Crear Mantenimiento Personalizado
            </Button>
          </div>
        </Card>
      )}

      {/* FORMULARIO PRINCIPAL */}
      {(!showTemplates || isEdit) && (
        <>
          <Alert
            message="Registro de Mantenimiento Legal - ISO 9001:2015"
            description="Complete todos los campos para asegurar la trazabilidad y cumplimiento normativo. Los campos marcados son obligatorios según auditorías ISO."
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                name="title"
                label="Título de la Inspección/Certificación"
                rules={[{ required: true, message: 'Campo obligatorio para trazabilidad' }]}
                extra="Describa claramente el tipo de inspección según normativa aplicable"
              >
                <Input 
                  placeholder="Ej: Inspección Quinquenal OCA - Instalación Eléctrica BT >100kW"
                  prefix={<SafetyCertificateOutlined />}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="tipo_regulacion"
                label="Categoría Normativa"
                rules={[{ required: true, message: 'Seleccione la categoría' }]}
                extra="Clasificación según tipo de instalación/equipo"
              >
                <Select placeholder="Seleccione la categoría normativa">
                  {Object.entries(CATEGORIAS_MANTENIMIENTO_LEGAL).map(([key, categoria]) => (
                    <Option key={key} value={key}>
                      <Space>
                        {categoria.icon}
                        <div>
                          <div><strong>{key}</strong></div>
                          <div style={{ fontSize: '11px', color: '#666' }}>
                            {categoria.normativa} - {categoria.descripcion}
                          </div>
                        </div>
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="maquina_id"
                label="Equipo/Instalación Afectada"
                rules={[{ required: true, message: 'Seleccione el equipo' }]}
                extra="Equipo o instalación sujeta a inspección legal"
                >
                <Select 
                    placeholder="Seleccione el equipo/instalación"
                    showSearch
                    optionFilterProp="label"
                    filterOption={(input, option) => {
                    if (!input || input.trim() === '') return true;
                    const searchTerm = input.toLowerCase().trim();
                    return option.label.toLowerCase().includes(searchTerm);
                    }}
                    allowClear
                    options={machines.map(machine => ({
                    value: machine.id,
                    label: machine.nombre
                    }))}
                />
                </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="frecuencia"
                label="Periodicidad Legal"
                rules={[{ required: true, message: 'Seleccione la frecuencia' }]}
                extra="Frecuencia obligatoria según reglamento"
              >
                <Select placeholder="Según normativa">
                  {FRECUENCIAS_LEGALES.map(freq => (
                    <Option key={freq.value} value={freq.value}>
                      <div>
                        <div><strong>{freq.label}</strong></div>
                        <div style={{ fontSize: '11px', color: '#666' }}>{freq.descripcion}</div>
                      </div>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="fechaInicio"
                label="Fecha Próxima Inspección"
                rules={[{ required: true, message: 'Fecha obligatoria' }]}
                extra="Fecha límite según certificado vigente"
              >
                <DatePicker 
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
                  placeholder="Seleccione la fecha"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="notification_interval"
                label="Días de Aviso Previo"
                initialValue={30}
                extra="Días de antelación para alertas"
              >
                <InputNumber 
                  min={1}
                  max={365}
                  style={{ width: '100%' }}
                  addonAfter="días"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="organismo_certificador"
                label="Organismo Certificador/Inspector"
                rules={[{ required: true, message: 'Organismo obligatorio' }]}
                extra="Debe ser organismo autorizado según normativa"
              >
                <Select placeholder="Seleccione organismo autorizado">
                  {ORGANISMOS_CERTIFICADORES.map(org => (
                    <Option key={org.value} value={org.value}>
                      <div>
                        <div><strong>{org.label}</strong></div>
                        <div style={{ fontSize: '11px', color: '#666' }}>
                          {org.tipo} - Especialidades: {org.especialidades.join(', ')}
                        </div>
                      </div>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="numero_certificado"
                label="Número de Certificado/Expediente"
                extra="Número de referencia del certificado oficial"
              >
                <Input placeholder="Ej: OCA-2024-001234, ITV-VAL-2024-5678" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="normativa_aplicable"
            label="Normativa y Referencias Legales"
            extra="Cite los reglamentos y normas específicas que aplican"
          >
            <TextArea 
              rows={2}
              placeholder="Ej: RD 842/2002 REBT, ITC-BT-04, UNE 20460, Ley 31/1995 PRL"
            />
          </Form.Item>

          <Form.Item
            name="description"
            label="Descripción Técnica y Alcance"
            rules={[{ required: true, message: 'Descripción obligatoria' }]}
            extra="Detalle técnico de la inspección, equipos incluidos y criterios de aceptación"
          >
            <TextArea 
              rows={4}
              placeholder="Describa el alcance de la inspección, equipos incluidos, pruebas a realizar, criterios de aceptación según normativa..."
            />
          </Form.Item>

          <Divider orientation="left">Asignación de Responsabilidades</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="assigned_role_id"
                label="Rol Responsable del Seguimiento"
                extra="Rol interno responsable de la gestión y seguimiento"
              >
                <Select placeholder="Seleccione el rol responsable">
                  {roles.map(role => (
                    <Option key={role.id} value={role.id}>{role.nombre}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="assigned_user_id"
                label="Persona Responsable"
                extra="Persona específica encargada del seguimiento"
              >
                <Select placeholder="Seleccione la persona responsable">
                  {users.map(user => (
                    <Option key={user.id} value={user.id}>{user.username}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          {/* INFORMACIÓN DE LA PLANTILLA SELECCIONADA */}
          {selectedTemplate && (
            <Card 
              title="Información de la Plantilla Seleccionada" 
              size="small" 
              style={{ marginTop: 16, backgroundColor: '#f9f9f9' }}
            >
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Equipos Típicos">
                  {selectedTemplate.equipos_tipicos?.join(', ')}
                </Descriptions.Item>
                <Descriptions.Item label="Documentos Requeridos">
                  {selectedTemplate.documentos_requeridos?.join(', ')}
                </Descriptions.Item>
                <Descriptions.Item label="Nivel de Criticidad">
                  <Tag color={selectedTemplate.nivel_criticidad === 'CRÍTICA' ? 'red' : 
                            selectedTemplate.nivel_criticidad === 'ALTA' ? 'orange' : 'blue'}>
                    {selectedTemplate.nivel_criticidad}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Organismos Aplicables">
                  {selectedTemplate.organismos?.join(', ')}
                </Descriptions.Item>
              </Descriptions>
            </Card>
          )}

          {/* SECCIÓN DE DOCUMENTOS CON ENLACES EN EL FORMULARIO */}
          {!isEdit && (
            <>
              <Divider orientation="left">
                <FileTextOutlined /> Documentación Legal y Certificados
              </Divider>
              
              <Alert
                message="Documentación para Trazabilidad ISO 9001"
                description="La documentación es CRÍTICA para auditorías. Suba certificados oficiales, informes de inspección y cualquier documento que demuestre el cumplimiento legal."
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Card title="Gestión de Documentos" size="small">
                <p><strong>Documentos que debe subir después de crear el mantenimiento:</strong></p>
                <ul>
                  <li>📄 <strong>Certificado oficial</strong> del organismo autorizado (OCA, ENAC, etc.)</li>
                  <li>📄 <strong>Informe técnico</strong> detallado de la inspección</li>
                  <li>📄 <strong>Acta de inspección</strong> firmada por el técnico competente</li>
                  <li>📄 <strong>Documentación complementaria</strong> (fotos, medidas, esquemas)</li>
                  <li>📄 <strong>Etiquetas o placas</strong> de identificación actualizadas</li>
                </ul>
                
                <Alert
                  message="Los documentos se podrán subir y enlazar después de crear el mantenimiento usando el botón 'Certificados' en la tabla"
                  type="info"
                  style={{ marginTop: 12 }}
                />
              </Card>
            </>
          )}
        </>
      )}
    </Form>
  );

  // Definir columnas de la tabla ultra-profesional
  const columns = [
    {
      title: 'Inspección/Certificación',
      dataIndex: 'title',
      key: 'title',
      width: '25%',
      render: (text, record) => (
        <div>
          <Text strong style={{ color: '#1890ff', cursor: 'pointer' }} 
                onClick={() => handleViewDetail(record)}>
            {text}
          </Text>
          {record.numero_certificado && (
            <div>
              <Tag color="blue" size="small">
                📋 {record.numero_certificado}
              </Tag>
            </div>
          )}
          <div style={{ fontSize: '11px', color: '#666', marginTop: 4 }}>
            {record.tipo_regulacion && (
              <Tag color={CATEGORIAS_MANTENIMIENTO_LEGAL[record.tipo_regulacion]?.color} size="small">
                {CATEGORIAS_MANTENIMIENTO_LEGAL[record.tipo_regulacion]?.icon} {record.tipo_regulacion}
              </Tag>
            )}
          </div>
        </div>
      )
    },
    {
      title: 'Equipo/Instalación',
      dataIndex: 'maquina_nombre',
      key: 'maquina_nombre',
      width: '15%',
      render: (text) => (
        <div>
          <Text>{text}</Text>
        </div>
      )
    },
    {
      title: 'Organismo & Frecuencia',
      key: 'organismo_freq',
      width: '15%',
      render: (_, record) => (
        <div>
          <div>
            <Tag color="geekblue" size="small">
              {record.organismo_certificador || 'Sin asignar'}
            </Tag>
          </div>
          <div style={{ marginTop: 4 }}>
            <Badge 
              color={record.frecuencia === 'Quinquenal' || record.frecuencia === 'Cada 8 años' ? 'volcano' : 'blue'} 
              text={record.frecuencia}
            />
          </div>
        </div>
      )
    },
    {
      title: 'Estado de Cumplimiento',
      dataIndex: 'next_maintenance_date',
      key: 'next_maintenance_date',
      width: '20%',
      sorter: (a, b) => dayjs(a.next_maintenance_date).unix() - dayjs(b.next_maintenance_date).unix(),
      render: (date, record) => {
        if (!date) return <Text type="danger">Sin fecha programada</Text>;
        
        const status = getExpirationStatus(date);
        return (
          <div>
            <div><Text strong>{dayjs(date).format('DD/MM/YYYY')}</Text></div>
            <Badge 
              status={status.status === 'expired' ? 'error' : 
                     status.status === 'critical' ? 'error' :
                     status.status === 'warning' ? 'warning' : 
                     status.status === 'notice' ? 'processing' : 'success'} 
              text={<Text style={{ fontSize: '11px' }}>{status.text}</Text>}
            />
            <div style={{ marginTop: 2 }}>
              <Tag 
                color={status.status === 'expired' || status.status === 'critical' ? 'red' : 
                      status.status === 'warning' ? 'orange' : 
                      status.status === 'notice' ? 'gold' : 'green'}
                size="small"
              >
                {status.action}
              </Tag>
            </div>
          </div>
        );
      }
    },
    {
      title: 'Documentos',
      key: 'documents',
      align: 'center',
      width: '10%',
      render: (_, record) => (
        <Tooltip title="Gestionar Certificados y Documentos Oficiales">
          <Button 
            icon={<FilePdfOutlined />} 
            onClick={() => handleOpenDocs(record)}
            size="small"
            type="primary"
            ghost
          >
            Certificados
          </Button>
        </Tooltip>
      )
    },
    {
  title: 'Acciones',
  key: 'actions',
  align: 'center',
  width: '15%',
  render: (_, record) => {
    const status = getExpirationStatus(record.next_maintenance_date);
    
    // Menu para roles con permisos de gestión
    const manageMenu = (
      <Menu>
        <Menu.Item key="detail" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>
          Ver Detalle Completo
        </Menu.Item>
        <Menu.Item key="edit" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
          Editar
        </Menu.Item>
        <Menu.Item key="docs" icon={<FilePdfOutlined />} onClick={() => handleOpenDocs(record)}>
          Gestionar Documentos
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item
          key="delete"
          icon={<DeleteOutlined />}
          danger
          onClick={() => {
            Modal.confirm({
              title: '¿Eliminar Mantenimiento Legal?',
              content: 'Esta acción eliminará el registro y afectará la trazabilidad ISO 9001. ¿Continuar?',
              icon: <ExclamationCircleOutlined />,
              okText: 'Sí, eliminar',
              cancelText: 'Cancelar',
              okButtonProps: { danger: true },
              onOk: () => handleDelete(record.id)
            });
          }}
        >
          Eliminar
        </Menu.Item>
      </Menu>
    );

    // Menu para mecánicos (solo lectura)
    const readOnlyMenu = (
      <Menu>
        <Menu.Item key="detail" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>
          Ver Detalle Completo
        </Menu.Item>
        <Menu.Item key="docs" icon={<FilePdfOutlined />} onClick={() => handleOpenDocs(record)}>
          Ver Documentos
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item key="restricted" icon={<LockOutlined />} disabled>
          <span style={{ color: '#999' }}>Permisos Restringidos</span>
        </Menu.Item>
      </Menu>
    );

    return (
      <Space size="small">
        {status.level >= 2 && (
          <Tooltip title={`Acción requerida: ${status.action}`}>
            <Button
              icon={<BellOutlined />}
              size="small"
              danger={status.level >= 3}
              type={status.level >= 3 ? "primary" : "default"}
            />
          </Tooltip>
        )}
        
        {/* Mostrar menu según permisos */}
        <Dropdown overlay={canManageOrEdit ? manageMenu : readOnlyMenu} trigger={['click']}>
          <Button 
            icon={<MoreOutlined />} 
            size="small" 
            style={isMechanic ? { borderColor: '#1890ff', color: '#1890ff' } : {}}
          />
        </Dropdown>
        
        {/* Indicador visual para mecánicos */}
        {isMechanic && (
          <Tooltip title="Solo lectura">
            <LockOutlined style={{ color: '#1890ff', fontSize: '12px' }} />
          </Tooltip>
        )}
      </Space>
    );
  }
}  ];

  const stats = getAdvancedStats();

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2} className="page-title">
            <SafetyCertificateOutlined /> Mantenimiento Legal y Regulatorio
            {isMechanic && (
                <Tag color="blue" style={{ marginLeft: 8, fontSize: '12px' }}>
                Solo Lectura
                </Tag>
            )}
            </Title>
        <Space>
            {canManageOrEdit ? (
                <Button 
                    type="primary" 
                    icon={<PlusOutlined />}
                    onClick={handleCreate}
                    size="large"
                >
                    Nueva Inspección Legal
                </Button>
                ) : (
                <Tooltip title="No tienes permisos para crear mantenimientos legales">
                    <Button 
                    disabled
                    icon={<LockOutlined />}
                    size="large"
                    >
                    Nueva Inspección Legal
                    </Button>
                </Tooltip>
                )}

        </Space>
      </div>

      {/* PANEL DE ESTADÍSTICAS PROFESIONAL */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Inspecciones"
              value={stats.total}
              prefix={<SafetyCertificateOutlined />}
              suffix={<div style={{ fontSize: '12px', color: '#666' }}>registradas</div>}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="CRÍTICO - Vencidas"
              value={stats.vencidos}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
              suffix={<div style={{ fontSize: '12px', color: '#cf1322' }}>RENOVAR YA</div>}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Próximas (30 días)"
              value={stats.proximos + stats.criticos}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
              suffix={<div style={{ fontSize: '12px', color: '#fa8c16' }}>planificar</div>}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Vigentes"
              value={stats.vigentes}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={<div style={{ fontSize: '12px', color: '#52c41a' }}>cumpliendo</div>}
            />
          </Card>
        </Col>
      </Row>
      {isMechanic && (
        <Alert
          message="Modo Solo Lectura"
          description="Como mecánico, puedes visualizar todos los mantenimientos legales y exportar informes, pero no puedes crear, editar o eliminar registros. Para gestionar mantenimientos, contacta con tu supervisor."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          closable
        />
      )}

      {/* ALERTAS DE CRITICIDAD */}
      {(stats.vencidos > 0 || stats.criticos > 0) && (
        <Alert
            message={`¡ATENCIÓN! ${stats.vencidos + stats.criticos} inspecciones requieren acción inmediata`}
            description="El incumplimiento de las inspecciones legales puede resultar en sanciones, cierre de instalaciones y pérdida de certificaciones ISO 9001"
            type="error"
            showIcon
            action={
            canManageOrEdit ? (
                <Button size="small" danger onClick={handleCreate}>
                Crear Inspección
                </Button>
            ) : (
                <Button size="small" disabled icon={<LockOutlined />}>
                Sin Permisos
                </Button>
            )
            }
            style={{ marginBottom: 16 }}
        />
        )}
      
      <Card>
        <Table
          columns={columns}
          dataSource={legalMaintenances}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} de ${total} inspecciones | Vigentes: ${stats.vigentes} | Críticas: ${stats.vencidos + stats.criticos}`
          }}
          scroll={{ x: 'max-content' }}
          rowClassName={(record) => {
            const status = getExpirationStatus(record.next_maintenance_date);
            return status.status === 'expired' || status.status === 'critical' ? 'critical-row' : 
                   status.status === 'warning' ? 'warning-row' : '';
          }}
        />
      </Card>

      {/* MODAL DE CREACIÓN CON PLANTILLAS */}
      <Modal
        title={
          <div>
            <SafetyCertificateOutlined /> {showTemplates ? 'Seleccionar Plantilla' : 'Nueva Inspección Legal'}
          </div>
        }
        open={isCreateModalVisible}
        onCancel={() => setIsCreateModalVisible(false)}
        width={showTemplates ? 1200 : 800}
        footer={showTemplates ? null : [
          <Button key="cancel" onClick={() => setIsCreateModalVisible(false)}>
            Cancelar
          </Button>,
          <Button
            key="submit"
            type="primary"
            loading={submitting}
            onClick={handleSubmitCreate}
            icon={<SafetyCertificateOutlined />}
          >
            Crear Inspección Legal
          </Button>
        ]}
        destroyOnClose
      >
        {renderMaintenanceForm(createForm)}
      </Modal>

      {/* MODAL DE EDICIÓN */}
      <Modal
        title={
          <div>
            <EditOutlined /> Editar Mantenimiento Legal
          </div>
        }
        open={isEditModalVisible}
        onCancel={() => setIsEditModalVisible(false)}
        width={800}
        footer={[
          <Button key="cancel" onClick={() => setIsEditModalVisible(false)}>
            Cancelar
          </Button>,
          <Button
            key="submit"
            type="primary"
            loading={submitting}
            onClick={handleSubmitEdit}
            icon={<EditOutlined />}
          >
            Actualizar Mantenimiento
          </Button>
        ]}
        destroyOnClose
      >
        {renderMaintenanceForm(editForm, true)}
      </Modal>

      {/* MODAL DE DETALLE COMPLETO */}
      <Modal
        title={
          <div>
            <EyeOutlined /> Detalle Completo - {selectedMaintenance?.title}
          </div>
        }
        open={isDetailModalVisible}
        onCancel={() => setIsDetailModalVisible(false)}
        width={900}
        footer={[
          <Button key="docs" icon={<FilePdfOutlined />} onClick={() => {
            setIsDetailModalVisible(false);
            handleOpenDocs(selectedMaintenance);
          }}>
            Gestionar Documentos
          </Button>,
          <Button key="close" type="primary" onClick={() => setIsDetailModalVisible(false)}>
            Cerrar
          </Button>
        ]}
      >
        {selectedMaintenance && (
          <div>
            <Descriptions title="Información Legal y Normativa" bordered column={2}>
              <Descriptions.Item label="Categoría Normativa" span={2}>
                <Tag color={CATEGORIAS_MANTENIMIENTO_LEGAL[selectedMaintenance.tipo_regulacion]?.color}>
                  {CATEGORIAS_MANTENIMIENTO_LEGAL[selectedMaintenance.tipo_regulacion]?.icon} {selectedMaintenance.tipo_regulacion}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Normativa Aplicable" span={2}>
                {selectedMaintenance.normativa_aplicable || 'No especificada'}
              </Descriptions.Item>
              <Descriptions.Item label="Organismo Certificador">
                {selectedMaintenance.organismo_certificador}
              </Descriptions.Item>
              <Descriptions.Item label="Número Certificado">
                {selectedMaintenance.numero_certificado || 'Sin asignar'}
              </Descriptions.Item>
              <Descriptions.Item label="Equipo/Instalación">
                {selectedMaintenance.maquina_nombre}
              </Descriptions.Item>
              <Descriptions.Item label="Frecuencia Legal">
                {selectedMaintenance.frecuencia}
              </Descriptions.Item>
              <Descriptions.Item label="Próxima Inspección">
                {selectedMaintenance.next_maintenance_date ? 
                  dayjs(selectedMaintenance.next_maintenance_date).format('DD/MM/YYYY') : 
                  'Sin programar'
                }
              </Descriptions.Item>
              <Descriptions.Item label="Estado">
                {(() => {
                  const status = getExpirationStatus(selectedMaintenance.next_maintenance_date);
                  return (
                    <Badge 
                      status={status.status === 'expired' ? 'error' : 
                             status.status === 'critical' ? 'error' :
                             status.status === 'warning' ? 'warning' : 'success'} 
                      text={status.action}
                    />
                  );
                })()}
              </Descriptions.Item>
              <Descriptions.Item label="Descripción Técnica" span={2}>
                {selectedMaintenance.description}
              </Descriptions.Item>
            </Descriptions>

            <Divider />
            
            <Timeline>
              <Timeline.Item color="blue" dot={<CalendarOutlined />}>
                <Text strong>Creado:</Text> {dayjs(selectedMaintenance.created_at).format('DD/MM/YYYY HH:mm')}
              </Timeline.Item>
              <Timeline.Item color="green" dot={<CheckCircleOutlined />}>
                <Text strong>Próxima Inspección:</Text> {dayjs(selectedMaintenance.next_maintenance_date).format('DD/MM/YYYY')}
              </Timeline.Item>
              <Timeline.Item color="red" dot={<WarningOutlined />}>
                <Text strong>Alerta:</Text> {selectedMaintenance.notification_interval} días antes
              </Timeline.Item>
            </Timeline>
          </div>
        )}
      </Modal>

      {/* MODAL DE GESTIÓN DE DOCUMENTOS */}
      {selectedMaintenance && (
        <Modal
          title={
            <div>
              <FilePdfOutlined /> Certificados y Documentos Oficiales
              <div style={{ fontSize: '14px', fontWeight: 'normal', marginTop: 4 }}>
                {selectedMaintenance.title}
              </div>
            </div>
          }
          open={isDocModalVisible}
          onCancel={() => setIsDocModalVisible(false)}
          footer={null}
          width="90%"
          destroyOnClose
        >
          <Alert
            message="Documentación Crítica para Auditorías ISO 9001"
            description="Mantenga aquí TODOS los certificados oficiales, informes de inspección y documentación legal. Esta es la evidencia que revisarán los auditores para verificar el cumplimiento normativo."
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <DocumentAttachmentManager
            entityType="maintenance"
            entityId={selectedMaintenance.id}
            title=""
          />
        </Modal>
      )}

      <style jsx global>{`
        .critical-row {
          background-color: #fff2f0 !important;
          border-left: 4px solid #ff4d4f !important;
        }
        .warning-row {
          background-color: #fff7e6 !important;
          border-left: 4px solid #faad14 !important;
        }
        .ant-statistic-title {
          font-size: 14px;
        }
        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }
        .page-title {
          margin: 0;
        }
        .ant-descriptions-item-label {
          font-weight: 600;
          background-color: #fafafa;
        }
      `}</style>
    </div>
  );
};

export default MantenimientoLegal;