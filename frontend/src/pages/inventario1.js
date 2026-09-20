// src/pages/Inventario.js (COMPLETO con Ordenamiento Alfabético y Paginación Corregida)
import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Modal, Form, Input, Select, message, Space, Spin, Alert, Typography, Popconfirm, Row, Col, Statistic, Card, Tag } from 'antd';
import { DeleteOutlined, EditOutlined, PlusOutlined, SearchOutlined, FileExcelOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import * as XLSX from 'xlsx';
import '../styles/CommonPage.css';

const { Title, Text } = Typography;
const { Option } = Select;

const Inventario = () => {
  const [inventario, setInventario] = useState({ items: [], total_value: 0 });
  const [loading, setLoading] = useState(true);
  // --- Estados para Modal "Donde se Usa" (Añadidos) ---
  const [usageModalVisible, setUsageModalVisible] = useState(false);
  const [partUsageData, setPartUsageData] = useState([]);
  const [loadingUsage, setLoadingUsage] = useState(false);
  const [viewingPart, setViewingPart] = useState(null);
  // ----------------------------------------------------

  // 🔧 ESTADO PARA PAGINACIÓN
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 15,
    showSizeChanger: true,
    showQuickJumper: true,
    pageSizeOptions: ['10', '15', '30', '50', '100'],
    showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} productos`,
  });

  // 🔧 FUNCIÓN PARA MANEJAR CAMBIOS EN LA PAGINACIÓN
  const handleTableChange = (pag, filters, sorter) => {
    console.log('Cambio en paginación inventario:', pag);
    setPagination({
      ...pagination,
      current: pag.current,
      pageSize: pag.pageSize,
    });
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      const data = await fetchWithAuth('/inventario');
      
      // Ordenar alfabéticamente por nombre del producto
      const sortedItems = (data?.items || [])
        .map(item => ({...item, key: item.id}))
        .sort((a, b) => (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' }));
      
      setInventario({
          items: sortedItems,
          total_value: data?.total_value || 0
      });
    } catch (error) {
      console.error('Error al cargar inventario:', error);
      message.error(`Error al cargar inventario: ${error.message || 'Error desconocido'}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // --- FUNCIÓN PARA MOSTRAR USO (Añadida) ---
  const handleShowUsage = useCallback(async (record) => {
      const partName = record.nombre || `ID ${record.id}`;
      console.log(`Mostrando uso para repuesto: ${partName} (ID: ${record.id})`);
      setViewingPart({ id: record.id, nombre: partName });
      setPartUsageData([]);
      setLoadingUsage(true);
      setUsageModalVisible(true);
      try {
          const usageData = await fetchWithAuth(`/inventory/${record.id}/usage`);
          setPartUsageData(usageData || []);
          console.log("Usage data received:", usageData);
          if (!usageData || usageData.length === 0) {
               message.info(`El repuesto "${partName}" no está actualmente asociado a ninguna máquina en el BOM.`);
          }
      } catch (error) {
           console.error("Error fetching usage data:", error);
           message.error(`Error al cargar datos de uso: ${error.message || 'Error desconocido'}`);
           setUsageModalVisible(false);
      } finally {
           setLoadingUsage(false);
      }
  }, []);
  // --------------------------------------

  // --- FUNCIÓN PARA EXPORTAR EXCEL (Añadida) ---
   const handleExportExcel = () => {
      console.log("Exportando inventario a Excel...");
      if (!inventario || inventario.items.length === 0) {
          message.warning("No hay datos de inventario para exportar.");
          return;
      }
      message.loading({ content: 'Generando Excel...', key: 'exportExcelInv' });
      const dataToExport = inventario.items.map(item => ({
          'ID': item.id,
          'Producto': item.nombre,
          'Cantidad': item.cantidad,
          'Almacén': item.almacen, // Ya viene como string de la API /inventario
          'Precio': item.precio === '****' ? 'No autorizado' : item.precio, // Manejar ocultación
          'Valor Total': item.valor_total === '****' ? 'No autorizado' : item.valor_total,
          'Proveedor': item.proveedor || '-',
      }));
      try {
          const worksheet = XLSX.utils.json_to_sheet(dataToExport);
          const columnWidths = [ { wch: 8 }, { wch: 35 }, { wch: 10 }, { wch: 20 }, { wch: 15 }, { wch: 15 }, { wch: 25 } ];
          worksheet['!cols'] = columnWidths;
          const workbook = XLSX.utils.book_new();
          XLSX.utils.book_append_sheet(workbook, worksheet, "Inventario");
          XLSX.writeFile(workbook, "Inventario_General.xlsx");
          message.success({ content: 'Exportación a Excel completada.', key: 'exportExcelInv', duration: 3 });
      } catch (error) {
          console.error("Error al generar Excel:", error);
          message.error({ content: 'Error al generar el archivo Excel.', key: 'exportExcelInv', duration: 3 });
      }
    };
  // --------------------------------------

  // --- Columnas (Añadida columna Acciones) ---
  const columns = [
    { 
      title: 'Producto', 
      dataIndex: 'nombre', 
      key: 'nombre', 
      defaultSortOrder: 'ascend',
      sorter: (a, b) => (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' })
    },
    { title: 'Cantidad', dataIndex: 'cantidad', key: 'cantidad', sorter: (a, b) => a.cantidad - b.cantidad, align: 'right' },
    { title: 'Almacén', dataIndex: 'almacen', key: 'almacen', render: (text) => text || '-', width: 150 }, // Usar 'almacen' que viene de la API
    { title: 'Precio (€)', dataIndex: 'precio', key: 'precio', render: (precio) => (precio === "****" ? precio : `${parseFloat(precio || 0).toFixed(2)}€`), align: 'right' }, // Asegurar formato número
    { title: 'Valor Total (€)', dataIndex: 'valor_total', key: 'valor_total', render: (valor) => (valor === "****" ? valor : `${parseFloat(valor || 0).toFixed(2)}€`), align: 'right' }, // Asegurar formato número
    { title: 'Proveedor', dataIndex: 'proveedor', key: 'proveedor', render: (proveedor) => proveedor || '-', },
    // --- COLUMNA ACCIONES AÑADIDA ---
    {
       title: 'Acciones', key: 'acciones', width: 100, align: 'center',
       render: (_, record) => (
         <Space>
           <Button icon={<SearchOutlined />} onClick={() => handleShowUsage(record)} size="small" title="Ver dónde se usa"/>
           {/* Aquí no hay Editar/Eliminar */}
         </Space>
       ),
     },
    // ----------------------------
  ];
  // --- Fin Columnas ---


  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2} className="page-title" style={{ marginBottom: 0 }}>Vista General de Inventario</Title>
         {/* --- BOTÓN EXPORTAR AÑADIDO --- */}
         <Button type="primary" icon={<FileExcelOutlined />} onClick={handleExportExcel} disabled={loading || !inventario || inventario.items.length === 0} ghost>
            Exportar a Excel
         </Button>
         {/* -------------------------- */}
      </div>

      {/* Estadísticas */}
      <Row gutter={[16, 16]} style={{ margin: '16px 0' }}>
        <Col xs={24} sm={12} md={8}>
          <Card bordered={false}><Statistic title="Items Diferentes" value={inventario.items.length} /></Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card bordered={false}><Statistic title="Valor Total Estimado" value={inventario.total_value === "****" ? "No autorizado" : inventario.total_value} precision={inventario.total_value === "****" ? 0 : 2} suffix={inventario.total_value === "****" ? "" : "€"} /></Card>
        </Col>
      </Row>

      {/* 🔧 TABLA DE INVENTARIO CON PAGINACIÓN CORREGIDA */}
      <Card className="table-container">
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={inventario.items} // Usar inventario.items
            loading={loading}
            rowKey="key" // Usar la key que añadimos
            pagination={pagination}
            onChange={handleTableChange}
            scroll={{ x: 'max-content' }} // Ajustar scroll
            size="small"
            bordered
          />
        </Spin>
      </Card>

       {/* --- MODAL PARA "DÓNDE SE USA" (AÑADIDO AL FINAL) --- */}
       <Modal
         title={viewingPart ? `Máquinas que usan: ${viewingPart.nombre} (ID: ${viewingPart.id})` : 'Cargando...'}
         open={usageModalVisible}
         onCancel={() => setUsageModalVisible(false)}
         footer={[ <Button key="back" onClick={() => setUsageModalVisible(false)}>Cerrar</Button> ]} // Añadir botón Cerrar
         width={600}
       >
         <Spin spinning={loadingUsage}>
           {partUsageData.length > 0 ? (
             <Table
               dataSource={partUsageData}
               rowKey={(record) => `${record.machine.id}-${viewingPart?.id}`} // Clave compuesta
               size="small"
               pagination={false}
               columns={[
                 { title: 'ID Máquina', dataIndex: ['machine', 'id'], key: 'machine_id' },
                 { title: 'Nombre Máquina', dataIndex: ['machine', 'nombre'], key: 'machine_name' },
                 { title: 'Cantidad Usada', dataIndex: 'quantity', key: 'quantity', align: 'right' },
               ]}
             />
           ) : (
             !loadingUsage && <Text>Este repuesto no está actualmente asociado a ninguna máquina en el BOM.</Text>
           )}
         </Spin>
       </Modal>
       {/* ----------------------------------- */}

    </div>
  );
};

export default Inventario;