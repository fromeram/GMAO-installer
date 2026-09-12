// frontend/src/pages/MaintenanceBacklog.js - Enhanced with Edit Functionality
import React, { useState, useEffect } from 'react';
import { 
  Table, Button, Modal, Form, Input, Select, 
  Tag, message, Card, Space, Row, Col, Statistic, InputNumber, Descriptions 
} from 'antd';
import { PlusOutlined, SwapOutlined, EditOutlined, EyeOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';

const { TextArea } = Input;
const { Option } = Select;

const MaintenanceBacklog = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [sections, setSections] = useState([]);
  const [lines, setLines] = useState([]);
  const [machines, setMachines] = useState([]);
  const [filteredLines, setFilteredLines] = useState([]);
  const [filteredMachines, setFilteredMachines] = useState([]);
  const [editingItem, setEditingItem] = useState(null);
  const [viewingItem, setViewingItem] = useState(null);
  const [form] = Form.useForm();

  // Cargar datos iniciales
  useEffect(() => {
    loadData();
    loadSections();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchWithAuth('/maintenance-backlog');
      setItems(data);
    } catch (error) {
      message.error('Error al cargar los trabajos pendientes');
    } finally {
      setLoading(false);
    }
  };

  const loadSections = async () => {
    try {
      const data = await fetchWithAuth('/secciones');
      setSections(data);
      
      // Extraer todas las líneas y máquinas
      const allLines = [];
      const allMachines = [];
      
      data.forEach(section => {
        section.lines?.forEach(line => {
          allLines.push({ ...line, sectionId: section.id });
          line.machines?.forEach(machine => {
            allMachines.push({ ...machine, lineId: line.id, sectionId: section.id });
          });
        });
      });
      
      setLines(allLines);
      setMachines(allMachines);
    } catch (error) {
      console.error('Error cargando secciones:', error);
    }
  };

  const handleSectionChange = (sectionId) => {
    // Limpiar selecciones dependientes
    form.setFieldsValue({ line_id: undefined, machine_id: undefined });
    
    // Filtrar líneas de la sección seleccionada
    const sectionLines = lines.filter(line => line.sectionId === sectionId);
    setFilteredLines(sectionLines);
    setFilteredMachines([]);
  };

  const handleLineChange = (lineId) => {
    // Limpiar selección de máquina
    form.setFieldsValue({ machine_id: undefined });
    
    // Filtrar máquinas de la línea seleccionada
    const lineMachines = machines.filter(machine => machine.lineId === lineId);
    setFilteredMachines(lineMachines);
  };

  const handleSubmit = async (values) => {
    try {
      const method = editingItem ? 'PUT' : 'POST';
      const url = editingItem 
        ? `/maintenance-backlog/${editingItem.id}` 
        : '/maintenance-backlog';
      
      await fetchWithAuth(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      });
      
      message.success(editingItem ? 'Trabajo actualizado correctamente' : 'Trabajo pendiente añadido correctamente');
      setModalVisible(false);
      setEditingItem(null);
      form.resetFields();
      loadData();
    } catch (error) {
      message.error('Error al guardar el trabajo pendiente');
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    
    // Precargar el formulario con los datos del item
    form.setFieldsValue({
      title: item.title,
      description: item.description,
      section_id: item.section?.id,
      line_id: item.machine?.lineId,
      machine_id: item.machine?.id,
      priority: item.priority,
      estimated_hours: item.estimated_hours,
      estimated_downtime: item.estimated_downtime,
      notes: item.notes
    });
    
    // Configurar líneas y máquinas filtradas
    if (item.section?.id) {
      const sectionLines = lines.filter(line => line.sectionId === item.section.id);
      setFilteredLines(sectionLines);
      
      if (item.machine?.lineId) {
        const lineMachines = machines.filter(machine => machine.lineId === item.machine.lineId);
        setFilteredMachines(lineMachines);
      }
    }
    
    setModalVisible(true);
  };

  const handleView = (item) => {
    setViewingItem(item);
    setDetailModalVisible(true);
  };

  const handleConvertToWorkOrder = async (itemId) => {
    Modal.confirm({
      title: '¿Convertir en Orden de Trabajo?',
      content: 'Este trabajo pendiente se convertirá en una orden de trabajo activa.',
      onOk: async () => {
        try {
          await fetchWithAuth(`/maintenance-backlog/${itemId}/convert`, {
            method: 'POST'
          });
          message.success('Convertido en orden de trabajo');
          loadData();
        } catch (error) {
          message.error('Error al convertir en orden de trabajo');
        }
      }
    });
  };

  const handleAdd = () => {
    setEditingItem(null);
    form.resetFields();
    setFilteredLines([]);
    setFilteredMachines([]);
    setModalVisible(true);
  };

  const columns = [
    {
      title: 'Título',
      dataIndex: 'title',
      key: 'title',
      width: 200,
    },
    {
      title: 'Descripción',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text) => text && text.length > 50 ? `${text.substring(0, 50)}...` : text,
    },
    {
      title: 'Máquina',
      dataIndex: ['machine', 'nombre'],
      key: 'machine',
      width: 150,
    },
    {
      title: 'Sección',
      dataIndex: ['section', 'nombre'],
      key: 'section',
      width: 120,
    },
    {
      title: 'Prioridad',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority) => {
        const colorMap = {
          'Baja': 'default',
          'Media': 'blue',
          'Alta': 'orange',
          'Crítica': 'red'
        };
        return <Tag color={colorMap[priority]}>{priority}</Tag>;
      }
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => {
        const colorMap = {
          'Pendiente': 'default',
          'Planificado': 'blue',
          'En Progreso': 'orange',
          'Completado': 'green',
          'Cancelado': 'red'
        };
        return <Tag color={colorMap[status]}>{status}</Tag>;
      }
    },
    {
      title: 'Horas Est.',
      dataIndex: 'estimated_hours',
      key: 'estimated_hours',
      width: 100,
      align: 'center',
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
            title="Ver detalles"
          >
            Ver
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            title="Editar"
          >
            Editar
          </Button>
          {record.status === 'Pendiente' && (
            <Button
              type="primary"
              size="small"
              icon={<SwapOutlined />}
              onClick={() => handleConvertToWorkOrder(record.id)}
              title="Crear OT"
            >
              Crear OT
            </Button>
          )}
        </Space>
      ),
    },
  ];

  // Calcular estadísticas
  const stats = {
    total: items.length,
    pending: items.filter(i => i.status === 'Pendiente').length,
    critical: items.filter(i => i.priority === 'Crítica').length,
    totalHours: items.reduce((sum, item) => sum + (item.estimated_hours || 0), 0)
  };

  return (
    <div style={{ padding: '24px' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <h1 style={{ margin: 0 }}>Backlog de Mantenimiento</h1>
          <p style={{ margin: 0, color: '#666' }}>
            Trabajos pendientes para próximas paradas de planta
          </p>
        </Col>
        <Col>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            Añadir Trabajo Pendiente
          </Button>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="Total Pendientes" value={stats.total} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="Sin Planificar" 
              value={stats.pending}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="Prioridad Crítica" 
              value={stats.critical}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="Horas Estimadas" 
              value={stats.totalHours}
              suffix="h"
            />
          </Card>
        </Col>
      </Row>

      <Table
        loading={loading}
        columns={columns}
        dataSource={items}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />

      {/* Modal para Crear/Editar */}
      <Modal
        title={editingItem ? "Editar Trabajo Pendiente" : "Añadir Trabajo Pendiente"}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingItem(null);
          form.resetFields();
          setFilteredLines([]);
          setFilteredMachines([]);
        }}
        footer={null}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="title"
            label="Título"
            rules={[{ required: true }]}
          >
            <Input placeholder="Ej: Cambiar rodamientos desgastados" />
          </Form.Item>

          <Form.Item
            name="description"
            label="Descripción detallada"
            rules={[{ required: true }]}
          >
            <TextArea 
              rows={4} 
              placeholder="Describe el trabajo a realizar, partes necesarias, observaciones..."
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="section_id"
                label="Sección"
                rules={[{ required: true }]}
              >
                <Select 
                  placeholder="Seleccionar sección"
                  onChange={handleSectionChange}
                >
                  {sections.map(section => (
                    <Option key={section.id} value={section.id}>
                      {section.nombre}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="line_id"
                label="Línea"
                rules={[{ required: false }]}
              >
                <Select 
                  placeholder="Seleccionar línea"
                  disabled={!form.getFieldValue('section_id')}
                  onChange={handleLineChange}
                >
                  {filteredLines.map(line => (
                    <Option key={line.id} value={line.id}>
                      {line.nombre}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="machine_id"
                label="Máquina"
              >
                <Select 
                  placeholder="Seleccionar máquina"
                  disabled={!form.getFieldValue('line_id')}
                >
                  {filteredMachines.map(machine => (
                    <Option key={machine.id} value={machine.id}>
                      {machine.nombre}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="priority"
                label="Prioridad"
                initialValue="Media"
              >
                <Select>
                  <Option value="Baja">Baja</Option>
                  <Option value="Media">Media</Option>
                  <Option value="Alta">Alta</Option>
                  <Option value="Crítica">Crítica</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="estimated_hours"
                label="Horas estimadas"
              >
                <InputNumber min={0} placeholder="0" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="estimated_downtime"
                label="Tiempo parada (h)"
                tooltip="Tiempo que la máquina debe estar parada"
              >
                <InputNumber min={0} placeholder="0" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="notes"
            label="Notas adicionales"
          >
            <TextArea 
              rows={3} 
              placeholder="Material necesario, herramientas especiales, precauciones..."
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setModalVisible(false);
                setEditingItem(null);
                form.resetFields();
                setFilteredLines([]);
                setFilteredMachines([]);
              }}>
                Cancelar
              </Button>
              <Button type="primary" htmlType="submit">
                {editingItem ? 'Actualizar' : 'Guardar'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Modal para Ver Detalles */}
      <Modal
        title="Detalles del Trabajo Pendiente"
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false);
          setViewingItem(null);
        }}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            Cerrar
          </Button>,
          <Button key="edit" type="primary" onClick={() => {
            setDetailModalVisible(false);
            handleEdit(viewingItem);
          }}>
            Editar
          </Button>
        ]}
        width={600}
      >
        {viewingItem && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="Título">
              {viewingItem.title}
            </Descriptions.Item>
            <Descriptions.Item label="Descripción">
              {viewingItem.description}
            </Descriptions.Item>
            <Descriptions.Item label="Máquina">
              {viewingItem.machine?.nombre || 'No especificada'}
            </Descriptions.Item>
            <Descriptions.Item label="Sección">
              {viewingItem.section?.nombre || 'No especificada'}
            </Descriptions.Item>
            <Descriptions.Item label="Prioridad">
              <Tag color={viewingItem.priority === 'Crítica' ? 'red' : 
                          viewingItem.priority === 'Alta' ? 'orange' :
                          viewingItem.priority === 'Media' ? 'blue' : 'default'}>
                {viewingItem.priority}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Estado">
              <Tag color={viewingItem.status === 'Completado' ? 'green' : 
                          viewingItem.status === 'En Progreso' ? 'orange' :
                          viewingItem.status === 'Planificado' ? 'blue' : 'default'}>
                {viewingItem.status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Horas Estimadas">
              {viewingItem.estimated_hours || 0} horas
            </Descriptions.Item>
            <Descriptions.Item label="Tiempo de Parada Estimado">
              {viewingItem.estimated_downtime || 0} horas
            </Descriptions.Item>
            {viewingItem.notes && (
              <Descriptions.Item label="Notas Adicionales">
                {viewingItem.notes}
              </Descriptions.Item>
            )}
            <Descriptions.Item label="Creado por">
              {viewingItem.created_by?.username || 'No disponible'}
            </Descriptions.Item>
            <Descriptions.Item label="Asignado a">
              {viewingItem.assigned_to?.username || 'No asignado'}
            </Descriptions.Item>
            <Descriptions.Item label="Fecha de Creación">
              {viewingItem.created_at ? new Date(viewingItem.created_at).toLocaleString() : 'No disponible'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default MaintenanceBacklog;