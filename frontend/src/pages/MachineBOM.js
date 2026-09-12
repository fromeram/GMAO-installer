// src/pages/MachineBOM.js (Versión Responsive con filtro corregido)
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Typography, Breadcrumb, Button, Table, Space, message, Spin, Alert, Popconfirm, Modal, Form, Select, InputNumber, AutoComplete, Input } from 'antd';
import { DeleteOutlined, PlusOutlined, FileExcelOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import * as XLSX from 'xlsx';
import MobileLayout from '../components/MobileLayout';

const { Title, Text } = Typography;
const { Option } = Select;

const MachineBOM = () => {
  const { machineId } = useParams();
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [bomList, setBomList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [machineName, setMachineName] = useState(''); // Nombre de la máquina
  const [isAddPartModalVisible, setIsAddPartModalVisible] = useState(false);
  const [allParts, setAllParts] = useState([]);
  const [loadingParts, setLoadingParts] = useState(false);
  const [isSubmittingAdd, setIsSubmittingAdd] = useState(false);
  const [addPartForm] = Form.useForm();
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  
  // Estados para búsqueda (como en Maquinas.js)
  const [searchOptions, setSearchOptions] = useState([]);
  const [searchValue, setSearchValue] = useState('');

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

  const canManage = currentUser?.role === "Administrador" || currentUser?.role === "Jefe de Mantenimiento";

  // Función para manejar búsqueda (basada en Maquinas.js)
  const handlePartSearch = (value) => {
    setSearchValue(value);
    
    if (!value) {
      setSearchOptions([]);
      return;
    }
    
    // Filtrar partes que coincidan con la búsqueda
    const matchingParts = allParts.filter(part => 
      (part.nombre?.toLowerCase().includes(value.toLowerCase()) || false) ||
      (part.product_name?.toLowerCase().includes(value.toLowerCase()) || false)
    );
    
    // Generar opciones para autocompletado
    const options = matchingParts.map(part => ({
      value: part.id,
      label: (
        <div>
          <strong>{part.nombre || part.product_name}</strong> - Stock: {part.cantidad}
        </div>
      ),
      part: part // Guardar referencia completa
    }));
    
    setSearchOptions(options);
  };

  // Carga de datos del BOM
  const fetchBomData = useCallback(async () => {
    setLoading(true);
    setError(null);
    console.log(`Fetching BOM for machine ID: ${machineId}`);
    try {
      const machineData = await fetchWithAuth(`/maquinas/${machineId}`);
      if (machineData && machineData.nombre) {
        setMachineName(machineData.nombre);
      }
      
      const data = await fetchWithAuth(`/maquinas/${machineId}/parts`);
      const processedData = (data || []).map(item => ({ ...item, key: item.inventory_id }));
      setBomList(processedData);
      console.log('BOM data received:', processedData);
    } catch (err) {
      console.error("Error fetching BOM data:", err);
      const errorMsg = `Error cargando BOM: ${err.message || 'Error desconocido'}`;
      setError(errorMsg);
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [machineId]);

  useEffect(() => {
    fetchBomData();
  }, [fetchBomData]);

  // Carga de todos los repuestos para el modal
  const fetchAllParts = async () => {
    if (allParts.length > 0) return;
    console.log('Fetching all parts...');
    setLoadingParts(true);
    try {
      const partsData = await fetchWithAuth('/productos');
      setAllParts(partsData || []);
      console.log('Available parts:', partsData);
    } catch (err) {
      console.error("Error fetching parts:", err);
      message.error(`Error cargando repuestos: ${err.message || ''}`);
    } finally {
      setLoadingParts(false);
    }
  };

  // Abrir modal añadir
  const handleAddPart = () => {
    addPartForm.resetFields();
    setSearchValue('');
    setSearchOptions([]);
    setIsAddPartModalVisible(true);
    fetchAllParts();
  };

  // Submit modal añadir
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
      fetchBomData();
    } catch (errorInfo) {
      console.error('Error add part:', errorInfo);
      message.error(`Error: ${errorInfo?.message || 'Revise campos'}`);
    } finally {
      setIsSubmittingAdd(false);
    }
  };

  // Eliminar parte del BOM
  const handleDeletePart = async (inventoryId) => {
    const partToDelete = bomList.find(item => item.inventory_id === inventoryId);
    const partName = partToDelete?.part?.product_name || `ID ${inventoryId}`;
    const loadingKey = `delete-bom-${machineId}-${inventoryId}`;
    message.loading({ content: `Eliminando ${isMobile ? '' : partName}...`, key: loadingKey });
    try {
      const endpoint = `/maquinas/${machineId}/parts/${inventoryId}`;
      await fetchWithAuth(endpoint, { method: 'DELETE' });
      message.success({
        content: `Repuesto ${isMobile ? '' : partName} eliminado.`,
        key: loadingKey,
        duration: 2
      });
      fetchBomData();
    } catch (error) {
      message.error({
        content: `Error: ${error.message || ''}`,
        key: loadingKey,
        duration: 4
      });
      console.error(`Error deleting part ${inventoryId}:`, error);
    }
  };

  // Exportar a Excel
  const handleExportExcel = () => {
    console.log(`Exportando BOM máquina ${machineId} a Excel...`);
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
      XLSX.writeFile(workbook, `BOM_Maquina_${machineId}.xlsx`);
      message.success({ content: 'Exportación completada.', key: 'exportExcelBOM', duration: 3 });
    } catch (error) {
      console.error("Error al generar Excel:", error);
      message.error({ content: 'Error al generar archivo Excel.', key: 'exportExcelBOM', duration: 3 });
    }
  };

  // Columnas tabla BOM
  const desktopColumns = [
    { title: 'ID Repuesto', dataIndex: 'inventory_id', key: 'inventory_id', width: 120 },
    { title: 'Nombre Repuesto', dataIndex: ['part', 'product_name'], key: 'part_name', render: (name) => name || 'N/A' },
    { title: 'Cantidad', dataIndex: 'quantity', key: 'quantity', width: 100, align: 'right' },
    { title: 'Stock Actual', dataIndex: ['part', 'quantity'], key: 'stock', width: 100, align: 'right', render: (stock) => stock || 0 },
    {
      title: 'Acciones',
      key: 'actions',
      width: 120,
      align: 'center',
      render: (_, record) => (
        <Popconfirm
          title={`¿Quitar "${record.part?.product_name || record.inventory_id}"?`}
          onConfirm={() => handleDeletePart(record.inventory_id)}
          okText="Sí"
          cancelText="No"
          disabled={!canManage}
        >
          <Button type="primary" danger disabled={!canManage} size="small" icon={<DeleteOutlined />}> Quitar </Button>
        </Popconfirm>
      ),
    },
  ];

  // Columnas móviles optimizadas
  const mobileColumns = [
    {
      title: 'Repuesto',
      dataIndex: ['part', 'product_name'],
      key: 'part_name',
      render: (name, record) => (
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '13px' }}>
            {name || 'N/A'}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            ID: {record.inventory_id}
          </div>
        </div>
      )
    },
    {
      title: 'Cant.',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 60,
      align: 'center',
      render: (quantity, record) => (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontWeight: 'bold' }}>{quantity}</div>
          <div style={{ fontSize: '11px', color: '#666' }}>
            Stock: {record.part?.quantity || 0}
          </div>
        </div>
      )
    },
    {
      title: '',
      key: 'actions',
      width: 50,
      align: 'center',
      render: (_, record) => (
        <Popconfirm
          title="¿Quitar repuesto?"
          onConfirm={() => handleDeletePart(record.inventory_id)}
          okText="Sí"
          cancelText="No"
          disabled={!canManage}
        >
          <Button type="primary" danger disabled={!canManage} size="small" icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  // ===============================
  // CONTENIDO DEL MODAL Y TABLAS
  // ===============================

  // Contenido compartido para ambas versiones
  const bomContent = (
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
          size={isMobile ? "small" : "middle"}
        />
      )}

      <Spin spinning={loading}>
        <Table
          columns={isMobile ? mobileColumns : desktopColumns}
          dataSource={bomList}
          rowKey="key"
          pagination={{ 
            pageSize: isMobile ? 10 : 15,
            size: isMobile ? "small" : "default"
          }}
          locale={{ 
            emptyText: loading ? 'Cargando...' : 'No hay repuestos asociados.' 
          }}
          size="small"
          bordered
          scroll={isMobile ? { x: '100%' } : undefined}
        />
      </Spin>

      {/* Modal Añadir Repuesto */}
      <Modal
        title={`🔧 MODAL MODIFICADO - Añadir Repuesto${isMobile ? '' : ` al BOM de Máquina ${machineId}`}`}
        open={isAddPartModalVisible}
        onOk={handleAddPartSubmit}
        onCancel={() => setIsAddPartModalVisible(false)}
        confirmLoading={isSubmittingAdd}
        destroyOnClose
        maskClosable={false}
        width={isMobile ? "95%" : 520}
      >
        <div style={{ backgroundColor: '#fff2e8', padding: '10px', marginBottom: '16px', border: '2px solid #ffa940' }}>
          <h3 style={{ color: '#d46b08', margin: 0 }}>🚨 ARCHIVO MODIFICADO CORRECTAMENTE</h3>
          <p style={{ margin: '5px 0 0 0' }}>Si ves este mensaje, estamos editando el archivo correcto</p>
        </div>
        <Spin spinning={loadingParts}>
          <Form form={addPartForm} layout="vertical" name="add_part_form">
            
            {/* =========== SELECTOR DE REPUESTOS =========== */}
            
            {/* SOLUCIÓN SIMPLIFICADA: Select con búsqueda mejorada */}
            <Form.Item
              name="inventory_id"
              label="Seleccionar Repuesto"
              rules={[{ required: true, message: 'Seleccione repuesto' }]}
            >
              <Select
                showSearch
                placeholder="Escriba para buscar repuesto..."
                filterOption={(input, option) => {
                  if (!input || input.trim() === '') return true;
                  
                  // Obtener el texto del Option
                  const optionText = option.children || '';
                  const searchTerm = input.toLowerCase().trim();
                  const result = String(optionText).toLowerCase().includes(searchTerm);
                  
                  console.log(`Buscando "${searchTerm}" en "${optionText}": ${result}`);
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
            
            {/* DEBUG: Mostrar información de depuración */}
            {process.env.NODE_ENV === 'development' && (
              <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
                <div>Total repuestos cargados: {allParts.length}</div>
                <div>Cargando: {loadingParts ? 'Sí' : 'No'}</div>
                {allParts.length > 0 && (
                  <div>Ejemplo: {allParts[0]?.nombre || allParts[0]?.product_name}</div>
                )}
              </div>
            )}
            
            {/* ============================================= */}

            <Form.Item
              name="quantity"
              label="Cantidad Necesaria"
              initialValue={1}
              rules={[
                { required: true, message: 'Indique cantidad' },
                { type: 'number', min: 1, message: 'Mínimo 1' }
              ]}
            >
              <InputNumber 
                min={1} 
                style={{ width: '100%' }} 
                size={isMobile ? "small" : "middle"}
              />
            </Form.Item>
          </Form>
        </Spin>
      </Modal>
    </>
  );

  // Versión móvil
  if (isMobile) {
    return (
      <MobileLayout 
        title={`BOM: ${machineName || `Máquina ${machineId}`}`}
        onBack={() => navigate(-1)}
      >
        <div style={{ padding: '0 5px' }}>
          {/* Botones acción */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            marginBottom: 8 
          }}>
            <Text style={{ fontSize: '14px' }}>
              Lista de Materiales
            </Text>
            <Space size="small">
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleAddPart}
                disabled={!canManage}
                size="small"
              />
              <Button
                icon={<FileExcelOutlined />}
                onClick={handleExportExcel}
                disabled={loading || bomList.length === 0}
                size="small"
              />
            </Space>
          </div>

          {bomContent}
        </div>
      </MobileLayout>
    );
  }

  // Versión escritorio
  return (
    <div className="container mx-auto p-4">
      <Breadcrumb style={{ marginBottom: '16px' }}>
        <Breadcrumb.Item><Link to="/maquinas">Máquinas</Link></Breadcrumb.Item>
        <Breadcrumb.Item>BOM {machineName || `Máquina ID: ${machineId}`}</Breadcrumb.Item>
      </Breadcrumb>

      {/* Cabecera con Botones Añadir y Exportar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
         <Title level={2} style={{ marginBottom: 0 }}>Lista de Materiales (BOM) - {machineName || `Máquina ID: ${machineId}`}</Title>
         <Space>
             <Button type="primary" icon={<PlusOutlined />} onClick={handleAddPart} disabled={!canManage}> Añadir Repuesto </Button>
             <Button type="primary" icon={<FileExcelOutlined />} onClick={handleExportExcel} disabled={loading || bomList.length === 0} ghost> Exportar a Excel </Button>
         </Space>
      </div>

      {bomContent}
    </div>
  );
};

export default MachineBOM;