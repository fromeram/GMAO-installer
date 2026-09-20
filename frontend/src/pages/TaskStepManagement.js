// src/pages/TaskStepManagement.js (Versión Completa y Revisada - Usa Concatenación para URL PUT)
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Typography, Breadcrumb, Button, Table, Space, message, Spin, Alert, Popconfirm, Modal, Form, Input, InputNumber, Card, Tag, Tooltip, Select } from 'antd'; // <-- Card y todos los demás necesarios
import { PlusOutlined, EditOutlined, DeleteOutlined, ArrowLeftOutlined, FileExcelOutlined } from '@ant-design/icons'; // Añadido FileExcelOutlined
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import * as XLSX from 'xlsx'; // Para exportar

const { Title, Text } = Typography;
const { TextArea } = Input;

// Funciones auxiliares de formato
const formatDate = (dateString) => {
    if (!dateString) return '-'; try { return new Date(dateString).toLocaleString('es-ES', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }); } catch (e) { return dateString; }
};
const getTypeColor = (type) => {
    const typeColors = { 'Preventivo': 'green', 'Correctivo': 'red', 'Inspección': 'blue', 'Mejora': 'cyan', 'Modificación': 'purple', 'Seguridad': 'orange' }; return typeColors[type] || 'default';
};
const getStatusColor = (status) => {
    const colors = { 'Pendiente': 'gold', 'En curso': 'blue', 'En revisión': 'purple', 'Cerrada': 'green' }; return colors[status] || 'default';
};

