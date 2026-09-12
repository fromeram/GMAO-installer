// src/pages/CalendarioVacaciones.js (Corregido)
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
    Calendar, Select, Typography, Spin, Alert, message, Col, Row, Card, Tag, Button, Space,
    Modal, Form, Input, DatePicker, Popconfirm, Tooltip, Switch
} from 'antd';
import { 
    PlusOutlined, EditOutlined, DeleteOutlined, CheckOutlined, CloseOutlined, 
    QuestionCircleOutlined, SwapOutlined, ClockCircleOutlined, IssuesCloseOutlined, 
    StopOutlined, ReloadOutlined, InfoCircleOutlined 
} from '@ant-design/icons';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import locale from 'antd/es/date-picker/locale/es_ES';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
import isBetween from 'dayjs/plugin/isBetween';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import '../styles/CommonPage.css';

// --- Configuración Dayjs ---
dayjs.locale('es'); 
dayjs.extend(utc); 
dayjs.extend(timezone); 
dayjs.extend(isBetween);
dayjs.tz.setDefault("Europe/Madrid");

// --- Constantes y Helpers ---
const { Title, Text } = Typography; 
const { Option } = Select; 
const { TextArea } = Input;

// Estilos para el calendario
const calendarCustomStyles = `
  /* Aumentar tamaño de celdas del calendario */
  .ant-picker-calendar-full .ant-picker-calendar-date {
    height: auto !important;
    min-height: 120px !important; 
    padding: 4px 8px !important;
  }

  /* Aumentar ancho de las celdas - afecta a toda la tabla */
  .ant-picker-calendar-full .ant-picker-panel {
    width: 100% !important;
  }

  /* Asegurar que los días de la semana tienen suficiente espacio */
  .ant-picker-calendar-full .ant-picker-panel .ant-picker-calendar-date-content {
    height: auto !important;
    overflow-y: auto !important;
    max-height: calc(100% - 20px) !important;
  }

  /* Mejorar la visualización de cada celda de día */
  .ant-picker-calendar-full .ant-picker-cell-in-view {
    min-width: 100px !important;
  }

  /* Permitir scroll vertical dentro de cada celda si hay muchos eventos */
  .ant-picker-calendar-full .ant-picker-calendar-date-content {
    overflow-y: auto;
  }

  /* Estilos para la vista de mes completo */
  .ant-picker-calendar-full .ant-picker-cell {
    padding: 1px !important;
  }
  
  /* Clases para estados de solicitudes */
  .vacation-list-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 2px 4px;
    margin-bottom: 2px;
    border-radius: 2px;
  }
  
  .vacation-status-pending {
    background-color: rgba(250, 219, 20, 0.1);
    border: 1px dashed #faad14;
  }
  
  .vacation-status-approved {
    background-color: rgba(82, 196, 26, 0.1);
    border: 1px solid #52c41a;
  }
  
  .vacation-status-rejected {
    background-color: rgba(255, 77, 79, 0.1);
    border: 1px dashed #ff4d4f;
  }
  
  .has-pending-requests {
    background-color: rgba(250, 173, 20, 0.05);
  }
  
  .base-shift-overlay {
    margin-left: 4px;
    opacity: 0.6;
    font-size: 10px;
  }
  
  .vacation-list-item-actions {
    opacity: 0.7;
  }
  
  .vacation-list-item-actions:hover {
    opacity: 1;
  }
`;

// Colores e iconos para estados y tipos
const requestStatusColors = { 
    'Solicitado': 'gold', 
    'Aprobado': 'success', 
    'Rechazado': 'error' 
};

const requestStatusIcons = { 
    'Solicitado': <ClockCircleOutlined />, 
    'Aprobado': <CheckOutlined />, 
    'Rechazado': <CloseOutlined /> 
};

const shiftColors = { 
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
    'no_assignment': 'default',
    '-': 'default'
};

const shiftIcons = { 
    'M': <></>, 
    'T': <></>, 
    'N': <></>, 
    'P': <></>, 
    'L': <></>, 
    'V': <></>, 
    'B': <></>, 
    'A': <></>, 
    'F': <></>, 
    '?': <QuestionCircleOutlined />, 
    'override': <SwapOutlined />, 
    'absence': <IssuesCloseOutlined />, 
    'shift': <></>, 
    'error': <StopOutlined />, 
    'no_assignment': <></>,
    '-': <></>
};

const absenceTypeNames = { 
    'V': 'Vacaciones', 
    'B': 'Baja Médica', 
    'A': 'As.Propios', 
    'F': 'Festivo' 
};

