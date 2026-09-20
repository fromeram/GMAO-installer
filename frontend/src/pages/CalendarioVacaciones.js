// src/pages/CalendarioVacaciones.js (PARTE 1 - Inicio hasta mitad)
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
    Calendar, Select, Typography, Spin, Alert, message, Col, Row, Card, Tag, Button, Space,
    Modal, Form, Input, DatePicker, Popconfirm, Tooltip, Switch, Table, Empty
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
import relativeTime from 'dayjs/plugin/relativeTime';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import '../styles/CommonPage.css';

// --- Configuración Dayjs ---
dayjs.locale('es'); 
dayjs.extend(utc); 
dayjs.extend(timezone); 
dayjs.extend(isBetween);
dayjs.extend(relativeTime);
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

// Componente para el panel de solicitudes pendientes GLOBALES
const PendingRequestsPanel = ({ isVisible, onClose, onNavigateToMonth, globalPendingRequests }) => {
    if (!isVisible) return null;

    const columns = [
        {
            title: 'Usuario',
            dataIndex: 'username',
            key: 'username',
            render: (username, record) => (
                <div>
                    <strong style={{ color: '#1890ff', fontSize: '14px' }}>
                        {username}
                    </strong>
                    <div style={{ fontSize: '11px', color: '#999', marginTop: '2px' }}>
                        ID: {record.user_id}
                    </div>
                </div>
            )
        },
        {
            title: 'Fechas',
            key: 'dates',
            render: (_, record) => (
                <div>
                    <div style={{ fontWeight: 'bold' }}>
                        {dayjs(record.start_date).format('DD/MM/YYYY')}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                        hasta {dayjs(record.end_date).format('DD/MM/YYYY')}
                    </div>
                    <div style={{ fontSize: '11px', color: '#999' }}>
                        ({dayjs(record.end_date).diff(dayjs(record.start_date), 'days') + 1} días)
                    </div>
                    <div style={{ fontSize: '10px', color: '#fa8c16', fontWeight: 'bold' }}>
                        📅 {dayjs(record.start_date).format('MMMM YYYY')}
                    </div>
                </div>
            )
        },
        {
            title: 'Notas',
            dataIndex: 'notes',
            key: 'notes',
            ellipsis: true,
            render: notes => (
                <span style={{ fontStyle: notes ? 'normal' : 'italic', color: notes ? 'inherit' : '#999' }}>
                    {notes || 'Sin notas'}
                </span>
            )
        },
        {
            title: 'Solicitado',
            dataIndex: 'created_at',
            key: 'created_at',
            render: date => (
                <div>
                    <div>{dayjs(date).format('DD/MM/YYYY')}</div>
                    <div style={{ fontSize: '11px', color: '#999' }}>
                        {dayjs(date).fromNow()}
                    </div>
                </div>
            )
        },
        {
            title: 'Acciones',
            key: 'actions',
            render: (_, record) => (
                <Button 
                    type="primary" 
                    size="small" 
                    onClick={() => {
                        if (onNavigateToMonth) {
                            onNavigateToMonth(dayjs(record.start_date));
                            onClose();
                        }
                    }}
                    style={{ fontSize: '12px' }}
                >
                    📅 Ver en Calendario
                </Button>
            )
        }
    ];

    return (
        <div style={{ 
            position: 'absolute',
            zIndex: 1000,
            width: '90%',
            backgroundColor: 'white',
            boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
            borderRadius: '8px',
            padding: '20px',
            top: '120px',
            left: '5%',
            maxHeight: '75vh',
            overflow: 'auto',
            border: '1px solid #e8e8e8'
        }}>
            <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '16px',
                borderBottom: '1px solid #f0f0f0',
                paddingBottom: '12px'
            }}>
                <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
                    📋 Todas las Solicitudes Pendientes ({globalPendingRequests.length})
                </Title>
                <Button 
                    type="text" 
                    icon={<CloseOutlined />} 
                    onClick={onClose}
                    style={{ color: '#999' }}
                />
            </div>
            
            {globalPendingRequests.length > 0 ? (
                <>
                    <Alert
                        message="⚠️ Gestión Necesaria"
                        description={`Hay ${globalPendingRequests.length} solicitudes de vacaciones pendientes de aprobación en diferentes meses. Es importante gestionarlas pronto para que los empleados puedan planificar.`}
                        type="warning"
                        showIcon
                        style={{ marginBottom: '16px' }}
                    />
                    <Table 
                        columns={columns} 
                        dataSource={globalPendingRequests} 
                        pagination={{ 
                            pageSize: 10,
                            showSizeChanger: false,
                            showTotal: (total) => `${total} solicitudes pendientes`
                        }}
                        size="small"
                        scroll={{ y: 400 }}
                        style={{ border: '1px solid #f0f0f0', borderRadius: '4px' }}
                    />
                </>
            ) : (
                <Empty 
                    description="✅ No hay solicitudes pendientes en todo el sistema"
                    style={{ padding: '40px 0' }}
                />
            )}
        </div>
    );
};

