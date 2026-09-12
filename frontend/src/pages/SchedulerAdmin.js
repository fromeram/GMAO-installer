// src/pages/SchedulerAdmin.js - VERSIÓN COMPLETAMENTE CORREGIDA
import React, { useState, useEffect } from 'react';
import { 
  Card, Typography, Table, Button, Switch, Space, Tabs, Input, Form, 
  Select, InputNumber, TimePicker, message, Spin, Alert, Modal, Tag, Collapse, Empty
} from 'antd';
import { 
  ReloadOutlined, PlayCircleOutlined, PauseCircleOutlined, 
  SettingOutlined, ClockCircleOutlined, SendOutlined, RobotOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;
const { Panel } = Collapse;
const { TextArea } = Input;

const SchedulerAdmin = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [schedulerStatus, setSchedulerStatus] = useState({
    running: false,
    job_count: 0,
    next_run_times: {},
    config: { email: {}, tasks: {}, ai_predictions: {} },
    available_tasks: []
  });
  const [configForm] = Form.useForm();
  const [logData, setLogData] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [runningTask, setRunningTask] = useState(null);

  // ✅ MAPEO SEGURO DE NOMBRES EN ESPAÑOL
  const getTaskDisplayName = (taskId) => {
    const safeTaskId = String(taskId || '').toLowerCase();
    
    const taskNames = {
      'generate_daily_orders': 'Generar Órdenes Diarias',
      'generate_orders': 'Generar Órdenes Diarias',
      'check_upcoming_maintenance': 'Verificar Mantenimientos Próximos',
      'check_upcoming': 'Verificar Mantenimientos Próximos',
      'check_low_stock': 'Verificar Stock Bajo',
      'check_stock': 'Verificar Stock Bajo',
      'check_overdue_tasks': 'Verificar Órdenes Vencidas',
      'check_overdue': 'Verificar Órdenes Vencidas',
      'generate_weekly_metrics': 'Generar Métricas Semanales',
      'generate_metrics': 'Generar Métricas Semanales',
      'update_maintenance_backlog': 'Actualizar Backlog de Mantenimiento',
      'maintenance_backup': 'Actualizar Backlog de Mantenimiento',
      'run_ai_predictions': 'Predicciones de IA',
      'ai_predictions': 'Predicciones de IA',
      'cleanup_old_audit_logs': 'Limpiar Logs de Auditoría',
      'cleanup_audit_logs': 'Limpiar Auditoría'
    };
    
    if (taskNames[safeTaskId]) {
      return taskNames[safeTaskId];
    }
    
    try {
      return safeTaskId.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    } catch (error) {
      console.warn('Error processing task name:', error);
      return 'Tarea Desconocida';
    }
  };

  // Cargar estado inicial
  useEffect(() => {
    fetchSchedulerStatus();
  }, []);

  // Función para cargar el estado del scheduler
  const fetchSchedulerStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchWithAuth('/scheduler/status');
      console.log('Scheduler status response:', response);
      
      setSchedulerStatus({
        running: response.running || false,
        job_count: response.job_count || 0,
        next_run_times: response.next_run_times || {},
        config: response.config || { email: {}, tasks: {}, ai_predictions: {} },
        available_tasks: response.available_tasks || []
      });
      
      // ✅ INICIALIZAR FORMULARIO CON CONFIGURACIÓN ACTUAL
      const currentConfig = response.config || {};
      
      // Asegurar que ai_predictions existe
      if (!currentConfig.ai_predictions) {
        currentConfig.ai_predictions = {
          max_machines_per_cycle: 3,
          cooldown_minutes: 10,
          confidence_threshold: 60,
          priority_sections: "1,4,7"
        };
      }
      
      configForm.setFieldsValue({
        email: currentConfig.email || {},
        tasks: currentConfig.tasks || {},
        ai_predictions: currentConfig.ai_predictions || {}
      });
      
    } catch (err) {
      console.error("Error fetching scheduler status:", err);
      setError("No se pudo cargar el estado del scheduler. Por favor, verifique que tiene permisos de administrador.");
    } finally {
      setLoading(false);
    }
  };

  // Iniciar el scheduler
  const startScheduler = async () => {
    try {
      await fetchWithAuth('/scheduler/start', { method: 'POST' });
      message.success("Scheduler iniciado correctamente");
      fetchSchedulerStatus();
    } catch (err) {
      message.error("Error al iniciar el scheduler");
      console.error(err);
    }
  };

  // Detener el scheduler
  const stopScheduler = async () => {
    Modal.confirm({
      title: '¿Detener el Scheduler?',
      content: 'Esto detendrá todas las tareas programadas. ¿Seguro que desea continuar?',
      okText: 'Sí, detener',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await fetchWithAuth('/scheduler/stop', { method: 'POST' });
          message.success("Scheduler detenido correctamente");
          fetchSchedulerStatus();
        } catch (err) {
          message.error("Error al detener el scheduler");
          console.error(err);
        }
      }
    });
  };

  // Recargar el scheduler
  const reloadScheduler = async () => {
    try {
      await fetchWithAuth('/scheduler/reload', { method: 'POST' });
      message.success("Scheduler recargado correctamente");
      fetchSchedulerStatus();
    } catch (err) {
      message.error("Error al recargar el scheduler");
      console.error(err);
    }
  };

  // ✅ ACTUALIZAR CONFIGURACIÓN CON SOPORTE COMPLETO PARA IA
  const updateConfig = async (values) => {
    try {
      // ✅ LIMPIAR Y VALIDAR DATOS INCLUYENDO IA
      const cleanConfig = {
        email: values.email || {},
        tasks: values.tasks || {},
        ai_predictions: values.ai_predictions || {}
      };
      
      // Limpiar valores undefined/null del email
      if (cleanConfig.email) {
        Object.keys(cleanConfig.email).forEach(key => {
          if (cleanConfig.email[key] === undefined || cleanConfig.email[key] === null) {
            delete cleanConfig.email[key];
          }
        });
      }
      
      // Limpiar valores undefined/null de las tareas
      if (cleanConfig.tasks) {
        Object.keys(cleanConfig.tasks).forEach(taskKey => {
          if (cleanConfig.tasks[taskKey]) {
            Object.keys(cleanConfig.tasks[taskKey]).forEach(field => {
              if (cleanConfig.tasks[taskKey][field] === undefined || cleanConfig.tasks[taskKey][field] === null) {
                delete cleanConfig.tasks[taskKey][field];
              }
            });
          }
        });
      }
      
      // ✅ LIMPIAR CONFIGURACIÓN DE IA
      if (cleanConfig.ai_predictions) {
        Object.keys(cleanConfig.ai_predictions).forEach(key => {
          if (cleanConfig.ai_predictions[key] === undefined || cleanConfig.ai_predictions[key] === null) {
            delete cleanConfig.ai_predictions[key];
          }
        });
      }
      
      console.log("✅ Configuración que se va a enviar:", cleanConfig);
      
      await fetchWithAuth('/scheduler/config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(cleanConfig),
      });
      
      message.success("Configuración actualizada correctamente");
      fetchSchedulerStatus();
    } catch (err) {
      console.error("Error al actualizar configuración:", err);
      message.error("Error al actualizar la configuración");
    }
  };

  // Cargar logs
  const fetchLogs = async () => {
    setLoadingLogs(true);
    try {
      const response = await fetchWithAuth('/scheduler/logs');
      setLogData(response);
    } catch (err) {
      console.error("Error fetching scheduler logs:", err);
      message.error("No se pudieron cargar los logs del scheduler");
    } finally {
      setLoadingLogs(false);
    }
  };

  // Ejecutar tarea ahora
  const runTaskNow = async (taskId) => {
    try {
      setRunningTask(taskId);
      await fetchWithAuth('/scheduler/run-task', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ task_name: taskId }),
      });
      message.success(`Tarea iniciada correctamente`);
      setTimeout(fetchSchedulerStatus, 1000);
    } catch (err) {
      message.error(`Error al ejecutar tarea`);
      console.error(err);
    } finally {
      setRunningTask(null);
    }
  };

  // Función para formatear tiempo de próxima ejecución
  const formatNextRun = (timeString) => {
    if (!timeString || timeString === 'N/A' || timeString === 'No programado') {
      return 'No programado';
    }
    try {
      return dayjs(timeString).format('DD/MM/YYYY HH:mm:ss');
    } catch (error) {
      return 'Fecha inválida';
    }
  };

  // ✅ PROCESAR DATOS DE TAREAS DE FORMA SEGURA
  const processTaskData = () => {
    const tasks = [];
    const nextRunTimes = schedulerStatus.next_run_times || {};
    
    Object.entries(nextRunTimes).forEach(([taskId, nextRun]) => {
      try {
        const safeTaskId = String(taskId || 'unknown');
        tasks.push({
          key: safeTaskId,
          id: safeTaskId,
          name: getTaskDisplayName(safeTaskId),
          next_run: nextRun
        });
      } catch (error) {
        console.warn('Error processing task:', taskId, error);
      }
    });
    
    return tasks;
  };

  // Render de la interfaz
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <p>Cargando configuración del scheduler...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Error de Permisos"
        description={error}
        type="error"
        showIcon
        style={{ margin: '20px' }}
        action={
          <Button onClick={fetchSchedulerStatus} type="primary">
            Reintentar
          </Button>
        }
      />
    );
  }

  const taskData = processTaskData();

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <SettingOutlined style={{ marginRight: '8px' }} />
        Administración del Scheduler
      </Title>

      <Tabs defaultActiveKey="status">
        <TabPane tab="Estado del Sistema" key="status">
          <Card title="Estado Actual del Scheduler">
            <div style={{ marginBottom: '16px' }}>
              <Space size="large">
                <div>
                  <Text strong>Estado: </Text>
                  <Tag color={schedulerStatus.running ? 'green' : 'red'}>
                    {schedulerStatus.running ? 'EJECUTÁNDOSE' : 'DETENIDO'}
                  </Tag>
                </div>
                <div>
                  <Text strong>Trabajos Activos: </Text>
                  <Tag color="blue">{schedulerStatus.job_count}</Tag>
                </div>
              </Space>
            </div>

            <Space style={{ marginBottom: '16px' }}>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={startScheduler}
                disabled={schedulerStatus.running}
              >
                Iniciar Scheduler
              </Button>
              <Button
                danger
                icon={<PauseCircleOutlined />}
                onClick={stopScheduler}
                disabled={!schedulerStatus.running}
              >
                Detener Scheduler
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={reloadScheduler}
              >
                Recargar Configuración
              </Button>
              <Button
                onClick={fetchSchedulerStatus}
              >
                Actualizar Estado
              </Button>
            </Space>

            <Title level={4}>Tareas Programadas</Title>
            {taskData.length > 0 ? (
              <Table
                columns={[
                  {
                    title: 'Tarea',
                    dataIndex: 'name',
                    key: 'name',
                    render: (text, record) => (
                      <Space>
                        {record.id.includes('ai') ? <RobotOutlined style={{ color: '#1890ff' }} /> : <ClockCircleOutlined />}
                        <Text strong>{text}</Text>
                        {record.id.includes('ai') && <Tag color="blue">IA</Tag>}
                      </Space>
                    ),
                  },
                  {
                    title: 'Próxima Ejecución',
                    dataIndex: 'next_run',
                    key: 'next_run',
                    render: (text) => (
                      <Text type={text && text !== 'No programado' && text !== 'N/A' ? 'secondary' : 'warning'}>
                        {formatNextRun(text)}
                      </Text>
                    ),
                  },
                  {
                    title: 'Acciones',
                    key: 'actions',
                    render: (_, record) => (
                      <Space>
                        <Button
                          type="primary"
                          size="small"
                          icon={<SendOutlined />}
                          loading={runningTask === record.id}
                          onClick={() => runTaskNow(record.id)}
                        >
                          Ejecutar Ahora
                        </Button>
                      </Space>
                    ),
                  },
                ]}
                dataSource={taskData}
                pagination={false}
                size="middle"
              />
            ) : (
              <Empty
                description="No hay tareas programadas"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </Card>
        </TabPane>

        <TabPane tab="Configuración" key="config">
          <Card title="Configuración del Scheduler">
            <Form
              form={configForm}
              layout="vertical"
              onFinish={updateConfig}
            >
              <Collapse defaultActiveKey={['1', '2', '3']}>
                <Panel header="Configuración de Correo Electrónico" key="1">
                  <Form.Item
                    name={['email', 'enabled']}
                    valuePropName="checked"
                    label="Activar envío de correos"
                  >
                    <Switch />
                  </Form.Item>
                  
                  <Form.Item
                    name={['email', 'smtp_server']}
                    label="Servidor SMTP"
                  >
                    <Input placeholder="smtp.example.com" />
                  </Form.Item>
                  
                  <Form.Item
                    name={['email', 'smtp_port']}
                    label="Puerto SMTP"
                  >
                    <InputNumber min={1} max={65535} />
                  </Form.Item>
                  
                  <Form.Item
                    name={['email', 'username']}
                    label="Usuario"
                  >
                    <Input placeholder="usuario@example.com" />
                  </Form.Item>
                  
                  <Form.Item
                    name={['email', 'password']}
                    label="Contraseña"
                  >
                    <Input.Password placeholder="Contraseña" />
                  </Form.Item>
                  
                  <Form.Item
                    name={['email', 'sender']}
                    label="Remitente"
                  >
                    <Input placeholder="GMAO System <sistema@example.com>" />
                  </Form.Item>
                </Panel>
                
                <Panel header="Configuración de Tareas" key="2">
                  {Object.entries(schedulerStatus.config.tasks || {}).map(([taskId, taskConfig]) => {
                    if (!taskId || typeof taskConfig !== 'object') {
                      return null;
                    }
                    
                    const safeTaskId = String(taskId);
                    
                    return (
                      <div key={safeTaskId} style={{ marginBottom: '20px', padding: '10px', border: '1px solid #f0f0f0', borderRadius: '4px' }}>
                        <Title level={5}>
                          <Space>
                            {safeTaskId.includes('ai') && <RobotOutlined style={{ color: '#1890ff' }} />}
                            {getTaskDisplayName(safeTaskId)}
                            {safeTaskId.includes('ai') && <Tag color="blue">IA</Tag>}
                          </Space>
                        </Title>
                        
                        {taskConfig.description && (
                          <Paragraph type="secondary" style={{ fontSize: '12px', marginBottom: '8px' }}>
                            {taskConfig.description}
                          </Paragraph>
                        )}
                        
                        <Form.Item
                          name={['tasks', safeTaskId, 'enabled']}
                          valuePropName="checked"
                          label="Activar tarea"
                        >
                          <Switch />
                        </Form.Item>
                        
                        <Form.Item
                          name={['tasks', safeTaskId, 'cron']}
                          label="Programación CRON"
                          help="Formato: minuto hora día mes día_semana (ej: */10 * * * * = cada 10 minutos)"
                        >
                          <Input placeholder="*/10 * * * *" />
                        </Form.Item>
                        
                        {(safeTaskId === 'generate_orders' || safeTaskId === 'check_upcoming') && (
                          <Form.Item
                            name={['tasks', safeTaskId, 'advance_days']}
                            label={safeTaskId === 'generate_orders' ? "Días de adelanto para generar órdenes" : "Días de adelanto para alertas"}
                            help={safeTaskId === 'generate_orders' ? "Generar órdenes X días antes" : "Alertar X días antes del vencimiento"}
                          >
                            <InputNumber min={0} max={30} placeholder="7" />
                          </Form.Item>
                        )}
                      </div>
                    );
                  })}
                </Panel>

                {/* ✅ PANEL NUEVO PARA CONFIGURACIÓN DE IA */}
                <Panel header={
                  <span>
                    <RobotOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                    Configuración de Predicciones IA
                  </span>
                } key="3">
                  <Alert
                    message="Configuración de Inteligencia Artificial"
                    description="Ajusta los parámetros para las predicciones automáticas de mantenimiento usando IA."
                    type="info"
                    showIcon
                    style={{ marginBottom: '16px' }}
                  />
                  
                  <Form.Item
                    name={['ai_predictions', 'max_machines_per_cycle']}
                    label="Máquinas por Ciclo"
                    help="Número máximo de máquinas a analizar en cada ciclo de predicciones"
                  >
                    <InputNumber min={1} max={10} placeholder="3" />
                  </Form.Item>
                  
                  <Form.Item
                    name={['ai_predictions', 'cooldown_minutes']}
                    label="Tiempo de Espera (minutos)"
                    help="Minutos de espera antes de analizar la misma máquina nuevamente"
                  >
                    <InputNumber min={5} max={120} placeholder="10" />
                  </Form.Item>
                  
                  <Form.Item
                    name={['ai_predictions', 'confidence_threshold']}
                    label="Umbral de Confianza (%)"
                    help="Porcentaje mínimo de confianza para guardar una predicción"
                  >
                    <InputNumber min={30} max={95} placeholder="60" />
                  </Form.Item>
                  
                  <Form.Item
                    name={['ai_predictions', 'priority_sections']}
                    label="Secciones Prioritarias"
                    help="IDs de secciones separados por comas (ej: 1,4,7)"
                  >
                    <Input placeholder="1,4,7" />
                  </Form.Item>
                  
                  <Form.Item
                    name={['ai_predictions', 'auto_retry_failed']}
                    valuePropName="checked"
                    label="Reintentar Fallos Automáticamente"
                  >
                    <Switch />
                  </Form.Item>
                </Panel>
              </Collapse>

              <Form.Item style={{ marginTop: '16px' }}>
                <Button type="primary" htmlType="submit">
                  Guardar Configuración
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        <TabPane tab="Logs del Sistema" key="logs">
          <Card 
            title="Logs del Scheduler"
            extra={
              <Button 
                onClick={fetchLogs}
                loading={loadingLogs}
                icon={<ReloadOutlined />}
              >
                Cargar Logs
              </Button>
            }
          >
            {logData.length > 0 ? (
              <div style={{ 
                backgroundColor: '#f6f8fa', 
                padding: '12px', 
                borderRadius: '6px',
                fontFamily: 'monospace',
                fontSize: '12px',
                maxHeight: '400px',
                overflowY: 'auto'
              }}>
                {logData.map((line, index) => (
                  <div key={index} style={{ marginBottom: '2px' }}>
                    {String(line || '')}
                  </div>
                ))}
              </div>
            ) : (
              <Empty description="No hay logs disponibles" />
            )}
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default SchedulerAdmin;