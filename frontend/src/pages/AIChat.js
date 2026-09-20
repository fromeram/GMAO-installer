// src/pages/AIChat.js - VERSIÓN COMPLETA CON FUNCIONALIDADES ADICIONALES
import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Input,
  Button,
  Avatar,
  Typography,
  Space,
  Spin,
  Alert,
  Select,
  Tag,
  Row,
  Col,
  Tooltip,
  Modal,
  Badge,
  Empty,
  Switch,
  Slider,
  Dropdown,
  Menu,
  Statistic,
  Divider,
  List,
  Drawer,
  Rate,
  notification
} from 'antd';
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  DeleteOutlined,
  DownloadOutlined,
  SettingOutlined,
  BulbOutlined,
  ToolOutlined,
  WarningOutlined,
  QuestionCircleOutlined,
  ClearOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  SaveOutlined,
  HistoryOutlined,
  StarOutlined,
  ShareAltOutlined,
  CopyOutlined,
  EyeOutlined,
  SwapOutlined, // Reemplazar CompareOutlined
  HeartOutlined,
  DislikeOutlined,
  MoreOutlined
} from '@ant-design/icons';
import { api } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import ModelSelector from '../components/ModelSelector';

const timeAgo = (date) => {
  const now = new Date();
  const diff = now - new Date(date);
  const minutes = Math.floor(diff / 60000);
  
  if (minutes < 1) return 'ahora mismo';
  if (minutes < 60) return `hace ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `hace ${hours} h`;
  const days = Math.floor(hours / 24);
  return `hace ${days} días`;
};

const { TextArea } = Input;
const { Text, Title, Paragraph } = Typography;
const { Option } = Select;

const AIChat = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Estado para modelo de IA - CORREGIDO: cargar desde configuración
  const [selectedModel, setSelectedModel] = useState('');
  const [availableModels, setAvailableModels] = useState([]);
  const [aiConfig, setAiConfig] = useState(null);
  
  // Estado para tipo de asistente
  const [assistantType, setAssistantType] = useState('maintenance-expert');
  
  // Estado de configuración avanzada
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2048);
  
  const [showSuggestions, setShowSuggestions] = useState(true);
  
  // NUEVAS FUNCIONALIDADES
  const [conversationHistory, setConversationHistory] = useState([]);
  const [favoriteMessages, setFavoriteMessages] = useState([]);
  const [showComparator, setShowComparator] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [userPreferences, setUserPreferences] = useState({
    defaultModel: '',
    autoSave: true,
    showTimestamps: true,
    compactMode: false,
    notificationSound: false
  });
  const [modelStats, setModelStats] = useState({});
  const [quickModelSwitch, setQuickModelSwitch] = useState(false);
  
  const messagesEndRef = useRef(null);
  const { currentUser } = useAuth();

  // Cargar configuración al inicializar
  useEffect(() => {
    loadAIConfiguration();
    loadAvailableModels();
    loadUserPreferences();
    loadConversationHistory();
  }, []);

  const loadAIConfiguration = async () => {
    try {
      const response = await api.get('/ai/configuration');
      const config = response.data.configuration;
      setAiConfig(config);
      
      // Establecer modelo por defecto para chat desde la configuración
      if (config.default_chat_model) {
        setSelectedModel(config.default_chat_model);
        console.log('Modelo de chat cargado desde configuración:', config.default_chat_model);
      }
    } catch (error) {
      console.error('Error cargando configuración de IA:', error);
      // Fallback a modelo por defecto si falla
      setSelectedModel('llama3.2:3b');
    }
  };

  const loadAvailableModels = async () => {
    try {
      const response = await api.get('/ai/models/available');
      const models = response.data.models || [];
      setAvailableModels(models);
      
      // Actualizar estadísticas de modelos
      const stats = {};
      models.forEach(model => {
        stats[model.name] = {
          available: model.available,
          speed: model.speed,
          lastUsed: sessionStorage.getItem(`model_last_used_${model.name}`) || null,
          usageCount: parseInt(sessionStorage.getItem(`model_usage_${model.name}`) || '0')
        };
      });
      setModelStats(stats);
    } catch (error) {
      console.error('Error cargando modelos:', error);
    }
  };

  const loadUserPreferences = () => {
    try {
      const saved = sessionStorage.getItem(`ai_chat_preferences_${currentUser?.id}`);
      if (saved) {
        const preferences = JSON.parse(saved);
        setUserPreferences(prev => ({ ...prev, ...preferences }));
        
        // Aplicar preferencias cargadas
        if (preferences.defaultModel && availableModels.some(m => m.name === preferences.defaultModel)) {
          setSelectedModel(preferences.defaultModel);
        }
      }
    } catch (error) {
      console.error('Error cargando preferencias:', error);
    }
  };

  const saveUserPreferences = (newPreferences) => {
    try {
      const updated = { ...userPreferences, ...newPreferences };
      setUserPreferences(updated);
      sessionStorage.setItem(`ai_chat_preferences_${currentUser?.id}`, JSON.stringify(updated));
      notification.success({
        message: 'Preferencias guardadas',
        description: 'Tus preferencias se han guardado correctamente',
        duration: 2
      });
    } catch (error) {
      console.error('Error guardando preferencias:', error);
    }
  };

  const loadConversationHistory = () => {
    try {
      const saved = sessionStorage.getItem(`ai_chat_history_${currentUser?.id}`);
      if (saved) {
        const history = JSON.parse(saved);
        setConversationHistory(history.slice(0, 10)); // Últimas 10 conversaciones
      }
    } catch (error) {
      console.error('Error cargando historial:', error);
    }
  };

  const saveConversationToHistory = () => {
    if (messages.length === 0) return;
    
    try {
      const conversation = {
        id: Date.now(),
        title: messages.find(m => m.type === 'user')?.content?.slice(0, 50) + '...' || 'Conversación sin título',
        messages: messages,
        model: selectedModel,
        assistant: assistantType,
        timestamp: new Date().toISOString(),
        messageCount: messages.filter(m => m.type !== 'system').length
      };
      
      const history = [...conversationHistory];
      history.unshift(conversation);
      const updatedHistory = history.slice(0, 10); // Mantener solo 10
      
      setConversationHistory(updatedHistory);
      sessionStorage.setItem(`ai_chat_history_${currentUser?.id}`, JSON.stringify(updatedHistory));
      
      notification.success({
        message: 'Conversación guardada',
        description: 'La conversación se ha guardado en tu historial',
        duration: 2
      });
    } catch (error) {
      console.error('Error guardando conversación:', error);
    }
  };

  const loadConversationFromHistory = (conversation) => {
    setMessages(conversation.messages);
    setSelectedModel(conversation.model);
    setAssistantType(conversation.assistant);
    notification.info({
      message: 'Conversación cargada',
      description: `Conversación del ${new Date(conversation.timestamp).toLocaleDateString()}`,
      duration: 2
    });
  };

  // Tipos de asistente
  const assistantTypes = [
    {
      id: 'maintenance-expert',
      name: 'Experto en Mantenimiento',
      description: 'Especializado en mantenimiento industrial y predictivo',
      icon: <ToolOutlined />,
      color: '#1890ff'
    },
    {
      id: 'failure-analyst',
      name: 'Analista de Fallos',
      description: 'Análisis de patrones de fallo y causas raíz',
      icon: <WarningOutlined />,
      color: '#fa541c'
    },
    {
      id: 'optimization-advisor',
      name: 'Asesor de Optimización',
      description: 'Optimización de procesos y cronogramas',
      icon: <BulbOutlined />,
      color: '#52c41a'
    },
    {
      id: 'general-assistant',
      name: 'Asistente General',
      description: 'Conversación general y soporte técnico básico',
      icon: <RobotOutlined />,
      color: '#722ed1'
    }
  ];

  // Preguntas sugeridas por tipo de asistente
  const suggestedQuestionsByType = {
    'maintenance-expert': [
      "¿Cuándo debo hacer mantenimiento a la máquina de prensado?",
      "Genera un plan de mantenimiento para esta semana",
      "¿Qué repuestos debería tener en stock?",
      "Calcula el MTBF de mis máquinas principales"
    ],
    'failure-analyst': [
      "Analiza los fallos recientes de la línea de producción",
      "¿Cuál es la causa raíz más probable de este fallo?",
      "Identifica patrones en el historial de averías",
      "¿Qué datos necesitas para el diagnóstico?"
    ],
    'optimization-advisor': [
      "Sugiere mejoras para reducir los tiempos de parada",
      "¿Cómo puedo optimizar mi cronograma de mantenimiento?",
      "¿Qué KPIs debería mejorar primero?",
      "Recomienda estrategias de eficiencia operacional"
    ],
    'general-assistant': [
      "¿Cuál es el estado actual de las máquinas críticas?",
      "Explícame cómo funciona el sistema GMAO",
      "¿Cuáles son las mejores prácticas de mantenimiento?",
      "Ayúdame con este procedimiento de trabajo"
    ]
  };

  // Presets de configuración rápida
  const configPresets = {
    creative: { temperature: 0.9, maxTokens: 3000, name: '🎨 Creativo' },
    balanced: { temperature: 0.7, maxTokens: 2048, name: '⚖️ Equilibrado' },
    focused: { temperature: 0.3, maxTokens: 1024, name: '🎯 Preciso' },
    detailed: { temperature: 0.5, maxTokens: 4096, name: '📋 Detallado' }
  };

  // Scroll automático al final
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (messages.length === 0 && selectedModel) {
      addWelcomeMessage();
    }
  }, [selectedModel, assistantType]);

  const addWelcomeMessage = () => {
    if (!selectedModel) return;
    
    const currentAssistant = assistantTypes.find(a => a.id === assistantType);
    
    const welcomeMessage = {
      id: 'welcome-' + Date.now(),
      type: 'ai',
      content: `¡Hola ${currentUser?.username}! 👋\n\nSoy tu ${currentAssistant?.name || 'asistente de IA'} usando el modelo ${selectedModel}.\n\nPuedo ayudarte con:\n\n• Predicciones de fallos y mantenimiento\n• Análisis de patrones y causas raíz\n• Optimización de cronogramas\n• Recomendaciones de repuestos\n• Interpretación de métricas MTBF/MTTR\n\n¿En qué puedo ayudarte hoy?`,
      timestamp: new Date(),
      model: selectedModel,
      assistantType: assistantType,
      suggestions: suggestedQuestionsByType[assistantType]?.slice(0, 3) || []
    };
    setMessages([welcomeMessage]);
  };

  // Enviar mensaje
  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    const currentAssistant = assistantTypes.find(a => a.id === assistantType);

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
      user: currentUser.username
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setLoading(true);
    setShowSuggestions(false);

    // Actualizar estadísticas de uso del modelo
    updateModelUsage(selectedModel);

    try {
      const response = await api.post('/ai/chat/message', {
        message: currentInput,
        model: selectedModel,
        assistant_type: assistantType,
        assistant_prompt: currentAssistant?.prompt,
        settings: {
          temperature: temperature,
          max_tokens: maxTokens
        },
        context: {
          user_role: currentUser.role,
          user_section: currentUser.section_id,
          conversation_history: messages.slice(-5)
        }
      });

      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: response.data.response,
        timestamp: new Date(),
        model: selectedModel,
        assistantType: assistantType,
        suggestions: response.data.suggestions || [],
        data: response.data.data || null,
        confidence: response.data.confidence || null,
        responseTime: response.data.response_time || null
      };

      setMessages(prev => [...prev, aiMessage]);

      // Auto-guardar si está habilitado
      if (userPreferences.autoSave && messages.length > 5) {
        setTimeout(saveConversationToHistory, 1000);
      }

      // Notificación de sonido si está habilitada
      if (userPreferences.notificationSound) {
        // Aquí podrías añadir un sonido de notificación
        console.log('🔔 Notificación de respuesta');
      }

    } catch (error) {
      console.error('Error enviando mensaje:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: `Lo siento, no he podido procesar tu solicitud. Error: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date(),
        model: selectedModel,
        assistantType: assistantType,
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const updateModelUsage = (modelName) => {
    try {
      const currentCount = parseInt(sessionStorage.getItem(`model_usage_${modelName}`) || '0');
      sessionStorage.setItem(`model_usage_${modelName}`, (currentCount + 1).toString());
      sessionStorage.setItem(`model_last_used_${modelName}`, new Date().toISOString());
      
      // Actualizar estadísticas locales
      setModelStats(prev => ({
        ...prev,
        [modelName]: {
          ...prev[modelName],
          usageCount: currentCount + 1,
          lastUsed: new Date().toISOString()
        }
      }));
    } catch (error) {
      console.error('Error actualizando estadísticas:', error);
    }
  };

  // Manejar Enter
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Usar pregunta sugerida
  const handleSuggestedQuestion = (question) => {
    setInputValue(question);
    setShowSuggestions(false);
  };

  // Cambiar tipo de asistente
  const handleAssistantTypeChange = (typeId) => {
    setAssistantType(typeId);
    const assistant = assistantTypes.find(a => a.id === typeId);
    
    const assistantChangeMessage = {
      id: 'assistant-change-' + Date.now(),
      type: 'system',
      content: `Asistente cambiado a: ${assistant.name}\n${assistant.description}`,
      timestamp: new Date(),
      model: selectedModel,
      assistantType: typeId
    };
    
    setMessages(prev => [...prev, assistantChangeMessage]);
  };

  // Manejar cambio de modelo
  const handleModelChange = (newModel) => {
    setSelectedModel(newModel);
    console.log('Modelo cambiado a:', newModel);
    
    // Actualizar preferencias si está configurado
    if (userPreferences.defaultModel !== newModel) {
      saveUserPreferences({ defaultModel: newModel });
    }
    
    // Mensaje del sistema notificando el cambio
    const modelChangeMessage = {
      id: 'model-change-' + Date.now(),
      type: 'system',
      content: `Modelo cambiado a: ${newModel}`,
      timestamp: new Date(),
      model: newModel,
      assistantType: assistantType
    };
    
    setMessages(prev => [...prev, modelChangeMessage]);
  };

  // Aplicar preset de configuración
  const applyConfigPreset = (presetName) => {
    const preset = configPresets[presetName];
    setTemperature(preset.temperature);
    setMaxTokens(preset.maxTokens);
    
    notification.info({
      message: 'Preset aplicado',
      description: `Configuración ${preset.name} aplicada`,
      duration: 2
    });
  };

  // Limpiar conversación
  const clearConversation = () => {
    Modal.confirm({
      title: '¿Limpiar conversación?',
      content: 'Se eliminará todo el historial de la conversación actual.',
      icon: <DeleteOutlined />,
      okText: 'Sí, limpiar',
      cancelText: 'Cancelar',
      onOk: () => {
        setMessages([]);
        setShowSuggestions(true);
        setTimeout(addWelcomeMessage, 100);
      }
    });
  };

  // Exportar conversación
  const exportConversation = () => {
    if (messages.length === 0) {
      Modal.warning({
        title: 'Sin conversación',
        content: 'No hay mensajes para exportar.'
      });
      return;
    }

    const conversationText = messages.map(msg => {
      const time = msg.timestamp.toLocaleString();
      const sender = msg.type === 'user' ? msg.user : 
                    msg.type === 'system' ? 'Sistema' :
                    `IA (${msg.model})`;
      let content = `[${time}] ${sender}: ${msg.content}`;
      
      if (msg.suggestions && msg.suggestions.length > 0) {
        content += `\n    Sugerencias: ${msg.suggestions.join(', ')}`;
      }
      
      if (msg.responseTime) {
        content += `\n    Tiempo de respuesta: ${msg.responseTime}ms`;
      }
      
      return content;
    }).join('\n\n');

    const element = document.createElement('a');
    const file = new Blob([conversationText], { type: 'text/plain; charset=utf-8' });
    element.href = URL.createObjectURL(file);
    element.download = `conversacion-ia-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);

    notification.success({
      title: 'Conversación exportada',
      content: 'El archivo se ha descargado correctamente.'
    });
  };

  // Copiar mensaje al portapapeles
  const copyMessage = (content) => {
    navigator.clipboard.writeText(content).then(() => {
      notification.success({
        message: 'Copiado',
        description: 'Mensaje copiado al portapapeles',
        duration: 1
      });
    });
  };

  // Añadir a favoritos
  const addToFavorites = (message) => {
    const favorite = {
      id: Date.now(),
      content: message.content,
      model: message.model,
      assistant: message.assistantType,
      timestamp: message.timestamp,
      user: currentUser.username
    };
    
    const newFavorites = [...favoriteMessages, favorite];
    setFavoriteMessages(newFavorites);
    sessionStorage.setItem(`ai_chat_favorites_${currentUser?.id}`, JSON.stringify(newFavorites));
    
    notification.success({
      message: 'Añadido a favoritos',
      description: 'El mensaje se ha guardado en tus favoritos',
      duration: 2
    });
  };

  // Valorar respuesta
  const rateResponse = (messageId, rating) => {
    // Aquí podrías enviar la valoración al servidor
    console.log(`Mensaje ${messageId} valorado con ${rating} estrellas`);
    notification.info({
      message: 'Valoración enviada',
      description: `Has valorado esta respuesta con ${rating} estrella${rating !== 1 ? 's' : ''}`,
      duration: 2
    });
  };

  // Renderizar mensaje con funcionalidades adicionales
  const renderMessage = (message) => {
    const isUser = message.type === 'user';
    const isError = message.type === 'error';
    const isSystem = message.type === 'system';
    
    const currentAssistant = assistantTypes.find(a => a.id === message.assistantType);
    
    const avatarColor = isUser ? '#1890ff' : 
                       isError ? '#ff4d4f' : 
                       isSystem ? '#722ed1' : 
                       (currentAssistant?.color || '#52c41a');

    // Menu de acciones para cada mensaje
    const messageActions = (
      <Menu>
        <Menu.Item key="copy" icon={<CopyOutlined />} onClick={() => copyMessage(message.content)}>
          Copiar texto
        </Menu.Item>
        {!isUser && !isSystem && (
          <Menu.Item key="favorite" icon={<StarOutlined />} onClick={() => addToFavorites(message)}>
            Añadir a favoritos
          </Menu.Item>
        )}
        <Menu.Item key="share" icon={<ShareAltOutlined />}>
          Compartir
        </Menu.Item>
      </Menu>
    );

    return (
      <div
        key={message.id}
        style={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          marginBottom: 16
        }}
      >
        <div
          style={{
            maxWidth: userPreferences.compactMode ? '85%' : '75%',
            display: 'flex',
            flexDirection: isUser ? 'row-reverse' : 'row',
            alignItems: 'flex-start'
          }}
        >
          <Avatar
            icon={isUser ? <UserOutlined /> : 
                  isSystem ? <SettingOutlined /> : 
                  currentAssistant?.icon || <RobotOutlined />}
            style={{
              backgroundColor: avatarColor,
              margin: isUser ? '0 0 0 8px' : '0 8px 0 0',
              flexShrink: 0
            }}
          />
          
          <div
            style={{
              backgroundColor: isUser ? '#e6f7ff' : 
                              isError ? '#fff2f0' : 
                              isSystem ? '#f9f0ff' : '#f6ffed',
              borderRadius: '12px',
              padding: userPreferences.compactMode ? '8px 12px' : '12px 16px',
              border: `1px solid ${isUser ? '#91d5ff' : 
                                  isError ? '#ffccc7' : 
                                  isSystem ? '#d3adf7' : '#b7eb8f'}`,
              position: 'relative',
              wordWrap: 'break-word',
              overflowWrap: 'break-word'
            }}
          >
            {/* Header del mensaje */}
            <div style={{ 
              marginBottom: 8, 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center' 
            }}>
              <div>
                <Text strong>
                  {isUser ? message.user : 
                   isSystem ? 'Sistema' :
                   isError ? 'Error' : 
                   currentAssistant?.name || 'Asistente IA'}
                </Text>
                {message.model && !isUser && !isSystem && (
                  <Tag size="small" color="blue" style={{ marginLeft: 8 }}>
                    {message.model}
                  </Tag>
                )}
                {userPreferences.showTimestamps && (
                  <Text type="secondary" style={{ fontSize: '12px', marginLeft: 8 }}>
                    {timeAgo(message.timestamp)}
                  </Text>
                )}
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                {message.responseTime && (
                  <Tooltip title={`Tiempo de respuesta: ${message.responseTime}ms`}>
                    <Tag icon={<ClockCircleOutlined />} size="small">
                      {message.responseTime}ms
                    </Tag>
                  </Tooltip>
                )}
                
                {message.confidence && (
                  <Tooltip title={`Confianza: ${message.confidence}%`}>
                    <Badge 
                      count={`${message.confidence}%`} 
                      style={{ 
                        backgroundColor: message.confidence > 80 ? '#52c41a' : 
                                       message.confidence > 60 ? '#faad14' : '#fa541c',
                        fontSize: '10px'
                      }} 
                    />
                  </Tooltip>
                )}

                {/* Menu de acciones */}
                <Dropdown overlay={messageActions} trigger={['click']} placement="bottomRight">
                  <Button type="text" size="small" icon={<MoreOutlined />} />
                </Dropdown>
              </div>
            </div>
            
            {/* Contenido del mensaje */}
            <div style={{ 
              margin: 0, 
              whiteSpace: 'pre-wrap',
              maxHeight: 'none',
              overflowY: 'visible',
              wordBreak: 'break-word'
            }}>
              {message.content}
            </div>

            {/* Valoración para respuestas de IA */}
            {!isUser && !isSystem && !isError && (
              <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Text type="secondary" style={{ fontSize: '12px' }}>¿Te ha ayudado?</Text>
                <Rate 
                  allowHalf 
                  defaultValue={0} 
                  style={{ fontSize: '12px' }}
                  onChange={(value) => rateResponse(message.id, value)}
                />
              </div>
            )}

            {/* Sugerencias */}
            {message.suggestions && message.suggestions.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <Text type="secondary" style={{ fontSize: '12px', marginBottom: 4, display: 'block' }}>
                  💡 Sugerencias:
                </Text>
                <div>
                  {message.suggestions.map((suggestion, idx) => (
                    <Tag 
                      key={idx} 
                      color="blue" 
                      style={{ margin: '2px', cursor: 'pointer', fontSize: '11px' }}
                      onClick={() => handleSuggestedQuestion(suggestion)}
                    >
                      {suggestion}
                    </Tag>
                  ))}
                </div>
              </div>
            )}

            {/* Datos estructurados */}
            {message.data && (
              <div style={{ 
                marginTop: 8, 
                padding: 8, 
                backgroundColor: 'rgba(0,0,0,0.02)', 
                borderRadius: 6,
                fontSize: '11px',
                maxHeight: '100px',
                overflow: 'auto'
              }}>
                <Text code style={{ fontSize: '10px' }}>
                  {JSON.stringify(message.data, null, 2)}
                </Text>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const currentAssistant = assistantTypes.find(a => a.id === assistantType);
  const currentSuggestions = suggestedQuestionsByType[assistantType] || [];

  // Modelos más usados para selector rápido
  const topUsedModels = availableModels
    .filter(m => m.available)
    .sort((a, b) => (modelStats[b.name]?.usageCount || 0) - (modelStats[a.name]?.usageCount || 0))
    .slice(0, 3);

  return (
    <div style={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={3} style={{ margin: 0 }}>
              <RobotOutlined style={{ marginRight: 8, color: '#52c41a' }} />
              Asistente IA de Mantenimiento
            </Title>
            <Text type="secondary">
              Conversa con nuestro experto en mantenimiento industrial
            </Text>
          </Col>
          <Col>
            <Space>
              {/* Selector rápido de modelo */}
              {quickModelSwitch && (
                <Select
                  size="small"
                  value={selectedModel}
                  onChange={handleModelChange}
                  style={{ width: 150 }}
                  placeholder="Modelo rápido"
                >
                  {topUsedModels.map(model => (
                    <Option key={model.name} value={model.name}>
                      <Space>
                        <ThunderboltOutlined />
                        {model.displayName}
                      </Space>
                    </Option>
                  ))}
                </Select>
              )}

              <Tooltip title="Selector rápido de modelo">
                <Button 
                  icon={<ThunderboltOutlined />}
                  onClick={() => setQuickModelSwitch(!quickModelSwitch)}
                  type={quickModelSwitch ? "primary" : "default"}
                  size="small"
                />
              </Tooltip>

              <Tooltip title="Comparar modelos">
                <Button 
                  icon={<SwapOutlined />}
                  onClick={() => setShowComparator(!showComparator)}
                  type={showComparator ? "primary" : "default"}
                  size="small"
                />
              </Tooltip>

              <Tooltip title="Historial de conversaciones">
                <Button 
                  icon={<HistoryOutlined />}
                  onClick={() => Modal.info({
                    title: 'Historial de Conversaciones',
                    width: 600,
                    content: (
                      <List
                        dataSource={conversationHistory}
                        renderItem={conv => (
                          <List.Item
                            actions={[
                              <Button 
                                size="small" 
                                type="link"
                                onClick={() => loadConversationFromHistory(conv)}
                              >
                                Cargar
                              </Button>
                            ]}
                          >
                            <List.Item.Meta
                              title={conv.title}
                              description={
                                <div>
                                  <Text type="secondary">{new Date(conv.timestamp).toLocaleDateString()}</Text>
                                  <Tag size="small" style={{ marginLeft: 8 }}>{conv.model}</Tag>
                                  <Text type="secondary" style={{ marginLeft: 8 }}>
                                    {conv.messageCount} mensajes
                                  </Text>
                                </div>
                              }
                            />
                          </List.Item>
                        )}
                      />
                    )
                  })}
                  size="small"
                />
              </Tooltip>

              <Tooltip title="Preferencias">
                <Button 
                  icon={<UserOutlined />}
                  onClick={() => setShowPreferences(true)}
                  size="small"
                />
              </Tooltip>
              
              <Tooltip title="Configuración avanzada">
                <Button 
                  icon={<SettingOutlined />}
                  onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                  type={showAdvancedSettings ? "primary" : "default"}
                  size="small"
                />
              </Tooltip>
              
              <Tooltip title="Guardar conversación">
                <Button 
                  icon={<SaveOutlined />}
                  onClick={saveConversationToHistory}
                  disabled={messages.length === 0}
                  size="small"
                />
              </Tooltip>
              
              <Tooltip title="Limpiar conversación">
                <Button 
                  icon={<ClearOutlined />} 
                  onClick={clearConversation}
                  disabled={messages.length === 0}
                  size="small"
                />
              </Tooltip>
              
              <Tooltip title="Exportar conversación">
                <Button 
                  icon={<DownloadOutlined />} 
                  onClick={exportConversation}
                  disabled={messages.length === 0}
                  size="small"
                />
              </Tooltip>
            </Space>
          </Col>
        </Row>

        {/* Selectores principales */}
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col xs={24} sm={12}>
            <div style={{ marginBottom: 8 }}>
              <Text strong>Tipo de Asistente:</Text>
            </div>
            <Select
              value={assistantType}
              onChange={handleAssistantTypeChange}
              style={{ width: '100%' }}
            >
              {assistantTypes.map(assistant => (
                <Option key={assistant.id} value={assistant.id}>
                  <Space>
                    <span style={{ color: assistant.color }}>{assistant.icon}</span>
                    {assistant.name}
                  </Space>
                </Option>
              ))}
            </Select>
          </Col>
          
          <Col xs={24} sm={12}>
            <div style={{ marginBottom: 8 }}>
              <Text strong>Modelo de IA:</Text>
            </div>
            <ModelSelector
              selectedModel={selectedModel}
              onModelChange={handleModelChange}
              showDetailedInfo={false}
              size="default"
            />
          </Col>
        </Row>

        {/* Presets de configuración rápida */}
        <Row style={{ marginTop: 12 }}>
          <Col span={24}>
            <Text strong style={{ marginRight: 8 }}>Presets rápidos:</Text>
            <Space>
              {Object.entries(configPresets).map(([key, preset]) => (
                <Button
                  key={key}
                  size="small"
                  onClick={() => applyConfigPreset(key)}
                  style={{ fontSize: '11px' }}
                >
                  {preset.name}
                </Button>
              ))}
            </Space>
          </Col>
        </Row>

        {/* Configuración avanzada (colapsable) */}
        {showAdvancedSettings && (
          <div style={{ 
            marginTop: 16, 
            padding: 16, 
            backgroundColor: '#f9f9f9', 
            borderRadius: 8,
            border: '1px solid #e8e8e8'
          }}>
            <Text strong style={{ marginBottom: 12, display: 'block' }}>
              Configuración Avanzada del Modelo
            </Text>
            
            <Row gutter={16}>
              <Col span={12}>
                <div style={{ marginBottom: 16 }}>
                  <Text>Temperatura (Creatividad): {temperature}</Text>
                  <Slider
                    min={0.1}
                    max={1.0}
                    step={0.1}
                    value={temperature}
                    onChange={setTemperature}
                    tooltip={{ formatter: (value) => `${value} (${value < 0.3 ? 'Conservador' : value < 0.7 ? 'Equilibrado' : 'Creativo'})` }}
                  />
                </div>
              </Col>
              
              <Col span={12}>
                <div style={{ marginBottom: 16 }}>
                  <Text>Tokens máximos: {maxTokens}</Text>
                  <Slider
                    min={512}
                    max={4096}
                    step={256}
                    value={maxTokens}
                    onChange={setMaxTokens}
                    tooltip={{ formatter: (value) => `${value} tokens` }}
                  />
                </div>
              </Col>
            </Row>

            {/* Estadísticas de uso de modelos */}
            <Divider orientation="left" orientationMargin="0">
              Estadísticas de Uso
            </Divider>
            <Row gutter={8}>
              {topUsedModels.map(model => (
                <Col span={8} key={model.name}>
                  <Card size="small" style={{ textAlign: 'center' }}>
                    <Statistic
                      title={model.displayName}
                      value={modelStats[model.name]?.usageCount || 0}
                      suffix="usos"
                      valueStyle={{ fontSize: '14px' }}
                    />
                    <Text type="secondary" style={{ fontSize: '10px' }}>
                      {modelStats[model.name]?.lastUsed ? 
                        timeAgo(new Date(modelStats[model.name].lastUsed)) : 
                        'Nunca usado'
                      }
                    </Text>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        )}

        {/* Información del asistente seleccionado */}
        <Alert
          message={
            <Space>
              <span style={{ color: currentAssistant?.color }}>{currentAssistant?.icon}</span>
              {currentAssistant?.name} usando {selectedModel || 'cargando...'}
            </Space>
          }
          description={currentAssistant?.description}
          type="info"
          showIcon={false}
          size="small"
          style={{ marginTop: 12 }}
        />
      </Card>

      {/* Área de chat principal */}
      <Card 
        style={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          padding: 0,
          overflow: 'hidden'
        }}
        bodyStyle={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          padding: 0,
          overflow: 'hidden'
        }}
      >
        {/* Mensajes */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            overflowX: 'hidden',
            padding: '16px',
            backgroundColor: '#fafafa',
            maxHeight: 'calc(100vh - 400px)'
          }}
        >
          {/* Preguntas sugeridas */}
          {showSuggestions && messages.length <= 1 && (
            <div style={{ marginBottom: 24 }}>
              <Text strong style={{ marginBottom: 12, display: 'block' }}>
                <BulbOutlined style={{ marginRight: 8, color: '#faad14' }} />
                Preguntas sugeridas para {currentAssistant?.name}:
              </Text>
              <div>
                {currentSuggestions.map((question, idx) => (
                  <Tag
                    key={idx}
                    color="blue"
                    style={{ 
                      margin: '4px',
                      padding: '6px 12px',
                      cursor: 'pointer',
                      fontSize: '13px',
                      lineHeight: '1.4'
                    }}
                    onClick={() => handleSuggestedQuestion(question)}
                  >
                    <QuestionCircleOutlined style={{ marginRight: 4 }} />
                    {question}
                  </Tag>
                ))}
              </div>
            </div>
          )}

          {/* Lista de mensajes */}
          {messages.length === 0 ? (
            <Empty
              image={<RobotOutlined style={{ fontSize: '64px', color: '#d9d9d9' }} />}
              description={
                <span>
                  No hay mensajes aún.<br />
                  ¡Inicia una conversación con tu asistente de IA!
                </span>
              }
            />
          ) : (
            messages.map(renderMessage)
          )}

          {/* Indicador de escritura */}
          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                <Avatar
                  icon={currentAssistant?.icon || <RobotOutlined />}
                  style={{ backgroundColor: currentAssistant?.color || '#52c41a', marginRight: 8 }}
                />
                <div
                  style={{
                    backgroundColor: '#f6ffed',
                    borderRadius: '12px',
                    padding: '12px 16px',
                    border: '1px solid #b7eb8f'
                  }}
                >
                  <Space>
                    <Spin size="small" />
                    <Text type="secondary">
                      {selectedModel} está analizando y preparando respuesta...
                    </Text>
                  </Space>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input área */}
        <div
          style={{
            borderTop: '1px solid #f0f0f0',
            padding: '16px',
            backgroundColor: 'white',
            flexShrink: 0
          }}
        >
          <Row gutter={8}>
            <Col flex="auto">
              <TextArea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`Pregúntale a ${currentAssistant?.name} usando ${selectedModel || 'modelo de IA'}...`}
                autoSize={{ minRows: 1, maxRows: 4 }}
                disabled={loading || !selectedModel}
                style={{ resize: 'none' }}
              />
            </Col>
            <Col>
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={sendMessage}
                loading={loading}
                disabled={!inputValue.trim() || !selectedModel}
                style={{ height: '100%', minHeight: 32 }}
                size="large"
              >
                {loading ? 'Enviando...' : 'Enviar'}
              </Button>
            </Col>
          </Row>

          {/* Información adicional */}
          <div style={{ 
            marginTop: 8, 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            fontSize: '12px'
          }}>
            <Text type="secondary">
              Presiona <kbd>Enter</kbd> para enviar, <kbd>Shift+Enter</kbd> para nueva línea
            </Text>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Tag size="small" color="blue">
                {selectedModel || 'Sin modelo'}
              </Tag>
              <Badge
                count={messages.filter(m => m.type !== 'system').length}
                style={{ backgroundColor: '#52c41a' }}
                title="Mensajes en conversación"
              />
              <Text type="secondary">mensajes</Text>
              {userPreferences.autoSave && (
                <Tooltip title="Auto-guardado activado">
                  <SaveOutlined style={{ color: '#52c41a' }} />
                </Tooltip>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Drawer de Preferencias */}
      <Drawer
        title="Preferencias del Chat"
        placement="right"
        onClose={() => setShowPreferences(false)}
        visible={showPreferences}
        width={400}
      >
        <div>
          <Title level={4}>Configuración Personal</Title>
          
          <div style={{ marginBottom: 16 }}>
            <Text strong>Modelo preferido por defecto:</Text>
            <Select
              value={userPreferences.defaultModel}
              onChange={(value) => saveUserPreferences({ defaultModel: value })}
              style={{ width: '100%', marginTop: 8 }}
              placeholder="Seleccionar modelo preferido"
            >
              {availableModels.filter(m => m.available).map(model => (
                <Option key={model.name} value={model.name}>
                  {model.displayName}
                </Option>
              ))}
            </Select>
          </div>

          <Divider />

          <div style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Switch
                  checked={userPreferences.autoSave}
                  onChange={(checked) => saveUserPreferences({ autoSave: checked })}
                />
                <Text style={{ marginLeft: 8 }}>Auto-guardar conversaciones</Text>
              </div>

              <div>
                <Switch
                  checked={userPreferences.showTimestamps}
                  onChange={(checked) => saveUserPreferences({ showTimestamps: checked })}
                />
                <Text style={{ marginLeft: 8 }}>Mostrar marcas de tiempo</Text>
              </div>

              <div>
                <Switch
                  checked={userPreferences.compactMode}
                  onChange={(checked) => saveUserPreferences({ compactMode: checked })}
                />
                <Text style={{ marginLeft: 8 }}>Modo compacto</Text>
              </div>

              <div>
                <Switch
                  checked={userPreferences.notificationSound}
                  onChange={(checked) => saveUserPreferences({ notificationSound: checked })}
                />
                <Text style={{ marginLeft: 8 }}>Sonido de notificación</Text>
              </div>
            </Space>
          </div>

          <Divider />

          <Title level={5}>Estadísticas de Uso</Title>
          <div>
            <Text strong>Total de conversaciones guardadas: </Text>
            <Text>{conversationHistory.length}</Text>
          </div>
          <div>
            <Text strong>Mensajes favoritos: </Text>
            <Text>{favoriteMessages.length}</Text>
          </div>
          <div style={{ marginTop: 8 }}>
            <Text strong>Modelo más usado: </Text>
            <Text>
              {Object.entries(modelStats).reduce((a, b) => 
                (modelStats[a[0]]?.usageCount || 0) > (modelStats[b[0]]?.usageCount || 0) ? a : b, 
                ['N/A', {}]
              )[0]}
            </Text>
          </div>

          <Divider />

          <Button 
            type="primary" 
            block
            onClick={() => setShowPreferences(false)}
          >
            Cerrar Preferencias
          </Button>
        </div>
      </Drawer>

      {/* Modal Comparador de Modelos */}
      <Modal
        title="Comparador de Modelos"
        visible={showComparator}
        onCancel={() => setShowComparator(false)}
        footer={null}
        width={800}
      >
        <ModelComparator 
          availableModels={availableModels}
          onClose={() => setShowComparator(false)}
        />
      </Modal>
    </div>
  );
};

// Componente Comparador de Modelos
const ModelComparator = ({ availableModels, onClose }) => {
  const [compareModels, setCompareModels] = useState([]);
  const [testQuestion, setTestQuestion] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const runComparison = async () => {
    if (compareModels.length < 2) {
      notification.warning({
        message: 'Selecciona al menos 2 modelos',
        description: 'Necesitas seleccionar al menos 2 modelos para comparar'
      });
      return;
    }

    if (!testQuestion.trim()) {
      notification.warning({
        message: 'Escribe una pregunta',
        description: 'Necesitas escribir una pregunta para probar los modelos'
      });
      return;
    }

    setLoading(true);
    try {
      const promises = compareModels.map(async model => {
        const response = await api.post('/ai/chat/message', {
          message: testQuestion,
          model: model,
          assistant_type: 'general-assistant'
        });
        return {
          model,
          response: response.data.response,
          responseTime: response.data.response_time,
          confidence: response.data.confidence
        };
      });
      
      const results = await Promise.all(promises);
      setResults(results);
      
      notification.success({
        message: 'Comparación completada',
        description: `Se han comparado ${results.length} modelos exitosamente`
      });
    } catch (error) {
      notification.error({
        message: 'Error en la comparación',
        description: 'Hubo un error al comparar los modelos'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <TextArea 
        placeholder="Escribe una pregunta para probar los modelos..."
        value={testQuestion}
        onChange={(e) => setTestQuestion(e.target.value)}
        autoSize={{ minRows: 2, maxRows: 4 }}
        style={{ marginBottom: 16 }}
      />
      
      <Select
        mode="multiple"
        placeholder="Selecciona modelos a comparar (máximo 4)"
        value={compareModels}
        onChange={setCompareModels}
        style={{ width: '100%', marginBottom: 16 }}
        maxTagCount={4}
      >
        {availableModels.filter(m => m.available).map(model => (
          <Option key={model.name} value={model.name}>
            <Space>
              {model.displayName}
              <Tag size="small" color="blue">{model.speed}</Tag>
            </Space>
          </Option>
        ))}
      </Select>
      
      <div style={{ marginBottom: 16 }}>
        <Button 
          type="primary" 
          onClick={runComparison}
          loading={loading}
          disabled={compareModels.length < 2 || !testQuestion.trim()}
          block
        >
          {loading ? 'Comparando modelos...' : `Comparar ${compareModels.length} modelos`}
        </Button>
      </div>
      
      {results.length > 0 && (
        <div style={{ maxHeight: 400, overflowY: 'auto' }}>
          <Title level={5}>Resultados de la Comparación</Title>
          {results.map((result, index) => (
            <Card 
              size="small" 
              key={result.model} 
              style={{ marginBottom: 12 }}
              title={
                <Space>
                  <Text strong>{availableModels.find(m => m.name === result.model)?.displayName}</Text>
                  <Tag color="blue">#{index + 1}</Tag>
                </Space>
              }
              extra={
                <Space>
                  <Tag color="green">⏱️ {result.responseTime}ms</Tag>
                  <Tag color="orange">📊 {result.confidence}%</Tag>
                </Space>
              }
            >
              <Paragraph 
                style={{ 
                  margin: 0, 
                  maxHeight: 100, 
                  overflowY: 'auto',
                  fontSize: '13px'
                }}
              >
                {result.response}
              </Paragraph>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default AIChat;