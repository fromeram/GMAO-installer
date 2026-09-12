// WorkOrderForm.js - CON PESTAÑAS Y GESTIÓN DE DOCUMENTOS PARA AUDITORÍAS
import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Select, DatePicker, Button, Space, Row, Col, message, Divider, InputNumber, Checkbox, List, Typography, Alert, Tabs, Descriptions, Tag } from 'antd';
import { ClockCircleOutlined, FileOutlined, FormOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { fetchWithAuth } from '../apiConfig';
import dayjs from 'dayjs';
import DocumentAttachmentManager from '../components/DocumentAttachmentManager';

const { TextArea } = Input;
const { Option } = Select;
const { Text } = Typography;
const { TabPane } = Tabs;

const WorkOrderForm = ({ onSubmit, preloadedData, sections, inventory, onCancel }) => {
  const [form] = Form.useForm();
  const { currentUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [lines, setLines] = useState([]);
  const [machines, setMachines] = useState([]);
  const [machineParts, setMachineParts] = useState([]);
  const [users, setUsers] = useState([]);
  const [failureCodes, setFailureCodes] = useState([]);
  const [causeCodes, setCauseCodes] = useState([]);
  const [remedyCodes, setRemedyCodes] = useState([]);
  const [availableTaskLists, setAvailableTaskLists] = useState([]);
  const [includeChecklist, setIncludeChecklist] = useState(false);
  const [selectedTaskList, setSelectedTaskList] = useState(null);
  const [stepProgress, setStepProgress] = useState({});
  const [activeTab, setActiveTab] = useState("form");

  // NUEVA FUNCIÓN: Manejador para capitalizar la primera letra
  const handleAutoCapitalize = (changedValues) => {
    // changedValues es un objeto como { title: 'n' } o { details: 'u' }
    for (const fieldName in changedValues) {
      const value = changedValues[fieldName];

      // Condición: solo actuar si el valor es un string, si es el primer carácter
      // que se escribe (longitud 1) y si es una letra minúscula.
      if (typeof value === 'string' && value.length === 1 && value >= 'a' && value <= 'z') {
        form.setFieldsValue({
          [fieldName]: value.toUpperCase()
        });
      }
    }
  };
  // Verificación de permisos
  const isEditable = () => {
    if (!currentUser || !preloadedData) return true; // Nueva orden
    
    const userRole = currentUser.role;
    const isAdminOrMaintenance = ["Administrador", "Jefe de Mantenimiento"].includes(userRole);
    const isJefeSeccion = userRole === "Jefe de Sección";
    const isMecanico = userRole === "Mecánico";
    
    if (isAdminOrMaintenance) return true;
    if (preloadedData.status === 'Cerrada') return false;
    if (isJefeSeccion && preloadedData.section_id === currentUser.section_id) return true;
    if (isMecanico && preloadedData.assigned_to_id === currentUser.id) return true;
    
    return false;
  };

  const canEdit = isEditable();
  const isAdminOrMaintenance = ["Administrador", "Jefe de Mantenimiento"].includes(currentUser?.role);

  // Manejo de cambios en los selects
  const handleSectionChange = async (sectionId) => {
    const selectedSection = sections.find(s => s.id === sectionId);
    setLines(selectedSection?.lines || []);
    setMachines([]);
    setMachineParts([]);
    form.setFieldsValue({ line_id: null, machine_id: null, repuesto_id: null });
  };

  const handleLineChange = (lineId) => {
    const selectedLine = lines.find(l => l.id === lineId);
    setMachines(selectedLine?.machines || []);
    setMachineParts([]);
    form.setFieldsValue({ machine_id: null, repuesto_id: null });
  };

  const handleMachineChange = async (machineId) => {
    try {
      const parts = await fetchWithAuth(`/maquinas/${machineId}/parts`);
      setMachineParts(parts || []);
      form.setFieldsValue({ repuesto_id: null });
    } catch (error) {
      console.error("Error loading machine parts:", error);
      setMachineParts([]);
    }
  };

  const handleTaskListChange = (taskListId) => {
    const taskList = availableTaskLists.find(tl => tl.id === taskListId);
    setSelectedTaskList(taskList);
    if (taskList?.steps) {
      const initialProgress = {};
      taskList.steps.forEach(step => {
        initialProgress[step.id] = { completed: false, notes: '', actual_time_minutes: null };
      });
      setStepProgress(initialProgress);
    }
  };

  // Funciones para el checklist
  const handleStepComplete = (stepId, completed) => {
    setStepProgress(prev => ({ 
      ...prev, 
      [stepId]: { 
        ...prev[stepId], 
        completed, 
        completed_at: completed ? new Date().toISOString() : null 
      }
    }));
  };

  const handleStepNotes = (stepId, notes) => {
    setStepProgress(prev => ({ 
      ...prev, 
      [stepId]: { 
        ...prev[stepId], 
        notes 
      }
    }));
  };

  const handleStepTime = (stepId, minutes) => {
    setStepProgress(prev => ({ 
      ...prev, 
      [stepId]: { 
        ...prev[stepId], 
        actual_time_minutes: minutes 
      }
    }));
  };

  // Carga de datos generales
  useEffect(() => {
    const loadGeneralData = async () => {
      try {
        const [usersData, failureData, causeData, remedyData, taskListsData] = await Promise.all([
          fetchWithAuth('/users'),
          fetchWithAuth('/failure-codes?active_only=true'),
          fetchWithAuth('/cause-codes?active_only=true'),
          fetchWithAuth('/remedy-codes?active_only=true'),
          fetchWithAuth('/task-lists')
        ]);
        setUsers(usersData || []);
        setFailureCodes(failureData || []);
        setCauseCodes(causeData || []);
        setRemedyCodes(remedyData || []);
        setAvailableTaskLists(taskListsData || []);
      } catch (error) {
        message.error("Error al cargar datos iniciales para el formulario.");
      }
    };
    loadGeneralData();
  }, []);

  // Efecto para rellenar el formulario cuando hay datos precargados
  useEffect(() => {
    if (preloadedData && sections.length > 0) {
      form.setFieldsValue({
        ...preloadedData,
        actual_start_time: preloadedData.actual_start_time ? dayjs(preloadedData.actual_start_time) : null,
        actual_end_time: preloadedData.actual_end_time ? dayjs(preloadedData.actual_end_time) : null,
      });

      const selectedSection = sections.find(s => s.id === preloadedData.section_id);
      if (selectedSection) {
        setLines(selectedSection.lines || []);
      }
    } else {
      form.resetFields();
      form.setFieldsValue({ 
        status: 'Pendiente', 
        operator: currentUser?.username, 
        assigned_to_id: currentUser?.id 
      });
    }
  }, [preloadedData, sections, form]);

  // Efecto para cargar las máquinas cuando las líneas cambian
  useEffect(() => {
    if (preloadedData && lines.length > 0) {
      const selectedLine = lines.find(l => l.id === preloadedData.line_id);
      if (selectedLine) {
        setMachines(selectedLine.machines || []);
      }
    }
  }, [preloadedData, lines]);
  useEffect(() => {
    // Solo ejecutar si:
    // 1. Hay preloadedData (orden existente)
    // 2. Hay machines cargadas
    // 3. La orden tiene una máquina asignada
    if (preloadedData && machines.length > 0 && preloadedData.machine_id) {
      const loadMachinePartsForExistingOrder = async () => {
        try {
          console.log('🔧 Cargando repuestos para orden existente, máquina ID:', preloadedData.machine_id);
          const parts = await fetchWithAuth(`/maquinas/${preloadedData.machine_id}/parts`);
          console.log('🔧 Repuestos cargados:', parts);
          setMachineParts(parts || []);
        } catch (error) {
          console.error("Error loading machine parts for existing order:", error);
          setMachineParts([]);
        }
      };
      
      loadMachinePartsForExistingOrder();
    }
  }, [preloadedData, machines]);

  // Envío del formulario
  const onFinish = async (values) => {
    if (!canEdit) {
      message.error("No tienes permisos para guardar esta orden.");
      return;
    }

    
    setLoading(true);
    try {
      let checklistData = null;
      if (includeChecklist && selectedTaskList) {
        const totalSteps = selectedTaskList.steps?.length || 0;
        const completedSteps = Object.values(stepProgress).filter(s => s.completed).length;
        checklistData = {
          task_list_id: selectedTaskList.id,
          steps_progress: Object.values(stepProgress),
          progress_percent: totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0,
          is_completed: totalSteps > 0 && completedSteps === totalSteps,
          total_elapsed_time: Object.values(stepProgress).reduce((sum, s) => sum + (s.actual_time_minutes || 0), 0)
        };
      }
      
      const dataToSubmit = {
        ...values,
        actual_start_time: values.actual_start_time ? dayjs(values.actual_start_time).toISOString() : null,
        actual_end_time: values.actual_end_time ? dayjs(values.actual_end_time).toISOString() : null,
        task_list_id: includeChecklist ? selectedTaskList?.id : null,
        checklist_data: checklistData,
        ...(preloadedData && { id: preloadedData.id })
      };
      
      await onSubmit(dataToSubmit);
    } catch (error) {
      message.error(error.message || 'Error al procesar la orden.');
    } finally {
      setLoading(false);
    }
  };

  // Componente del formulario principal
  const FormTab = () => (
    <div style={{ maxHeight: '70vh', overflowY: 'auto', padding: '8px 16px' }}>
      <Form 
        form={form} 
        layout="vertical" 
        onFinish={onFinish} 
        onValuesChange={handleAutoCapitalize} // <-- AÑADIR ESTA LÍNEA
        initialValues={{ 
          status: 'Pendiente', 
          operator: currentUser?.username, 
          assigned_to_id: currentUser?.id 
        }}
      >
        {/* Información Básica */}
        <div style={{ marginBottom: 24, paddingLeft: '8px' }}>
          <h4 style={{ color: '#1890ff', borderBottom: '1px solid #d9d9d9', paddingBottom: 8, paddingLeft: '4px' }}>
            📋 Información Básica
          </h4>
          <Row gutter={16}>
            <Col xs={24} sm={24} md={12} lg={12}>
              <Form.Item 
                name="title" 
                label="Título de la Orden" 
                rules={[{ required: true, message: 'El título es requerido' }]}
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <Input placeholder="Descripción breve del trabajo" disabled={!canEdit} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={24} md={12} lg={12}>
              <Form.Item 
                name="work_type" 
                label="Tipo de Trabajo" 
                rules={[{ required: true }]}
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <Select placeholder="Seleccione el tipo" disabled={!canEdit}>
                  <Option value="Correctivo">🔧 Correctivo</Option>
                  <Option value="Preventivo">🛠️ Preventivo</Option>
                  <Option value="Inspección">🔍 Inspección</Option>
                  <Option value="Mejora">⚡ Mejora</Option>
                  <Option value="Cambio de Formato">🔄 Cambio de Formato</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item 
            name="details" 
            label="Descripción Detallada del Trabajo"
            style={{ marginBottom: 16, paddingLeft: '8px' }}
          >
            <TextArea 
              rows={3} 
              placeholder="Descripción detallada del problema o trabajo a realizar..." 
              disabled={!canEdit} 
            />
          </Form.Item>
        </div>

        {/* Ubicación y Localización */}
        <div style={{ marginBottom: 24, paddingLeft: '8px' }}>
          <h4 style={{ color: '#52c41a', borderBottom: '1px solid #d9d9d9', paddingBottom: 8, paddingLeft: '4px' }}>
            📍 Ubicación y Localización
          </h4>
          <Row gutter={16}>
            <Col xs={24} sm={12} md={8} lg={8}>
              <Form.Item 
                name="section_id" 
                label="Sección de la Planta" 
                rules={[{ required: true }]}
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <Select 
                  placeholder="Seleccione la sección" 
                  onChange={handleSectionChange} 
                  disabled={!canEdit} 
                  showSearch 
                  optionFilterProp="children"
                >
                  {sections.map(s => <Option key={s.id} value={s.id}>{s.nombre}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8} lg={8}>
              <Form.Item 
                name="line_id" 
                label="Línea de Producción" 
                rules={[{ required: true }]}
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <Select 
                  placeholder="Seleccione la línea" 
                  onChange={handleLineChange} 
                  disabled={!canEdit || !lines.length} 
                  showSearch 
                  optionFilterProp="children"
                >
                  {lines.map(l => <Option key={l.id} value={l.id}>{l.nombre}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={24} md={8} lg={8}>
              <Form.Item 
                name="machine_id" 
                label="Máquina o Equipo" 
                rules={[{ required: true }]}
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <Select 
                  placeholder="Seleccione la máquina" 
                  onChange={handleMachineChange} 
                  disabled={!canEdit || !machines.length} 
                  showSearch 
                  optionFilterProp="children"
                >
                  {machines.map(m => <Option key={m.id} value={m.id}>{m.nombre}</Option>)}
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </div>

        {/* Personal Responsable */}
        <div style={{ marginBottom: 24, paddingLeft: '8px' }}>
          <h4 style={{ color: '#fa8c16', borderBottom: '1px solid #d9d9d9', paddingBottom: 8, paddingLeft: '4px' }}>
            👥 Personal Responsable
          </h4>
          <Row gutter={16}>
            <Col xs={24} sm={24} md={12} lg={12}>
              <Form.Item 
                name="operator" 
                label="Operario que Reporta" 
                rules={[{ required: true }]}
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <Input disabled={!canEdit} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={24} md={12} lg={12}>
              <Form.Item 
                name="assigned_to_id" 
                label="Técnico Asignado"
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <Select 
                  placeholder="Seleccione el técnico" 
                  disabled={!canEdit} 
                  showSearch 
                  optionFilterProp="children"
                >
                  {users.filter(u => ["Mecánico", "Jefe de Sección", "Jefe de Mantenimiento"].includes(u.role)).map(u => 
                    <Option key={u.id} value={u.id}>{u.username} ({u.role})</Option>
                  )}
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </div>

        {/* Lista de Tareas (Checklist) */}
        <div style={{ marginBottom: 24, paddingLeft: '8px' }}>
          <h4 style={{ color: '#722ed1', borderBottom: '1px solid #d9d9d9', paddingBottom: 8, paddingLeft: '4px' }}>
            ✅ Lista de Tareas (Checklist)
          </h4>
          <Form.Item style={{ marginBottom: 12, paddingLeft: '8px' }}>
            <Checkbox 
              checked={includeChecklist} 
              onChange={e => setIncludeChecklist(e.target.checked)} 
              disabled={!canEdit} 
            />
            <Text style={{ marginLeft: 8 }}>Incluir checklist en esta orden de trabajo</Text>
          </Form.Item>
          
          {includeChecklist && (
            <Form.Item 
              name="task_list_id" 
              label="Seleccionar Lista de Tareas" 
              rules={[{ required: includeChecklist, message: 'Seleccione una lista de tareas' }]}
              style={{ marginBottom: 16, paddingLeft: '8px' }}
            >
              <Select 
                placeholder="Seleccione una lista de tareas" 
                onChange={handleTaskListChange} 
                showSearch 
                disabled={!canEdit}
              >
                {availableTaskLists.map(tl => <Option key={tl.id} value={tl.id}>{tl.name}</Option>)}
              </Select>
            </Form.Item>
          )}
          
          {includeChecklist && selectedTaskList?.steps?.length > 0 && (
            <div style={{ paddingLeft: '8px' }}>
              <List
                size="small"
                header={<Text strong>Pasos para: {selectedTaskList.name}</Text>}
                bordered
                dataSource={selectedTaskList.steps.sort((a,b) => a.step_order - b.step_order)}
                renderItem={step => (
                  <List.Item style={{ padding: '12px' }}>
                    <Row align="middle" gutter={16} style={{ width: '100%' }}>
                      <Col xs={2} sm={2} md={1} lg={1}>
                        <Checkbox 
                          checked={stepProgress[step.id]?.completed} 
                          onChange={e => handleStepComplete(step.id, e.target.checked)} 
                          disabled={!canEdit} 
                        />
                      </Col>
                      <Col xs={22} sm={14} md={12} lg={12}>
                        <Text strong>{step.step_order}.</Text> {step.description}
                        {step.estimated_time_minutes && 
                          <Text type="secondary" style={{ marginLeft: 8 }}>
                            <ClockCircleOutlined /> {step.estimated_time_minutes} min
                          </Text>
                        }
                      </Col>
                      <Col xs={24} sm={8} md={7} lg={7}>
                        <Input.TextArea 
                          value={stepProgress[step.id]?.notes} 
                          onChange={e => handleStepNotes(step.id, e.target.value)} 
                          placeholder="Notas del paso..." 
                          rows={1} 
                          disabled={!canEdit} 
                          style={{ fontSize: '12px' }}
                        />
                      </Col>
                      <Col xs={24} sm={24} md={4} lg={4}>
                        <InputNumber 
                          value={stepProgress[step.id]?.actual_time_minutes} 
                          onChange={val => handleStepTime(step.id, val)} 
                          placeholder="Minutos reales" 
                          min={0} 
                          disabled={!canEdit} 
                          style={{ width: '100%' }}
                          size="small"
                        />
                      </Col>
                    </Row>
                  </List.Item>
                )}
                style={{ marginBottom: 24 }}
              />
            </div>
          )}
        </div>
        
        <Divider />
        
        {/* Repuestos y Materiales */}
        <div style={{ marginBottom: 24, paddingLeft: '8px' }}>
          <h4 style={{ color: '#13c2c2', borderBottom: '1px solid #d9d9d9', paddingBottom: 8, paddingLeft: '4px' }}>
            🔩 Repuestos y Materiales
          </h4>
          <Row gutter={16}>
            <Col xs={24} sm={24} md={12} lg={12}>
              <Form.Item 
                name="repuesto_id" 
                label="Repuesto Utilizado"
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <Select
                  placeholder={!form.getFieldValue('machine_id') ? "Primero seleccione una máquina" : "Seleccione el repuesto utilizado"}
                  allowClear
                  showSearch
                  optionFilterProp="children"
                  disabled={!canEdit || !machineParts.length}
                >
                  {machineParts.map(p => <Option key={p.inventory_id} value={p.inventory_id}>{p.part?.product_name || `ID ${p.inventory_id}`}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={24} md={12} lg={12}>
              <Form.Item 
                name="quantity_used" 
                label="Cantidad Utilizada"
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <InputNumber 
                  min={0} 
                  style={{ width: '100%' }} 
                  disabled={!canEdit} 
                  placeholder="Cantidad de repuestos"
                />
              </Form.Item>
            </Col>
          </Row>
        </div>
        
        {/* Códigos de Diagnóstico */}
        <div style={{ marginBottom: 24, paddingLeft: '8px' }}>
          <h4 style={{ color: '#f5222d', borderBottom: '1px solid #d9d9d9', paddingBottom: 8, paddingLeft: '4px' }}>
            🔧 Códigos de Diagnóstico
          </h4>
          <Row gutter={16}>
            <Col xs={24} sm={8} md={8} lg={8}>
              <Form.Item 
                name="failure_code_id" 
                label="Código de Falla"
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <Select placeholder="Código de falla (opcional)" allowClear showSearch disabled={!canEdit}>
                  {failureCodes.map(c => <Option key={c.id} value={c.id}>{c.code} - {c.description}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={8} md={8} lg={8}>
              <Form.Item 
                name="cause_code_id" 
                label="Código de Causa"
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <Select placeholder="Código de causa (opcional)" allowClear showSearch disabled={!canEdit}>
                  {causeCodes.map(c => <Option key={c.id} value={c.id}>{c.code} - {c.description}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={8} md={8} lg={8}>
              <Form.Item 
                name="remedy_code_id" 
                label="Código de Remedio"
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <Select placeholder="Código de remedio (opcional)" allowClear showSearch disabled={!canEdit}>
                  {remedyCodes.map(c => <Option key={c.id} value={c.id}>{c.code} - {c.description}</Option>)}
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </div>
        
        {/* Tiempos y Control */}
        <div style={{ marginBottom: 24, paddingLeft: '8px' }}>
          <h4 style={{ color: '#eb2f96', borderBottom: '1px solid #d9d9d9', paddingBottom: 8, paddingLeft: '4px' }}>
            ⏰ Tiempos y Control de Trabajo
          </h4>
          <Row gutter={16}>
            <Col xs={24} sm={8} md={8} lg={8}>
              <Form.Item 
                name="actual_start_time" 
                label="Fecha y Hora de Inicio"
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <DatePicker 
                  showTime 
                  format="YYYY-MM-DD HH:mm" 
                  style={{ width: '100%' }} 
                  disabled={!canEdit}
                  placeholder="Inicio del trabajo"
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={8} md={8} lg={8}>
              <Form.Item 
                name="actual_end_time" 
                label="Fecha y Hora de Finalización"
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <DatePicker 
                  showTime 
                  format="YYYY-MM-DD HH:mm" 
                  style={{ width: '100%' }} 
                  disabled={!canEdit}
                  placeholder="Fin del trabajo"
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={8} md={8} lg={8}>
              <Form.Item 
                name="downtime_hours" 
                label="Horas de Parada de Máquina"
                style={{ marginBottom: 16, paddingLeft: '8px' }}
              >
                <InputNumber 
                  min={0} 
                  step={0.1} 
                  style={{ width: '100%' }} 
                  disabled={!canEdit}
                  placeholder="Horas de parada"
                />
              </Form.Item>
            </Col>
          </Row>
        </div>
        
        {/* Notas y Estado Final */}
        <div style={{ marginBottom: 24, paddingLeft: '8px' }}>
          <h4 style={{ color: '#389e0d', borderBottom: '1px solid #d9d9d9', paddingBottom: 8, paddingLeft: '4px' }}>
            📝 Notas y Estado de la Orden
          </h4>
          <Form.Item 
            name="completion_notes" 
            label="Notas de Finalización y Observaciones"
            style={{ marginBottom: 16, paddingLeft: '8px' }}
          >
            <TextArea 
              rows={3} 
              placeholder="Notas sobre la finalización del trabajo, pruebas realizadas, observaciones importantes..." 
              disabled={!canEdit} 
            />
          </Form.Item>
          
          <Form.Item 
            name="status" 
            label="Estado de la Orden de Trabajo" 
            rules={[{ required: true }]}
            style={{ marginBottom: 16, paddingLeft: '8px' }}
          >
            <Select disabled={!canEdit || (!isAdminOrMaintenance && preloadedData?.status === 'Cerrada')}>
              <Option value="Pendiente">⏳ Pendiente</Option>
              <Option value="En curso">🔄 En curso</Option>
              <Option value="En revisión">👀 En revisión</Option>
              <Option value="Cerrada">✅ Cerrada</Option>
            </Select>
          </Form.Item>
        </div>

        {/* Botones de Acción */}
        <div style={{ 
          textAlign: 'right', 
          marginTop: 32, 
          paddingTop: 16, 
          borderTop: '1px solid #d9d9d9',
          background: '#fafafa',
          margin: '32px -16px -8px -16px',
          padding: '16px 24px'
        }}>
          <Space size="large">
            <Button size="large" onClick={onCancel}>
              Cancelar
            </Button>
            <Button 
              type="primary" 
              size="large" 
              htmlType="submit" 
              loading={loading} 
              disabled={!canEdit}
            >
              {preloadedData ? '💾 Actualizar Orden' : '➕ Crear Orden'}
            </Button>
          </Space>
        </div>
      </Form>
    </div>
  );

  // Componente para la gestión de documentos - SOLO PARA ÓRDENES EXISTENTES
  const DocumentsTab = () => {
    if (!preloadedData?.id) {
      return (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Alert
            message="Orden Pendiente de Crear"
            description="Los documentos solo se pueden adjuntar después de crear la orden de trabajo. Guarda primero la orden y luego podrás subir documentos."
            type="info"
            showIcon
          />
        </div>
      );
    }

    return (
      <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
        <Alert
          message="📁 Documentos de la Orden de Trabajo"
          description={
            <div>
              <p><strong>Trazabilidad Completa:</strong> Todos los documentos subidos aquí quedan vinculados específicamente a esta orden de trabajo.</p>
              <p><strong>Para Auditorías:</strong> Esta es la forma profesional de demostrar que los certificados, fotos del antes/después, y cualquier otro documento corresponden exactamente a este trabajo y no a otro.</p>
              <p><strong>Ejemplos de documentos:</strong> Certificados OCA, fotos del trabajo realizado, checklist completados, informes de inspección, etc.</p>
            </div>
          }
          type="success"
          showIcon
          style={{ marginBottom: 16 }}
        />
        
        <DocumentAttachmentManager 
          entityType="work_order"
          entityId={preloadedData.id}
          title="Documentos de la Orden"
        />
      </div>
    );
  };

  // Renderizado del componente principal
  if (preloadedData && !canEdit) {
  return (
    <div>
      <Card title="Orden de Trabajo - Solo Lectura">
        <Alert
          message={preloadedData.status === 'Cerrada' ? "Orden Cerrada" : "Sin Permisos de Edición"}
          description={preloadedData.status === 'Cerrada' ? "Esta orden ya está cerrada." : "No tienes permisos para editar esta orden."}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
        
        {/* Mostrar información básica de la orden */}
        <Descriptions bordered column={2}>
          <Descriptions.Item label="Título">{preloadedData.title}</Descriptions.Item>
          <Descriptions.Item label="Estado">
            <Tag color={preloadedData.status === 'Cerrada' ? 'green' : 'gold'}>
              {preloadedData.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Tipo">{preloadedData.work_type}</Descriptions.Item>
          <Descriptions.Item label="Operador">{preloadedData.operator}</Descriptions.Item>
          {preloadedData.details && (
            <Descriptions.Item label="Detalles" span={2}>
              {preloadedData.details}
            </Descriptions.Item>
          )}
        </Descriptions>
        
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Button type="primary" onClick={onCancel || (() => window.history.back())}>
            Volver
          </Button>
        </div>
      </Card>

      {/* AGREGAR: Mostrar documentos incluso en modo solo lectura */}
      {preloadedData?.id && (
        <Card 
          title="📁 Documentos de la Orden" 
          style={{ marginTop: 16 }}
        >
          <Alert
            message="Documentos Asociados"
            description="Documentos vinculados a esta orden de trabajo para trazabilidad y auditorías."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <DocumentAttachmentManager 
            entityType="work_order"
            entityId={preloadedData.id}
            title=""
            readOnly={true}  // Opcional: puedes pasar esta prop si tu componente la soporta
          />
        </Card>
      )}
    </div>
  );
}

  return (
    <Card title={preloadedData ? "Editar Orden de Trabajo" : "Nueva Orden de Trabajo"}>
      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        type="card"
        size="small"
      >
        <TabPane 
          tab={<span><FormOutlined /> Datos de la Orden</span>} 
          key="form"
        >
          <FormTab />
        </TabPane>
        
        <TabPane 
          tab={
            <span>
              <FileOutlined /> 
              Documentos Adjuntos 
              {!preloadedData?.id && <span style={{ color: '#999' }}>(Disponible tras crear)</span>}
            </span>
          } 
          key="documents"
          disabled={!preloadedData?.id}
        >
          <DocumentsTab />
        </TabPane>
      </Tabs>
    </Card>
  );
};

export default WorkOrderForm;