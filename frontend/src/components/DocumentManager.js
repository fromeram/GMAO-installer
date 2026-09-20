// src/components/DocumentManager.js
import React, { useState, useEffect } from 'react';
import { Table, Button, Upload, Modal, Form, Input, Space, message, Typography, Tooltip } from 'antd';
import { UploadOutlined, FileOutlined, DeleteOutlined, DownloadOutlined, EyeOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';

const { Text, Title } = Typography;
const { Dragger } = Upload;

const DocumentManager = ({ entityType, entityId, title = "Documentos" }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadVisible, setUploadVisible] = useState(false);
  const [fileList, setFileList] = useState([]);
  const [form] = Form.useForm();
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewDocument, setPreviewDocument] = useState(null);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await fetchWithAuth(`/documents/list/${entityType}/${entityId}`);
      setDocuments(data || []);
    } catch (error) {
      console.error("Error loading documents:", error);
      message.error("Error al cargar documentos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (entityId) {
      loadDocuments();
    }
  }, [entityType, entityId]);

  const handleUpload = async () => {
    try {
      const values = await form.validateFields();
      
      const formData = new FormData();
      formData.append('file', fileList[0].originFileObj);
      formData.append('entity_type', entityType);
      formData.append('entity_id', entityId);
      formData.append('description', values.description || '');
      
      const response = await fetchWithAuth('/documents/upload', {
        method: 'POST',
        body: formData,
        headers: {
          // No incluir 'Content-Type' para que el navegador establezca el boundary correcto
        },
      });
      
      message.success('Documento subido correctamente');
      setUploadVisible(false);
      form.resetFields();
      setFileList([]);
      loadDocuments();
    } catch (error) {
      console.error("Error uploading document:", error);
      message.error("Error al subir documento");
    }
  };

  const handleDelete = async (docId) => {
    try {
      await fetchWithAuth(`/documents/${docId}`, {
        method: 'DELETE'
      });
      message.success('Documento eliminado correctamente');
      loadDocuments();
    } catch (error) {
      console.error("Error deleting document:", error);
      message.error("Error al eliminar documento");
    }
  };

  const handleDownload = async (docId, fileName) => {
    try {
      // Redireccionar a la URL de descarga
      window.open(`/api/documents/download/${docId}`, '_blank');
    } catch (error) {
      console.error("Error downloading document:", error);
      message.error("Error al descargar documento");
    }
  };

  const handlePreview = (doc) => {
    setPreviewDocument(doc);
    setPreviewVisible(true);
  };

  const uploadProps = {
    onRemove: () => {
      setFileList([]);
    },
    beforeUpload: (file) => {
      // Validar tipo de archivo
      const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'application/msword', 
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                           'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
      
      const isAllowed = allowedTypes.includes(file.type);
      if (!isAllowed) {
        message.error('Solo se permiten archivos PDF, imágenes, Word y Excel');
      }
      
      // Validar tamaño (10MB)
      const isLessThan10MB = file.size / 1024 / 1024 < 10;
      if (!isLessThan10MB) {
        message.error('El archivo debe ser menor de 10MB');
      }
      
      if (isAllowed && isLessThan10MB) {
        setFileList([file]);
      }
      
      // Prevent upload
      return false;
    },
    fileList,
  };

  const columns = [
    {
      title: 'Archivo',
      dataIndex: 'original_file_name',
      key: 'original_file_name',
      render: (text, record) => {
        // Mostrar ícono según tipo
        let icon;
        const fileType = record.file_type.toLowerCase();
        
        if (['pdf'].includes(fileType)) {
          icon = <FileOutlined style={{ color: 'red' }} />;
        } else if (['jpg', 'jpeg', 'png'].includes(fileType)) {
          icon = <FileOutlined style={{ color: 'blue' }} />;
        } else if (['doc', 'docx'].includes(fileType)) {
          icon = <FileOutlined style={{ color: 'green' }} />;
        } else if (['xls', 'xlsx'].includes(fileType)) {
          icon = <FileOutlined style={{ color: 'green' }} />;
        } else {
          icon = <FileOutlined />;
        }
        
        return (
          <Space>
            {icon} <Text>{text}</Text>
          </Space>
        );
      }
    },
    {
      title: 'Descripción',
      dataIndex: 'description',
      key: 'description',
      render: text => text || '-'
    },
    {
      title: 'Tamaño',
      dataIndex: 'file_size',
      key: 'file_size',
      render: size => {
        // Convertir bytes a KB/MB
        if (size < 1024) {
          return `${size} bytes`;
        } else if (size < 1024 * 1024) {
          return `${(size / 1024).toFixed(2)} KB`;
        } else {
          return `${(size / 1024 / 1024).toFixed(2)} MB`;
        }
      }
    },
    {
      title: 'Subido Por',
      dataIndex: 'uploaded_by',
      key: 'uploaded_by',
    },
    {
      title: 'Fecha',
      dataIndex: 'uploaded_at',
      key: 'uploaded_at',
      render: date => new Date(date).toLocaleDateString()
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="Descargar">
            <Button 
              icon={<DownloadOutlined />} 
              size="small"
              onClick={() => handleDownload(record.id, record.original_file_name)}
            />
          </Tooltip>
          {['pdf', 'jpg', 'jpeg', 'png'].includes(record.file_type.toLowerCase()) && (
            <Tooltip title="Vista Previa">
              <Button 
                icon={<EyeOutlined />} 
                size="small"
                onClick={() => handlePreview(record)}
              />
            </Tooltip>
          )}
          <Tooltip title="Eliminar">
            <Button 
              icon={<DeleteOutlined />} 
              size="small" 
              danger
              onClick={() => handleDelete(record.id)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // Renderizar miniatura o PDF embedido
  const renderPreview = () => {
    if (!previewDocument) return null;
    
    const fileType = previewDocument.file_type.toLowerCase();
    
    if (['jpg', 'jpeg', 'png'].includes(fileType)) {
      return (
        <img 
          src={`/api/documents/download/${previewDocument.id}`} 
          alt={previewDocument.original_file_name}
          style={{ maxWidth: '100%', maxHeight: '80vh' }}
        />
      );
    } else if (fileType === 'pdf') {
      return (
        <iframe
          src={`/api/documents/download/${previewDocument.id}`}
          width="100%"
          height="500px"
          title={previewDocument.original_file_name}
        />
      );
    }
    
    return <Text>Vista previa no disponible para este tipo de archivo</Text>;
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4}>{title}</Title>
        <Button 
          type="primary" 
          icon={<UploadOutlined />}
          onClick={() => setUploadVisible(true)}
        >
          Subir Documento
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={documents}
        rowKey="id"
        loading={loading}
        pagination={documents.length > 10 ? { pageSize: 10 } : false}
      />

      {/* Modal de subida */}
      <Modal
        title="Subir Documento"
        open={uploadVisible}
        onCancel={() => {
          setUploadVisible(false);
          setFileList([]);
          form.resetFields();
        }}
        onOk={handleUpload}
        okText="Subir"
        cancelText="Cancelar"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="file" label="Archivo" rules={[{ required: true, message: 'Por favor seleccione un archivo' }]}>
            <Dragger {...uploadProps} accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx">
              <p className="ant-upload-drag-icon">
                <UploadOutlined />
              </p>
              <p className="ant-upload-text">Haga clic o arrastre el archivo para subirlo</p>
              <p className="ant-upload-hint">
                Soporta PDF, imágenes, Word y Excel. Máximo 10MB.
              </p>
            </Dragger>
          </Form.Item>
          <Form.Item name="description" label="Descripción">
            <Input.TextArea rows={3} placeholder="Descripción opcional del documento" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Modal de vista previa */}
      <Modal
        title={previewDocument?.original_file_name || "Vista Previa"}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={[
          <Button key="download" icon={<DownloadOutlined />} onClick={() => handleDownload(previewDocument?.id, previewDocument?.original_file_name)}>
            Descargar
          </Button>,
          <Button key="close" type="primary" onClick={() => setPreviewVisible(false)}>
            Cerrar
          </Button>
        ]}
        width={800}
      >
        {renderPreview()}
      </Modal>
    </div>
  );
};

export default DocumentManager;