// WorkOrderForm.js - VERSIÓN COMPLETA CORREGIDA CON RESTRICCIONES POR ROL
import React, { useState, useEffect } from 'react';
import { Form, Select, Input, DatePicker, InputNumber, Button, Card, Alert, Space, message } from 'antd';
import { useAuth } from '../contexts/AuthContext';
import { fetchWithAuth } from '../apiConfig';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
dayjs.locale('es');

const { Option } = Select;
const { TextArea } = Input;

const WorkOrderForm = ({ sections, inventory, onSubmit, preloadedData = null }) => {
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

  // Determinar el rol del usuario
  const userRole = currentUser?.role || "";
  const isSimplifiedForm = ['Mecánico', 'Jefe de Sección'].includes(userRole);
  const isAdminOrMaintenance = ['Administrador', 'Jefe de Mantenimiento'].includes(userRole);
  const isMecanico = userRole === 'Mecánico';

  // Función para verificar si puede editar la orden
  const canEditOrder = () => {
    if (!preloadedData) return true; // Puede crear nuevas órdenes
    
    // Admin y Jefe de Mantenimiento pueden editar cualquier orden
    if (isAdminOrMaintenance) return true;
    
    // Si la orden está cerrada, solo Admin y Jefe de Mantenimiento pueden editarla
    if (preloadedData.status === 'Cerrada') return false;
    
    // Jefe de Sección puede editar órdenes de su sección que no estén cerradas
    if (userRole === 'Jefe de Sección' && preloadedData.section_id === currentUser.section_id) {
      return true;
    }
    
    // Mecánicos solo pueden editar sus propias órdenes asignadas que no estén cerradas
    if (isMecanico && preloadedData.assigned_to_id === currentUser.id) {
      return true;
    }
    
    return false;
  };

  console.log("Rol del usuario:", userRole);
  console.log("Es formulario simplificado:", isSimplifiedForm);
  console.log("Es admin o jefe:", isAdminOrMaintenance);
  console.log("Puede editar esta orden:", canEditOrder());

  // Verificación de permisos al cargar
  useEffect(() => {
    if (preloadedData && !canEditOrder()) {
      const reason = preloadedData.status === 'Cerrada' 
        ? 'Esta orden está cerrada y no puede ser modificada.'
        : 'No tienes permisos para editar esta orden.';
      
      message.error(reason);
      return;
    }
  }, [preloadedData]);

  // Definir los tipos de trabajo permitidos según el rol
  const allowedWorkTypes = isSimplifiedForm 
    ? ['Preventivo', 'Correctivo', 'Inspección', 'Mejora', 'Modificación', 'Seguridad']
    : ['Preventivo', 'Correctivo', 'Inspección', 'Mejora', 'Modificación', 'Seguridad'];

  // Cargar usuarios (mecánicos)
  useEffect(() => {
    const loadUsers = async () => {
      try {
        const response = await fetchWithAuth('/users');
        // ✅ SOLUCIÓN: Incluir mecánicos (role_id 4) Y Jefe de Mantenimiento (role_id 2)
        const assignableUsers = response.filter(user => 
          user.role_id === 4 || // Mecánico
          user.role_id === 2    // Jefe de Mantenimiento
        );
        setUsers(assignableUsers);
      } catch (error) {
        console.error('Error al cargar usuarios:', error);
        message.error('Error al cargar la lista de técnicos');
      }
    };
    loadUsers();
  }, []);

  // Cargar Códigos de Falla/Causa/Remedio
  useEffect(() => {
    const loadCodes = async () => {
      try {
        const [failRes, causeRes, remedyRes] = await Promise.all([
          fetchWithAuth('/failure-codes'),
          fetchWithAuth('/cause-codes'),
          fetchWithAuth('/remedy-codes')
        ]);
        setFailureCodes(failRes || []);
        setCauseCodes(causeRes || []);
        setRemedyCodes(remedyRes || []);
      } catch (error) {
        console.error("Error al cargar códigos:", error);
        message.error("No se pudieron cargar los códigos de falla/causa/remedio");
      }
    };
    loadCodes();
  }, []);

  // Función para cargar líneas basada en la sección seleccionada
  const handleSectionChange = (sectionId) => {
    form.setFieldsValue({ line_id: undefined, machine_id: undefined });
    const selectedSection = sections.find(s => s.id === sectionId);
    setLines(selectedSection?.lines || []);
    setMachines([]);
    setMachineParts([]);
  };

  // Función para cargar máquinas basada en la línea seleccionada
  const handleLineChange = (lineId) => {
    form.setFieldsValue({ machine_id: undefined });
    const selectedLine = lines.find(l => l.id === lineId);
    setMachines(selectedLine?.machines || []);
    setMachineParts([]);
  };

  // Cargar partes (repuestos) asociadas a la máquina
  const loadMachineParts = async (machineId) => {
    if (!machineId) {
      setMachineParts([]);
      return;
    }
    
    console.log(`🔧 Cargando repuestos para máquina ID: ${machineId}`);
    
    try {
      const response = await fetchWithAuth(`/maquinas/${machineId}/parts`);
      console.log('📦 Repuestos de la máquina recibidos:', response);
      
      if (Array.isArray(response)) {
        setMachineParts(response);
        console.log(`✅ Se cargaron ${response.length} repuestos para la máquina`);
      } else {
        console.error('❌ Respuesta inesperada del BOM:', response);
        setMachineParts([]);
      }
    } catch (error) {
      console.error('❌ Error al cargar repuestos de la máquina:', error);
      message.error('No se pudieron cargar los repuestos asociados a esta máquina');
      setMachineParts([]);
    }
  };

  // Manejar cambio de máquina
  const handleMachineChange = (machineId) => {
    console.log(`🏭 Máquina seleccionada: ${machineId}`);
    form.setFieldsValue({ repuesto_id: undefined });
    setSelectedProduct(null);
    loadMachineParts(machineId);
  };

  // Cargar datos precargados cuando se edita
  useEffect(() => {
    if (preloadedData) {
      console.log("📝 Datos precargados recibidos:", preloadedData);
      
      // Verificar permisos antes de cargar los datos
      if (!canEditOrder()) {
        return; // No cargar datos si no puede editar
      }
      
      // Cargar sección, líneas y máquinas
      const selectedSection = sections.find(s => s.id === preloadedData.section_id);
      if (selectedSection) {
        setLines(selectedSection.lines || []);
        
        const selectedLine = selectedSection.lines?.find(l => l.id === preloadedData.line_id);
        if (selectedLine) {
          setMachines(selectedLine.machines || []);
        }
      }
      
      // Cargar producto seleccionado del BOM de la máquina
      if (preloadedData.repuesto_id && preloadedData.machine_id) {
        loadMachineParts(preloadedData.machine_id);
      }

      // Convertir strings de fecha/hora a objetos dayjs
      const startTimeDayjs = preloadedData.actual_start_time ? dayjs(preloadedData.actual_start_time) : null;
      const endTimeDayjs = preloadedData.actual_end_time ? dayjs(preloadedData.actual_end_time) : null;

      form.setFieldsValue({
        ...preloadedData,
        operator: preloadedData.operator || currentUser.username,
        failure_code_id: preloadedData.failure_code?.id || preloadedData.failure_code_id || undefined,
        cause_code_id: preloadedData.cause_code?.id || preloadedData.cause_code_id || undefined,
        remedy_code_id: preloadedData.remedy_code?.id || preloadedData.remedy_code_id || undefined,
        actual_start_time: startTimeDayjs && startTimeDayjs.isValid() ? startTimeDayjs : null,
        actual_end_time: endTimeDayjs && endTimeDayjs.isValid() ? endTimeDayjs : null
      });
    } else {
      form.resetFields();
      
      // Inicializar valores por defecto según el rol
      if (isSimplifiedForm) {
        form.setFieldsValue({
          work_type: 'Correctivo',
          operator: currentUser?.username,
          assigned_to_id: currentUser?.id,
          quantity_used: 0,
          status: 'Pendiente'
        });
      } else {
        form.setFieldsValue({
          work_type: 'Preventivo',
          status: 'Pendiente',
          operator: currentUser?.username,
          quantity_used: 0
        });
      }
      
      setSelectedProduct(null);
      setMachineParts([]);
    }
  }, [preloadedData, sections, inventory, form, currentUser, isSimplifiedForm]);

  // Manejar selección de producto/repuesto
  const handleProductSelect = (productId) => {
    console.log(`🎯 Producto seleccionado: ${productId}`);
    
    const machinePartItem = machineParts.find(item => item.inventory_id === productId);
    let product = null;
    
    if (machinePartItem) {
      product = {
        id: machinePartItem.inventory_id,
        nombre: machinePartItem.part?.product_name || machinePartItem.part?.nombre,
        quantity: machinePartItem.part?.quantity || machinePartItem.part?.cantidad || 0,
        ...machinePartItem.part
      };
    }
    
    console.log('🔍 Producto encontrado:', product);
    setSelectedProduct(product);
    
    if (!product) {
      form.setFieldsValue({ quantity_used: undefined });
    }
  };

  // onFinish - Función de envío del formulario
  const onFinish = async (values) => {
    // Verificación final de permisos
    if (preloadedData && !canEditOrder()) {
      const reason = preloadedData.status === 'Cerrada' 
        ? 'No puedes modificar una orden que ya está cerrada.'
        : 'No tienes permisos para editar esta orden.';
      
      message.error(reason);
      return;
    }

    setLoading(true);
    try {
      console.log('📤 Enviando formulario con valores:', values);
      
      // Configuración específica para formulario simplificado
      if (isSimplifiedForm && !preloadedData) {
        values.status = 'En revisión';
        values.assigned_to_id = currentUser.id;
        
        if (!values.title && values.details) {
          values.title = values.details;
        }
      }

      // Validar work_type
      if (!allowedWorkTypes.includes(values.work_type)) {
        values.work_type = isSimplifiedForm ? 'Correctivo' : 'Preventivo';
      }

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
        ...(preloadedData && { id: preloadedData.id })
      };

      console.log("📋 Datos FORMATEADOS a enviar:", dataToSubmit);
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
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <div style={{ textAlign: 'center' }}>
          <Button type="primary" onClick={() => window.history.back()}>
            Volver
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card title={preloadedData ? "Editar Orden de Trabajo" : "Nueva Orden de Trabajo"} bordered={false}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={preloadedData ? {} : {
          work_type: isSimplifiedForm ? 'Correctivo' : 'Preventivo',
          status: 'Pendiente',
          operator: currentUser?.username,
          assigned_to_id: isSimplifiedForm ? currentUser?.id : undefined,
          quantity_used: 0
        }}
      >
        {/* Alerta para órdenes cerradas que admin/jefe puede editar */}
        {preloadedData && preloadedData.status === 'Cerrada' && isAdminOrMaintenance && (
          <Alert
            message="Atención: Editando Orden Cerrada"
            description="Esta orden ya está cerrada. Solo administradores y jefes de mantenimiento pueden modificar órdenes cerradas."
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {/* Información Básica */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {!isSimplifiedForm && (
            <Form.Item
              name="title"
              label="Título/Descripción"
              rules={[{ required: !isSimplifiedForm, message: 'El título es obligatorio' }]}
            >
              <Input disabled={preloadedData && !canEditOrder()} />
            </Form.Item>
          )}

          <Form.Item
            name="work_type"
            label="Tipo de Mantenimiento"
            rules={[{ required: true, message: 'Seleccione el tipo de mantenimiento' }]}
          >
            <Select disabled={preloadedData && !canEditOrder()}>
              {allowedWorkTypes.map(type => (
                <Option key={type} value={type}>{type}</Option>
              ))}
            </Select>
          </Form.Item>

          {!isSimplifiedForm && (
            <Form.Item
              name="status"
              label="Estado"
              rules={[{ required: !isSimplifiedForm, message: 'Por favor seleccione un estado' }]}
            >
              <Select disabled={(!isAdminOrMaintenance && preloadedData?.status === 'Cerrada') || (preloadedData && !canEditOrder())}>
                <Option value="Pendiente">Pendiente</Option>
                <Option value="En curso">En curso</Option>
                <Option value="En revisión">En revisión</Option>
                {isAdminOrMaintenance && (
                  <Option value="Cerrada">Cerrada</Option>
                )}
              </Select>
            </Form.Item>
          )}
          
          {isSimplifiedForm && (
            <Form.Item
              name="status"
              hidden={true}
              initialValue="Pendiente"
            >
              <Input type="hidden" />
            </Form.Item>
          )}
        </div>

        {/* Ubicación */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Form.Item
            name="section_id"
            label="Sección"
            rules={[{ required: true, message: 'Seleccione una sección' }]}
          >
            <Select
              placeholder="Seleccione sección"
              onChange={handleSectionChange}
              allowClear
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
            rules={[{ required: true, message: 'Seleccione una línea' }]}
          >
            <Select
              placeholder="Seleccione línea"
              disabled={!form.getFieldValue('section_id') || (preloadedData && !canEditOrder())}
              onChange={handleLineChange}
              allowClear
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
            rules={[{ required: true, message: 'Seleccione una máquina' }]}
          >
            <Select
              placeholder="Seleccione máquina"
              disabled={!form.getFieldValue('line_id') || (preloadedData && !canEditOrder())}
              onChange={handleMachineChange}
              allowClear
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
          {!isSimplifiedForm ? (
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
          ) : (
            <Form.Item
              name="assigned_to_id"
              label="Técnico Asignado"
              hidden={!preloadedData}
            >
              <Input disabled value={currentUser?.username} />
            </Form.Item>
          )}

          <Form.Item
            name="operator"
            label="Creado por"
          >
            <Input disabled value={form.getFieldValue('operator') || currentUser?.username} />
          </Form.Item>
        </div>

        {/* SECCIÓN DE REPUESTOS */}
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
                    ? "Seleccione repuesto" 
                    : "No hay repuestos asociados a esta máquina"
              }
              onChange={handleProductSelect}
              allowClear
              disabled={!machineParts.length || !form.getFieldValue('machine_id') || (preloadedData && !canEditOrder())}
              showSearch
              optionFilterProp="children"
              filterOption={(input, option) =>
                option.children.toLowerCase().includes(input.toLowerCase())
              }
              notFoundContent={
                !form.getFieldValue('machine_id') 
                  ? "Seleccione una máquina primero"
                  : "No hay repuestos asociados"
              }
            >
              {machineParts.map(item => {
                const partName = item.part?.product_name || item.part?.nombre || `Repuesto ID ${item.inventory_id}`;
                const requiredQty = item.quantity || 0;
                const availableStock = item.part?.quantity || item.part?.quantity  || 0;
                
                return (
                  <Option key={item.inventory_id} value={item.inventory_id}>
                    {partName} - Requerido: {requiredQty} (Stock: {availableStock})
                  </Option>
                );
              })}
            </Select>
          </Form.Item>

          {form.getFieldValue('repuesto_id') && (
            <Form.Item
              name="quantity_used"
              label="Cantidad a utilizar"
              rules={[
                { required: !!form.getFieldValue('repuesto_id'), message: 'Ingrese la cantidad' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value && !getFieldValue('repuesto_id')) {
                      return Promise.resolve();
                    }
                    if (value && value <= 0) {
                      return Promise.reject(new Error('La cantidad debe ser mayor a 0'));
                    }
                    if (selectedProduct && value > selectedProduct.cquantity) {
                      return Promise.reject(new Error(`Stock insuficiente (${selectedProduct.quantity} disponible)`));
                    }
                    return Promise.resolve();
                  },
                }),
              ]}
              dependencies={['repuesto_id']}
            >
              <InputNumber 
                min={0} 
                style={{ width: '100%' }} 
                placeholder="Cantidad usada"
                disabled={preloadedData && !canEditOrder()}
              />
            </Form.Item>
          )}
        </div>

        {/* Códigos Falla/Causa/Remedio */}
        {(isAdminOrMaintenance || preloadedData) && (
          <>
            <h3 className="text-lg font-semibold mt-6 mb-3 border-t pt-4">Códigos de Cierre (Opcional)</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Form.Item
                name="failure_code_id"
                label="Código de Falla"
              >
                <Select
                  placeholder="Seleccione código de falla"
                  allowClear
                  showSearch
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    option.children.toLowerCase().includes(input.toLowerCase())
                  }
                  disabled={preloadedData && !canEditOrder()}
                >
                  {failureCodes.map(code => (
                    <Option key={code.id} value={code.id}>
                      {`${code.code} - ${code.description}`}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="cause_code_id"
                label="Código de Causa"
              >
                <Select
                  placeholder="Seleccione código de causa"
                  allowClear
                  showSearch
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    option.children.toLowerCase().includes(input.toLowerCase())
                  }
                  disabled={preloadedData && !canEditOrder()}
                >
                  {causeCodes.map(code => (
                    <Option key={code.id} value={code.id}>
                      {`${code.code} - ${code.description}`}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="remedy_code_id"
                label="Código de Remedio"
              >
                <Select
                  placeholder="Seleccione código de remedio"
                  allowClear
                  showSearch
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    option.children.toLowerCase().includes(input.toLowerCase())
                  }
                  disabled={preloadedData && !canEditOrder()}
                >
                  {remedyCodes.map(code => (
                    <Option key={code.id} value={code.id}>
                      {`${code.code} - ${code.description}`}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </div>
          </>
        )}

        {/* Detalles */}
        <Form.Item
          name="details"
          label={isSimplifiedForm ? "Descripción del trabajo" : "Detalles del trabajo / Notas de Cierre"}
          rules={[{ required: true, message: 'Por favor, proporcione detalles del trabajo' }]}
        >
          <TextArea 
            rows={4} 
            disabled={preloadedData && !canEditOrder()}
          />
        </Form.Item>

        {/* Campo title oculto para formulario simplificado */}
        {isSimplifiedForm && (
          <Form.Item
            name="title"
            hidden={true}
          >
            <Input type="hidden" />
          </Form.Item>
        )}

        {/* Campos de cierre adicionales */}
        {preloadedData && isAdminOrMaintenance && (
          <>
            <h3 className="text-lg font-semibold mt-6 mb-3 border-t pt-4">Información de Cierre</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Form.Item
                name="actual_start_time"
                label="Hora Inicio Real"
              >
                <DatePicker
                  showTime={{ format: 'HH:mm' }}
                  format="DD/MM/YYYY HH:mm"
                  placeholder="Seleccionar fecha y hora"
                  style={{ width: '100%' }}
                  disabled={preloadedData && !canEditOrder()}
                />
              </Form.Item>
              <Form.Item
                name="actual_end_time"
                label="Hora Fin Real"
              >
                <DatePicker
                  showTime={{ format: 'HH:mm' }}
                  format="DD/MM/YYYY HH:mm"
                  placeholder="Seleccionar fecha y hora"
                  style={{ width: '100%' }}
                  disabled={preloadedData && !canEditOrder()}
                />
              </Form.Item>
              <Form.Item
                name="downtime_hours"
                label="Horas de Inactividad"
              >
                <InputNumber 
                  min={0} 
                  step={0.1} 
                  style={{ width: '100%' }} 
                  placeholder="Ej: 1.5"
                  disabled={preloadedData && !canEditOrder()}
                />
              </Form.Item>
            </div>
            <Form.Item
              name="completion_notes"
              label="Notas Adicionales de Cierre"
            >
              <TextArea 
                rows={3} 
                disabled={preloadedData && !canEditOrder()}
              />
            </Form.Item>
          </>
        )}

        {/* Botones */}
        <div className="flex justify-end space-x-4 mt-6">
          {canEditOrder() && (
            <Button type="primary" htmlType="submit" loading={loading}>
              {preloadedData ? 'Actualizar Orden' : 'Crear Orden'}
            </Button>
          )}
        </div>
      </Form>

      {/* Alerta de Stock Bajo */}
      {selectedProduct && selectedProduct.cantidad < 5 && (
        <Alert
          message="Stock Bajo"
          description={`El producto seleccionado '${selectedProduct.nombre || selectedProduct.product_name}' tiene un stock bajo (${selectedProduct.cantidad} unidades)`}
          type="warning"
          showIcon
          className="mt-4"
        />
      )}

      {/* Debug Info - Solo en desarrollo */}
      {process.env.NODE_ENV === 'development' && (
        <Card title="Debug Info" style={{ marginTop: 16 }} size="small">
          <div style={{ fontSize: '12px', fontFamily: 'monospace' }}>
            <div>🔧 Machine Parts Count: {machineParts.length}</div>
            <div>🏭 Selected Machine: {form.getFieldValue('machine_id')}</div>
            <div>👤 User Role: {userRole}</div>
            <div>📝 Is Simplified Form: {isSimplifiedForm.toString()}</div>
            {machineParts.length > 0 && (
              <div>🎯 First Machine Part: {JSON.stringify(machineParts[0], null, 2)}</div>
            )}
          </div>
        </Card>
      )}
    </Card>
  );
};

export default WorkOrderForm;