// src/pages/InfoPlanta.js (Versión Responsive CON NAVEGACIÓN A MÁQUINAS)
import React, { useState, useEffect } from 'react';
import { Tree, Card, Typography, Spin, message, Empty, Button, Space, Tooltip } from 'antd';
import { EyeOutlined, ToolOutlined, HistoryOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { useNavigate } from 'react-router-dom';
import '../styles/CommonPage.css';
import MobileLayout from '../components/MobileLayout';

const { Title, Text } = Typography;

const InfoPlanta = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
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

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await fetchWithAuth('/infoplanta');
      
      // ✅ TRANSFORMAR DATOS PARA EL ÁRBOL CON NAVEGACIÓN
      const treeData = response.map(section => ({
        title: (
          <div style={{ 
            padding: '4px 0',
            fontWeight: 'bold',
            fontSize: isMobile ? '14px' : '16px',
            color: '#1890ff'
          }}>
            📍 {section.nombre}
            <Text type="secondary" style={{ 
              marginLeft: '8px', 
              fontSize: isMobile ? '11px' : '12px',
              fontWeight: 'normal'
            }}>
              ({section.lines?.length || 0} líneas, {
                section.lines?.reduce((total, line) => total + (line.machines?.length || 0), 0) || 0
              } máquinas)
            </Text>
          </div>
        ),
        key: `section-${section.id}`,
        icon: <ToolOutlined style={{ color: '#1890ff' }} />,
        children: section.lines.map(line => ({
          title: (
            <div style={{ 
              padding: '2px 0',
              fontSize: isMobile ? '13px' : '14px',
              color: '#52c41a'
            }}>
              🔧 {line.nombre}
              <Text type="secondary" style={{ 
                marginLeft: '8px', 
                fontSize: isMobile ? '10px' : '11px'
              }}>
                ({line.machines?.length || 0} máquinas)
              </Text>
            </div>
          ),
          key: `line-${line.id}`,
          icon: <ToolOutlined style={{ color: '#52c41a', fontSize: '12px' }} />,
          children: line.machines.map(machine => ({
            title: (
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '4px 0',
                borderRadius: '4px',
                transition: 'all 0.3s ease'
              }}
              onMouseEnter={(e) => {
                if (!isMobile) {
                  e.currentTarget.style.backgroundColor = '#f0f9ff';
                  e.currentTarget.style.padding = '4px 8px';
                }
              }}
              onMouseLeave={(e) => {
                if (!isMobile) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.padding = '4px 0';
                }
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ 
                    fontWeight: 'bold',
                    fontSize: isMobile ? '13px' : '14px',
                    color: '#262626'
                  }}>
                    🔩 {machine.nombre}
                  </div>
                  <div style={{ 
                    fontSize: isMobile ? '10px' : '11px', 
                    color: '#666',
                    marginTop: '2px'
                  }}>
                    {machine.marca} {machine.modelo}
                    {machine.criticidad && (
                      <span style={{ 
                        marginLeft: '6px',
                        color: machine.criticidad === 'Alta' ? '#ff4d4f' : 
                              machine.criticidad === 'Media' ? '#fa8c16' : '#52c41a',
                        fontWeight: '500'
                      }}>
                        • {machine.criticidad}
                      </span>
                    )}
                  </div>
                </div>
                
                {/* ✅ BOTONES DE ACCIÓN PARA CADA MÁQUINA */}
                <div style={{ 
                  display: 'flex', 
                  gap: isMobile ? '4px' : '8px',
                  marginLeft: '8px'
                }}>
                  <Tooltip title="Ver detalles completos">
                    <Button
                      type="primary"
                      size="small"
                      icon={<EyeOutlined />}
                      style={{
                        fontSize: isMobile ? '10px' : '12px',
                        height: isMobile ? '24px' : '28px',
                        padding: isMobile ? '0 6px' : '0 8px'
                      }}
                      onClick={(e) => {
                        e.stopPropagation(); // Evitar que se expanda/colapse el nodo
                        console.log('🔍 Navegando a detalles de máquina:', machine.id, machine.nombre);
                        navigate(`/maquinas/${machine.id}/detail`);
                      }}
                    >
                      {!isMobile && "Detalles"}
                    </Button>
                  </Tooltip>
                  
                  {!isMobile && (
                    <Tooltip title="Ver historial de órdenes">
                      <Button
                        size="small"
                        icon={<HistoryOutlined />}
                        style={{
                          fontSize: '12px',
                          height: '28px',
                          padding: '0 8px'
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          console.log('📋 Navegando a historial de máquina:', machine.id, machine.nombre);
                          navigate(`/maquinas/${machine.id}/history`);
                        }}
                      >
                        Historial
                      </Button>
                    </Tooltip>
                  )}
                </div>
              </div>
            ),
            key: `machine-${machine.id}`,
            icon: <div style={{ 
              width: '8px', 
              height: '8px', 
              borderRadius: '50%', 
              backgroundColor: machine.criticidad === 'Alta' ? '#ff4d4f' : 
                              machine.criticidad === 'Media' ? '#fa8c16' : '#52c41a',
              display: 'inline-block'
            }} />,
            isLeaf: true,
            // ✅ DATOS ADICIONALES PARA FUTURAS FUNCIONALIDADES
            machineData: {
              id: machine.id,
              nombre: machine.nombre,
              marca: machine.marca,
              modelo: machine.modelo,
              criticidad: machine.criticidad,
              numero_serie: machine.numero_serie,
              section: section.nombre,
              line: line.nombre
            }
          }))
        }))
      }));
      
      setData(treeData);
      setError(null);
      
      console.log('✅ Estructura de planta cargada:', {
        secciones: treeData.length,
        totalLineas: treeData.reduce((total, section) => total + (section.children?.length || 0), 0),
        totalMaquinas: treeData.reduce((total, section) => 
          total + (section.children?.reduce((lineTotal, line) => 
            lineTotal + (line.children?.length || 0), 0) || 0), 0)
      });
      
    } catch (error) {
      console.error('Error al cargar la información de la planta:', error);
      setError('Error al cargar la información de la planta');
      message.error('Error al cargar la información de la planta');
    } finally {
      setLoading(false);
    }
  };

  // ✅ FUNCIÓN PARA MANEJAR CLICS EN NODOS (OPCIONAL - para clics generales)
  const handleNodeSelect = (selectedKeys, info) => {
    const nodeKey = selectedKeys[0];
    if (!nodeKey) return;

    // Solo procesar clics en máquinas
    if (nodeKey.startsWith('machine-')) {
      const machineId = nodeKey.replace('machine-', '');
      const machineData = info.node.machineData;
      
      console.log('🖱️ Clic en máquina desde árbol:', machineData);
      
      // Navegación opcional desde el árbol completo (si no usan los botones)
      // navigate(`/maquinas/${machineId}/detail`);
    }
  };

  // ✅ FUNCIÓN PARA EXPANDIR/COLAPSAR TODOS LOS NODOS
  const [expandedKeys, setExpandedKeys] = useState([]);
  const [autoExpandParent, setAutoExpandParent] = useState(true);

  const handleExpandAll = () => {
    const allKeys = [];
    data.forEach(section => {
      allKeys.push(section.key);
      if (section.children) {
        section.children.forEach(line => {
          allKeys.push(line.key);
        });
      }
    });
    setExpandedKeys(allKeys);
  };

  const handleCollapseAll = () => {
    setExpandedKeys([]);
  };

  // Contenido común para ambas versiones
  const content = (
    <>
      {error && (
        <div style={{ marginBottom: isMobile ? 8 : 16 }}>
          <Empty 
            description={error} 
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </div>
      )}
      
      <Card 
        className="form-container"
        bodyStyle={{ padding: isMobile ? 8 : 16 }}
        size={isMobile ? "small" : "default"}
        title={
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '8px'
          }}>
            <span>Estructura de la Planta</span>
            {!loading && data.length > 0 && (
              <Space size="small">
                <Button 
                  size="small" 
                  type="text"
                  onClick={handleExpandAll}
                  style={{ fontSize: isMobile ? '11px' : '12px' }}
                >
                  Expandir Todo
                </Button>
                <Button 
                  size="small" 
                  type="text"
                  onClick={handleCollapseAll}
                  style={{ fontSize: isMobile ? '11px' : '12px' }}
                >
                  Colapsar Todo
                </Button>
              </Space>
            )}
          </div>
        }
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: isMobile ? '20px' : '40px' }}>
            <Spin size={isMobile ? "default" : "large"} />
            <div style={{ marginTop: isMobile ? 8 : 16 }}>
              <Text>Cargando estructura de la planta...</Text>
            </div>
          </div>
        ) : data.length === 0 ? (
          <Empty 
            description="No se encontró información de la planta"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <>
            {/* ✅ INFORMACIÓN RESUMIDA */}
            <div style={{ 
              marginBottom: isMobile ? 12 : 16,
              padding: isMobile ? '8px' : '12px',
              backgroundColor: '#f6ffed',
              border: '1px solid #b7eb8f',
              borderRadius: '6px'
            }}>
              <Text style={{ fontSize: isMobile ? '12px' : '14px', color: '#389e0d' }}>
                📊 <strong>Resumen:</strong> {data.length} secciones, {' '}
                {data.reduce((total, section) => total + (section.children?.length || 0), 0)} líneas, {' '}
                {data.reduce((total, section) => 
                  total + (section.children?.reduce((lineTotal, line) => 
                    lineTotal + (line.children?.length || 0), 0) || 0), 0)} máquinas totales
              </Text>
            </div>

            {/* ✅ ÁRBOL INTERACTIVO CON NAVEGACIÓN */}
            <Tree
              showLine
              showIcon
              defaultExpandAll={false}
              expandedKeys={expandedKeys}
              autoExpandParent={autoExpandParent}
              onExpand={(keys) => {
                setExpandedKeys(keys);
                setAutoExpandParent(false);
              }}
              onSelect={handleNodeSelect}
              treeData={data}
              blockNode
              style={{ 
                fontSize: isMobile ? 12 : 14,
                backgroundColor: 'transparent'
              }}
              titleRender={(nodeData) => nodeData.title}
            />

            {/* ✅ INSTRUCCIONES DE USO */}
            <div style={{
              marginTop: isMobile ? 12 : 20,
              padding: isMobile ? '8px' : '12px',
              backgroundColor: '#fff7e6',
              border: '1px solid #ffd591',
              borderRadius: '6px'
            }}>
              <Text style={{ 
                fontSize: isMobile ? '11px' : '12px', 
                color: '#d46b08'
              }}>
                💡 <strong>Instrucciones:</strong> 
                {isMobile 
                  ? " Toca 'Detalles' para ver información completa de cada máquina."
                  : " Haz clic en 'Detalles' para ver información completa de cada máquina, o en 'Historial' para ver sus órdenes de trabajo."
                }
              </Text>
            </div>
          </>
        )}
      </Card>
    </>
  );

  // Renderizado condicional según dispositivo
  if (isMobile) {
    return (
      <MobileLayout title="Información de Planta">
        <div style={{ padding: '0 5px' }}>
          {content}
        </div>
      </MobileLayout>
    );
  }

  // Versión de escritorio
  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2} className="page-title">
          Información de Planta
          {!loading && data.length > 0 && (
            <Text type="secondary" style={{ 
              fontSize: '16px', 
              fontWeight: 'normal',
              marginLeft: '16px'
            }}>
              • Estructura organizacional completa
            </Text>
          )}
        </Title>
      </div>

      {content}
    </div>
  );
};

export default InfoPlanta;