// src/pages/CalendarioTurnos.js (Versión corregida)
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
    Calendar, Select, Typography, Spin, Alert, message, Col, Row, Card, Tag, Button, Space,
    Modal, Form, Input, DatePicker, Popconfirm, Tooltip
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SwapOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import locale from 'antd/es/date-picker/locale/es_ES';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import '../styles/CommonPage.css';

// --- Configuración Dayjs ---
dayjs.locale('es');
dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.tz.setDefault("Europe/Madrid"); // O tu zona horaria local

// --- Constantes y Helpers ---
const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

// Definir colores de eventos
const eventColors = { 
    'M': 'geekblue', 
    'T': 'green', 
    'N': 'purple', 
    'P': 'cyan', 
    'L': 'default', 
    'V': 'gold', 
    'B': 'red', 
    'A': 'orange', 
    'F': 'magenta', 
    '?': 'error', 
    'override': 'warning', 
    'absence': 'volcano', 
    'shift': 'processing', 
    'error': 'error', 
    'no_assignment': 'default' 
};

const calendarCustomStyles = `
  /* Aumentar tamaño de celdas del calendario */
  .ant-picker-calendar-full .ant-picker-calendar-date {
    height: auto !important;
    min-height: 120px !important; /* Ajusta este valor para cambiar la altura */
    padding: 4px 8px !important; /* Ajustar el padding interno */
  }

  /* Aumentar ancho de las celdas - afecta a toda la tabla */
  .ant-picker-calendar-full .ant-picker-panel {
    width: 100% !important;
  }

  /* Asegurar que los días de la semana tienen suficiente espacio */
  .ant-picker-calendar-full .ant-picker-panel .ant-picker-calendar-date-content {
    height: auto !important;
    overflow-y: auto !important;
    max-height: calc(100% - 20px) !important; /* Ajustar según necesidad */
  }

  /* Mejorar la visualización de cada celda de día */
  .ant-picker-calendar-full .ant-picker-cell-in-view {
    min-width: 100px !important; /* Ancho mínimo para cada celda */
  }

  /* Permitir scroll vertical dentro de cada celda si hay muchos eventos */
  .ant-picker-calendar-full .ant-picker-calendar-date-content {
    overflow-y: auto;
  }

  /* Estilos para la vista de mes completo */
  .ant-picker-calendar-full .ant-picker-cell {
    padding: 1px !important;
  }
`;


const absenceTypeNames = { 'V': 'Vacaciones', 'B': 'Baja Médica', 'A': 'As.Propios', 'F': 'Festivo' };
const shiftCodeNames = { 'M': 'Mañana', 'T': 'Tarde', 'N': 'Noche' };

const getEventTag = (eventData) => {
    if (!eventData) return <Tag color="default">-</Tag>;
    let color = 'default'; 
    let text = '?'; 
    let typeName = ''; 
    let notes = '';
    
    if (eventData.type === 'shift') { 
        color = eventColors[eventData.code] || eventColors.shift; 
        text = eventData.code || '?'; 
        typeName = `Turno: ${text} (${eventData.pattern_name || '?'})`;
    }
    else if (eventData.type === 'absence') { 
        color = eventColors[eventData.absence_type] || eventColors.absence; 
        text = eventData.absence_type || '?'; 
        typeName = absenceTypeNames[text] || 'Ausencia'; 
        notes = eventData.notes || ''; 
    }
    else if (eventData.type === 'override') { 
        color = eventColors.override; 
        text = eventData.code || '?'; 
        const shiftName = shiftCodeNames[text] || text; 
        typeName = `Cobertura: ${shiftName}`; 
        notes = eventData.notes || ''; 
    }
    else if (eventData.type === 'error') { 
        color = eventColors.error; 
        text = '?'; 
        typeName = "Error"; 
    }
    else if (eventData.type === 'no_assignment') { 
        color = eventColors.no_assignment; 
        text = '-'; 
        typeName = "Sin Asignación"; 
    }
    
    const title = `${typeName}${notes ? ` | Notas: ${notes}` : ''}`;
    const style = eventData.type === 'override' ? { borderStyle: 'dashed' } : {};
    
    return (
        <Tooltip title={title} placement="topLeft">
            <Tag color={color} style={{ marginRight: 3, ...style }}>{text}</Tag>
        </Tooltip>
    );
};

