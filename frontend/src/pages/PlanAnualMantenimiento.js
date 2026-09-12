import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Card, Typography, Spin, Alert, Button, Tag, Tooltip, Row, Col, Space, 
  Modal, Calendar, List, Avatar, Badge, Drawer, message 
} from 'antd';
import { 
  CalendarOutlined, LeftOutlined, RightOutlined, EditOutlined, EyeOutlined,
  ToolOutlined, CheckCircleOutlined, ClockCircleOutlined, ArrowLeftOutlined,
  SettingOutlined, FileExcelOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import '../styles/CommonPage.css';
import '../styles/PlanAnual.css';
import * as XLSX from 'xlsx';

dayjs.locale('es');

const { Title, Text } = Typography;

// --- Componente Leyenda de Colores ---
const Legend = () => (
  <Space wrap style={{ 
    marginTop: '16px', 
    padding: '12px', 
    background: '#fafafa', 
    borderRadius: '8px', 
    width: '100%', 
    justifyContent: 'center',
    border: '1px solid #d9d9d9'
  }}>
    <Text strong style={{ marginRight: '16px' }}>Leyenda:</Text>
    <Tag color="#d9f7be" style={{ margin: '2px' }}>
      <ClockCircleOutlined /> 1 Tarea Programada
    </Tag>
    <Tag color="#b7eb8f" style={{ margin: '2px' }}>
      <ClockCircleOutlined /> 2 Tareas Programadas
    </Tag>
    <Tag color="#73d13d" style={{ margin: '2px' }}>
      <ClockCircleOutlined /> 3+ Tareas Programadas
    </Tag>
    <Tag color="#52c41a" style={{ margin: '2px' }}>
      <CheckCircleOutlined /> Realizado
    </Tag>
  </Space>
);

// --- Componente Vista Mensual Detallada ---
const MonthlyDetailView = ({ year, month, plans, onEventClick, visible, onClose }) => {
  const monthData = useMemo(() => {
    if (!plans || plans.length === 0) return [];
    
    const startOfMonth = dayjs().year(year).month(month).startOf('month');
    const endOfMonth = dayjs().year(year).month(month).endOf('month');
    
    return plans.filter(plan => {
      const planDate = dayjs(plan.scheduled_date);
      return planDate.isBetween(startOfMonth, endOfMonth, 'day', '[]');
    });
  }, [year, month, plans]);

  const eventsByDate = useMemo(() => {
    return monthData.reduce((acc, plan) => {
      const dateStr = dayjs(plan.scheduled_date).format('YYYY-MM-DD');
      if (!acc[dateStr]) acc[dateStr] = [];
      acc[dateStr].push(plan);
      return acc;
    }, {});
  }, [monthData]);

  const monthName = dayjs().year(year).month(month).format('MMMM YYYY');

  const dateCellRender = (date) => {
    const dateStr = date.format('YYYY-MM-DD');
    const dayEvents = eventsByDate[dateStr] || [];
    
    if (dayEvents.length === 0) return null;

    return (
      <div style={{ fontSize: '12px' }}>
        {dayEvents.map((event, index) => (
          <div 
            key={event.id}
            style={{
              backgroundColor: event.status === 'Realizado' ? '#52c41a' : '#1890ff',
              color: 'white',
              padding: '1px 4px',
              margin: '1px 0',
              borderRadius: '2px',
              cursor: 'pointer',
              fontSize: '10px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}
            onClick={(e) => {
              e.stopPropagation();
              onEventClick(event);
            }}
          >
            {event.status === 'Realizado' ? <CheckCircleOutlined /> : <ClockCircleOutlined />}
            {' '}{event.title.substring(0, 15)}...
          </div>
        ))}
      </div>
    );
  };

  return (
    <Drawer
      title={
        <Space>
          <CalendarOutlined />
          <Text strong>Calendario Mensual - {monthName}</Text>
        </Space>
      }
      width="90%"
      open={visible}
      onClose={onClose}
      extra={
        <Button onClick={onClose} icon={<ArrowLeftOutlined />}>
          Volver al Plan Anual
        </Button>
      }
    >
      <Row gutter={[16, 16]}>
        <Col span={16}>
          <Card title="Calendario del Mes" style={{ height: '600px' }}>
            <Calendar
              value={dayjs().year(year).month(month)}
              mode="month"
              fullscreen={false}
              dateCellRender={dateCellRender}
              headerRender={() => null}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card 
            title={
              <Space>
                <ToolOutlined />
                <Text>Mantenimientos del Mes ({monthData.length})</Text>
              </Space>
            }
            style={{ height: '600px', overflow: 'auto' }}
          >
            <List
              dataSource={monthData.sort((a, b) => dayjs(a.scheduled_date).diff(dayjs(b.scheduled_date)))}
              renderItem={(plan) => (
                <List.Item 
                  style={{ 
                    cursor: 'pointer',
                    borderRadius: '6px',
                    margin: '4px 0',
                    padding: '8px',
                    border: '1px solid #f0f0f0',
                    transition: 'all 0.2s'
                  }}
                  className="maintenance-item"
                  onClick={() => onEventClick(plan)}
                >
                  <List.Item.Meta
                    avatar={
                      <Avatar 
                        icon={plan.status === 'Realizado' ? <CheckCircleOutlined /> : <ClockCircleOutlined />}
                        style={{ 
                          backgroundColor: plan.status === 'Realizado' ? '#52c41a' : '#1890ff' 
                        }}
                      />
                    }
                    title={
                      <Space direction="vertical" size={2}>
                        <Text strong style={{ fontSize: '14px' }}>{plan.title}</Text>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {plan.maquina_nombre}
                        </Text>
                      </Space>
                    }
                    description={
                      <Space>
                        <Tag color={plan.status === 'Realizado' ? 'green' : 'blue'}>
                          {plan.status}
                        </Tag>
                        <Text style={{ fontSize: '12px' }}>
                          {dayjs(plan.scheduled_date).format('DD/MM/YYYY')}
                        </Text>
                      </Space>
                    }
                  />
                  <div style={{ fontSize: '12px', color: '#999' }}>
                    {plan.status === 'Realizado' ? 
                      <EyeOutlined title="Ver orden de trabajo" /> : 
                      <EditOutlined title="Editar mantenimiento" />
                    }
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
      
      <style jsx>{`
        .maintenance-item:hover {
          background-color: #f0f2f5 !important;
          transform: translateY(-1px);
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
      `}</style>
    </Drawer>
  );
};

// --- Componente para la vista anual "Heatmap" ---
const AnnualHeatmapView = ({ year, eventsByDay, onEventClick, onMonthClick }) => {
  const months = Array.from({ length: 12 }).map((_, i) => dayjs().year(year).month(i));

  const getDayClass = (events = []) => {
    if (events.length === 0) return 'heatmap-0';
    if (events.some(e => e.status === 'Realizado')) return 'heatmap-realizado';
    if (events.length === 1) return 'heatmap-1';
    if (events.length === 2) return 'heatmap-2';
    return 'heatmap-3'; // 3 o más
  };

  const getMonthStats = (monthIndex) => {
    const monthStart = dayjs().year(year).month(monthIndex).startOf('month');
    const monthEnd = dayjs().year(year).month(monthIndex).endOf('month');
    
    let programados = 0;
    let realizados = 0;
    
    Object.keys(eventsByDay).forEach(dateStr => {
      const date = dayjs(dateStr);
      if (date.isBetween(monthStart, monthEnd, 'day', '[]')) {
        eventsByDay[dateStr].forEach(event => {
          if (event.status === 'Realizado') realizados++;
          else programados++;
        });
      }
    });
    
    return { programados, realizados };
  };

  return (
    <Row gutter={[16, 16]}>
      {months.map((monthDate, monthIndex) => {
        const monthName = monthDate.format('MMMM');
        const daysInMonth = monthDate.daysInMonth();
        const firstDayOfMonth = monthDate.startOf('month').day();
        const startOffset = firstDayOfMonth === 0 ? 6 : firstDayOfMonth - 1;
        const dayCells = [...Array(startOffset).fill(null), ...Array.from({ length: daysInMonth }, (_, i) => i + 1)];
        const stats = getMonthStats(monthIndex);

        return (
          <Col xs={24} sm={12} md={8} lg={6} key={monthIndex}>
            <Badge.Ribbon 
              text={`${stats.realizados + stats.programados} tareas`}
              color={stats.realizados + stats.programados > 0 ? 'blue' : 'gray'}
            >
              <Card 
                title={
                  <Space>
                    <Text>{monthName.charAt(0).toUpperCase() + monthName.slice(1)}</Text>
                    <Button 
                      type="link" 
                      size="small" 
                      icon={<CalendarOutlined />}
                      onClick={() => onMonthClick(monthIndex)}
                      style={{ padding: 0 }}
                    >
                      Ver Detalle
                    </Button>
                  </Space>
                }
                size="small" 
                className="month-card heatmap-card"
                style={{ cursor: 'pointer' }}
                onClick={() => onMonthClick(monthIndex)}
              >
                <div className="calendar-grid">
                  {['L', 'M', 'X', 'J', 'V', 'S', 'D'].map(day => (
                    <div key={day} className="day-header">{day}</div>
                  ))}
                  {dayCells.map((day, index) => {
                    const dateStr = day ? dayjs().year(year).month(monthIndex).date(day).format('YYYY-MM-DD') : '';
                    const dayEvents = eventsByDay[dateStr] || [];
                    const dayClassName = getDayClass(dayEvents);
                    const firstEvent = dayEvents[0];
                    
                    const tooltipTitle = dayEvents.length > 0 
                      ? dayEvents.map(e => `${e.title} - ${e.maquina_nombre} (${e.status})`).join('\n')
                      : '';

                    return (
                      <Tooltip key={index} title={tooltipTitle}>
                        <div 
                          className={`day-cell ${dayClassName}`} 
                          onClick={firstEvent ? (e) => {
                            e.stopPropagation();
                            onEventClick(firstEvent);
                          } : null}
                        >
                          {day && <span className="day-number">{day}</span>}
                        </div>
                      </Tooltip>
                    );
                  })}
                </div>
                
                {/* Stats del mes */}
                <div style={{ marginTop: '8px', textAlign: 'center' }}>
                  <Space size={4}>
                    {stats.realizados > 0 && (
                      <Tag color="green" size="small">
                        <CheckCircleOutlined /> {stats.realizados}
                      </Tag>
                    )}
                    {stats.programados > 0 && (
                      <Tag color="blue" size="small">
                        <ClockCircleOutlined /> {stats.programados}
                      </Tag>
                    )}
                  </Space>
                </div>
              </Card>
            </Badge.Ribbon>
          </Col>
        );
      })}
    </Row>
  );
};

// --- Componente Principal ---
const PlanAnualMantenimiento = () => {
  const [year, setYear] = useState(dayjs().year());
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedMonth, setSelectedMonth] = useState(null);
  const [monthViewVisible, setMonthViewVisible] = useState(false);
  const [showDebug, setShowDebug] = useState(false);
  const navigate = useNavigate();

  const fetchAnnualPlan = useCallback(async (selectedYear) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWithAuth(`/plan-anual?year=${selectedYear}`);
      setPlans(data || []);
    } catch (err) { 
      setError('No se pudo cargar el plan anual de mantenimiento.');
    } finally { 
      setLoading(false); 
    }
  }, []);

  useEffect(() => { 
    fetchAnnualPlan(year); 
  }, [year, fetchAnnualPlan]);

  const eventsByDay = useMemo(() => {
    const grouped = plans.reduce((acc, plan) => {
      const dateStr = dayjs(plan.scheduled_date).format('YYYY-MM-DD');
      if (!acc[dateStr]) acc[dateStr] = [];
      acc[dateStr].push(plan);
      return acc;
    }, {});
    
    return grouped;
  }, [plans]);
  
  const handleEventClick = (event) => {
    if (event.status === 'Realizado' && event.work_order_id) {
      // Mantenimiento realizado - abrir orden de trabajo
      // Usar replace: true para evitar problemas de navegación
      navigate('/ordenes', { 
        state: { openOrderId: event.work_order_id },
        replace: true 
      });
    } else {
      // Mantenimiento programado - editar plan
      navigate('/mantenimiento/preventivo', { 
        state: { editPlanId: event.id },
        replace: true 
      });
    }
  };

  const handleMonthClick = (monthIndex) => {
    setSelectedMonth(monthIndex);
    setMonthViewVisible(true);
  };

  // ⭐ FUNCIÓN PARA EXPORTAR A EXCEL - NUEVA IMPLEMENTACIÓN
  const exportToExcel = () => {
    try {
      message.loading({ content: 'Generando archivo Excel del Plan Anual...', key: 'exportExcel' });

      // Formatear fecha para exportación
      const formatDateForExport = (dateString) => {
        if (!dateString) return '';
        try {
          return dayjs(dateString).format('DD/MM/YYYY');
        } catch (e) {
          return dateString;
        }
      };

      // Preparar datos para exportación
      const dataForExport = plans.map((plan, index) => ({
        'Nº': index + 1,
        'ID Plan': plan.id,
        'Título del Mantenimiento': plan.title || 'Sin título',
        'Máquina/Equipo': plan.maquina_nombre || 'Sin especificar',
        'ID Máquina': plan.machine_id || 'N/A',
        'Fecha Programada': formatDateForExport(plan.scheduled_date),
        'Estado': plan.status || 'Desconocido',
        'Orden de Trabajo ID': plan.work_order_id || 'No generada',
        'Mes': dayjs(plan.scheduled_date).format('MMMM'),
        'Trimestre': `Q${Math.ceil((dayjs(plan.scheduled_date).month() + 1) / 3)}`,
        'Semana del Año': dayjs(plan.scheduled_date).week(),
        'Día de la Semana': dayjs(plan.scheduled_date).format('dddd'),
        'Es Realizado': plan.status === 'Realizado' ? 'Sí' : 'No',
        'Año': year
      }));

      // Crear hoja de trabajo
      const worksheet = XLSX.utils.json_to_sheet(dataForExport);

      // Configurar anchos de columnas
      const columnWidths = [
        { wch: 5 },   // Nº
        { wch: 10 },  // ID Plan
        { wch: 35 },  // Título
        { wch: 25 },  // Máquina
        { wch: 12 },  // ID Máquina
        { wch: 15 },  // Fecha Programada
        { wch: 12 },  // Estado
        { wch: 15 },  // Orden de Trabajo ID
        { wch: 12 },  // Mes
        { wch: 10 },  // Trimestre
        { wch: 12 },  // Semana del Año
        { wch: 15 },  // Día de la Semana
        { wch: 12 },  // Es Realizado
        { wch: 8 }    // Año
      ];
      worksheet['!cols'] = columnWidths;

      // Crear resumen estadístico en una segunda hoja
      const stats = plans.reduce((acc, plan) => {
        const month = dayjs(plan.scheduled_date).format('MMMM');
        const status = plan.status;
        
        if (!acc[month]) {
          acc[month] = { Programado: 0, Realizado: 0, Total: 0 };
        }
        
        acc[month][status] = (acc[month][status] || 0) + 1;
        acc[month].Total += 1;
        
        return acc;
      }, {});

      const statsData = Object.keys(stats).map(month => ({
        'Mes': month,
        'Programados': stats[month].Programado || 0,
        'Realizados': stats[month].Realizado || 0,
        'Total': stats[month].Total,
        'Porcentaje Completado': stats[month].Total > 0 
          ? `${Math.round((stats[month].Realizado || 0) / stats[month].Total * 100)}%` 
          : '0%'
      }));

      const statsWorksheet = XLSX.utils.json_to_sheet(statsData);
      statsWorksheet['!cols'] = [
        { wch: 15 }, // Mes
        { wch: 12 }, // Programados
        { wch: 12 }, // Realizados
        { wch: 10 }, // Total
        { wch: 18 }  // Porcentaje
      ];

      // Crear libro de trabajo con múltiples hojas
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "Plan Anual Detallado");
      XLSX.utils.book_append_sheet(workbook, statsWorksheet, "Resumen por Mes");

      // Crear hoja de información general
      const infoData = [
        { 'Campo': 'Año del Plan', 'Valor': year },
        { 'Campo': 'Total Mantenimientos', 'Valor': plans.length },
        { 'Campo': 'Mantenimientos Realizados', 'Valor': plans.filter(p => p.status === 'Realizado').length },
        { 'Campo': 'Mantenimientos Programados', 'Valor': plans.filter(p => p.status === 'Programado').length },
        { 'Campo': 'Porcentaje de Cumplimiento', 'Valor': plans.length > 0 ? `${Math.round(plans.filter(p => p.status === 'Realizado').length / plans.length * 100)}%` : '0%' },
        { 'Campo': 'Fecha de Exportación', 'Valor': dayjs().format('DD/MM/YYYY HH:mm:ss') },
        { 'Campo': 'Máquinas Involucradas', 'Valor': [...new Set(plans.map(p => p.maquina_nombre))].length }
      ];

      const infoWorksheet = XLSX.utils.json_to_sheet(infoData);
      infoWorksheet['!cols'] = [{ wch: 25 }, { wch: 20 }];
      XLSX.utils.book_append_sheet(workbook, infoWorksheet, "Información General");

      // Guardar archivo
      const fileName = `Plan_Anual_Mantenimiento_${year}_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`;
      XLSX.writeFile(workbook, fileName);

      message.success({ 
        content: `Plan anual exportado correctamente: ${fileName}`, 
        key: 'exportExcel', 
        duration: 4 
      });

    } catch (error) {
      console.error("Error al generar Excel:", error);
      message.error({ 
        content: 'Error al generar el archivo Excel del plan anual.', 
        key: 'exportExcel', 
        duration: 3 
      });
    }
  };

  const stats = useMemo(() => {
    const realizados = plans.filter(p => p.status === 'Realizado').length;
    const programados = plans.filter(p => p.status === 'Programado').length;
    return { realizados, programados, total: realizados + programados };
  }, [plans]);

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header" style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        background: 'white',
        padding: '16px 24px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '24px'
      }}>
        <div>
          <Title level={2} className="page-title" style={{ margin: 0 }}>
            <CalendarOutlined style={{ marginRight: '12px' }} />
            Plan de Mantenimiento Anual
          </Title>
          <Text type="secondary">
            Gestión y visualización del calendario anual de mantenimientos
          </Text>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* ⭐ BOTÓN DE EXPORTAR EXCEL - NUEVA IMPLEMENTACIÓN */}
          <Button
            icon={<FileExcelOutlined />}
            onClick={exportToExcel}
            disabled={loading || plans.length === 0}
            type="default"
            style={{ 
              backgroundColor: '#52c41a', 
              borderColor: '#52c41a', 
              color: 'white' 
            }}
          >
            Exportar Excel
          </Button>
          
          {/* Estadísticas */}
          <Space size="large">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                {stats.realizados}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Realizados</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                {stats.programados}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Programados</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#722ed1' }}>
                {stats.total}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Total</div>
            </div>
            
            {/* Botón para mostrar debug info */}
            <Button 
              size="small" 
              type="dashed" 
              onClick={() => setShowDebug(!showDebug)}
            >
              {showDebug ? 'Ocultar' : 'Debug'}
            </Button>
          </Space>
          
          {/* Selector de año */}
          <div className="year-selector">
            <Button 
              icon={<LeftOutlined />} 
              onClick={() => setYear(y => y - 1)}
              type="text"
            />
            <Title level={3} style={{ margin: 0, minWidth: '80px', textAlign: 'center' }}>
              {year}
            </Title>
            <Button 
              icon={<RightOutlined />} 
              onClick={() => setYear(y => y + 1)}
              type="text"
            />
          </div>
        </div>
      </div>

      {/* Debug Info */}
      {showDebug && (
        <Alert 
          message="Información de Debug" 
          description={
            <div style={{ fontSize: '12px', fontFamily: 'monospace' }}>
              <strong>Total planes cargados:</strong> {plans.length}<br/>
              <strong>Realizados:</strong> {plans.filter(p => p.status === 'Realizado').length}<br/>
              <strong>Programados:</strong> {plans.filter(p => p.status === 'Programado').length}<br/>
              <strong>Primeros 3 items:</strong><br/>
              {plans.slice(0, 3).map((plan, idx) => (
                <div key={idx} style={{ marginLeft: '10px', fontSize: '11px' }}>
                  {idx + 1}. {plan.title} - {plan.status} - WO: {plan.work_order_id || 'N/A'} - Fecha: {plan.scheduled_date}
                </div>
              ))}
            </div>
          }
          type="info"
          style={{ marginBottom: '16px' }}
          closable
          onClose={() => setShowDebug(false)}
        />
      )}

      {/* Leyenda */}
      <Legend />

      {/* Contenido principal */}
      <div style={{ marginTop: '24px' }}>
        {loading && (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '16px' }}>Cargando plan anual...</div>
          </div>
        )}
        
        {error && (
          <Alert 
            message="Error al cargar datos"
            description={error}
            type="error" 
            showIcon 
            style={{ marginBottom: '24px' }}
          />
        )}
        
        {!loading && !error && (
          <AnnualHeatmapView 
            year={year} 
            eventsByDay={eventsByDay} 
            onEventClick={handleEventClick}
            onMonthClick={handleMonthClick}
          />
        )}
      </div>

      {/* Vista mensual detallada */}
      <MonthlyDetailView
        year={year}
        month={selectedMonth}
        plans={plans}
        onEventClick={handleEventClick}
        visible={monthViewVisible}
        onClose={() => setMonthViewVisible(false)}
      />
    </div>
  );
};

export default PlanAnualMantenimiento;