// src/components/MaintenanceHistoryTable.js (Versión con Filtros)
import React, { useState, useEffect } from 'react';
import { Table, Tag, Spin, Empty, Alert, Row, Col, DatePicker, Select, Button } from 'antd';
import { ClearOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { Link } from 'react-router-dom';
import moment from 'moment';

const { RangePicker } = DatePicker;
const { Option } = Select;

const MaintenanceHistoryTable = ({ machineId }) => {
  const [history, setHistory] = useState([]); // Almacenará el historial completo sin filtrar
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  // NUEVO: Estado para manejar los filtros aplicados
  const [filters, setFilters] = useState({
    dateRange: null,
    workType: null,
  });

  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const isMobile = windowWidth < 768;

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      setError(null);
      try {
        // MODIFICADO: Quitamos el límite para obtener todo el historial y poder filtrarlo bien
        const data = await fetchWithAuth(`/maquinas/${machineId}/history`);
        setHistory(data || []);
      } catch (err) {
        console.error("Error fetching machine history:", err);
        setError("No se pudo cargar el historial de mantenimiento");
      } finally {
        setLoading(false);
      }
    };

    if (machineId) {
      fetchHistory();
    }
  }, [machineId]);

  // NUEVO: Handlers para los filtros
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleClearFilters = () => {
    setFilters({ dateRange: null, workType: null });
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = moment(dateString);
    if (!date.isValid()) return '-';
    if (isMobile) return date.format('DD/MM/YY');
    return date.format('DD/MM/YYYY');
  };

  const getTypeColor = (type) => {
    const colors = {
      'Preventivo': 'green', 'Correctivo': 'red', 'Inspección': 'blue',
      'Mejora': 'cyan', 'Modificación': 'purple', 'Seguridad': 'orange'
    };
    return colors[type] || 'default';
  };

  // NUEVO: Lógica para aplicar los filtros al historial
  const filteredHistory = history.filter(item => {
    const { dateRange, workType } = filters;
    
    // Filtrar por tipo de trabajo
    if (workType && item.work_type !== workType) {
      return false;
    }

    // Filtrar por rango de fechas (usamos la fecha de finalización)
    if (dateRange && dateRange[0] && item.finished_at) {
      const itemDate = moment(item.finished_at);
      if (!itemDate.isBetween(dateRange[0], dateRange[1], 'day', '[]')) {
        return false;
      }
    }
    
    return true;
  });

  const desktopColumns = [
    // ... (columnas sin cambios)
  ];
  const mobileColumns = [
    // ... (columnas sin cambios)
  ];

  if (loading) return <Spin tip={isMobile ? "Cargando..." : "Cargando historial..."} size={isMobile ? "small" : "default"} />;
  if (error) return <Alert message={error} type="error" />;

  return (
    <>
      {/* NUEVO: Barra de filtros */}
      <div style={{ marginBottom: 16, padding: '12px', background: '#f8f9fa', borderRadius: '8px' }}>
        <Row gutter={[16, 16]} align="bottom">
          <Col xs={24} sm={10}>
            <label>Filtrar por Fecha</label>
            <RangePicker
              value={filters.dateRange}
              onChange={value => handleFilterChange('dateRange', value)}
              style={{ width: '100%' }}
              format="DD/MM/YYYY"
            />
          </Col>
          <Col xs={24} sm={10}>
            <label>Filtrar por Tipo</label>
            <Select
              value={filters.workType}
              onChange={value => handleFilterChange('workType', value)}
              placeholder="Todos los tipos"
              style={{ width: '100%' }}
              allowClear
            >
              <Option value="Preventivo">Preventivo</Option>
              <Option value="Correctivo">Correctivo</Option>
              <Option value="Inspección">Inspección</Option>
              <Option value="Mejora">Mejora</Option>
              <Option value="Modificación">Modificación</Option>
              <Option value="Seguridad">Seguridad</Option>
            </Select>
          </Col>
          <Col xs={24} sm={4}>
            <Button
              icon={<ClearOutlined />}
              onClick={handleClearFilters}
              style={{ width: '100%' }}
            >
              Limpiar
            </Button>
          </Col>
        </Row>
      </div>

      {filteredHistory.length === 0 && !loading ? (
        <Empty description="No hay registros que coincidan con los filtros" />
      ) : (
        <Table
          columns={isMobile ? mobileColumns : desktopColumns}
          dataSource={filteredHistory} // MODIFICADO: Usar el historial filtrado
          rowKey="id"
          pagination={false}
          size="small"
          style={{ fontSize: isMobile ? '12px' : '14px' }}
        />
      )}
    </>
  );
};

// Se mantienen las mismas columnas, solo las copio aquí para que el fichero esté completo.
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
      title: 'Fecha Finalización',
      dataIndex: 'finished_at',
      key: 'date',
      render: (date) => moment(date).isValid() ? moment(date).format('DD/MM/YYYY') : '-',
      sorter: (a, b) => moment(a.finished_at).unix() - moment(b.finished_at).unix(),
    },
    {
      title: 'Tipo',
      dataIndex: 'work_type',
      key: 'type',
      render: (type) => {
        const colors = { 'Preventivo': 'green', 'Correctivo': 'red', 'Inspección': 'blue', 'Mejora': 'cyan', 'Modificación': 'purple', 'Seguridad': 'orange' };
        return <Tag color={colors[type] || 'default'}>{type}</Tag>
      }
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
            <span>{moment(record.finished_at).isValid() ? moment(record.finished_at).format('DD/MM/YY') : '-'}</span>
            <Tag color={{ 'Preventivo': 'green', 'Correctivo': 'red', 'Inspección': 'blue' }[record.work_type] || 'default'} style={{ fontSize: '10px', padding: '0 2px', margin: 0 }}>
              {record.work_type}
            </Tag>
          </div>
        </div>
      )
    }
];


export default MaintenanceHistoryTable;