const MANAGER_ROLES = ["Administrador", "Jefe Mantenimiento", "Jefe Sección"];

// --- Componente Principal ---
const CalendarioTurnos = () => {
    // --- Estados ---
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [calendarData, setCalendarData] = useState({});
    const [selectedDate, setSelectedDate] = useState(dayjs.tz());
    const { currentUser } = useAuth();
    const [isAbsenceModalVisible, setIsAbsenceModalVisible] = useState(false);
    const [absenceModalMode, setAbsenceModalMode] = useState('add');
    const [editingAbsenceData, setEditingAbsenceData] = useState(null);
    const [absenceForm] = Form.useForm();
    const [isSubmittingAbsence, setIsSubmittingAbsence] = useState(false);
    const [isOverrideModalVisible, setIsOverrideModalVisible] = useState(false);
    const [overrideForm] = Form.useForm();
    const [isSubmittingOverride, setIsSubmittingOverride] = useState(false);
    const [usersForSelect, setUsersForSelect] = useState([]);
    const [loadingUsers, setLoadingUsers] = useState(false);

    // Permiso Memoizado
    const hasManagementPermission = useMemo(() => {
        return currentUser?.role && MANAGER_ROLES.includes(currentUser.role);
    }, [currentUser]);

    // --- Funciones de Carga de Datos ---
    const fetchCalendarData = useCallback(async (year, month) => {
        setLoading(true); // Asegura poner loading al inicio
        setError(null);
        console.log(`Workspaceing calendar data for ${year}-${month}`); // Log útil
        try {
            const url = `/calendar-data?year=${year}&month=${month}`; // Sin /api/
            const data = await fetchWithAuth(url);
            // Validación robusta de la respuesta
            if (typeof data !== 'object' || data === null) {
                console.error("Invalid data structure received:", data);
                throw new Error("Respuesta inválida del servidor al cargar calendario.");
            }
            setCalendarData(data || {});
            console.log(`Calendar data received successfully.`);
        } catch (err) {
            console.error("Error fetching calendar data:", err);
            const errorMsg = `Error al cargar datos del calendario: ${err.message || 'Desconocido'}`;
            setError(errorMsg);
            // message.error(errorMsg); // Evitar doble mensaje si ya hay Alert
            setCalendarData({}); // Limpiar datos en caso de error
        } finally {
            setLoading(false); // <<<--- ASEGURAR QUE SE LLAMA SIEMPRE
        }
    }, []); // No depende de estado externo que cambie frecuentemente

    const fetchUsersForSelect = useCallback(async () => {
        // Evitar llamadas concurrentes o innecesarias
        if (usersForSelect.length > 0 || loadingUsers) return;
        setLoadingUsers(true);
        console.log("Fetching users for select...");
        try {
            const usersData = await fetchWithAuth('/users'); // Sin /api/
            // Filtrar usuarios activos si es necesario, o dejar que el backend lo haga
            setUsersForSelect(usersData || []);
        } catch (err) {
            console.error("Error fetching users:", err);
            message.error(`Error cargando usuarios: ${err.message || '?'}`);
        } finally {
            setLoadingUsers(false);
        }
    }, [usersForSelect.length, loadingUsers]); // Dependencias correctas

    // Handlers para ausencias y overrides
    const handleEditAbsence = useCallback((absenceRecord) => {
        if (!hasManagementPermission) { 
            message.warning("Permiso denegado."); 
            return; 
        }
        setAbsenceModalMode('edit'); 
        setEditingAbsenceData(absenceRecord);
        absenceForm.resetFields();
        absenceForm.setFieldsValue({ 
            user_id: absenceRecord.user_id, 
            absence_type: absenceRecord.absence_type, 
            dateRange: [dayjs.tz(absenceRecord.start_date), dayjs.tz(absenceRecord.end_date)], 
            notes: absenceRecord.notes 
        });
        if(usersForSelect.length === 0) { 
            fetchUsersForSelect(); 
        }
        setIsAbsenceModalVisible(true);
    }, [hasManagementPermission, absenceForm, usersForSelect.length, fetchUsersForSelect]);

    const handleDeleteAbsence = useCallback(async (absenceId) => {
        if (!hasManagementPermission) { 
            message.error("Permiso denegado."); 
            return; 
        }
        if (absenceId === undefined || absenceId === null) { 
            message.error("Error interno: ID de ausencia inválido."); 
            return; 
        }
        try { 
            await fetchWithAuth(`/absences/${absenceId}`, { method: 'DELETE' }); 
            message.success('Ausencia eliminada.'); 
            fetchCalendarData(selectedDate.year(), selectedDate.month() + 1); 
        }
        catch (err) { 
            console.error("Error deleting absence:", err); 
            message.error(`Error al eliminar: ${err.message || '?'}`); 
        }
    }, [hasManagementPermission, selectedDate, fetchCalendarData]);

    const handleDeleteOverride = useCallback(async (overrideId) => {
        if (!hasManagementPermission) { 
            message.error("Permiso denegado."); 
            return; 
        }
        if (overrideId === undefined || overrideId === null) { 
            console.error("ID de override inválido"); 
            message.error("Error interno."); 
            return; 
        }
        try { 
            await fetchWithAuth(`/shift-overrides/${overrideId}`, { method: 'DELETE' }); 
            message.success('Cobertura/Cambio eliminado.'); 
            fetchCalendarData(selectedDate.year(), selectedDate.month() + 1); 
        }
        catch (err) { 
            console.error("Error deleting override:", err); 
            message.error(`Error al eliminar: ${err.message || '?'}`); 
        }
    }, [hasManagementPermission, selectedDate, fetchCalendarData]);

    // useEffect principal para cargar datos
    useEffect(() => {
        // Llama a fetchCalendarData cuando selectedDate cambia
        fetchCalendarData(selectedDate.year(), selectedDate.month() + 1);
        // Llama a fetchUsersForSelect solo si la lista está vacía
        if (usersForSelect.length === 0) {
            fetchUsersForSelect();
        }
        // No necesitamos cargar patrones de turno
    }, [selectedDate, fetchCalendarData, fetchUsersForSelect, usersForSelect.length]); // Dependencias correctas

    const getOptimalCellHeight = useCallback(() => {
        // Calcula la altura óptima basada en el número de usuarios activos
        const userCount = usersForSelect.length;
        // Cada usuario ocupa aproximadamente 20px (ajusta según necesites)
        const baseHeight = 60; // Altura base de la celda
        const heightPerUser = 20; // Altura aproximada por usuario
        
        return Math.max(120, baseHeight + (userCount * heightPerUser));
    }, [usersForSelect.length]);

    

    // --- Renderizado de Celdas del Calendario ---
    const dateCellRender = useCallback((value) => {
        const dateStr = value.format('YYYY-MM-DD');
        const dailyData = calendarData[dateStr];
        if (!dailyData || Object.keys(dailyData).length === 0) return null;
        const entries = Object.entries(dailyData).sort((a, b) => a[0].localeCompare(b[0]));
    
        return (
            <ul style={{ 
                margin: 0, 
                padding: 0, 
                listStyle: 'none', 
                lineHeight: '1.2',
                minHeight: '80px', // Añadir altura mínima para la lista
                maxHeight: '100%',
                overflowY: 'auto' // Permitir scroll si hay muchos usuarios
            }}>
                {entries.map(([username, eventData]) => {
                    const tag = getEventTag(eventData);
                    const isAbsence = eventData?.type === 'absence';
                    const isOverride = eventData?.type === 'override';

                    return (
                        <li 
                            key={`${username}-${eventData?.id || 'event'}`} 
                            style={{ 
                                whiteSpace: 'nowrap', 
                                overflow: 'hidden', 
                                textOverflow: 'ellipsis', 
                                fontSize: '11px', 
                                marginTop: '2px', 
                                display: 'flex', 
                                justifyContent: 'space-between', 
                                alignItems: 'center' 
                            }}
                        >
                            {/* Span principal - Ya no clickable para editar */}
                            <span style={{ 
                                flexGrow: 1, 
                                overflow: 'hidden', 
                                textOverflow: 'ellipsis' 
                            }}>
                                {tag} {username}
                            </span>
                            {/* Botones Ausencia */}
                            {isAbsence && hasManagementPermission && (
                                <Space size={2} style={{ marginLeft: '4px', flexShrink: 0 }}>
                                    <Tooltip title="Editar Ausencia">
                                        <Button 
                                            type="text" 
                                            size="small" 
                                            icon={<EditOutlined />} 
                                            onClick={(e) => { 
                                                e.stopPropagation();
                                                handleEditAbsence(eventData); 
                                            }} 
                                            style={{ 
                                                padding: '0 4px', 
                                                height: 'auto', 
                                                lineHeight: 'inherit', 
                                                border: 'none' 
                                            }} 
                                        />
                                    </Tooltip>
                                    <Tooltip title="Eliminar Ausencia">
                                        <Popconfirm 
                                            title="¿Eliminar ausencia?" 
                                            onConfirm={(e) => { 
                                                if (e) e.stopPropagation();
                                                handleDeleteAbsence(eventData.id); 
                                            }} 
                                            onCancel={(e) => {
                                                if (e) e.stopPropagation();
                                            }} 
                                            okText="Sí" 
                                            cancelText="No" 
                                            okButtonProps={{ danger: true }}
                                        >
                                            <Button 
                                                type="text" 
                                                danger 
                                                size="small" 
                                                icon={<DeleteOutlined />} 
                                                onClick={(e) => e.stopPropagation()}
                                                style={{ 
                                                    padding: '0 4px', 
                                                    height: 'auto', 
                                                    lineHeight: 'inherit', 
                                                    border: 'none' 
                                                }} 
                                            />
                                        </Popconfirm>
                                    </Tooltip>
                                </Space>
                            )}
                            {/* Botones Override */}
                            {isOverride && hasManagementPermission && (
                                <Space size={2} style={{ marginLeft: '4px', flexShrink: 0 }}>
                                    <Tooltip title="Eliminar Cobertura">
                                        <Popconfirm 
                                            title="¿Eliminar cobertura?" 
                                            onConfirm={(e) => { 
                                                if (e) e.stopPropagation();
                                                handleDeleteOverride(eventData.id); 
                                            }} 
                                            onCancel={(e) => {
                                                if (e) e.stopPropagation();
                                            }} 
                                            okText="Sí" 
                                            cancelText="No" 
                                            okButtonProps={{ danger: true }}
                                        >
                                            <Button 
                                                type="text" 
                                                danger 
                                                size="small" 
                                                icon={<DeleteOutlined />} 
                                                onClick={(e) => e.stopPropagation()}
                                                style={{ 
                                                    padding: '0 4px', 
                                                    height: 'auto', 
                                                    lineHeight: 'inherit', 
                                                    border: 'none' 
                                                }} 
                                            />
                                        </Popconfirm>
                                    </Tooltip>
                                </Space>
                            )}
                        </li>
                    );
                })}
            </ul>
        );
    }, [calendarData, hasManagementPermission, handleEditAbsence, handleDeleteAbsence, handleDeleteOverride]);

    // Cabecera del Calendario
    const headerRender = useCallback(({ value, onChange }) => {
        const current = value.clone();
        const year = current.year();
        const month = current.month();
        
        const monthOptions = [];
        for (let i = 0; i < 12; i++) {
            const monthName = current.month(i).format('MMMM');
            monthOptions.push(
                <Option key={i} value={i}>
                    {monthName.charAt(0).toUpperCase() + monthName.slice(1)}
                </Option>
            );
        }
        
        const yearOptions = [];
        for (let i = year - 5; i < year + 6; i += 1) {
            yearOptions.push(
                <Option key={i} value={i}>{i}</Option>
            );
        }
        
        return (
            <div style={{ padding: '8px 12px' }}>
                <Row justify="space-between" align="middle" gutter={8}>
                    <Col>
                        <Title level={4} style={{ margin: 0 }}>
                            {value.format('MMMM YYYY').charAt(0).toUpperCase() + value.format('MMMM YYYY').slice(1)}
                        </Title>
                    </Col>
                    <Col>
                        <Space>
                            <Select
                                size="small"
                                style={{ width: 80 }}
                                value={year}
                                onChange={(newYear) => {
                                    const now = current.year(newYear);
                                    onChange(now);
                                    setSelectedDate(now);
                                }}
                            >
                                {yearOptions}
                            </Select>
                            <Select
                                size="small"
                                style={{ width: 120 }}
                                value={month}
                                onChange={(newMonth) => {
                                    const now = current.month(newMonth);
                                    onChange(now);
                                    setSelectedDate(now);
                                }}
                            >
                                {monthOptions}
                            </Select>
                            <Button
                                size="small"
                                onClick={() => {
                                    const now = dayjs.tz();
                                    onChange(now);
                                    setSelectedDate(now);
                                }}
                            >
                                Hoy
                            </Button>
                        </Space>
                    </Col>
                </Row>
            </div>
        );
    }, []);

    // --- Handlers para Ausencias ---
    const handleDateSelect = useCallback((date, info) => {
        // Si no es un click en la fecha, no hacemos nada
        if (info.source !== 'date') {
            return;
        }
        
        // Verificar permisos
        if (!hasManagementPermission) { 
            message.warning("Permiso denegado."); 
            return; 
        }
        
        // Configurar y mostrar modal de ausencia
        setAbsenceModalMode('add'); 
        setEditingAbsenceData(null);
        absenceForm.resetFields(); 
        absenceForm.setFieldsValue({ dateRange: [date, date] });
        
        if(usersForSelect.length === 0) { 
            fetchUsersForSelect(); 
        }
        
        setIsAbsenceModalVisible(true);
    }, [hasManagementPermission, absenceForm, usersForSelect, fetchUsersForSelect]);

    const handleAbsenceModalSubmit = async () => {
        setIsSubmittingAbsence(true);
        try {
            const values = await absenceForm.validateFields();
            if (!values.dateRange || values.dateRange.length !== 2) throw new Error("Rango inválido.");
            const payload = { 
                user_id: values.user_id, 
                absence_type: values.absence_type, 
                start_date: values.dateRange[0].format('YYYY-MM-DD'), 
                end_date: values.dateRange[1].format('YYYY-MM-DD'), 
                notes: values.notes || null 
            };
            if (absenceModalMode === 'edit' && editingAbsenceData) {
                 await fetchWithAuth(`/absences/${editingAbsenceData.id}`, { 
                     method: 'PUT', 
                     headers: { 'Content-Type': 'application/json' }, 
                     body: JSON.stringify(payload) 
                 });
                 message.success('Ausencia actualizada.');
            } else {
                 await fetchWithAuth('/absences', { 
                     method: 'POST', 
                     headers: { 'Content-Type': 'application/json' }, 
                     body: JSON.stringify(payload) 
                 });
                 message.success('Ausencia registrada.');
            }
            setIsAbsenceModalVisible(false); 
            setEditingAbsenceData(null);
            fetchCalendarData(selectedDate.year(), selectedDate.month() + 1); // Recargar calendario
        } catch (errorInfo) { 
            console.error('Error guardando ausencia:', errorInfo); 
            if (errorInfo instanceof Error) { 
                message.error(`Error: ${errorInfo.message}`); 
            } else { 
                message.error('Revise campos.'); 
            } 
        }
        finally { 
            setIsSubmittingAbsence(false); 
        }
    };

    const handleAbsenceModalCancel = () => {
        setIsAbsenceModalVisible(false); 
        setEditingAbsenceData(null); 
        absenceForm.resetFields();
    };

    // --- Handlers para Overrides ---
    const handleOpenOverrideModal = () => {
        if (!hasManagementPermission) { 
            message.warning("Permiso denegado."); 
            return; 
        }
        overrideForm.resetFields(); 
        overrideForm.setFieldsValue({ date: selectedDate });
        if (usersForSelect.length === 0) { 
            fetchUsersForSelect(); 
        }
        setIsOverrideModalVisible(true);
    };
    
    const handleOverrideModalSubmit = async () => {
        setIsSubmittingOverride(true);
        try {
            const values = await overrideForm.validateFields(); // Valida y obtiene valores
            console.log("Valores del formulario de override:", values);
            
            // Asegurarse de que la fecha esté en el formato correcto
            if (!values.date || !values.date.isValid()) {
                throw new Error("Fecha inválida");
            }
            
            // Crear payload con formato explícito para la fecha
            const payload = {
                user_id: values.user_id,
                date: values.date.format('YYYY-MM-DD'),
                actual_shift_code: values.actual_shift_code,
                notes: values.notes || null
            };
            
            console.log("Enviando payload de override:", payload);
            
            // Usar try/catch específico para la llamada a la API
            try {
                const response = await fetchWithAuth('/shift-overrides', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                console.log("Respuesta del servidor para override:", response);
                
                // Si llegamos aquí, la operación tuvo éxito (ya sea creación o actualización)
                let successMessage = 'Cobertura/Cambio registrado correctamente.';
                
                message.success(successMessage);
                setIsOverrideModalVisible(false);
                
                // Recargar datos del calendario para mostrar los cambios
                fetchCalendarData(selectedDate.year(), selectedDate.month() + 1);
            } catch (apiError) {
                // Manejo mejorado de errores de API
                console.error("Error de API:", apiError);
                let errorMsg = "Error al registrar cobertura/cambio.";
                
                // Si tenemos un mensaje específico del servidor, úsalo
                if (apiError.message) {
                    errorMsg = apiError.message;
                } else if (apiError.response && apiError.response.detail) {
                    errorMsg = apiError.response.detail;
                }
                
                message.error(errorMsg);
            }
        } catch (validationError) {
            // Manejo de errores de validación del formulario
            console.error('Error de validación formulario:', validationError);
            
            if (validationError.errorFields && validationError.errorFields.length > 0) {
                const firstError = validationError.errorFields[0];
                message.error(`Error en campo ${firstError.name[0]}: ${firstError.errors[0]}`);
            } else if (validationError instanceof Error) {
                message.error(`Error: ${validationError.message}`);
            } else {
                message.error('Error en el formulario. Revise los campos.');
            }
        } finally {
            setIsSubmittingOverride(false);
        }
    };
    
    const handleOverrideModalCancel = () => {
        setIsOverrideModalVisible(false); 
        overrideForm.resetFields();
    };

    // Memoizar headerRender
    const memoizedHeaderRender = useMemo(() => headerRender, [headerRender]);

    // --- Renderizado del Componente ---
    return (
      <div className="page-container">
         <style>{calendarCustomStyles}</style>
         <Title level={2} className="page-title">Calendario de Turnos</Title>
         {error && <Alert message="Error al cargar datos" description={error} type="error" showIcon closable onClose={() => setError(null)} style={{ marginBottom: 16 }} />}
         {/* El Spin cubre toda la sección de Card + Calendar + Legend */}
         <Spin spinning={loading} tip="Cargando calendario...">
             <Card className="table-container" bordered={false}>
                 <Space style={{ marginBottom: 16 }}>
                     {hasManagementPermission && ( 
                         <Button 
                             icon={<PlusOutlined />} 
                             onClick={() => handleDateSelect(selectedDate, { source: 'date' })}
                         > 
                             Registrar Ausencia 
                         </Button> 
                     )}
                     {hasManagementPermission && ( 
                         <Button 
                             icon={<SwapOutlined />} 
                             onClick={handleOpenOverrideModal}
                         > 
                             Registrar Cobertura 
                         </Button> 
                     )}
                 </Space>
                 <Calendar
                     locale={locale}
                     dateCellRender={dateCellRender}
                     headerRender={memoizedHeaderRender}
                     onSelect={handleDateSelect} // Para añadir ausencia al clicar día
                     value={selectedDate}
                 />
             </Card>
             <Card size="small" title="Leyenda" style={{ marginTop: 16 }}>
                 <Space wrap>
                     {Object.entries(eventColors)
                         .filter(([key]) => ['M', 'T', 'N', 'P', 'L', 'V', 'B', 'A', 'F', '?', 'override'].includes(key))
                         .map(([code, color]) => {
                             const text = {
                                 'M': 'Mañana', 
                                 'T': 'Tarde', 
                                 'N': 'Noche', 
                                 'P': 'Partido', 
                                 'L': 'Libre', 
                                 'V': 'Vacaciones', 
                                 'B': 'Baja', 
                                 'A': 'As.Propios', 
                                 'F': 'Festivo', 
                                 '?': 'Error', 
                                 'override': 'Cobertura'
                             }[code] || 'Otro';
                             
                             return (
                                 <Tag color={color} key={code}>
                                     {code === 'override' ? <SwapOutlined /> : code}: {text}
                                 </Tag>
                             );
                         })
                     }
                 </Space>
             </Card>
         </Spin>

         {/* --- MODAL AUSENCIAS --- */}
         <Modal 
             title={absenceModalMode === 'edit' ? `Editar Ausencia ID: ${editingAbsenceData?.id || '?'}` : `Registrar Ausencia`} 
             open={isAbsenceModalVisible} 
             onOk={handleAbsenceModalSubmit} 
             onCancel={handleAbsenceModalCancel} 
             confirmLoading={isSubmittingAbsence} 
             destroyOnClose 
             okText={absenceModalMode === 'edit' ? "Actualizar" : "Guardar"} 
             cancelText="Cancelar" 
             width={600}
         >
             <Spin spinning={loadingUsers}>
                 <Form form={absenceForm} layout="vertical" name="absence_form">
                     <Form.Item name="user_id" label="Usuario" rules={[{ required: true }]}>
                         <Select 
                             showSearch 
                             placeholder="Usuario" 
                             optionFilterProp="children" 
                             filterOption={(input, option) => (option?.children ?? '').toLowerCase().includes(input.toLowerCase())} 
                             loading={loadingUsers} 
                             disabled={absenceModalMode === 'edit'}
                         >
                             {usersForSelect.map(user => (
                                 <Option key={user.id} value={user.id}>{user.username}</Option>
                             ))}
                             </Select>
                     </Form.Item>
                     <Form.Item name="absence_type" label="Tipo Ausencia" rules={[{ required: true }]}>
                         <Select placeholder="Tipo">
                             <Option value="V">V - Vacaciones</Option>
                             <Option value="B">B - Baja Médica</Option>
                             <Option value="A">A - Asuntos Propios</Option>
                             <Option value="F">F - Festivo</Option>
                         </Select>
                     </Form.Item>
                     <Form.Item name="dateRange" label="Fechas (Inicio - Fin)" rules={[{ required: true, message: 'Selecciona rango' }]}>
                         <DatePicker.RangePicker format="YYYY-MM-DD" style={{ width: '100%' }} locale={locale} />
                     </Form.Item>
                     <Form.Item name="notes" label="Notas (Opcional)">
                         <TextArea rows={2} />
                     </Form.Item>
                 </Form>
             </Spin>
         </Modal>

         {/* --- MODAL OVERRIDES --- */}
         <Modal 
             title="Registrar Cobertura / Cambio de Turno" 
             open={isOverrideModalVisible} 
             onOk={handleOverrideModalSubmit} 
             onCancel={handleOverrideModalCancel} 
             confirmLoading={isSubmittingOverride} 
             okText="Guardar Cambio" 
             cancelText="Cancelar" 
             width={600}
         >
             <Spin spinning={loadingUsers}>
                 <Form 
                     form={overrideForm} 
                     layout="vertical" 
                     name="override_form" 
                     onValuesChange={(changedValues, allValues) => { 
                         console.log('Override Form Values Changing:', allValues); 
                     }}
                 >
                     <Form.Item 
                        name="user_id" 
                        label="Usuario" 
                        rules={[
                            { 
                                required: true, 
                                message: 'Debe seleccionar un usuario',
                                type: 'number',
                                transform: (value) => {
                                    // Convertir a número si es string
                                    return typeof value === 'string' ? parseInt(value, 10) : value;
                                }
                            }
                        ]}
                    >
                        <Select 
                            showSearch 
                            placeholder="Usuario" 
                            optionFilterProp="children"
                            filterOption={(input, option) => 
                                (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                            }
                            loading={loadingUsers}
                        >
                            {usersForSelect.map(user => (
                                <Option key={user.id} value={user.id}>{user.username}</Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item 
                        name="date" 
                        label="Fecha del Cambio" 
                        rules={[{ required: true, message: 'Selecciona fecha' }]}
                    >
                        <DatePicker format="YYYY-MM-DD" style={{ width: '100%' }} locale={locale} />
                    </Form.Item>
                    <Form.Item 
                        name="actual_shift_code" 
                        label="Turno Realizado" 
                        rules={[
                            { 
                                required: true, 
                                message: 'Debe seleccionar un turno',
                                whitespace: true 
                            }
                        ]}
                    >
                        <Select placeholder="Selecciona turno cubierto">
                            <Option value="M">M - Mañana</Option>
                            <Option value="T">T - Tarde</Option>
                            <Option value="N">N - Noche</Option>
                        </Select>
                    </Form.Item>
                    <Form.Item name="notes" label="Notas (Opcional)">
                        <TextArea rows={2} placeholder="Ej: Cubre turno de compañero X por..." />
                    </Form.Item>
                 </Form>
             </Spin>
         </Modal>
      </div>
    );
};

export default CalendarioTurnos;