const TaskStepManagement = () => {
  const { listId } = useParams();
  console.log(">>> Task List ID recibido en TaskStepManagement:", listId); // Log inicial útil
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  const [taskListInfo, setTaskListInfo] = useState(null);
  const [stepsList, setStepsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Estados para el modal de pasos
  const [isStepModalVisible, setIsStepModalVisible] = useState(false);
  const [editingStepRecord, setEditingStepRecord] = useState(null); // Nombre correcto
  const [isSubmittingStep, setIsSubmittingStep] = useState(false);
  const [stepForm] = Form.useForm();

  const canManage = currentUser?.role === "Administrador" || currentUser?.role === "Jefe de Mantenimiento";

  // Cargar datos de la lista y sus pasos
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWithAuth(`/task-lists/${listId}`);
      setTaskListInfo(data);
      setStepsList((data?.steps || []).map(step => ({ ...step, key: step.id })));
    } catch (err) {
      console.error("Error fetching task list details:", err);
      setError(`Error al cargar detalles: ${err.message || 'Desconocido'}`);
      message.error(`Error al cargar detalles: ${err.message || 'Desconocido'}`);
    } finally {
      setLoading(false);
    }
  }, [listId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // --- Handlers para CRUD de Pasos ---
  const handleAddStep = () => {
      setEditingStepRecord(null); // Correcto
      const nextOrder = stepsList.length > 0 ? Math.max(...stepsList.map(s => s.step_order)) + 10 : 10;
      stepForm.resetFields();
      stepForm.setFieldsValue({ step_order: nextOrder });
      setIsStepModalVisible(true);
  };

  const handleEditStep = (record) => {
      setEditingStepRecord(record); // Correcto
      stepForm.setFieldsValue(record);
      setIsStepModalVisible(true);
  };

  const handleDeleteStep = async (stepId) => {
     const stepToDelete = stepsList.find(s => s.id === stepId);
     const loadingKey = `deleteStep-${stepId}`;
     message.loading({ content: `Eliminando paso ${stepToDelete?.step_order || stepId}...`, key: loadingKey });
     try {
         const listIdNum = parseInt(listId, 10);
         const stepIdNum = parseInt(stepId, 10);
         if (isNaN(listIdNum) || isNaN(stepIdNum)) { throw new Error("IDs inválidos para URL DELETE"); }
         const endpoint = `/task-lists/${listIdNum}/steps/${stepIdNum}`; // URL corregida
         await fetchWithAuth(endpoint, { method: 'DELETE' });
         message.success({ content: 'Paso eliminado.', key: loadingKey, duration: 2 });
         loadData();
     } catch (error) {
         message.error({ content: `Error: ${error.message || 'No se pudo eliminar'}`, key: loadingKey, duration: 4 });
         console.error("Delete step error:", error);
     }
  };

  const handleStepModalSubmit = async () => {
     setIsSubmittingStep(true);
     try {
         const values = await stepForm.validateFields();
         const isEditing = !!editingStepRecord; // Correcto
         let url = '';
         const method = isEditing ? 'PUT' : 'POST';

         const listIdNum = parseInt(listId, 10);
         if (isNaN(listIdNum)) { throw new Error("listId inválido"); }

         if (isEditing) {
             const stepId = editingStepRecord?.id; // Correcto
             const stepIdNum = parseInt(stepId, 10);
             if (isNaN(stepIdNum)) { throw new Error("stepId inválido para PUT"); }
             // --- USAR CONCATENACIÓN EN LUGAR DE PLANTILLA ---
             url = '/task-lists/' + listIdNum + '/steps/' + stepIdNum;
             // ---------------------------------------------
         } else {
             url = `/task-lists/${listIdNum}/steps`; // Esta ya estaba bien
         }

         const payload = { ...values };
         console.log(`Enviando ${method} a URL: ${url} con Payload:`, payload); // Log URL corregido

         await fetchWithAuth(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });

         message.success(`Paso ${isEditing ? 'actualizado' : 'añadido'} correctamente.`); // Correcto
         setIsStepModalVisible(false);
         loadData();

     } catch (errorInfo) {
         console.error('Error guardando paso:', errorInfo);
         if (errorInfo instanceof Error) { message.error(`Error: ${errorInfo.message}`); }
         else { message.error('Revise los campos del formulario.'); }
     } finally {
         setIsSubmittingStep(false);
     }
  };
  // --- Fin Handlers ---

  // --- Función Exportar Pasos (Opcional) ---
  const handleExportStepsExcel = () => {
      if (stepsList.length === 0) { message.warning("No hay pasos para exportar."); return; }
      const loadingKey = `exportExcelSteps-${listId}`;
      message.loading({ content: 'Generando Excel...', key: loadingKey });
      const dataToExport = stepsList.map(step => ({
          'Orden': step.step_order,
          'Descripción': step.description,
          'Tiempo Estimado (min)': step.estimated_time_minutes || '-',
      }));
      try {
          const worksheet = XLSX.utils.json_to_sheet(dataToExport);
          const columnWidths = [ { wch: 8 }, { wch: 60 }, { wch: 20 } ];
          worksheet['!cols'] = columnWidths;
          const workbook = XLSX.utils.book_new();
          XLSX.utils.book_append_sheet(workbook, worksheet, `Pasos Lista ${listId}`);
          XLSX.writeFile(workbook, `Pasos_Lista_${taskListInfo?.name || listId}.xlsx`);
          message.success({ content: 'Exportación completada.', key: loadingKey, duration: 3 });
      } catch (error) {
          console.error("Error al generar Excel:", error);
          message.error({ content: 'Error al generar archivo Excel.', key: loadingKey, duration: 3 });
      }
  };
  // ---------------------------------------

  // --- Columnas Tabla Pasos ---
  const columns = [ /* ... (Sin cambios) ... */
      { title: 'Orden', dataIndex: 'step_order', key: 'step_order', width: 100, sorter: (a, b) => a.step_order - b.step_order },
      { title: 'Descripción del Paso', dataIndex: 'description', key: 'description' },
      { title: 'Tiempo Est. (min)', dataIndex: 'estimated_time_minutes', key: 'estimated_time_minutes', width: 150, align: 'right', render: (mins) => mins ?? '-' }, // Usar ?? por si es 0
      { title: 'Acciones', key: 'actions', width: 150, align: 'center',
        render: (_, record) => (
          <Space>
            <Button type="primary" icon={<EditOutlined />} onClick={() => handleEditStep(record)} disabled={!canManage} size="small" title="Editar Paso"/>
            <Popconfirm title={`¿Eliminar paso ${record.step_order}?`} onConfirm={() => handleDeleteStep(record.id)} okText="Sí" cancelText="No" okType="danger" disabled={!canManage}>
               <Button type="primary" danger icon={<DeleteOutlined />} disabled={!canManage} size="small" title="Eliminar Paso"/>
            </Popconfirm>
          </Space>
        ),
      },
  ];
  // --- Fin Columnas ---

  return (
    <div className="page-container">
      <Breadcrumb style={{ marginBottom: '16px' }}>
        <Breadcrumb.Item><Link to="/listas-tareas">Listas de Tareas</Link></Breadcrumb.Item>
        <Breadcrumb.Item>{taskListInfo ? taskListInfo.name : `Lista ID: ${listId}`}</Breadcrumb.Item>
        <Breadcrumb.Item>Gestionar Pasos</Breadcrumb.Item>
      </Breadcrumb>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
         <Title level={2} style={{ marginBottom: 0 }}>Pasos para: {taskListInfo?.name || `Lista ID ${listId}`}</Title>
         <Space>
             <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/listas-tareas')}>Volver a Listas</Button>
             <Button type="primary" icon={<PlusOutlined />} onClick={handleAddStep} disabled={!canManage}> Añadir Paso </Button>
             <Button icon={<FileExcelOutlined />} onClick={handleExportStepsExcel} disabled={loading || stepsList.length === 0}> Exportar Pasos </Button>
          </Space>
      </div>
      {taskListInfo?.description && <Typography.Paragraph>{taskListInfo.description}</Typography.Paragraph>}
      {taskListInfo?.applies_to_type && <Typography.Paragraph type="secondary">Aplicable a: {taskListInfo.applies_to_type}</Typography.Paragraph>}

      {error && <Alert message="Error" description={error} type="error" showIcon closable onClose={() => setError(null)} style={{ marginBottom: 16 }} />}

      <Card className="table-container" style={{ marginTop: 16 }}>
        <Spin spinning={loading}>
          <Table columns={columns} dataSource={stepsList} rowKey="key" pagination={{ pageSize: 20, showSizeChanger: true }} locale={{ emptyText: loading ? 'Cargando...' : 'Esta lista no tiene pasos.' }} size="small" bordered />
        </Spin>
      </Card>

      {/* Modal para Crear/Editar Pasos */}
      <Modal
        title={`${editingStepRecord ? 'Editar' : 'Nuevo'} Paso para Lista: ${taskListInfo?.name || listId}`} // Correcto
        open={isStepModalVisible}
        onOk={handleStepModalSubmit}
        onCancel={() => setIsStepModalVisible(false)}
        confirmLoading={isSubmittingStep}
        destroyOnClose
        maskClosable={false}
        okText={editingStepRecord ? 'Actualizar Paso' : 'Añadir Paso'} // Correcto
        cancelText="Cancelar"
      >
         <Form form={stepForm} layout="vertical" name="task_step_form">
            <Form.Item name="step_order" label="Orden del Paso" rules={[{ required: true, message: 'Indique orden.' }, { type: 'integer', min: 1 }]}>
               <InputNumber min={1} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="description" label="Descripción de la Tarea" rules={[{ required: true, message: 'Descripción obligatoria.' }]}>
               <TextArea rows={3} />
            </Form.Item>
            <Form.Item name="estimated_time_minutes" label="Tiempo Estimado (minutos, opcional)" rules={[{ type: 'integer', min: 0 }]}>
               <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
         </Form>
       </Modal>
    </div>
  );
};

export default TaskStepManagement;