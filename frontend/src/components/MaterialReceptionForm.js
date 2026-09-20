// src/components/MaterialReceptionForm.js - VERSIÓN COMPLETA CORREGIDA CON AUTOCOMPLETADO DE PRODUCTOS
import React, { useState } from 'react';
import {
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  Button,
  Space,
  message,
  Divider,
  Typography,
  Row,
  Col,
  Tooltip,
  AutoComplete
} from 'antd';
import {
  ShoppingCartOutlined,
  DollarOutlined,
  HomeOutlined,
  TeamOutlined,
  TagsOutlined,
  WarningOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';

const { Option } = Select;
const { Text, Title } = Typography;

const MaterialReceptionForm = ({ 
  visible, 
  onCancel, 
  onSuccess, 
  almacenes = [], 
  proveedores = [] 
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  
  // Estado para mostrar precio neto calculado
  const [precioNeto, setPrecioNeto] = useState(0);
  
  // Estados para AutoComplete de productos
  const [productNameOptions, setProductNameOptions] = useState([]);
  const [productos, setProductos] = useState([]);

  // Cargar productos existentes cuando se abre el modal
  React.useEffect(() => {
    if (visible) {
      fetchProductos();
    }
  }, [visible]);

  // Función para cargar productos existentes
  const fetchProductos = async () => {
    try {
      const productosData = await fetchWithAuth('/productos');
      setProductos(productosData || []);
      
      // Preparar opciones iniciales (los 10 más recientes)
      const recentOptions = (productosData || [])
        .slice(0, 10)
        .map(p => ({
          value: p.nombre,
          label: `${p.nombre} (Stock: ${p.cantidad})`,
          id: p.id,
          stock: p.cantidad,
          precio: p.precio,
          almacen_id: p.almacen_id,
          supplier_id: p.supplier_id
        }));
      setProductNameOptions(recentOptions);
    } catch (error) {
      console.error('Error cargando productos:', error);
    }
  };

  // Función para buscar productos mientras el usuario escribe
  const handleProductNameSearch = (value) => {
    if (!value || value.length < 1) {
      // Mostrar productos recientes cuando no hay búsqueda
      const recentOptions = productos
        .slice(0, 10)
        .map(p => ({
          value: p.nombre,
          label: `${p.nombre} (Stock: ${p.cantidad})`,
          id: p.id,
          stock: p.cantidad,
          precio: p.precio,
          almacen_id: p.almacen_id,
          supplier_id: p.supplier_id
        }));
      setProductNameOptions(recentOptions);
      return;
    }

    // Filtrar productos que coincidan con la búsqueda
    const filtered = productos
      .filter(p => p.nombre.toLowerCase().includes(value.toLowerCase()))
      .sort((a, b) => (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' }))
      .slice(0, 20) // Mostrar máximo 20 resultados
      .map(p => ({
        value: p.nombre,
        label: `${p.nombre} (Stock: ${p.cantidad})`,
        id: p.id,
        stock: p.cantidad,
        precio: p.precio,
        almacen_id: p.almacen_id,
        supplier_id: p.supplier_id
      }));

    setProductNameOptions(filtered);
  };

  // Función cuando se selecciona un producto existente
  const handleProductSelect = (value, option) => {
    const selectedProduct = productNameOptions.find(p => p.value === value);
    if (selectedProduct) {
      // Autorellenar campos relacionados
      form.setFieldsValue({
        warehouse_id: selectedProduct.almacen_id,
        price: selectedProduct.precio || 0,
        supplier_id: selectedProduct.supplier_id
      });
      
      message.info(`Producto seleccionado: ${value} (Stock actual: ${selectedProduct.stock})`);
    }
  };

  // Función para calcular precio neto cuando cambian precio o descuento
  const calcularPrecioNeto = () => {
    const precio = form.getFieldValue('price') || 0;
    const descuento = form.getFieldValue('discount') || 0;
    const neto = precio * (1 - descuento / 100);
    setPrecioNeto(neto);
  };

  // Función principal de envío del formulario
  const handleSubmit = async (values) => {
    setLoading(true);

    // Construir payload asegurando que stock_minimo se incluya
    const payload = {
      product_name: values.product_name?.trim(),
      quantity: parseInt(values.quantity) || 0,
      warehouse_id: parseInt(values.warehouse_id),
      price: parseFloat(values.price) || 0,
      supplier_id: values.supplier_id ? parseInt(values.supplier_id) : null,
      discount: values.discount ? parseFloat(values.discount) : 0,
      stock_minimo: values.stock_minimo !== undefined && values.stock_minimo !== null ? 
                    parseInt(values.stock_minimo) : 0
    };

    // Validaciones
    if (!payload.product_name) {
      message.error('El nombre del producto es obligatorio');
      setLoading(false);
      return;
    }

    if (payload.quantity <= 0) {
      message.error('La cantidad debe ser mayor a 0');
      setLoading(false);
      return;
    }

    if (!payload.warehouse_id) {
      message.error('Debe seleccionar un almacén');
      setLoading(false);
      return;
    }

    if (payload.price < 0) {
      message.error('El precio no puede ser negativo');
      setLoading(false);
      return;
    }

    if (payload.discount < 0 || payload.discount > 100) {
      message.error('El descuento debe estar entre 0 y 100%');
      setLoading(false);
      return;
    }

    try {
      const response = await fetchWithAuth('/productos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      message.success('Material recibido y registrado correctamente');
      form.resetFields();
      setPrecioNeto(0);
      onSuccess && onSuccess();
    } catch (error) {
      const errorMessage = error.detail || error.message || 'Error desconocido';
      message.error(`Error al procesar recepción: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  // Función para cancelar y limpiar el formulario
  const handleCancel = () => {
    form.resetFields();
    setPrecioNeto(0);
    onCancel && onCancel();
  };

  // Función para limpiar el formulario
  const handleReset = () => {
    form.resetFields();
    setPrecioNeto(0);
    message.info('Formulario limpiado');
  };

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShoppingCartOutlined style={{ color: '#52c41a' }} />
          <span>Recepción de Material</span>
        </div>
      }
      open={visible}
      onCancel={handleCancel}
      width={800}
      footer={null}
      destroyOnClose
      maskClosable={false}
    >
      <div style={{ marginBottom: '16px' }}>
        <Text type="secondary">
          Registra la entrada de nuevo material al inventario. Los campos marcados con * son obligatorios.
        </Text>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        autoComplete="off"
        preserve={false}
      >
        {/* Información del Producto */}
        <Row gutter={[16, 0]}>
          {/* Columna Izquierda - Información del Producto */}
          <Col xs={24} md={12}>
            <Form.Item
              name="product_name"
              label={
                <span>
                  <span style={{ color: 'red' }}>*</span> Nombre del Producto
                </span>
              }
              rules={[{ required: true, message: 'El nombre del producto es obligatorio' }]}
              tooltip="Nombre descriptivo del material que se está recibiendo. Escribe para buscar productos existentes."
            >
              <AutoComplete
                options={productNameOptions}
                onSearch={handleProductNameSearch}
                onSelect={handleProductSelect}
                placeholder="Escribe para buscar productos existentes o crear uno nuevo..."
                filterOption={false}
                allowClear
                style={{ width: '100%' }}
                notFoundContent="No se encontraron productos. Puedes crear uno nuevo."
              />
            </Form.Item>

            <Row gutter={[8, 0]}>
              <Col span={12}>
                <Form.Item
                  name="quantity"
                  label={
                    <span>
                      <span style={{ color: 'red' }}>*</span> Cantidad
                    </span>
                  }
                  rules={[
                    { required: true, message: 'La cantidad es obligatoria' },
                    { 
                      type: 'number', 
                      min: 1, 
                      message: 'Debe ser mayor a 0' 
                    }
                  ]}
                  tooltip="Cantidad de unidades que se están recibiendo"
                >
                  <InputNumber
                    min={1}
                    max={999999}
                    style={{ width: '100%' }}
                    placeholder="1"
                    precision={0}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="stock_minimo"
                  label="Stock Mínimo"
                  rules={[
                    { 
                      type: 'number', 
                      min: 0, 
                      message: 'No puede ser negativo',
                      transform: (value) => {
                        return value === '' || value === null || value === undefined 
                          ? 0 
                          : Number(value);
                      }
                    }
                  ]}
                  tooltip="Cantidad mínima recomendada en inventario para generar alertas de reposición"
                >
                  <InputNumber
                    min={0}
                    max={999999}
                    style={{ width: '100%' }}
                    placeholder="0"
                    precision={0}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="warehouse_id"
              label={
                <span>
                  <span style={{ color: 'red' }}>*</span> Almacén de Destino
                </span>
              }
              rules={[{ required: true, message: 'Debe seleccionar un almacén' }]}
              tooltip="Ubicación donde se almacenará el material"
            >
              <Select
                placeholder="Escribe para buscar almacén..."
                allowClear
                showSearch
                filterOption={(input, option) =>
                  option.children.toLowerCase().includes(input.toLowerCase())
                }
                optionFilterProp="children"
                style={{ width: '100%' }}
              >
                {almacenes.map(almacen => (
                  <Option key={almacen.id} value={almacen.id}>
                    {almacen.name}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>

          {/* Columna Derecha - Información Financiera */}
          <Col xs={24} md={12}>
            <Row gutter={[8, 0]}>
              <Col span={12}>
                <Form.Item
                  name="price"
                  label="Precio Unitario (€)"
                  rules={[
                    { 
                      type: 'number', 
                      min: 0, 
                      message: 'El precio no puede ser negativo' 
                    }
                  ]}
                  tooltip="Precio por unidad antes de aplicar descuentos"
                >
                  <InputNumber
                    min={0}
                    max={999999}
                    style={{ width: '100%' }}
                    placeholder="0.00"
                    precision={2}
                    step={0.01}
                    onChange={calcularPrecioNeto}
                    prefix={<DollarOutlined />}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
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
                        return value === '' || value === null || value === undefined 
                          ? 0 
                          : Number(value);
                      }
                    }
                  ]}
                  tooltip="Porcentaje de descuento aplicado al precio unitario"
                >
                  <InputNumber
                    min={0}
                    max={100}
                    style={{ width: '100%' }}
                    placeholder="0"
                    precision={2}
                    step={0.01}
                    onChange={calcularPrecioNeto}
                  />
                </Form.Item>
              </Col>
            </Row>

            {/* Mostrar precio neto calculado */}
            {precioNeto > 0 && (
              <div style={{ 
                padding: '8px 12px', 
                backgroundColor: '#f6ffed', 
                border: '1px solid #b7eb8f', 
                borderRadius: '6px',
                marginBottom: '16px'
              }}>
                <Text strong style={{ color: '#52c41a' }}>
                  Precio Neto: {precioNeto.toFixed(2)} €
                </Text>
              </div>
            )}

            <Form.Item
              name="supplier_id"
              label="Proveedor"
              tooltip="Proveedor del material (opcional)"
            >
              <Select
                placeholder="Escribe para buscar proveedor..."
                allowClear
                showSearch
                filterOption={(input, option) =>
                  option.children.toLowerCase().includes(input.toLowerCase())
                }
                optionFilterProp="children"
                style={{ width: '100%' }}
              >
                {proveedores.map(proveedor => (
                  <Option key={proveedor.id} value={proveedor.id}>
                    {proveedor.company || proveedor.name}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Divider />

        {/* Resumen de la operación */}
        <div style={{ 
          backgroundColor: '#fafafa', 
          padding: '16px', 
          borderRadius: '6px',
          marginBottom: '24px' 
        }}>
          <Title level={5} style={{ marginBottom: '8px' }}>
            Resumen de la Recepción
          </Title>
          <Row gutter={[16, 8]}>
            <Col span={8}>
              <Text type="secondary">Producto:</Text>
              <br />
              <Text strong>{form.getFieldValue('product_name') || 'Sin especificar'}</Text>
            </Col>
            <Col span={8}>
              <Text type="secondary">Cantidad:</Text>
              <br />
              <Text strong>{form.getFieldValue('quantity') || 0} unidades</Text>
            </Col>
            <Col span={8}>
              <Text type="secondary">Valor Total:</Text>
              <br />
              <Text strong style={{ color: '#52c41a' }}>
                {((form.getFieldValue('quantity') || 0) * precioNeto).toFixed(2)} €
              </Text>
            </Col>
          </Row>
        </div>

        {/* Botones de acción */}
        <Form.Item style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
            <Button 
              onClick={handleReset}
              disabled={loading}
            >
              Limpiar Formulario
            </Button>
            
            <Space>
              <Button 
                onClick={handleCancel}
                disabled={loading}
              >
                Cancelar
              </Button>
              <Button 
                type="primary" 
                htmlType="submit"
                loading={loading}
                icon={<ShoppingCartOutlined />}
              >
                {loading ? 'Procesando...' : 'Recibir Material'}
              </Button>
            </Space>
          </div>
        </Form.Item>
      </Form>

      {/* Nota informativa */}
      <div style={{ 
        marginTop: '16px', 
        padding: '12px', 
        backgroundColor: '#e6f7ff', 
        border: '1px solid #91d5ff',
        borderRadius: '6px'
      }}>
        <Text type="secondary" style={{ fontSize: '12px' }}>
          <WarningOutlined style={{ marginRight: '4px' }} />
          <strong>Nota:</strong> Si el producto ya existe en el inventario, se sumará la cantidad recibida al stock actual.
          Los datos de precio, almacén y proveedor se actualizarán con los nuevos valores introducidos.
        </Text>
      </div>
    </Modal>
  );
};

export default MaterialReceptionForm;