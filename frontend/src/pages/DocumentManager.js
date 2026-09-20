// src/components/DocumentManager.jsx
import React, { useState, useEffect } from 'react';
import { Card, Upload, Button, Table, Tag, message, Space, Radio, Tooltip, Popconfirm, Spin } from 'antd'; // Asegúrate que Tooltip, Popconfirm, Spin están importados
import { UploadOutlined, InfoCircleOutlined } from '@ant-design/icons'; // Asegúrate que InfoCircleOutlined está importado
import { useNavigate } from 'react-router-dom';
import { fetchWithAuth, processDocumentWithAI } from '../apiConfig'; // Verifica que processDocumentWithAI se importe correctamente
import '../styles/CommonPage.css'; // Verifica que la ruta a tus estilos es correcta

const DocumentManager = () => {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(false); // Estado para carga general
    const [processingId, setProcessingId] = useState(null); // Estado para saber qué ID específico se está procesando por click
    const [documentType, setDocumentType] = useState('albaran');
    const navigate = useNavigate();

    // Función para cargar documentos
    const fetchDocuments = async () => {
        // No ponemos setLoading(true) aquí para permitir el refresco en segundo plano sin bloquear la UI
        try {
            const data = await fetchWithAuth('/documents');
            setDocuments(data);
            return data; // Devolvemos los datos para usarlos en useEffect
        } catch (error) {
            // Evitamos mostrar mensaje de error en cada fallo del polling para no molestar
            // message.error('Error al cargar documentos');
            console.error('Error al cargar documentos (polling):', error);
            return null; // Devolver null si falla
        } finally {
            // No ponemos setLoading(false) aquí
        }
    };

    // Función para eliminar documento
    const handleDelete = async (id) => {
        setLoading(true); // Bloquear UI mientras se elimina
        try {
            await fetchWithAuth(`/documents/${id}`, {
                method: 'DELETE'
            });
            message.success('Documento eliminado correctamente');
            fetchDocuments(); // Recargar lista
        } catch (error) {
            message.error('Error al eliminar el documento');
            console.error('Error al eliminar documento:', error);
        } finally {
            setLoading(false);
        }
    };

    // Función para iniciar el procesamiento IA
    const handleProcessWithAI = async (documentId) => {
        // --- LOG DE INICIO ---
        console.log(`[handleProcessWithAI] Iniciando para ID: ${documentId}`);
        setProcessingId(documentId); // Marcar este ID como procesándose
        message.loading({ content: `Iniciando procesamiento IA para Doc ${documentId}...`, key: `processAI_${documentId}`, duration: 0 });

        try {
            console.log(`Enviando solicitud para procesar documento ${documentId} con IA...`);
            const response = await processDocumentWithAI(documentId);
            // --- LOG DE RESPUESTA ---
            console.log(`[handleProcessWithAI] Respuesta API para ID ${documentId}:`, response);

            if (response.success) {
                message.success({ content: `Procesamiento IA iniciado para Doc ${documentId}. El estado se actualizará pronto.`, key: `processAI_${documentId}`, duration: 5 });
                // Actualizar la tabla inmediatamente para reflejar el estado 'processing'
                fetchDocuments();
            } else {
                console.error(`Error al INICIAR procesamiento IA para Doc ${documentId}: ${response.error || 'Error desconocido'}`);
                message.error({ content: `Error al iniciar procesamiento: ${response.error || 'Error desconocido'}`, key: `processAI_${documentId}` });
                setProcessingId(null); // Resetear ID si falló el inicio
            }
        } catch (error) {
            // --- LOG DE ERROR ---
            console.error(`[handleProcessWithAI] Error en catch para ID ${documentId}:`, error);
            message.error({ content: `Error al iniciar procesamiento: ${error.message}`, key: `processAI_${documentId}` });
            setProcessingId(null); // Resetear ID en caso de error de comunicación
        }
    };

    // Definición de las columnas de la tabla
    const columns = [
        {
            title: 'Nombre Archivo',
            dataIndex: 'filename',
            key: 'filename',
            // Opcional: Añadir tooltip con nombre original si es diferente
            render: (text, record) => (
                <Tooltip title={record.original_filename !== record.filename ? `Original: ${record.original_filename}` : ''}>
                    {text}
                </Tooltip>
            )
        },
        {
            title: 'Tipo',
            dataIndex: 'type',
            key: 'type',
            render: type => (
                <Tag color={type === 'albaran' ? 'blue' : 'green'} style={{textTransform: 'capitalize'}}>
                    {type.replace('_', ' ')}
                </Tag>
            )
        },
        {
            title: 'Estado',
            dataIndex: 'status',
            key: 'status',
            render: (status, record) => {
                // --- LOG DE RENDER ESTADO ---
                console.log(`[Render Estado] ID: ${record.id}, Status: ${status}, ErrorMsg: ${record.error_message}`);
                const statusColors = {
                    pending: 'default',
                    processing: 'processing',
                    completed: 'success',
                    error: 'error',
                    confirmed: 'blue'
                };
                const statusText = status ? status.toUpperCase() : 'DESCONOCIDO';

                if (status === 'error') {
                    return (
                        <Space>
                            <Tag color={statusColors[status]}>{statusText}</Tag>
                            {record.error_message && (
                                <Tooltip title={record.error_message} overlayStyle={{ maxWidth: '400px' }}>
                                    <InfoCircleOutlined style={{ color: 'red', cursor: 'help' }} />
                                </Tooltip>
                            )}
                        </Space>
                    );
                }
                 if (status === 'processing') {
                     return <Tag icon={<Spin size="small" />} color={statusColors[status]}>{statusText}</Tag>;
                 }

                return <Tag color={statusColors[status] || 'default'}>{statusText}</Tag>;
            }
        },
        {
            title: 'Fecha Subida',
            dataIndex: 'created_at',
            key: 'created_at',
            render: date => date ? new Date(date).toLocaleString() : '-'
        },
         {
            title: 'Fecha Procesado',
            dataIndex: 'processed_at',
            key: 'processed_at',
            render: date => date ? new Date(date).toLocaleString() : '-'
        },
        {
            title: 'Acciones',
            key: 'actions',
            render: (_, record) => {
                const isCurrentlyProcessing = processingId === record.id; // Este botón específico fue clickeado?
                const isRowProcessing = record.status === 'processing';   // El estado general de la fila es processing?

                // --- LOG DE RENDER ACCIONES ---
                console.log(`[Render Acciones] ID: ${record.id}, Status: ${record.status}, isCurrentlyProcessing (click): ${isCurrentlyProcessing}, isRowProcessing (estado): ${isRowProcessing}`);

                return (
                    <Space>
                        {/* Botón Verificar/Ver Datos */}
                        {(record.status === 'completed' || record.status === 'confirmed') && (
                            <Button
                                type="primary"
                                onClick={() => navigate(`/documentos/${record.id}/verificar`)}
                                disabled={isCurrentlyProcessing || isRowProcessing} // Deshabilitar si se está procesando
                            >
                                {record.status === 'confirmed' ? 'Ver Datos' : 'Verificar'}
                            </Button>
                        )}

                        {/* Botón Procesar con IA */}
                        {record.status === 'pending' && (
                            <Button
                                type="default"
                                onClick={() => handleProcessWithAI(record.id)}
                                loading={isCurrentlyProcessing} // Muestra Spin si este ID está procesándose por click
                                disabled={isCurrentlyProcessing || isRowProcessing || loading} // Deshabilitar si procesando (click o estado) o carga general
                            >
                                {isCurrentlyProcessing ? 'Iniciando...' : 'Procesar con IA'}
                            </Button>
                        )}

                        {/* Botón Eliminar con Confirmación */}
                         <Popconfirm
                             title="¿Seguro que quieres eliminar este documento?"
                             onConfirm={() => handleDelete(record.id)}
                             okText="Sí"
                             cancelText="No"
                             disabled={isCurrentlyProcessing || isRowProcessing} // Deshabilitar si se procesa
                         >
                             <Button
                                 type="text"
                                 danger
                                 disabled={isCurrentlyProcessing || isRowProcessing} // Deshabilitar si se procesa
                             >
                                 Eliminar
                             </Button>
                         </Popconfirm>
                    </Space>
                );
            }
        }
    ];

    // Efecto para cargar datos y manejar el estado processingId con el polling
    useEffect(() => {
        let isMounted = true; // Flag para evitar actualizaciones si el componente se desmonta

        const fetchDataAndCheckProcessing = async () => {
             console.log('[useEffect] Verificando actualizaciones...');
             // No mostramos el spinner general durante el polling
             const fetchedDocs = await fetchDocuments(); // fetchDocuments ya no usa setLoading

             if (!isMounted) return; // Salir si el componente se desmontó mientras se cargaban datos

             // Si teníamos un ID en procesamiento, verificar si sigue en ese estado
             if (processingId && fetchedDocs) {
                 const docBeingProcessed = fetchedDocs.find(doc => doc.id === processingId);
                 if (!docBeingProcessed || docBeingProcessed.status !== 'processing') {
                     console.log(`[useEffect] Doc ${processingId} ya no está 'processing'. Limpiando processingId.`);
                     setProcessingId(null); // Limpiar el estado local
                     message.destroy(`processAI_${processingId}`);
                 } else {
                      console.log(`[useEffect] Doc ${processingId} sigue en estado 'processing'.`);
                 }
             } else if (processingId) {
                 // Si processingId está activo pero falló la carga de documentos
                 console.log(`[useEffect] No se pudieron cargar documentos, pero processingId (${processingId}) sigue activo.`);
             }
        };

        // Cargar documentos inicialmente
        setLoading(true); // Activar loading solo para la carga inicial
        fetchDataAndCheckProcessing().finally(() => {
             if (isMounted) setLoading(false); // Desactivar loading inicial cuando termine
        });


        // Establecer el intervalo para refresco periódico
        const interval = setInterval(fetchDataAndCheckProcessing, 10000); // Cada 10 segundos

        // Limpiar el intervalo cuando el componente se desmonte
        return () => {
             isMounted = false; // Marcar como desmontado
             clearInterval(interval);
             // Opcional: Limpiar mensajes pendientes si el componente se desmonta
             if (processingId) message.destroy(`processAI_${processingId}`);
        }
    }, [processingId]); // <- useEffect se ejecuta si processingId cambia

    // Función para manejar la subida de archivos (sin cambios)
    const customRequest = async ({ file, onSuccess, onError }) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('doc_type', documentType);

        setLoading(true); // Activar loading durante la subida
        try {
            const response = await fetch('/api/documents/upload', {
                method: 'POST',
                body: formData,
                headers: {
                    'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error en la respuesta:', response.status, errorText);
                onError(new Error(`Error del servidor: ${response.status}`));
                message.error(`Error al subir el documento: ${response.status}`);
                return;
            }
            const data = await response.json();
            if (data.success) {
                onSuccess();
                message.success('Documento subido correctamente');
                fetchDocuments(); // Recargar la lista
            } else {
                 onError(new Error('Error al subir el documento'));
                 message.error(`Error: ${data.message || 'Error desconocido'}`);
            }
        } catch (error) {
            console.error('Error en la subida:', error);
            onError(error);
            message.error(`Error en la petición: ${error.message}`);
        } finally {
             setLoading(false); // Desactivar loading al terminar subida
        }
    };

    // Renderizado del componente
    return (
        <div className="page-container">
            <Card title="Gestión de Documentos">
                <Space direction="vertical" style={{ width: '100%' }}>
                    {/* Selección de Tipo y Botón de Subida */}
                    <Space wrap>
                         <Radio.Group
                            value={documentType}
                            onChange={e => setDocumentType(e.target.value)}
                            // style={{ marginBottom: 16 }} // Quitar margen inferior si está en Space
                        >
                            <Radio.Button value="albaran">Albarán</Radio.Button>
                            <Radio.Button value="parte_trabajo">Parte de Trabajo</Radio.Button>
                        </Radio.Group>

                         <Upload
                            customRequest={customRequest}
                            showUploadList={false}
                            beforeUpload={(file) => {
                                const isImage = file.type.startsWith('image/');
                                const isPdf = file.type === 'application/pdf';
                                if (!isImage && !isPdf) {
                                    message.error('Solo puedes subir imágenes (JPG, PNG, GIF...) o archivos PDF!');
                                    return Upload.LIST_IGNORE;
                                }
                                const maxSize = 100 * 1024 * 1024; // 100MB
                                if (file.size > maxSize) {
                                    message.error('El archivo excede el límite de 100MB');
                                    return Upload.LIST_IGNORE;
                                }
                                return true; // Permite la subida
                            }}
                            disabled={loading} // Deshabilitar subida si algo está cargando/procesando
                        >
                            <Button icon={<UploadOutlined />} disabled={loading}>
                                Subir {documentType === 'albaran' ? 'Albarán' : 'Parte de Trabajo'}
                            </Button>
                        </Upload>
                    </Space>

                    {/* Tabla de Documentos */}
                    <Table
                        columns={columns}
                        dataSource={documents}
                        rowKey="id"
                        loading={loading} // Muestra el estado de carga general de la tabla
                        style={{marginTop: '16px'}} // Añadir un poco de espacio arriba
                    />
                </Space>
            </Card>
        </div>
    );
};

export default DocumentManager;