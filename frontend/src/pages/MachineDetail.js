// src/pages/MachineDetail.js
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Card, Typography, Descriptions, Tabs, Button, Statistic, Row, Col, 
  Divider, Space, Spin, Alert, Image, Empty
} from 'antd';
import { ArrowLeftOutlined, ToolOutlined, FileOutlined, HistoryOutlined, BarChartOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import DocumentAttachmentManager from '../components/DocumentAttachmentManager';
import MaintenanceHistoryTable from '../components/MaintenanceHistoryTable'; 
import { Link } from 'react-router-dom';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const MachineDetail = () => {
  const { machineId } = useParams();
  const navigate = useNavigate();
  const [machine, setMachine] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [metrics, setMetrics] = useState({
    mtbf: 0,
    mttr: 0,
    disponibilidad: 0,
    lastYear: {
      preventivas: 0,
      correctivas: 0,
      total: 0
    }
  });

  // Cargar información
  useEffect(() => {
    const fetchMachineData = async () => {
      setLoading(true);
      try {
        // Cargar datos básicos de la máquina
        const machineData = await fetchWithAuth(`/maquinas/${machineId}`);
        setMachine(machineData);
        
        // Cargar métricas (podría ser un nuevo endpoint)
        try {
          const metricsData = await fetchWithAuth(`/maquinas/${machineId}/metrics`);
          setMetrics(metricsData);
        } catch (metricsError) {
          console.error("Error loading metrics:", metricsError);
          // No mostrar error general, solo log para métricas
        }
      } catch (error) {
        console.error("Error fetching machine details:", error);
        setError("No se pudo cargar la información de la máquina");
      } finally {
        setLoading(false);
      }
    };

    fetchMachineData();
  }, [machineId]);

  if (loading) {
    return <Spin size="large" tip="Cargando información de la máquina..." />;
  }

  if (error) {
    return (
      <Alert
        message="Error"
        description={error}
        type="error"
        showIcon
        action={
          <Button size="small" onClick={() => navigate('/maquinas')}>
            Volver
          </Button>
        }
      />
    );
  }

  if (!machine) {
    return <Alert message="Máquina no encontrada" type="warning" showIcon />;
  }

  return (
    <div className="machine-detail-container">
      <div className="header-with-back">
        <Space>
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={() => navigate('/maquinas')}
          >
            Volver
          </Button>
          <Title level={2}>{machine.nombre}</Title>
        </Space>
      </div>

      {/* Información general */}
      <Card>
        <Descriptions title="Información General" bordered>
          <Descriptions.Item label="ID">{machine.id}</Descriptions.Item>
          <Descriptions.Item label="Modelo">{machine.modelo}</Descriptions.Item>
          <Descriptions.Item label="Marca">{machine.marca}</Descriptions.Item>
          <Descriptions.Item label="Número de Serie">{machine.numero_serie}</Descriptions.Item>
          <Descriptions.Item label="Sección" span={2}>
            {machine.section?.nombre || "-"}
          </Descriptions.Item>
          <Descriptions.Item label="Línea" span={2}>
            {machine.line?.nombre || "-"}
          </Descriptions.Item>
          <Descriptions.Item label="Criticidad" span={2}>
            {machine.criticidad || "No especificada"}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Métricas y KPIs */}
      <Card title="Métricas de Rendimiento" style={{ marginTop: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic 
              title="MTBF (Tiempo Medio Entre Fallos)" 
              value={metrics.mtbf} 
              suffix="horas"
              precision={1}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="MTTR (Tiempo Medio de Reparación)" 
              value={metrics.mttr} 
              suffix="horas"
              precision={1}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Disponibilidad" 
              value={metrics.disponibilidad} 
              suffix="%"
              precision={2}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="OTs en el último año" 
              value={metrics.lastYear.total}
              valueStyle={{ color: '#3f8600' }}
            />
            <div style={{ fontSize: '12px', marginTop: '8px' }}>
              Preventivas: {metrics.lastYear.preventivas} | 
              Correctivas: {metrics.lastYear.correctivas}
            </div>
          </Col>
        </Row>
      </Card>

      {/* Tabs con documentación, historial y repuestos */}
      <Card style={{ marginTop: 16 }}>
        <Tabs defaultActiveKey="documentation">
          <TabPane 
            tab={<span><FileOutlined /> Documentación</span>} 
            key="documentation"
          >
            <DocumentAttachmentManager 
              entityType="machine" 
              entityId={machineId} 
              title="Documentos de la Máquina"
            />
          </TabPane>
          
          <TabPane 
            tab={<span><HistoryOutlined /> Historial de Mantenimiento</span>} 
            key="history"
          >
            <div style={{ marginBottom: 16 }}>
              <Link to={`/maquinas/${machineId}/history`}>
                <Button type="primary">Ver Historial Completo</Button>
              </Link>
            </div>
            {/* Componente que muestra las últimas 5 órdenes */}
            <MaintenanceHistoryTable machineId={machineId} limit={5} />
          </TabPane>
          
          <TabPane 
            tab={<span><ToolOutlined /> Lista de Repuestos (BOM)</span>} 
            key="parts"
          >
            <div style={{ marginBottom: 16 }}>
              <Link to={`/maquinas/${machineId}/bom`}>
                <Button type="primary">Gestionar Repuestos</Button>
              </Link>
            </div>
            {/* Tabla simplificada de partes */}
            {machine.parts && machine.parts.length > 0 ? (
              <table className="parts-table">
                <thead>
                  <tr>
                    <th>ID Repuesto</th>
                    <th>Nombre</th>
                    <th>Cantidad Requerida</th>
                    <th>Stock Actual</th>
                  </tr>
                </thead>
                <tbody>
                  {machine.parts.map(part => (
                    <tr key={part.inventory_id}>
                      <td>{part.inventory_id}</td>
                      <td>{part.part?.product_name || "-"}</td>
                      <td className="numeric">{part.quantity}</td>
                      <td className="numeric">{part.part?.quantity || 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <Empty description="No hay repuestos asociados a esta máquina" />
            )}
          </TabPane>
          
          <TabPane 
            tab={<span><BarChartOutlined /> Análisis</span>} 
            key="analysis"
          >
            {/* Gráficos de análisis */}
            <div style={{ textAlign: 'center', padding: 20 }}>
              <div id="failureChart" style={{ height: 300 }}></div>
              <Divider />
              <div id="maintenanceTypeChart" style={{ height: 300 }}></div>
            </div>
          </TabPane>
        </Tabs>
      </Card>

      {/* Galería de imágenes */}
      <Card title="Galería de Imágenes" style={{ marginTop: 16 }}>
        {machine.images && machine.images.length > 0 ? (
          <Image.PreviewGroup>
            <div style={{ display: 'flex', overflowX: 'auto', gap: 8, padding: 8 }}>
              {machine.images.map((img, index) => (
                <Image
                  key={index}
                  width={200}
                  src={img.url}
                  alt={`Imagen ${index + 1} de ${machine.nombre}`}
                />
              ))}
            </div>
          </Image.PreviewGroup>
        ) : (
          <Empty description="No hay imágenes disponibles para esta máquina" />
        )}
        <div style={{ marginTop: 16, textAlign: 'center' }}>
          <Button type="primary">
            Añadir Imágenes
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default MachineDetail;