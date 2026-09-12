import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Input, message, Typography, Space, Collapse } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import '../styles/CommonPage.css';

const { Title } = Typography;
const { Panel } = Collapse;

const Secciones = () => {
  const [secciones, setSecciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [lineaModalVisible, setLineaModalVisible] = useState(false);
  const [selectedSeccion, setSelectedSeccion] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [form] = Form.useForm();
  const [lineaForm] = Form.useForm();

  const fetchData = async () => {
    try {
      setLoading(true);
      const data = await fetchWithAuth('/secciones');
      setSecciones(data);
    } catch (error) {
      message.error('Error al cargar las secciones');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmit = async (values) => {
    try {
      if (editingId) {
        await fetchWithAuth(`/secciones/${editingId}`, {
          method: 'PUT',
          body: JSON.stringify(values)
        });
        message.success('Sección actualizada correctamente');
      } else {
        await fetchWithAuth('/secciones', {
          method: 'POST',
          body: JSON.stringify(values)
        });
        message.success('Sección creada correctamente');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingId(null);
      fetchData();
    } catch (error) {
      message.error('Error al guardar la sección');
    }
  };

  const handleDelete = async (id) => {
    try {
      await fetchWithAuth(`/secciones/${id}`, {
        method: 'DELETE'
      });
      message.success('Sección eliminada correctamente');
      fetchData();
    } catch (error) {
      message.error('Error al eliminar la sección');
    }
  };

  const handleAddLinea = async (values) => {
    try {
      await fetchWithAuth('/secciones/line', {
        method: 'POST',
        body: JSON.stringify({
          nombre: values.nombre,
          section_id: selectedSeccion.id
        })
      });
      message.success('Línea añadida correctamente');
      setLineaModalVisible(false);
      lineaForm.resetFields();
      fetchData();
    } catch (error) {
      message.error('Error al crear la línea');
    }
  };

  const handleDeleteLinea = async (lineaId) => {
    try {
      await fetchWithAuth(`/secciones/line/${lineaId}`, {
        method: 'DELETE'
      });
      message.success('Línea eliminada correctamente');
      fetchData();
    } catch (error) {
      message.error('Error al eliminar la línea. Puede que tenga máquinas asociadas.');
    }
  };

  const expandedRowRender = (seccion) => {
    const columnasLineas = [
      {
        title: 'Nombre de Línea',
        dataIndex: 'nombre',
        key: 'nombre',
      },
      {
        title: 'Acciones',
        key: 'acciones',
        render: (_, record) => (
          <Button
            type="primary"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteLinea(record.id)}
          >
            Eliminar Línea
          </Button>
        ),
      },
    ];

    return (
      <div style={{ padding: '20px' }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setSelectedSeccion(seccion);
            setLineaModalVisible(true);
          }}
          style={{ marginBottom: 16 }}
        >
          Añadir Línea
        </Button>
        <Table
          columns={columnasLineas}
          dataSource={seccion.lines || []}
          pagination={false}
          rowKey="id"
        />
      </div>
    );
  };

  const columns = [
    {
      title: 'Nombre de Sección',
      dataIndex: 'nombre',
      key: 'nombre',
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => {
              setEditingId(record.id);
              form.setFieldsValue(record);
              setModalVisible(true);
            }}
          />
          <Button
            type="primary"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            Eliminar Sección
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2} className="page-title">Gestión de Secciones</Title>
      </div>

      <Card className="form-container">
        <div className="button-container">
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingId(null);
              form.resetFields();
              setModalVisible(true);
            }}
          >
            Nueva Sección
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={secciones}
          loading={loading}
          rowKey="id"
          expandable={{
            expandedRowRender: expandedRowRender,
            rowExpandable: record => true,
          }}
          pagination={{ pageSize: 10 }}
        />

        <Modal
          title={editingId ? "Editar Sección" : "Nueva Sección"}
          open={modalVisible}
          onCancel={() => {
            setModalVisible(false);
            setEditingId(null);
            form.resetFields();
          }}
          footer={null}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
          >
            <Form.Item
              name="nombre"
              label="Nombre de la Sección"
              rules={[{ required: true, message: 'Por favor ingrese el nombre' }]}
            >
              <Input />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit">
                {editingId ? 'Actualizar' : 'Crear'}
              </Button>
            </Form.Item>
          </Form>
        </Modal>

        <Modal
          title="Nueva Línea"
          open={lineaModalVisible}
          onCancel={() => {
            setLineaModalVisible(false);
            lineaForm.resetFields();
          }}
          footer={null}
        >
          <Form
            form={lineaForm}
            layout="vertical"
            onFinish={handleAddLinea}
          >
            <Form.Item
              name="nombre"
              label="Nombre de la Línea"
              rules={[{ required: true, message: 'Por favor ingrese el nombre de la línea' }]}
            >
              <Input />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit">
                Crear Línea
              </Button>
            </Form.Item>
          </Form>
        </Modal>
      </Card>
    </div>
  );
};

export default Secciones;
