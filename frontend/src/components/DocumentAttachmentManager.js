// src/components/DocumentAttachmentManager.js (Versión CORREGIDA)
import React, { useState, useEffect } from 'react';
import { Table, Button, Upload, Modal, Form, Input, Space, message, Typography, Tooltip, Spin  } from 'antd';
import { UploadOutlined, FileOutlined, DeleteOutlined, DownloadOutlined, EyeOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';

const { Text, Title } = Typography;
const { Dragger } = Upload;

const DocumentAttachmentManager = ({ entityType, entityId, title = "Documentos" }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadVisible, setUploadVisible] = useState(false);
  const [fileList, setFileList] = useState([]);
  const [form] = Form.useForm();
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewDocument, setPreviewDocument] = useState(null);

  const loadDocuments = async () => {
    if (!entityType || !entityId) return;
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
    loadDocuments();
  }, [entityType, entityId]);

  const handleUpload = async () => {
    try {
      const values = await form.validateFields();
      
      // ✅ VALIDACIÓN CORREGIDA: Verificar que hay archivo seleccionado
      if (!fileList || fileList.length === 0) {
        message.error('Por favor, seleccione un archivo para subir.');
        return;
      }

      // ✅ VERIFICAR QUE EL ARCHIVO EXISTE Y ES VÁLIDO
      const file = fileList[0];
      if (!file || !file.originFileObj) {
        message.error('Archivo inválido. Por favor, seleccione otro archivo.');
        return;
      }
      
      // ✅ CREAR FORMDATA CORRECTAMENTE
      const formData = new FormData();
      formData.append('file', file.originFileObj); // ¡USAR originFileObj!
      
      // ✅ CONSTRUIR URL CON QUERY PARAMETER
      const descriptionParam = values.description 
        ? `?description=${encodeURIComponent(values.description)}` 
        : '';
      const endpoint = `/documents/${entityType}/${entityId}/upload${descriptionParam}`;

      console.log('📤 Subiendo archivo:', file.originFileObj.name);
      console.log('📤 Tamaño:', file.originFileObj.size);
      console.log('📤 Endpoint:', endpoint);

      setLoading(true);
      
      // ✅ SOLUCION DEFINITIVA: Usar el token correcto de sessionStorage
      const token = sessionStorage.getItem('access_token');
      
      if (!token) {
        throw new Error('No hay token de autenticación disponible');
      }

      console.log('🔑 Token encontrado:', token.substring(0, 20) + '...');

      const response = await fetch(`/api${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          // ❗ NO ESTABLECER Content-Type - el navegador lo configurará automáticamente para FormData
        },
        body: formData,
      });

      // ✅ MANEJAR LA RESPUESTA
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // Si no es JSON válido, usar el mensaje por defecto
        }
        
        // Si es error 401, redirigir al login
        if (response.status === 401) {
          sessionStorage.removeItem('access_token');
          window.location.href = '/login';
          return;
        }
        
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log('✅ Upload exitoso:', result);
      
      message.success('Documento subido correctamente');
      setUploadVisible(false);
      form.resetFields();
      setFileList([]);
      await loadDocuments();
      
    } catch (error) {
      console.error("Error uploading document:", error);
      message.error(error.message || "Error al subir documento");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (docId) => {
    try {
      console.log('🗑️ Eliminando documento ID:', docId);
      
      // ✅ SOLUCIÓN FINAL: Usar la misma estrategia que el download
      // Download funciona con: /documents/download/{id}
      // Necesitamos: /documents/delete/{id} o similar
      
      // Intentamos con fetchWithAuth usando una ruta específica como download
      try {
        console.log('🗑️ Intentando con ruta específica: /documents/attachment/{id}');
        const result = await fetchWithAuth(`/documents/attachment/${docId}`, { method: 'DELETE' });
        console.log('✅ Delete exitoso con ruta específica:', result);
        message.success('Documento eliminado correctamente');
        await loadDocuments();
        return;
      } catch (specificError) {
        console.log('❌ Ruta específica falló, intentando alternativa...');
      }
      
      // Si la ruta específica no existe, usar la instancia de axios para documentos
      try {
        console.log('🗑️ Intentando con axios directo...');
        const { api } = await import('../apiConfig'); // Importar la instancia axios
        
        const response = await api.delete(`/documents/${docId}`);
        console.log('✅ Delete exitoso con axios:', response);
        message.success('Documento eliminado correctamente');
        await loadDocuments();
        return;
      } catch (axiosError) {
        console.log('❌ Axios falló, usando fetch directo...');
      }
      
      // Fallback final: fetch directo
      const token = sessionStorage.getItem('access_token');
      if (!token) {
        throw new Error('No hay token de autenticación disponible');
      }

      const response = await fetch(`/api/documents/${docId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 204 || response.status === 200) {
        console.log('✅ Delete exitoso con fetch directo');
        message.success('Documento eliminado correctamente');
        await loadDocuments();
        return;
      }

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // Si no es JSON válido, usar el mensaje por defecto
        }
        throw new Error(errorMessage);
      }
      
    } catch (error) {
      console.error("Error eliminando documento:", error);
      const errorMessage = error.message || "Error al eliminar documento";
      console.error("Detalles del error:", errorMessage);
      message.error(errorMessage);
    }
  };

  // Función de descarga CORREGIDA
