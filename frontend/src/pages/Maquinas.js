// src/pages/Maquinas.js (Versión Responsive con Ordenamiento Alfabético y Paginación Corregida)
import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Button, Modal, Form, Input, Select, message, Typography, Space, Spin, Alert, Popconfirm, AutoComplete } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, UnorderedListOutlined, HistoryOutlined, FileExcelOutlined, SearchOutlined, EyeOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { fetchWithAuth } from '../apiConfig';
import * as XLSX from 'xlsx';
import '../styles/CommonPage.css';
import { useAuth } from '../contexts/AuthContext';
import MobileLayout from '../components/MobileLayout';

const { Title, Text } = Typography;
const { Option } = Select;

const Maquinas = () => {
  const [machines, setMachines] = useState([]);
  const [sections, setSections] = useState([]);
  const [filteredLines, setFilteredLines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form] = Form.useForm();
  const { currentUser } = useAuth();
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  // Estados para búsqueda y filtros
  const [searchText, setSearchText] = useState('');
  const [searchOptions, setSearchOptions] = useState([]);
  const [filteredMachines, setFilteredMachines] = useState([]);

  // 🔧 ESTADO PARA PAGINACIÓN
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    showSizeChanger: true,
    showQuickJumper: true,
    pageSizeOptions: ['10', '20', '30', '50', '100'],
    showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} máquinas`,
  });

  // Detectar tamaño de pantalla para modo responsivo
  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  // Determinar si estamos en modo móvil
  const isMobile = windowWidth < 768;

  // Verificación de permisos basados en rol
  const isMechanic = currentUser?.role === 'Mecánico';
  const canManageOrEdit = currentUser?.role === 'Administrador' || currentUser?.role === 'Jefe de Mantenimiento' || currentUser?.role === 'Jefe de Sección';

  // 🔧 FUNCIÓN PARA MANEJAR CAMBIOS EN LA PAGINACIÓN
  const handleTableChange = (pag, filters, sorter) => {
    console.log('Cambio en paginación máquinas:', pag);
    setPagination({
      ...pagination,
      current: pag.current,
      pageSize: pag.pageSize,
    });
  };

  // Función para manejar búsqueda con autocompletado
  const handleSearch = value => {
    setSearchText(value);
    
    // 🔧 RESETEAR PAGINACIÓN AL BUSCAR
    setPagination({
      ...pagination,
      current: 1
    });
    
    if (!value) {
      // Mantener orden alfabético cuando se limpia la búsqueda
      const sortedMachines = [...machines].sort((a, b) => 
        (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' })
      );
      setFilteredMachines(sortedMachines);
      setSearchOptions([]);
      return;
    }
    
    // Filtrar máquinas que coincidan con la búsqueda
    const matchingMachines = machines.filter(machine => 
      (machine.nombre?.toLowerCase().includes(value.toLowerCase()) || false) ||
      (machine.modelo?.toLowerCase().includes(value.toLowerCase()) || false) ||
      (machine.marca?.toLowerCase().includes(value.toLowerCase()) || false) ||
      (machine.numero_serie?.toLowerCase().includes(value.toLowerCase()) || false) ||
      (machine.criticidad?.toLowerCase().includes(value.toLowerCase()) || false)
    );
    
    // Ordenar alfabéticamente los resultados de búsqueda
    const sortedMatchingMachines = matchingMachines.sort((a, b) => 
      (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' })
    );
    
    setFilteredMachines(sortedMatchingMachines);
    
    // Generar opciones para autocompletado
    const options = sortedMatchingMachines.map(machine => ({
      value: machine.nombre,
      label: (
        <div>
          <strong>{machine.nombre}</strong> - {machine.modelo} ({machine.marca})
        </div>
      )
    }));
    
    setSearchOptions(options);
  };

  // --- Carga de Datos ---
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sectionsData, maquinasData] = await Promise.allSettled([
        fetchWithAuth('/secciones'),
        fetchWithAuth('/maquinas')
      ]);

      if (sectionsData.status === 'fulfilled') {
        setSections(sectionsData.value || []);
      } else {
        console.error("Error cargando secciones:", sectionsData.reason);
        throw new Error(`Error al cargar secciones: ${sectionsData.reason?.message || 'Desconocido'}`);
      }

      if (maquinasData.status === 'fulfilled') {
        // Añadir key para la tabla y ordenar alfabéticamente
        const machinesWithKeys = (maquinasData.value || []).map(m => ({ ...m, key: m.id }));
        const sortedMachines = machinesWithKeys.sort((a, b) => 
          (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' })
        );
        setMachines(sortedMachines);
        setFilteredMachines(sortedMachines); // Inicializar filteredMachines con todas las máquinas ordenadas
      } else {
        console.error("Error cargando máquinas:", maquinasData.reason);
        throw new Error(`Error al cargar máquinas: ${maquinasData.reason?.message || 'Desconocido'}`);
      }

    } catch (error) {
      message.error(error.message || 'Error al cargar los datos iniciales');
      setError(error.message || 'Error al cargar los datos iniciales');
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // --- Manejo del Modal ---
  const handleEdit = (record) => {
    if (!canManageOrEdit) return;
    setEditingRecord(record);
    form.setFieldsValue({ ...record });
    const section = sections.find(s => s.id === record.section_id);
    setFilteredLines(section?.lines || []);
    setModalVisible(true);
  };
  
  const handleAddNew = () => {
    if (!canManageOrEdit) return;
    setEditingRecord(null);
    form.resetFields();
    setFilteredLines([]);
    setModalVisible(true);
  };
  
  const handleCancel = () => {
    setModalVisible(false);
  };
  
  const handleSubmit = async () => {
    if (!canManageOrEdit) return;
    setIsSubmitting(true);
    try {
      const values = await form.validateFields();
      const payload = { ...values };
      const method = editingRecord ? 'PUT' : 'POST';
      const url = editingRecord ? `/maquinas/${editingRecord.id}` : '/maquinas';
      await fetchWithAuth(url, { 
        method, 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify(payload) 
      });
      message.success(`Máquina ${editingRecord ? 'actualizada' : 'creada'} correctamente`);
      setModalVisible(false);
      fetchData(); // Recargar datos
    } catch (errorInfo) {
      console.error("Error en submit:", errorInfo);
      if (errorInfo instanceof Error) {
        message.error(`Error: ${errorInfo.message}`);
      } else {
        message.error('Revise los campos del formulario.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const handleDelete = async (id) => {
    if (!canManageOrEdit) return;
    Modal.confirm({
      title: '¿Eliminar esta Máquina?',
      content: 'Esta acción no se puede deshacer. Asegúrese de que no tenga mantenimientos u órdenes asociadas.',
      okText: 'Sí, eliminar',
      okType: 'danger',
      cancelText: 'No',
      onOk: async () => {
        try {
          await fetchWithAuth(`/maquinas/${id}`, { method: 'DELETE' });
          message.success('Máquina eliminada correctamente');
          fetchData(); // Recargar datos
        } catch (error) {
          const errorMsg = error.detail || 'Error al eliminar. Verifique dependencias.';
          message.error(errorMsg);
          console.error("Delete error:", error);
        }
      },
    });
  };
  
  const handleSectionChange = (sectionId) => {
    form.setFieldsValue({ line_id: undefined });
    const section = sections.find(s => s.id === sectionId);
    setFilteredLines(section?.lines || []);
  };

  // --- Exportar a Excel ---
  const handleExportExcel = () => {
    if (filteredMachines.length === 0) {
      message.warning("No hay máquinas para exportar.");
      return;
    }

    message.loading({ content: 'Generando Excel...', key: 'exportExcelMaquinas' });

    // Preparar datos para exportar (usando filteredMachines en lugar de machines)
    const dataToExport = filteredMachines.map(machine => {
      // Buscar nombres de sección y línea
      const sectionName = sections.find(s => s.id === machine.section_id)?.nombre || machine.section_id;
      const lineName = sections.flatMap(s => s.lines).find(l => l.id === machine.line_id)?.nombre || machine.line_id;

      return {
        'ID': machine.id,
        'Nombre Máquina': machine.nombre,
        'Modelo': machine.modelo,
        'Marca': machine.marca,
        'Nº Serie': machine.numero_serie,
        'Criticidad': machine.criticidad || '-',
        'Sección': sectionName,
        'Línea': lineName,
      };
    });

    try {
      // Crear hoja
      const worksheet = XLSX.utils.json_to_sheet(dataToExport);
      // Ajustar anchos
      const columnWidths = [
        { wch: 8 }, { wch: 30 }, { wch: 20 }, { wch: 20 }, 
        { wch: 25 }, { wch: 15 }, { wch: 20 }, { wch: 20 }
      ];
      worksheet['!cols'] = columnWidths;
      // Crear libro y añadir hoja
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "Maquinas");
      // Descargar archivo
      XLSX.writeFile(workbook, "Lista_Maquinas.xlsx");
      message.success({ 
        content: 'Exportación a Excel completada.', 
        key: 'exportExcelMaquinas', 
        duration: 3 
      });
    } catch (error) {
      console.error("Error al generar Excel:", error);
      message.error({
        content: 'Error al generar el archivo Excel.',
        key: 'exportExcelMaquinas',
        duration: 3
      });
    }
  };

  // --- Definición de Columnas (versión escritorio) ---
  const desktopColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { 
      title: 'Nombre', 
      dataIndex: 'nombre', 
      key: 'nombre', 
      defaultSortOrder: 'ascend',
      sorter: (a, b) => (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' }),
      render: (text, record) => (
        <Link to={`/maquinas/${record.id}/detail`}>{text}</Link>
      )
    },
    { title: 'Modelo', dataIndex: 'modelo', key: 'modelo' },
    { title: 'Marca', dataIndex: 'marca', key: 'marca' },
    { title: 'Nº Serie', dataIndex: 'numero_serie', key: 'numero_serie' },
    { 
      title: 'Criticidad', 
      dataIndex: 'criticidad', 
      key: 'criticidad', 
      width: 120, 
      render: (text) => text || '-' 
    },
    { 
      title: 'Acciones', 
      key: 'acciones', 
      width: 240, 
      align: 'center',
      render: (_, record) => (
        <Space>
          {/* Solo mostrar botón de edición para roles administrativos */}
          {canManageOrEdit && (
            <Button 
              type="primary" 
              icon={<EditOutlined />} 
              onClick={() => handleEdit(record)} 
              size="small" 
              title="Editar Máquina"
            />
          )}
          
          {/* Solo mostrar botón de BOM para roles administrativos */}
          {canManageOrEdit && (
            <Link to={`/maquinas/${record.id}/bom`}>
              <Button 
                icon={<UnorderedListOutlined />} 
                size="small" 
                title="Ver/Editar BOM" 
              />
            </Link>
          )}
          
          {/* Mostrar detalles para todos los roles incluyendo mecánicos */}
          <Link to={`/maquinas/${record.id}/detail`}>
            <Button 
              icon={<EyeOutlined />} 
              size="small" 
              title="Ver Detalles" 
            />
          </Link>
          
          {/* Solo mostrar botón de eliminar para roles administrativos */}
          {canManageOrEdit && (
            <Popconfirm 
              title={`¿Eliminar máquina "${record.nombre}"?`} 
              onConfirm={() => handleDelete(record.id)} 
              okText="Sí" 
              cancelText="No" 
              okType="danger"
            >
              <Button 
                type="primary" 
                danger 
                icon={<DeleteOutlined />} 
                size="small" 
                title="Eliminar Máquina"
              />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  // --- Definición de Columnas (versión móvil) ---
  const mobileColumns = [
    { 
      title: 'Máquina', 
      dataIndex: 'nombre', 
      key: 'nombre',
      defaultSortOrder: 'ascend',
      sorter: (a, b) => (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' }),
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
            <Link to={`/maquinas/${record.id}/detail`}>{text}</Link>
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.marca} {record.modelo}
            {record.criticidad && (
              <span style={{ marginLeft: '8px', color: '#1890ff' }}>
                ({record.criticidad})
              </span>
            )}
          </div>
        </div>
      )
    },
    { 
      title: 'Acciones', 
      key: 'acciones', 
      width: 90, 
      align: 'center',
      render: (_, record) => (
        <Space size="small">
          <Link to={`/maquinas/${record.id}/detail`}>
            <Button 
              icon={<EyeOutlined />} 
              size="small" 
              type="primary"
            />
          </Link>
          
          {canManageOrEdit && (
            <Button 
              icon={<EditOutlined />} 
              onClick={() => handleEdit(record)} 
              size="small" 
            />
          )}
          
          {canManageOrEdit && (
            <Popconfirm 
              title="¿Eliminar?" 
              onConfirm={() => handleDelete(record.id)} 
              okText="Sí" 
              cancelText="No" 
              okType="danger"
            >
              <Button 
                danger 
                icon={<DeleteOutlined />} 
                size="small" 
              />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  // Contenido del formulario de máquina (compartido entre desktop y móvil)
  const machineForm = (
    <Form form={form} layout="vertical" name="machine_form">
      <Form.Item 
        name="nombre" 
        label="Nombre" 
        rules={[{ required: true, message: 'Ingrese nombre' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item 
        name="modelo" 
        label="Modelo" 
        rules={[{ required: true, message: 'Ingrese modelo' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item 
        name="marca" 
        label="Marca" 
        rules={[{ required: true, message: 'Ingrese marca' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item 
        name="numero_serie" 
        label="Número de Serie" 
        rules={[{ required: true, message: 'Ingrese número de serie' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item 
        name="section_id" 
        label="Sección" 
        rules={[{ required: true, message: 'Seleccione sección' }]}
      >
        <Select 
          placeholder="Seleccione sección" 
          onChange={handleSectionChange} 
          allowClear
          size={isMobile ? "small" : "middle"}
        >
          {sections.map(section => (
            <Option key={section.id} value={section.id}>
              {section.nombre}
            </Option>
          ))}
        </Select>
      </Form.Item>
      <Form.Item 
        name="line_id" 
        label="Línea" 
        rules={[{ required: true, message: 'Seleccione línea' }]}
      >
        <Select 
          placeholder="Seleccione línea" 
          allowClear 
          disabled={!form.getFieldValue('section_id')}
          size={isMobile ? "small" : "middle"}
        >
          {filteredLines.map(line => (
            <Option key={line.id} value={line.id}>
              {line.nombre}
            </Option>
          ))}
        </Select>
      </Form.Item>
      <Form.Item 
        name="criticidad" 
        label="Criticidad" 
        rules={[{ required: false }]}
      >
        <Select 
          placeholder="Seleccione criticidad (Opcional)" 
          allowClear
          size={isMobile ? "small" : "middle"}
        >
          <Option value="Alta">Alta</Option>
          <Option value="Media">Media</Option>
          <Option value="Baja">Baja</Option>
        </Select>
      </Form.Item>
    </Form>
  );

  // Versión móvil
  if (isMobile) {
    return (
      <MobileLayout title="Gestión de Máquinas">
        <div style={{ padding: '0 5px' }}>
          {/* Buscador */}
          <div style={{ marginBottom: '8px' }}>
            <AutoComplete
              options={searchOptions}
              style={{ width: '100%' }}
              onSearch={handleSearch}
              value={searchText}
              onChange={setSearchText}
              size="small"
            >
              <Input.Search
                placeholder="Buscar máquina..."
                enterButton={<SearchOutlined />}
                onSearch={handleSearch}
                allowClear
                size="small"
              />
            </AutoComplete>
          </div>
          
          {/* Botones de acción */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            marginBottom: '8px' 
          }}>
            <div>
              <Text style={{ fontSize: '14px' }}>
                {filteredMachines.length} máquinas
              </Text>
            </div>
            <Space size="small">
              {canManageOrEdit && (
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />} 
                  onClick={handleAddNew}
                  size="small"
                >
                  Nueva
                </Button>
              )}
              <Button 
                icon={<FileExcelOutlined />} 
                onClick={handleExportExcel} 
                disabled={loading || filteredMachines.length === 0} 
                size="small"
              />
            </Space>
          </div>
          
          {/* Tabla */}
          {error && (
            <Alert 
              message="Error de Carga" 
              description={error} 
              type="error" 
              showIcon 
              closable 
              onClose={() => setError(null)} 
              style={{ marginBottom: 8 }} 
            />
          )}
          
          <Card className="table-container" size="small" bodyStyle={{ padding: '8px' }}>
            <Spin spinning={loading}>
              <Table 
                columns={mobileColumns} 
                dataSource={filteredMachines} 
                rowKey="id" 
                pagination={{ 
                  pageSize: 10,
                  size: "small",
                  showSizeChanger: false
                }} 
                size="small" 
                bordered={false}
              />
            </Spin>
          </Card>
        </div>
        
        {/* Modal Edición/Creación */}
        <Modal
          title={editingRecord ? `Editar: ${editingRecord.nombre}` : 'Nueva Máquina'}
          open={modalVisible}
          onCancel={handleCancel}
          confirmLoading={isSubmitting}
          onOk={handleSubmit}
          okText={editingRecord ? 'Actualizar' : 'Guardar'}
          cancelText="Cancelar"
          width="95%"
          destroyOnClose
          maskClosable={false}
        >
          {machineForm}
        </Modal>
      </MobileLayout>
    );
  }

  // Versión escritorio
  return (
    <div className="page-container">
      <Title level={2} className="page-title">Gestión de Máquinas</Title>

      {error && (
        <Alert 
          message="Error de Carga" 
          description={error} 
          type="error" 
          showIcon 
          closable 
          onClose={() => setError(null)} 
          style={{ marginBottom: 16 }} 
        />
      )}

      <Card className="table-container">
        {/* Barra de acciones: Búsqueda y Botones */}
        <div style={{ 
          marginBottom: 16, 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center' 
        }}>
          {/* Buscador con Autocompletado */}
          <AutoComplete
            options={searchOptions}
            style={{ width: 400 }}
            onSearch={handleSearch}
            value={searchText}
            onChange={setSearchText}
            placeholder="Buscar por nombre, modelo, marca..."
          >
            <Input.Search
              size="middle"
              enterButton={<SearchOutlined />}
              onSearch={handleSearch}
              allowClear
            />
          </AutoComplete>
          
          {/* Botones de Acción */}
          <Space>
            {/* Ocultar botones de Nueva Máquina para mecánicos */}
            {canManageOrEdit && (
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={handleAddNew}
              >
                Nueva Máquina
              </Button>
            )}
            <Button 
              type="primary" 
              icon={<FileExcelOutlined />} 
              onClick={handleExportExcel} 
              disabled={loading || filteredMachines.length === 0} 
              ghost
            >
              Exportar a Excel
            </Button>
          </Space>
        </div>

        {/* 🔧 TABLA DE MÁQUINAS CON PAGINACIÓN CORREGIDA */}
        <Spin spinning={loading}>
          <Table 
            columns={desktopColumns} 
            dataSource={filteredMachines} 
            rowKey="id" 
            pagination={pagination}
            onChange={handleTableChange}
            size="small" 
            bordered 
          />
        </Spin>

        {/* Modal para Editar/Crear Máquina */}
        <Modal
          title={editingRecord ? `Editar Máquina: ${editingRecord.nombre}` : 'Nueva Máquina'}
          open={modalVisible}
          onCancel={handleCancel}
          confirmLoading={isSubmitting}
          onOk={handleSubmit}
          okText={editingRecord ? 'Actualizar' : 'Guardar'}
          cancelText="Cancelar"
          width={720}
          destroyOnClose
          maskClosable={false}
        >
          {machineForm}
        </Modal>
      </Card>
    </div>
  );
};

export default Maquinas;