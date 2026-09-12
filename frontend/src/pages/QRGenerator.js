// src/pages/QRGenerator.js (Versión Responsive)
import React, { useState, useEffect } from 'react';
import { Card, Select, Button, message, Typography, Input, Row, Col } from 'antd';
import { QRCodeCanvas } from 'qrcode.react';
import { DownloadOutlined, PrinterOutlined } from '@ant-design/icons';
import { api } from '../apiConfig';
import html2canvas from 'html2canvas';
import { useAuth } from '../contexts/AuthContext';
import MobileLayout from '../components/MobileLayout';

const { Title, Text } = Typography;
const { Option } = Select;

const QRGenerator = () => {
  const [machines, setMachines] = useState([]);
  const [selectedMachine, setSelectedMachine] = useState(null);
  const [loading, setLoading] = useState(false);
  const [qrValue, setQrValue] = useState('');
  const [qrTitle, setQrTitle] = useState('');
  const [baseUrl, setBaseUrl] = useState(window.location.origin); // URL por defecto
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  const { currentUser } = useAuth(); // Obtener información del usuario
  
  // Verificar si es mecánico
  const isMechanic = currentUser?.role === 'Mecánico';
  
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

  useEffect(() => {
    const loadMachines = async () => {
      setLoading(true);
      try {
       const response = await api.get('/maquinas');
       const data = response.data;
        setMachines(data || []);
      } catch (error) {
        console.error("Error loading machines:", error);
        message.error("Error al cargar la lista de máquinas");
      } finally {
        setLoading(false);
      }
    };

    loadMachines();
  }, []);

  useEffect(() => {
    if (selectedMachine) {
      // Crear URL que apunte a la página de detalle de la máquina
      const url = `${baseUrl}/maquinas/${selectedMachine.id}/detail`;
      setQrValue(url);
      setQrTitle(`${selectedMachine.nombre} (${selectedMachine.modelo})`);
    } else {
      setQrValue('');
      setQrTitle('');
    }
  }, [selectedMachine, baseUrl]);

  const handleMachineChange = (machineId) => {
    const machine = machines.find(m => m.id === machineId);
    setSelectedMachine(machine || null);
  };

  const handleBaseUrlChange = (e) => {
    if (!isMechanic) { // Solo permitir cambios si NO es mecánico
      setBaseUrl(e.target.value);
    }
  };

  const handleDownload = () => {
    if (!qrValue) {
      message.warning("Por favor seleccione una máquina primero");
      return;
    }

    // Capturar el div completo con html2canvas
    const qrCodeContainer = document.getElementById('qr-code-container');
    
    html2canvas(qrCodeContainer, { scale: 2 }).then(canvas => {
      const imgData = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.href = imgData;
      link.download = `QR_${selectedMachine.nombre.replace(/\s+/g, '_')}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      message.success("QR descargado correctamente");
    });
  };

  const handlePrint = () => {
    if (!qrValue) {
      message.warning("Por favor seleccione una máquina primero");
      return;
    }
    
    const printWindow = window.open('', '', 'height=500,width=500');
    const qrCodeContainer = document.getElementById('qr-code-container');
    
    html2canvas(qrCodeContainer, { scale: 2 }).then(canvas => {
      const imgData = canvas.toDataURL('image/png');
      
      printWindow.document.write(`
        <html>
          <head>
            <title>QR Código para ${selectedMachine.nombre}</title>
            <style>
              body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 20px;
              }
              .qr-container {
                margin: 20px auto;
                max-width: 300px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                padding: 15px;
              }
              .qr-title {
                font-weight: bold;
                font-size: 16px;
                margin-bottom: 10px;
              }
              .qr-subtitle {
                font-size: 12px;
                color: #666;
                margin-bottom: 15px;
              }
              img {
                max-width: 100%;
              }
              .info {
                margin-top: 15px;
                font-size: 11px;
                color: #888;
              }
            </style>
          </head>
          <body>
            <div class="qr-container">
              <div class="qr-title">${selectedMachine.nombre}</div>
              <div class="qr-subtitle">Modelo: ${selectedMachine.modelo} | S/N: ${selectedMachine.numero_serie}</div>
              <img src="${imgData}" alt="QR Code">
              <div class="info">
                Escanea para ver detalles y registrar mantenimiento
              </div>
            </div>
          </body>
        </html>
      `);
      
      printWindow.document.close();
      printWindow.focus();
      setTimeout(() => {
        printWindow.print();
        printWindow.close();
      }, 250);
    });
  };

  // Contenido común para ambas versiones
  const configCard = (
    <Card 
      title="Configuración" 
      size={isMobile ? "small" : "default"}
      bodyStyle={isMobile ? { padding: '12px' } : {}}
    >
      <div style={{ marginBottom: isMobile ? 12 : 20 }}>
        <Text strong>Seleccione una Máquina:</Text>
        <Select
          style={{ width: '100%', marginTop: 8 }}
          placeholder="Seleccione una máquina"
          onChange={handleMachineChange}
          loading={loading}
          showSearch
          optionFilterProp="children"
          filterOption={(input, option) =>
            option.children.toLowerCase().includes(input.toLowerCase())
          }
          size={isMobile ? "small" : "middle"}
        >
          {machines.map(machine => (
            <Option key={machine.id} value={machine.id}>
              {machine.nombre} ({machine.modelo})
            </Option>
          ))}
        </Select>
      </div>
      
      <div style={{ marginBottom: isMobile ? 12 : 20 }}>
        <Text strong>URL Base:</Text>
        <Input 
          value={baseUrl} 
          onChange={handleBaseUrlChange} 
          placeholder="Ej: https://mi-gmao.local o https://192.168.1.50"
          style={{ marginTop: 8 }}
          disabled={isMechanic} // Deshabilitar para mecánicos
          size={isMobile ? "small" : "middle"}
        />
        <Text type="secondary" style={{ fontSize: isMobile ? 10 : 12 }}>
          {isMechanic 
            ? "La URL base está configurada por el administrador" 
            : "URL para acceder al sistema desde el exterior"}
        </Text>
      </div>
      
      <div style={{ marginTop: isMobile ? 16 : 30 }}>
        <Text strong>URL generada:</Text>
        <Input 
          value={qrValue} 
          readOnly 
          style={{ marginTop: 8 }}
          size={isMobile ? "small" : "middle"}
        />
      </div>
    </Card>
  );

  const qrCard = (
    <Card 
      title="Código QR Generado" 
      size={isMobile ? "small" : "default"}
      bodyStyle={isMobile ? { padding: '12px' } : {}}
    >
      {qrValue ? (
        <div>
          <div 
            id="qr-code-container" 
            style={{ 
              textAlign: 'center', 
              padding: isMobile ? 12 : 20, 
              border: '1px solid #f0f0f0', 
              borderRadius: 4 
            }}
          >
            <Title level={isMobile ? 5 : 4}>{qrTitle}</Title>
            <QRCodeCanvas 
              value={qrValue} 
              size={isMobile ? 150 : 200} 
              level="H" 
              includeMargin={true}
              style={{ margin: isMobile ? '10px auto' : '20px auto' }}
            />
            <Text style={{ fontSize: isMobile ? 12 : 14 }}>
              Escanea para ver detalles y registrar mantenimiento
            </Text>
          </div>
          
          <div style={{ 
            marginTop: isMobile ? 12 : 20, 
            display: 'flex', 
            justifyContent: 'center', 
            gap: isMobile ? 5 : 10 
          }}>
            <Button 
              type="primary" 
              icon={<DownloadOutlined />} 
              onClick={handleDownload}
              size={isMobile ? "small" : "middle"}
            >
              Descargar
            </Button>
            <Button 
              icon={<PrinterOutlined />} 
              onClick={handlePrint}
              size={isMobile ? "small" : "middle"}
            >
              Imprimir
            </Button>
          </div>
        </div>
      ) : (
        <div style={{ 
          textAlign: 'center', 
          padding: isMobile ? 20 : 40 
        }}>
          <Text>Seleccione una máquina para generar el código QR</Text>
        </div>
      )}
    </Card>
  );

  // Renderizado condicional según dispositivo
  if (isMobile) {
    return (
      <MobileLayout title="Generador QR">
        <div style={{ padding: '0 5px' }}>
          {configCard}
          <div style={{ height: '12px' }} />
          {qrCard}
        </div>
      </MobileLayout>
    );
  }

  // Versión de escritorio
  return (
    <div className="qr-generator-container">
      <Title level={2}>Generador de Códigos QR para Máquinas</Title>
      
      <Row gutter={24}>
        <Col span={12}>
          {configCard}
        </Col>
        
        <Col span={12}>
          {qrCard}
        </Col>
      </Row>
    </div>
  );
};

export default QRGenerator;