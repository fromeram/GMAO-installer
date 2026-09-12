import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    Card, Button, Table, Typography, message, 
    Form, Input, InputNumber, Select, Divider, 
    Space, Tabs, Modal, Popconfirm 
} from 'antd';
import { fetchWithAuth } from '../apiConfig';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;

const DocumentVerification = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [document, setDocument] = useState(null);
    const [extractedData, setExtractedData] = useState(null);
    const [warehouses, setWarehouses] = useState([]);
    const [currentItem, setCurrentItem] = useState(null);
    const [itemModalVisible, setItemModalVisible] = useState(false);
    const [itemForm] = Form.useForm();
    const [processedItems, setProcessedItems] = useState([]);

    useEffect(() => {
        fetchDocumentData();
    }, [id]);

    const fetchDocumentData = async () => {
        try {
            setLoading(true);
            const response = await fetchWithAuth(`/documents/${id}/data`);
            setDocument(response.document);
            setExtractedData(response.extracted_data);
            setWarehouses(response.warehouses || []);
        } catch (error) {
            message.error('Error al cargar datos del documento');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleProcessItem = (item) => {
        setCurrentItem(item);
        
        // Preparar datos en el formulario dependiendo del tipo de documento
        if (document.type === 'albaran') {
            itemForm.setFieldsValue({
                description: item.description,
                quantity: item.quantity,
                unit_price: item.unit_price,
                warehouse_id: warehouses.length > 0 ? warehouses[0].id : null
            });
        } else if (document.type === 'parte_trabajo') {
            itemForm.setFieldsValue({
                machine: item.machine,
                details: item.details,
                operator: item.operator
            });
        }
        
        setItemModalVisible(true);
    };

    const handleItemSubmit = async (values) => {
        try {
            setLoading(true);
            
            // Añadir ID del item para rastreo (si tiene)
            const itemData = { ...values, originalId: currentItem.id || null };
            
            const response = await fetchWithAuth(`/documents/${id}/confirm-item`, {
                method: 'POST',
                body: JSON.stringify(itemData)
            });
            
            if (response.success) {
                message.success(response.message);
                
                // Marcar item como procesado y cerrrar modal
                setProcessedItems([...processedItems, currentItem]);
                setItemModalVisible(false);
                
                // Si todos los items han sido procesados, preguntar si desea completar el documento
                const allItemsProcessed = checkAllItemsProcessed();
                if (allItemsProcessed) {
                    Modal.confirm({
                        title: '¿Completar documento?',
                        content: 'Todos los elementos han sido procesados. ¿Desea marcar el documento como completo?',
                        onOk: () => handleCompleteDocument(),
                        okText: 'Completar',
                        cancelText: 'Más tarde'
                    });
                }
            } else {
                message.error('Error al procesar elemento');
            }
        } catch (error) {
            message.error('Error de comunicación con el servidor');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleCompleteDocument = async () => {
        try {
            setLoading(true);
            const response = await fetchWithAuth(`/documents/${id}/complete`, {
                method: 'POST'
            });
            
            if (response.success) {
                message.success('Documento completado correctamente');
                navigate('/documentos');
            } else {
                message.error('Error al completar documento');
            }
        } catch (error) {
            message.error('Error de comunicación con el servidor');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const checkAllItemsProcessed = () => {
        if (document.type === 'albaran' && extractedData?.products) {
            return processedItems.length >= extractedData.products.length;
        } else if (document.type === 'parte_trabajo' && extractedData?.work_orders) {
            return processedItems.length >= extractedData.work_orders.length;
        }
        return false;
    };

    const renderItemTable = () => {
        if (document.type === 'albaran' && extractedData?.products) {
            const columns = [
                { title: 'Código', dataIndex: 'code', key: 'code' },
                { title: 'Descripción', dataIndex: 'description', key: 'description' },
                { title: 'Cantidad', dataIndex: 'quantity', key: 'quantity' },
                { title: 'Precio', dataIndex: 'unit_price', key: 'unit_price',
                  render: price => `${price}€` },
                { title: 'Total', dataIndex: 'total', key: 'total',
                  render: total => `${total}€` },
                { title: 'Estado', key: 'status',
                  render: (_, record) => {
                      const processed = processedItems.some(item => 
                          item.description === record.description);
                      return processed ? 
                          <Text type="success">Procesado</Text> : 
                          <Text type="warning">Pendiente</Text>;
                  }
                },
                { title: 'Acciones', key: 'actions',
                  render: (_, record) => {
                      const processed = processedItems.some(item => 
                          item.description === record.description);
                      return processed ? 
                          <Button type="default" disabled>Procesado</Button> : 
                          <Button type="primary" onClick={() => handleProcessItem(record)}>
                              Procesar
                          </Button>;
                  }
                }
            ];
            
            return (
                <Table 
                    columns={columns} 
                    dataSource={extractedData.products}
                    rowKey="description"
                    pagination={false}
                />
            );
            
        } else if (document.type === 'parte_trabajo' && extractedData?.work_orders) {
            const columns = [
                { title: 'Máquina', dataIndex: 'machine', key: 'machine' },
                { title: 'Descripción', dataIndex: 'details', key: 'details' },
                { title: 'Operario', dataIndex: 'operator', key: 'operator' },
                { title: 'Estado', key: 'status',
                  render: (_, record) => {
                      const processed = processedItems.some(item => 
                          item.machine === record.machine && item.details === record.details);
                      return processed ? 
                          <Text type="success">Procesado</Text> : 
                          <Text type="warning">Pendiente</Text>;
                  }
                },
                { title: 'Acciones', key: 'actions',
                  render: (_, record) => {
                      const processed = processedItems.some(item => 
                          item.machine === record.machine && item.details === record.details);
                      return processed ? 
                          <Button type="default" disabled>Procesado</Button> : 
                          <Button type="primary" onClick={() => handleProcessItem(record)}>
                              Procesar
                          </Button>;
                  }
                }
            ];
            
            return (
                <Table 
                    columns={columns} 
                    dataSource={extractedData.work_orders}
                    rowKey={record => `${record.machine}-${record.details}`}
                    pagination={false}
                />
            );
        }
        
        return <div>No hay datos para mostrar</div>;
    };

    const renderItemModal = () => {
        if (!currentItem) return null;
        
        if (document.type === 'albaran') {
            return (
                <Modal
                    title="Procesar Producto"
                    open={itemModalVisible}
                    onCancel={() => setItemModalVisible(false)}
                    footer={null}
                >
                    <Form
                        form={itemForm}
                        layout="vertical"
                        onFinish={handleItemSubmit}
                    >
                        <Form.Item name="description" label="Descripción del Producto">
                            <Input />
                        </Form.Item>
                        <Form.Item name="quantity" label="Cantidad" rules={[{ required: true }]}>
                            <InputNumber min={0} />
                        </Form.Item>
                        <Form.Item name="unit_price" label="Precio Unitario">
                            <InputNumber 
                                min={0} 
                                formatter={value => `${value}€`}
                                parser={value => value.replace('€', '')}
                            />
                        </Form.Item>
                        <Form.Item 
                            name="warehouse_id" 
                            label="Almacén Destino"
                            rules={[{ required: true, message: 'Seleccione un almacén' }]}
                        >
                            <Select placeholder="Seleccione almacén">
                                {warehouses.map(warehouse => (
                                    <Option key={warehouse.id} value={warehouse.id}>
                                        {warehouse.name}
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                        
                        <Form.Item>
                            <Space>
                                <Button type="primary" htmlType="submit">
                                    Confirmar
                                </Button>
                                <Button onClick={() => setItemModalVisible(false)}>
                                    Cancelar
                                </Button>
                            </Space>
                        </Form.Item>
                    </Form>
                </Modal>
            );
        } else if (document.type === 'parte_trabajo') {
            return (
                <Modal
                    title="Procesar Orden de Trabajo"
                    open={itemModalVisible}
                    onCancel={() => setItemModalVisible(false)}
                    footer={null}
                >
                    <Form
                        form={itemForm}
                        layout="vertical"
                        onFinish={handleItemSubmit}
                    >
                        <Form.Item name="machine" label="Máquina">
                            <Input />
                        </Form.Item>
                        <Form.Item name="details" label="Descripción del Trabajo">
                            <Input.TextArea rows={4} />
                        </Form.Item>
                        <Form.Item name="operator" label="Operario">
                            <Input />
                        </Form.Item>
                        
                        <Form.Item>
                            <Space>
                                <Button type="primary" htmlType="submit">
                                    Crear Orden de Trabajo
                                </Button>
                                <Button onClick={() => setItemModalVisible(false)}>
                                    Cancelar
                                </Button>
                            </Space>
                        </Form.Item>
                    </Form>
                </Modal>
            );
        }
    };

    if (loading && !document) {
        return <div>Cargando datos...</div>;
    }

    return (
        <div className="page-container">
            <Card 
                title={`Verificación de Documento: ${document?.original_filename}`}
                extra={
                    <Space>
                        <Popconfirm
                            title="¿Marcar documento como completado?"
                            onConfirm={handleCompleteDocument}
                            okText="Sí"
                            cancelText="No"
                        >
                            <Button type="primary">
                                Completar Documento
                            </Button>
                        </Popconfirm>
                        <Button onClick={() => navigate('/documentos')}>
                            Volver
                        </Button>
                    </Space>
                }
            >
                {/* Añadimos aquí la información del proveedor para albaranes */}
                {document?.type === 'albaran' && extractedData && (
                    <div style={{ marginBottom: 16 }}>
                        <Divider orientation="left">Datos del Documento</Divider>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
                            <div style={{ minWidth: '300px' }}>
                                <Title level={5}>Proveedor</Title>
                                <p><strong>Nombre:</strong> {extractedData.supplier?.name || 'No disponible'}</p>
                                <p><strong>Dirección:</strong> {extractedData.supplier?.address || 'No disponible'}</p>
                                <p><strong>Teléfono:</strong> {extractedData.supplier?.phone || 'No disponible'}</p>
                                <p><strong>Email:</strong> {extractedData.supplier?.email || 'No disponible'}</p>
                            </div>
                            <div style={{ minWidth: '300px' }}>
                                <Title level={5}>Documento</Title>
                                <p><strong>Número:</strong> {extractedData.document?.number || 'No disponible'}</p>
                                <p><strong>Fecha:</strong> {extractedData.document?.date || 'No disponible'}</p>
                                <p><strong>NIF/CIF:</strong> {extractedData.document?.nif || 'No disponible'}</p>
                                <p><strong>Referencia:</strong> {extractedData.document?.reference || 'No disponible'}</p>
                            </div>
                            <div style={{ minWidth: '300px' }}>
                                <Title level={5}>Totales</Title>
                                <p><strong>Base Imponible:</strong> {extractedData.totals?.taxable_base || 0}€</p>
                                <p><strong>IVA ({extractedData.totals?.vat_rate || 21}%):</strong> {extractedData.totals?.vat_amount || 0}€</p>
                                <p><strong>Total:</strong> <span style={{ fontWeight: 'bold', fontSize: '1.1em' }}>{extractedData.totals?.total_amount || 0}€</span></p>
                            </div>
                        </div>
                    </div>
                )}
                
                <Divider orientation="left">
                    {document?.type === 'albaran' ? 'Productos en Albarán' : 'Órdenes de Trabajo'}
                </Divider>
                
                <div>
                    <Text>Procese cada elemento individualmente. Una vez procesados todos, 
                    puede marcar el documento como completado.</Text>
                </div>
                
                <div style={{ marginTop: 16 }}>
                    {renderItemTable()}
                </div>
                
                {renderItemModal()}
            </Card>
        </div>
    );
};

export default DocumentVerification;