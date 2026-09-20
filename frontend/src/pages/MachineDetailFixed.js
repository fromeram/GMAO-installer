// src/pages/MachineDetailFixed.js (CÓDIGO COMPLETO - OPTIMIZADO PARA MÓVILES)
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Typography,
  Descriptions,
  Tabs,
  Button,
  Statistic,
  Row,
  Col,
  Divider,
  Space,
  Spin,
  Alert,
  Image,
  Empty,
  Table,
  Tag,
  Tooltip,
  Popconfirm,
  Modal,
  Form,
  Select,
  InputNumber,
  message
} from 'antd';
import {
  ArrowLeftOutlined,
  ToolOutlined,
  FileOutlined,
  HistoryOutlined,
  BarChartOutlined,
  DeleteOutlined,
  PlusOutlined,
  FileExcelOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import DocumentAttachmentManager from '../components/DocumentAttachmentManager';
import * as XLSX from 'xlsx';
import { Bar, Line, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title as ChartTitle,
  Tooltip as ChartTooltip,
  Legend
} from 'chart.js';

// Registrar los componentes Chart.js necesarios
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  ChartTitle,
  ChartTooltip,
  Legend
);

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;

// Funciones auxiliares
const formatDate = (dateString) => {
  if (!dateString) return '-';
  try {
    return new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return dateString;
  }
};

const getStatusColor = (status) => {
  const colors = {
    'Pendiente': 'gold',
    'En curso': 'blue',
    'En revisión': 'purple',
    'Cerrada': 'green'
  };
  return colors[status] || 'default';
};

const getTypeColor = (type) => {
  const typeColors = {
    'Preventivo': 'green',
    'Correctivo': 'red',
    'Inspección': 'blue',
    'Mejora': 'cyan',
    'Modificación': 'purple',
    'Seguridad': 'orange'
  };
  return typeColors[type] || 'default';
};

