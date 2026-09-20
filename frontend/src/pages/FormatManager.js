// src/pages/FormatManager.js - Gestión de Formatos Maestros
import React, { useState, useEffect } from 'react';
import { 
  Table, Button, Modal, Form, Input, InputNumber, Select, message, 
  Space, Card, Typography, Popconfirm, Tag, Switch, Alert 
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, SettingOutlined,
  ClockCircleOutlined, ToolOutlined 
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';

const { Title } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const FormatManager = () => {
  const [formats, setFormats] = useState([]);
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingFormat, setEditingFormat] = useState(null);
  const [form] = Form.useForm();
  const { currentUser } = useAuth();

  // Solo admin y jefe de mantenimiento pueden gestionar formatos
  const canManage = ['Administrador', 'Jefe de Mantenimiento'].includes(currentUser?.role);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [formatsData, machinesData] = await Promise.all([
        fetchWithAuth('/formats'),
        fetchWithAuth('/maquinas')
      ]);
      setFormats(formatsData || []);
      setMachines(machinesData || []);
    } catch (error) {
      console.error('Error cargando datos:', error);
      message.error('Error al cargar los datos');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values) => {
    try {
      const url = editingFormat ? `/formats/${editingFormat.id}` : '/formats';
      const method = editingFormat ? 'PUT' : 'POST';
      
      await fetchWithAuth(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      });

      message.success(`Formato ${editingFormat ? 'actualizado' : 'creado'} correctamente`);
      setModalVisible(false);
      setEditingFormat(null);
      form.resetFields();
      loadData();
    } catch (error) {
      console.error('Error:', error);
      message.error(error.message || 'Error al guardar el formato');
    }
  };

  const handleEdit = (record) => {
    setEditingFormat(record);
    form.setFieldsValue({
      ...record,
      machines_requiring_adjustment: record.machines_requiring_adjustment || [],
      tools_materials_needed: record.tools_materials_needed || []
    });
    setModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      await fetchWithAuth(`/formats/${id}`, { method: 'DELETE' });
      message.success('Formato eliminado correctamente');
      loadData();
    } catch (error) {
      console.error('Error:', error);
      message.error('Error al eliminar el formato');
    }
  };

  const handleToggleActive = async (record) => {
    try {
      await fetchWithAuth(`/formats/${record.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active: !record.active })
      });
      message.success(`Formato ${record.active ? 'desactivado' : 'activado'}`);
      loadData();
    } catch (error) {
      console.error('Error:', error);
      message.error('Error al cambiar el estado del formato');
    }
  };

  const columns = [
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <span style={{ fontWeight: record.active ? 'normal' : 'lighter', color: record.active ? 'inherit' : '#ccc' }}>
            {text}
          </span>
          {!record.active && <Tag color="orange">Inactivo</Tag>}
        </Space>
      )
    },
    {
      title: 'Descripción',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: 'Tiempo Setup Estimado',
      dataIndex: 'estimated_setup_time',
      key: 'estimated_setup_time',
      render: (time) => time ? `${time} hrs` : '-',
      align: 'center'
    },
    {
      title: 'Máquinas Asociadas',
      dataIndex: 'machines_requiring_adjustment',
      key: 'machines_requiring_adjustment',
      render: (machineIds) => {
        if (!machineIds || machineIds.length === 0) return '-';
        return `${machineIds.length} máquina${machineIds.length !== 1 ? 's' : ''}`;
      },
      align: 'center'
    },
    {
      title: 'Estado',
      dataIndex: 'active',
      key: 'active',
      render: (active, record) => (
        <Switch 
          checked={active} 
          onChange={() => handleToggleActive(record)}
          disabled={!canManage}
          checkedChildren="Activo"
          unCheckedChildren="Inactivo"
        />
      ),
      align: 'center'
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
            disabled={!canManage}
            size="small"
          />
          <Popconfirm
            title="¿Eliminar este formato?"
            onConfirm={() => handleDelete(record.id)}
            disabled={!canManage}
          >
            <Button 
              icon={<DeleteOutlined />} 
              danger 
              disabled={!canManage}
              size="small"
            />
          </Popconfirm>
        </Space>
      ),
      align: 'center'
    }
  ];

  if (!canManage) {
    return (
      <div style={{ padding: 24 }}>
        <Alert 
          message="Acceso Restringido" 
          description="No tienes permisos para gestionar formatos. Esta funcionalidad está disponible solo para Administradores y Jefes de Mantenimiento."
          type="warning" 
          showIcon 
        />
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2}>Gestión de Formatos</Title>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={() => {
            setEditingFormat(null);
            form.resetFields();
            setModalVisible(true);
          }}
        >
          Nuevo Formato
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={formats}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title={editingFormat ? 'Editar Formato' : 'Nuevo Formato'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingFormat(null);
          form.resetFields();
        }}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="Nombre del Formato"
            rules={[{ required: true, message: 'El nombre es requerido' }]}
          >
            <Input placeholder="Ej: Formato A4, Formato Botella 500ml" />
          </Form.Item>

          <Form.Item
            name="description"
            label="Descripción"
          >
            <TextArea 
              rows={3} 
              placeholder="Descripción detallada del formato..."
            />
          </Form.Item>

          <Form.Item
            name="estimated_setup_time"
            label="Tiempo Estimado de Setup (horas)"
          >
            <InputNumber 
              min={0} 
              step={0.1} 
              style={{ width: '100%' }}
              placeholder="Ej: 2.5"
              addonAfter="horas"
            />
          </Form.Item>

          <Form.Item
            name="machines_requiring_adjustment"
            label="Máquinas que Requieren Ajuste"
          >
            <Select
              mode="multiple"
              placeholder="Seleccionar máquinas..."
              style={{ width: '100%' }}
              showSearch
              optionFilterProp="children"
            >
              {machines.map(machine => (
                <Option key={machine.id} value={machine.id}>
                  {machine.nombre} - {machine.modelo}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="tools_materials_needed"
            label="Herramientas/Materiales Necesarios"
          >
            <Select
              mode="tags"
              placeholder="Escribir herramientas/materiales..."
              style={{ width: '100%' }}
              tokenSeparators={[',']}
            />
          </Form.Item>

          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>
                Cancelar
              </Button>
              <Button type="primary" htmlType="submit">
                {editingFormat ? 'Actualizar' : 'Crear'} Formato
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default FormatManager;