import React, { useState, useEffect } from 'react';

const FormatOrderUpdateModal = ({ 
  visible, 
  onCancel, 
  onSubmit, 
  order,
  loading = false 
}) => {
  const [formData, setFormData] = useState({
    status: '',
    setup_duration: '',
    production_loss_hours: '',
    actual_start_time: '',
    actual_end_time: '',
    completion_notes: '',
    setup_notes: ''
  });
  const [calculatedEfficiency, setCalculatedEfficiency] = useState(null);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (visible && order) {
      setFormData({
        status: order.status || 'Pendiente',
        setup_duration: order.setup_duration || '',
        production_loss_hours: order.production_loss_hours || '',
        actual_start_time: order.actual_start_time || '',
        actual_end_time: order.actual_end_time || '',
        completion_notes: order.completion_notes || '',
        setup_notes: order.setup_notes || ''
      });
      
      if (order.setup_duration && order.estimated_setup_duration) {
        const efficiency = (order.estimated_setup_duration / order.setup_duration) * 100;
        setCalculatedEfficiency(efficiency);
      }
    }
  }, [visible, order]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    if (field === 'setup_duration' && value && order?.estimated_setup_duration) {
      const efficiency = (order.estimated_setup_duration / parseFloat(value)) * 100;
      setCalculatedEfficiency(efficiency);
    }
    
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.status) {
      newErrors.status = 'El estado es requerido';
    }
    
    if (!formData.setup_duration) {
      newErrors.setup_duration = 'El tiempo real es obligatorio';
    } else if (isNaN(formData.setup_duration) || parseFloat(formData.setup_duration) <= 0) {
      newErrors.setup_duration = 'Debe ser un número mayor a 0';
    }
    
    if (formData.production_loss_hours && (isNaN(formData.production_loss_hours) || parseFloat(formData.production_loss_hours) < 0)) {
      newErrors.production_loss_hours = 'Debe ser un número mayor o igual a 0';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;
    
    try {
      const submitData = {
        ...formData,
        setup_duration: parseFloat(formData.setup_duration),
        production_loss_hours: formData.production_loss_hours ? parseFloat(formData.production_loss_hours) : null,
      };
      
      await onSubmit(order.id, submitData);
    } catch (error) {
      console.error('Error al actualizar orden:', error);
    }
  };

  const getEfficiencyColor = (efficiency) => {
    if (efficiency >= 100) return '#52c41a';
    if (efficiency >= 80) return '#faad14';
    return '#ff4d4f';
  };

  const getEfficiencyStatus = (efficiency) => {
    if (efficiency >= 120) return 'Excelente';
    if (efficiency >= 100) return 'Eficiente';
    if (efficiency >= 80) return 'Aceptable';
    return 'Necesita Mejora';
  };

  if (!visible) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '24px',
        width: '900px',
        maxWidth: '90vw',
        maxHeight: '90vh',
        overflow: 'auto',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
      }}>
        <div style={{ marginBottom: '24px', borderBottom: '1px solid #f0f0f0', paddingBottom: '16px' }}>
          <h2 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>
            Actualizar Orden {order?.order_number || order?.id}
          </h2>
        </div>

        <div style={{
          backgroundColor: '#fafafa',
          padding: '16px',
          borderRadius: '6px',
          marginBottom: '24px',
          border: '1px solid #d9d9d9'
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div><strong>Título:</strong> {order?.title}</div>
            <div>
              <strong>Tipo:</strong> 
              <span style={{
                marginLeft: '8px',
                padding: '2px 8px',
                backgroundColor: '#1890ff',
                color: 'white',
                borderRadius: '4px',
                fontSize: '12px'
              }}>
                {order?.format_change_type}
              </span>
            </div>
            <div><strong>Tiempo Estimado:</strong> {order?.estimated_setup_duration || 'N/A'} horas</div>
            <div>
              <strong>Estado Actual:</strong> 
              <span style={{
                marginLeft: '8px',
                padding: '2px 8px',
                backgroundColor: order?.status === 'Cerrada' ? '#52c41a' : 
                                 order?.status === 'En curso' ? '#faad14' : '#1890ff',
                color: 'white',
                borderRadius: '4px',
                fontSize: '12px'
              }}>
                {order?.status}
              </span>
            </div>
          </div>
        </div>

        <div>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>
              Estado de la Orden *
            </label>
            <select
              value={formData.status}
              onChange={(e) => handleInputChange('status', e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: errors.status ? '1px solid #ff4d4f' : '1px solid #d9d9d9',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            >
              <option value="Pendiente">🔵 Pendiente</option>
              <option value="En curso">🟡 En Curso</option>
              <option value="En revisión">🟠 En Revisión</option>
              <option value="Cerrada">🟢 Cerrada</option>
            </select>
            {errors.status && <div style={{ color: '#ff4d4f', fontSize: '12px', marginTop: '4px' }}>{errors.status}</div>}
          </div>

          <div style={{ 
            margin: '24px 0', 
            borderTop: '1px solid #f0f0f0', 
            paddingTop: '16px',
            fontWeight: '500',
            color: '#1890ff'
          }}>
            ⏱️ Tiempos de Ejecución
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>
                ⭐ Tiempo Real de Setup (horas) *
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={formData.setup_duration}
                onChange={(e) => handleInputChange('setup_duration', e.target.value)}
                placeholder="Tiempo real empleado"
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: errors.setup_duration ? '1px solid #ff4d4f' : '1px solid #d9d9d9',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
              {errors.setup_duration && <div style={{ color: '#ff4d4f', fontSize: '12px', marginTop: '4px' }}>{errors.setup_duration}</div>}
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>
                Pérdida de Producción (horas)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={formData.production_loss_hours}
                onChange={(e) => handleInputChange('production_loss_hours', e.target.value)}
                placeholder="Horas de producción perdidas"
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: errors.production_loss_hours ? '1px solid #ff4d4f' : '1px solid #d9d9d9',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
              {errors.production_loss_hours && <div style={{ color: '#ff4d4f', fontSize: '12px', marginTop: '4px' }}>{errors.production_loss_hours}</div>}
            </div>
          </div>

          {calculatedEfficiency && (
            <div style={{
              backgroundColor: calculatedEfficiency >= 100 ? '#f6ffed' : '#fff7e6',
              border: `1px solid ${calculatedEfficiency >= 100 ? '#b7eb8f' : '#ffd591'}`,
              borderRadius: '6px',
              padding: '16px',
              marginBottom: '24px'
            }}>
              <div style={{ fontWeight: '500', marginBottom: '8px' }}>
                Eficiencia Calculada: {calculatedEfficiency.toFixed(1)}%
              </div>
              <div style={{
                width: '100%',
                height: '8px',
                backgroundColor: '#f0f0f0',
                borderRadius: '4px',
                overflow: 'hidden',
                marginBottom: '8px'
              }}>
                <div style={{
                  width: `${Math.min(calculatedEfficiency, 150)}%`,
                  height: '100%',
                  backgroundColor: getEfficiencyColor(calculatedEfficiency),
                  transition: 'width 0.3s ease'
                }} />
              </div>
              <div>
                <strong>Evaluación:</strong> {getEfficiencyStatus(calculatedEfficiency)}
                {calculatedEfficiency > 100 && (
                  <span style={{ color: '#52c41a', marginLeft: '8px' }}>
                    ⚡ Ahorro de {((order?.estimated_setup_duration || 0) - parseFloat(formData.setup_duration || 0)).toFixed(1)} horas
                  </span>
                )}
                {calculatedEfficiency < 100 && (
                  <span style={{ color: '#ff4d4f', marginLeft: '8px' }}>
                    ⚠️ Exceso de {(parseFloat(formData.setup_duration || 0) - (order?.estimated_setup_duration || 0)).toFixed(1)} horas
                  </span>
                )}
              </div>
            </div>
          )}

          <div style={{ 
            margin: '24px 0', 
            borderTop: '1px solid #f0f0f0', 
            paddingTop: '16px',
            fontWeight: '500',
            color: '#1890ff'
          }}>
            📅 Fechas de Ejecución
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>
                Hora de Inicio Real
              </label>
              <input
                type="datetime-local"
                value={formData.actual_start_time}
                onChange={(e) => handleInputChange('actual_start_time', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>
                Hora de Finalización Real
              </label>
              <input
                type="datetime-local"
                value={formData.actual_end_time}
                onChange={(e) => handleInputChange('actual_end_time', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
            </div>
          </div>

          <div style={{ 
            margin: '24px 0', 
            borderTop: '1px solid #f0f0f0', 
            paddingTop: '16px',
            fontWeight: '500',
            color: '#1890ff'
          }}>
            📝 Observaciones
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>
              Notas del Setup
            </label>
            <textarea
              value={formData.setup_notes}
              onChange={(e) => handleInputChange('setup_notes', e.target.value)}
              placeholder="Detalles técnicos, problemas encontrados, mejoras aplicadas..."
              rows={3}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d9d9d9',
                borderRadius: '6px',
                fontSize: '14px',
                resize: 'vertical'
              }}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>
              Notas de Finalización
            </label>
            <textarea
              value={formData.completion_notes}
              onChange={(e) => handleInputChange('completion_notes', e.target.value)}
              placeholder="Observaciones finales, resultados obtenidos..."
              rows={2}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d9d9d9',
                borderRadius: '6px',
                fontSize: '14px',
                resize: 'vertical'
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <button
              type="button"
              onClick={onCancel}
              style={{
                padding: '8px 16px',
                border: '1px solid #d9d9d9',
                borderRadius: '6px',
                backgroundColor: 'white',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={loading}
              style={{
                padding: '8px 16px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: loading ? '#ccc' : '#1890ff',
                color: 'white',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              {loading ? 'Actualizando...' : '✅ Actualizar Orden'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FormatOrderUpdateModal;