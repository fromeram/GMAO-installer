// src/pages/AIAdmin.js - SIN RESTRICCIONES DE PERMISOS
import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Switch,
  Button,
  Select,
  Divider,
  Alert,
  Row,
  Col,
  Typography,
  Table,
  Tag,
  Space,
  Modal,
  Progress,
  Tooltip,
  message
} from 'antd';
import {
  SettingOutlined,
  RobotOutlined,
  SaveOutlined,
  ReloadOutlined,
  ExperimentOutlined,
  DatabaseOutlined,
  ApiOutlined,
  ThunderboltOutlined,
  UserOutlined
} from '@ant-design/icons';
import { api } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';

const { Option } = Select;
const { Title, Text, Paragraph } = Typography;

const AIAdmin = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [models, setModels] = useState([]);
  const [ollamaHealth, setOllamaHealth] = useState(null);
  const [config, setConfig] = useState({});
  
  const { currentUser } = useAuth();

  useEffect(() => {
    loadConfiguration();
    loadModels();
    checkOllamaHealth();
  }, []);

  const loadConfiguration = async () => {
    try {
      const response = await api.get('/ai/configuration');
      const loadedConfig = response.data.configuration || {};
      
      console.log('✅ Configuración cargada:', loadedConfig);
      
      setConfig(loadedConfig);
      form.setFieldsValue(loadedConfig);
      
    } catch (error) {
      console.error('❌ Error cargando configuración:', error);
      message.error('Error cargando configuración. Usando valores por defecto.');
      
      // Usar valores por defecto
      const defaultConfig = {
        default_prediction_model: 'deepseek-r1:8b',
        default_chat_model: 'llama3.2:3b',
        prediction_confidence_threshold: 70,
        auto_prediction_enabled: true,
        prediction_frequency_hours: 24,
        performance_evaluation_days: 30,
        ollama_server_url: 'http://192.168.1.62:11434',
        max_prediction_history_days: 365
      };
      setConfig(defaultConfig);
      form.setFieldsValue(defaultConfig);
    }
  };

  const loadModels = async () => {
    try {
      const response = await api.get('/ai/models/available');
      const modelsData = response.data.models || [];
      setModels(modelsData);
      console.log('🤖 Modelos cargados:', modelsData.length);
    } catch (error) {
      console.error('❌ Error cargando modelos:', error);
      message.warning('Error cargando lista de modelos');
    }
  };

  const checkOllamaHealth = async () => {
    try {
      const response = await api.get('/ai/models/health');
      setOllamaHealth(response.data);
    } catch (error) {
      console.error('❌ Error verificando Ollama:', error);
    }
  };

  const saveConfiguration = async (values) => {
    try {
      setLoading(true);
      
      console.log('💾 Guardando configuración:', values);
      
      const response = await api.post('/ai/configuration', {
        configuration: values
      });
      
      console.log('✅ Respuesta del servidor:', response.data);
      
      // Actualizar estado local
      setConfig(values);
      
      message.success('¡Configuración guardada exitosamente!');
      
    } catch (error) {
      console.error('❌ Error guardando configuración:', error);
      
      const errorMsg = error.response?.data?.detail || error.message || 'Error desconocido';
      message.error(`Error guardando configuración: ${errorMsg}`);
      
    } finally {
      setLoading(false);
    }
  };

  const testModel = async (modelName) => {
    try {
      setLoading(true);
      
      const response = await api.post(`/ai/models/test/${modelName}`);
      
      if (response.data.status === 'success') {
        Modal.success({
          title: '✅ Test Exitoso',
          content: (
            <div>
              <p><strong>Modelo:</strong> {modelName}</p>
              <p><strong>Tiempo de respuesta:</strong> {response.data.response_time_ms}ms</p>
              <p><strong>Respuesta:</strong> {response.data.response}</p>
            </div>
          )
        });
      } else {
        Modal.error({
          title: '❌ Test Fallido',
          content: `Error: ${response.data.message}`
        });
      }
    } catch (error) {
      Modal.error({
        title: '❌ Test Fallido',
        content: `Error probando modelo ${modelName}: ${error.message}`
      });
    } finally {
      setLoading(false);
    }
  };

  const modelColumns = [
    {
      title: 'Modelo',
      dataIndex: 'displayName',
      key: 'name',
      render: (text, record) => (
        <div>
          <strong>{text}</strong>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>{record.name}</Text>
        </div>
      )
    },
    {
      title: 'Estado',
      dataIndex: 'available',
      key: 'available',
      render: (available) => (
        <Tag color={available ? 'green' : 'red'}>
          {available ? 'Disponible' : 'No disponible'}
        </Tag>
      )
    },
    {
      title: 'Velocidad',
      dataIndex: 'speed',
      key: 'speed',
      render: (speed) => {
        const color = speed === 'Muy rápido' ? 'green' : 
                    speed === 'Rápido' ? 'blue' :
                    speed === 'Moderado' ? 'orange' : 'red';
        return <Tag color={color}>{speed}</Tag>;
      }
    },
    {
      title: 'Tamaño',
      dataIndex: 'size',
      key: 'size'
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            size="small" 
            icon={<ExperimentOutlined />}
            onClick={() => testModel(record.name)}
            disabled={!record.available}
            loading={loading}
          >
            Test
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div>
      {/* Header */}
      <Card style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2} style={{ margin: 0 }}>
              <SettingOutlined style={{ marginRight: 8, color: '#722ed1' }} />
              Configuración de IA
            </Title>
            <Text type="secondary">
              <UserOutlined style={{ marginRight: 4 }} />
              Configuración del sistema de inteligencia artificial - Usuario: {currentUser?.username}
            </Text>
          </Col>
          <Col>
            <Space>
              <Button 
                icon={<ReloadOutlined />} 
                onClick={() => {
                  loadConfiguration();
                  loadModels();
                  checkOllamaHealth();
                }}
                loading={loading}
              >
                Recargar Todo
              </Button>
              <Button 
                type="primary" 
                icon={<SaveOutlined />}
                onClick={() => form.submit()}
                loading={loading}
                size="large"
              >
                Guardar Cambios
              </Button>
            </Space>
          </Col>
        </Row>

        {/* Info sobre permisos */}
        <Alert
          message="Configuración Libre"
          description="Cualquier usuario puede modificar los modelos de IA y configuraciones. Los cambios afectan a todos los usuarios del sistema."
          type="info"
          showIcon
          style={{ marginTop: 16 }}
        />

        {/* Estado de Ollama */}
        {ollamaHealth && (
          <Alert
            message={
              <Space>
                <span>Estado de Ollama:</span>
                <Tag color={ollamaHealth.connected ? 'green' : 'red'}>
                  {ollamaHealth.connected ? 'Conectado' : 'Desconectado'}
                </Tag>
                {ollamaHealth.connected && (
                  <span style={{ fontSize: '12px' }}>
                    {ollamaHealth.models_count} modelos disponibles
                  </span>
                )}
              </Space>
            }
            type={ollamaHealth.connected ? 'success' : 'error'}
            style={{ marginTop: 12 }}
            showIcon
          />
        )}
      </Card>

      <Row gutter={16}>
        {/* Configuración Principal */}
        <Col xs={24} lg={12}>
          <Card title="Configuración Principal" extra={<RobotOutlined />}>
            <Form
              form={form}
              layout="vertical"
              onFinish={saveConfiguration}
            >
              <Divider orientation="left">Modelos por Defecto</Divider>
              
              <Form.Item 
                name="default_chat_model" 
                label="Modelo para Chat y Conversación"
                tooltip="Modelo usado para el chat general con usuarios"
              >
                <Select 
                  placeholder="Seleccionar modelo para chat"
                  showSearch
                  optionFilterProp="children"
                >
                  {models.filter(m => m.available).map(model => (
                    <Option key={model.name} value={model.name}>
                      <Space>
                        <span>{model.displayName}</span>
                        <Tag size="small" color="blue">{model.speed}</Tag>
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item 
                name="default_prediction_model" 
                label="Modelo para Predicciones y Análisis"
                tooltip="Modelo usado para análisis predictivo y diagnósticos técnicos"
              >
                <Select 
                  placeholder="Seleccionar modelo para predicciones"
                  showSearch
                  optionFilterProp="children"
                >
                  {models.filter(m => m.available).map(model => (
                    <Option key={model.name} value={model.name}>
                      <Space>
                        <span>{model.displayName}</span>
                        <Tag size="small" color="green">{model.speed}</Tag>
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Divider orientation="left">Configuración de Predicciones</Divider>

              <Form.Item 
                name="prediction_confidence_threshold" 
                label="Umbral de Confianza (%)"
                tooltip="Confianza mínima para considerar una predicción válida"
              >
                <InputNumber 
                  min={50} 
                  max={95} 
                  step={5}
                  style={{ width: '100%' }}
                  formatter={value => `${value}%`}
                  parser={value => value.replace('%', '')}
                />
              </Form.Item>

              <Form.Item 
                name="auto_prediction_enabled" 
                label="Predicciones Automáticas"
                valuePropName="checked"
                tooltip="Activar análisis automático periódico"
              >
                <Switch />
              </Form.Item>

              <Form.Item 
                name="prediction_frequency_hours" 
                label="Frecuencia de Análisis (horas)"
                tooltip="Cada cuántas horas ejecutar análisis automático"
              >
                <InputNumber 
                  min={1} 
                  max={168} 
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Divider orientation="left">Configuración Avanzada</Divider>

              <Form.Item 
                name="ollama_server_url" 
                label="URL del Servidor Ollama"
                tooltip="Dirección del servidor Ollama"
              >
                <Input placeholder="http://192.168.1.62:11434" />
              </Form.Item>

              <Form.Item 
                name="max_prediction_history_days" 
                label="Días de Historial de Predicciones"
                tooltip="Cuántos días mantener el historial"
              >
                <InputNumber 
                  min={30} 
                  max={730} 
                  style={{ width: '100%' }}
                />
              </Form.Item>

              {/* Botón de guardado en el formulario */}
              <Form.Item style={{ marginTop: 24 }}>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  icon={<SaveOutlined />}
                  loading={loading}
                  size="large"
                  block
                >
                  Guardar Configuración
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* Estado de Modelos */}
        <Col xs={24} lg={12}>
          <Card 
            title="Modelos Disponibles" 
            extra={<DatabaseOutlined />}
            style={{ marginBottom: 16 }}
          >
            <Table
              columns={modelColumns}
              dataSource={models}
              rowKey="name"
              size="small"
              pagination={false}
              scroll={{ y: 300 }}
            />
          </Card>

          {/* Estadísticas del Sistema */}
          <Card title="Estado del Sistema" extra={<ApiOutlined />}>
            <Row gutter={16}>
              <Col span={12}>
                <div style={{ textAlign: 'center', marginBottom: 16 }}>
                  <Text strong>Modelos Disponibles</Text>
                  <div style={{ fontSize: '24px', color: '#52c41a' }}>
                    {models.filter(m => m.available).length}/{models.length}
                  </div>
                </div>
              </Col>
              <Col span={12}>
                <div style={{ textAlign: 'center', marginBottom: 16 }}>
                  <Text strong>Configuración Actual</Text>
                  <div style={{ fontSize: '12px', marginTop: 8 }}>
                    <div><strong>Chat:</strong> {config.default_chat_model || 'No configurado'}</div>
                    <div><strong>Predicción:</strong> {config.default_prediction_model || 'No configurado'}</div>
                    <div><strong>Confianza:</strong> {config.prediction_confidence_threshold || 70}%</div>
                  </div>
                </div>
              </Col>
            </Row>

            <Divider />

            <Alert
              message="Información del Sistema"
              description={
                <div style={{ fontSize: '12px' }}>
                  <div>• Configuración guardada en memoria del servidor</div>
                  <div>• Los cambios se aplican inmediatamente</div>
                  <div>• Todos los usuarios pueden cambiar modelos</div>
                  <div>• Estado de Ollama: {ollamaHealth?.connected ? '🟢 Conectado' : '🔴 Desconectado'}</div>
                </div>
              }
              type="info"
              size="small"
              showIcon
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AIAdmin;