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
    
    // ✅ NUEVO: Para cambios globales, limpiar sección y línea
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

  // ✅ NUEVA FUNCIÓN: Manejar selección de formato destino para auto-completado
  const handleFormatToChange = async (formatId) => {
    const selectedFormat = formats.find(f => f.id === formatId);
    
    if (selectedFormat && changeType === 'Global' && selectedFormat.machines_requiring_adjustment) {
      // Auto-completar máquinas desde el formato global
      form.setFieldsValue({ 
        affected_machines: selectedFormat.machines_requiring_adjustment 
      });
      setSelectedMachines(selectedFormat.machines_requiring_adjustment);
      
      // Auto-completar sección de referencia (usar la primera sección de las máquinas)
      await loadMachinesInfoAndSetSection(selectedFormat.machines_requiring_adjustment);
      
      message.success(`Formato global cargado: ${selectedFormat.machines_requiring_adjustment.length} máquinas seleccionadas automáticamente`);
    }
  };

  // ✅ NUEVA FUNCIÓN: Cargar info de máquinas y establecer sección para cambios globales
  const loadMachinesInfoAndSetSection = async (machineIds) => {
    try {
      const machinesData = await fetchWithAuth('/maquinas');
      const selectedMachinesInfo = machinesData.filter(m => machineIds.includes(m.id));
      
      if (selectedMachinesInfo.length > 0) {
        // Obtener la primera sección como referencia para la base de datos
        const firstMachine = selectedMachinesInfo[0];
        if (firstMachine.line_id) {
          const lineData = await fetchWithAuth(`/lines/${firstMachine.line_id}`);
          if (lineData && lineData.section_id) {
            form.setFieldsValue({ 
              section_id: lineData.section_id,
              line_id: null // No establecer línea específica para globales
            });
          }
        }
      }
    } catch (error) {
      console.error('Error cargando información de máquinas:', error);
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

      // ✅ MODIFICADO: Para cambios globales, la sección puede ser null en el envío final
      const submitData = {
        ...values,
        operator: currentUser?.username,
        // Para cambios globales, permitir section_id opcional
        section_id: values.format_change_type === 'Global' ? (values.section_id || null) : values.section_id,
        affected_machines: values.format_change_type !== 'Individual' ? values.affected_machines : null,
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
    
    // ✅ CAMBIO: Para cambios globales, NO multiplicar por número de máquinas
    if (changeType === 'Global') {
      return baseTime; // El tiempo ya incluye todas las máquinas
    }
    
    // Para Individual y Línea, sí multiplicar
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
                placeholder={changeType === 'Global' ? "(Auto-completado por formato)" : "Seleccione sección"}
                onChange={handleSectionChange}
                showSearch
                optionFilterProp="children"
                disabled={changeType === 'Global'}
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
                placeholder={changeType === 'Global' ? "(Auto-completado por formato)" : "Seleccione línea"}
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
                {users.filter(user => user.role === 'Mecánico' || user.role === 'Jefe de Sección' || user.role === 'Jefe de Mantenimiento').map(user => (
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
            label="Máquinas Afectadas (Auto-completado por formato)"
            rules={[{ required: true, message: 'Seleccione al menos una máquina' }]}
          >
            <Select
              mode="multiple"
              placeholder="Se completará automáticamente al seleccionar formato destino"
              disabled={true}
              showSearch
              optionFilterProp="children"
            >
              {/* Las opciones se cargarán dinámicamente desde el formato */}
            </Select>
          </Form.Item>
        ) : (
          <Form.Item
            name="affected_machines"
            label="Máquinas Afectadas (de la línea seleccionada)"
            rules={[{ required: true, message: 'Seleccione al menos una máquina' }]}
          >
            <Select
              mode="multiple"
              placeholder="Seleccione múltiples máquinas"
              disabled={!form.getFieldValue('line_id')}
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
                onChange={handleFormatToChange}
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
                      {/* Indicador de formato global */}
                      {format.machines_requiring_adjustment && format.machines_requiring_adjustment.length > 1 && (
                        <Tag color="green">
                          <GlobalOutlined /> Global ({format.machines_requiring_adjustment.length} máq.)
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

        {/* Configuración del Setup */}
        <Title level={4}>⏱️ Configuración del Setup</Title>
        
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="estimated_setup_duration"
              label="Duración Estimada del Setup (horas)"
              tooltip={`Tiempo estimado calculado: ${calculateEstimatedTime().toFixed(1)} horas`}
            >
              <InputNumber
                min={0}
                step={0.1}
                style={{ width: '100%' }}
                placeholder={`Sugerido: ${calculateEstimatedTime().toFixed(1)}`}
                addonAfter="horas"
              />
            </Form.Item>
          </Col>
          
          <Col span={12}>
            <Form.Item
              name="setup_team"
              label="Equipo de Setup Adicional"
            >
              <Select
                mode="multiple"
                placeholder="Seleccionar técnicos adicionales"
                showSearch
                optionFilterProp="children"
              >
                {users.filter(user => 
                  ['Mecánico', 'Jefe de Sección', 'Técnico', 'Jefe de Mantenimiento'].includes(user.role) && 
                  user.id !== currentUser?.id
                ).map(user => (
                  <Option key={user.id} value={user.id}>
                    <Space>
                      <TeamOutlined />
                      {user.username} ({user.role})
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
            placeholder="Instrucciones especiales, precauciones, herramientas necesarias..."
          />
        </Form.Item>

        {/* Tiempo estimado total */}
        {calculateEstimatedTime() > 0 && (
          <Alert
            type="info"
            message={
              <Space>
                <ClockCircleOutlined />
                <Text strong>Tiempo total estimado: {calculateEstimatedTime().toFixed(1)} horas</Text>
                {selectedMachines.length > 1 && (
                  <Text type="secondary">
                    ({selectedMachines.length} máquinas × tiempo base)
                  </Text>
                )}
              </Space>
            }
            style={{ marginBottom: 16 }}
          />
        )}

        <Divider />

        {/* Botones de acción */}
        <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
          <Space>
            <Button onClick={() => window.history.back()}>
              Cancelar
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