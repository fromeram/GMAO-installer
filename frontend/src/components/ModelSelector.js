// src/components/ModelSelector.js - VERSIÓN CORREGIDA
import React, { useState, useEffect } from 'react';
import {
  Select,
  Card,
  Row,
  Col,
  Tag,
  Tooltip,
  Button,
  Space,
  Progress,
  Typography,
  Alert,
  Modal,
  Spin
} from 'antd';
import {
  ThunderboltOutlined,
  ClockCircleOutlined,
  ApiOutlined,
  RobotOutlined,
  BulbOutlined,
  WarningOutlined,
  ToolOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import { api } from '../apiConfig';

const { Option } = Select;
const { Text, Title } = Typography;

const ModelSelector = ({ 
  selectedModel, 
  onModelChange, 
  showDetailedInfo = true,
  size = 'default'
}) => {
  const [availableModels, setAvailableModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [ollamaHealth, setOllamaHealth] = useState(null);
  const [showModelInfo, setShowModelInfo] = useState(false);
  const [selectedModelInfo, setSelectedModelInfo] = useState(null);

  // Mapeo de iconos por modelo
  const modelIcons = {
    'llama3.2:1b': <ThunderboltOutlined />,
    'llama3.2:3b': <ApiOutlined />,
    'llama3:8b': <RobotOutlined />,
    'gemma2:9b': <BulbOutlined />,
    'gemma3:27b': <WarningOutlined />,
    'mistral:7b': <ToolOutlined />,
    'qwen2.5:7b': <ApiOutlined />,
    'deepseek-r1:8b': <RobotOutlined />
  };

  // Colores por velocidad
  const speedColors = {
    'Muy rápido': 'green',
    'Rápido': 'blue',
    'Moderado': 'orange',
    'Lento': 'red'
  };

  // Configuración de progreso por velocidad
  const speedProgress = {
    'Muy rápido': { percent: 90, status: 'success' },
    'Rápido': { percent: 75, status: 'success' },
    'Moderado': { percent: 50, status: 'active' },
    'Lento': { percent: 25, status: 'exception' }
  };

  useEffect(() => {
    loadModelsAndHealth();
  }, []);

  // CORREGIDO: Actualizar información cuando cambia el modelo seleccionado
  useEffect(() => {
    if (selectedModel && availableModels.length > 0) {
      const modelInfo = availableModels.find(m => m.name === selectedModel);
      setSelectedModelInfo(modelInfo);
    }
  }, [selectedModel, availableModels]);

  const loadModelsAndHealth = async () => {
    setLoading(true);
    try {
      const [modelsResponse, healthResponse] = await Promise.all([
        api.get('/ai/models/available'),
        api.get('/ai/models/health')
      ]);

      const models = modelsResponse.data.models || [];
      setAvailableModels(models);
      setOllamaHealth(healthResponse.data);

      console.log('Modelos cargados en ModelSelector:', models);
      
      // CORREGIDO: Si no hay modelo seleccionado pero hay modelos disponibles,
      // usar el primer modelo disponible
      if (!selectedModel && models.length > 0) {
        const firstAvailable = models.find(m => m.available);
        if (firstAvailable && onModelChange) {
          console.log('Seleccionando primer modelo disponible:', firstAvailable.name);
          onModelChange(firstAvailable.name);
        }
      }
    } catch (error) {
      console.error('Error cargando modelos:', error);
      // Usar modelos predefinidos como fallback
      const fallbackModels = [
        {
          name: 'llama3.2:1b',
          displayName: 'Llama 3.2 1B',
          description: 'Modelo ligero y rápido',
          speed: 'Muy rápido',
          quality: 'Buena',
          size: '1.3GB',
          available: false
        },
        {
          name: 'llama3.2:3b',
          displayName: 'Llama 3.2 3B',
          description: 'Equilibrio entre velocidad y calidad',
          speed: 'Rápido',
          quality: 'Muy buena',
          size: '2.0GB',
          available: false
        },
        {
          name: 'deepseek-r1:8b',
          displayName: 'DeepSeek R1 8B',
          description: 'Modelo avanzado para razonamiento',
          speed: 'Moderado',
          quality: 'Excelente',
          size: '4.8GB',
          available: false
        }
      ];
      setAvailableModels(fallbackModels);
    } finally {
      setLoading(false);
    }
  };

  const handleModelChange = (modelName) => {
    console.log('ModelSelector: Cambiando modelo a:', modelName);
    const model = availableModels.find(m => m.name === modelName);
    setSelectedModelInfo(model);
    
    // CORREGIDO: Siempre llamar a onModelChange cuando se selecciona un modelo
    if (onModelChange) {
      onModelChange(modelName);
    }
  };

  const showModelDetails = () => {
    const model = availableModels.find(m => m.name === selectedModel) || selectedModelInfo;
    if (model) {
      setSelectedModelInfo(model);
      setShowModelInfo(true);
    }
  };

  const renderModelOption = (model) => {
    const icon = modelIcons[model.name] || <RobotOutlined />;
    const speedColor = speedColors[model.speed] || 'default';
    const progress = speedProgress[model.speed] || { percent: 50, status: 'active' };

    return (
      <div style={{ padding: '8px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span style={{ color: '#1890ff' }}>{icon}</span>
          <strong>{model.displayName || model.name}</strong>
          <Tag size="small" color={speedColor}>
            {model.speed}
          </Tag>
          {!model.available && (
            <Tag size="small" color="red">
              No disponible
            </Tag>
          )}
        </div>
        
        <div style={{ fontSize: '12px', color: '#666', marginBottom: 4 }}>
          {model.description}
        </div>
        
        {showDetailedInfo && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Text style={{ fontSize: '11px' }}>Velocidad:</Text>
            <Progress 
              percent={progress.percent} 
              size="small" 
              status={progress.status}
              style={{ width: 60, margin: 0 }}
              showInfo={false}
            />
            <Text style={{ fontSize: '11px', color: '#666' }}>
              {model.size}
            </Text>
          </div>
        )}
      </div>
    );
  };

  const currentModel = availableModels.find(m => m.name === selectedModel) || selectedModelInfo;

  // CORREGIDO: Asegurar que el valor del Select coincida con selectedModel
  const selectValue = selectedModel || undefined;

  return (
    <div>
      {/* Selector principal */}
      <div style={{ marginBottom: showDetailedInfo ? 12 : 0 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Select
            value={selectValue} // CORREGIDO: usar selectValue
            onChange={handleModelChange}
            style={{ width: size === 'small' ? 200 : 300 }}
            size={size}
            loading={loading}
            showSearch
            optionFilterProp="children"
            placeholder="Selecciona un modelo de IA"
            notFoundContent={loading ? <Spin size="small" /> : "No hay modelos disponibles"}
            dropdownRender={menu => (
              <div>
                {menu}
                <div style={{ padding: '8px', borderTop: '1px solid #f0f0f0' }}>
                  <Space>
                    <Button 
                      size="small" 
                      icon={<ReloadOutlined />}
                      onClick={loadModelsAndHealth}
                      loading={loading}
                    >
                      Actualizar
                    </Button>
                    <Button 
                      size="small" 
                      icon={<InfoCircleOutlined />}
                      onClick={showModelDetails}
                      type="link"
                      disabled={!selectedModel}
                    >
                      Info del modelo
                    </Button>
                  </Space>
                </div>
              </div>
            )}
          >
            {availableModels.map(model => (
              <Option 
                key={model.name} 
                value={model.name}
                disabled={!model.available}
              >
                {renderModelOption(model)}
              </Option>
            ))}
          </Select>

          {showDetailedInfo && (
            <Tooltip title="Información del modelo seleccionado">
              <Button
                icon={<InfoCircleOutlined />}
                onClick={showModelDetails}
                size={size}
                disabled={!selectedModel}
              />
            </Tooltip>
          )}
        </Space>
      </div>

      {/* Estado de Ollama */}
      {showDetailedInfo && ollamaHealth && (
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
          type={ollamaHealth.connected ? 'success' : 'warning'}
          size="small"
          showIcon={false}
          style={{ marginBottom: 12 }}
        />
      )}

      {/* Información del modelo seleccionado */}
      {showDetailedInfo && currentModel && (
        <Card size="small" style={{ marginBottom: 12 }}>
          <Row gutter={16}>
            <Col span={12}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                {modelIcons[currentModel.name] || <RobotOutlined />}
                <Text strong>{currentModel.displayName}</Text>
              </div>
              <Text style={{ fontSize: '12px', color: '#666' }}>
                {currentModel.description}
              </Text>
            </Col>
            <Col span={12}>
              <div style={{ marginBottom: 4 }}>
                <Text style={{ fontSize: '12px' }}>Velocidad: </Text>
                <Tag color={speedColors[currentModel.speed]} size="small">
                  {currentModel.speed}
                </Tag>
              </div>
              <div style={{ marginBottom: 4 }}>
                <Text style={{ fontSize: '12px' }}>Calidad: </Text>
                <Text style={{ fontSize: '12px' }}>{currentModel.quality}</Text>
              </div>
              <div>
                <Text style={{ fontSize: '12px' }}>Tamaño: </Text>
                <Text style={{ fontSize: '12px' }}>{currentModel.size}</Text>
              </div>
            </Col>
          </Row>
        </Card>
      )}

      {/* Modal de información detallada */}
      <Modal
        title={
          <Space>
            {selectedModelInfo && (modelIcons[selectedModelInfo.name] || <RobotOutlined />)}
            Información del Modelo
          </Space>
        }
        visible={showModelInfo}
        onCancel={() => setShowModelInfo(false)}
        footer={[
          <Button key="close" onClick={() => setShowModelInfo(false)}>
            Cerrar
          </Button>
        ]}
        width={600}
      >
        {selectedModelInfo && (
          <div>
            <Row gutter={16}>
              <Col span={12}>
                <Card title="Especificaciones" size="small">
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>Nombre completo:</Text>
                    <br />
                    <Text>{selectedModelInfo.displayName}</Text>
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>Identificador:</Text>
                    <br />
                    <Text code>{selectedModelInfo.name}</Text>
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>Tamaño:</Text>
                    <br />
                    <Text>{selectedModelInfo.size}</Text>
                  </div>
                  <div>
                    <Text strong>Estado:</Text>
                    <br />
                    <Tag color={selectedModelInfo.available ? 'green' : 'red'}>
                      {selectedModelInfo.available ? 'Disponible' : 'No disponible'}
                    </Tag>
                  </div>
                </Card>
              </Col>
              
              <Col span={12}>
                <Card title="Rendimiento" size="small">
                  <div style={{ marginBottom: 12 }}>
                    <Text strong>Velocidad de respuesta:</Text>
                    <br />
                    <Progress 
                      percent={speedProgress[selectedModelInfo.speed]?.percent || 50}
                      status={speedProgress[selectedModelInfo.speed]?.status || 'active'}
                      format={() => selectedModelInfo.speed}
                    />
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>Calidad:</Text>
                    <br />
                    <Text>{selectedModelInfo.quality}</Text>
                  </div>
                  <div>
                    <Text strong>Caso de uso recomendado:</Text>
                    <br />
                    <Text style={{ fontSize: '12px' }}>
                      {selectedModelInfo.speed === 'Muy rápido' ? 'Consultas rápidas y simples' :
                       selectedModelInfo.speed === 'Rápido' ? 'Conversación general' :
                       selectedModelInfo.speed === 'Moderado' ? 'Análisis técnico detallado' :
                       'Análisis complejo y predicciones avanzadas'}
                    </Text>
                  </div>
                </Card>
              </Col>
            </Row>
            
            <Card title="Descripción" size="small" style={{ marginTop: 16 }}>
              <Text>{selectedModelInfo.description}</Text>
            </Card>

            {/* Recomendaciones de uso */}
            <Card title="Recomendaciones" size="small" style={{ marginTop: 16 }}>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {selectedModelInfo.speed === 'Muy rápido' && (
                  <>
                    <li>Ideal para consultas rápidas y respuestas inmediatas</li>
                    <li>Perfecto para preguntas simples sobre mantenimiento</li>
                    <li>Menor consumo de recursos</li>
                  </>
                )}
                {selectedModelInfo.speed === 'Rápido' && (
                  <>
                    <li>Buen equilibrio entre velocidad y calidad</li>
                    <li>Recomendado para conversación general</li>
                    <li>Análisis básico de problemas</li>
                  </>
                )}
                {selectedModelInfo.speed === 'Moderado' && (
                  <>
                    <li>Análisis técnico más detallado</li>
                    <li>Mejor comprensión de contexto</li>
                    <li>Recomendaciones más precisas</li>
                  </>
                )}
                {selectedModelInfo.speed === 'Lento' && (
                  <>
                    <li>Máxima calidad en las respuestas</li>
                    <li>Análisis complejo y predicciones avanzadas</li>
                    <li>Mejor para tareas críticas</li>
                  </>
                )}
              </ul>
            </Card>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ModelSelector;