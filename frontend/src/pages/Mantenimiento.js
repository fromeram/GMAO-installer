// src/pages/Mantenimiento.js (Versión final con navegación y fecha corregidas)

import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, DatePicker, Card, Typography, message, Space, Select, Tooltip } from 'antd';
import { SearchOutlined, ClearOutlined, EyeOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import { useNavigate } from 'react-router-dom';
import '../styles/CommonPage.css';
import dayjs from 'dayjs';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

const Mantenimiento = () => {
  const [mantenimientos, setMantenimientos] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [machines, setMachines] = useState([]);
  const [filters, setFilters] = useState({
    dateRange: null,
    machineId: null,
  });

  const navigate = useNavigate();

  useEffect(() => {
    const fetchMachines = async () => {
      try {
        const data = await fetchWithAuth('/maquinas');
        setMachines(data);
      } catch (error) {
        message.error('Error al cargar la lista de máquinas para el filtro.');
      }
    };
    fetchMachines();
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      
      if (filters.dateRange && filters.dateRange[0]) {
        params.append('start', filters.dateRange[0].format('YYYY-MM-DD'));
        params.append('end', filters.dateRange[1].format('YYYY-MM-DD'));
      }
      if (filters.machineId) {
        params.append('machine_id', filters.machineId);
      }
      
      const data = await fetchWithAuth(`/maintenance?${params.toString()}`);
      setMantenimientos(data);
    } catch (error) {
      message.error('Error al cargar los mantenimientos');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleClearFilters = () => {
    setFilters({ dateRange: null, machineId: null });
  };
  
  const columns = [
    {
      title: 'Título del Plan',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: 'Tipo',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: 'Máquina',
      dataIndex: 'machineName',
      key: 'machineName',
    },
    {
      title: 'Fecha de Realización',
      dataIndex: 'finished_at',
      key: 'finished_at',
      render: (date) => (date ? dayjs(date).format('DD/MM/YYYY') : 'N/A'),
      sorter: (a, b) => dayjs(a.finished_at || 0).unix() - dayjs(b.finished_at || 0).unix(),
      defaultSortOrder: 'descend',
    },
    {
        title: 'Acciones',
        key: 'actions',
        align: 'center',
        render: (text, record) => (
            <Tooltip title="Ver Orden de Trabajo Generada">
                <Button
                    type="primary"
                    shape="circle"
                    icon={<EyeOutlined />}
                    // CORRECCIÓN CLAVE: Navega a /ordenes y pasa el ID en el 'state'
                    onClick={() => navigate('/ordenes', { state: { openOrderId: record.work_order_id } })}
                    disabled={!record.work_order_id} 
                />
            </Tooltip>
        )
    }
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2} className="page-title">Historial de Mantenimientos Realizados</Title>
      </div>

      <Card className="form-container">
        <Space direction="vertical" style={{ width: '100%' }}>
          <div style={{ marginBottom: 16 }}>
            <Space wrap>
              <RangePicker 
                onChange={(dates) => handleFilterChange('dateRange', dates)}
                value={filters.dateRange}
                format="DD/MM/YYYY"
              />
              <Select
                showSearch
                placeholder="Seleccionar máquina"
                value={filters.machineId}
                onChange={(value) => handleFilterChange('machineId', value)}
                style={{ width: 250 }}
                allowClear
                filterOption={(input, option) =>
                  option.children.toLowerCase().includes(input.toLowerCase())
                }
              >
                {machines.map(machine => (
                  <Option key={machine.id} value={machine.id}>{machine.nombre}</Option>
                ))}
              </Select>
              <Button 
                type="primary" 
                icon={<SearchOutlined />}
                onClick={fetchData}
                loading={loading}
              >
                Buscar
              </Button>
              <Button 
                icon={<ClearOutlined />}
                onClick={handleClearFilters}
              >
                Limpiar
              </Button>
            </Space>
          </div>

          <Table
            columns={columns}
            dataSource={mantenimientos}
            loading={loading}
            rowKey="id"
            pagination={{ pageSize: 15, showSizeChanger: true }}
            scroll={{ x: true }}
          />
        </Space>
      </Card>
    </div>
  );
};

export default Mantenimiento;