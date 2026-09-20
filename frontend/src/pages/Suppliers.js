// suppliers.js - Con Ordenamiento Alfabético y Paginación Corregida
import React, { useState, useEffect } from 'react';
// Agrega EditOutlined y DeleteOutlined si quieres añadir borrado también
import { Table, Button, Modal, Form, Input, message, Typography, Card, Space, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined } from '@ant-design/icons'; // Añade EditOutlined
import { fetchWithAuth } from '../apiConfig';
import '../styles/CommonPage.css';

const { Title } = Typography;

const Suppliers = () => {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState(null); // Nuevo estado para saber si editamos
  const [form] = Form.useForm();

  // 🔧 ESTADO PARA PAGINACIÓN
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    showSizeChanger: true,
    showQuickJumper: true,
    pageSizeOptions: ['10', '20', '30', '50'],
    showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} proveedores`,
  });

  // 🔧 FUNCIÓN PARA MANEJAR CAMBIOS EN LA PAGINACIÓN
  const handleTableChange = (pag, filters, sorter) => {
    console.log('Cambio en paginación proveedores:', pag);
    setPagination({
      ...pagination,
      current: pag.current,
      pageSize: pag.pageSize,
    });
  };

  const fetchSuppliers = async () => {
    setLoading(true); // Mostrar carga al refetch
    try {
      const data = await fetchWithAuth('/suppliers');
      
      // Ordenar alfabéticamente por empresa
      const sortedSuppliers = (data || []).sort((a, b) => 
        (a.company || '').localeCompare(b.company || '', 'es', { sensitivity: 'base' })
      );
      
      setSuppliers(sortedSuppliers);
      setLoading(false);
    } catch (error) {
      message.error('Error al cargar proveedores');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuppliers();
  }, []);

  // --- NUEVA FUNCIÓN PARA ABRIR MODAL EN MODO EDICIÓN ---
  const handleEdit = (record) => {
    setEditingSupplier(record); // Guarda el proveedor que se está editando
    form.setFieldsValue(record); // Rellena el formulario con sus datos
    setModalVisible(true);       // Abre el modal
  };
  // ------------------------------------------------------

  // --- FUNCIÓN PARA ABRIR MODAL EN MODO CREACIÓN ---
  const handleAddNew = () => {
    setEditingSupplier(null); // Asegura que no estamos editando
    form.resetFields();       // Limpia el formulario
    setModalVisible(true);    // Abre el modal
  };
  // --------------------------------------------------

  // --- MODIFICAR handleSubmit PARA CREAR O ACTUALIZAR ---
  const handleSubmit = async (values) => {
    try {
      let response;
      if (editingSupplier) {
        // Estamos editando
        response = await fetchWithAuth(`/suppliers/${editingSupplier.id}`, {
          method: 'PUT', // Método PUT
          body: JSON.stringify(values) // Envía los valores del formulario
        });
        message.success('Proveedor actualizado correctamente');
      } else {
        // Estamos creando
        response = await fetchWithAuth('/suppliers', {
          method: 'POST',
          body: JSON.stringify(values)
        });
        message.success('Proveedor creado correctamente');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingSupplier(null); // Resetea el estado de edición
      fetchSuppliers(); // Recarga la lista
    } catch (error) {
       // Intenta obtener el detalle del error si el backend lo envía
       const errorDetail = error?.response?.data?.detail || (editingSupplier ? 'Error al actualizar proveedor' : 'Error al crear proveedor');
       message.error(errorDetail);
    }
  };
  // ---------------------------------------------------------

  const handleCancel = () => {
      setModalVisible(false);
      form.resetFields();
      setEditingSupplier(null); // Asegúrate de resetear al cancelar
  };


  // --- AÑADIR COLUMNA DE ACCIONES ---
  const columns = [
    { 
      title: 'Empresa', 
      dataIndex: 'company', 
      key: 'company',
      defaultSortOrder: 'ascend',
      sorter: (a, b) => (a.company || '').localeCompare(b.company || '', 'es', { sensitivity: 'base' })
    },
    { title: 'Agente Comercial', dataIndex: 'name', key: 'name' }, // Ya debería funcionar con el cambio en backend
    { title: 'Teléfono', dataIndex: 'phone', key: 'phone' },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, record) => ( // El primer argumento es el texto, el segundo el registro completo
        <Space size="middle">
          <Button icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            Editar
          </Button>
          {/* Podrías añadir un botón de borrar aquí también si lo necesitas */}
          {/* <Popconfirm title="¿Seguro que quieres borrar este proveedor?" onConfirm={() => handleDelete(record.id)}>
             <Button danger icon={<DeleteOutlined />}>Borrar</Button>
          </Popconfirm> */}
        </Space>
      ),
    },
  ];
  // ---------------------------------

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2} className="page-title">Gestión de Proveedores</Title>
      </div>

      <Card className="form-container">
        <Space direction="vertical" style={{ width: '100%' }}>
          <div className="button-container">
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAddNew} // Cambiado para usar la nueva función
            >
              Nuevo Proveedor
            </Button>
          </div>

          {/* 🔧 TABLA CON PAGINACIÓN CORREGIDA */}
          <Table
            loading={loading}
            columns={columns} // Columnas actualizadas
            dataSource={suppliers}
            rowKey="id"
            pagination={pagination}
            onChange={handleTableChange}
          />
        </Space>
      </Card>

      <Modal
        // --- Título dinámico del Modal ---
        title={editingSupplier ? "Editar Proveedor" : "Nuevo Proveedor"}
        // ---------------------------------
        open={modalVisible}
        onCancel={handleCancel} // Usar handleCancel
        footer={null}
        destroyOnClose // Opcional: resetea el estado del form al cerrar
        width={600}
      >
        {/* El formulario ahora sirve para crear y editar */}
        <Form form={form} onFinish={handleSubmit} layout="vertical" initialValues={editingSupplier || {}}>
          <Form.Item
            name="company"
            label="Empresa"
            rules={[{ required: true, message: 'Por favor ingrese el nombre de la empresa' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="name"
            label="Agente Comercial"
            rules={[{ required: true, message: 'Por favor ingrese el nombre del agente' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="phone"
            label="Teléfono"
            rules={[{ required: true, message: 'Por favor ingrese el teléfono' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              {/* --- Texto dinámico del botón --- */}
              {editingSupplier ? "Actualizar" : "Guardar"}
              {/* ------------------------------ */}
            </Button>
             <Button style={{ marginLeft: 8 }} onClick={handleCancel}>
               Cancelar
             </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Suppliers;