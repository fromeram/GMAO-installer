// src/pages/MachineHistory.js (Versión Responsive)
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Typography, Breadcrumb, Table, Tag, Tooltip, Spin, Alert, message, Button, Space } from 'antd';
import { FileExcelOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import * as XLSX from 'xlsx';
import MobileLayout from '../components/MobileLayout';

const { Title, Text } = Typography;

const MachineHistory = () => {
  const { machineId } = useParams();
  const navigate = useNavigate();
  const [historyList, setHistoryList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [machineName, setMachineName] = useState('');
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

  // Funciones auxiliares
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      if (isMobile) {
        return new Date(dateString).toLocaleDateString('es-ES', {
          day: '2-digit',
          month: '2-digit',
          year: '2-digit'
        });
      }
      return new Date(dateString).toLocaleString('es-ES', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit'
      });
    } catch (e) {
      return dateString;
    }
  };

  const getStatusColor = (status) => {
    const colors = { 'Pendiente': 'gold', 'En curso': 'blue', 'En revisión': 'purple', 'Cerrada': 'green' };
    return colors[status] || 'default';
  };

  const getTypeColor = (type) => {
    const typeColors = { 
      'Preventivo': 'green', 'Correctivo': 'red', 'Inspección': 'blue', 
      'Mejora': 'cyan', 'Modificación': 'purple', 'Seguridad': 'orange' 
    };
    return typeColors[type] || 'default';
  };

  const fetchHistoryData = useCallback(async () => {
    setLoading(true);
    setError(null);
    console.log(`Fetching history for machine ID: ${machineId}`);
    try {
      // Primero, intentamos obtener los datos de la máquina para mostrar su nombre
      try {
        const machineData = await fetchWithAuth(`/maquinas/${machineId}`);
        if (machineData && machineData.nombre) {
          setMachineName(machineData.nombre);
        } else {
          setMachineName(`ID ${machineId}`);
        }
      } catch (machineError) {
        console.error("Error fetching machine name:", machineError);
        setMachineName(`ID ${machineId}`);
      }

      // Ahora cargamos el historial
      const data = await fetchWithAuth(`/maquinas/${machineId}/history`);
      const processedData = (data || []).map(item => ({ ...item, key: item.id }));
      setHistoryList(processedData);
      console.log('History data received:', processedData);
    } catch (err) {
      console.error("Error fetching history data:", err);
      const errorMsg = `Error cargando historial: ${err.message || 'Error desconocido'}`;
      setError(errorMsg);
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [machineId]);

  useEffect(() => {
    fetchHistoryData();
  }, [fetchHistoryData]);

  // Exportar a Excel
  const handleExportExcel = () => {
    console.log(`Exportando historial máquina ${machineId} a Excel...`);
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
        { wch: 12 }, { wch: 30 }, { wch: 15 }, { wch: 15 }, 
        { wch: 18 }, { wch: 18 }, { wch: 15 }, { wch: 10 }, 
        { wch: 10 }, { wch: 10 }, { wch: 25 }, { wch: 8 }, 
        { wch: 30 }, { wch: 40 }, { wch: 10 }
      ];
      worksheet['!cols'] = columnWidths;
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "Historial Maquina");
      XLSX.writeFile(workbook, `Historial_${machineName.replace(/\s+/g, '_') || `Maquina_${machineId}`}.xlsx`);
      message.success({ content: 'Exportación completada.', key: 'exportExcelHist', duration: 3 });
    } catch (error) {
      console.error("Error al generar Excel:", error);
      message.error({ content: 'Error al generar archivo Excel.', key: 'exportExcelHist', duration: 3 });
    }
  };

  // Columnas para la tabla de historial (versión escritorio)
  const desktopColumns = [
    { title: 'Nº Orden', dataIndex: 'order_number', key: 'order_number', width: 120 },
    { title: 'Fecha Cierre', dataIndex: 'finished_at', key: 'finished_at', render: formatDate, sorter: (a, b) => new Date(a.finished_at || 0) - new Date(b.finished_at || 0), width: 170 },
    { title: 'Tipo', dataIndex: 'work_type', key: 'work_type', render: (type) => <Tag color={getTypeColor(type)}>{type}</Tag>, width: 130 },
    { title: 'Estado', dataIndex: 'status', key: 'status', render: (status) => <Tag color={getStatusColor(status)}>{status}</Tag>, width: 120 },
    { title: 'Título / Descripción', dataIndex: 'title', key: 'title', ellipsis: true, render: (text, record) => <Tooltip title={record.details || text}>{text}</Tooltip> },
    { title: 'Técnico', dataIndex: ['assigned_to', 'username'], key: 'assigned_to', render: (username) => username || '-', width: 150 },
    { title: 'Cód. Falla', dataIndex: ['failure_code', 'code'], key: 'failure_code', render: (code, record) => record.failure_code ? <Tooltip title={record.failure_code.description}>{code}</Tooltip> : '-', width: 110, align: 'center' },
    { title: 'Cód. Causa', dataIndex: ['cause_code', 'code'], key: 'cause_code', render: (code, record) => record.cause_code ? <Tooltip title={record.cause_code.description}>{code}</Tooltip> : '-', width: 110, align: 'center' },
    { title: 'Cód. Remedio', dataIndex: ['remedy_code', 'code'], key: 'remedy_code', render: (code, record) => record.remedy_code ? <Tooltip title={record.remedy_code.description}>{code}</Tooltip> : '-', width: 110, align: 'center' },
  ];

  // Columnas para la tabla de historial (versión móvil)
  const mobileColumns = [
    {
      title: 'OT',
      dataIndex: 'order_number',
      key: 'order_number',
      width: 70,
      render: (text, record) => (
        <Link to={`/ordenes/${record.id}`}>
          {text ? text.split('-')[1] || text : `${record.id}`}
        </Link>
      )
    },
    {
      title: 'Información',
      dataIndex: 'title',
      key: 'info',
      render: (title, record) => (
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '13px', marginBottom: '4px' }}>
            {title.length > 40 ? `${title.substring(0, 40)}...` : title}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text style={{ fontSize: '12px', color: '#666' }}>
              {formatDate(record.finished_at)}
            </Text>
            <Space size={2}>
              <Tag color={getTypeColor(record.work_type)} style={{ fontSize: '10px', margin: 0, padding: '0 4px' }}>
                {record.work_type}
              </Tag>
              <Tag color={getStatusColor(record.status)} style={{ fontSize: '10px', margin: 0, padding: '0 4px' }}>
                {record.status}
              </Tag>
            </Space>
          </div>
        </div>
      )
    }
  ];

  // Contenido común para ambas versiones
  const historyContent = (
    <>
      {error && (
        <Alert 
          message="Error de Carga" 
          description={error} 
          type="error" 
          showIcon 
          closable 
          onClose={() => setError(null)} 
          style={{ marginBottom: isMobile ? 8 : 16 }} 
        />
      )}

      <Spin spinning={loading}>
        <Table 
          columns={isMobile ? mobileColumns : desktopColumns} 
          dataSource={historyList} 
          rowKey="key" 
          pagination={{ 
            pageSize: isMobile ? 10 : 15, 
            showSizeChanger: !isMobile, 
            pageSizeOptions: isMobile ? ['10'] : ['15', '30', '50'],
            size: isMobile ? "small" : "default"
          }} 
          locale={{ emptyText: loading ? 'Cargando...' : 'No hay historial para esta máquina.' }} 
          size="small" 
          bordered 
          scroll={isMobile ? { x: '100%' } : { x: 1400 }} 
        />
      </Spin>
    </>
  );

  // Versión móvil
  if (isMobile) {
    return (
      <MobileLayout 
        title={`Historial: ${machineName.substring(0, 20)}${machineName.length > 20 ? '...' : ''}`}
        onBack={() => navigate(-1)}
      >
        <div style={{ padding: '0 5px' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            marginBottom: 8 
          }}>
            <Text style={{ fontSize: '14px' }}>
              Historial de OTs
            </Text>
            <Button 
              icon={<FileExcelOutlined />} 
              onClick={handleExportExcel} 
              disabled={loading || historyList.length === 0} 
              size="small"
            />
          </div>

          {historyContent}
        </div>
      </MobileLayout>
    );
  }

  // Versión escritorio
  return (
    <div className="container mx-auto p-4">
      <Breadcrumb style={{ marginBottom: '16px' }}>
        <Breadcrumb.Item><Link to="/maquinas">Máquinas</Link></Breadcrumb.Item>
        <Breadcrumb.Item>Historial {machineName || `Máquina ID: ${machineId}`}</Breadcrumb.Item>
      </Breadcrumb>

      {/* Cabecera con Botón Exportar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} style={{ marginBottom: 0 }}>Historial OTs - {machineName || `Máquina ID: ${machineId}`}</Title>
        <Button 
          type="primary" 
          icon={<FileExcelOutlined />} 
          onClick={handleExportExcel} 
          disabled={loading || historyList.length === 0} 
          ghost
        >
          Exportar a Excel
        </Button>
      </div>

      {historyContent}
    </div>
  );
};

export default MachineHistory;