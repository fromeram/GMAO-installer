// WorkOrderForm.js - CON CHECKLIST INTEGRADO CONDICIONALMENTE
import React, { useState, useEffect } from 'react';
import { Form, Select, Input, DatePicker, InputNumber, Button, Card, Alert, Space, message, Switch, Divider, List, Checkbox, Row, Col, Typography, Collapse } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { fetchWithAuth } from '../apiConfig';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
dayjs.locale('es');

const { Option } = Select;
const { TextArea } = Input;
const { Panel } = Collapse;
const { Text, Title } = Typography;

const WorkOrderForm = ({ sections, inventory, onSubmit, preloadedData = null, onCancel }) => {
  const [form] = Form.useForm();
  const { currentUser } = useAuth();
  const [lines, setLines] = useState([]);
  const [machines, setMachines] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState([]);
  const [failureCodes, setFailureCodes] = useState([]);
  const [causeCodes, setCauseCodes] = useState([]);
  const [remedyCodes, setRemedyCodes] = useState([]);
  const [machineParts, setMachineParts] = useState([]);
  
  // Estados para el checklist
  const [includeChecklist, setIncludeChecklist] = useState(false);
  const [availableTaskLists, setAvailableTaskLists] = useState([]);
  const [selectedTaskList, setSelectedTaskList] = useState(null);
  const [checklistSteps, setChecklistSteps] = useState([]);
  const [stepProgress, setStepProgress] = useState({});

  // Determinar el rol del usuario
  const userRole = currentUser?.role || "";
  const isAdminOrMaintenance = ['Administrador', 'Jefe de Mantenimiento'].includes(userRole);
  const isMecanico = userRole === 'Mecánico';

  // Función para verificar si puede editar la orden
  const canEditOrder = () => {
    if (!preloadedData) return true; // Puede crear nuevas órdenes
    
    // Admin y Jefe de Mantenimiento pueden editar cualquier orden
    if (isAdminOrMaintenance) return true;
    
    // Si la orden está cerrada, solo Admin y Jefe de Mantenimiento pueden editarla
    if (preloadedData.status === 'Cerrada') return false;
    
    // Jefe de Sección puede editar órdenes de su sección
    if (userRole === 'Jefe de Sección' && preloadedData.section_id === currentUser.section_id) return true;
    
    // Mecánico puede editar órdenes asignadas a él
    if (isMecanico && preloadedData.assigned_to_id === currentUser.id) return true;
    
    return false;
  };

  // Cargar datos iniciales
  useEffect(() => {
    loadUsers();
    loadCodes();
    loadTaskLists();
    
    if (preloadedData && preloadedData.has_checklist) {
      setIncludeChecklist(true);
      loadExistingChecklistData(preloadedData.id);
    }
  }, []);

  const loadUsers = async () => {
    try {
      const data = await fetchWithAuth('/users');
      setUsers(data);
    } catch (error) {
      console.error('Error cargando usuarios:', error);
    }
  };

  const loadCodes = async () => {
    try {
      const [failureResponse, causeResponse, remedyResponse] = await Promise.allSettled([
        fetchWithAuth('/failure-codes?active_only=true'),
        fetchWithAuth('/cause-codes?active_only=true'),
        fetchWithAuth('/remedy-codes?active_only=true')
      ]);

      if (failureResponse.status === 'fulfilled') setFailureCodes(failureResponse.value || []);
      if (causeResponse.status === 'fulfilled') setCauseCodes(causeResponse.value || []);
      if (remedyResponse.status === 'fulfilled') setRemedyCodes(remedyResponse.value || []);
    } catch (error) {
      console.error('Error cargando códigos:', error);
    }
  };

  const loadTaskLists = async () => {
    try {
      const data = await fetchWithAuth('/task-lists');
      setAvailableTaskLists(data || []);
    } catch (error) {
      console.error('Error cargando listas de tareas:', error);
    }
  };

  const loadExistingChecklistData = async (workOrderId) => {
    try {
      const response = await fetchWithAuth(`/work-orders/${workOrderId}/checklist-data`);
      if (response.task_list) {
        setSelectedTaskList(response.task_list);
        setChecklistSteps(response.task_list.steps || []);
        
        if (response.existing_progress) {
          const progress = {};
          response.existing_progress.steps_progress.forEach(step => {
            progress[step.step_id] = step;
          });
          setStepProgress(progress);
        }
      }
    } catch (error) {
      console.error('Error cargando datos del checklist:', error);
    }
  };

  const handleSectionChange = async (sectionId) => {
    try {
      const data = await fetchWithAuth(`/lines/section/${sectionId}`);
      setLines(data);
      setMachines([]);
      setMachineParts([]);
      form.setFieldsValue({ line_id: undefined, machine_id: undefined, repuesto_id: undefined });
    } catch (error) {
      console.error('Error cargando líneas:', error);
      message.error('Error al cargar las líneas');
    }
  };

  const handleLineChange = async (lineId) => {
    try {
      const data = await fetchWithAuth(`/machines/line/${lineId}`);
      setMachines(data);
      setMachineParts([]);
      form.setFieldsValue({ machine_id: undefined, repuesto_id: undefined });
    } catch (error) {
      console.error('Error cargando máquinas:', error);
      message.error('Error al cargar las máquinas');
    }
  };

  const handleMachineChange = async (machineId) => {
    try {
      const data = await fetchWithAuth(`/maquinas/${machineId}/parts`);
      setMachineParts(data);
      form.setFieldsValue({ repuesto_id: undefined });
    } catch (error) {
      console.error('Error cargando repuestos:', error);
      message.error('Error al cargar los repuestos');
    }
  };

  const handleProductSelect = (inventoryId) => {
    if (inventoryId) {
      const selectedPart = machineParts.find(part => part.inventory_id === inventoryId);
      setSelectedProduct(selectedPart || null);
    } else {
      setSelectedProduct(null);
    }
  };

  // Manejo del checklist
  const handleIncludeChecklistChange = (checked) => {
    setIncludeChecklist(checked);
    if (!checked) {
      setSelectedTaskList(null);
      setChecklistSteps([]);
      setStepProgress({});
      form.setFieldsValue({ task_list_id: undefined });
    }
  };

  const handleTaskListChange = async (taskListId) => {
    if (!taskListId) {
      setSelectedTaskList(null);
      setChecklistSteps([]);
      setStepProgress({});
      return;
    }

    try {
      const data = await fetchWithAuth(`/task-lists/${taskListId}`);
      setSelectedTaskList(data);
      setChecklistSteps(data.steps || []);
      
      // Inicializar progreso de pasos
      const initialProgress = {};
      data.steps.forEach(step => {
        initialProgress[step.id] = {
          step_id: step.id,
          completed: false,
          notes: '',
          actual_time_minutes: null
        };
      });
      setStepProgress(initialProgress);
    } catch (error) {
      console.error('Error cargando lista de tareas:', error);
      message.error('Error al cargar la lista de tareas');
    }
  };

  const handleStepComplete = (stepId, completed) => {
    const now = new Date().toISOString();
    setStepProgress(prev => ({
      ...prev,
      [stepId]: {
        ...prev[stepId],
        completed,
        completed_at: completed ? now : null,
        started_at: prev[stepId]?.started_at || (completed ? now : null)
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

  // Cargar datos precargados
  useEffect(() => {
    const loadPreloadedData = async () => {
      if (preloadedData) {
        await handleSectionChange(preloadedData.section_id);
        await handleLineChange(preloadedData.line_id);
        await handleMachineChange(preloadedData.machine_id);

        setTimeout(() => {
          const formValues = {
            ...preloadedData,
            actual_start_time: preloadedData.actual_start_time ? dayjs(preloadedData.actual_start_time) : null,
            actual_end_time: preloadedData.actual_end_time ? dayjs(preloadedData.actual_end_time) : null,
          };

          console.log("🔧 Estableciendo valores del formulario:", formValues);
          form.setFieldsValue(formValues);
        }, 100);
      }
    };

    if (preloadedData && sections.length > 0) {
      loadPreloadedData();
    }
  }, [preloadedData, sections, form]);

  // Función principal de envío
  const onFinish = async (values) => {
    setLoading(true);
    try {
      console.log("📋 Valores RAW del formulario:", values);
      
      // Validaciones básicas
      if (!values.machine_id) {
        message.error('Debe seleccionar una máquina antes de crear la orden');
        setLoading(false);
        return;
      }
      
      if (!values.section_id) {
        message.error('Debe seleccionar una sección antes de crear la orden');
        setLoading(false);
        return;
      }
      
      if (!values.line_id) {
        message.error('Debe seleccionar una línea antes de crear la orden');
        setLoading(false);
        return;
      }

      // Preparar datos del checklist si está incluido
      let checklistData = null;
      if (includeChecklist && selectedTaskList) {
        const completedSteps = Object.values(stepProgress).filter(step => step.completed).length;
        const totalSteps = checklistSteps.length;
        
        checklistData = {
          task_list_id: selectedTaskList.id,
          steps_progress: Object.values(stepProgress),
          progress_percent: totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0,
          is_completed: completedSteps === totalSteps && totalSteps > 0,
          total_elapsed_time: Object.values(stepProgress).reduce((sum, step) => 
            sum + (step.actual_time_minutes || 0), 0
          )
        };
      }

      // Payload completo
      const dataToSubmit = {
        ...values,
        actual_start_time: values.actual_start_time ? values.actual_start_time.toISOString() : null,
        actual_end_time: values.actual_end_time ? values.actual_end_time.toISOString() : null,
        section_id: Number(values.section_id),
        line_id: Number(values.line_id),
        machine_id: Number(values.machine_id),
        assigned_to_id: Number(values.assigned_to_id),
        repuesto_id: values.repuesto_id ? Number(values.repuesto_id) : null,
        quantity_used: values.quantity_used ? Number(values.quantity_used) : 0,
        failure_code_id: values.failure_code_id || null,
        cause_code_id: values.cause_code_id || null,
        remedy_code_id: values.remedy_code_id || null,
        downtime_hours: values.downtime_hours || null,
        completion_notes: values.completion_notes || null,
        status: values.status || 'Pendiente',
        task_list_id: includeChecklist ? selectedTaskList?.id : null,
        checklist_data: checklistData,
        ...(preloadedData && { id: preloadedData.id })
      };

      console.log("👷‍♂️ PAYLOAD COMPLETO CON CHECKLIST:", dataToSubmit);
      await onSubmit(dataToSubmit);
      
    } catch (error) {
      console.error("❌ Error en onFinish:", error);
      message.error(error.message || 'Error al procesar la orden');
    } finally {
      setLoading(false);
    }
  };

  // Si no puede editar, mostrar mensaje de error
  if (preloadedData && !canEditOrder()) {
    return (
      <Card title="Sin Permisos de Edición" bordered={false}>
        <Alert
          message={preloadedData.status === 'Cerrada' ? "Orden Cerrada" : "Sin Permisos"}
          description={
            preloadedData.status === 'Cerrada' 
              ? "Esta orden de trabajo ya está cerrada y no puede ser modificada."
              : "No tienes permisos para editar esta orden de trabajo."
          }
          type="warning"
          showIcon
        />
      </Card>
    );
  }

  return (
    <Card title={preloadedData ? "Editar Orden de Trabajo" : "Nueva Orden de Trabajo"} bordered={false}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          status: 'Pendiente',
          operator: currentUser?.username,
          assigned_to_id: currentUser?.id
        }}
      >
        {/* Información básica */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Form.Item
            name="title"
            label="Título"
            rules={[{ required: true, message: 'Ingrese el título de la orden' }]}
          >
            <Input 
              placeholder="Descripción breve del trabajo a realizar"
              disabled={preloadedData && !canEditOrder()}
            />
          </Form.Item>

          <Form.Item
            name="work_type"
            label="Tipo de Trabajo"
            rules={[{ required: true, message: 'Seleccione el tipo de trabajo' }]}
          >
            <Select
              placeholder="Seleccione tipo"
              disabled={preloadedData && !canEditOrder()}
            >
              <Option value="Correctivo">Correctivo</Option>
              <Option value="Preventivo">Preventivo</Option>
              <Option value="Inspección">Inspección</Option>
              <Option value="Mejora">Mejora</Option>
              <Option value="Cambio de Formato">Cambio de Formato</Option>
            </Select>
          </Form.Item>
        </div>

        <Form.Item
          name="details"
          label="Descripción Detallada"
          rules={[{ required: true, message: 'Ingrese los detalles del trabajo' }]}
        >
          <TextArea
            rows={3}
            placeholder="Descripción detallada del problema o trabajo a realizar..."
            disabled={preloadedData && !canEditOrder()}
          />
        </Form.Item>

        {/* Ubicación */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Form.Item
            name="section_id"
            label="Sección"
            rules={[{ required: true, message: 'Seleccione la sección' }]}
          >
            <Select
              placeholder="Seleccione sección"
              onChange={handleSectionChange}
              showSearch
              optionFilterProp="children"
              disabled={preloadedData && !canEditOrder()}
            >
              {sections.map(section => (
                <Option key={section.id} value={section.id}>
                  {section.nombre}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="line_id"
            label="Línea"
            rules={[{ required: true, message: 'Seleccione la línea' }]}
          >
            <Select
              placeholder="Seleccione línea"
              onChange={handleLineChange}
              showSearch
              optionFilterProp="children"
              disabled={!lines.length || (preloadedData && !canEditOrder())}
            >
              {lines.map(line => (
                <Option key={line.id} value={line.id}>
                  {line.nombre}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="machine_id"
            label="Máquina"
            rules={[{ required: true, message: 'Seleccione la máquina' }]}
          >
            <Select
              placeholder="Seleccione máquina"
              onChange={handleMachineChange}
              showSearch
              optionFilterProp="children"
              disabled={!machines.length || (preloadedData && !canEditOrder())}
            >
              {machines.map(machine => (
                <Option key={machine.id} value={machine.id}>
                  {machine.nombre}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </div>

        {/* Personal */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Form.Item
            name="assigned_to_id"
            label="Técnico Asignado"
            rules={[{ required: true, message: 'Seleccione el técnico responsable' }]}
          >
            <Select
              placeholder="Seleccione técnico"
              showSearch
              optionFilterProp="children"
              filterOption={(input, option) =>
                option.children.toLowerCase().includes(input.toLowerCase())
              }
              allowClear
              disabled={preloadedData && !canEditOrder()}
            >
              {users.map(user => (
                <Option key={user.id} value={user.id}>
                  {user.username}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="operator"
            label="Creado por"
          >
            <Input disabled value={currentUser?.username} />
          </Form.Item>
        </div>

        {/* SECCIÓN DE CHECKLIST */}
        <Divider orientation="left">
          <Space>
            <CheckCircleOutlined />
            Lista de Verificación (Checklist)
          </Space>
        </Divider>

        <Form.Item>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Switch
                checked={includeChecklist}
                onChange={handleIncludeChecklistChange}
                disabled={preloadedData && !canEditOrder()}
              />
              <span style={{ marginLeft: 8 }}>
                Incluir checklist en esta orden de trabajo
              </span>
            </div>
            
            {includeChecklist && (
              <Form.Item
                name="task_list_id"
                label="Seleccionar Lista de Tareas"
                rules={[{ required: includeChecklist, message: 'Seleccione una lista de tareas' }]}
              >
                <Select
                  placeholder="Seleccione lista de tareas"
                  onChange={handleTaskListChange}
                  showSearch
                  optionFilterProp="children"
                  disabled={preloadedData && !canEditOrder()}
                >
                  {availableTaskLists.map(taskList => (
                    <Option key={taskList.id} value={taskList.id}>
                      {taskList.name} - {taskList.description}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            )}
          </Space>
        </Form.Item>

        {/* MOSTRAR CHECKLIST SI ESTÁ SELECCIONADO */}
        {includeChecklist && selectedTaskList && checklistSteps.length > 0 && (
          <Card 
            size="small" 
            title={`Checklist: ${selectedTaskList.name}`}
            style={{ marginBottom: 16 }}
          >
            <List
              size="small"
              dataSource={checklistSteps.sort((a, b) => a.step_order - b.step_order)}
              renderItem={(step, index) => {
                const progress = stepProgress[step.id] || {};
                const isCompleted = progress.completed;
                
                return (
                  <List.Item style={{ padding: '8px 0' }}>
                    <Row gutter={16} style={{ width: '100%' }}>
                      <Col span={1}>
                        <Checkbox
                          checked={isCompleted}
                          onChange={(e) => handleStepComplete(step.id, e.target.checked)}
                          disabled={preloadedData && !canEditOrder()}
                        />
                      </Col>
                      <Col span={1}>
                        <Text strong>{step.step_order}</Text>
                      </Col>
                      <Col span={10}>
                        <Text style={{ textDecoration: isCompleted ? 'line-through' : 'none' }}>
                          {step.description}
                        </Text>
                        {step.estimated_time_minutes && (
                          <div>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              <ClockCircleOutlined /> Estimado: {step.estimated_time_minutes} min
                            </Text>
                          </div>
                        )}
                      </Col>
                      <Col span={4}>
                        <InputNumber
                          size="small"
                          placeholder="Min reales"
                          min={0}
                          step={1}
                          value={progress.actual_time_minutes}
                          onChange={(value) => handleStepTime(step.id, value)}
                          disabled={preloadedData && !canEditOrder()}
                          style={{ width: '100%' }}
                        />
                      </Col>
                      <Col span={8}>
                        <Input.TextArea
                          size="small"
                          rows={1}
                          placeholder="Notas del paso..."
                          value={progress.notes}
                          onChange={(e) => handleStepNotes(step.id, e.target.value)}
                          disabled={preloadedData && !canEditOrder()}
                        />
                      </Col>
                    </Row>
                  </List.Item>
                );
              }}
            />
            
            {/* Resumen del progreso */}
            <div style={{ marginTop: 16, padding: 12, backgroundColor: '#f5f5f5', borderRadius: 4 }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Text strong>
                    Progreso: {Object.values(stepProgress).filter(s => s.completed).length} / {checklistSteps.length}
                  </Text>
                </Col>
                <Col span={8}>
                  <Text strong>
                    Tiempo Total: {Object.values(stepProgress).reduce((sum, s) => sum + (s.actual_time_minutes || 0), 0)} min
                  </Text>
                </Col>
                <Col span={8}>
                  <Text strong>
                    Tiempo Estimado: {checklistSteps.reduce((sum, s) => sum + (s.estimated_time_minutes || 0), 0)} min
                  </Text>
                </Col>
              </Row>
            </div>
          </Card>
        )}

        {/* Repuestos */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Form.Item
            name="repuesto_id"
            label="Repuesto (De la máquina seleccionada)"
          >
            <Select
              placeholder={
                !form.getFieldValue('machine_id') 
                  ? "Primero seleccione una máquina"
                  : machineParts.length 
                    ? "Seleccione repuesto de la máquina"
                    : "Esta máquina no tiene repuestos asociados"
              }
              onChange={handleProductSelect}
              allowClear
              showSearch
              optionFilterProp="children"
              disabled={!form.getFieldValue('machine_id') || !machineParts.length || (preloadedData && !canEditOrder())}
            >
              {machineParts.map(part => (
                <Option key={part.inventory_id} value={part.inventory_id}>
                  {part.part?.product_name || `ID: ${part.inventory_id}`}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="quantity_used"
            label="Cantidad Utilizada"
          >
            <InputNumber
              min={0}
              style={{ width: '100%' }}
              placeholder="0"
              disabled={preloadedData && !canEditOrder()}
            />
          </Form.Item>
        </div>

        {/* Códigos FCR */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Form.Item name="failure_code_id" label="Código de Falla">
            <Select
              placeholder="Seleccione código"
              allowClear
              showSearch
              optionFilterProp="children"
              disabled={preloadedData && !canEditOrder()}
            >
              {failureCodes.map(code => (
                <Option key={code.id} value={code.id}>
                  {code.code} - {code.description}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="cause_code_id" label="Código de Causa">
            <Select
              placeholder="Seleccione código"
              allowClear
              showSearch
              optionFilterProp="children"
              disabled={preloadedData && !canEditOrder()}
            >
              {causeCodes.map(code => (
                <Option key={code.id} value={code.id}>
                  {code.code} - {code.description}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="remedy_code_id" label="Código de Solución">
            <Select
              placeholder="Seleccione código"
              allowClear
              showSearch
              optionFilterProp="children"
              disabled={preloadedData && !canEditOrder()}
            >
              {remedyCodes.map(code => (
                <Option key={code.id} value={code.id}>
                  {code.code} - {code.description}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </div>

        {/* Campos adicionales */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Form.Item name="actual_start_time" label="Fecha/Hora de Inicio">
            <DatePicker
              showTime
              format="YYYY-MM-DD HH:mm"
              style={{ width: '100%' }}
              disabled={preloadedData && !canEditOrder()}
            />
          </Form.Item>

          <Form.Item name="actual_end_time" label="Fecha/Hora de Finalización">
            <DatePicker
              showTime
              format="YYYY-MM-DD HH:mm"
              style={{ width: '100%' }}
              disabled={preloadedData && !canEditOrder()}
            />
          </Form.Item>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Form.Item name="downtime_hours" label="Horas de Parada">
            <InputNumber
              min={0}
              step={0.1}
              style={{ width: '100%' }}
              placeholder="0.0"
              disabled={preloadedData && !canEditOrder()}
            />
          </Form.Item>

          <Form.Item name="status" label="Estado">
            <Select
              placeholder="Seleccione estado"
              disabled={preloadedData && !canEditOrder()}
            >
              <Option value="Pendiente">Pendiente</Option>
              <Option value="En curso">En curso</Option>
              <Option value="En revisión">En revisión</Option>
              <Option value="Cerrada">Cerrada</Option>
            </Select>
          </Form.Item>
        </div>

        <Form.Item name="completion_notes" label="Notas de Finalización">
          <TextArea
            rows={3}
            placeholder="Notas sobre la finalización del trabajo..."
            disabled={preloadedData && !canEditOrder()}
          />
        </Form.Item>

        {/* Botones */}
        <div style={{ textAlign: 'right', marginTop: 24 }}>
          <Space>
            <Button onClick={onCancel}>Cancelar</Button>
            <Button type="primary" htmlType="submit" loading={loading}>
              {preloadedData ? 'Actualizar' : 'Crear'} Orden
            </Button>
          </Space>
        </div>
      </Form>
    </Card>
  );
};

export default WorkOrderForm;