const shiftCodeNames = { 
    'M': 'Mañana', 
    'T': 'Tarde', 
    'N': 'Noche' 
};

// Función para generar etiquetas de eventos de vacaciones
const getVacationEventTag = (eventData) => {
    if (!eventData) return <Tag color="default">-</Tag>;
    
    const status = eventData.status || 'Solicitado';
    const color = requestStatusColors[status] || 'default';
    const icon = requestStatusIcons[status];
    
    return (
        <Tooltip title={`${status} | ${eventData.start_date} a ${eventData.end_date}`}>
            <Tag color={color} icon={icon}>V</Tag>
        </Tooltip>
    );
};

// Función para generar etiquetas de eventos base (turnos, ausencias)
const getBaseEventTag = (eventData) => {
    if (!eventData) return <Tag color="default">-</Tag>;
    
    let color = 'default';
    let text = '?';
    let icon = null;
    
    if (eventData.type === 'shift') {
        color = shiftColors[eventData.code] || 'default';
        text = eventData.code || '?';
        icon = shiftIcons[eventData.code];
    } 
    else if (eventData.type === 'absence') {
        color = shiftColors[eventData.absence_type] || 'volcano';
        text = eventData.absence_type || '?';
        icon = shiftIcons[eventData.absence_type];
    }
    else if (eventData.type === 'override') {
        color = shiftColors.override;
        text = eventData.code || '?';
        icon = shiftIcons.override;
    }
    else if (eventData.type === 'error') {
        color = 'error';
        text = '?';
        icon = <StopOutlined />;
    }
    else {
        color = 'default';
        text = '-';
    }
    
    const typeName = eventData.type === 'shift' 
        ? `Turno: ${text}` 
        : eventData.type === 'absence' 
            ? absenceTypeNames[text] || 'Ausencia'
            : eventData.type === 'override'
                ? `Cobertura: ${shiftCodeNames[text] || text}`
                : "Desconocido";
                
    const notes = eventData.notes || '';
    const title = `${typeName}${notes ? ` | ${notes}` : ''}`;
    
    return (
        <Tooltip title={title}>
            <Tag color={color} icon={icon}>{text}</Tag>
        </Tooltip>
    );
};

const MANAGER_ROLES = ["Administrador", "Jefe Mantenimiento", "Jefe Sección"];

