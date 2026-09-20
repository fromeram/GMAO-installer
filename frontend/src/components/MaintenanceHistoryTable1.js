// src/components/MaintenanceHistoryTable.js (Versión Responsive)
import React, { useState, useEffect } from 'react';
import { Table, Tag, Spin, Empty, Alert } from 'antd';
import { fetchWithAuth } from '../apiConfig';
import { Link } from 'react-router-dom';

const MaintenanceHistoryTable = ({ machineId, limit = 5 }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

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
    const fetchHistory = async () => {
      setLoading(true);
      try {
        // Obtener las últimas órdenes de trabajo para esta máquina
        const data = await fetchWithAuth(`/maquinas/${machineId}/history?limit=${limit}`);
        setHistory(data || []);
      } catch (err) {
        console.error("Error fetching machine history:", err);
        setError("No se pudo cargar el historial de mantenimiento");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [machineId, limit]);

  // Función para formatear fecha
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      if (isMobile) {
        return new Date(dateString).toLocaleDateString('es-ES', {
          day: '2-digit',
          month: '2-digit',
          year: '2-digit'
        });
      }
      return new Date(dateString).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
    } catch (e) {
      return dateString;
    }
  };

  // Función para obtener color según tipo de mantenimiento
  const getTypeColor = (type) => {
    const colors = {
      'Preventivo': 'green',
      'Correctivo': 'red',
      'Inspección': 'blue',
      'Mejora': 'cyan',
      'Modificación': 'purple',
      'Seguridad': 'orange'
    };
    return colors[type] || 'default';
  };

  // Definición de columnas (versión escritorio)
  const desktopColumns = [
    {
      title: 'Orden',
      dataIndex: 'order_number',
      key: 'order_number',
      render: (text, record) => (
        <Link to={`/ordenes/${record.id}`}>
          {text || `OT-${record.id}`}
        </Link>
      )
    },
    {
      title: 'Fecha',
      dataIndex: 'finished_at',
      key: 'date',
      render: (date) => formatDate(date)
    },
    {
      title: 'Tipo',
      dataIndex: 'work_type',
      key: 'type',
      render: (type) => (
        <Tag color={getTypeColor(type)}>{type}</Tag>
      )
    },
    {
      title: 'Título',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true
    },
    {
      title: 'Técnico',
      dataIndex: ['assigned_to', 'username'],
      key: 'technician',
      render: (text) => text || '-'
    }
  ];

  // Definición de columnas (versión móvil)
  const mobileColumns = [
    {
      title: 'Orden',
      dataIndex: 'order_number',
      key: 'order_number',
      width: 70,
      render: (text, record) => (
        <Link to={`/ordenes/${record.id}`}>
          {text ? text.substring(0, 6) : `OT-${record.id}`}
        </Link>
      )
    },
    {
      title: 'Info',
      dataIndex: 'title',
      key: 'info',
      render: (title, record) => (
        <div>
          <div style={{ fontSize: '13px', fontWeight: 'bold', marginBottom: '2px' }}>
            {title.length > 25 ? `${title.substring(0, 25)}...` : title}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#888' }}>
            <span>{formatDate(record.finished_at)}</span>
            <Tag color={getTypeColor(record.work_type)} style={{ fontSize: '10px', padding: '0 2px', margin: 0 }}>
              {record.work_type}
            </Tag>
          </div>
        </div>
      )
    }
  ];

  if (loading) {
    return <Spin tip={isMobile ? "Cargando..." : "Cargando historial..."} size={isMobile ? "small" : "default"} />;
  }

  if (error) {
    return <Alert message={error} type="error" />;
  }

  if (!history || history.length === 0) {
    return <Empty description="No hay registros de mantenimiento para esta máquina" />;
  }

  return (
    <Table
      columns={isMobile ? mobileColumns : desktopColumns}
      dataSource={history}
      rowKey="id"
      pagination={false}
      size="small"
      style={{ fontSize: isMobile ? '12px' : '14px' }}
    />
  );
};

export default MaintenanceHistoryTable;