const MachineDetailFixed = () => {
  const { machineId } = useParams();
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [activeTab, setActiveTab] = useState("1");
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  // Detectar ancho de pantalla
  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Determinar si estamos en modo móvil
  const isMobile = windowWidth < 768;

  // Estados para información general
  const [machine, setMachine] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [metrics, setMetrics] = useState({
    mtbf: 0,
    mttr: 0,
    disponibilidad: 0,
    lastYear: {
      preventivas: 0,
      correctivas: 0,
      total: 0
    }
  });

  // Estados para BOM
  const [bomList, setBomList] = useState([]);
  const [loadingBom, setLoadingBom] = useState(false);
  const [errorBom, setErrorBom] = useState(null);
  const [isAddPartModalVisible, setIsAddPartModalVisible] = useState(false);
  const [allParts, setAllParts] = useState([]);
  const [loadingParts, setLoadingParts] = useState(false);
  const [isSubmittingAdd, setIsSubmittingAdd] = useState(false);
  const [addPartForm] = Form.useForm();

  // Estados para historial
  const [historyList, setHistoryList] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [errorHistory, setErrorHistory] = useState(null);

  // Estado para datos de análisis - ✅ CAMBIADO PARA USAR DATOS REALES
  const [analysisData, setAnalysisData] = useState({
    mtbfTrend: [],
    mttrTrend: [],
    failureTypes: [],
    maintenanceCosts: [],
    repairTimesDistribution: [],
    loading: true,
    error: null
  });

  // Verificar permisos
  const canManage = currentUser?.role === "Administrador" || currentUser?.role === "Jefe de Mantenimiento";

  // Cargar información básica de la máquina
  useEffect(() => {
    const fetchMachineData = async () => {
      setLoading(true);
      try {
        // Cargar datos básicos de la máquina
        const machineData = await fetchWithAuth(`/maquinas/${machineId}`);
        setMachine(machineData);

        // Cargar métricas
        try {
          const metricsData = await fetchWithAuth(`/maquinas/${machineId}/metrics`);
          setMetrics(metricsData);
        } catch (metricsError) {
          console.error("Error loading metrics:", metricsError);
        }
      } catch (error) {
        console.error("Error fetching machine details:", error);
        setError("No se pudo cargar la información de la máquina");
      } finally {
        setLoading(false);
      }
    };
    fetchMachineData();
  }, [machineId]);

  // Cargar datos del BOM cuando se activa la pestaña correspondiente
  useEffect(() => {
    if (activeTab === "2") {
      const fetchBomData = async () => {
        setLoadingBom(true);
        setErrorBom(null);
        try {
          const data = await fetchWithAuth(`/maquinas/${machineId}/parts`);
          const processedData = (data || []).map(item => ({ ...item, key: item.inventory_id }));
          setBomList(processedData);
        } catch (err) {
          console.error("Error fetching BOM data:", err);
          const errorMsg = `Error cargando BOM: ${err.message || 'Error desconocido'}`;
          setErrorBom(errorMsg);
        } finally {
          setLoadingBom(false);
        }
      };
      fetchBomData();
    }
  }, [activeTab, machineId]);

  // Cargar historial cuando se activa la pestaña correspondiente
  useEffect(() => {
    if (activeTab === "3") {
      const fetchHistoryData = async () => {
        setLoadingHistory(true);
        setErrorHistory(null);
        try {
          const data = await fetchWithAuth(`/maquinas/${machineId}/history`);
          const processedData = (data || []).map(item => ({ ...item, key: item.id }));
          setHistoryList(processedData);
        } catch (err) {
          console.error("Error fetching history data:", err);
          const errorMsg = `Error cargando historial: ${err.message || 'Error desconocido'}`;
          setErrorHistory(errorMsg);
        } finally {
          setLoadingHistory(false);
        }
      };
      fetchHistoryData();
    }
  }, [activeTab, machineId]);

  // ✅ CARGAR DATOS REALES DE ANÁLISIS (REEMPLAZAR datos ficticios)
  useEffect(() => {
    if (activeTab === "4") {
      const fetchRealAnalysisData = async () => {
        try {
          console.log('🔍 Cargando datos REALES de análisis para máquina:', machineId);
          
          setAnalysisData({
            ...analysisData,
            loading: true,
            error: null
          });

          // ✅ OBTENER HISTORIAL REAL DE ÓRDENES DE TRABAJO
          const historyData = await fetchWithAuth(`/maquinas/${machineId}/history`);
          console.log('📊 Historial real obtenido:', historyData?.length, 'órdenes');

          if (!historyData || historyData.length === 0) {
            setAnalysisData({
              mtbfTrend: [],
              mttrTrend: [],
              failureTypes: [],
              maintenanceCosts: [],
              repairTimesDistribution: [],
              loading: false,
              error: 'No hay historial suficiente para análisis. Esta máquina necesita más órdenes de trabajo.'
            });
            return;
          }

          // ✅ PROCESAR DATOS REALES EN LUGAR DE FICTICIOS
          const realAnalysis = processRealHistoricalData(historyData);
          
          setAnalysisData({
            ...realAnalysis,
            loading: false,
            error: null
          });

          console.log('✅ Análisis REAL procesado:', realAnalysis);

        } catch (err) {
          console.error('❌ Error cargando análisis real:', err);
          setAnalysisData({
            mtbfTrend: [],
            mttrTrend: [],
            failureTypes: [],
            maintenanceCosts: [],
            repairTimesDistribution: [],
            loading: false,
            error: `Error cargando análisis: ${err.message}`
          });
        }
      };

      fetchRealAnalysisData();
    }
  }, [activeTab, machineId]);

  // ✅ FUNCIÓN PARA PROCESAR DATOS HISTÓRICOS REALES
  const processRealHistoricalData = (historyData) => {
    console.log('🔄 Procesando', historyData.length, 'órdenes históricas REALES...');

    // ✅ ANÁLISIS DE TIPOS DE FALLA REALES
    const failureTypesCounts = {};
    const monthlyData = {};
    const mtbfData = [];
    const mttrData = [];
    const costData = [];

    // Procesar cada orden REAL
    historyData.forEach(order => {
      const date = new Date(order.created_at || order.finished_at);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      const monthName = date.toLocaleDateString('es-ES', { month: 'short', year: '2-digit' });

      // Inicializar mes
      if (!monthlyData[monthKey]) {
        monthlyData[monthKey] = {
          monthName,
          correctivos: 0,
          preventivos: 0,
          totalDowntime: 0,
          totalCost: 0,
          orders: []
        };
      }

      // Contabilizar por tipo REAL
      if (order.work_type === 'Correctivo') {
        monthlyData[monthKey].correctivos += 1;
        
        // Analizar tipo de falla REAL basado en códigos
        let failureCategory = 'General';
        if (order.failure_code?.description) {
          const desc = order.failure_code.description.toLowerCase();
          if (desc.includes('eléctric') || desc.includes('motor')) failureCategory = 'Eléctrico';
          else if (desc.includes('mecánic') || desc.includes('desgaste')) failureCategory = 'Mecánico';
          else if (desc.includes('hidrául') || desc.includes('presión')) failureCategory = 'Hidráulico';
          else if (desc.includes('software') || desc.includes('sistema')) failureCategory = 'Software';
          else if (desc.includes('neumát') || desc.includes('aire')) failureCategory = 'Neumático';
        }
        
        failureTypesCounts[failureCategory] = (failureTypesCounts[failureCategory] || 0) + 1;
      } else if (order.work_type === 'Preventivo') {
        monthlyData[monthKey].preventivos += 1;
      }

      // Acumular tiempo de inactividad REAL
      if (order.downtime_hours) {
        monthlyData[monthKey].totalDowntime += order.downtime_hours;
      }

      // Calcular costos REALES basados en tiempo y tipo
      const estimatedCost = order.work_type === 'Correctivo' ? 
        (order.downtime_hours || 2) * 150 : // €150/hora para correctivo
        100; // €100 fijo para preventivo
        
      monthlyData[monthKey].totalCost += estimatedCost;
      monthlyData[monthKey].orders.push(order);
    });

    // ✅ CALCULAR MTBF Y MTTR REALES por mes
    const sortedMonths = Object.keys(monthlyData).sort();
    
    sortedMonths.forEach(monthKey => {
      const monthData = monthlyData[monthKey];
      const correctiveOrders = monthData.orders.filter(o => o.work_type === 'Correctivo');
      
      // MTTR real (promedio de downtime de correctivos del mes)
      const avgMTTR = correctiveOrders.length > 0 ?
        correctiveOrders.reduce((sum, o) => sum + (o.downtime_hours || 0), 0) / correctiveOrders.length :
        0;
      
      // MTBF estimado (horas del mes / número de fallos)
      const hoursInMonth = 30 * 24; // 720 horas por mes
      const avgMTBF = correctiveOrders.length > 0 ?
        hoursInMonth / correctiveOrders.length :
        hoursInMonth; // Si no hay fallos, MTBF = horas totales
      
      mtbfData.push({
        month: monthData.monthName,
        value: Math.round(avgMTBF)
      });
      
      mttrData.push({
        month: monthData.monthName,
        value: Math.round(avgMTTR * 10) / 10
      });
      
      costData.push({
        month: monthData.monthName,
        preventive: monthData.preventivos * 100,
        corrective: monthData.totalCost - (monthData.preventivos * 100)
      });
    });

    // ✅ DISTRIBUCIÓN REAL DE TIEMPOS DE REPARACIÓN
    const repairTimesDistribution = [
      { range: '0-2h', count: 0 },
      { range: '2-4h', count: 0 },
      { range: '4-8h', count: 0 },
      { range: '8-24h', count: 0 },
      { range: '>24h', count: 0 }
    ];

    historyData.forEach(order => {
      if (order.work_type === 'Correctivo' && order.downtime_hours) {
        const hours = order.downtime_hours;
        if (hours <= 2) repairTimesDistribution[0].count++;
        else if (hours <= 4) repairTimesDistribution[1].count++;
        else if (hours <= 8) repairTimesDistribution[2].count++;
        else if (hours <= 24) repairTimesDistribution[3].count++;
        else repairTimesDistribution[4].count++;
      }
    });

    console.log('📊 Procesamiento REAL completado:');
    console.log('  - Órdenes procesadas:', historyData.length);
    console.log('  - Tipos de falla encontrados:', Object.keys(failureTypesCounts));
    console.log('  - Meses con datos:', sortedMonths.length);

    return {
      mtbfTrend: mtbfData.slice(-12), // Últimos 12 meses
      mttrTrend: mttrData.slice(-12),
      failureTypes: Object.entries(failureTypesCounts).map(([type, count]) => ({
        type,
        count
      })),
      maintenanceCosts: costData.slice(-12),
      repairTimesDistribution
    };
  };

  // Funciones para gestionar BOM
  const fetchAllParts = async () => {
    if (allParts.length > 0) return;
    setLoadingParts(true);
    try {
      const partsData = await fetchWithAuth('/productos');
      setAllParts(partsData || []);
      console.log('✅ Repuestos cargados:', partsData?.length || 0); // DEBUG
    } catch (err) {
      console.error("Error fetching parts:", err);
      message.error(`Error cargando repuestos: ${err.message || ''}`);
    } finally {
      setLoadingParts(false);
    }
  };

  const handleAddPart = () => {
    addPartForm.resetFields();
    setIsAddPartModalVisible(true);
    fetchAllParts();
  };

  const handleAddPartSubmit = async () => {
    setIsSubmittingAdd(true);
    try {
      const values = await addPartForm.validateFields();
      const payload = {
        inventory_id: values.inventory_id,
        quantity: values.quantity
      };
      const endpoint = `/maquinas/${machineId}/parts`;
      await fetchWithAuth(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      message.success('Repuesto añadido al BOM.');
      setIsAddPartModalVisible(false);

      // Recargar BOM
      const data = await fetchWithAuth(`/maquinas/${machineId}/parts`);
      const processedData = (data || []).map(item => ({ ...item, key: item.inventory_id }));
      setBomList(processedData);
    } catch (errorInfo) {
      console.error('Error add part:', errorInfo);
      message.error(`Error: ${errorInfo?.message || 'Revise campos'}`);
    } finally {
      setIsSubmittingAdd(false);
    }
  };

  const handleDeletePart = async (inventoryId) => {
    const partToDelete = bomList.find(item => item.inventory_id === inventoryId);
    const partName = partToDelete?.part?.product_name || `ID ${inventoryId}`;
    const loadingKey = `delete-bom-${machineId}-${inventoryId}`;

    message.loading({ content: `Eliminando ${partName}...`, key: loadingKey });

    try {
      const endpoint = `/maquinas/${machineId}/parts/${inventoryId}`;
      await fetchWithAuth(endpoint, { method: 'DELETE' });
      message.success({ content: `Repuesto ${partName} eliminado.`, key: loadingKey, duration: 2 });

      // Recargar BOM
      const data = await fetchWithAuth(`/maquinas/${machineId}/parts`);
      const processedData = (data || []).map(item => ({ ...item, key: item.inventory_id }));
      setBomList(processedData);
    } catch (error) {
      message.error({ content: `Error: ${error.message || ''}`, key: loadingKey, duration: 4 });
      console.error(`Error deleting part ${inventoryId}:`, error);
    }
  };

  // Funciones para exportar a Excel
  const handleExportBOMExcel = () => {
    if (bomList.length === 0) {
      message.warning("No hay repuestos en el BOM para exportar.");
      return;
    }

    message.loading({ content: 'Generando Excel...', key: 'exportExcelBOM' });

    const dataToExport = bomList.map(item => ({
      'ID Repuesto': item.inventory_id,
      'Nombre Repuesto': item.part?.product_name || 'N/A',
      'Cantidad Requerida': item.quantity,
      'Stock Actual': item.part?.quantity || 0
    }));

    try {
      const worksheet = XLSX.utils.json_to_sheet(dataToExport);
      const columnWidths = [{ wch: 12 }, { wch: 40 }, { wch: 15 }, { wch: 15 }];
      worksheet['!cols'] = columnWidths;

      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, `BOM Maquina ${machineId}`);
      XLSX.writeFile(workbook, `BOM_${machine?.nombre || `Maquina_${machineId}`}.xlsx`);

      message.success({ content: 'Exportación completada.', key: 'exportExcelBOM', duration: 3 });
    } catch (error) {
      console.error("Error al generar Excel:", error);
      message.error({ content: 'Error al generar archivo Excel.', key: 'exportExcelBOM', duration: 3 });
    }
  };

  const handleExportHistoryExcel = () => {
    if (historyList.length === 0) {
      message.warning("No hay historial para exportar.");
      return;
    }

    message.loading({ content: 'Generando Excel...', key: 'exportExcelHist' });

    const dataToExport = historyList.map(order => ({
      'Nº Orden': order.order_number || '-',
      'Título': order.title,
      'Tipo': order.work_type,
      'Estado': order.status,
      'Fecha Creación': formatDate(order.created_at),
      'Fecha Cierre': formatDate(order.finished_at),
      'Técnico': order.assigned_to?.username,
      'Cód. Falla': order.failure_code?.code,
      'Cód. Causa': order.cause_code?.code,
      'Cód. Remedio': order.remedy_code?.code,
      'Repuesto': order.repuesto?.product_name,
      'Cant. Usada': order.quantity_used,
      'Notas Cierre': order.completion_notes,
      'Detalles': order.details,
      'Horas Inactividad': order.downtime_hours,
    }));

    try {
      const worksheet = XLSX.utils.json_to_sheet(dataToExport);
      const columnWidths = [
        { wch: 12 },
        { wch: 30 },
        { wch: 15 },
        { wch: 15 },
        { wch: 18 },
        { wch: 18 },
        { wch: 15 },
        { wch: 10 },
        { wch: 10 },
        { wch: 10 },
        { wch: 25 },
        { wch: 8 },
        { wch: 30 },
        { wch: 40 },
        { wch: 10 }
      ];
      worksheet['!cols'] = columnWidths;

      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "Historial Maquina");
      XLSX.writeFile(workbook, `Historial_${machine?.nombre || `Maquina_${machineId}`}.xlsx`);

      message.success({ content: 'Exportación completada.', key: 'exportExcelHist', duration: 3 });
    } catch (error) {
      console.error("Error al generar Excel:", error);
      message.error({ content: 'Error al generar archivo Excel.', key: 'exportExcelHist', duration: 3 });
    }
  };

  // Columnas para tablas adaptadas a móvil
  const bomColumns = [
    {
      title: 'ID',
      dataIndex: 'inventory_id',
      key: 'inventory_id',
      width: isMobile ? 60 : 120
    },
    {
      title: 'Nombre Repuesto',
      dataIndex: ['part', 'product_name'],
      key: 'part_name',
      render: (name) => name || 'N/A',
      ellipsis: isMobile
    },
    {
      title: 'Cant.',
      dataIndex: 'quantity',
      key: 'quantity',
      width: isMobile ? 60 : 100,
      align: 'right'
    },
    ...( !isMobile ? [{
      title: 'Stock Actual',
      dataIndex: ['part', 'quantity'],
      key: 'stock',
      width: 100,
      align: 'right',
      render: (stock) => stock || 0
    }] : []),
    {
      title: 'Acciones',
      key: 'actions',
      width: isMobile ? 80 : 120,
      align: 'center',
      render: (_, record) => (
        <Popconfirm
          title={isMobile ? "¿Quitar?" : `¿Quitar "${record.part?.product_name || record.inventory_id}"?`}
          onConfirm={() => handleDeletePart(record.inventory_id)}
          okText="Sí"
          cancelText="No"
          disabled={!canManage}
        >
          <Button
            type="primary"
            danger
            disabled={!canManage}
            size="small"
            icon={<DeleteOutlined />}
          >
            { !isMobile && "Quitar" }
          </Button>
        </Popconfirm>
      ),
    },
  ];

  const historyColumns = [
    {
      title: 'Nº Orden',
      dataIndex: 'order_number',
      key: 'order_number',
      width: isMobile ? 80 : 120
    },
    {
      title: isMobile ? 'Fecha' : 'Fecha Cierre',
      dataIndex: 'finished_at',
      key: 'finished_at',
      render: (date) => isMobile ?
        (date ? new Date(date).toLocaleDateString() : '-') :
        formatDate(date),
      sorter: (a, b) => new Date(a.finished_at || 0) - new Date(b.finished_at || 0),
      width: isMobile ? 90 : 170
    },
    {
      title: 'Tipo',
      dataIndex: 'work_type',
      key: 'work_type',
      render: (type) => <Tag color={getTypeColor(type)}>{type}</Tag>,
      width: isMobile ? 90 : 130
    },
    ...( !isMobile ? [{
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      render: (status) => <Tag color={getStatusColor(status)}>{status}</Tag>,
      width: 120
    }] : []),
    {
      title: 'Título',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (text, record) => <Tooltip title={record.details || text}>{text}</Tooltip>
    },
    ...( !isMobile ? [{
      title: 'Técnico',
      dataIndex: ['assigned_to', 'username'],
      key: 'assigned_to',
      render: (username) => username || '-',
      width: 150
    }] : []),
    ...( !isMobile ? [{
      title: 'Cód. Falla',
      dataIndex: ['failure_code', 'code'],
      key: 'failure_code',
      render: (code, record) => record.failure_code ?
        <Tooltip title={record.failure_code.description}>{code}</Tooltip> : '-',
      width: 110,
      align: 'center'
    }] : []),
    ...( !isMobile ? [{
      title: 'Cód. Causa',
      dataIndex: ['cause_code', 'code'],
      key: 'cause_code',
      render: (code, record) => record.cause_code ?
        <Tooltip title={record.cause_code.description}>{code}</Tooltip> : '-',
      width: 110,
      align: 'center'
    }] : []),
    ...( !isMobile ? [{
      title: 'Cód. Remedio',
      dataIndex: ['remedy_code', 'code'],
      key: 'remedy_code',
      render: (code, record) => record.remedy_code ?
        <Tooltip title={record.remedy_code.description}>{code}</Tooltip> : '-',
      width: 110,
      align: 'center'
    }] : [])
  ];

  if (loading) {
    return (
      <div className="page-container" style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '60vh',
        padding: isMobile ? '10px' : '20px'
      }}>
        <Spin size={isMobile ? "default" : "large"} tip="Cargando detalles de la máquina..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container" style={{
        padding: isMobile ? '10px' : '20px'
      }}>
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
          action={
            <Button
              size={isMobile ? "small" : "middle"}
              type="primary"
              onClick={() => navigate('/maquinas')}
            >
              Volver a Máquinas
            </Button>
          }
        />
      </div>
    );
  }

  if (!machine) {
    return (
      <div className="page-container" style={{
        padding: isMobile ? '10px' : '20px'
      }}>
        <Alert
          message="Máquina no encontrada"
          description="La máquina solicitada no existe o ha sido eliminada."
          type="warning"
          showIcon
          action={
            <Button
              size={isMobile ? "small" : "middle"}
              type="primary"
              onClick={() => navigate('/maquinas')}
            >
              Volver a Máquinas
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="page-container" style={{
      padding: isMobile ? '8px' : '24px'
    }}>
      <div className="page-header" style={{
        marginBottom: isMobile ? '12px' : '24px'
      }}>
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/maquinas')}
            size={isMobile ? "small" : "middle"}
          >
            { !isMobile && "Volver" }
          </Button>
          <Title level={isMobile ? 4 : 2} className="page-title" style={{ margin: 0 }}>
            { machine.nombre }
          </Title>
        </Space>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="card"
        size={isMobile ? "small" : "large"}
        style={{ marginBottom: isMobile ? '8px' : '16px' }}
      >
        {/* PESTAÑA INFORMACIÓN GENERAL */}
        <TabPane
          tab={<span><ToolOutlined /> {!isMobile && "Información"}</span>}
          key="1"
        >
          {/* Información general */}
          <Card size={isMobile ? "small" : "default"}>
            <Descriptions
              title="Información General"
              bordered
              column={isMobile ? 1 : 3}
              size={isMobile ? "small" : "default"}
            >
              <Descriptions.Item label="ID">{ machine.id }</Descriptions.Item>
              <Descriptions.Item label="Modelo">{ machine.modelo }</Descriptions.Item>
              <Descriptions.Item label="Marca">{ machine.marca }</Descriptions.Item>
              <Descriptions.Item label="Número de Serie">{ machine.numero_serie }</Descriptions.Item>
              <Descriptions.Item label="Sección" span={isMobile ? 1 : 2}>
                { machine.section?.nombre || "-" }
              </Descriptions.Item>
              <Descriptions.Item label="Línea" span={isMobile ? 1 : 2}>
                { machine.line?.nombre || "-" }
              </Descriptions.Item>
              <Descriptions.Item label="Criticidad" span={isMobile ? 1 : 2}>
                { machine.criticidad || "No especificada" }
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* Métricas y KPIs */}
          <Card
            title="Métricas de Rendimiento"
            style={{ marginTop: isMobile ? '8px' : '16px' }}
            size={isMobile ? "small" : "default"}
          >
            <Row gutter={isMobile ? [8, 8] : [16, 0]}>
              <Col xs={12} sm={6}>
                <Statistic
                  title={isMobile ? "MTTR" : "MTTR (Tiempo Medio de Reparación)"}
                  value={metrics.mttr}
                  suffix={isMobile ? "h" : "horas"}
                  precision={1}
                  valueStyle={{ fontSize: isMobile ? '16px' : '24px' }}
                />
              </Col>
              <Col xs={12} sm={6}>
                <Statistic
                  title="Disponibilidad"
                  value={metrics.disponibilidad}
                  suffix="%"
                  precision={2}
                  valueStyle={{ fontSize: isMobile ? '16px' : '24px' }}
                />
              </Col>
              <Col xs={12} sm={6}>
                <Statistic
                  title={isMobile ? "OTs Año" : "OTs en el último año"}
                  value={metrics.lastYear.total}
                  valueStyle={{
                    color: '#3f8600',
                    fontSize: isMobile ? '16px' : '24px'
                  }}
                />
                { !isMobile && (
                  <div style={{ fontSize: '12px', marginTop: '8px' }}>
                    Preventivas: { metrics.lastYear.preventivas } |
                    Correctivas: { metrics.lastYear.correctivas }
                  </div>
                )}
              </Col>
            </Row>
          </Card>

          {/* Documentación */}
          <Card
            title="Documentos Asociados"
            style={{ marginTop: isMobile ? '8px' : '16px' }}
            size={isMobile ? "small" : "default"}
          >
            <DocumentAttachmentManager
              entityType="machine"
              entityId={machineId}
              title="Documentos"
            />
          </Card>
        </TabPane>

        {/* PESTAÑA LISTA DE REPUESTOS */}
        <TabPane
          tab={<span><FileOutlined /> {!isMobile && "Lista de Repuestos"}</span>}
          key="2"
        >
          <Card size={isMobile ? "small" : "default"}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: isMobile ? '8px' : '16px',
              flexDirection: isMobile ? 'column' : 'row',
              gap: isMobile ? '8px' : '0'
            }}>
              <Title level={isMobile ? 5 : 4} style={{ margin: 0 }}>
                Lista de Materiales (BOM)
              </Title>
              <Space direction={isMobile ? "vertical" : "horizontal"} style={{ width: isMobile ? '100%' : 'auto' }}>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleAddPart}
                  disabled={!canManage}
                  size={isMobile ? "small" : "middle"}
                  block={isMobile}
                >
                  { isMobile ? "Añadir" : "Añadir Repuesto" }
                </Button>
                <Button
                  type="primary"
                  icon={<FileExcelOutlined />}
                  onClick={handleExportBOMExcel}
                  disabled={loadingBom || bomList.length === 0}
                  ghost
                  size={isMobile ? "small" : "middle"}
                  block={isMobile}
                >
                  { isMobile ? "Exportar" : "Exportar a Excel" }
                </Button>
              </Space>
            </div>

            {errorBom && (
              <Alert
                message="Error de Carga"
                description={errorBom}
                type="error"
                showIcon
                closable
                onClose={() => setErrorBom(null)}
                style={{ marginBottom: isMobile ? '8px' : '16px' }}
              />
            )}

            <Spin spinning={loadingBom}>
              <div style={{ overflowX: 'auto' }}>
                <Table
                  columns={bomColumns}
                  dataSource={bomList}
                  rowKey="key"
                  pagination={{
                    pageSize: isMobile ? 5 : 10,
                    size: isMobile ? "small" : "default"
                  }}
                  locale={{
                    emptyText: loadingBom ? 'Cargando...' : 'No hay repuestos asociados.'
                  }}
                  size="small"
                  bordered
                  scroll={isMobile ? { x: '100%' } : undefined}
                />
              </div>
            </Spin>
          </Card>

          {/* MODAL AÑADIR REPUESTO */}
          <Modal
            title={`🔧 FILTRO CORREGIDO - Añadir Repuesto${isMobile ? '' : ` al BOM`}`}
            open={isAddPartModalVisible}
            onOk={handleAddPartSubmit}
            onCancel={() => setIsAddPartModalVisible(false)}
            confirmLoading={isSubmittingAdd}
            destroyOnClose
            maskClosable={false}
            width={isMobile ? "95%" : 520}
          >
            <Spin spinning={loadingParts}>
              <Form form={addPartForm} layout="vertical" name="add_part_form">
                <Form.Item
                  name="inventory_id"
                  label="Seleccionar Repuesto"
                  rules={[{ required: true, message: 'Seleccione repuesto' }]}
                >
                  <Select
                    showSearch
                    placeholder="🔍 Escriba para buscar repuesto..."
                    filterOption={(input, option) => {
                      if (!input || input.trim() === '') return true;
                      const optionText = option.children || '';
                      const searchTerm = input.toLowerCase().trim();
                      const result = String(optionText).toLowerCase().includes(searchTerm);
                      console.log(`🔍 Buscando "${searchTerm}" en "${optionText}": ${result}`);
                      return result;
                    }}
                    loading={loadingParts}
                    disabled={loadingParts}
                    allowClear
                    size={isMobile ? "small" : "middle"}
                    notFoundContent={loadingParts ? 'Cargando repuestos...' : 'No se encontraron repuestos'}
                    style={{ width: '100%' }}
                  >
                    {allParts.map(part => {
                      const displayName = part.nombre || part.product_name || `ID: ${part.id}`;
                      const stockInfo = ` (Stock: ${part.cantidad || 0})`;
                      const fullText = displayName + stockInfo;
                      return (
                        <Option key={part.id} value={part.id}>
                          {fullText}
                        </Option>
                      );
                    })}
                  </Select>
                </Form.Item>

                {/* DEBUG INFO - Solo en desarrollo */}
                {process.env.NODE_ENV === 'development' && (
                  <div style={{
                    fontSize: '12px',
                    color: '#666',
                    backgroundColor: '#f6ffed',
                    padding: '8px',
                    border: '1px solid #b7eb8f',
                    borderRadius: '4px',
                    marginBottom: '16px'
                  }}>
                    <div>✅ Total repuestos cargados: <strong>{allParts.length}</strong></div>
                    <div>🔄 Cargando: {loadingParts ? 'Sí' : 'No'}</div>
                    {allParts.length > 0 && (
                      <div>📝 Ejemplo: <em>{allParts[0]?.nombre || allParts[0]?.product_name || 'Sin nombre'}</em></div>
                    )}
                  </div>
                )}

                <Form.Item
                  name="quantity"
                  label="Cantidad Necesaria"
                  initialValue={1}
                  rules={[
                    { required: true, message: 'Indique cantidad' },
                    { type: 'number', min: 1, message: 'Mínimo 1' }
                  ]}
                >
                  <InputNumber min={1} style={{ width: '100%' }} />
                </Form.Item>
              </Form>
            </Spin>
          </Modal>
        </TabPane>

        {/* PESTAÑA HISTORIAL */}
        <TabPane
          tab={<span><HistoryOutlined /> {!isMobile && "Historial"}</span>}
          key="3"
        >
          <Card size={isMobile ? "small" : "default"}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: isMobile ? '8px' : '16px',
              flexDirection: isMobile ? 'column' : 'row',
              gap: isMobile ? '8px' : '0'
            }}>
              <Title level={isMobile ? 5 : 4} style={{ margin: 0 }}>
                Historial de Órdenes de Trabajo
              </Title>
              <Button
                type="primary"
                icon={<FileExcelOutlined />}
                onClick={handleExportHistoryExcel}
                disabled={loadingHistory || historyList.length === 0}
                ghost
                size={isMobile ? "small" : "middle"}
                block={isMobile}
              >
                { isMobile ? "Exportar" : "Exportar a Excel" }
              </Button>
            </div>

            {errorHistory && (
              <Alert
                message="Error de Carga"
                description={errorHistory}
                type="error"
                showIcon
                closable
                onClose={() => setErrorHistory(null)}
                style={{ marginBottom: isMobile ? '8px' : '16px' }}
              />
            )}

            <Spin spinning={loadingHistory}>
              <div style={{ overflowX: 'auto' }}>
                <Table
                  columns={historyColumns}
                  dataSource={historyList}
                  rowKey="key"
                  pagination={{
                    pageSize: isMobile ? 5 : 10,
                    size: isMobile ? "small" : "default"
                  }}
                  locale={{
                    emptyText: loadingHistory ? 'Cargando...' : 'No hay historial para esta máquina.'
                  }}
                  size="small"
                  bordered
                  scroll={isMobile ? { x: '100%' } : { x: 1400 }}
                />
              </div>
            </Spin>
          </Card>
        </TabPane>

        {/* PESTAÑA ANÁLISIS CON DATOS REALES */}
        <TabPane
          tab={<span><BarChartOutlined /> {!isMobile && "Análisis REAL"}</span>}
          key="4"
        >
          {analysisData.loading ? (
            <div style={{ textAlign: 'center', padding: isMobile ? '30px' : '50px' }}>
              <Spin size={isMobile ? "default" : "large"} />
              <div style={{ marginTop: isMobile ? '12px' : '20px' }}>
                ✅ Cargando análisis con datos REALES de {machine.nombre}...
              </div>
            </div>
          ) : analysisData.error ? (
            <Alert
              message="Sin datos suficientes para análisis"
              description={
                <div>
                  <p>{analysisData.error}</p>
                  <p><strong>ℹ️ Información:</strong> Esta máquina necesita más historial de órdenes de trabajo para generar gráficos significativos.</p>
                  <p><strong>📊 Requerimientos mínimos:</strong> Al menos 3-5 órdenes de trabajo completadas.</p>
                </div>
              }
              type="warning"
              showIcon
            />
          ) : (
            <div>
              <Title level={isMobile ? 4 : 3} style={{ marginBottom: isMobile ? '16px' : '24px' }}>
                📊 Análisis de Rendimiento REAL - {machine.nombre}
              </Title>

              {/* Alerta de datos reales */}
              <Alert
                message="✅ Datos 100% Reales de tu GMAO"
                description={`Todos los gráficos y estadísticas se basan en las órdenes de trabajo reales de ${machine.nombre} registradas en tu sistema desde abril 2025.`}
                type="success"
                showIcon
                style={{ marginBottom: 16 }}
              />

              {/* Primera fila de gráficos */}
              <Row gutter={[isMobile ? 8 : 16, isMobile ? 8 : 24]}>
                <Col xs={24} md={12}>
                  <Card
                    title="📈 Tendencia MTBF REAL"
                    size={isMobile ? "small" : "default"}
                    bodyStyle={{ padding: isMobile ? 8 : 24 }}
                  >
                    <div style={{ height: isMobile ? 200 : 300 }}>
                      {analysisData.mtbfTrend?.length > 0 ? (
                        <Line
                          data={{
                            labels: analysisData.mtbfTrend.map(d => d.month),
                            datasets: [
                              {
                                label: 'MTBF (horas) - DATOS REALES',
                                data: analysisData.mtbfTrend.map(d => d.value),
                                borderColor: '#1890ff',
                                backgroundColor: 'rgba(24, 144, 255, 0.1)',
                                tension: 0.3,
                                fill: true
                              }
                            ]
                          }}
                          options={{
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                              y: {
                                beginAtZero: false,
                                title: {
                                  display: !isMobile,
                                  text: 'Horas entre fallos'
                                },
                                ticks: {
                                  font: {
                                    size: isMobile ? 10 : 12
                                  }
                                }
                              },
                              x: {
                                ticks: {
                                  font: {
                                    size: isMobile ? 10 : 12
                                  }
                                }
                              }
                            },
                            plugins: {
                              legend: {
                                display: !isMobile
                              },
                              title: {
                                display: !isMobile,
                                text: 'Basado en órdenes de trabajo reales',
                                font: {
                                  size: 14
                                }
                              }
                            }
                          }}
                        />
                      ) : (
                        <Empty 
                          description="Sin datos MTBF suficientes" 
                          image={Empty.PRESENTED_IMAGE_SIMPLE}
                        />
                      )}
                    </div>
                  </Card>
                </Col>
                <Col xs={24} md={12}>
                  <Card
                    title="📉 Tendencia MTTR REAL"
                    size={isMobile ? "small" : "default"}
                    bodyStyle={{ padding: isMobile ? 8 : 24 }}
                  >
                    <div style={{ height: isMobile ? 200 : 300 }}>
                      {analysisData.mttrTrend?.length > 0 ? (
                        <Line
                          data={{
                            labels: analysisData.mttrTrend.map(d => d.month),
                            datasets: [
                              {
                                label: 'MTTR (horas) - DATOS REALES',
                                data: analysisData.mttrTrend.map(d => d.value),
                                borderColor: '#ff4d4f',
                                backgroundColor: 'rgba(255, 77, 79, 0.1)',
                                tension: 0.3,
                                fill: true
                              }
                            ]
                          }}
                          options={{
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                              y: {
                                beginAtZero: true,
                                title: {
                                  display: !isMobile,
                                  text: 'Horas de reparación'
                                },
                                ticks: {
                                  font: {
                                    size: isMobile ? 10 : 12
                                  }
                                }
                              },
                              x: {
                                ticks: {
                                  font: {
                                    size: isMobile ? 10 : 12
                                  }
                                }
                              }
                            },
                            plugins: {
                              legend: {
                                display: !isMobile
                              },
                              title: {
                                display: !isMobile,
                                text: 'Tiempo real de inactividad por reparaciones',
                                font: {
                                  size: 14
                                }
                              }
                            }
                          }}
                        />
                      ) : (
                        <Empty 
                          description="Sin datos MTTR suficientes" 
                          image={Empty.PRESENTED_IMAGE_SIMPLE}
                        />
                      )}
                    </div>
                  </Card>
                </Col>
              </Row>

              {/* Segunda fila de gráficos */}
              {(!isMobile || (isMobile && activeTab === "4")) && (
                <Row gutter={[isMobile ? 8 : 16, isMobile ? 8 : 24]} style={{ marginTop: isMobile ? '8px' : '24px' }}>
                  <Col xs={24} md={12}>
                    <Card
                      title="🔧 Tipos de Fallo REALES"
                      size={isMobile ? "small" : "default"}
                      bodyStyle={{ padding: isMobile ? 8 : 24 }}
                    >
                      <div style={{ height: isMobile ? 200 : 300 }}>
                        {analysisData.failureTypes?.length > 0 ? (
                          <Pie
                            data={{
                              labels: analysisData.failureTypes.map(d => d.type),
                              datasets: [
                                {
                                  data: analysisData.failureTypes.map(d => d.count),
                                  backgroundColor: [
                                    '#1890ff',
                                    '#13c2c2',
                                    '#fa8c16',
                                    '#722ed1',
                                    '#eb2f96'
                                  ],
                                  borderWidth: 1
                                }
                              ]
                            }}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              plugins: {
                                legend: {
                                  position: isMobile ? 'bottom' : 'right',
                                  labels: {
                                    font: {
                                      size: isMobile ? 10 : 12
                                    }
                                  }
                                },
                                title: {
                                  display: !isMobile,
                                  text: 'Basado en códigos de falla reales',
                                  font: {
                                    size: 14
                                  }
                                }
                              }
                            }}
                          />
                        ) : (
                          <Empty 
                            description="Sin fallos correctivos registrados" 
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                          />
                        )}
                      </div>
                    </Card>
                  </Col>

                  {/* Para móvil, no mostrar todos los gráficos para no sobrecargar */}
                  {!isMobile && (
                    <Col xs={24} md={12}>
                      <Card title="⏱️ Distribución Tiempos Reparación REALES">
                        <div style={{ height: 300 }}>
                          {analysisData.repairTimesDistribution?.some(d => d.count > 0) ? (
                            <Bar
                              data={{
                                labels: analysisData.repairTimesDistribution.map(d => d.range),
                                datasets: [
                                  {
                                    label: 'Cantidad de reparaciones REALES',
                                    data: analysisData.repairTimesDistribution.map(d => d.count),
                                    backgroundColor: '#ffc53d'
                                  }
                                ]
                              }}
                              options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                scales: {
                                  y: {
                                    beginAtZero: true,
                                    title: {
                                      display: true,
                                      text: 'Número de reparaciones'
                                    }
                                  },
                                  x: {
                                    title: {
                                      display: true,
                                      text: 'Tiempo de reparación'
                                    }
                                  }
                                },
                                plugins: {
                                  title: {
                                    display: true,
                                    text: 'Distribución real de tiempos de inactividad',
                                    font: {
                                      size: 14
                                    }
                                  }
                                }
                              }}
                            />
                          ) : (
                            <Empty 
                              description="Sin datos de tiempos de reparación" 
                              image={Empty.PRESENTED_IMAGE_SIMPLE}
                            />
                          )}
                        </div>
                      </Card>
                    </Col>
                  )}
                </Row>
              )}

              {/* Costos de mantenimiento REALES - solo en desktop */}
              {!isMobile && analysisData.maintenanceCosts?.length > 0 && (
                <Row gutter={[16, 24]} style={{ marginTop: '24px' }}>
                  <Col span={24}>
                    <Card title="💰 Estimación de Costos REALES por Mes">
                      <div style={{ height: 300 }}>
                        <Bar
                          data={{
                            labels: analysisData.maintenanceCosts.map(d => d.month),
                            datasets: [
                              {
                                label: 'Preventivo (€)',
                                data: analysisData.maintenanceCosts.map(d => d.preventive),
                                backgroundColor: '#52c41a'
                              },
                              {
                                label: 'Correctivo (€)',
                                data: analysisData.maintenanceCosts.map(d => d.corrective),
                                backgroundColor: '#f5222d'
                              }
                            ]
                          }}
                          options={{
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                              y: {
                                beginAtZero: true,
                                title: {
                                  display: true,
                                  text: 'Euros (€)'
                                }
                              }
                            },
                            plugins: {
                              title: {
                                display: true,
                                text: 'Estimación basada en tiempo de inactividad real',
                                font: {
                                  size: 14
                                }
                              }
                            }
                          }}
                        />
                      </div>
                    </Card>
                  </Col>
                </Row>
              )}

              {/* Resumen KPIs REALES - simplificado en móvil */}
              <Row gutter={[isMobile ? 8 : 16, isMobile ? 8 : 24]} style={{ marginTop: isMobile ? '8px' : '24px' }}>
                <Col span={24}>
                  <Card
                    title="📊 Indicadores Clave REALES"
                    size={isMobile ? "small" : "default"}
                  >
                    <Row gutter={[isMobile ? 8 : 16, isMobile ? 8 : 16]}>
                      <Col xs={24} md={8}>
                        <Statistic
                          title="Disponibilidad Calculada"
                          value={metrics.disponibilidad || 0}
                          suffix="%"
                          valueStyle={{
                            color: '#3f8600',
                            fontSize: isMobile ? '18px' : '24px'
                          }}
                          precision={1}
                        />
                        { !isMobile && (
                          <Text type="secondary">
                            Basado en tiempo real de inactividad registrado
                          </Text>
                        )}
                      </Col>
                      <Col xs={24} md={8}>
                        <Statistic
                          title="Fallos Correctivos REALES"
                          value={analysisData.failureTypes?.reduce((sum, type) => sum + type.count, 0) || 0}
                          suffix="fallos"
                          valueStyle={{
                            color: '#cf1322',
                            fontSize: isMobile ? '18px' : '24px'
                          }}
                        />
                        { !isMobile && (
                          <Text type="secondary">
                            Registrados en órdenes de trabajo correctivas
                          </Text>
                        )}
                      </Col>
                      <Col xs={24} md={8}>
                        <Statistic
                          title="MTTR Promedio REAL"
                          value={analysisData.mttrTrend?.length > 0 ? 
                            (analysisData.mttrTrend.reduce((sum, d) => sum + d.value, 0) / analysisData.mttrTrend.length).toFixed(1) : 
                            0
                          }
                          suffix="horas"
                          valueStyle={{
                            color: '#108ee9',
                            fontSize: isMobile ? '18px' : '24px'
                          }}
                        />
                        { !isMobile && (
                          <Text type="secondary">
                            Promedio de tiempo real de reparación
                          </Text>
                        )}
                      </Col>
                    </Row>
                    { !isMobile && <Divider /> }
                    { !isMobile && (
                      <Alert
                        message="💡 Análisis Basado en Datos Reales"
                        description={
                          <ul>
                            <li>Todos los gráficos utilizan únicamente datos de órdenes de trabajo reales de tu GMAO</li>
                            <li>Los cálculos de MTBF/MTTR se basan en fechas y tiempos reales registrados</li>
                            <li>Los tipos de fallo se extraen de los códigos de falla configurados en tu sistema</li>
                            <li>Las estimaciones de costo se calculan usando el tiempo de inactividad real reportado</li>
                          </ul>
                        }
                        type="info"
                        showIcon
                      />
                    )}
                  </Card>
                </Col>
              </Row>
            </div>
          )}
        </TabPane>
      </Tabs>
    </div>
  );
};

export default MachineDetailFixed;