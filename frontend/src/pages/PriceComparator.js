// src/pages/PriceComparator.js - REEMPLAZA COMPLETAMENTE EL ARCHIVO EXISTENTE
import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Card, 
  Table, 
  Tag, 
  Space, 
  Alert, 
  Spin, 
  Button, 
  Statistic, 
  Row, 
  Col,
  Divider,
  Tooltip,
  Badge
} from 'antd';
import { 
  ShoppingCartOutlined, 
  DollarOutlined, 
  PercentageOutlined,
  TrophyOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

const PriceComparator = () => {
  // --- Hooks de autenticación y navegación ---
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  // --- Estados principales ---
  const [loading, setLoading] = useState(true);
  const [productsWithMultipleSuppliers, setProductsWithMultipleSuppliers] = useState([]);
  const [error, setError] = useState(null);
  const [isAuthorized, setIsAuthorized] = useState(false);

  // --- Verificación de Permisos ---
  useEffect(() => {
    const userRole = currentUser?.role?.nombre || (typeof currentUser?.role === 'string' ? currentUser.role : null);

    console.log('🔍 PriceComparator - Verificando permisos para usuario:', {
      currentUser: currentUser?.username,
      userRole,
      hasRole: !!currentUser?.role
    });

    // ✅ CORREGIDO: Incluir "Jefe de Mantenimiento" (con "de")
    const authorizedRoles = ['Administrador', 'Jefe de Mantenimiento', 'Calidad', 'Contabilidad'];
    
    if (authorizedRoles.includes(userRole)) {
      console.log('✅ Usuario autorizado para PriceComparator');
      setIsAuthorized(true);
    } else if (currentUser) {
      console.log('❌ Usuario NO autorizado para PriceComparator');
      setIsAuthorized(false);
    }
    
    setLoading(false);
  }, [currentUser]);

  // Cargar datos cuando el usuario está autorizado
  useEffect(() => {
    if (isAuthorized) {
      fetchProductsWithMultipleSuppliers();
    }
  }, [isAuthorized]);

  const fetchProductsWithMultipleSuppliers = async () => {
    if (!isAuthorized) return;
    
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔄 Cargando productos con múltiples proveedores...');
      
      // Obtener todos los precios de proveedores
      const allPrices = await fetchWithAuth('/supplier-prices/all');
      console.log('✅ Precios obtenidos:', allPrices?.length || 0);
      
      if (!allPrices || allPrices.length === 0) {
        setProductsWithMultipleSuppliers([]);
        return;
      }
      
      // Agrupar por nombre de producto
      const productGroups = {};
      
      allPrices.forEach(price => {
        const productName = price.product_name;
        
        if (!productGroups[productName]) {
          productGroups[productName] = [];
        }
        
        productGroups[productName].push(price);
      });
      
      // Filtrar solo productos con múltiples proveedores
      const multiSupplierProducts = Object.entries(productGroups)
        .filter(([productName, prices]) => prices.length > 1)
        .map(([productName, prices]) => {
          // Ordenar precios de menor a mayor
          const sortedPrices = prices.sort((a, b) => {
            const priceA = parseFloat(a.price) * (1 - parseFloat(a.discount || 0) / 100);
            const priceB = parseFloat(b.price) * (1 - parseFloat(b.discount || 0) / 100);
            return priceA - priceB;
          });
          
          const lowestPrice = parseFloat(sortedPrices[0].price) * (1 - parseFloat(sortedPrices[0].discount || 0) / 100);
          const highestPrice = parseFloat(sortedPrices[sortedPrices.length - 1].price) * (1 - parseFloat(sortedPrices[sortedPrices.length - 1].discount || 0) / 100);
          const savingsAmount = highestPrice - lowestPrice;
          const savingsPercentage = ((savingsAmount / highestPrice) * 100).toFixed(1);
          
          return {
            key: productName,
            productName,
            supplierCount: prices.length,
            prices: sortedPrices,
            lowestPrice,
            highestPrice,
            savingsAmount,
            savingsPercentage: parseFloat(savingsPercentage),
            bestSupplier: sortedPrices[0].supplier?.company || sortedPrices[0].supplier?.name || 'N/A'
          };
        })
        .sort((a, b) => b.savingsPercentage - a.savingsPercentage); // Ordenar por mayor ahorro
      
      console.log('✅ Productos con múltiples proveedores:', multiSupplierProducts.length);
      setProductsWithMultipleSuppliers(multiSupplierProducts);
      
    } catch (err) {
      console.error('❌ Error obteniendo productos con múltiples proveedores:', err);
      setError('Error al cargar los productos con múltiples proveedores: ' + (err.message || 'Error desconocido'));
    } finally {
      setLoading(false);
    }
  };

  const renderPriceDetails = (prices) => {
    return (
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        {prices.map((price, index) => {
          const finalPrice = parseFloat(price.price) * (1 - parseFloat(price.discount || 0) / 100);
          const isLowest = index === 0;
          const isHighest = index === prices.length - 1 && prices.length > 1;
          
          return (
            <div key={price.id} style={{ 
              padding: '8px', 
              border: `1px solid ${isLowest ? '#52c41a' : isHighest ? '#ff4d4f' : '#d9d9d9'}`,
              borderRadius: '4px',
              backgroundColor: isLowest ? '#f6ffed' : isHighest ? '#fff2f0' : '#fafafa'
            }}>
              <Space direction="vertical" size={2}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text strong style={{ color: isLowest ? '#52c41a' : isHighest ? '#ff4d4f' : 'inherit' }}>
                    {price.supplier?.company || price.supplier?.name || 'Proveedor N/A'}
                  </Text>
                  {isLowest && <Tag color="green" icon={<TrophyOutlined />}>Mejor Precio</Tag>}
                  {isHighest && prices.length > 1 && <Tag color="red">Más Caro</Tag>}
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Space>
                    <Text>Precio: <Text strong>€{parseFloat(price.price).toFixed(2)}</Text></Text>
                    {price.discount > 0 && (
                      <Tag color="orange" icon={<PercentageOutlined />}>
                        -{price.discount}%
                      </Tag>
                    )}
                  </Space>
                  <Text strong style={{ color: isLowest ? '#52c41a' : undefined }}>
                    Final: €{finalPrice.toFixed(2)}
                  </Text>
                </div>
                
                {price.warehouse?.name && (
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    Almacén: {price.warehouse.name}
                  </Text>
                )}
              </Space>
            </div>
          );
        })}
      </Space>
    );
  };

  const columns = [
    {
      title: 'Producto',
      dataIndex: 'productName',
      key: 'productName',
      width: '25%',
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: (
        <Space>
          Proveedores
          <Tooltip title="Número de proveedores que ofrecen este producto">
            <InfoCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'supplierCount',
      key: 'supplierCount',
      width: '10%',
      align: 'center',
      render: (count) => <Badge count={count} style={{ backgroundColor: '#1890ff' }} />
    },
    {
      title: 'Mejor Proveedor',
      dataIndex: 'bestSupplier',
      key: 'bestSupplier',
      width: '15%',
      render: (text) => <Tag color="green">{text}</Tag>
    },
    {
      title: 'Ahorro Potencial',
      key: 'savings',
      width: '15%',
      align: 'center',
      render: (_, record) => (
        <Space direction="vertical" size={0} style={{ textAlign: 'center' }}>
          <Text strong style={{ color: '#52c41a' }}>
            €{record.savingsAmount.toFixed(2)}
          </Text>
          <Text style={{ fontSize: '12px', color: '#52c41a' }}>
            ({record.savingsPercentage}%)
          </Text>
        </Space>
      ),
      sorter: (a, b) => a.savingsPercentage - b.savingsPercentage
    },
    {
      title: 'Rango de Precios',
      key: 'priceRange',
      width: '15%',
      align: 'center',
      render: (_, record) => (
        <Space direction="vertical" size={0} style={{ textAlign: 'center' }}>
          <Text style={{ color: '#52c41a' }}>€{record.lowestPrice.toFixed(2)}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>a</Text>
          <Text style={{ color: '#ff4d4f' }}>€{record.highestPrice.toFixed(2)}</Text>
        </Space>
      )
    },
    {
      title: 'Detalles de Precios',
      key: 'details',
      width: '20%',
      render: (_, record) => renderPriceDetails(record.prices)
    }
  ];

  const totalProducts = productsWithMultipleSuppliers.length;
  const totalSavings = productsWithMultipleSuppliers.reduce((sum, product) => sum + product.savingsAmount, 0);
  const avgSavingsPercentage = totalProducts > 0 
    ? (productsWithMultipleSuppliers.reduce((sum, product) => sum + product.savingsPercentage, 0) / totalProducts).toFixed(1)
    : 0;

  // Renderizado para permisos
  if (!isAuthorized && currentUser) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Acceso Denegado"
          description="No tienes permisos para acceder al comparador de precios. Solo usuarios con roles de Administrador, Jefe de Mantenimiento, Calidad o Contabilidad pueden acceder."
          type="error"
          showIcon
          action={
            <Button type="primary" onClick={() => navigate('/')}>
              Volver al Dashboard
            </Button>
          }
        />
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: '20px' }}>
          <Text>Cargando productos con múltiples proveedores...</Text>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" danger onClick={fetchProductsWithMultipleSuppliers}>
              Reintentar
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ margin: 0 }}>
          <ShoppingCartOutlined style={{ marginRight: '8px' }} />
          Comparador de Precios - Productos con Múltiples Proveedores
        </Title>
        <Text type="secondary">
          Vista rápida de productos con opciones de múltiples proveedores para optimizar compras
        </Text>
      </div>

      {/* Estadísticas Generales */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Productos con Múltiples Proveedores"
              value={totalProducts}
              prefix={<ShoppingCartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Ahorro Total Potencial"
              value={totalSavings}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="€"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="% Promedio de Ahorro"
              value={avgSavingsPercentage}
              precision={1}
              prefix={<PercentageOutlined />}
              suffix="%"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Mejor Oportunidad"
              value={totalProducts > 0 ? productsWithMultipleSuppliers[0]?.savingsPercentage : 0}
              precision={1}
              prefix={<TrophyOutlined />}
              suffix="% ahorro"
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {totalProducts === 0 ? (
        <Card>
          <Alert
            message="No hay productos con múltiples proveedores"
            description="Actualmente no hay productos que tengan precios de múltiples proveedores en el sistema. Añade más precios de proveedores para ver comparaciones."
            type="info"
            showIcon
          />
        </Card>
      ) : (
        <>
          <Alert
            message={`Se encontraron ${totalProducts} productos con múltiples proveedores`}
            description="Los productos están ordenados por mayor potencial de ahorro. Los precios incluyen descuentos aplicados."
            type="success"
            showIcon
            style={{ marginBottom: '16px' }}
          />

          <Card>
            <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space>
                <Button 
                  icon={<ShoppingCartOutlined />} 
                  onClick={fetchProductsWithMultipleSuppliers}
                  loading={loading}
                >
                  Actualizar
                </Button>
              </Space>
              <Text type="secondary">
                Última actualización: {new Date().toLocaleString()}
              </Text>
            </div>

            <Table
              columns={columns}
              dataSource={productsWithMultipleSuppliers}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => 
                  `${range[0]}-${range[1]} de ${total} productos`
              }}
              scroll={{ x: 1200 }}
              size="middle"
            />
          </Card>
        </>
      )}
    </div>
  );
};

export default PriceComparator;