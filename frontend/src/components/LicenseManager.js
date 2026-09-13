import React, { useState, useEffect } from 'react';
import { Tag, Modal, Input, Button, message, Card, Typography, Space, Alert, Divider } from 'antd';
import { 
  KeyOutlined, 
  CopyOutlined, 
  SafetyCertificateOutlined, 
  ClockCircleOutlined, 
  CheckCircleOutlined, 
  ExclamationCircleOutlined,
  MailOutlined
} from '@ant-design/icons';
import API_BASE_URL from '../apiConfig';

const { Title, Text, Paragraph } = Typography;

export default function LicenseManager({ isMobile }) {
  const [licenseData, setLicenseData] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [activationKey, setActivationKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [activating, setActivating] = useState(false);

  const fetchLicenseStatus = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL || '/api'}/license/status`);
      if (res.ok) {
        const data = await res.json();
        setLicenseData(data);
      }
    } catch (err) {
      console.error("Error consultando estado de licencia:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLicenseStatus();
    // Consultar cada 30 minutos
    const interval = setInterval(fetchLicenseStatus, 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const copyMachineId = () => {
    if (licenseData?.machine_id) {
      navigator.clipboard.writeText(licenseData.machine_id);
      message.success("ID de Servidor copiado al portapapeles");
    }
  };

  const handleActivate = async () => {
    if (!activationKey.trim()) {
      message.warning("Por favor introduce una clave de activación");
      return;
    }

    try {
      setActivating(true);
      const res = await fetch(`${API_BASE_URL || '/api'}/license/activate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ license_key: activationKey.trim() })
      });

      const result = await res.json();
      if (!res.ok) {
        throw new Error(result.detail || "Clave de activación no válida");
      }

      message.success("¡Licencia activada con éxito!");
      setActivationKey('');
      setModalOpen(false);
      await fetchLicenseStatus();
    } catch (err) {
      message.error(err.message || "Error al activar la licencia");
    } finally {
      setActivating(false);
    }
  };

  if (!licenseData) return null;

  const isLocked = licenseData.is_locked || licenseData.status === 'expired';
  const isLicensed = licenseData.status === 'licensed';
  const daysRemaining = licenseData.days_remaining ?? 0;

  return (
    <>
      {/* 1. Indicador en la barra superior (Header) */}
      <div style={{ display: 'inline-block', cursor: 'pointer', marginRight: 12 }} onClick={() => setModalOpen(true)}>
        {isLicensed ? (
          <Tag color="success" style={{ padding: '4px 10px', borderRadius: 6, fontSize: '12px', fontWeight: 500 }}>
            <SafetyCertificateOutlined style={{ marginRight: 5 }} />
            {!isMobile && "Licencia Oficial: "}{licenseData.licensed_to || "Activa"}
          </Tag>
        ) : isLocked ? (
          <Tag color="error" style={{ padding: '4px 10px', borderRadius: 6, fontSize: '12px', fontWeight: 600 }}>
            <ExclamationCircleOutlined style={{ marginRight: 5 }} />
            Licencia Expirada
          </Tag>
        ) : (
          <Tag color="processing" style={{ padding: '4px 10px', borderRadius: 6, fontSize: '12px', fontWeight: 500 }}>
            <ClockCircleOutlined style={{ marginRight: 5 }} />
            {!isMobile && "Prueba 3 Meses: "}{daysRemaining} {daysRemaining === 1 ? 'día' : 'días'}
          </Tag>
        )}
      </div>

      {/* 2. Modal Normal de Gestión / Activación */}
      <Modal
        title={
          <Space>
            <KeyOutlined style={{ color: '#1677ff' }} />
            <span>Gestión de Licencia - GMAO System</span>
          </Space>
        }
        open={modalOpen && !isLocked}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={580}
      >
        <div style={{ padding: '10px 0' }}>
          {isLicensed ? (
            <Alert
              message="Sistema Licenciado Oficialmente"
              description={`Titular: ${licenseData.licensed_to} (${licenseData.license_type === 'permanente' ? 'Licencia Permanente de por Vida' : `Válida hasta ${licenseData.expires_at}`})`}
              type="success"
              showIcon
              icon={<CheckCircleOutlined />}
              style={{ marginBottom: 16 }}
            />
          ) : (
            <Alert
              message="Periodo de Evaluación Activo (3 Meses Gratuitos)"
              description={`Te quedan ${daysRemaining} días de prueba para evaluar GMAO System en tu planta industrial.`}
              type="info"
              showIcon
              icon={<ClockCircleOutlined />}
              style={{ marginBottom: 16 }}
            />
          )}

          <Card size="small" style={{ background: '#fafafa', marginBottom: 16, borderRadius: 8 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>ID Único de tu Servidor (Machine ID):</Text>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 4 }}>
              <Text code strong style={{ fontSize: 15, letterSpacing: '1px' }}>
                {licenseData.machine_id}
              </Text>
              <Button size="small" icon={<CopyOutlined />} onClick={copyMachineId}>
                Copiar
              </Button>
            </div>
          </Card>

          <Divider style={{ margin: '14px 0' }}>Activar Nueva Licencia</Divider>

          <Paragraph style={{ fontSize: 13, color: '#595959' }}>
            Si dispones de una clave de activación proporcionada por Fran Romera, ingrésala a continuación:
          </Paragraph>

          <Input.TextArea
            rows={3}
            placeholder="Pega aquí tu clave: LIC-GMAO-..."
            value={activationKey}
            onChange={(e) => setActivationKey(e.target.value)}
            style={{ fontFamily: 'monospace', fontSize: 12, marginBottom: 12 }}
          />

          <Button 
            type="primary" 
            block 
            icon={<KeyOutlined />} 
            onClick={handleActivate}
            loading={activating}
            size="large"
          >
            Activar Clave de Licencia
          </Button>

          <Divider style={{ margin: '16px 0' }} />

          <div style={{ textAlign: 'center', color: '#8c8c8c', fontSize: 12 }}>
            <MailOutlined style={{ marginRight: 5 }} />
            Para soporte oficial o licencias permanentes, contacta con <strong>Fran Romera</strong>.
          </div>
        </div>
      </Modal>

      {/* 3. Modal Completo de Bloqueo cuando Expira el Trial de 3 Meses */}
      <Modal
        open={isLocked}
        closable={false}
        maskClosable={false}
        footer={null}
        width={620}
        centered
      >
        <div style={{ textAlign: 'center', padding: '15px 10px' }}>
          <div style={{ fontSize: 52, marginBottom: 12 }}>🔒</div>
          <Title level={3} style={{ marginBottom: 8, color: '#cf1322' }}>
            Periodo de Prueba Finalizado
          </Title>
          <Paragraph style={{ fontSize: 15, color: '#595959', maxWidth: 500, margin: '0 auto 20px auto' }}>
            Los 3 meses de evaluación gratuita de <strong>GMAO System</strong> en este servidor han concluido.
            Para continuar disfrutando del sistema y mantener tus datos activos, ingresa tu clave de activación.
          </Paragraph>

          <Card style={{ background: '#fff1f0', borderColor: '#ffa39e', textAlign: 'left', marginBottom: 20 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>Identificador de tu Servidor (Machine ID):</Text>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 4 }}>
              <Text strong style={{ fontSize: 16, color: '#cf1322', letterSpacing: '1px' }}>
                {licenseData.machine_id}
              </Text>
              <Button size="small" type="primary" danger ghost icon={<CopyOutlined />} onClick={copyMachineId}>
                Copiar ID
              </Button>
            </div>
            <Divider style={{ margin: '12px 0' }} />
            <Text style={{ fontSize: 13, color: '#262626' }}>
              📞 <strong>Cómo obtener tu clave:</strong> Envía este ID de Servidor a <strong>Fran Romera</strong> para recibir tu clave de activación permanente o soporte comercial.
            </Text>
          </Card>

          <div style={{ textAlign: 'left', marginBottom: 12 }}>
            <Text strong style={{ fontSize: 13 }}>Introducir Clave de Activación:</Text>
            <Input.TextArea
              rows={3}
              placeholder="LIC-GMAO-..."
              value={activationKey}
              onChange={(e) => setActivationKey(e.target.value)}
              style={{ fontFamily: 'monospace', fontSize: 12, marginTop: 6 }}
            />
          </div>

          <Button 
            type="primary" 
            danger
            block 
            size="large"
            icon={<KeyOutlined />} 
            onClick={handleActivate}
            loading={activating}
            style={{ height: 45, fontWeight: 600 }}
          >
            Desbloquear y Activar GMAO System
          </Button>
        </div>
      </Modal>
    </>
  );
}