const MANAGER_ROLES = ["Administrador", "Jefe Mantenimiento", "Jefe Sección", "Calidad"];
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
    const [isPendingPanelVisible, setIsPendingPanelVisible] = useState(false);
    const [globalPendingRequests, setGlobalPendingRequests] = useState([]);

    // Permiso Memoizado
    const hasManagementPermission = useMemo(() => {
        const userRole = currentUser?.role?.nombre || (typeof currentUser?.role === 'string' ? currentUser.role : '');
        const hasPermission = MANAGER_ROLES.includes(userRole);
        console.log('🔍 hasManagementPermission check:', {
            currentUser: currentUser?.username,
            userRole,
            MANAGER_ROLES,
            hasPermission
        });
        return hasPermission;
    }, [currentUser]);

    // Método para navegar a un mes específico
    const navigateToMonth = useCallback((date) => {
        setSelectedDate(date);
    }, []);

    // NUEVA FUNCIÓN para cargar TODAS las solicitudes pendientes
    const fetchAllPendingRequests = useCallback(async () => {
        if (!hasManagementPermission) return;
        
        try {
            const response = await fetchWithAuth('/vacation-requests/all-pending');
            const requests = response.pending_requests || [];
            setGlobalPendingRequests(requests);
            console.log(`✅ Cargadas ${requests.length} solicitudes pendientes globales`);
        } catch (error) {
            console.error('Error cargando solicitudes pendientes globales:', error);
            setGlobalPendingRequests([]);
        }
    }, [hasManagementPermission]);
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
            setError(msg);
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
            
            // Detectar si hay solicitudes pendientes EN ESTE MES
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
            
            // TAMBIÉN recargar solicitudes globales
            if (hasManagementPermission) {
                fetchAllPendingRequests();
            }
            
        } catch (err) {
            console.error("Error al cargar solicitudes:", err);
            const msg = `Error cargando solicitudes: ${err.message || 'Desconocido'}`;
            setError(msg);
            message.error(msg);
            setVacationRequestsData({});
        } finally {
            setLoadingRequests(false);
        }
    }, [hasManagementPermission, fetchAllPendingRequests]);

    const fetchUsersForSelect = useCallback(async () => {
        if (usersForSelect.length > 0 || loadingUsersSelect) return;
        
        setLoadingUsersSelect(true);
        try {
            const usersData = await fetchWithAuth('/users');
            if (Array.isArray(usersData)) {
                setUsersForSelect(usersData);
                console.log(`Cargados ${usersData.length} usuarios para selector`);
            } else {
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
    useEffect(() => {
        if (hasManagementPermission && usersForSelect.length === 0) {
            fetchUsersForSelect();
        }
        
        if (hasManagementPermission) {
            fetchAllPendingRequests();
        }
    }, [hasManagementPermission, usersForSelect.length, fetchUsersForSelect, fetchAllPendingRequests]);

    useEffect(() => {
        const year = selectedDate.year();
        const month = selectedDate.month() + 1;
        
        console.log(`Cargando datos para ${month}/${year} (showAllUsers: ${showAllUsers})`);
        fetchBaseCalendarData(year, month);
        fetchVacationRequestsData(year, month);
    }, [selectedDate, showAllUsers, fetchBaseCalendarData, fetchVacationRequestsData]);

    // --- Renderizado de Celdas ---
    const dateCellRender = useCallback((value) => {
        const dateStr = value.format('YYYY-MM-DD');
        const baseDayData = baseCalendarData[dateStr] || {};
        const requestsDayData = vacationRequestsData[dateStr] || {};
        
        // Extraer todos los usuarios únicos que aparecen en este día
        const allUsernames = new Set([
            ...Object.keys(baseDayData),
            ...Object.keys(requestsDayData)
        ]);
        
        if (allUsernames.size === 0) {
            return <div className="vacation-calendar-cell-content" />;
        }

        // Convertir usernames a objetos de usuario
        const usersToShow = Array.from(allUsernames).map(username => {
            const foundUser = users.find(u => u.username === username);
            return foundUser || { username, id: null };
        }).sort((a, b) => a.username.localeCompare(b.username));

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
                        const isRequestApproved = vacationRequest?.status === 'Aprobado';

                        // Mostrar solicitud según estado
                        if (vacationRequest && (isRequestPending || isRequestRejected)) {
                            displayTag = getVacationEventTag(vacationRequest);
                            
                            // Mostrar turno base como referencia
                            if (baseEvent) {
                                baseInfoSpan = <span className="base-shift-overlay">
                                    {getBaseEventTag(baseEvent)}
                                </span>;
                            }
                            
                            if (isRequestPending) itemClassName += " vacation-status-pending";
                            if (isRequestRejected) itemClassName += " vacation-status-rejected";
                            
                            // Botones de acción
                            const canEdit = isOwnRequest && isRequestPending;
                            const canDelete = (isOwnRequest || canCurrentUserManage) && isRequestPending;
                            const canApprove = canCurrentUserManage && isRequestPending;

                            if (canEdit || canDelete || canApprove) {
                                actionButtons = (
                                    <div className="vacation-list-item-actions">
                                        <Space size={2}>
                                            {canEdit && (
                                                <Button 
                                                    type="text" 
                                                    size="small" 
                                                    icon={<EditOutlined style={{ fontSize: '10px' }} />}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleOpenRequestModal('edit', vacationRequest);
                                                    }}
                                                    style={{ padding: '0 2px', height: '20px' }}
                                                />
                                            )}
                                            {canApprove && (
                                                <>
                                                    <Button 
                                                        type="text" 
                                                        size="small" 
                                                        icon={<CheckOutlined style={{ fontSize: '10px', color: 'green' }} />}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleOpenApprovalModal(vacationRequest, 'Aprobado');
                                                        }}
                                                        style={{ padding: '0 2px', height: '20px' }}
                                                    />
                                                    <Button 
                                                        type="text" 
                                                        size="small" 
                                                        icon={<CloseOutlined style={{ fontSize: '10px', color: 'red' }} />}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleOpenApprovalModal(vacationRequest, 'Rechazado');
                                                        }}
                                                        style={{ padding: '0 2px', height: '20px' }}
                                                    />
                                                </>
                                            )}
                                            {canDelete && (
                                                <Popconfirm
                                                    title="¿Eliminar solicitud?"
                                                    onConfirm={(e) => {
                                                        e?.stopPropagation();
                                                        handleDeleteVacation(vacationRequest.id);
                                                    }}
                                                    okText="Sí"
                                                    cancelText="No"
                                                >
                                                    <Button 
                                                        type="text" 
                                                        size="small" 
                                                        icon={<DeleteOutlined style={{ fontSize: '10px', color: 'red' }} />}
                                                        onClick={(e) => e.stopPropagation()}
                                                        style={{ padding: '0 2px', height: '20px' }}
                                                    />
                                                </Popconfirm>
                                            )}
                                        </Space>
                                    </div>
                                );
                            }
                        }
                        else if (vacationRequest && isRequestApproved) {
                            displayTag = getVacationEventTag(vacationRequest);
                            itemClassName += " vacation-status-approved";
                        }
                        else if (baseEvent) {
                            displayTag = getBaseEventTag(baseEvent);
                        }
                        else {
                            return null;
                        }

                        return (
                            <li key={`${user.id || user.username}-${dateStr}`} className={itemClassName}>
                                <span style={{ display: 'flex', alignItems: 'center', fontSize: '11px' }}>
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
    }, [baseCalendarData, vacationRequestsData, users, currentUser, hasManagementPermission]);
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
            <div style={{ padding: '8px 12px' }}>
                <Row justify="space-between" align="middle" gutter={8}>
                    <Col>
                        <Space>
                            <Button 
                                type="primary" 
                                icon={<PlusOutlined />}
                                onClick={() => handleOpenRequestModal('add', null, selectedDate)}
                                disabled={!currentUser}
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
                            
                            {hasManagementPermission && globalPendingRequests.length > 0 && (
                                <Button 
                                    type="default"
                                    danger
                                    size="small"
                                    icon={<InfoCircleOutlined />}
                                    onClick={() => setIsPendingPanelVisible(!isPendingPanelVisible)}
                                    style={{ 
                                        backgroundColor: '#fff2e8',
                                        borderColor: '#ffbb96',
                                        color: '#d46b08'
                                    }}
                                >
                                    {isPendingPanelVisible ? 'Ocultar' : `Ver ${globalPendingRequests.length} Pendientes`}
                                </Button>
                            )}
                        </Space>
                    </Col>
                    
                    <Col>
                        <Space>
                            <Text style={{ fontSize: '12px' }}>Mostrar días completos:</Text>
                            <Switch 
                                size="small" 
                                checked={showAllUsers} 
                                onChange={setShowAllUsers} 
                                checkedChildren="Sí" 
                                unCheckedChildren="No"
                            />
                            
                            <Select
                                size="small"
                                style={{ width: 80 }}
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
                            
                            <Button size="small" onClick={goToToday}>
                                Hoy
                            </Button>
                            
                            <Button 
                                size="small" 
                                icon={<ReloadOutlined />} 
                                onClick={reloadData}
                                loading={loadingBase || loadingRequests}
                            >
                                Recargar
                            </Button>
                        </Space>
                    </Col>
                </Row>
            </div>
        );
    }, [currentUser, hasPendingRequests, hasManagementPermission, globalPendingRequests.length, isPendingPanelVisible, showAllUsers, selectedDate, loadingBase, loadingRequests, fetchBaseCalendarData, fetchVacationRequestsData]);

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

    // --- Handlers para Modales y Acciones ---
    const handleDateSelect = (date, info) => {
        if (info.source === 'date') {
            handleOpenRequestModal('add', null, date);
        }
    };
    
    const handleOpenRequestModal = (mode = 'add', record = null, defaultDate = null) => {
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
        
        if (mode === 'edit' && record) {
            requestForm.setFieldsValue({
                user_id: record.user_id,
                dateRange: [dayjs.tz(record.start_date), dayjs.tz(record.end_date)],
                notes: record.notes || ''
            });
        } else {
            requestForm.resetFields();
            if (defaultDate) {
                requestForm.setFieldsValue({
                    dateRange: [defaultDate, defaultDate],
                    user_id: hasManagementPermission ? undefined : currentUser?.id
                });
            }
        }
        
        if (hasManagementPermission && usersForSelect.length === 0) {
            fetchUsersForSelect();
        }
        
        setIsRequestModalVisible(true);
    };

    const handleOpenApprovalModal = (record, action) => {
        if (!hasManagementPermission) {
            message.error("No tienes permiso para esta acción");
            return;
        }
        
        setSelectedRequestForApproval(record);
        approvalForm.setFieldsValue({
            status: action
        });
        setIsApprovalModalVisible(true);
    };
    
    const handleVacationSubmit = async (values) => {
        setIsSubmittingRequest(true);
        try {
            const userIdToSubmit = hasManagementPermission && values.user_id ? 
                values.user_id : currentUser?.id;
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
                message.info("La edición de solicitudes no está habilitada actualmente");
            } else {
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
    
    const handleVacationModalCancel = () => {
        setIsRequestModalVisible(false);
        setEditingRequestData(null);
        requestForm.resetFields();
    };
    
    const handleApprovalSubmit = async (values) => {
        setIsSubmittingApproval(true);
        try {
            if (!selectedRequestForApproval || !values.status) {
                throw new Error("Datos de aprobación incompletos");
            }
            
            const payload = {
                status: values.status,
                manager_notes: values.manager_notes || null
            };
            
            console.log("Enviando respuesta:", payload);
            const response = await fetchWithAuth(`/vacation-requests/${selectedRequestForApproval.id}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            console.log("Respuesta:", response);
            message.success(`Solicitud ${values.status.toLowerCase()} correctamente`);
            
            setIsApprovalModalVisible(false);
            setSelectedRequestForApproval(null);
            approvalForm.resetFields();
            
            const cy = selectedDate.year();
            const cm = selectedDate.month() + 1;
            fetchBaseCalendarData(cy, cm);
            fetchVacationRequestsData(cy, cm);
        } catch (errorInfo) {
            console.error('Error procesando aprobación:', errorInfo);
            if (errorInfo instanceof Error) {
                message.error(`Error: ${errorInfo.message}`);
            } else {
                message.error('Por favor revise los campos del formulario');
            }
        } finally {
            setIsSubmittingApproval(false);
        }
    };
    
    const handleApprovalModalCancel = () => {
        setIsApprovalModalVisible(false);
        setSelectedRequestForApproval(null);
        approvalForm.resetFields();
    };
    
    const handleDeleteVacation = async (requestId) => {
        const requestToDelete = findRequestInCalendarData(requestId);
        
        if (!requestToDelete) {
            message.error("Solicitud no encontrada");
            return;
        }
        
        const canDelete = hasManagementPermission || 
            (currentUser?.id === requestToDelete.user_id && requestToDelete.status === 'Solicitado');
            
        if (!canDelete) {
            message.error("No tienes permiso para eliminar esta solicitud");
            return;
        }
        
        if (requestToDelete.status !== 'Solicitado') {
            message.warning("Solo se pueden eliminar solicitudes pendientes");
            return;
        }
        
        try {
            await fetchWithAuth(`/vacation-requests/${requestId}`, {
                method: 'DELETE'
            });
            
            message.success('Solicitud eliminada correctamente');
            
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
            for (const username in dayData) {
                const request = dayData[username];
                if (request && request.id === requestId) {
                    return request;
                }
            }
        }
        return null;
    };

    // --- Renderizado Principal ---
    if (error) {
        return (
            <div className="page-container">
                <style>{calendarCustomStyles}</style>
                <Title level={2} className="page-title">Calendario de Vacaciones</Title>
                <Alert message="Error al cargar datos" description={error} type="error" showIcon />
                <Button 
                    style={{ marginTop: 16 }} 
                    onClick={() => window.location.reload()}
                >
                    Recargar Página
                </Button>
            </div>
        );
    }

    const combinedLoading = loadingBase || loadingRequests || loadingUsersSelect;

    return (
        <div className="page-container">
            <style>{calendarCustomStyles}</style>
            <Title level={2} className="page-title">Calendario de Vacaciones</Title>
            
            <Spin spinning={combinedLoading} tip="Cargando calendario...">
                <Card className="table-container" bordered={false}>
                    <Calendar 
                        locale={locale} 
                        dateCellRender={dateCellRender} 
                        headerRender={headerRender} 
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
                                .filter(([key]) => !['override', 'absence', 'shift', 'error', 'no_assignment'].includes(key))
                                .map(([code, color]) => {
                                    const text = shiftCodeNames[code] || absenceTypeNames[code] || code;
                                    return (
                                        <Tag 
                                            icon={shiftIcons[code]} 
                                            color={color} 
                                            key={code}
                                        >
                                            {code} - {text}
                                        </Tag>
                                    );
                                })}
                        </Space>
                    </Card>
                </Col>
            </Row>

            {/* Modal para nueva solicitud de vacaciones */}
            <Modal 
                title={`${requestModalMode === 'edit' ? 'Editar' : 'Nueva'} Solicitud de Vacaciones`} 
                open={isRequestModalVisible} 
                onOk={requestForm.submit} 
                onCancel={handleVacationModalCancel} 
                confirmLoading={isSubmittingRequest} 
                destroyOnClose 
                okText={requestModalMode === 'edit' ? 'Actualizar' : 'Solicitar'} 
                cancelText="Cancelar" 
                width={500}
            >
                <Spin spinning={loadingUsersSelect}>
                    <Form form={requestForm} layout="vertical" onFinish={handleVacationSubmit} name="vacation_form">
                        {hasManagementPermission ? (
                            <Form.Item 
                                name="user_id" 
                                label="Usuario" 
                                rules={[{ required: true, message: 'Selecciona un usuario' }]}
                            >
                                <Select 
                                    placeholder="Seleccionar usuario" 
                                    showSearch 
                                    filterOption={(input, option) => 
                                        option.children.toLowerCase().includes(input.toLowerCase())
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
                onOk={approvalForm.submit} 
                onCancel={handleApprovalModalCancel} 
                confirmLoading={isSubmittingApproval} 
                destroyOnClose 
                okText={approvalForm.getFieldValue('status')} 
                cancelText="Cancelar" 
                width={500}
            >
                <Form form={approvalForm} layout="vertical" onFinish={handleApprovalSubmit} name="approval_form">
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

            {/* Panel de solicitudes pendientes globales */}
            <PendingRequestsPanel 
                isVisible={isPendingPanelVisible}
                onClose={() => setIsPendingPanelVisible(false)}
                onNavigateToMonth={navigateToMonth}
                globalPendingRequests={globalPendingRequests}
            />
        </div>
    );
};

export default CalendarioVacaciones;