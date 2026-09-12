// src/pages/ShiftPatternManagement.js
import React, { useState, useEffect, useCallback } from 'react';
import {
    Table, Button, Modal, Form, Input, message, Space, Spin,
    Alert, Typography, Popconfirm, Card, Tooltip // Añadidos Tooltip, Card
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, FileExcelOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import * as XLSX from 'xlsx';
import '../styles/CommonPage.css'; // O tu CSS común

const { Title } = Typography;
const { TextArea } = Input;

const ShiftPatternManagement = () => {
  const [patterns, setPatterns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null); // null para añadir, objeto para editar
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form] = Form.useForm();
  const { currentUser } = useAuth();

  // Permisos - Asume que solo Admin/Jefe Mant pueden gestionar patrones
  const canManage = currentUser?.role === "Administrador" || currentUser?.role === "Jefe de Mantenimiento";

  // Carga de datos
  const loadPatterns = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWithAuth('/shift-patterns'); // Usa el endpoint que devuelve lista básica
      setPatterns((data || []).map(p => ({ ...p, key: p.id })));
    } catch (err) {
      console.error("Error fetching shift patterns:", err);
      setError(`Error al cargar patrones: ${err.message || 'Desconocido'}`);
      message.error(`Error al cargar patrones: ${err.message || 'Desconocido'}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPatterns();
  }, [loadPatterns]);

  // Handlers para CRUD
  const handleAdd = () => {
    setEditingRecord(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (record) => {
    setEditingRecord(record);
    // Precargar formulario (los nombres de campo deben coincidir con los 'name' de Form.Item)
    form.setFieldsValue({
        name: record.name,
        description: record.description,
        pattern_sequence: record.pattern_sequence // Precargar secuencia
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (id) => {
     const patternToDelete = patterns.find(p => p.id === id);
     Modal.confirm({
          title: `¿Eliminar Patrón "${patternToDelete?.name || id}"?`,
          content: 'Asegúrate de que no esté asignado a ningún usuario. Esta acción no se puede deshacer.',
          okText: 'Sí, eliminar', okType: 'danger', cancelText: 'No',
          onOk: async () => {
              const loadingKey = `deletePattern-${id}`;
              message.loading({ content: `Eliminando patrón...`, key: loadingKey });
              try {
                  await fetchWithAuth(`/shift-patterns/${id}`, { method: 'DELETE' });
                  message.success({ content: 'Patrón eliminado.', key: loadingKey, duration: 2 });
                  loadPatterns(); // Recargar
              } catch (error) {
                  // El backend ya valida si está en uso y devuelve 400
                  message.error({ content: `Error: ${error.message || 'No se pudo eliminar'}`, key: loadingKey, duration: 4 });
                  console.error("Delete pattern error:", error);
              }
          },
     });
  };

  const handleModalSubmit = async () => {
     setIsSubmitting(true);
     try {
         const values = await form.validateFields();
         const method = editingRecord ? 'PUT' : 'POST';
         const url = editingRecord ? `/shift-patterns/${editingRecord.id}` : '/shift-patterns';

         const payload = { ...values };
         // Validar longitud de secuencia? Pydantic ya valida min_length=1
         if (!payload.pattern_sequence || payload.pattern_sequence.length === 0) {
             message.error("La secuencia del patrón no puede estar vacía.");
             setIsSubmitting(false);
             return;
         }

         console.log(`Enviando ${method} a ${url}`, payload);

         await fetchWithAuth(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
         message.success(`Patrón de Turno ${editingRecord ? 'actualizado' : 'creado'} correctamente.`);
         setIsModalVisible(false);
         loadPatterns();

     } catch (errorInfo) {
         console.error('Error guardando patrón:', errorInfo);
         if (errorInfo instanceof Error) { message.error(`Error: ${errorInfo.message}`); }
         else { message.error('Revise los campos del formulario.'); }
     } finally {
         setIsSubmitting(false);
     }
  };

  // --- Función Exportar ---
  const handleExportExcel = () => {
      if (patterns.length === 0) { message.warning("No hay patrones para exportar."); return; }
      message.loading({ content: 'Generando Excel...', key: 'exportExcelPatterns' });
      const dataToExport = patterns.map(p => ({
          'ID': p.id,
          'Nombre': p.name,
          'Descripción': p.description || '-',
          'Secuencia': p.pattern_sequence,
          'Longitud Ciclo (días)': p.cycle_length_days,
      }));
      try {
          const worksheet = XLSX.utils.json_to_sheet(dataToExport);
          const columnWidths = [ { wch: 8 }, { wch: 25 }, { wch: 40 }, { wch: 40 }, { wch: 15 } ];
          worksheet['!cols'] = columnWidths;
          const workbook = XLSX.utils.book_new();
          XLSX.utils.book_append_sheet(workbook, worksheet, "PatronesTurno");
          XLSX.writeFile(workbook, "Patrones_Turno.xlsx");
          message.success({ content: 'Exportación completada.', key: 'exportExcelPatterns', duration: 3 });
      } catch (error) {
          console.error("Error al generar Excel:", error);
          message.error({ content: 'Error al generar el archivo Excel.', key: 'exportExcelPatterns', duration: 3 });
      }
    };
  // ----------------------

  // --- Columnas Tabla ---
  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: 'Nombre Patrón', dataIndex: 'name', key: 'name', sorter: (a, b) => a.name.localeCompare(b.name) },
    { title: 'Descripción', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: 'Secuencia', dataIndex: 'pattern_sequence', key: 'pattern_sequence', ellipsis: true, render: (text) => <Tooltip title={text}><code>{text}</code></Tooltip> },
    { title: 'Longitud (días)', dataIndex: 'cycle_length_days', key: 'cycle_length_days', width: 120, align: 'center' },
    {
      title: 'Acciones', key: 'actions', width: 150, align: 'center',
      render: (_, record) => (
        <Space>
          <Button type="primary" icon={<EditOutlined />} onClick={() => handleEdit(record)} disabled={!canManage} size="small" title="Editar Patrón"/>
          <Popconfirm title={`¿Eliminar patrón "${record.name}"?`} onConfirm={() => handleDelete(record.id)} okText="Sí" cancelText="No" okType="danger" disabled={!canManage}>
             <Button type="primary" danger icon={<DeleteOutlined />} disabled={!canManage} size="small" title="Eliminar Patrón"/>
          </Popconfirm>
        </Space>
      ),
    },
  ];
  // --- Fin Columnas ---

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2} className="page-title" style={{ marginBottom: 0 }}>Gestión de Patrones de Turno</Title>
        <Space>
           <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd} disabled={!canManage}> Nuevo Patrón </Button>
           <Button icon={<FileExcelOutlined />} onClick={handleExportExcel} disabled={loading || patterns.length === 0} ghost> Exportar a Excel </Button>
        </Space>
      </div>

      {error && <Alert message="Error" description={error} type="error" showIcon closable onClose={() => setError(null)} style={{ marginBottom: 16 }} />}

      <Card className="table-container" style={{ marginTop: 16 }}>
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={patterns}
            rowKey="key"
            pagination={{ pageSize: 10, showSizeChanger: true }}
            locale={{ emptyText: loading ? 'Cargando...' : 'No hay patrones de turno creados.' }}
            size="small"
            bordered
          />
        </Spin>
      </Card>

      {/* --- Modal para Crear/Editar Patrón --- */}
      <Modal
        title={`${editingRecord ? 'Editar' : 'Nuevo'} Patrón de Turno`}
        open={isModalVisible}
        onOk={handleModalSubmit}
        onCancel={() => setIsModalVisible(false)}
        confirmLoading={isSubmitting}
        destroyOnClose
        maskClosable={false}
        okText={editingRecord ? 'Actualizar' : 'Crear'}
        cancelText="Cancelar"
        width={600} // Ajustar ancho si es necesario
      >
         <Form form={form} layout="vertical" name="shift_pattern_form">
            <Form.Item name="name" label="Nombre del Patrón" rules={[{ required: true, message: 'El nombre es obligatorio.' }]}>
                <Input placeholder="Ej: Rotativo 7x7, Partida L-V"/>
            </Form.Item>
            <Form.Item name="description" label="Descripción (Opcional)">
                <TextArea rows={2} />
            </Form.Item>
            <Form.Item
              name="pattern_sequence"
              label="Secuencia de Códigos"
              rules={[{ required: true, message: 'La secuencia es obligatoria (usar M, T, N, L, P, etc.)' }]}
              tooltip="Introduce la secuencia completa de códigos de turno para un ciclo (ej: MMMMMMMLLTTTTTTTLLNNNNNNNLLLLLLL)"
            >
                <Input placeholder="Ej: MMMMMMMLLTTTTTTTLLNNNNNNNLLLLLLL"/>
            </Form.Item>
         </Form>
       </Modal>
      {/* ---------------------------------- */}
    </div>
  );
};

export default ShiftPatternManagement;