const handleDownload = async (documentId, originalFilename) => {
  try {
    console.log(`⬇️ Descargando documento ${documentId}...`);
    
    const token = sessionStorage.getItem('access_token');
    if (!token) {
      throw new Error("No está autenticado");
    }

    // USAR ENDPOINT ESPECÍFICO PARA DESCARGA
    const response = await fetch(`/api/documents/download/${documentId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`Error al descargar: ${errorData.detail || response.statusText}`);
    }

    // Obtener información del archivo de las cabeceras
    const contentLength = response.headers.get('Content-Length');
    const contentType = response.headers.get('Content-Type');
    
    console.log(`📁 Archivo info - Tamaño: ${contentLength} bytes, Tipo: ${contentType}`);

    const blob = await response.blob();
    
    // VERIFICACIÓN CRÍTICA: Tamaño del blob
    if (blob.size === 0) {
      throw new Error('El archivo descargado está vacío');
    }
    
    if (blob.size < 1024 && contentType === 'application/json') {
      // Probablemente es un mensaje de error JSON
      const errorText = await blob.text();
      throw new Error(`Error del servidor: ${errorText}`);
    }
    
    console.log(`✅ Descarga exitosa - Tamaño del blob: ${blob.size} bytes`);
    
    // Crear enlace de descarga
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = originalFilename;
    
    document.body.appendChild(a);
    a.click();
    
    // Cleanup
    window.URL.revokeObjectURL(url);
    a.remove();
    
    console.log(`🎉 Descarga completada: ${originalFilename}`);

  } catch (error) {
    console.error('❌ Error en la descarga:', error);
    message.error('Error al descargar el archivo: ' + error.message);
  }
};


  const handlePreview = async (doc) => {
    try {
      setPreviewDocument(doc);
      setPreviewVisible(true);
    } catch (error) {
      console.error('Error previewing document:', error);
      message.error('Error al mostrar vista previa');
    }
  };


  // ✅ CONFIGURACIÓN CORREGIDA DEL UPLOAD
  const uploadProps = {
    onRemove: () => {
      setFileList([]);
    },
    beforeUpload: (file) => {
      console.log('📁 Archivo seleccionado:', file.name, file.size);
      
      // Validar tamaño
      const isLt200M = file.size / 1024 / 1024 < 200;
      if (!isLt200M) {
        message.error('El archivo debe ser menor de 200MB');
        return Upload.LIST_IGNORE;
      }

      // Validar extensión
      const allowedTypes = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx', 'txt'];
      const fileExtension = file.name.split('.').pop().toLowerCase();
      if (!allowedTypes.includes(fileExtension)) {
        message.error('Tipo de archivo no permitido');
        return Upload.LIST_IGNORE;
      }

      // ✅ ASEGURAR QUE EL ARCHIVO SE GUARDA CORRECTAMENTE
      setFileList([{
        uid: file.uid,
        name: file.name,
        status: 'done',
        originFileObj: file // ¡IMPORTANTE: Guardar el archivo original!
      }]);
      
      return false; // Prevenir upload automático
    },
    fileList,
    maxCount: 1, // Solo un archivo a la vez
  };

  const columns = [
    {
      title: 'Archivo',
      dataIndex: 'original_file_name',
      key: 'original_file_name',
      render: (text) => (<Space><FileOutlined /> <Text>{text}</Text></Space>)
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
      render: size => (size / 1024 / 1024).toFixed(2) + ' MB' 
    },
    { 
      title: 'Subido Por', 
      dataIndex: ['uploaded_by', 'username'], 
      key: 'uploaded_by' 
    },
    { 
      title: 'Fecha', 
      dataIndex: 'uploaded_at', 
      key: 'uploaded_at', 
      render: date => date ? new Date(date).toLocaleDateString() : '-' 
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
              onClick={() => handleDownload(record.id)}
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

  const renderPreview = () => {
    if (!previewDocument) return null;
    
    const token = sessionStorage.getItem('access_token');
    if (!token) {
      return <Text>Error: No está autenticado</Text>;
    }

    // Para imágenes
    if (['jpg', 'jpeg', 'png'].includes(previewDocument.file_type.toLowerCase())) {
      return (
        <PreviewImage 
          documentId={previewDocument.id} 
          filename={previewDocument.original_file_name}
          token={token}
        />
      );
    } 
    // Para PDFs
    else if (previewDocument.file_type.toLowerCase() === 'pdf') {
      return (
        <PreviewPDF 
          documentId={previewDocument.id} 
          filename={previewDocument.original_file_name}
          token={token}
        />
      );
    }
    
    return <Text>Vista previa no disponible para este tipo de archivo.</Text>;
  };
  // Componente para previsualizar imágenes - VERSIÓN CORREGIDA
const PreviewImage = ({ documentId, filename }) => {
  const [imageSrc, setImageSrc] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const loadImage = async () => {
      try {
        console.log(`🖼️ Cargando imagen del documento ${documentId}...`);
        
        // USAR ENDPOINT ESPECÍFICO PARA VISTA PREVIA
        const token = sessionStorage.getItem('access_token');
        const response = await fetch(`/api/documents/preview/${documentId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Error HTTP: ${response.status}`);
        }

        const blob = await response.blob();
        console.log(`✅ Imagen cargada - Tamaño: ${blob.size} bytes, Tipo: ${blob.type}`);
        
        if (blob.size === 0) {
          throw new Error('El archivo está vacío');
        }
        
        // Verificar que es realmente una imagen
        if (!blob.type.startsWith('image/')) {
          throw new Error(`Tipo de archivo inválido: ${blob.type}`);
        }
        
        const url = window.URL.createObjectURL(blob);
        setImageSrc(url);
        
      } catch (error) {
        console.error('❌ Error loading image:', error);
        setError(`Error al cargar imagen: ${error.message}`);
      } finally {
        setLoading(false);
      }
    };

    loadImage();

    // Cleanup
    return () => {
      if (imageSrc) {
        window.URL.revokeObjectURL(imageSrc);
      }
    };
  }, [documentId]);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '50px' }}><Spin size="large" /></div>;
  }

  if (error) {
    return <div style={{ textAlign: 'center', padding: '50px', color: 'red' }}>{error}</div>;
  }

  if (!imageSrc) {
    return <div style={{ textAlign: 'center', padding: '50px' }}>No se pudo cargar la imagen</div>;
  }

  return (
    <img 
      src={imageSrc} 
      alt={filename} 
      style={{ 
        maxWidth: '100%', 
        maxHeight: '70vh', 
        objectFit: 'contain',
        display: 'block',
        margin: '0 auto'
      }}
      onError={() => setError('Error al mostrar la imagen')}
    />
  );
};

// Componente para previsualizar PDFs - VERSIÓN CORREGIDA
const PreviewPDF = ({ documentId, filename }) => {
  const [pdfSrc, setPdfSrc] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const loadPDF = async () => {
      try {
        console.log(`📄 Cargando PDF del documento ${documentId}...`);
        
        // USAR ENDPOINT ESPECÍFICO PARA VISTA PREVIA
        const token = sessionStorage.getItem('access_token');
        const response = await fetch(`/documents/preview/${documentId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Error HTTP: ${response.status}`);
        }

        const blob = await response.blob();
        console.log(`✅ PDF cargado - Tamaño: ${blob.size} bytes, Tipo: ${blob.type}`);
        
        if (blob.size === 0) {
          throw new Error('El archivo PDF está vacío');
        }
        
        // Verificar que es realmente un PDF
        if (blob.type !== 'application/pdf') {
          throw new Error(`Tipo de archivo inválido: ${blob.type}`);
        }
        
        const url = window.URL.createObjectURL(blob);
        setPdfSrc(url);
        
      } catch (error) {
        console.error('❌ Error loading PDF:', error);
        setError(`Error al cargar PDF: ${error.message}`);
      } finally {
        setLoading(false);
      }
    };

    loadPDF();

    // Cleanup
    return () => {
      if (pdfSrc) {
        window.URL.revokeObjectURL(pdfSrc);
      }
    };
  }, [documentId]);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '50px' }}><Spin size="large" /></div>;
  }

  if (error) {
    return <div style={{ textAlign: 'center', padding: '50px', color: 'red' }}>{error}</div>;
  }

  if (!pdfSrc) {
    return <div style={{ textAlign: 'center', padding: '50px' }}>No se pudo cargar el PDF</div>;
  }

  return (
    <iframe 
      src={pdfSrc} 
      width="100%" 
      height="600px" 
      title={filename}
      style={{ border: 'none' }}
    />
  );
};

  return (
    <div>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: 16 
      }}>
        <Title level={4} style={{ margin: 0 }}>{title}</Title>
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
        confirmLoading={loading}
      >
        <Form form={form} layout="vertical">
          <Form.Item 
            name="description" 
            label="Descripción (opcional)"
          >
            <Input placeholder="Descripción del documento" />
          </Form.Item>
          
          <Form.Item 
            label="Archivo"
            required
          >
            <Dragger {...uploadProps}>
              <p className="ant-upload-drag-icon">
                <UploadOutlined />
              </p>
              <p className="ant-upload-text">
                Haga clic o arrastre el archivo para subirlo
              </p>
              <p className="ant-upload-hint">
                Soporta PDF, imágenes, Word y Excel. Máximo 200MB.
              </p>
            </Dragger>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`Vista Previa: ${previewDocument?.original_file_name || 'Documento'}`}
        open={previewVisible}
        onCancel={() => {
          setPreviewVisible(false);
          setPreviewDocument(null);
        }}
        footer={[
          <Button key="download" type="primary" onClick={() => handleDownload(previewDocument?.id, previewDocument?.original_file_name)}>
            Descargar
          </Button>,
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            Cerrar
          </Button>
        ]}
        width="90%"
        style={{ top: 20 }}
        destroyOnClose
      >
        {renderPreview()}
      </Modal>
    </div>
  );
};

export default DocumentAttachmentManager;