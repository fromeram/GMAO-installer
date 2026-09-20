// src/pages/QRScanner.js (Versión Responsive)
import React, { useState, useEffect } from 'react';
import { Card, Button, message, Typography, Spin, Alert } from 'antd';
import { ScanOutlined, CloseOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { QrReader } from 'react-qr-reader';
import MobileLayout from '../components/MobileLayout';

const { Title, Text } = Typography;

const QRScanner = () => {
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  const navigate = useNavigate();
  
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

  const handleScan = (data) => {
    if (data) {
      setScanning(false);
      setResult(data);
      
      // Procesar el resultado para extraer ID de máquina
      try {
        const url = new URL(data);
        const pathSegments = url.pathname.split('/');
        const machineIdIndex = pathSegments.findIndex(segment => segment === 'maquinas') + 1;
        
        if (machineIdIndex > 0 && machineIdIndex < pathSegments.length) {
          const machineId = pathSegments[machineIdIndex];
          
          // Mostrar mensaje de éxito
          message.success(`QR escaneado correctamente. Redirigiendo...`);
          
          // Redirigir a la página de la máquina
          setTimeout(() => {
            navigate(`/maquinas/${machineId}/detail`);
          }, 1000);
        } else {
          setError("El QR no contiene una URL válida de máquina");
        }
      } catch (err) {
        console.error("Error processing QR code:", err);
        setError("Error al procesar el código QR");
      }
    }
  };

  const handleError = (err) => {
    console.error("QR Scanner error:", err);
    setError("Error al acceder a la cámara. Verifica los permisos.");
    setScanning(false);
  };

  const startScanning = () => {
    setScanning(true);
    setResult(null);
    setError(null);
  };

  const stopScanning = () => {
    setScanning(false);
  };

  // Contenido del escáner QR (compartido entre móvil y desktop)
  const scannerContent = (
    <>
      {scanning ? (
        <div>
          <div style={{ marginBottom: isMobile ? 8 : 16, textAlign: 'center' }}>
            <Text>Apunta la cámara al código QR de la máquina</Text>
          </div>
          
          <div style={{ 
            maxWidth: isMobile ? '100%' : '400px', 
            margin: '0 auto' 
          }}>
            <QrReader
              delay={300}
              onError={handleError}
              onScan={handleScan}
              style={{ width: '100%' }}
              facingMode="environment" // Usar cámara trasera
            />
          </div>
          
          <div style={{ marginTop: isMobile ? 8 : 16, textAlign: 'center' }}>
            <Button 
              type="primary" 
              danger
              icon={<CloseOutlined />} 
              onClick={stopScanning}
              size={isMobile ? "small" : "middle"}
            >
              Cancelar
            </Button>
          </div>
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: isMobile ? 10 : 20 }}>
          {error && (
            <Alert
              message="Error"
              description={error}
              type="error"
              showIcon
              style={{ marginBottom: isMobile ? 10 : 20 }}
              closable
              onClose={() => setError(null)}
            />
          )}
          
          {result && (
            <div style={{ marginBottom: isMobile ? 10 : 20 }}>
              <Alert
                message="QR Escaneado"
                description={<Text copyable>{result}</Text>}
                type="success"
                showIcon
              />
            </div>
          )}
          
          <Button 
            type="primary" 
            icon={<ScanOutlined />} 
            onClick={startScanning}
            size={isMobile ? "middle" : "large"}
          >
            Escanear Código QR
          </Button>
          
          <div style={{ marginTop: isMobile ? 10 : 20 }}>
            <Text type="secondary" style={{ fontSize: isMobile ? 12 : 14 }}>
              Esta función permite escanear códigos QR de máquinas para acceder rápidamente a su información.
            </Text>
          </div>
        </div>
      )}
    </>
  );

  // Renderizado condicional según el tamaño de pantalla
  if (isMobile) {
    return (
      <MobileLayout title="Escáner QR">
        <Card size="small" bodyStyle={{ padding: '12px' }}>
          {scannerContent}
        </Card>
      </MobileLayout>
    );
  }

  return (
    <div className="page-container">
      <Title level={2}>Escáner de Códigos QR</Title>
      
      <Card>
        {scannerContent}
      </Card>
    </div>
  );
};

export default QRScanner;