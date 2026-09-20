// src/pages/Productos.js (Con Clasificación por Tipos y Recepción de Material)
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Table, Button, Modal, Form, Input, InputNumber, 
  Select, message, Space, Spin, Alert, Typography, 
  Popconfirm, AutoComplete, Card, Row, Col, Tooltip, Tag
} from 'antd';
import { 
  DeleteOutlined, EditOutlined, PlusOutlined, SearchOutlined, 
  FileExcelOutlined, ShoppingCartOutlined, EyeOutlined,
  SettingOutlined, ThunderboltOutlined, CloudOutlined, ToolOutlined 
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import * as XLSX from 'xlsx';
import '../styles/CommonPage.css';
import { useNavigate, useLocation } from 'react-router-dom';
import MaterialReceptionForm from '../components/MaterialReceptionForm';

const { Option } = Select;
const { Text, Title } = Typography;
const { Search } = Input;

const Productos = () => {
  const [productos, setProductos] = useState([]);
  const [productosFiltered, setProductosFiltered] = useState([]);
  const [proveedores, setProveedores] = useState([]);
  const [almacenes, setAlmacenes] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [form] = Form.useForm();
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  // Estados para Modal "Donde se Usa"
  const [usageModalVisible, setUsageModalVisible] = useState(false);
  const [partUsageData, setPartUsageData] = useState([]);
  const [loadingUsage, setLoadingUsage] = useState(false);
  const [viewingPart, setViewingPart] = useState(null);

  // Estados para Recepción de Material
  const [receptionModalVisible, setReceptionModalVisible] = useState(false);

  // Nuevo estado para opciones de autocompletado
  const [productNameOptions, setProductNameOptions] = useState([]);
  // Estado para producto ya existente seleccionado
  const [selectedExistingProduct, setSelectedExistingProduct] = useState(null);

  // 🔧 ESTADO PARA PAGINACIÓN
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 15,
    showSizeChanger: true,
    showQuickJumper: true,
    pageSizeOptions: ['10', '15', '20', '30', '50', '100'],
    showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} productos`,
  });

  // --- Constantes para tipos de producto ---
  const PRODUCT_TYPES = [
    { value: 'mecánico', label: 'Mecánico', icon: <SettingOutlined />, color: 'green' },
    { value: 'eléctrico', label: 'Eléctrico', icon: <ThunderboltOutlined />, color: 'gold' },
    { value: 'neumático', label: 'Neumático', icon: <CloudOutlined />, color: 'blue' },
    { value: 'limpieza', label: 'Limpieza', icon: <ToolOutlined />, color: 'purple' } 
  ];

  // Función helper para obtener información del tipo
  const getTypeInfo = (tipo) => {
    return PRODUCT_TYPES.find(t => t.value === tipo) || PRODUCT_TYPES[0];
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      const [productosData, proveedoresData, almacenesData] = await Promise.all([
        fetchWithAuth('/productos'),
        fetchWithAuth('/suppliers'),
        fetchWithAuth('/almacenes')
      ]);
      
      // Ordenar productos alfabéticamente por nombre
      const productosConKey = (productosData || [])
        .map(p => ({ 
          ...p, 
          key: p.id,
          // Asegurar que tipo existe, usar 'mecánico' como default
          tipo: p.tipo || 'mecánico'
        }))
        .sort((a, b) => (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' }));
      
      setProductos(productosConKey);
      setProductosFiltered(productosConKey);
      setProveedores(proveedoresData || []);
      setAlmacenes(almacenesData || []);
      
      // Preparar opciones para autocompletado (también ordenadas)
      const uniqueNames = [...new Set(productosData.map(p => p.nombre))]
        .sort((a, b) => a.localeCompare(b, 'es', { sensitivity: 'base' }));
      setProductNameOptions(uniqueNames.map(name => ({ value: name })));
    } catch (error) {
      message.error('Error al cargar datos: ' + (error.message || 'Error desconocido'));
      console.error("Fetch Data Error:", error);
    } finally {
      setLoading(false);
    }
  };

  // 🔧 FUNCIÓN PARA MANEJAR CAMBIOS EN LA PAGINACIÓN
  const handleTableChange = (pag, filters, sorter) => {
    console.log('Cambio en tabla:', pag);
    setPagination({
      ...pagination,
      current: pag.current,
      pageSize: pag.pageSize,
    });
  };

  // useEffect para cargar datos iniciales y manejar parámetros de estado
  useEffect(() => {
    fetchData();
    
    // Verificar si venimos de la página de detalle con parámetros de estado
    const state = location.state;
    if (state) {
      // Si hay ID de producto para editar, abrir el modal con ese producto
      if (state.editProduct) {
        const productId = state.editProduct;
        console.log("Abriendo modal para editar producto ID:", productId);
        
        // Buscar el producto en la lista
        setTimeout(() => {
          const productToEdit = productos.find(p => p.id === productId);
          if (productToEdit) {
            handleEditClick(productToEdit);
          } else {
            // Si el producto no está en la lista actual, podríamos cargarlo directamente
            const fetchProductToEdit = async () => {
              try {
                const productData = await fetchWithAuth(`/productos/${productId}`);
                if (productData) {
                  handleEditClick(productData);
                }
              } catch (error) {
                console.error("Error al cargar producto para editar:", error);
                message.error("No se pudo cargar el producto para editar");
              }
            };
            
            fetchProductToEdit();
          }
        }, 500);
      }
      
      // Si hay ID de producto para gestionar stock, abrir el modal con foco en cantidad
      if (state.editStock) {
        const productId = state.editStock;
        console.log("Abriendo modal para gestionar stock del producto ID:", productId);
        
        // Buscar el producto en la lista
        setTimeout(() => {
          const productToEdit = productos.find(p => p.id === productId);
          if (productToEdit) {
            handleEditClick(productToEdit);
            
            // Después de abrir el modal, enfocar el campo de cantidad
            setTimeout(() => {
              const quantityInput = document.querySelector('input[name="quantity"]');
              if (quantityInput) {
                quantityInput.focus();
                quantityInput.select();
              }
            }, 500);
          } else {
            // Si el producto no está en la lista actual, podríamos cargarlo directamente
            const fetchProductToEdit = async () => {
              try {
                const productData = await fetchWithAuth(`/productos/${productId}`);
                if (productData) {
                  handleEditClick(productData);
                  // Después de abrir el modal, enfocar el campo de cantidad
                  setTimeout(() => {
                    const quantityInput = document.querySelector('input[name="quantity"]');
                    if (quantityInput) {
                      quantityInput.focus();
                      quantityInput.select();
                    }
                  }, 500);
                }
              } catch (error) {
                console.error("Error al cargar producto para gestionar stock:", error);
                message.error("No se pudo cargar el producto para gestionar stock");
              }
            };
            
            fetchProductToEdit();
          }
        }, 500);
      }
      
      // Limpiar el estado de la ubicación para evitar que se abra automáticamente de nuevo
      if (state.fromDetail) {
        window.history.replaceState({}, document.title);
      }
    }
  }, [location.state]);

  // Función para filtrar productos
  const handleSearch = (value) => {
    setSearchTerm(value);
    // 🔧 RESETEAR PAGINACIÓN AL BUSCAR
    setPagination({
      ...pagination,
      current: 1 // Volver a la primera página
    });
    
    if (!value) {
      // Mantener orden alfabético cuando se limpia la búsqueda
      const sortedProducts = [...productos].sort((a, b) => 
        (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' })
      );
      setProductosFiltered(sortedProducts);
      return;
    }
    
    const filtered = productos.filter(producto => 
      producto.nombre.toLowerCase().includes(value.toLowerCase()) ||
      (producto.tipo && producto.tipo.toLowerCase().includes(value.toLowerCase()))
    );
    
    // Ordenar alfabéticamente los resultados filtrados
    const sortedFiltered = filtered.sort((a, b) => 
      (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' })
    );
    
    setProductosFiltered(sortedFiltered);
    
    if (sortedFiltered.length === 0) {
      message.info(`No se encontraron productos que coincidan con "${value}"`);
    } else {
      message.success(`Se encontraron ${sortedFiltered.length} productos`);
    }
  };

  const handleDelete = async (id) => {
    try {
      await fetchWithAuth(`/productos/${id}`, { method: 'DELETE' });
      message.success('Producto eliminado correctamente');
      fetchData();
    } catch (error) {
      const errorMsg = error.detail || error.message || 'Error desconocido al eliminar';
      message.error(`Error al eliminar: ${errorMsg}`);
      console.error("Delete error:", error);
    }
  };

  // Función para buscar producto por nombre en autocompletado del modal
  const handleAutoCompleteSearch = (value) => {
    if (!value) {
      const recentOptions = productos.slice(0, 5).map(p => ({
        value: p.nombre,
        id: p.id,
        almacen_id: p.almacen_id,
        precio: p.precio,
        cantidad: p.cantidad,
        supplier_id: p.supplier_id,
        descuento: p.descuento,
        stock_minimo: p.stock_minimo || 0,
        tipo: p.tipo || 'mecánico'
      }));
      setProductNameOptions(recentOptions);
      return;
    }

    const filtered = productos
      .filter(p => p.nombre.toLowerCase().includes(value.toLowerCase()))
      .sort((a, b) => (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' }))
      .map(p => ({
        value: p.nombre,
        id: p.id,
        almacen_id: p.almacen_id,
        precio: p.precio,
        cantidad: p.cantidad,
        supplier_id: p.supplier_id,
        descuento: p.descuento,
        stock_minimo: p.stock_minimo || 0,
        tipo: p.tipo || 'mecánico'
      }));

    setProductNameOptions(filtered);
  };

  // Función para seleccionar un producto existente
  const handleSelectExistingProduct = (value, option) => {
    const product = productNameOptions.find(p => p.value === value);
    if (product) {
      setSelectedExistingProduct(product);
      
      form.setFieldsValue({
        quantity: product.cantidad || 0,
        warehouse_id: product.almacen_id,
        price: product.precio || 0,
        discount: product.descuento || 0,
        supplier_id: product.supplier_id,
        stock_minimo: product.stock_minimo || 0,
        tipo: product.tipo || 'mecánico'
      });
      
      message.info(`Cargados datos del producto existente: "${value}"`);
    }
  };

  const handleSubmit = async (values) => {
    const dataToSend = {
      ...values,
      quantity: Number(values.quantity) || 0,
      price: Number(values.price) || 0,
      discount: values.discount === null || values.discount === '' || isNaN(Number(values.discount)) 
        ? null 
        : Number(values.discount),
      tipo: values.tipo || 'mecánico' // Asegurar que siempre hay un tipo
    };
    
    if (dataToSend.discount === null) delete dataToSend.discount;
    
    const method = editingId ? 'PUT' : 'POST';
    const url = editingId ? `/productos/${editingId}` : '/productos';
    
    if (!editingId && selectedExistingProduct) {
      Modal.confirm({
        title: 'Producto ya existente',
        content: `El producto "${values.product_name}" ya existe. ¿Desea actualizar su cantidad en lugar de crear uno nuevo?`,
        okText: 'Sí, actualizar existente',
        cancelText: 'No, crear nuevo',
        onOk: async () => {
          try {
            await fetchWithAuth(`/productos/${selectedExistingProduct.id}`, { 
              method: 'PUT', 
              headers: { 'Content-Type': 'application/json' }, 
              body: JSON.stringify({
                product_name: values.product_name, // ¡AGREGAR ESTA LÍNEA!
                quantity: Number(values.quantity) || 0,
                warehouse_id: values.warehouse_id,
                price: Number(values.price) || 0,
                discount: values.discount !== null ? Number(values.discount) : null,
                supplier_id: values.supplier_id,
                stock_minimo: values.stock_minimo !== null ? Number(values.stock_minimo) : 0,
                tipo: values.tipo || 'mecánico'
              }) 
            });
            message.success(`Producto "${values.product_name}" actualizado correctamente`);
            setModalVisible(false); 
            setSelectedExistingProduct(null);
            form.resetFields();
            fetchData();
          } catch (error) {
            console.error('Error completo al actualizar producto existente:', error);
            const errorMsg = error.detail || error.message || 'Error desconocido al guardar';
            message.error(`Error al actualizar producto existente: ${errorMsg}`);
          }
        },
        onCancel: async () => {
          try {
            await procesarSubmit(method, url, dataToSend);
          } catch (error) {
            console.error('Error al crear nuevo producto:', error);
          }
        }
      });
    } else {
      try {
        await procesarSubmit(method, url, dataToSend);
      } catch (error) {
        console.error('Error al guardar producto:', error);
      }
    }
  };

  // Función auxiliar para procesar el envío
  const procesarSubmit = async (method, url, dataToSend) => {
    console.log(`Enviando (${method}) a ${url}:`, dataToSend);
    
    try {
      await fetchWithAuth(url, { 
        method, 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify(dataToSend) 
      });
      message.success(`Producto ${editingId ? 'actualizado' : 'creado'} correctamente`);
      setModalVisible(false); 
      setEditingId(null); 
      setSelectedExistingProduct(null);
      form.resetFields();
      fetchData();
    } catch (error) {
      console.error('Error completo en handleSubmit:', error);
      const errorMsg = error.detail || error.message || 'Error desconocido al guardar';
      message.error(`Error al guardar: ${errorMsg}`);
    }
  };

  const handleEditClick = (record) => {
    console.log("Editando registro:", record);
    setEditingId(record.id);
    setSelectedExistingProduct(null);
    
    form.setFieldsValue({
      product_name: record.nombre,
      quantity: Number(record.cantidad) || 0,
      warehouse_id: record.almacen_id,
      price: Number(record.precio) || 0,
      discount: record.descuento !== null && record.descuento !== undefined 
        ? Number(record.descuento) 
        : 0,
      supplier_id: record.supplier_id,
      stock_minimo: record.stock_minimo || 0,
      tipo: record.tipo || 'mecánico'
    });
    
    setModalVisible(true);
  };

  // Función para mostrar uso
  const handleShowUsage = useCallback(async (record) => {
    const partName = record.nombre || record.product_name || `ID ${record.id}`;
    console.log(`Mostrando uso para repuesto: ${partName} (ID: ${record.id})`);
    setViewingPart({ id: record.id, nombre: partName });
    setPartUsageData([]);
    setLoadingUsage(true);
    setUsageModalVisible(true);
    try {
      const usageData = await fetchWithAuth(`/inventory/${record.id}/usage`);
      setPartUsageData(usageData || []);
      console.log("Usage data received:", usageData);
      if (!usageData || usageData.length === 0) {
        message.info(`El repuesto "${partName}" no está actualmente asociado a ninguna máquina en el BOM.`);
      }
    } catch (error) {
      console.error("Error fetching usage data:", error);
      message.error(`Error al cargar datos de uso: ${error.message || 'Error desconocido'}`);
      setUsageModalVisible(false);
    } finally {
      setLoadingUsage(false);
    }
  }, []);

  // Función para exportar Excel
  const handleExportExcel = () => {
    console.log("Exportando productos a Excel...");
    if (productos.length === 0) { 
      message.warning("No hay productos para exportar."); 
      return; 
    }
    
    message.loading({ content: 'Generando Excel...', key: 'exportExcelProd' });
    
    const dataToExport = productosFiltered.map(prod => ({
      'ID': prod.id,
      'Tipo': prod.tipo ? prod.tipo.charAt(0).toUpperCase() + prod.tipo.slice(1) : 'Mecánico',
      'Nombre': prod.nombre,
      'Cantidad': prod.cantidad,
      'Almacén ID': prod.almacen_id,
      'Precio (€)': prod.precio,
      'Descuento (%)': prod.descuento || 0,
      'Proveedor ID': prod.supplier_id,
      'Stock Mínimo': prod.stock_minimo || 0,
    }));
    
    try {
      const worksheet = XLSX.utils.json_to_sheet(dataToExport);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "Productos");
      XLSX.writeFile(workbook, "Productos_Stock_con_Tipos.xlsx");
      message.success({ content: 'Exportación a Excel completada.', key: 'exportExcelProd', duration: 3 });
    } catch (error) {
      console.error("Error al generar Excel:", error);
      message.error({ content: 'Error al generar el archivo Excel.', key: 'exportExcelProd', duration: 3 });
    }
  };

  // Función para ver detalle del producto
  const handleViewDetail = (record) => {
    navigate(`/productos/${record.id}`);
  };

  // Columnas para la tabla MEJORADAS
  const columns = [
    {
      title: 'Tipo',
      dataIndex: 'tipo',
      key: 'tipo',
      width: 120,
      align: 'center',
      render: (tipo) => {
        const typeInfo = getTypeInfo(tipo);
        return (
          <Tag color={typeInfo.color} icon={typeInfo.icon}>
            {typeInfo.label}
          </Tag>
        );
      },
      filters: PRODUCT_TYPES.map(type => ({
        text: type.label,
        value: type.value
      })),
      onFilter: (value, record) => (record.tipo || 'mecánico') === value,
    },
    { 
      title: 'Nombre', 
      dataIndex: 'nombre', 
      key: 'nombre',
      sorter: (a, b) => (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' }),
      render: (text, record) => (
        <Tooltip title="Ver detalles del producto">
          <Button 
            type="link" 
            onClick={() => handleViewDetail(record)}
            style={{ padding: 0, textAlign: 'left', height: 'auto' }}
          >
            {text}
          </Button>
        </Tooltip>
      )
    },
    { 
      title: 'Cantidad', 
      dataIndex: 'cantidad', 
      key: 'cantidad',
      sorter: (a, b) => a.cantidad - b.cantidad,
      render: (cantidad, record) => {
        const stockMinimo = record.stock_minimo || 0;
        let color = 'default';
        
        if (cantidad <= 0) color = 'red';
        else if (cantidad <= stockMinimo) color = 'orange';
        else if (cantidad <= stockMinimo * 1.5) color = 'gold';
        else color = 'green';
        
        return (
          <span style={{ 
            color: color === 'red' ? '#ff4d4f' : 
                   color === 'orange' ? '#fa8c16' : 
                   color === 'gold' ? '#faad14' : '#52c41a',
            fontWeight: cantidad <= stockMinimo ? 'bold' : 'normal'
          }}>
            {cantidad}
          </span>
        );
      }
    },
    { title: 'Almacén ID', dataIndex: 'almacen_id', key: 'almacen_id' },
    { 
      title: 'Precio', 
      dataIndex: 'precio', 
      key: 'precio',
      sorter: (a, b) => (a.precio || 0) - (b.precio || 0),
      render: precio => precio ? `${precio.toFixed(2)} €` : '0.00 €'
    },
    { 
      title: 'Descuento', 
      dataIndex: 'descuento', 
      key: 'descuento',
      render: descuento => descuento ? `${descuento}%` : '0%'
    },
    { title: 'Proveedor ID', dataIndex: 'supplier_id', key: 'supplier_id' },
    { 
      title: 'Stock Mín', 
      dataIndex: 'stock_minimo', 
      key: 'stock_minimo',
      render: stock => stock || 0
    },
    {
      title: 'Acciones',
      key: 'acciones',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="Ver detalles">
            <Button 
              icon={<EyeOutlined />} 
              size="small" 
              type="default"
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          <Tooltip title="Ver dónde se usa">
            <Button 
              icon={<SearchOutlined />} 
              size="small" 
              onClick={() => handleShowUsage(record)}
            />
          </Tooltip>
          <Tooltip title="Editar">
            <Button 
              icon={<EditOutlined />} 
              size="small" 
              onClick={() => handleEditClick(record)}
            />
          </Tooltip>
          <Popconfirm 
            title="¿Seguro que desea eliminar?" 
            onConfirm={() => handleDelete(record.id)} 
            okText="Sí" 
            cancelText="No"
          >
            <Tooltip title="Eliminar">
              <Button 
                danger 
                icon={<DeleteOutlined />} 
                size="small" 
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="page-container">
      <Title level={2}>Gestión de Productos</Title>
      
      <Card className="search-card">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8}>
            <Search
              placeholder="Buscar productos..."
              onSearch={handleSearch}
              onChange={(e) => !e.target.value && handleSearch('')}
              allowClear
              style={{ width: '100%' }}
            />
          </Col>
          
          <Col xs={24} sm={16} style={{ textAlign: 'right' }}>
            <Space>
              <Button
                type="primary"
                icon={<ShoppingCartOutlined />}
                onClick={() => setReceptionModalVisible(true)}
              >
                Recibir Material
              </Button>
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={() => {
                  setEditingId(null);
                  setSelectedExistingProduct(null);
                  form.resetFields();
                  setModalVisible(true);
                }}
              >
                Nuevo Producto
              </Button>
              <Button 
                icon={<FileExcelOutlined />} 
                onClick={handleExportExcel} 
                disabled={loading || productosFiltered.length === 0}
              >
                Exportar Excel
              </Button>
            </Space>
          </Col>
          
          <Col span={24}>
            {searchTerm && (
              <Text type="secondary">
                Mostrando {productosFiltered.length} resultados{searchTerm ? ` para "${searchTerm}"` : ''}
              </Text>
            )}
          </Col>
        </Row>
      </Card>

      <Table 
        loading={loading} 
        columns={columns} 
        dataSource={productosFiltered}
        rowKey="id" 
        scroll={{ x: 'max-content' }}
        pagination={pagination}
        onChange={handleTableChange}
      />

      {/* Modal Editar/Crear Producto */}
      <Modal 
        title={editingId ? "Editar Producto" : "Nuevo Producto"} 
        open={modalVisible} 
        onCancel={() => { 
          setModalVisible(false); 
          setEditingId(null);
          setSelectedExistingProduct(null);
          form.resetFields(); 
        }} 
        destroyOnClose 
        footer={null} 
        width={600}
      >
        <Form 
          form={form} 
          layout="vertical" 
          onFinish={handleSubmit} 
          initialValues={{ 
            quantity: 0, 
            price: 0,
            discount: 0,
            tipo: 'mecánico'
          }}
        >
          <Row gutter={16}>
            <Col span={16}>
              <Form.Item 
                name="product_name" 
                label="Nombre Producto" 
                rules={[{ required: true, message: 'Por favor ingrese el nombre del producto' }]}
              >
                <AutoComplete
                  options={productNameOptions}
                  onSearch={handleAutoCompleteSearch}
                  onSelect={handleSelectExistingProduct}
                  placeholder="Escriba para buscar o crear"
                  filterOption={false}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item 
                name="tipo" 
                label="Tipo de Producto" 
                rules={[{ required: true, message: 'Seleccione un tipo' }]}
              >
                <Select placeholder="Seleccione tipo">
                  {PRODUCT_TYPES.map(type => (
                    <Option key={type.value} value={type.value}>
                      <Space>
                        {type.icon}
                        {type.label}
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item 
                name="quantity" 
                label="Cantidad" 
                rules={[
                  { required: true, message: 'Por favor ingrese la cantidad' },
                  { 
                    type: 'number', 
                    min: 0, 
                    message: 'La cantidad debe ser un número positivo',
                    transform: (value) => {
                      return value === null || value === undefined || value === '' 
                        ? 0 
                        : Number(value);
                    }
                  }
                ]}
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item 
                name="warehouse_id" 
                label="Almacén" 
                rules={[{ required: true, message: 'Por favor seleccione un almacén' }]}
              >
                <Select 
                  placeholder="Seleccione almacén" 
                  allowClear
                  showSearch
                  filterOption={(input, option) =>
                    option.children.toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {almacenes.map(almacen => (
                    <Option key={almacen.id} value={almacen.id}>
                      {almacen.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item 
                name="price" 
                label="Precio" 
                rules={[{ 
                  type: 'number', 
                  min: 0, 
                  message: 'El precio debe ser positivo',
                  transform: (value) => {
                    return value === null || value === undefined || value === '' 
                      ? 0 
                      : Number(value);
                  }
                }]}
              >
                <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item 
                name="stock_minimo" 
                label="Stock Mínimo" 
                rules={[
                  { 
                    type: 'number', 
                    min: 0, 
                    message: 'Debe ser un número positivo',
                    transform: (value) => {
                      return value === null || value === undefined || value === '' 
                        ? 0 
                        : Number(value);
                    }
                  }
                ]}
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item 
                name="discount" 
                label="Descuento (%)" 
                rules={[
                  { 
                    type: 'number', 
                    min: 0, 
                    max: 100, 
                    message: 'Debe estar entre 0 y 100%',
                    transform: (value) => {
                      return value === null || value === undefined || value === '' 
                        ? 0 
                        : Number(value);
                    }
                  }
                ]}
              >
                <Input type="number" min={0} max={100} step={0.01} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item 
                name="supplier_id" 
                label="Proveedor"
              >
                <Select 
                  placeholder="Opcional" 
                  allowClear
                  showSearch
                  filterOption={(input, option) =>
                    option.children.toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {proveedores.map(p => (
                    <Option key={p.id} value={p.id}>
                      {p.company || p.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item style={{ textAlign: 'right', marginTop: 24 }}>
            <Space>
              <Button onClick={() => { 
                setModalVisible(false); 
                setEditingId(null);
                setSelectedExistingProduct(null);
                form.resetFields(); 
              }}>
                Cancelar
              </Button>
              <Button type="primary" htmlType="submit">
                {editingId ? 'Actualizar' : 'Guardar'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Modal para "Dónde se Usa" */}
      <Modal
        title={viewingPart ? `Máquinas que usan: ${viewingPart.nombre} (ID: ${viewingPart.id})` : 'Cargando...'}
        open={usageModalVisible}
        onCancel={() => setUsageModalVisible(false)}
        footer={[ <Button key="back" onClick={() => setUsageModalVisible(false)}>Cerrar</Button> ]}
        width={600}
      >
        <Spin spinning={loadingUsage}>
          {partUsageData.length > 0 ? (
            <Table
              dataSource={partUsageData}
              rowKey={(record) => `${record.machine.id}-${viewingPart?.id}`}
              size="small"
              pagination={false}
              columns={[
                { title: 'ID Máquina', dataIndex: ['machine', 'id'], key: 'machine_id' },
                { title: 'Nombre Máquina', dataIndex: ['machine', 'nombre'], key: 'machine_name' },
                { title: 'Cantidad Usada', dataIndex: 'quantity', key: 'quantity', align: 'right' },
              ]}
            />
          ) : (
            !loadingUsage && <Text>Este repuesto no está actualmente asociado a ninguna máquina en el BOM.</Text>
          )}
        </Spin>
      </Modal>

      {/* Modal de Recepción de Material */}
      <MaterialReceptionForm
        visible={receptionModalVisible}
        onCancel={() => setReceptionModalVisible(false)}
        onSuccess={() => {
          setReceptionModalVisible(false);
          fetchData(); // Recargar datos después de recibir material
        }}
        almacenes={almacenes}
        proveedores={proveedores}
      />
    </div>
  );
};

export default Productos;