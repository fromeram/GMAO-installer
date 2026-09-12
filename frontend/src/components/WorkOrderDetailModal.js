// WorkOrderDetailModal.js - CON DOCUMENTACIÓN PARA AUDITORÍA

import React from 'react';
import { Modal, Button, Alert, Tag, Divider, Spin } from 'antd';
import { EditOutlined, FileTextOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import TechnicianManager from './TechnicianManager';
import DocumentAttachmentManager from './DocumentAttachmentManager'; // ⭐ AÑADIR DOCUMENTACIÓN

const WorkOrderDetailModal = ({ 
  visible, 
  onCancel, 
  orderDetail, 
  onEdit = null,
  showEditButton = true,
  title = "Detalle del Parte de Trabajo",
  onTechnicianUpdate,
  loading = false
}) => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  // Resto de funciones existentes (canEditOrder, formatDate, etc.)
  const canEditOrder = (order) => {
    if (!currentUser || !order) return false;
    
    const userRole = currentUser.role;
    const isAdminOrMaintenance = ["Administrador", "Jefe de Mantenimiento"].includes(userRole);
    const isJefeSeccion = userRole === "Jefe de Sección";
    const isMecanico = userRole === "Mecánico";
    
    if (isAdminOrMaintenance) return true;
    
    if (isJefeSeccion && order.section_id === currentUser.section_id && order.status !== 'Cerrada') {
      return true;
    }
    
    if (isMecanico && order.assigned_to_id === currentUser.id && order.status !== 'Cerrada') {
      return true;
    }
    
    return false;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      return new Date(dateString).toLocaleString('es-ES', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit'
      });
    } catch (e) {
      return dateString;
    }
  };

  const getStatusColor = (status) => {
    const colors = { 
      'Pendiente': 'gold', 
      'En curso': 'blue', 
      'En revisión': 'purple', 
      'Cerrada': 'green' 
    };
    return colors[status] || 'default';
  };

  const getTypeColor = (type) => {
    const typeColors = { 
      'Preventivo': 'green', 
      'Correctivo': 'red', 
      'Inspección': 'blue', 
      'Mejora': 'cyan', 
      'Modificación': 'purple', 
      'Seguridad': 'orange' 
    };
    return typeColors[type] || 'default';
  };

  if (!orderDetail) return null;

  const canEdit = canEditOrder(orderDetail);

  return (
    <Modal
      title={`${title} - ID #${orderDetail?.id || 'N/A'}`}
      open={visible}
      onCancel={onCancel}
      width={1400} // ⭐ ANCHO AUMENTADO PARA DOCUMENTACIÓN
      footer={[
        <Button key="close" onClick={onCancel}>
          Cerrar
        </Button>,
        <Button 
          key="view-orders" 
          onClick={() => {
            onCancel();
            navigate('/ordenes');
          }}
        >
          Ver Todas las Órdenes
        </Button>,
        ...(canEdit && showEditButton && onEdit ? [
          <Button 
            key="edit" 
            type="primary" 
            icon={<EditOutlined />}
            onClick={() => onEdit(orderDetail)}
          >
            Editar Orden
          </Button>
        ] : [])
      ]}
    >
      <div style={{ maxHeight: '75vh', overflowY: 'auto' }}>
        {loading && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin size="large" />
            <p>Cargando detalles...</p>
          </div>
        )}

        {!loading && (
          <>
            {/* Alertas existentes */}
            {orderDetail.status === 'Cerrada' && (
              <Alert
                message="Orden Cerrada"
                description="Esta orden de trabajo ya está cerrada y no puede ser modificada."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}
            
            {!canEdit && orderDetail.status !== 'Cerrada' && (
              <Alert
                message="Sin Permisos de Edición"
                description="No tienes permisos para editar esta orden de trabajo."
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            {/* Gestión de Técnicos */}
            <TechnicianManager 
              workOrderId={orderDetail.id}
              onUpdate={onTechnicianUpdate}
            />
            
            <Divider />

            {/* Información básica existente */}
            <div style={{ marginBottom: 20 }}>
              <h3>Información Básica del Trabajo</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div><strong>ID del Trabajo:</strong> #{orderDetail.id}</div>
                <div><strong>Estado:</strong> <Tag color={getStatusColor(orderDetail.status)}>{orderDetail.status}</Tag></div>
                <div><strong>Tipo de Trabajo:</strong> <Tag color={getTypeColor(orderDetail.work_type)}>{orderDetail.work_type}</Tag></div>
                <div><strong>Fecha de Creación:</strong> {formatDate(orderDetail.created_at)}</div>
                <div><strong>Operario Reportante:</strong> {orderDetail.operator}</div>
                <div><strong>Número de Orden:</strong> {orderDetail.order_number || `OT-${orderDetail.id}`}</div>
              </div>
            </div>

            {/* Ubicación */}
            <div style={{ marginBottom: 20 }}>
              <h3>Ubicación del Trabajo</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
                <div><strong>Sección:</strong> {typeof orderDetail.section === 'object' ? orderDetail.section?.nombre : orderDetail.section}</div>
                <div><strong>Línea de Producción:</strong> {typeof orderDetail.line === 'object' ? orderDetail.line?.nombre : orderDetail.line}</div>
                <div><strong>Máquina/Equipo:</strong> {orderDetail.machine?.nombre || orderDetail.machine_name || orderDetail.machine || 'No especificado'}</div>
              </div>
            </div>

            {/* Descripción del Trabajo */}
            <div style={{ marginBottom: 20 }}>
              <h3>Descripción del Trabajo</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 8 }}>
                <div><strong>Título:</strong> {orderDetail.title}</div>
                <div><strong>Detalles:</strong> {orderDetail.details || 'Sin detalles especificados'}</div>
              </div>
            </div>

            {/* ⭐ NUEVA SECCIÓN: DOCUMENTACIÓN PARA AUDITORÍA */}
            <Divider />
            <div style={{ 
              marginBottom: 20,
              padding: '16px',
              backgroundColor: '#f6ffed',
              border: '1px solid #b7eb8f',
              borderRadius: '6px'
            }}>
              <h3 style={{ 
                color: '#52c41a', 
                marginTop: 0,
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <FileTextOutlined />
                📋 Documentación de la Orden
                <span style={{ 
                  fontSize: '12px', 
                  color: '#666',
                  fontWeight: 'normal',
                  marginLeft: '8px'
                }}>
                  (Trazabilidad ISO 9001)
                </span>
              </h3>
              
              <Alert
                message="Documentación para Auditorías"
                description="Todos los documentos adjuntos aquí están vinculados específicamente a esta orden de trabajo para garantizar la trazabilidad completa."
                type="success"
                showIcon
                style={{ marginBottom: 16 }}
              />
              
              <DocumentAttachmentManager
                entityType="work_order"
                entityId={orderDetail.id}
                title="Documentos de la Orden"
                readOnly={false} // Permitir subir/eliminar documentos
              />
            </div>

            {/* Resto de secciones existentes (Repuestos, Tiempos, etc.) */}
            {orderDetail.repuesto && (
              <div style={{ marginBottom: 20 }}>
                <h3>Repuestos Utilizados</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <div><strong>Repuesto:</strong> {orderDetail.repuesto.product_name}</div>
                  <div><strong>Cantidad Utilizada:</strong> {orderDetail.quantity_used || 0} unidades</div>
                </div>
              </div>
            )}

            {/* Tiempos y Duración */}
            {(orderDetail.actual_start_time || orderDetail.actual_end_time || orderDetail.downtime_hours) && (
              <div style={{ marginBottom: 20 }}>
                <h3>Tiempos y Duración</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
                  <div><strong>Inicio Real:</strong> {formatDate(orderDetail.actual_start_time) || 'No registrado'}</div>
                  <div><strong>Fin Real:</strong> {formatDate(orderDetail.actual_end_time) || 'No registrado'}</div>
                  <div><strong>Horas de Parada:</strong> {orderDetail.downtime_hours || 0} horas</div>
                </div>
              </div>
            )}

            {/* Notas Adicionales */}
            {orderDetail.completion_notes && (
              <div style={{ marginBottom: 20 }}>
                <h3>Notas de Finalización</h3>
                <div style={{ 
                  padding: 12, 
                  backgroundColor: '#fafafa', 
                  border: '1px solid #d9d9d9', 
                  borderRadius: 6,
                  fontStyle: 'italic'
                }}>
                  {orderDetail.completion_notes}
                </div>
              </div>
            )}

            {/* Resumen del Certificado de Trabajo */}
            <div style={{ 
              marginTop: 30, 
              padding: 16, 
              backgroundColor: '#f6ffed', 
              border: '1px solid #b7eb8f', 
              borderRadius: 6 
            }}>
              <h3 style={{ color: '#52c41a', marginTop: 0 }}>📋 Certificado de Trabajo Realizado</h3>
              <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                <div><strong>Estado del Trabajo:</strong> {orderDetail.status === 'Cerrada' ? '✅ Trabajo completado' : '⏳ En seguimiento'}</div>
                <div><strong>Área de Responsabilidad:</strong> {typeof orderDetail.section === 'object' ? orderDetail.section?.nombre : orderDetail.section} - {typeof orderDetail.line === 'object' ? orderDetail.line?.nombre : orderDetail.line}</div>
                <div><strong>Equipo Involucrado:</strong> {orderDetail.machine?.nombre || orderDetail.machine_name || orderDetail.machine || 'No especificado'}</div>
                <div><strong>Tipo de Intervención:</strong> {orderDetail.work_type}</div>
                <div><strong>Evidencia Documental:</strong> Registro digital completo disponible</div>
                {orderDetail.failure_code && (
                  <div><strong>Código de Falla Registrado:</strong> {orderDetail.failure_code.code} - {orderDetail.failure_code.description}</div>
                )}
                {orderDetail.repuesto && (
                  <div><strong>Repuesto Utilizado:</strong> {orderDetail.repuesto.product_name} (Cantidad: {orderDetail.quantity_used || 0})</div>
                )}
                {orderDetail.downtime_hours && (
                  <div><strong>Tiempo de Inactividad Registrado:</strong> {orderDetail.downtime_hours} horas</div>
                )}
                {orderDetail.technicians && orderDetail.technicians.length > 0 && (
                  <div><strong>Técnicos Asignados:</strong> {orderDetail.technicians.map(t => `${t.username} (${t.role})`).join(', ')}</div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};

export default WorkOrderDetailModal;