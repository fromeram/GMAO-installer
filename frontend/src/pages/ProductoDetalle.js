// src/pages/ProductoDetalle.js (Versión Mejorada - Botones optimizados)
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    Card, Typography, Button, Spin, Alert, 
    Statistic, Row, Col, Space, Divider, Tag, Empty, Table
} from 'antd';
import { 
    ArrowLeftOutlined, EditOutlined, ShoppingCartOutlined,
    SearchOutlined, TagsOutlined, ToolOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import '../styles/CommonPage.css';
import MobileLayout from '../components/MobileLayout';

// Estilos para la versión de escritorio
const desktopStyles = {
    descriptionItem: {
        display: 'flex',
        flexDirection: 'column',
        marginBottom: '16px',
        borderBottom: '1px solid #f0f0f0',
        paddingBottom: '12px',
    },
    descriptionLabel: {
        fontWeight: 'bold',
        marginBottom: '8px',
        color: '#8c8c8c'
    },
    descriptionContent: {
        wordBreak: 'break-word',
        wordWrap: 'break-word',
        whiteSpace: 'pre-wrap'
    }
};

// Estilos para la versión móvil
const mobileStyles = {
    descriptionItem: {
        display: 'flex',
        flexDirection: 'column',
        marginBottom: '8px',
        borderBottom: '1px solid #f0f0f0',
        paddingBottom: '8px',
    },
    descriptionLabel: {
        fontWeight: 'bold',
        marginBottom: '4px',
        color: '#8c8c8c',
        fontSize: '12px'
    },
    descriptionContent: {
        wordBreak: 'break-word',
        wordWrap: 'break-word',
        whiteSpace: 'pre-wrap',
        fontSize: '14px'
    }
};

const { Title, Text, Paragraph } = Typography;

const ProductoDetalle = () => {
    const { productId } = useParams();
    const navigate = useNavigate();
    const [producto, setProducto] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [usageData, setUsageData] = useState([]);
    const [loadingUsage, setLoadingUsage] = useState(false);
    const [windowWidth, setWindowWidth] = useState(window.innerWidth);

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

    // Elegir los estilos según el dispositivo
    const styles = isMobile ? mobileStyles : desktopStyles;

    useEffect(() => {
        const fetchProductoDetalle = async () => {
            try {
                setLoading(true);
                // Obtener datos del producto
                const productoData = await fetchWithAuth(`/productos/${productId}`);
                setProducto(productoData);
                
                // Obtener datos de uso del producto
                setLoadingUsage(true);
                try {
                    const usageData = await fetchWithAuth(`/inventory/${productId}/usage`);
                    setUsageData(usageData || []);
                } catch (usageError) {
                    console.error("Error fetching usage data:", usageError);
                }
                setLoadingUsage(false);

            } catch (error) {
                console.error("Error fetching product details:", error);
                setError("No se pudo cargar la información del producto. Por favor, inténtelo de nuevo.");
            } finally {
                setLoading(false);
            }
        };

        fetchProductoDetalle();
    }, [productId]);

    // Función modificada para ir directamente a la edición de este producto específico
    const handleEditProduct = () => {
        // Navegar directamente a la página de productos con estado para que abra el modal de edición
        navigate('/productos', { 
            state: { 
                editProduct: parseInt(productId),
                fromDetail: true // Añadimos un flag para indicar que venimos de la página de detalle
            } 
        });
    };

    // Función modificada para ir directamente a gestionar el stock de este producto específico
    const handleManageStock = () => {
        // Navegar directamente a la página de productos con estado para que abra el modal de edición
        // enfocado en el campo de cantidad
        navigate('/productos', { 
            state: { 
                editStock: parseInt(productId),
                fromDetail: true // Añadimos un flag para indicar que venimos de la página de detalle
            } 
        });
    };

    if (loading) {
        return (
            <div className="page-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
                <Spin size={isMobile ? "default" : "large"} tip="Cargando detalles del producto..." />
            </div>
        );
    }

    if (error) {
        return (
            <div className="page-container" style={{ padding: isMobile ? '10px' : '20px' }}>
                <Alert
                    message="Error"
                    description={error}
                    type="error"
                    showIcon
                    action={
                        <Button size={isMobile ? "small" : "middle"} type="primary" onClick={() => navigate('/productos')}>
                            Volver a Productos
                        </Button>
                    }
                />
            </div>
        );
    }

    if (!producto) {
        return (
            <div className="page-container" style={{ padding: isMobile ? '10px' : '20px' }}>
                <Alert
                    message="Producto no encontrado"
                    description="El producto solicitado no existe o ha sido eliminado."
                    type="warning"
                    showIcon
                    action={
                        <Button size={isMobile ? "small" : "middle"} type="primary" onClick={() => navigate('/productos')}>
                            Volver a Productos
                        </Button>
                    }
                />
            </div>
        );
    }

    // Determinar el estado del stock con colores
    const getStockStatus = () => {
        const stockMinimo = producto.stock_minimo || 0;
        
        if (producto.cantidad <= 0) 
            return { color: 'red', text: 'AGOTADO' };
        if (producto.cantidad <= stockMinimo * 0.5) 
            return { color: 'orange', text: 'MUY BAJO' };
        if (producto.cantidad <= stockMinimo) 
            return { color: 'gold', text: 'BAJO MÍNIMO' };
        return { color: 'green', text: 'ADECUADO' };
    };

    const stockStatus = getStockStatus();

    // Calcular precio neto después del descuento
    const precioNeto = typeof producto.precio === 'number' && typeof producto.descuento === 'number'
        ? producto.precio * (1 - producto.descuento / 100)
        : (typeof producto.precio === 'number' ? producto.precio : 0);

    // Calcular valor total del stock
    const valorTotal = precioNeto * (producto.cantidad || 0);

    // Definir columnas para la tabla de uso (versión escritorio)
    const desktopUsageColumns = [
        {
            title: 'ID',
            dataIndex: ['machine', 'id'],
            key: 'id',
            width: 70,
        },
        {
            title: 'Máquina',
            dataIndex: ['machine', 'nombre'],
            key: 'nombre',
            render: (text) => (
                <div style={{ wordBreak: 'break-word', maxWidth: '300px' }}>
                    {text}
                </div>
            )
        },
        {
            title: 'Cantidad',
            dataIndex: 'quantity',
            key: 'quantity',
            width: 100,
            align: 'center',
        },
        {
            title: 'Acciones',
            key: 'actions',
            width: 100,
            align: 'center',
            render: (_, record) => (
                <Button
                    type="primary"
                    size="small"
                    icon={<ToolOutlined />}
                    onClick={() => navigate(`/maquinas/${record.machine.id}`)}
                >
                    Ver
                </Button>
            ),
        },
    ];

    // Definir columnas para la tabla de uso (versión móvil)
    const mobileUsageColumns = [
        {
            title: 'Máquina',
            dataIndex: ['machine', 'nombre'],
            key: 'nombre',
            render: (text, record) => (
                <div>
                    <div style={{ wordBreak: 'break-word', fontSize: '14px' }}>
                        {text}
                    </div>
                    <div style={{ fontSize: '12px', color: '#888' }}>
                        ID: {record.machine?.id} | Cant.: {record.quantity}
                    </div>
                </div>
            )
        },
        {
            title: '',
            key: 'actions',
            width: 50,
            align: 'center',
            render: (_, record) => (
                <Button
                    type="primary"
                    size="small"
                    icon={<ToolOutlined />}
                    onClick={() => navigate(`/maquinas/${record.machine.id}`)}
                />
            ),
        },
    ];

    // Versión móvil del producto
    if (isMobile) {
        return (
            <MobileLayout title={`Producto: ${producto.nombre.substring(0, 20)}${producto.nombre.length > 20 ? '...' : ''}`}>
                <div style={{ padding: '0 5px' }}>
                    {/* Información básica */}
                    <Card size="small" bodyStyle={{ padding: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '5px' }}>
                            <div>
                                <Text strong style={{ fontSize: '16px' }}>{producto.nombre}</Text>
                            </div>
                            <Tag color={stockStatus.color}>{stockStatus.text}</Tag>
                        </div>
                        
                        <Divider style={{ margin: '8px 0' }} />
                        
                        {/* ID y Almacén */}
                        <div style={styles.descriptionItem}>
                            <div style={styles.descriptionLabel}>ID / Almacén</div>
                            <div style={styles.descriptionContent}>
                                {producto.id} / {producto.almacen || 'No asignado'}
                            </div>
                        </div>
                        
                        {/* Proveedor */}
                        <div style={styles.descriptionItem}>
                            <div style={styles.descriptionLabel}>Proveedor</div>
                            <div style={styles.descriptionContent}>
                                {producto.proveedor || 'No especificado'}
                            </div>
                        </div>
                        
                        {/* Precios */}
                        <Row gutter={[8, 8]}>
                            <Col span={8}>
                                <div style={styles.descriptionItem}>
                                    <div style={styles.descriptionLabel}>Precio</div>
                                    <div style={styles.descriptionContent}>
                                        {typeof producto.precio === 'number' ? `${producto.precio.toFixed(2)}€` : '0.00€'}
                                    </div>
                                </div>
                            </Col>
                            <Col span={8}>
                                <div style={styles.descriptionItem}>
                                    <div style={styles.descriptionLabel}>Dto.</div>
                                    <div style={styles.descriptionContent}>
                                        {producto.descuento ? `${producto.descuento}%` : '0%'}
                                    </div>
                                </div>
                            </Col>
                            <Col span={8}>
                                <div style={styles.descriptionItem}>
                                    <div style={styles.descriptionLabel}>Neto</div>
                                    <div style={styles.descriptionContent}>
                                        {`${precioNeto.toFixed(2)}€`}
                                    </div>
                                </div>
                            </Col>
                        </Row>
                    </Card>
                    
                    {/* Stock */}
                    <Card size="small" bodyStyle={{ padding: '8px' }} style={{ marginTop: '8px' }}>
                        <Row gutter={[8, 8]}>
                            <Col span={24}>
                                <Statistic
                                    title="Cantidad Disponible"
                                    value={producto.cantidad}
                                    valueStyle={{ color: stockStatus.color, fontSize: '24px' }}
                                    prefix={<TagsOutlined />}
                                />
                            </Col>
                            <Col span={12}>
                                <Statistic
                                    title="Stock Mínimo"
                                    value={producto.stock_minimo || 0}
                                    valueStyle={{ fontSize: '16px' }}
                                />
                            </Col>
                            <Col span={12}>
                                <Statistic
                                    title="Diferencia"
                                    value={producto.cantidad - (producto.stock_minimo || 0)}
                                    valueStyle={{ 
                                        color: (producto.cantidad - (producto.stock_minimo || 0)) < 0 ? 'red' : 'green',
                                        fontSize: '16px'
                                    }}
                                    prefix={(producto.cantidad - (producto.stock_minimo || 0)) < 0 ? '-' : '+'}
                                />
                            </Col>
                        </Row>
                        
                        <Divider style={{ margin: '8px 0' }} />
                        
                        {/* Un solo botón para gestionar stock */}
                        <Button 
                            type="primary" 
                            block 
                            icon={<ShoppingCartOutlined />}
                            onClick={handleManageStock}
                            size="middle"
                        >
                            Gestionar Stock
                        </Button>
                    </Card>
                    
                    {/* Uso en Máquinas */}
                    <Card 
                        title="Uso en Máquinas" 
                        size="small" 
                        style={{ marginTop: '8px' }}
                        loading={loadingUsage}
                        bordered={false}
                    >
                        {usageData.length > 0 ? (
                            <Table
                                dataSource={usageData}
                                columns={mobileUsageColumns}
                                rowKey={(record) => `${record.machine?.id || 'unknown'}-${record.quantity}`}
                                pagination={usageData.length > 5 ? { pageSize: 5, size: "small" } : false}
                                size="small"
                                scroll={{ x: '100%' }}
                            />
                        ) : (
                            <Empty 
                                description="Sin asociaciones" 
                                image={Empty.PRESENTED_IMAGE_SIMPLE} 
                            />
                        )}
                    </Card>
                    
                    {/* Acciones */}
                    <div style={{ marginTop: '10px', display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                        <Button 
                            style={{ flex: 1 }}
                            icon={<ArrowLeftOutlined />}
                            onClick={() => navigate(-1)}
                        >
                            Volver
                        </Button>
                        <Button 
                            type="primary"
                            style={{ flex: 1 }}
                            icon={<EditOutlined />}
                            onClick={handleEditProduct}
                        >
                            Editar
                        </Button>
                    </div>
                </div>
            </MobileLayout>
        );
    }

    // Versión de escritorio
    return (
        <div className="page-container">
            <div className="page-header">
                <Space>
                    <Button 
                        icon={<ArrowLeftOutlined />} 
                        onClick={() => navigate(-1)}
                    >
                        Volver
                    </Button>
                    <Title level={2} className="page-title" style={{ margin: 0 }}>
                        Detalle de Producto
                    </Title>
                </Space>
                <Space>
                    {/* Un solo botón para editar en vez de dos separados */}
                    <Button 
                        type="primary"
                        icon={<EditOutlined />}
                        onClick={handleEditProduct}
                    >
                        Editar Información & Stock
                    </Button>
                </Space>
            </div>

            <Row gutter={[16, 16]}>
                {/* Columna con información del producto */}
                <Col xs={24} lg={16}>
                    <Card 
                        title={
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <div style={{ flexShrink: 0 }}>Información del Producto</div>
                                <Tag color={stockStatus.color} style={{ marginLeft: 'auto' }}>
                                    {stockStatus.text}
                                </Tag>
                            </div>
                        } 
                        bordered={false}
                    >
                        {/* Información del producto con layout optimizado para textos largos */}
                        <div>
                            {/* ID del producto */}
                            <div style={styles.descriptionItem}>
                                <div style={styles.descriptionLabel}>ID</div>
                                <div style={styles.descriptionContent}>{producto.id}</div>
                            </div>
                            
                            {/* Nombre del producto - texto largo */}
                            <div style={styles.descriptionItem}>
                                <div style={styles.descriptionLabel}>Nombre del Producto</div>
                                <div style={styles.descriptionContent}>
                                    <Text>{producto.nombre}</Text>
                                </div>
                            </div>
                            
                            {/* Almacén */}
                            <div style={styles.descriptionItem}>
                                <div style={styles.descriptionLabel}>Almacén</div>
                                <div style={styles.descriptionContent}>
                                    {producto.almacen || 'No asignado'}
                                </div>
                            </div>
                            
                            {/* Proveedor - texto largo */}
                            <div style={styles.descriptionItem}>
                                <div style={styles.descriptionLabel}>Proveedor</div>
                                <div style={styles.descriptionContent}>
                                    <Text>{producto.proveedor || 'No especificado'}</Text>
                                </div>
                            </div>
                            
                            {/* Row con información de precio */}
                            <Row gutter={[16, 16]}>
                                <Col xs={24} md={8}>
                                    <div style={styles.descriptionItem}>
                                        <div style={styles.descriptionLabel}>Precio Base</div>
                                        <div style={styles.descriptionContent}>
                                            {typeof producto.precio === 'number' 
                                                ? `${producto.precio.toFixed(2)} €` 
                                                : '0.00 €'}
                                        </div>
                                    </div>
                                </Col>
                                <Col xs={24} md={8}>
                                    <div style={styles.descriptionItem}>
                                        <div style={styles.descriptionLabel}>Descuento</div>
                                        <div style={styles.descriptionContent}>
                                            {producto.descuento 
                                                ? `${producto.descuento}%` 
                                                : '0%'}
                                        </div>
                                    </div>
                                </Col>
                                <Col xs={24} md={8}>
                                    <div style={styles.descriptionItem}>
                                        <div style={styles.descriptionLabel}>Precio Neto</div>
                                        <div style={styles.descriptionContent}>
                                            {`${precioNeto.toFixed(2)} €`}
                                        </div>
                                    </div>
                                </Col>
                            </Row>
                            
                            {/* Row con información de stock */}
                            <Row gutter={[16, 16]}>
                                <Col xs={24} md={8}>
                                    <div style={styles.descriptionItem}>
                                        <div style={styles.descriptionLabel}>Stock Mínimo</div>
                                        <div style={styles.descriptionContent}>
                                            {producto.stock_minimo || 0}
                                        </div>
                                    </div>
                                </Col>
                                <Col xs={24} md={8}>
                                    <div style={styles.descriptionItem}>
                                        <div style={styles.descriptionLabel}>Stock Actual</div>
                                        <div style={styles.descriptionContent}>
                                            <Text style={{ color: stockStatus.color, fontWeight: 'bold' }}>
                                                {producto.cantidad}
                                            </Text>
                                        </div>
                                    </div>
                                </Col>
                                <Col xs={24} md={8}>
                                    <div style={styles.descriptionItem}>
                                        <div style={styles.descriptionLabel}>Valor Total</div>
                                        <div style={styles.descriptionContent}>
                                            {`${valorTotal.toFixed(2)} €`}
                                        </div>
                                    </div>
                                </Col>
                            </Row>
                        </div>
                    </Card>
                </Col>
                
                {/* Columna con estadísticas */}
                <Col xs={24} lg={8}>
                    <Card 
                        title="Estado del Inventario" 
                        bordered={false}
                    >
                        <Statistic
                            title="Cantidad Disponible"
                            value={producto.cantidad}
                            valueStyle={{ color: stockStatus.color, fontSize: '36px' }}
                            prefix={<TagsOutlined />}
                        />
                        
                        <Divider />
                        
                        <Row gutter={[16, 16]}>
                            <Col span={12}>
                                <Statistic
                                    title="Stock Mínimo"
                                    value={producto.stock_minimo || 0}
                                    valueStyle={{ fontSize: '24px' }}
                                />
                            </Col>
                            <Col span={12}>
                                <Statistic
                                    title="Diferencia"
                                    value={producto.cantidad - (producto.stock_minimo || 0)}
                                    valueStyle={{ 
                                        color: (producto.cantidad - (producto.stock_minimo || 0)) < 0 ? 'red' : 'green',
                                        fontSize: '24px'
                                    }}
                                    prefix={(producto.cantidad - (producto.stock_minimo || 0)) < 0 ? '-' : '+'}
                                />
                            </Col>
                        </Row>
                        
                        <Divider />
                        
                        {/* Un solo botón para gestionar stock */}
                        <Button 
                            type="primary" 
                            block 
                            icon={<ShoppingCartOutlined />}
                            onClick={handleManageStock}
                            size="large"
                        >
                            Gestionar Stock
                        </Button>
                    </Card>
                </Col>
            </Row>

            <Divider orientation="left" style={{ marginTop: '24px' }}>
                Uso en Máquinas
            </Divider>
            
            <Card
                loading={loadingUsage}
                bordered={false}
            >
                {usageData.length > 0 ? (
                    <Table
                        dataSource={usageData}
                        columns={desktopUsageColumns}
                        rowKey={(record) => `${record.machine?.id || 'unknown'}-${record.quantity}`}
                        pagination={usageData.length > 10 ? { pageSize: 10 } : false}
                        size="middle"
                        scroll={{ x: 'max-content' }}
                    />
                ) : (
                    <Empty 
                        description="Este producto no está asociado a ninguna máquina" 
                        image={Empty.PRESENTED_IMAGE_SIMPLE} 
                    />
                )}
            </Card>
        </div>
    );
};

export default ProductoDetalle;