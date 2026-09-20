// src/components/FormatChangeForm.js - Formulario para Órdenes de Cambio de Formato
import React, { useState, useEffect } from 'react';
import { 
  Form, Select, Input, InputNumber, Button, Card, Alert, Space, 
  Radio, Divider, Typography, Tag, Tooltip, Row, Col, message
} from 'antd';
import { 
  GlobalOutlined, ApartmentOutlined, ToolOutlined, 
  ClockCircleOutlined, TeamOutlined 
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { fetchWithAuth } from '../apiConfig';

const { TextArea } = Input;
const { Option } = Select;
const { Title, Text } = Typography;

const FormatChangeForm = ({ onSubmit, preloadedData = null, sections = [], users = [] }) => {
  const [form] = Form.useForm();
  const { currentUser } = useAuth();
  const [loading, setLoading] = useState(false);
  
  // Estados para datos dependientes
  const [lines, setLines] = useState([]);
  const [machines, setMachines] = useState([]);
  const [formats, setFormats] = useState([]);
  const [selectedMachines, setSelectedMachines] = useState([]);
  
  // Estados para el tipo de cambio
  const [changeType, setChangeType] = useState('Individual');
  const [workType, setWorkType] = useState('Cambio de Formato');

  useEffect(() => {
    loadFormats();
    if (preloadedData) {
      loadPreloadedData();
    }
  }, [preloadedData]);

  const loadFormats = async () => {
    try {
      const formatsData = await fetchWithAuth('/formats');
      setFormats(formatsData || []);
    } catch (error) {
      console.error('Error cargando formatos:', error);
    }
  };

  const loadPreloadedData = () => {
    // Cargar datos si se está editando
    if (preloadedData) {
      const selectedSection = sections.find(s => s.id === preloadedData.section_id);
      if (selectedSection) {
        setLines(selectedSection.lines || []);
        
        const selectedLine = selectedSection.lines?.find(l => l.id === preloadedData.line_id);
        if (selectedLine) {
          setMachines(selectedLine.machines || []);
        }
      }
      
      setChangeType(preloadedData.format_change_type || 'Individual');
      setWorkType(preloadedData.work_type || 'Cambio de Formato');
      
      form.setFieldsValue({
        ...preloadedData,
        setup_team: preloadedData.setup_team || []
      });
    }
  };

  const handleSectionChange = (sectionId) => {
    form.setFieldsValue({ line_id: undefined, machine_id: undefined, affected_machines: [] });
    const selectedSection = sections.find(s => s.id === sectionId);
    setLines(selectedSection?.lines || []);
    setMachines([]);
    setSelectedMachines([]);
  };

  const handleLineChange = (lineId) => {
    form.setFieldsValue({ machine_id: undefined, affected_machines: [] });
    const selectedLine = lines.find(l => l.id === lineId);
    setMachines(selectedLine?.machines || []);
    setSelectedMachines([]);
  };

  const handleChangeTypeChange = (e) => {
    const newChangeType = e.target.value;
    setChangeType(newChangeType);
    
    // Limpiar selecciones de máquinas cuando cambia el tipo
    if (newChangeType === 'Individual') {
      form.setFieldsValue({ affected_machines: [], machine_id: undefined });
    } else {
      form.setFieldsValue({ machine_id: undefined, affected_machines: [] });
    }
    setSelectedMachines([]);
    
    // Para cambios globales, limpiar sección y línea ya que no son requeridas
    if (newChangeType === 'Global') {
      form.setFieldsValue({ section_id: undefined, line_id: undefined });
      setLines([]);
      setMachines([]);
    }
  };

  const handleMachineSelectionChange = (machineIds) => {
    setSelectedMachines(machineIds);
    
    // Si es cambio individual y se selecciona más de una máquina, cambiar a tipo Línea
    if (changeType === 'Individual' && machineIds.length > 1) {
      setChangeType('Línea');
      form.setFieldsValue({ format_change_type: 'Línea' });
    }
  };

  // Función para manejar selección de formato y auto-cargar máquinas
  const handleFormatChange = async (formatId, formatType) => {
    const selectedFormat = formats.find(f => f.id === formatId);
    
    // Solo auto-cargar máquinas si es cambio Global y el formato tiene máquinas predefinidas
    if (changeType === 'Global' && selectedFormat && selectedFormat.machines_requiring_adjustment) {
      const machineIds = selectedFormat.machines_requiring_adjustment;
      
      // Establecer las máquinas seleccionadas
      form.setFieldsValue({ 
        affected_machines: machineIds 
      });
      setSelectedMachines(machineIds);
      
      // Para cambios globales, cargar TODAS las máquinas disponibles
      const allMachines = [];
      sections.forEach(section => {
        section.lines?.forEach(line => {
          line.machines?.forEach(machine => {
            if (machineIds.includes(machine.id)) {
              allMachines.push({
                ...machine,
                section_name: section.nombre,
                line_name: line.nombre
              });
            }
          });
        });
      });
      
      setMachines(allMachines);
      
      message.success(
        `Plantilla global cargada: ${machineIds.length} máquinas de múltiples secciones`
      );
    }
  };

  const onFinish = async (values) => {
    setLoading(true);
    try {
      // Validaciones específicas
      if (values.format_change_type === 'Individual' && !values.machine_id) {
        throw new Error('Debe seleccionar una máquina para cambios individuales');
      }
      
      if (['Línea', 'Global'].includes(values.format_change_type) && 
          (!values.affected_machines || values.affected_machines.length === 0)) {
        throw new Error('Debe seleccionar al menos una máquina para cambios de línea/globales');
      }

      // Preparar datos para envío
      const submitData = {
        ...values,
        operator: currentUser?.username,
        // Para cambios globales, section_id es opcional
        section_id: changeType === 'Global' ? (values.section_id || null) : values.section_id,
        // Asegurar que affected_machines sea array para cambios multi-máquina
        affected_machines: values.format_change_type !== 'Individual' ? values.affected_machines : null,
        // Para cambios individuales, usar machine_id
        machine_id: values.format_change_type === 'Individual' ? values.machine_id : null
      };

      await onSubmit(submitData);
    } catch (error) {
      console.error('Error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Calcular tiempo estimado total basado en máquinas seleccionadas
  const calculateEstimatedTime = () => {
    if (!formats.length) return 0;
    
    const fromFormat = formats.find(f => f.id === form.getFieldValue('format_from_id'));
    const toFormat = formats.find(f => f.id === form.getFieldValue('format_to_id'));
    
    let baseTime = 0;
    if (fromFormat?.estimated_setup_time) baseTime += fromFormat.estimated_setup_time;
    if (toFormat?.estimated_setup_time) baseTime += toFormat.estimated_setup_time;
    
    // Multiplicar por número de máquinas para cambios multi-máquina
    const machineCount = changeType === 'Individual' ? 1 : selectedMachines.length || 1;
    return baseTime * machineCount;
  };

  return (
    <Card title={preloadedData ? "Editar Orden de Cambio de Formato" : "Nueva Orden de Cambio de Formato"}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          work_type: 'Cambio de Formato',
          format_change_type: 'Individual',
          assigned_to_id: currentUser?.id,
          setup_team: []
        }}
      >
        {/* Información Básica */}
        <Title level={4}>📋 Información Básica</Title>
        
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="title"
              label="Título del Cambio"
              rules={[{ required: true, message: 'El título es requerido' }]}
            >
              <Input placeholder="Ej: Cambio de formato A4 a A3 en Línea 1" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="work_type"
              label="Tipo de Trabajo"
              rules={[{ required: true }]}
            >
              <Select onChange={setWorkType}>
                <Option value="Cambio de Formato">
                  <ToolOutlined /> Cambio de Formato
                </Option>
                <Option value="Setup de Línea">
                  <ApartmentOutlined /> Setup de Línea
                </Option>
                <Option value="Cambio Global de Planta">
                  <GlobalOutlined /> Cambio Global de Planta
                </Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          name="details"
          label="Descripción Detallada"
        >
          <TextArea rows={3} placeholder="Descripción del cambio de formato..." />
        </Form.Item>

        <Divider />

        {/* Tipo de Cambio */}
        <Title level={4}>🔧 Tipo de Cambio</Title>
        
        <Form.Item
          name="format_change_type"
          label="Alcance del Cambio"
          rules={[{ required: true }]}
        >
          <Radio.Group onChange={handleChangeTypeChange} value={changeType}>
            <Space direction="vertical">
              <Radio value="Individual">
                <ToolOutlined /> <strong>Individual</strong> - Una máquina específica
              </Radio>
              <Radio value="Línea">
                <ApartmentOutlined /> <strong>Línea de Producción</strong> - Múltiples máquinas de una línea
              </Radio>
              <Radio value="Global">
                <GlobalOutlined /> <strong>Global de Planta</strong> - Múltiples líneas y secciones
              </Radio>
            </Space>
          </Radio.Group>
        </Form.Item>

        <Divider />

        {/* Ubicación y Máquinas */}
        <Title level={4}>📍 Ubicación y Máquinas Afectadas</Title>
        
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="section_id"
              label="Sección"
              rules={changeType !== 'Global' ? [{ required: true, message: 'Seleccione una sección' }] : []}
            >
              <Select
                placeholder={changeType === 'Global' ? "Opcional para cambios globales" : "Seleccione sección"}
                onChange={handleSectionChange}
                showSearch
                optionFilterProp="children"
                disabled={changeType === 'Global' && selectedMachines.length > 0}
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
              rules={changeType === 'Individual' ? [{ required: true, message: 'Seleccione una línea' }] : []}
            >
              <Select
                placeholder={changeType === 'Global' ? "No aplica para cambios globales" : "Seleccione línea"}
                disabled={!form.getFieldValue('section_id') || changeType === 'Global'}
                onChange={handleLineChange}
                showSearch
                optionFilterProp="children"
              >
                {lines.map(line => (
                  <Option key={line.id} value={line.id}>
                    {line.nombre}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          
          <Col span={8}>
            <Form.Item
              name="assigned_to_id"
              label="Técnico Responsable"
              rules={[{ required: true, message: 'Seleccione el técnico responsable' }]}
            >
              <Select
                placeholder="Seleccione técnico"
                showSearch
                optionFilterProp="children"
              >
                {users.filter(user => user.role === 'Mecánico' || user.role === 'Jefe de Sección').map(user => (
                  <Option key={user.id} value={user.id}>
                    {user.username} ({user.role})
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        {/* Selección de Máquinas */}
        {changeType === 'Individual' ? (
          <Form.Item
            name="machine_id"
            label="Máquina"
            rules={[{ required: true, message: 'Seleccione la máquina' }]}
          >
            <Select
              placeholder="Seleccione máquina"
              disabled={!form.getFieldValue('line_id')}
              showSearch
              optionFilterProp="children"
            >
              {machines.map(machine => (
                <Option key={machine.id} value={machine.id}>
                  <Space>
                    <strong>{machine.nombre}</strong>
                    <Text type="secondary">({machine.modelo})</Text>
                  </Space>
                </Option>
              ))}
            </Select>
          </Form.Item>
        ) : changeType === 'Global' ? (
          <Form.Item
            name="affected_machines"
            label="Máquinas Afectadas (se cargan automáticamente desde la plantilla)"
            rules={[{ required: true, message: 'Seleccione un formato con máquinas predefinidas' }]}
          >
            <Select
              mode="multiple"
              placeholder="Seleccione un formato arriba para cargar las máquinas"
              onChange={handleMachineSelectionChange}
              showSearch
              optionFilterProp="children"
            >
              {machines.map(machine => (
                <Option key={machine.id} value={machine.id}>
                  <Space>
                    <strong>{machine.nombre}</strong>
                    <Text type="secondary">
                      ({machine.section_name || 'N/A'} - {machine.line_name || 'N/A'})
                    </Text>
                  </Space>
                </Option>
              ))}
            </Select>
          </Form.Item>
        ) : (
          <Form.Item
            name="affected_machines"
            label={`Máquinas Afectadas ${changeType === 'Línea' ? '(de la línea seleccionada)' : '(múltiples líneas)'}`}
            rules={[{ required: true, message: 'Seleccione al menos una máquina' }]}
          >
            <Select
              mode="multiple"
              placeholder="Seleccione múltiples máquinas"
              disabled={changeType === 'Línea' && !form.getFieldValue('line_id')}
              onChange={handleMachineSelectionChange}
              showSearch
              optionFilterProp="children"
            >
              {machines.map(machine => (
                <Option key={machine.id} value={machine.id}>
                  <Space>
                    <strong>{machine.nombre}</strong>
                    <Text type="secondary">({machine.modelo})</Text>
                  </Space>
                </Option>
              ))}
            </Select>
          </Form.Item>
        )}

        {selectedMachines.length > 0 && (
          <Alert
            message={`Se han seleccionado ${selectedMachines.length} máquina${selectedMachines.length !== 1 ? 's' : ''} para el cambio`}
            type="info"
            style={{ marginBottom: 16 }}
          />
        )}

        <Divider />

        {/* Formatos */}
        <Title level={4}>🔄 Formatos de Cambio</Title>
        
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="format_from_id"
              label="Formato Actual (Origen)"
            >
              <Select
                placeholder="Seleccionar formato origen"
                allowClear
                showSearch
                optionFilterProp="children"
                onChange={(value) => handleFormatChange(value, 'from')}
              >
                {formats.filter(f => f.active).map(format => (
                  <Option key={format.id} value={format.id}>
                    <Space>
                      <strong>{format.name}</strong>
                      {format.estimated_setup_time && (
                        <Tag color="blue">
                          <ClockCircleOutlined /> {format.estimated_setup_time}h
                        </Tag>
                      )}
                    </Space>
                  </Option>
                ))}
              </Select>
            </Form.Item>
            
            <Form.Item
              name="format_from_name"
              label="O especificar nombre del formato origen"
            >
              <Input placeholder="Ej: Formato A4 actual" />
            </Form.Item>
          </Col>
          
          <Col span={12}>
            <Form.Item
              name="format_to_id"
              label="Formato Destino (Nuevo)"
            >
              <Select
                placeholder="Seleccionar formato destino"
                allowClear
                showSearch
                optionFilterProp="children"
                onChange={(value) => handleFormatChange(value, 'to')}
              >
                {formats.filter(f => f.active).map(format => (
                  <Option key={format.id} value={format.id}>
                    <Space>
                      <strong>{format.name}</strong>
                      {format.estimated_setup_time && (
                        <Tag color="green">
                          <ClockCircleOutlined /> {format.estimated_setup_time}h
                        </Tag>
                      )}
                    </Space>
                  </Option>
                ))}
              </Select>
            </Form.Item>
            
            <Form.Item
              name="format_to_name"
              label="O especificar nombre del formato destino"
            >
              <Input placeholder="Ej: Formato A3 nuevo" />
            </Form.Item>
          </Col>
        </Row>

        <Divider />

        {/* Planificación */}
        <Title level={4}>⏱️ Planificación del Setup</Title>
        
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="estimated_setup_duration"
              label="Tiempo Estimado de Setup (horas)"
            >
              <InputNumber 
                min={0} 
                step={0.1} 
                style={{ width: '100%' }}
                placeholder={`Sugerido: ${calculateEstimatedTime().toFixed(1)} hrs`}
                addonAfter="horas"
              />
            </Form.Item>
            
            {calculateEstimatedTime() > 0 && (
              <Alert
                message={`Tiempo sugerido basado en formatos: ${calculateEstimatedTime().toFixed(1)} horas`}
                type="info"
                style={{ marginBottom: 16 }}
              />
            )}
          </Col>
          
          <Col span={12}>
            <Form.Item
              name="setup_team"
              label="Equipo de Setup"
            >
              <Select
                mode="multiple"
                placeholder="Seleccionar miembros del equipo"
                showSearch
                optionFilterProp="children"
              >
                {users.filter(user => ['Mecánico', 'Jefe de Sección', 'Jefe de Mantenimiento'].includes(user.role)).map(user => (
                  <Option key={user.id} value={user.id}>
                    <Space>
                      {user.username}
                      <Tag color="blue">{user.role}</Tag>
                    </Space>
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          name="setup_notes"
          label="Notas del Setup"
        >
          <TextArea 
            rows={3} 
            placeholder="Instrucciones especiales, herramientas necesarias, precauciones..." 
          />
        </Form.Item>

        {/* Botones */}
        <Form.Item style={{ textAlign: 'right', marginTop: 24 }}>
          <Space>
            <Button onClick={() => form.resetFields()}>
              Limpiar
            </Button>
            <Button type="primary" htmlType="submit" loading={loading}>
              {preloadedData ? 'Actualizar' : 'Crear'} Orden de Cambio
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default FormatChangeForm;