// src/pages/CalendarioTurnos.js (COMPLETO con Modal para Añadir Ausencias)
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom'; // Importar hooks necesarios
import {
    Calendar, Select, Typography, Spin, Alert, message, Col, Row, Card, Tag, Button, Space,
    Modal, Form, Input, InputNumber, DatePicker, Popconfirm, Tooltip // Asegurar imports completos
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ArrowLeftOutlined, FileExcelOutlined } from '@ant-design/icons'; // Iconos necesarios
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import locale from 'antd/es/date-picker/locale/es_ES';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext'; // Importar useAuth
import '../styles/CommonPage.css';

dayjs.locale('es');

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;
const { RangePicker } = DatePicker; // Importar RangePicker

// Colores para los códigos (igual que antes)
const shiftColors = { 'M':'geekblue', 'T':'green', 'N':'purple', 'P':'cyan', 'L':'default', 'V':'gold', 'B':'red', 'A':'orange', 'F':'magenta', '?':'error' };
const getShiftColor = (code) => shiftColors[code] || 'default';

const CalendarioTurnos = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [calendarData, setCalendarData] = useState({});
    const [selectedDate, setSelectedDate] = useState(dayjs());
    const { currentUser } = useAuth(); // Obtener usuario actual para permisos futuros?

    // --- NUEVOS ESTADOS PARA MODAL AUSENCIAS ---
    const [isAbsenceModalVisible, setIsAbsenceModalVisible] = useState(false);
    const [selectedAbsenceDate, setSelectedAbsenceDate] = useState(null); // Guarda la fecha dayjs clicada
    const [usersForSelect, setUsersForSelect] = useState([]); // Lista de usuarios para el Select
    const [loadingUsers, setLoadingUsers] = useState(false); // Loading para la lista de usuarios
    const [absenceForm] = Form.useForm(); // Formulario para el modal de ausencia
    const [isSubmittingAbsence, setIsSubmittingAbsence] = useState(false);
    // ------------------------------------------

    // Función para cargar datos del calendario (sin cambios)
    const fetchCalendarData = useCallback(async (year, month) => {
        setLoading(true); setError(null); console.log(`Workspaceing calendar data for ${year}-${month}`);
        try { const url = `/calendar-data?year=${year}&month=${month}`; console.log(`Requesting URL: ${url}`); const data = await fetchWithAuth(url); setCalendarData(data || {}); console.log(`Calendar data received for ${year}-${month}:`, data); }
        catch (err) { console.error("Error fetching calendar data:", err); const errorMsg = `Error al cargar datos: ${err.message || 'Desconocido'}`; setError(errorMsg); message.error(errorMsg); setCalendarData({}); }
        finally { setLoading(false); }
    }, []);

    // --- NUEVA FUNCIÓN PARA CARGAR USUARIOS ---
    const fetchUsersForSelect = useCallback(async () => {
        if (usersForSelect.length > 0) return;
        setLoadingUsers(true); console.log("Fetching users for absence modal select...");
        try { const usersData = await fetchWithAuth('/users'); setUsersForSelect(usersData || []); }
        catch (err) { console.error("Error fetching users:", err); message.error(`Error cargando usuarios: ${err.message || 'Desconocido'}`); }
        finally { setLoadingUsers(false); }
    }, [usersForSelect.length]);
    // ----------------------------------------

    // useEffect principal
    useEffect(() => {
        fetchCalendarData(selectedDate.year(), selectedDate.month() + 1);
        // Cargar usuarios solo una vez o si la lista está vacía
        if (usersForSelect.length === 0) {
            fetchUsersForSelect();
        }
    }, [selectedDate, fetchCalendarData, fetchUsersForSelect, usersForSelect.length]); // Dependencias actualizadas

    // Renderizado de Celdas (sin cambios)
    const dateCellRender = useCallback((value) => {
        const dateStr = value.format('YYYY-MM-DD'); const dailyShifts = calendarData[dateStr];
        if (!dailyShifts || Object.keys(dailyShifts).length === 0) return null;
        const shiftEntries = Object.entries(dailyShifts).sort((a, b) => a[0].localeCompare(b[0]));
        return ( <ul style={{ margin: 0, padding: 0, listStyle: 'none', lineHeight: '1.2' }}> {shiftEntries.map(([username, shiftCode]) => ( <li key={username} style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: '11px', marginTop: '2px' }}> <Tag color={getShiftColor(shiftCode)} style={{ marginRight: 3 }}>{shiftCode || '?'}</Tag>{username}</li> ))} </ul> );
    }, [calendarData]);

    // Cabecera Personalizada (sin cambios)
    const headerRender = useCallback(({ value, onChange }) => { /* ... (igual que antes) ... */
        const current = value.clone(); const year = current.year(); const month = current.month();
        const monthOptions = []; const localeData = dayjs.localeData();
        for (let i = 0; i < 12; i++) { const monthName = current.month(i).format('MMMM'); monthOptions.push(<Option key={i} value={i}>{monthName.charAt(0).toUpperCase() + monthName.slice(1)}</Option> ); }
        const yearOptions = []; for (let i = year - 5; i < year + 6; i += 1) { yearOptions.push( <Option key={i} value={i}>{i}</Option> ); }
        return ( <div style={{ padding: '8px 12px' }}> <Row justify="space-between" align="middle" gutter={8}> <Col><Title level={4} style={{ margin: 0 }}>{value.format('MMMM YYYY').charAt(0).toUpperCase() + value.format('MMMM YYYY').slice(1)}</Title></Col> <Col><Space> <Select size="small" style={{ width: 80 }} value={year} onChange={(newYear) => { const now = current.year(newYear); onChange(now); setSelectedDate(now); }}>{yearOptions}</Select> <Select size="small" style={{ width: 120 }} value={month} onChange={(newMonth) => { const now = current.month(newMonth); onChange(now); setSelectedDate(now); }}>{monthOptions}</Select> <Button size="small" onClick={() => { const now = dayjs(); onChange(now); setSelectedDate(now); }}>Hoy</Button> </Space></Col> </Row> </div> );
    }, []);

    // --- NUEVOS HANDLERS PARA MODAL AUSENCIAS ---
     const handleDateSelect = (date) => {
         console.log("Date selected for absence:", date.format("YYYY-MM-DD"));
         setSelectedAbsenceDate(date);
         absenceForm.resetFields();
         absenceForm.setFieldsValue({ dateRange: [date, date] }); // Preseleccionar rango con el día clicado
         // Cargar usuarios si no están cargados ya (redundante si se hizo en useEffect, pero seguro)
         if(usersForSelect.length === 0) { fetchUsersForSelect(); }
         setIsAbsenceModalVisible(true);
     };

     const handleAbsenceModalSubmit = async () => {
         setIsSubmittingAbsence(true);
         try {
             const values = await absenceForm.validateFields();
             // Validar que dateRange tiene dos valores
             if (!values.dateRange || values.dateRange.length !== 2) {
                throw new Error("Selecciona un rango de fechas válido.");
             }
             const payload = {
                 user_id: values.user_id,
                 absence_type: values.absence_type,
                 start_date: values.dateRange[0].format('YYYY-MM-DD'), // Formatear
                 end_date: values.dateRange[1].format('YYYY-MM-DD'),   // Formatear
                 notes: values.notes || null
             };
             console.log("Enviando datos de ausencia:", payload);
             await fetchWithAuth('/absences', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
             });
             message.success('Ausencia registrada correctamente.');
             setIsAbsenceModalVisible(false);
             // Recargar datos del calendario para reflejar la ausencia
             fetchCalendarData(selectedDate.year(), selectedDate.month() + 1);
         } catch (errorInfo) {
             console.error('Error registrando ausencia:', errorInfo);
             if (errorInfo instanceof Error) { message.error(`Error: ${errorInfo.message}`); }
             else { message.error('Revise los campos del formulario.'); }
         } finally {
             setIsSubmittingAbsence(false);
         }
     };

     const handleAbsenceModalCancel = () => {
         setIsAbsenceModalVisible(false);
         setSelectedAbsenceDate(null);
         absenceForm.resetFields();
     };
    // --- FIN HANDLERS AUSENCIAS ---

    return (
      <div className="page-container">
         <Title level={2} className="page-title">Calendario de Turnos</Title>
         {error && <Alert message="Error" description={error} type="error" showIcon closable onClose={() => setError(null)} style={{ marginBottom: 16 }} />}
         <Spin spinning={loading}>
             <Card className="table-container">
                 <Calendar
                     locale={locale}
                     dateCellRender={dateCellRender}
                     headerRender={headerRender}
                     onSelect={handleDateSelect} // <-- AÑADIDO: Llama a handleDateSelect al clicar día
                     onPanelChange={(date, mode) => { if (mode === 'month' && !date.isSame(selectedDate, 'month')) { setSelectedDate(date); } }}
                 />
             </Card>
         </Spin>
         <Card size="small" title="Leyenda" style={{ marginTop: 16 }}>
            <Space wrap> {Object.entries(shiftColors).map(([code, color]) => ( <Tag color={color} key={code}>{code}: { {M:'Mañana', T:'Tarde', N:'Noche', P:'Partido', L:'Libre', V:'Vacaciones', B:'Baja', A:'As.Propios', F:'Festivo', '?':'Error'}[code] || 'Otro' }</Tag> ))} </Space>
         </Card>

         {/* --- AÑADIDO: MODAL PARA REGISTRAR AUSENCIA --- */}
         <Modal
           title={`Registrar Ausencia para: ${selectedAbsenceDate ? selectedAbsenceDate.format('dddd, D [de] MMMM') : ''}`}
           open={isAbsenceModalVisible}
           onOk={handleAbsenceModalSubmit}
           onCancel={handleAbsenceModalCancel}
           confirmLoading={isSubmittingAbsence}
           destroyOnClose
           okText="Guardar Ausencia"
           cancelText="Cancelar"
           width={600}
         >
              <Spin spinning={loadingUsers}>
                  <Form form={absenceForm} layout="vertical" name="absence_form">
                      <Form.Item name="user_id" label="Usuario" rules={[{ required: true, message: 'Selecciona el usuario' }]}>
                          <Select showSearch placeholder="Selecciona un usuario" optionFilterProp="children" filterOption={(input, option) => (option?.children ?? '').toLowerCase().includes(input.toLowerCase())} loading={loadingUsers}>
                              {usersForSelect.map(user => ( <Option key={user.id} value={user.id}>{user.username}</Option> ))}
                          </Select>
                      </Form.Item>
                      <Form.Item name="absence_type" label="Tipo de Ausencia" rules={[{ required: true, message: 'Selecciona el tipo' }]}>
                          <Select placeholder="Selecciona tipo">
                              <Option value="V">V - Vacaciones</Option>
                              <Option value="B">B - Baja Médica</Option>
                              <Option value="A">A - Asuntos Propios</Option>
                              <Option value="F">F - Festivo (Asignado)</Option>
                          </Select>
                      </Form.Item>
                      <Form.Item name="dateRange" label="Fechas (Inicio - Fin, ambos incluidos)" rules={[{ required: true, message: 'Selecciona el rango de fechas' }]}>
                           <RangePicker format="YYYY-MM-DD" style={{ width: '100%' }} />
                      </Form.Item>
                      <Form.Item name="notes" label="Notas (Opcional)">
                           <TextArea rows={2} />
                      </Form.Item>
                  </Form>
              </Spin>
         </Modal>
         {/* --- FIN MODAL AUSENCIA --- */}

      </div>
    );
};

export default CalendarioTurnos;