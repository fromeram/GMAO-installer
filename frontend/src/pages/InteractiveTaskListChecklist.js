import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Checkbox, 
  Progress, 
  Typography, 
  Button, 
  Space, 
  Tag, 
  Input,
  message,
  Modal,
  Divider,
  Tooltip,
  Badge,
  Alert
} from 'antd';
import { 
  CheckCircleOutlined, 
  ClockCircleOutlined, 
  PlayCircleOutlined,
  PauseCircleOutlined,
  FileTextOutlined,
  SaveOutlined,
  PrinterOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const InteractiveTaskListChecklist = ({ 
  workOrder, 
  taskList, 
  onProgressUpdate,
  onComplete,
  readOnly = false 
}) => {
  const [checkedSteps, setCheckedSteps] = useState({});
  const [stepNotes, setStepNotes] = useState({});
  const [stepTimes, setStepTimes] = useState({});
  const [currentStep, setCurrentStep] = useState(null);
  const [startTime, setStartTime] = useState(null);
  const [totalElapsedTime, setTotalElapsedTime] = useState(0);
  const [isWorkInProgress, setIsWorkInProgress] = useState(false);
  const [currentTimer, setCurrentTimer] = useState(0);

  // Calcular progreso
  const totalSteps = taskList?.steps?.length || 0;
  const completedSteps = Object.values(checkedSteps).filter(Boolean).length;
  const progressPercent = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

  // Estado de guardado automático
  const [lastSaved, setLastSaved] = useState(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Timer para el paso actual
  useEffect(() => {
    let interval = null;
    if (isWorkInProgress && startTime) {
      interval = setInterval(() => {
        const now = new Date();
        const elapsed = Math.floor((now - startTime) / 1000 / 60); // minutos
        setCurrentTimer(elapsed);
      }, 1000);
    } else {
      setCurrentTimer(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isWorkInProgress, startTime]);

  useEffect(() => {
    // Cargar progreso guardado si existe
    loadSavedProgress();
  }, [workOrder?.id]);

  useEffect(() => {
    // Auto-save cada 30 segundos si hay cambios
    const interval = setInterval(() => {
      if (hasUnsavedChanges) {
        saveProgress();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [hasUnsavedChanges, checkedSteps, stepNotes]);

  const loadSavedProgress = async () => {
    try {
      // Intentar cargar desde sessionStorage como fallback
      const saved = sessionStorage.getItem(`checklist_${workOrder?.id}`);
      if (saved) {
        const data = JSON.parse(saved);
        setCheckedSteps(data.checkedSteps || {});
        setStepNotes(data.stepNotes || {});
        setStepTimes(data.stepTimes || {});
        setTotalElapsedTime(data.totalElapsedTime || 0);
      }
    } catch (error) {
      console.error('Error cargando progreso:', error);
    }
  };

  const saveProgress = async () => {
    try {
      const progressData = {
        workOrderId: workOrder?.id,
        checkedSteps,
        stepNotes,
        stepTimes,
        totalElapsedTime,
        lastUpdated: new Date().toISOString(),
        progressPercent
      };

      // Guardar localmente primero
      sessionStorage.setItem(`checklist_${workOrder?.id}`, JSON.stringify(progressData));
      
      // Llamada al backend si está disponible
      if (onProgressUpdate) {
        await onProgressUpdate(progressData);
      }

      setLastSaved(new Date());
      setHasUnsavedChanges(false);
      message.success('Progreso guardado automáticamente');
    } catch (error) {
      console.error('Error guardando progreso:', error);
      message.error('Error al guardar el progreso');
    }
  };

  const handleStepCheck = (stepId, checked) => {
    if (readOnly) return;

    const newCheckedSteps = { ...checkedSteps, [stepId]: checked };
    setCheckedSteps(newCheckedSteps);
    setHasUnsavedChanges(true);

    if (checked && currentStep === stepId) {
      // Completar paso actual
      completeCurrentStep();
    }

    // Si se completan todos los pasos
    const newCompletedCount = Object.values(newCheckedSteps).filter(Boolean).length;
    if (newCompletedCount === totalSteps && onComplete) {
      Modal.confirm({
        title: '¡Checklist Completado!',
        content: '¿Deseas marcar esta orden de trabajo como completada?',
        onOk: () => onComplete(newCheckedSteps, stepNotes),
        okText: 'Sí, completar',
        cancelText: 'No, continuar'
      });
    }
  };

  const startStep = (stepId) => {
    if (readOnly) return;
    
    setCurrentStep(stepId);
    setStartTime(new Date());
    setIsWorkInProgress(true);
    message.info('Paso iniciado - cronómetro en marcha');
  };

  const completeCurrentStep = () => {
    if (!currentStep || !startTime) return;

    const endTime = new Date();
    const elapsed = (endTime - startTime) / 1000 / 60; // minutos

    setStepTimes(prev => ({
      ...prev,
      [currentStep]: elapsed
    }));

    setTotalElapsedTime(prev => prev + elapsed);
    setCurrentStep(null);
    setStartTime(null);
    setIsWorkInProgress(false);
    setHasUnsavedChanges(true);
  };

  const addStepNote = (stepId, note) => {
    if (readOnly) return;
    
    setStepNotes(prev => ({
      ...prev,
      [stepId]: note
    }));
    setHasUnsavedChanges(true);
  };

  const exportChecklist = () => {
    const checklistData = {
      workOrder: {
        id: workOrder?.id,
        title: workOrder?.title,
        orderNumber: workOrder?.order_number
      },
      taskList: {
        name: taskList?.name,
        description: taskList?.description
      },
      progress: {
        completedSteps,
        totalSteps,
        progressPercent: Math.round(progressPercent),
        totalElapsedTime: Math.round(totalElapsedTime)
      },
      steps: taskList?.steps?.map(step => ({
        order: step.step_order,
        description: step.description,
        estimatedTime: step.estimated_time_minutes,
        actualTime: stepTimes[step.id] ? Math.round(stepTimes[step.id]) : null,
        completed: checkedSteps[step.id] || false,
        notes: stepNotes[step.id] || ''
      })) || [],
      exportedAt: new Date().toISOString()
    };

    const dataStr = JSON.stringify(checklistData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `checklist_${workOrder?.order_number || workOrder?.id}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (!taskList || !taskList.steps) {
    return (
      <Alert
        message="Sin Lista de Tareas"
        description="Esta orden no tiene una lista de tareas asociada."
        type="info"
        showIcon
      />
    );
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      {/* Header con información general */}
      <Card style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '16px' }}>
          <div>
            <Title level={3} style={{ margin: 0 }}>
              <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
              {taskList.name}
            </Title>
            <Text type="secondary">Orden: {workOrder?.order_number}</Text>
          </div>
          <Space>
            <Button 
              icon={<SaveOutlined />} 
              onClick={saveProgress}
              disabled={!hasUnsavedChanges}
              type={hasUnsavedChanges ? 'primary' : 'default'}
            >
              Guardar
            </Button>
            <Button 
              icon={<PrinterOutlined />} 
              onClick={exportChecklist}
            >
              Exportar
            </Button>
          </Space>
        </div>

        {taskList.description && (
          <Paragraph>{taskList.description}</Paragraph>
        )}

        {/* Barra de progreso */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <Text strong>Progreso: {completedSteps} de {totalSteps} pasos</Text>
            <Text type="secondary">
              {Math.round(progressPercent)}% completado
            </Text>
          </div>
          <Progress 
            percent={progressPercent} 
            status={progressPercent === 100 ? 'success' : 'active'}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
        </div>

        {/* Información de tiempo */}
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          <Tag icon={<ClockCircleOutlined />} color="blue">
            Tiempo estimado: {taskList.steps.reduce((sum, step) => sum + (step.estimated_time_minutes || 0), 0)} min
          </Tag>
          <Tag icon={<ClockCircleOutlined />} color="green">
            Tiempo real: {Math.round(totalElapsedTime)} min
          </Tag>
          {isWorkInProgress && (
            <Tag icon={<PlayCircleOutlined />} color="orange">
              En progreso: {currentTimer} min
            </Tag>
          )}
        </div>

        {lastSaved && (
          <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginTop: '8px' }}>
            Último guardado: {lastSaved.toLocaleString()}
          </Text>
        )}
      </Card>

      {/* Lista de pasos */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {taskList.steps
          .sort((a, b) => a.step_order - b.step_order)
          .map((step, index) => {
            const isCompleted = checkedSteps[step.id] || false;
            const isCurrent = currentStep === step.id;
            const hasNotes = stepNotes[step.id];
            const actualTime = stepTimes[step.id];

            return (
              <Card 
                key={step.id}
                size="small"
                style={{
                  border: isCurrent ? '2px solid #1890ff' : undefined,
                  backgroundColor: isCompleted ? '#f6ffed' : undefined,
                  opacity: readOnly && !isCompleted ? 0.7 : 1
                }}
              >
                <div style={{ display: 'flex', alignItems: 'start', gap: '12px' }}>
                  {/* Checkbox y número de paso */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: '80px' }}>
                    <Badge count={step.step_order} size="small" color="blue" />
                    <Checkbox
                      checked={isCompleted}
                      onChange={(e) => handleStepCheck(step.id, e.target.checked)}
                      disabled={readOnly}
                      style={{ transform: 'scale(1.2)' }}
                    />
                  </div>

                  {/* Contenido del paso */}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' }}>
                      <Text 
                        strong
                        style={{ 
                          textDecoration: isCompleted ? 'line-through' : 'none',
                          color: isCompleted ? '#52c41a' : 'inherit'
                        }}
                      >
                        {step.description}
                      </Text>
                      
                      {!readOnly && !isCompleted && (
                        <Button
                          size="small"
                          type={isCurrent ? "primary" : "default"}
                          icon={isCurrent ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                          onClick={() => isCurrent ? completeCurrentStep() : startStep(step.id)}
                        >
                          {isCurrent ? 'Completar' : 'Iniciar'}
                        </Button>
                      )}
                    </div>

                    {/* Información de tiempo */}
                    <div style={{ display: 'flex', gap: '12px', marginBottom: '8px', flexWrap: 'wrap' }}>
                      {step.estimated_time_minutes && (
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          <ClockCircleOutlined /> Estimado: {step.estimated_time_minutes} min
                        </Text>
                      )}
                      {actualTime && (
                        <Text style={{ fontSize: '12px', color: '#52c41a' }}>
                          <CheckCircleOutlined /> Real: {Math.round(actualTime)} min
                        </Text>
                      )}
                      {isCurrent && startTime && (
                        <Text style={{ fontSize: '12px', color: '#1890ff' }}>
                          <PlayCircleOutlined /> En progreso: {currentTimer} min
                        </Text>
                      )}
                    </div>

                    {/* Campo de notas */}
                    <div style={{ marginTop: '12px' }}>
                      <TextArea
                        placeholder="Añadir observaciones sobre este paso..."
                        value={stepNotes[step.id] || ''}
                        onChange={(e) => addStepNote(step.id, e.target.value)}
                        disabled={readOnly}
                        autoSize={{ minRows: 1, maxRows: 3 }}
                        style={{ fontSize: '12px' }}
                      />
                      {hasNotes && (
                        <Tag 
                          icon={<FileTextOutlined />} 
                          color="orange" 
                          size="small"
                          style={{ marginTop: '4px' }}
                        >
                          Con observaciones
                        </Tag>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
      </div>

      {/* Resumen final */}
      {progressPercent === 100 && (
        <Card style={{ marginTop: '20px', backgroundColor: '#f6ffed', border: '1px solid #b7eb8f' }}>
          <div style={{ textAlign: 'center' }}>
            <CheckCircleOutlined style={{ fontSize: '24px', color: '#52c41a', marginBottom: '8px' }} />
            <Title level={4} style={{ color: '#52c41a', margin: 0 }}>
              ¡Checklist Completado!
            </Title>
            <Text type="secondary">
              Todos los pasos han sido completados. Tiempo total: {Math.round(totalElapsedTime)} minutos.
            </Text>
          </div>
        </Card>
      )}
    </div>
  );
};

export default InteractiveTaskListChecklist;