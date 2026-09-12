// src/pages/GestionCodigos.js (Con Activar/Desactivar)
import React, { useState, useEffect } from 'react';
import { Tabs, Table, Button, Space, message, Spin, Typography, Popconfirm, Modal, Form, Alert, Switch, Radio } from 'antd';
import { useAuth } from '../contexts/AuthContext';
import { fetchWithAuth } from '../apiConfig';
import CodeForm from '../components/CodeForm';
import * as XLSX from 'xlsx';
import { FileExcelOutlined, PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const GestionCodigos = () => {
  const [failureCodes, setFailureCodes] = useState([]);
  const [causeCodes, setCauseCodes] = useState([]);
  const [remedyCodes, setRemedyCodes] = useState([]);
  const [loading, setLoading] = useState({ failure: true, cause: true, remedy: true });
  const [error, setError] = useState(null);
  const { currentUser } = useAuth();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [currentCodeType, setCurrentCodeType] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form] = Form.useForm();
  
  // Nuevo estado para filtrar por activo/inactivo
  const [filterStatus, setFilterStatus] = useState('active'); // 'active', 'inactive', 'all'

  const canManage = currentUser?.role === "Administrador" || currentUser?.role === "Jefe de Mantenimiento";

  const loadAllCodes = async () => {
    setLoading({ failure: true, cause: true, remedy: true });
    setError(null);
    try {
      const [failRes, causeRes, remedyRes] = await Promise.allSettled([
        fetchWithAuth('/failure-codes'), 
        fetchWithAuth('/cause-codes'), 
        fetchWithAuth('/remedy-codes')
      ]);
      
      if (failRes.status === 'fulfilled') setFailureCodes(failRes.value || []); 
      else throw failRes.reason;
      
      if (causeRes.status === 'fulfilled') setCauseCodes(causeRes.value || []); 
      else throw causeRes.reason;
      
      if (remedyRes.status === 'fulfilled') setRemedyCodes(remedyRes.value || []); 
      else throw remedyRes.reason;
    } catch (err) {
      const errorMsg = `Error cargando códigos: ${err?.message || 'Desconocido'}`;
      console.error(errorMsg, err); 
      setError(errorMsg); 
      message.error(errorMsg);
    } finally { 
      setLoading({ failure: false, cause: false, remedy: false }); 
    }
  };

  useEffect(() => { 
    loadAllCodes(); 
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAdd = (codeType) => {
    setEditingRecord(null); 
    setCurrentCodeType(codeType); 
    form.resetFields(); 
    // Establecer valor por defecto para active
    form.setFieldsValue({ active: true });
    setIsModalVisible(true);
  };
  
  const handleEdit = (record, codeType) => {
    setEditingRecord(record); 
    setCurrentCodeType(codeType); 
    setIsModalVisible(true);
  };
  
  const handleFormSubmit = async () => {
     setIsSubmitting(true);
     try {
         const values = await form.validateFields();
         const isEditing = !!editingRecord;
         let endpoint = '';
         const method = isEditing ? 'PUT' : 'POST';
         
         if (currentCodeType === 'Falla') endpoint = '/failure-codes';
         else if (currentCodeType === 'Causa') endpoint = '/cause-codes';
         else if (currentCodeType === 'Remedio') endpoint = '/remedy-codes';
         else throw new Error("Tipo desconocido");
         
         if (isEditing) endpoint += `/${editingRecord.id}`;
         
         await fetchWithAuth(endpoint, { 
           method, 
           headers: { 'Content-Type': 'application/json' }, 
           body: JSON.stringify(values) 
         });
         
         message.success(`Código ${isEditing ? 'actualizado' : 'creado'}.`); 
         setIsModalVisible(false); 
         loadAllCodes();
     } catch (errorInfo) {
         console.error('Error:', errorInfo); 
         message.error(`Error: ${errorInfo?.message || 'Revise campos'}`);
     } finally { 
         setIsSubmitting(false); 
     }
  };
  
  const handleDelete = async (record, codeType) => {
     const loadingKey = `deleteCode-${codeType}-${record.id}`; 
     message.loading({ content: `Eliminando...`, key: loadingKey });
     try {
         let endpoint = '';
         if (codeType === 'Falla') endpoint = `/failure-codes/${record.id}`;
         else if (codeType === 'Causa') endpoint = `/cause-codes/${record.id}`;
         else if (codeType === 'Remedio') endpoint = `/remedy-codes/${record.id}`;
         else throw new Error("Tipo desconocido");
         
         await fetchWithAuth(endpoint, { method: 'DELETE' });
         message.success({ content: `Código eliminado.`, key: loadingKey, duration: 2 }); 
         loadAllCodes();
     } catch (error) { 
         message.error({ content: `Error: ${error.message}`, key: loadingKey, duration: 4 }); 
         console.error(`Error eliminando:`, error); 
     }
  };

  // Nueva función para cambiar estado activo/inactivo
  // En GestionCodigos.js - Versión corregida de la función handleToggleActive

const handleToggleActive = async (record, codeType, newActiveState) => {
  const loadingKey = `toggleActive-${codeType}-${record.id}`;
  message.loading({ content: `${newActiveState ? 'Activando' : 'Desactivando'}...`, key: loadingKey });
  
  try {
    let endpoint = '';
    if (codeType === 'Falla') endpoint = `/failure-codes/${record.id}/set-active`;
    else if (codeType === 'Causa') endpoint = `/cause-codes/${record.id}/set-active`;
    else if (codeType === 'Remedio') endpoint = `/remedy-codes/${record.id}/set-active`;
    else throw new Error("Tipo desconocido");
    
    await fetchWithAuth(endpoint, { 
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify({ active: newActiveState }) 
    });
    
    message.success({ 
      content: `Código ${newActiveState ? 'activado' : 'desactivado'}.`, 
      key: loadingKey, 
      duration: 2 
    });
    
    // Actualizar la UI inmediatamente
    if (codeType === 'Falla') {
      setFailureCodes(failureCodes.map(code => 
        code.id === record.id ? {...code, active: newActiveState} : code
      ));
    } else if (codeType === 'Causa') {
      setCauseCodes(causeCodes.map(code => 
        code.id === record.id ? {...code, active: newActiveState} : code
      ));
    } else if (codeType === 'Remedio') {
      setRemedyCodes(remedyCodes.map(code => 
        code.id === record.id ? {...code, active: newActiveState} : code
      ));
    }
    
    loadAllCodes(); // También recargar para asegurarse
  } catch (error) {
    message.error({ 
      content: `Error: ${error.message}`, 
      key: loadingKey, 
      duration: 4 
    });
    console.error(`Error cambiando estado:`, error);
  }
};

  const handleExportExcel = (codeType) => {
    let data;
    let sheetName;
    let fileName;

    if (codeType === 'Falla') { 
      data = failureCodes; 
      sheetName = 'CodigosFalla'; 
      fileName = 'Codigos_Falla.xlsx'; 
    }
    else if (codeType === 'Causa') { 
      data = causeCodes; 
      sheetName = 'CodigosCausa'; 
      fileName = 'Codigos_Causa.xlsx'; 
    }
    else if (codeType === 'Remedio') { 
      data = remedyCodes; 
      sheetName = 'CodigosRemedio'; 
      fileName = 'Codigos_Remedio.xlsx'; 
    }
    else { 
      message.error("Tipo de código desconocido para exportar."); 
      return; 
    }

    // Filtrar según el estado actual si no es 'all'
    if (filterStatus !== 'all') {
      data = data.filter(item => 
        filterStatus === 'active' ? item.active : !item.active
      );
    }

    console.log(`Exportando Códigos de ${codeType} a Excel...`);
    if (!data || data.length === 0) { 
      message.warning(`No hay códigos de ${codeType} para exportar.`); 
      return; 
    }

    const loadingKey = `exportExcel-${codeType}`;
    message.loading({ content: 'Generando Excel...', key: loadingKey });

    const dataToExport = data.map(code => ({ 
        'ID': code.id,
        'Código': code.code,
        'Descripción': code.description,
        'Estado': code.active ? 'Activo' : 'Inactivo'
    }));

    try {
        const worksheet = XLSX.utils.json_to_sheet(dataToExport);
        const columnWidths = [{ wch: 8 }, { wch: 20 }, { wch: 50 }, { wch: 15 }];
        worksheet['!cols'] = columnWidths;
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
        XLSX.writeFile(workbook, fileName);
        message.success({ content: 'Exportación completada.', key: loadingKey, duration: 3 });
    } catch (error) {
        console.error("Error al generar Excel:", error);
        message.error({ content: 'Error al generar el archivo Excel.', key: loadingKey, duration: 3 });
    }
  };

  // Filtrar los datos según el estado seleccionado
  const getFilteredData = (data) => {
    if (filterStatus === 'all') return data;
    return data.filter(item => 
      filterStatus === 'active' ? item.active : !item.active
    );
  };

  const columns = (codeType) => [
     { 
       title: 'ID', 
       dataIndex: 'id', 
       key: 'id', 
       width: 80, 
       sorter: (a, b) => a.id - b.id 
     },
     { 
       title: 'Código', 
       dataIndex: 'code', 
       key: 'code', 
       sorter: (a, b) => a.code.localeCompare(b.code),
       render: (text, record) => (
         <span style={{ 
           textDecoration: !record.active ? 'line-through' : 'none',
           opacity: !record.active ? 0.5 : 1
         }}>
           {text}
         </span>
       )
     },
     { 
       title: 'Descripción', 
       dataIndex: 'description', 
       key: 'description', 
       ellipsis: true,
       render: (text, record) => (
         <span style={{ 
           textDecoration: !record.active ? 'line-through' : 'none',
           opacity: !record.active ? 0.5 : 1
         }}>
           {text}
         </span>
       )
     },
     { 
       title: 'Estado', 
       dataIndex: 'active', 
       key: 'active', 
       width: 100,
       render: (active, record) => (
         <Switch 
           checked={active} 
           onChange={(checked) => handleToggleActive(record, codeType, checked)}
           disabled={!canManage}
           checkedChildren="Activo" 
           unCheckedChildren="Inactivo"
         />
       )
     },
     { 
       title: 'Acciones', 
       key: 'actions', 
       width: 150, 
       align: 'center',
       render: (_, record) => ( 
         <Space size="middle">
           <Button 
             type="primary" 
             onClick={() => handleEdit(record, codeType)} 
             disabled={!canManage} 
             size="small" 
             icon={<EditOutlined />} 
           />
           <Popconfirm 
             title={`¿Eliminar código "${record.code}"?`} 
             onConfirm={() => handleDelete(record, codeType)} 
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
             />
           </Popconfirm>
         </Space> 
       ),
     },
  ];

  return (
    <div className="container mx-auto p-4">
      <Title level={2}>Gestión de Códigos</Title>
      {error && (
        <Alert 
          message="Error de Carga" 
          description={error} 
          type="error" 
          showIcon 
          closable 
          onClose={() => setError(null)} 
          style={{ marginBottom: 16 }} 
        />
      )}
      
      {/* Filtro por estado activo/inactivo */}
      <div style={{ marginBottom: 16 }}>
        <Radio.Group 
          value={filterStatus} 
          onChange={e => setFilterStatus(e.target.value)}
          optionType="button" 
          buttonStyle="solid"
        >
          <Radio.Button value="active">Activos</Radio.Button>
          <Radio.Button value="inactive">Inactivos</Radio.Button>
          <Radio.Button value="all">Todos</Radio.Button>
        </Radio.Group>
      </div>
      
      <Tabs defaultActiveKey="1">
        {/* Pestaña Fallas */}
        <TabPane tab="Códigos de Falla" key="1">
          <div style={{ marginBottom: 16, textAlign: 'right' }}>
             <Space>
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />} 
                  onClick={() => handleAdd('Falla')} 
                  disabled={!canManage}
                > 
                  Nuevo 
                </Button>
                <Button 
                  icon={<FileExcelOutlined />} 
                  onClick={() => handleExportExcel('Falla')} 
                  disabled={loading.failure || getFilteredData(failureCodes).length === 0}
                > 
                  Exportar 
                </Button>
             </Space>
          </div>
          <Spin spinning={loading.failure}>
            <Table 
              columns={columns('Falla')} 
              dataSource={getFilteredData(failureCodes)} 
              rowKey="id" 
              size="small" 
              bordered 
              pagination={{ pageSize: 30 }} 
            />
          </Spin>
        </TabPane>
        
        {/* Pestaña Causas */}
        <TabPane tab="Códigos de Causa" key="2">
           <div style={{ marginBottom: 16, textAlign: 'right' }}>
              <Space>
                 <Button 
                   type="primary" 
                   icon={<PlusOutlined />} 
                   onClick={() => handleAdd('Causa')} 
                   disabled={!canManage}
                 > 
                   Nuevo 
                 </Button>
                 <Button 
                   icon={<FileExcelOutlined />} 
                   onClick={() => handleExportExcel('Causa')} 
                   disabled={loading.cause || getFilteredData(causeCodes).length === 0}
                 > 
                   Exportar 
                 </Button>
              </Space>
           </div>
           <Spin spinning={loading.cause}>
             <Table 
               columns={columns('Causa')} 
               dataSource={getFilteredData(causeCodes)} 
               rowKey="id" 
               size="small" 
               bordered 
               pagination={{ pageSize: 30 }} 
             />
           </Spin>
        </TabPane>
        
        {/* Pestaña Remedios */}
        <TabPane tab="Códigos de Remedio" key="3">
            <div style={{ marginBottom: 16, textAlign: 'right' }}>
               <Space>
                  <Button 
                    type="primary" 
                    icon={<PlusOutlined />} 
                    onClick={() => handleAdd('Remedio')} 
                    disabled={!canManage}
                  > 
                    Nuevo 
                  </Button>
                  <Button 
                    icon={<FileExcelOutlined />} 
                    onClick={() => handleExportExcel('Remedio')} 
                    disabled={loading.remedy || getFilteredData(remedyCodes).length === 0}
                  > 
                    Exportar 
                  </Button>
                </Space>
            </div>
            <Spin spinning={loading.remedy}>
              <Table 
                columns={columns('Remedio')} 
                dataSource={getFilteredData(remedyCodes)} 
                rowKey="id" 
                size="small" 
                bordered 
                pagination={{ pageSize: 30 }} 
              />
            </Spin>
        </TabPane>
      </Tabs>
      
      {/* Modal Añadir/Editar */}
      <Modal 
        title={`${editingRecord ? 'Editar' : 'Nuevo'} Código de ${currentCodeType}`} 
        open={isModalVisible} 
        onOk={handleFormSubmit} 
        onCancel={() => setIsModalVisible(false)} 
        confirmLoading={isSubmitting} 
        destroyOnClose 
        maskClosable={false}
      >
         <CodeForm form={form} initialData={editingRecord} includeActive={true} />
      </Modal>
    </div>
  );
};

export default GestionCodigos;