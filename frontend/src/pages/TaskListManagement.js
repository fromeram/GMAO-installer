// src/pages/TaskListManagement.js (Versión Responsive)
import React, { useState, useEffect, useCallback } from 'react';
import { Tabs, Table, Button, Space, message, Spin, Typography, Popconfirm, Modal, Form, Alert, Card, Input, Select, InputNumber } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import '../styles/CommonPage.css';
import MobileLayout from '../components/MobileLayout';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const TaskListManagement = () => {
  const [taskLists, setTaskLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form] = Form.useForm();
  const { currentUser } = useAuth();
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

  // Permisos (ajustar según necesidad real del backend)
  const canManage = currentUser?.role === "Administrador" || currentUser?.role === "Jefe de Mantenimiento";

  // Carga inicial de las listas de tareas
  const loadTaskLists = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Usamos el endpoint que devuelve la lista básica (sin steps)
      const data = await fetchWithAuth('/task-lists');
      setTaskLists((data || []).map(list => ({ ...list, key: list.id })));
    } catch (err) {
      console.error("Error fetching task lists:", err);
      setError(`Error al cargar listas: ${err.message || 'Desconocido'}`);
      message.error(`Error al cargar listas: ${err.message || 'Desconocido'}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTaskLists();
  }, [loadTaskLists]);

  // --- Handlers para CRUD ---

  const handleAdd = () => {
    setEditingRecord(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (record) => {
    setEditingRecord(record);
    form.setFieldsValue(record); // Precargar formulario
    setIsModalVisible(true);
  };

  const handleDelete = async (id) => {
     // Lógica de confirmación y llamada a DELETE /task-lists/{id}
     const listToDelete = taskLists.find(list => list.id === id);
     Modal.confirm({
          title: `¿Eliminar Lista "${listToDelete?.name || id}"?`,
          content: 'Se eliminarán también todos sus pasos asociados. Esta acción no se puede deshacer.',
          okText: 'Sí, eliminar', okType: 'danger', cancelText: 'No',
          onOk: async () => {
              message.loading({ content: `Eliminando lista...`, key: `deleteList-${id}` });
              try {
                  await fetchWithAuth(`/task-lists/${id}`, { method: 'DELETE' });
                  message.success({ content: 'Lista eliminada.', key: `deleteList-${id}`, duration: 2 });
                  loadTaskLists(); // Recargar
              } catch (error) {
                  message.error({ content: `Error: ${error.message || 'No se pudo eliminar'}`, key: `deleteList-${id}`, duration: 4 });
                  console.error("Delete error:", error);
              }
          },
     });
  };

  const handleModalSubmit = async () => {
     // Lógica para validar form y llamar a POST o PUT /task-lists
     setIsSubmitting(true);
     try {
         const values = await form.validateFields();
         const method = editingRecord ? 'PUT' : 'POST';
         const url = editingRecord ? `/task-lists/${editingRecord.id}` : '/task-lists';
         const payload = { ...values };
         // Para POST, podríamos necesitar enviar steps: [] si el backend lo requiere
         if (!editingRecord) {
             payload.steps = []; // Enviar steps vacío al crear (V1 simple)
         }

         console.log(`Enviando ${method} a ${url}`, payload);

         await fetchWithAuth(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
         message.success(`Lista de Tareas ${editingRecord ? 'actualizada' : 'creada'} correctamente.`);
         setIsModalVisible(false);
         loadTaskLists();

     } catch (errorInfo) {
         console.error('Error guardando lista:', errorInfo);
         if (errorInfo instanceof Error) { message.error(`Error: ${errorInfo.message}`); }
         else { message.error('Revise los campos del formulario.'); }
     } finally {
         setIsSubmitting(false);
     }
  };

  // --- Columnas Tabla (versión escritorio) ---
  const desktopColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80, sorter: (a, b) => a.id - b.id },
    { title: 'Nombre Lista', dataIndex: 'name', key: 'name', sorter: (a, b) => a.name.localeCompare(b.name) },
    { title: 'Descripción', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: 'Tipo Aplicable', dataIndex: 'applies_to_type', key: 'applies_to_type', width: 150 },
    {
      title: 'Acciones', key: 'actions', width: 180, align: 'center',
      render: (_, record) => (
        <Space>
          <Link to={`/listas-tareas/${record.id}/pasos`}>
             <Button size="small">
                Gestionar Pasos
             </Button>
          </Link>
          <Button type="primary" icon={<EditOutlined />} onClick={() => handleEdit(record)} disabled={!canManage} size="small" title="Editar Info Lista"/>
          <Popconfirm title={`¿Eliminar lista "${record.name}"?`} onConfirm={() => handleDelete(record.id)} okText="Sí" cancelText="No" okType="danger" disabled={!canManage}>
             <Button type="primary" danger icon={<DeleteOutlined />} disabled={!canManage} size="small" title="Eliminar Lista"/>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // --- Columnas Tabla (versión móvil) ---
  const mobileColumns = [
    { 
      title: 'Nombre', 
      dataIndex: 'name', 
      key: 'name',
      ellipsis: true,
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#888' }}>
            ID: {record.id} | Tipo: {record.applies_to_type || 'N/A'}
          </div>
        </div>
      )
    },
    {
      title: 'Acciones', 
      key: 'actions', 
      width: 90, 
      align: 'center',
      render: (_, record) => (
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Link to={`/listas-tareas/${record.id}/pasos`}>
             <Button type="link" size="small" style={{ padding: '0 4px' }}>
                Ver Pasos
             </Button>
          </Link>
          <Space size="small">
            <Button type="primary" icon={<EditOutlined />} onClick={() => handleEdit(record)} disabled={!canManage} size="small"/>
            <Popconfirm title="¿Eliminar?" onConfirm={() => handleDelete(record.id)} okText="Sí" cancelText="No" okType="danger" disabled={!canManage}>
               <Button type="primary" danger icon={<DeleteOutlined />} disabled={!canManage} size="small"/>
            </Popconfirm>
          </Space>
        </Space>
      ),
    },
  ];

  // Contenido común
  const taskListTable = (
    <Card className="table-container" style={{ marginTop: isMobile ? 8 : 16 }}>
      <Spin spinning={loading}>
        <Table
          columns={isMobile ? mobileColumns : desktopColumns}
          dataSource={taskLists}
          rowKey="key"
          pagination={{ 
            pageSize: isMobile ? 10 : 15, 
            showSizeChanger: !isMobile, 
            pageSizeOptions: isMobile ? ['10'] : ['15', '30', '50'],
            size: isMobile ? "small" : "default"
          }}
          locale={{ emptyText: loading ? 'Cargando...' : 'No hay listas de tareas creadas.' }}
          size="small"
          bordered
        />
      </Spin>
    </Card>
  );

  const taskListForm = (
    <Form form={form} layout="vertical" name="task_list_form">
      <Form.Item name="name" label="Nombre de la Lista" rules={[{ required: true, message: 'El nombre es obligatorio.' }]}>
        <Input />
      </Form.Item>
      <Form.Item name="description" label="Descripción">
        <TextArea rows={isMobile ? 2 : 2} />
      </Form.Item>
      <Form.Item name="applies_to_type" label="Aplicable a Tipo de Equipo (Opcional)">
        <Input placeholder="Ej: Prensa, Horno, Motor Eléctrico"/>
      </Form.Item>
    </Form>
  );

  // Renderizado condicional según dispositivo
  if (isMobile) {
    return (
      <MobileLayout title="Listas de Tareas">
        <div style={{ padding: '0 5px' }}>
          {error && (
            <Alert 
              message="Error" 
              description={error} 
              type="error" 
              showIcon 
              closable 
              onClose={() => setError(null)} 
              style={{ marginBottom: 8 }} 
            />
          )}
          
          <div style={{ 
            display: 'flex', 
            justifyContent: 'flex-end', 
            marginBottom: 8 
          }}>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={handleAdd} 
              disabled={!canManage}
              size="small"
            >
              Nueva Lista
            </Button>
          </div>
          
          {taskListTable}
        </div>
        
        <Modal
          title={`${editingRecord ? 'Editar' : 'Nueva'} Lista de Tareas`}
          open={isModalVisible}
          onOk={handleModalSubmit}
          onCancel={() => setIsModalVisible(false)}
          confirmLoading={isSubmitting}
          destroyOnClose
          maskClosable={false}
          okText={editingRecord ? 'Actualizar' : 'Crear'}
          cancelText="Cancelar"
          width={isMobile ? "100%" : 800}
        >
          {taskListForm}
        </Modal>
      </MobileLayout>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2} className="page-title" style={{ marginBottom: 0 }}>Gestión de Listas de Tareas Estándar</Title>
        <Space>
           <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd} disabled={!canManage}> Nueva Lista </Button>
        </Space>
      </div>

      {error && <Alert message="Error" description={error} type="error" showIcon closable onClose={() => setError(null)} style={{ marginBottom: 16 }} />}

      {taskListTable}

      <Modal
        title={`${editingRecord ? 'Editar' : 'Nueva'} Lista de Tareas`}
        open={isModalVisible}
        onOk={handleModalSubmit}
        onCancel={() => setIsModalVisible(false)}
        confirmLoading={isSubmitting}
        destroyOnClose
        maskClosable={false}
        okText={editingRecord ? 'Actualizar' : 'Crear'}
        cancelText="Cancelar"
        width={isMobile ? "100%" : 800}
      >
        {taskListForm}
      </Modal>
    </div>
  );
};

export default TaskListManagement;