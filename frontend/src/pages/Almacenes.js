// Almacenes.js
// Página para gestionar almacenes: crear y eliminar almacenes.

import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Input, message, Typography } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import '../styles/CommonPage.css';

const { Title } = Typography;

const Almacenes = () => {
  const [almacenes, setAlmacenes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  const fetchData = async () => {
    try {
      setLoading(true);
      const data = await fetchWithAuth('/almacenes');
      setAlmacenes(data);
    } catch (error) {
      message.error('Error al cargar los almacenes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmit = async (values) => {
    try {
      await fetchWithAuth('/almacenes', {
        method: 'POST',
        body: JSON.stringify(values)
      });
      message.success('Almacén creado correctamente');
      setModalVisible(false);
      form.resetFields();
      fetchData();
    } catch (error) {
      message.error('Error al crear el almacén');
    }
  };

  const handleDelete = async (id) => {
    try {
      await fetchWithAuth(`/almacenes/${id}`, {
        method: 'DELETE'
      });
      message.success('Almacén eliminado correctamente');
      fetchData();
    } catch (error) {
      message.error('No se puede eliminar el almacén porque contiene productos');
    }
  };

  const columns = [
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_, record) => (
        <Button
          type="primary"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleDelete(record.id)}
        >
          Eliminar
        </Button>
      ),
    },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2} className="page-title">Gestión de Almacenes</Title>
      </div>

      <Card className="form-container">
        <div className="button-container">
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalVisible(true)}
          >
            Nuevo Almacén
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={almacenes}
          loading={loading}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />

        <Modal
          title="Nuevo Almacén"
          open={modalVisible}
          onCancel={() => {
            setModalVisible(false);
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
              name="name"
              label="Nombre del Almacén"
              rules={[{ required: true, message: 'Por favor ingrese el nombre' }]}
            >
              <Input />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit">
                Crear
              </Button>
            </Form.Item>
          </Form>
        </Modal>
      </Card>
    </div>
  );
};

export default Almacenes;