// --- Componente Principal ---
const CalendarioVacaciones = () => {
    // --- Estados ---
    const [loadingBase, setLoadingBase] = useState(true);
    const [loadingRequests, setLoadingRequests] = useState(true);
    const [error, setError] = useState(null);
    const [baseCalendarData, setBaseCalendarData] = useState({});
    const [vacationRequestsData, setVacationRequestsData] = useState({});
    const [users, setUsers] = useState([]);
    const [selectedDate, setSelectedDate] = useState(dayjs.tz());
    const { currentUser } = useAuth();
    const [isRequestModalVisible, setIsRequestModalVisible] = useState(false);
    const [requestModalMode, setRequestModalMode] = useState('add');
    const [editingRequestData, setEditingRequestData] = useState(null);
    const [requestForm] = Form.useForm();
    const [isSubmittingRequest, setIsSubmittingRequest] = useState(false);
    const [isApprovalModalVisible, setIsApprovalModalVisible] = useState(false);
    const [selectedRequestForApproval, setSelectedRequestForApproval] = useState(null);
    const [approvalForm] = Form.useForm();
    const [isSubmittingApproval, setIsSubmittingApproval] = useState(false);
    const [usersForSelect, setUsersForSelect] = useState([]);
    const [loadingUsersSelect, setLoadingUsersSelect] = useState(false);
    const [showAllUsers, setShowAllUsers] = useState(true);
    const [hasPendingRequests, setHasPendingRequests] = useState(false);

    // Permiso Memoizado
    const hasManagementPermission = useMemo(() => {
        return currentUser?.role && MANAGER_ROLES.includes(currentUser.role);
    }, [currentUser]);

    // --- Funciones de Carga de Datos ---
    const fetchBaseCalendarData = useCallback(async (year, month) => {
        setLoadingBase(true);
        console.log(`Fetcheando datos de calendario base para ${year}-${month}`);
        try {
            const url = `/calendar-data?year=${year}&month=${month}&show_all_users=${showAllUsers ? 'true' : 'false'}`;
            const data = await fetchWithAuth(url);
            
            if (!data || typeof data !== 'object') {
                throw new Error("Respuesta inválida al cargar datos base del calendario");
            }
            
            // Procesamos los datos y extraemos usuarios
            const processedBaseData = {};
            const userMap = {};
            
            Object.entries(data).forEach(([dateStr, usersOnDate]) => {
                processedBaseData[dateStr] = usersOnDate || {};
                
                if (usersOnDate && typeof usersOnDate === 'object') {
                    Object.keys(usersOnDate).forEach(username => {
                        if (!userMap[username]) {
                            const foundUser = usersForSelect.find(u => u.username === username);
                            userMap[username] = { 
                                id: foundUser?.id || null, 
                                username: username 
                            };
                        }
                    });
                }
            });
            
            const activeUsers = Object.values(userMap).sort((a,b) => 
                a.username.localeCompare(b.username)
            );
            
            setUsers(activeUsers);
            setBaseCalendarData(processedBaseData);
            console.log(`Datos base del calendario cargados. Usuarios detectados: ${activeUsers.length}`);
        } catch (err) {
            console.error("Error al cargar datos base:", err);
            const msg = `Error cargando turnos base: ${err.message || 'Desconocido'}`;
            setError(e => e ? `${e} | ${msg}` : msg);
            message.error(msg);
            setBaseCalendarData({});
            setUsers([]);
        } finally {
            setLoadingBase(false);
        }
    }, [usersForSelect, showAllUsers]);

    const fetchVacationRequestsData = useCallback(async (year, month) => {
        setLoadingRequests(true);
        console.log(`Fetching solicitudes de vacaciones para ${year}-${month}`);
        try {
            const url = `/vacation-requests/calendar?year=${year}&month=${month}`;
            const data = await fetchWithAuth(url);
            
            if (typeof data !== 'object' || data === null) {
                throw new Error("Respuesta inválida al cargar solicitudes");
            }
            
            setVacationRequestsData(data || {});
            
            // Detectar si hay solicitudes pendientes
            let pendingFound = false;
            Object.values(data || {}).forEach(dayData => {
                Object.values(dayData || {}).forEach(event => {
                    if (event?.status === 'Solicitado') {
                        pendingFound = true;
                    }
                });
            });
            
            setHasPendingRequests(pendingFound);
            console.log(`Datos de solicitudes cargados. Solicitudes pendientes: ${pendingFound ? 'Sí' : 'No'}`);
        } catch (err) {
            console.error("Error al cargar solicitudes:", err);
            const msg = `Error cargando solicitudes: ${err.message || 'Desconocido'}`;
            setError(e => e ? `${e} | ${msg}` : msg);
            message.error(msg);
            setVacationRequestsData({});
        } finally {
            setLoadingRequests(false);
        }
    }, []);

    const fetchUsersForSelect = useCallback(async () => {
        // Evitar cargar usuarios si ya están cargados o si ya está en proceso
        if (usersForSelect.length > 0 || loadingUsersSelect) return;
        
        setLoadingUsersSelect(true);
        try {
            const usersData = await fetchWithAuth('/users');
            if (Array.isArray(usersData)) {
                setUsersForSelect(usersData);
                console.log(`Cargados ${usersData.length} usuarios para selector`);
            } else {
                console.error("Formato de datos de usuarios inesperado:", usersData);
                setUsersForSelect([]);
            }
        } catch (err) {
            console.error("Error al cargar usuarios:", err);
            message.error(`Error cargando usuarios: ${err.message || 'Desconocido'}`);
        } finally {
            setLoadingUsersSelect(false);
        }
    }, [usersForSelect.length, loadingUsersSelect]);

    // --- useEffect para cargar datos ---
    // Efecto para cargar usuarios para el Select (si tiene permisos)
    useEffect(() => {
        if (hasManagementPermission && usersForSelect.length === 0) {
            fetchUsersForSelect();
        }
    }, [hasManagementPermission, usersForSelect.length, fetchUsersForSelect]);

    // Efecto principal para cargar datos del calendario cuando cambia la fecha o showAllUsers
    useEffect(() => {
        const year = selectedDate.year();
        const month = selectedDate.month() + 1; // En JS los meses van de 0-11, pero la API espera 1-12
        
        console.log(`Cargando datos para ${month}/${year} (showAllUsers: ${showAllUsers})`);
        fetchBaseCalendarData(year, month);
        fetchVacationRequestsData(year, month);
    }, [selectedDate, showAllUsers, fetchBaseCalendarData, fetchVacationRequestsData]);

    // --- Renderizado de Celdas ---
    const dateCellRender = useCallback((value) => {
        const dateStr = value.format('YYYY-MM-DD');
        const baseDayData = baseCalendarData[dateStr] || {};
        const requestsDayData = vacationRequestsData[dateStr] || {};
        
        // Mostrar todos los usuarios o solo los que tienen eventos en esta fecha
        const usersToShow = showAllUsers 
            ? users 
            : users.filter(u => u?.id && (baseDayData[u.username] || requestsDayData[u.username]));
            
        if (usersToShow.length === 0 && !loadingBase && !loadingRequests) {
            return <div className="vacation-calendar-cell-content" />;
        }

        return (
            <div className="vacation-calendar-cell-content">
                <ul style={{ 
                    margin: 0, 
                    padding: 0, 
                    listStyle: 'none', 
                    maxHeight: '100%',
                    overflowY: 'auto'
                }}>
                    {usersToShow.map((user) => {
                        // Verificar y mostrar el evento adecuado para este usuario en esta fecha
                        const username = user.username;
                        if (!username) return null;
                        
                        const baseEvent = baseDayData[username];
                        const vacationRequest = requestsDayData[username];
                        
                        let displayTag = null;
                        let baseInfoSpan = null;
                        let actionButtons = null;
                        let itemClassName = "vacation-list-item";
                        
                        // Permisos para administrar esta solicitud
                        const canCurrentUserManage = hasManagementPermission;
                        const isOwnRequest = currentUser?.id === vacationRequest?.user_id;
                        const isRequestPending = vacationRequest?.status === 'Solicitado';
                        const isRequestRejected = vacationRequest?.status === 'Rechazado';

                        // Prioridad: mostrar solicitud pendiente/rechazada sobre evento base
                        if (vacationRequest && (isRequestPending || isRequestRejected)) {
                            displayTag = getVacationEventTag(vacationRequest);
                            
                            // Mostrar el turno base por debajo como referencia
                            if (baseEvent) {
                                baseInfoSpan = <span className="base-shift-overlay">
                                    {getBaseEventTag(baseEvent)}
                                </span>;
                            }
                            
                            // Clases CSS específicas según estado
                            if (isRequestPending) itemClassName += " vacation-status-pending";
                            if (isRequestRejected) itemClassName += " vacation-status-rejected";
                            
                            // Botones de acción según permisos
                            const canEdit = isOwnRequest && isRequestPending;
                            const canDelete = (isOwnRequest || canCurrentUserManage) && isRequestPending;
                            const canApproveReject = canCurrentUserManage && isRequestPending;
                            
                            actionButtons = (
                                <Space size={0} className="vacation-list-item-actions">
                                    {canEdit && (
                                        <Tooltip title="Editar Solicitud">
                                            <Button 
                                                type="text" 
                                                size="small" 
                                                icon={<EditOutlined />} 
                                                onClick={(e) => { 
                                                    e.stopPropagation();
                                                    handleOpenRequestModal('edit', vacationRequest);
                                                }}
                                            />
                                        </Tooltip>
                                    )}
                                    
                                    {canDelete && (
                                        <Tooltip title="Eliminar Solicitud">
                                            <Popconfirm 
                                                title="¿Eliminar esta solicitud?" 
                                                onConfirm={(e) => { 
                                                    e.stopPropagation();
                                                    handleDeleteVacation(vacationRequest.id);
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
                                                />
                                            </Popconfirm>
                                        </Tooltip>
                                    )}
                                    
                                    {canApproveReject && (
                                        <>
                                            <Tooltip title="Aprobar">
                                                <Button 
                                                    type="text" 
                                                    style={{ color: 'green' }} 
                                                    size="small" 
                                                    icon={<CheckOutlined />} 
                                                    onClick={(e) => { 
                                                        e.stopPropagation();
                                                        handleOpenApprovalModal(vacationRequest, 'Aprobado');
                                                    }}
                                                />
                                            </Tooltip>
                                            
                                            <Tooltip title="Rechazar">
                                                <Button 
                                                    type="text" 
                                                    danger 
                                                    size="small" 
                                                    icon={<CloseOutlined />} 
                                                    onClick={(e) => { 
                                                        e.stopPropagation();
                                                        handleOpenApprovalModal(vacationRequest, 'Rechazado');
                                                    }}
                                                />
                                            </Tooltip>
                                        </>
                                    )}
                                </Space>
                            );
                        } else if (baseEvent) {
                            // Mostrar evento base (turno o ausencia) si no hay solicitud prioritaria
                            displayTag = getBaseEventTag(baseEvent);
                            
                            // Resaltar visualmente las vacaciones aprobadas
                            if (baseEvent.type === 'absence' && baseEvent.absence_type === 'V') {
                                itemClassName += " vacation-status-approved";
                            }
                        } else {
                            // Sin eventos para mostrar
                            if (!showAllUsers) return null;
                            displayTag = <Tag icon={shiftIcons['-']} color={shiftColors['-']}>-</Tag>;
                        }

                        return (
                            <li key={`${username}-${dateStr}`} className={itemClassName}>
                                <span style={{ 
                                    flexGrow: 1, 
                                    overflow: 'hidden', 
                                    textOverflow: 'ellipsis',
                                    display: 'flex',
                                    alignItems: 'center'
                                }}>
                                    {displayTag}
                                    <span style={{ 
                                        marginLeft: '4px', 
                                        overflow: 'hidden', 
                                        textOverflow: 'ellipsis' 
                                    }}>
                                        {username}
                                    </span>
                                    {baseInfoSpan}
                                </span>
                                {actionButtons}
                            </li>
                        );
                    })}
                </ul>
            </div>
        );
    }, [baseCalendarData, vacationRequestsData, users, currentUser, hasManagementPermission, showAllUsers]);

    // Cabecera del Calendario
    const headerRender = useCallback(({ value, onChange }) => {
        const currentYear = value.year();
        const currentMonth = value.month(); // 0 = Enero, 11 = Diciembre
    
        const monthOptions = [];
        let monthIter = dayjs().locale('es').month(0); // Empezar en Enero
        for (let i = 0; i < 12; i++) {
            const monthName = monthIter.month(i).format('MMMM');
            monthOptions.push(
                <Option key={i} value={i} style={{ textTransform: 'capitalize' }}>
                    {monthName}
                </Option>
            );
        }
    
        const yearOptions = [];
        for (let i = currentYear - 5; i < currentYear + 6; i += 1) {
            yearOptions.push(<Option key={i} value={i}>{i}</Option>);
        }
    
        const handleYearChange = (newYear) => {
            const newDate = value.year(newYear);
            onChange(newDate);
            setSelectedDate(newDate);
        };
    
        const handleMonthChange = (newMonthIndex) => {
            const newDate = value.month(newMonthIndex);
            onChange(newDate);
            setSelectedDate(newDate);
        };
    
        const goToToday = () => {
            const now = dayjs.tz();
            onChange(now);
            setSelectedDate(now);
        };
    
        const reloadData = () => {
             const year = selectedDate.year();
             const month = selectedDate.month() + 1;
             fetchBaseCalendarData(year, month);
             fetchVacationRequestsData(year, month);
        };
    
        return (
            <div style={{ padding: '10px 15px' }}>
                <Row justify="space-between" align="middle" gutter={8} style={{ marginBottom: '8px' }}>
                    <Col>
                        <Title level={4} style={{ margin: 0, textTransform: 'capitalize' }}>
                            {value.format('MMMM YYYY')}
                        </Title>
                    </Col>
                    <Col>
                        <Space>
                            <Select 
                                size="small" 
                                dropdownMatchSelectWidth={false} 
                                value={currentYear} 
                                onChange={handleYearChange}
                            >
                                {yearOptions}
                            </Select>
                            <Select 
                                size="small" 
                                style={{ width: 120 }} 
                                value={currentMonth} 
                                onChange={handleMonthChange}
                            >
                                {monthOptions}
                            </Select>
                            <Button size="small" onClick={goToToday}>Hoy</Button>
                            <Tooltip title="Recargar datos">
                               <Button size="small" icon={<ReloadOutlined />} onClick={reloadData} />
                            </Tooltip>
                        </Space>
                    </Col>
                </Row>
                <Row justify="end">
                    <Space align="center">
                        <Text style={{ fontSize: '12px' }}>Mostrar todos:</Text>
                        <Switch 
                            size="small" 
                            checked={showAllUsers} 
                            onChange={setShowAllUsers} 
                            checkedChildren="Sí" 
                            unCheckedChildren="No"
                        />
                        {hasPendingRequests && hasManagementPermission && (
                            <Tag color="orange" icon={<InfoCircleOutlined />}>
                                Solicitudes Pendientes
                            </Tag>
                        )}
                    </Space>
                </Row>
            </div>
        );
    }, [selectedDate, showAllUsers, hasPendingRequests, hasManagementPermission, fetchBaseCalendarData, fetchVacationRequestsData]);

    // --- Handlers para Modales y Acciones ---
    // Click en fecha del calendario
    const handleDateSelect = (date, info) => {
        if (info.source === 'date') {
            handleOpenRequestModal('add', null, date);
        }
    };
    
    // Abrir modal de solicitud (nueva o edición)
    const handleOpenRequestModal = (mode = 'add', record = null, defaultDate = null) => {
        // Verificar permisos para editar
        if (mode === 'edit') {
            if (!record || record.status !== 'Solicitado') {
                message.warning("Solo se pueden editar solicitudes pendientes");
                return;
            }
            
            if (!hasManagementPermission && currentUser?.id !== record.user_id) {
                message.error("No tienes permiso para editar esta solicitud");
                return;
            }
        }
        
        setRequestModalMode(mode);
        setEditingRequestData(mode === 'edit' ? record : null);
        requestForm.resetFields();
        
        // Configurar valores iniciales según modo
        let initialValues = {};
        if (mode === 'edit' && record) {
            initialValues = {
                user_id: record.user_id,
                dateRange: [dayjs.tz(record.start_date), dayjs.tz(record.end_date)],
                notes: record.notes
            };
        } else {
            const dateToUse = defaultDate || selectedDate;
            initialValues = {
                user_id: currentUser?.id,
                dateRange: [dateToUse, dateToUse]
            };
            
            // Cargar usuarios si es administrador y la lista está vacía
            if (hasManagementPermission && usersForSelect.length === 0) {
                fetchUsersForSelect();
            }
        }
        
        requestForm.setFieldsValue(initialValues);
        setIsRequestModalVisible(true);
    };
    
    // Enviar solicitud de vacaciones (crear o actualizar)
    const handleVacationModalSubmit = async () => {
        setIsSubmittingRequest(true);
        try {
            const values = await requestForm.validateFields();
            
            if (!values.dateRange || values.dateRange.length !== 2) {
                throw new Error("Rango de fechas inválido");
            }
            
            // Usar el ID del usuario actual si no es administrador
            const userIdToSubmit = hasManagementPermission ? values.user_id : currentUser?.id;
            if (!userIdToSubmit) {
                throw new Error("ID de usuario inválido");
            }
            
            const payload = {
                user_id: userIdToSubmit,
                start_date: values.dateRange[0].format('YYYY-MM-DD'),
                end_date: values.dateRange[1].format('YYYY-MM-DD'),
                notes: values.notes || null
            };
            
            if (requestModalMode === 'edit' && editingRequestData) {
                // La API actualmente no soporta edición, pero podríamos implementarla
                message.info("La edición de solicitudes no está habilitada actualmente");
            } else {
                // Crear nueva solicitud
                console.log("Enviando solicitud de vacaciones:", payload);
                const response = await fetchWithAuth('/vacation-requests', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                console.log("Respuesta:", response);
                message.success('Solicitud de vacaciones enviada correctamente');
            }
            
            // Cerrar modal y recargar datos
            setIsRequestModalVisible(false);
            setEditingRequestData(null);
            
            const cy = selectedDate.year();
            const cm = selectedDate.month() + 1;
            fetchBaseCalendarData(cy, cm);
            fetchVacationRequestsData(cy, cm);
        } catch (errorInfo) {
            console.error('Error guardando solicitud:', errorInfo);
            if (errorInfo instanceof Error) {
                message.error(`Error: ${errorInfo.message}`);
            } else {
                message.error('Por favor revise los campos del formulario');
            }
        } finally {
            setIsSubmittingRequest(false);
        }
    };
    
    // Cancelar modal de solicitud
    const handleVacationModalCancel = () => {
        setIsRequestModalVisible(false);
        setEditingRequestData(null);
        requestForm.resetFields();
    };
    
    // Abrir modal de aprobación/rechazo
    const handleOpenApprovalModal = (request, intendedStatus) => {
        if (!hasManagementPermission) {
            message.error("No tienes permiso para aprobar/rechazar solicitudes");
            return;
        }
        
        setSelectedRequestForApproval(request);
        approvalForm.resetFields();
        approvalForm.setFieldsValue({
            status: intendedStatus,
            manager_notes: request.manager_notes || ''
        });
        
        setIsApprovalModalVisible(true);
    };
    
    // Enviar aprobación/rechazo
    const handleApprovalSubmit = async () => {
        if (!selectedRequestForApproval) return;
        
        setIsSubmittingApproval(true);
        try {
            const values = await approvalForm.validateFields();
            
            const payload = {
                status: values.status,
                manager_notes: values.manager_notes || null
            };
            
            console.log("Enviando aprobación/rechazo:", payload);
            
            await fetchWithAuth(`/vacation-requests/${selectedRequestForApproval.id}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            message.success(`Solicitud ${values.status.toLowerCase()} correctamente`);
            
            // Cerrar modal y recargar datos
            setIsApprovalModalVisible(false);
            setSelectedRequestForApproval(null);
            
            const cy = selectedDate.year();
            const cm = selectedDate.month() + 1;
            fetchBaseCalendarData(cy, cm);
            fetchVacationRequestsData(cy, cm);
        } catch (errorInfo) {
            console.error('Error procesando solicitud:', errorInfo);
            if (errorInfo instanceof Error) {
                message.error(`Error: ${errorInfo.message}`);
            } else {
                message.error('Por favor revise los campos del formulario');
            }
        } finally {
            setIsSubmittingApproval(false);
        }
    };
    
    // Cancelar modal de aprobación
    const handleApprovalModalCancel = () => {
        setIsApprovalModalVisible(false);
        setSelectedRequestForApproval(null);
        approvalForm.resetFields();
    };
    
    // Eliminar solicitud de vacaciones
    const handleDeleteVacation = async (requestId) => {
        const requestToDelete = findRequestInCalendarData(requestId);
        
        if (!requestToDelete) {
            message.error("Solicitud no encontrada");
            return;
        }
        
        // Verificar permisos
        const canDelete = hasManagementPermission || 
            (currentUser?.id === requestToDelete.user_id && requestToDelete.status === 'Solicitado');
            
        if (!canDelete) {
            message.error("No tienes permiso para eliminar esta solicitud");
            return;
        }
        
        // Verificar estado
        if (requestToDelete.status !== 'Solicitado') {
            message.warning("Solo se pueden eliminar solicitudes pendientes");
            return;
        }
        
        try {
            await fetchWithAuth(`/vacation-requests/${requestId}`, {
                method: 'DELETE'
            });
            
            message.success('Solicitud eliminada correctamente');
            
            // Recargar datos
            const cy = selectedDate.year();
            const cm = selectedDate.month() + 1;
            fetchBaseCalendarData(cy, cm);
            fetchVacationRequestsData(cy, cm);
        } catch (err) {
            console.error("Error eliminando solicitud:", err);
            message.error(`Error al eliminar: ${err.message || 'Error desconocido'}`);
        }
    };

    // Helper para buscar una solicitud en los datos del calendario
    const findRequestInCalendarData = (requestId) => {
        for (const dateKey in vacationRequestsData) {
            const dayData = vacationRequestsData[dateKey];
            
            if (dayData && typeof dayData === 'object') {
                for (const username in dayData) {
                    const event = dayData[username];
                    
                    if (event?.type === 'vacation_request' && event.id === requestId) {
                        return event;
                    }
                }
            }
        }
        
        return null;
    };
    
    // Helper para estilos de celda
    const getCellClassName = useCallback((date) => {
        const dateStr = date.format('YYYY-MM-DD');
        const dayData = vacationRequestsData[dateStr] || {};
        
        for (const username in dayData) {
            const event = dayData[username];
            
            if (event?.status === 'Solicitado') {
                return 'has-pending-requests';
            }
        }
        
        return '';
    }, [vacationRequestsData]);

    // Memoizar headerRender
    const memoizedHeaderRender = useMemo(() => headerRender, [headerRender]);

    // --- Renderizado del Componente ---
    const combinedLoading = loadingBase || loadingRequests || loadingUsersSelect;

    return (
        <div className="page-container">
            <style>{calendarCustomStyles}</style>
            <Title level={2} className="page-title">Calendario de Vacaciones</Title>
            
            {error && (
                <Alert 
                    message="Error al cargar datos" 
                    description={error} 
                    type="error" 
                    showIcon 
                    closable 
                    onClose={() => setError(null)} 
                    style={{ marginBottom: 16 }} 
                />
            )}
            
            <Spin spinning={combinedLoading} tip="Cargando calendario...">
                <Card className="table-container" bordered={false}>
                    <Space style={{ marginBottom: 16 }}>
                        <Button 
                            icon={<PlusOutlined />} 
                            type="primary" 
                            onClick={() => handleOpenRequestModal('add', null, selectedDate)}
                        >
                            Solicitar Vacaciones/Ausencia
                        </Button>
                        
                        {hasPendingRequests && hasManagementPermission && (
                            <Alert 
                                type="warning" 
                                message="Hay solicitudes pendientes" 
                                showIcon 
                                style={{ marginBottom: 0 }}
                            />
                        )}
                    </Space>
                    
                    <Calendar 
                        locale={locale} 
                        dateCellRender={dateCellRender} 
                        headerRender={memoizedHeaderRender} 
                        onSelect={handleDateSelect} 
                        value={selectedDate} 
                        cellClassName={getCellClassName}
                    />
                </Card>
            </Spin>
            
            <Row gutter={16} style={{ marginTop: 16 }}>
                <Col span={12}>
                    <Card size="small" title="Leyenda Estados Solicitud">
                        <Space wrap>
                            {Object.entries(requestStatusColors).map(([status, color]) => (
                                <Tag 
                                    icon={requestStatusIcons[status]} 
                                    color={color} 
                                    key={status}
                                >
                                    {status}
                                </Tag>
                            ))}
                        </Space>
                    </Card>
                </Col>
                
                <Col span={12}>
                    <Card size="small" title="Leyenda Tipos Base">
                        <Space wrap>
                            {Object.entries(shiftColors)
                                .filter(([key]) => !['override','absence','shift','error','no_assignment','-'].includes(key))
                                .map(([code, color]) => {
                                    const name = absenceTypeNames[code] || shiftCodeNames[code] || code;
                                    return (
                                        <Tag 
                                            icon={shiftIcons[code]} 
                                            color={color} 
                                            key={code}
                                        >
                                            {code}: {name}
                                        </Tag>
                                    );
                                })
                            }
                        </Space>
                    </Card>
                </Col>
            </Row>

            {/* Modal para Solicitar/Editar Vacaciones */}
            <Modal 
                title={requestModalMode === 'edit' 
                    ? `Editar Solicitud ID: ${editingRequestData?.id || '?'}` 
                    : `Solicitar Vacaciones / Ausencia`
                } 
                open={isRequestModalVisible} 
                onOk={handleVacationModalSubmit} 
                onCancel={handleVacationModalCancel} 
                confirmLoading={isSubmittingRequest} 
                destroyOnClose 
                okText={requestModalMode === 'edit' ? "Actualizar" : "Enviar"} 
                cancelText="Cancelar" 
                width={600}
            >
                <Spin spinning={loadingUsersSelect}>
                    <Form form={requestForm} layout="vertical" name="request_form">
                        {hasManagementPermission ? (
                            <Form.Item 
                                name="user_id" 
                                label="Usuario (si solicita para otro)" 
                                rules={[{ required: true, message: 'Selecciona usuario' }]}
                            >
                                <Select 
                                    showSearch 
                                    placeholder="Usuario" 
                                    optionFilterProp="children" 
                                    filterOption={(input, option) => 
                                        (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                                    } 
                                    loading={loadingUsersSelect} 
                                    disabled={requestModalMode === 'edit'}
                                >
                                    {usersForSelect.map(user => (
                                        <Option key={user.id} value={user.id}>{user.username}</Option>
                                    ))}
                                </Select>
                            </Form.Item>
                        ) : (
                            <Form.Item name="user_id" hidden><Input /></Form.Item>
                        )}
                        
                        <Form.Item 
                            name="dateRange" 
                            label="Fechas Solicitadas (Inicio - Fin)" 
                            rules={[{ required: true, message: 'Selecciona rango de fechas' }]}
                        >
                            <DatePicker.RangePicker 
                                format="YYYY-MM-DD" 
                                style={{ width: '100%' }} 
                                locale={locale} 
                            />
                        </Form.Item>
                        
                        <Form.Item name="notes" label="Notas / Motivo (Opcional)">
                            <TextArea rows={3} />
                        </Form.Item>
                    </Form>
                </Spin>
            </Modal>

            {/* Modal para Aprobar/Rechazar Solicitudes */}
            <Modal 
                title={`${approvalForm.getFieldValue('status') || ''} Solicitud de Vacaciones`} 
                open={isApprovalModalVisible} 
                onOk={handleApprovalSubmit} 
                onCancel={handleApprovalModalCancel} 
                confirmLoading={isSubmittingApproval} 
                destroyOnClose 
                okText={approvalForm.getFieldValue('status')} 
                cancelText="Cancelar" 
                width={500}
            >
                <Form form={approvalForm} layout="vertical" name="approval_form">
                    <p>Solicitud ID: <strong>{selectedRequestForApproval?.id}</strong></p>
                    <p>Usuario: <strong>
                        {usersForSelect.find(u => u.id === selectedRequestForApproval?.user_id)?.username || '?'}
                    </strong></p>
                    <p>Fechas: <strong>
                        {dayjs.tz(selectedRequestForApproval?.start_date).format('DD/MM/YYYY')} - 
                        {dayjs.tz(selectedRequestForApproval?.end_date).format('DD/MM/YYYY')}
                    </strong></p>
                    
                    {selectedRequestForApproval?.notes && (
                        <p>Notas Solicitante: <i>{selectedRequestForApproval.notes}</i></p>
                    )}
                    
                    <Form.Item name="status" hidden><Input /></Form.Item>
                    
                    <Form.Item 
                        name="manager_notes" 
                        label={`Notas para ${approvalForm.getFieldValue('status') || 'la respuesta'} (Opcional)`}
                    >
                        <TextArea rows={3} />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default CalendarioVacaciones;