// src/pages/LowStockInventory.js - Con Ordenamiento Alfabético y Paginación Corregida
import React, { useState, useEffect } from 'react';
import {
    Typography, Table, Card, Space, Tag, Alert, Button, Spin, Tooltip, Row, Col, Statistic
} from 'antd';
import { WarningOutlined, SyncOutlined, ShoppingCartOutlined, SearchOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

const LowStockInventory = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lowStockItems, setLowStockItems] = useState([]);
    const navigate = useNavigate();

    // 🔧 ESTADO PARA PAGINACIÓN
    const [pagination, setPagination] = useState({
        current: 1,
        pageSize: 10,
        showSizeChanger: true,
        showQuickJumper: true,
        pageSizeOptions: ['10', '20', '30', '50'],
        showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} productos`,
    });

    // 🔧 FUNCIÓN PARA MANEJAR CAMBIOS EN LA PAGINACIÓN
    const handleTableChange = (pag, filters, sorter) => {
        console.log('Cambio en paginación bajo stock:', pag);
        setPagination({
            ...pagination,
            current: pag.current,
            pageSize: pag.pageSize,
        });
    };

    // Función para cargar datos
    const loadData = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchWithAuth('/inventory/low-stock');
            
            // Ordenar alfabéticamente por nombre del producto
            const sortedData = (data || []).sort((a, b) => 
                (a.product_name || '').localeCompare(b.product_name || '', 'es', { sensitivity: 'base' })
            );
            
            setLowStockItems(sortedData);
        } catch (err) {
            console.error("Error cargando datos de bajo stock:", err);
            setError(`Error: ${err.message || 'Desconocido'}`);
        } finally {
            setLoading(false);
        }
    };

    // Cargar datos al montar
    useEffect(() => {
        loadData();
    }, []);

    // Columnas de la tabla
    const columns = [
        {
            title: 'Producto',
            dataIndex: 'product_name',
            key: 'product_name',
            defaultSortOrder: 'ascend',
            sorter: (a, b) => (a.product_name || '').localeCompare(b.product_name || '', 'es', { sensitivity: 'base' }),
            render: (text, record) => (
                <span>
                    {text}
                    {record.quantity <= 0 && (
                        <Tag color="red" style={{ marginLeft: 8 }}>
                            AGOTADO
                        </Tag>
                    )}
                </span>
            )
        },
        {
            title: 'Stock Actual',
            dataIndex: 'quantity',
            key: 'quantity',
            sorter: (a, b) => a.quantity - b.quantity,
            render: (quantity, record) => {
                // Calcular porcentaje de stock
                const percentage = record.stock_minimo > 0 
                    ? (quantity / record.stock_minimo) * 100 
                    : 100;
                
                // Determinar color según porcentaje
                let color = 'green';
                if (percentage <= 0) color = 'red';
                else if (percentage <= 50) color = 'orange';
                else if (percentage <= 80) color = 'gold';
                
                return (
                    <Tag color={color}>
                        {quantity}
                    </Tag>
                );
            }
        },
        {
            title: 'Stock Mínimo',
            dataIndex: 'stock_minimo',
            key: 'stock_minimo'
        },
        {
            title: 'Almacén',
            dataIndex: 'almacen',
            key: 'almacen',
            render: (_, record) => record.almacen?.name || '-'
        },
        {
            title: 'Proveedor',
            dataIndex: 'proveedor',
            key: 'proveedor'
        },
        {
            title: 'Acciones',
            key: 'action',
            render: (_, record) => (
                <Space size="small">
                    <Tooltip title="Ver detalles del producto">
                        <Button 
                            type="primary" 
                            size="small" 
                            onClick={() => navigate(`/productos/${record.id}`)}
                            icon={<SearchOutlined />}
                        >
                            Detalles
                        </Button>
                    </Tooltip>
                </Space>
            )
        }
    ];

    return (
        <div className="page-container">
            <Row gutter={[16, 16]}>
                <Col span={24}>
                    <div className="page-header">
                        <Title level={2} className="page-title">
                            <WarningOutlined style={{ color: '#faad14', marginRight: 8 }} /> 
                            Productos con Bajo Stock
                        </Title>
                        <Button 
                            icon={<SyncOutlined />} 
                            onClick={loadData}
                            loading={loading}
                        >
                            Actualizar
                        </Button>
                    </div>
                </Col>

                <Col span={24}>
                    {error && (
                        <Alert 
                            message="Error al cargar datos" 
                            description={error} 
                            type="error" 
                            showIcon 
                            closable 
                            style={{ marginBottom: 16 }}
                        />
                    )}
                </Col>

                <Col md={8} sm={12} xs={24}>
                    <Card>
                        <Statistic 
                            title="Productos Bajo Mínimos" 
                            value={lowStockItems.length} 
                            valueStyle={{ color: lowStockItems.length > 0 ? '#ff4d4f' : '#52c41a' }}
                            prefix={<WarningOutlined />}
                        />
                    </Card>
                </Col>

                <Col span={24}>
                    {/* 🔧 TABLA CON PAGINACIÓN CORREGIDA */}
                    <Card>
                        <Spin spinning={loading}>
                            <Table 
                                columns={columns} 
                                dataSource={lowStockItems.map(item => ({ ...item, key: item.id }))} 
                                pagination={pagination}
                                onChange={handleTableChange}
                                locale={{ emptyText: 'No hay productos bajo mínimos' }}
                            />
                        </Spin>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default LowStockInventory;