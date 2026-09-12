// src/pages/InventoryReport.js (Con Fórmulas Excel - DETECCIÓN AUTOMÁTICA DE IDIOMA y MEJORA EN RESUMEN)
import React, { useState, useEffect, useMemo } from 'react';
import { Table, Button, Select, message, Space, Spin, Alert, Typography, Row, Col, Statistic, Card, Tag, Result } from 'antd';
import { 
  DownloadOutlined, SettingOutlined, ThunderboltOutlined, 
  CloudOutlined, ToolOutlined 
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import * as XLSX from 'xlsx';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import '../styles/CommonPage.css';

const { Title, Text } = Typography;
const { Option } = Select;

const InventoryReport = () => {
  const [inventoryData, setInventoryData] = useState([]);
  const [selectedType, setSelectedType] = useState('todos');
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    showSizeChanger: true,
    showQuickJumper: true,
    pageSizeOptions: ['10', '20', '50', '100'],
    showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} items`,
  });

  const { currentUser } = useAuth();
  const navigate = useNavigate();

  // === FUNCIÓN PARA DETECTAR IDIOMA Y CONFIGURAR FÓRMULAS ===
  const detectLanguageAndFormulas = () => {
    const userLang = navigator.language || navigator.userLanguage || 'en';
    const isSpanish = userLang.startsWith('es') || userLang.includes('ES');
    
    console.log(`Idioma detectado: ${userLang}, Excel en español: ${isSpanish}`);
    
    return {
      isSpanish,
      sumFunction: isSpanish ? 'SUMA' : 'SUM',
      sheetSeparator: isSpanish ? '!' : '.', 
      language: isSpanish ? 'ES' : 'EN'
    };
  };

  // --- Control de Permisos ---
  const isAuthorized = useMemo(() => {
    if (!currentUser) return false;
    const userRole = currentUser?.role?.nombre || (typeof currentUser?.role === 'string' ? currentUser.role : '');
    return ['Administrador', 'Contabilidad', 'Jefe de Taller'].includes(userRole);
  }, [currentUser]);

  // --- Carga de Datos ---
  useEffect(() => {
    if (!currentUser || !isAuthorized) {
       if (currentUser && !isAuthorized) setLoading(false);
       return;
    }

    setLoading(true);
    setError(null);
    fetchWithAuth('/inventario/reporte')
      .then(data => {
         const processedData = Array.isArray(data) 
           ? data
               .map(item => ({ 
                 ...item, 
                 key: item.id,
                 tipo: item.tipo || 'mecánico'
               }))
               .sort((a, b) => (a.product_name || '').localeCompare(b.product_name || '', 'es', { sensitivity: 'base' }))
           : [];
         setInventoryData(processedData);
      })
      .catch(err => {
        console.error("Error fetching inventory report data:", err);
        setError('Error al cargar los datos del inventario. Intente de nuevo.');
        message.error('Error al cargar datos: ' + (err.message || 'Error desconocido'));
      })
      .finally(() => {
        setLoading(false);
      });
  }, [isAuthorized, currentUser]);

  // --- Datos filtrados por tipo ---
  const filteredData = useMemo(() => {
    if (selectedType === 'todos') {
      return inventoryData;
    }
    return inventoryData.filter(item => item.tipo === selectedType);
  }, [inventoryData, selectedType]);

  // --- Configuración de selección de filas ---
  const rowSelection = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys),
  };

  // --- Cálculo de Totales por Tipo ---
  const statisticsByType = useMemo(() => {
    if (!isAuthorized || inventoryData.length === 0) {
        return {
          todos: { count: 0, totalQuantity: 0, totalValue: 0 },
          mecánico: { count: 0, totalQuantity: 0, totalValue: 0 },
          eléctrico: { count: 0, totalQuantity: 0, totalValue: 0 },
          neumático: { count: 0, totalQuantity: 0, totalValue: 0 },
          limpieza: { count: 0, totalQuantity: 0, totalValue: 0 }
        };
    }

    const stats = {
      todos: { count: 0, totalQuantity: 0, totalValue: 0 },
      mecánico: { count: 0, totalQuantity: 0, totalValue: 0 },
      eléctrico: { count: 0, totalQuantity: 0, totalValue: 0 },
      neumático: { count: 0, totalQuantity: 0, totalValue: 0 },
      limpieza: { count: 0, totalQuantity: 0, totalValue: 0 }
    };

    inventoryData.forEach(item => {
      const price = parseFloat(item.price || 0);
      const quantity = parseInt(item.quantity || 0, 10);
      const discount = parseFloat(item.discount || 0);
      const netPrice = price * (1 - discount / 100);
      const itemValue = quantity * netPrice;
      const tipo = item.tipo || 'mecánico';

      stats.todos.count++;
      stats.todos.totalQuantity += quantity;
      stats.todos.totalValue += itemValue;

      if (stats[tipo]) {
        stats[tipo].count++;
        stats[tipo].totalQuantity += quantity;
        stats[tipo].totalValue += itemValue;
      }
    });

    return stats;
  }, [inventoryData, isAuthorized]);

  // --- Cálculo de Totales de Selección ---
  const { totalQuantity, totalValue } = useMemo(() => {
    if (!isAuthorized || filteredData.length === 0) {
        return { totalQuantity: 0, totalValue: 0 };
    }

    let qty = 0;
    let value = 0;
    filteredData.forEach(item => {
      if (selectedRowKeys.includes(item.key)) {
        const price = parseFloat(item.price || 0);
        const quantity = parseInt(item.quantity || 0, 10);
        const discount = parseFloat(item.discount || 0);
        const netPrice = price * (1 - discount / 100);

        if (!isNaN(quantity) && quantity > 0) {
            qty += quantity;
            if (!isNaN(netPrice)) {
              value += quantity * netPrice;
            }
        }
      }
    });
    return { totalQuantity: qty, totalValue: value };
  }, [filteredData, selectedRowKeys, isAuthorized]);

  // --- Funciones auxiliares ---
  const getTypeIcon = (tipo) => {
    switch(tipo) {
      case 'eléctrico': return <ThunderboltOutlined style={{ color: '#faad14' }} />;
      case 'neumático': return <CloudOutlined style={{ color: '#1890ff' }} />;
      case 'limpieza': return <ToolOutlined style={{ color: '#722ed1' }} />;
      case 'mecánico': return <SettingOutlined style={{ color: '#52c41a' }} />;
      default: return <SettingOutlined style={{ color: '#52c41a' }} />;
    }
  };

  const getTypeColor = (tipo) => {
    switch(tipo) {
      case 'eléctrico': return 'gold';
      case 'neumático': return 'blue';
      case 'limpieza': return 'purple';
      case 'mecánico': return 'green';
      default: return 'green';
    }
  };

  // --- Manejo de cambios en la tabla ---
  const handleTableChange = (pag, filters, sorter) => {
    setPagination({
      ...pagination,
      current: pag.current,
      pageSize: pag.pageSize,
    });
  };

  // --- Columnas de la Tabla ---
  const columns = [
    {
      title: 'Tipo',
      dataIndex: 'tipo',
      key: 'tipo',
      width: 100,
      align: 'center',
      render: (tipo) => (
        <Tag color={getTypeColor(tipo)} icon={getTypeIcon(tipo)}>
          {tipo ? tipo.charAt(0).toUpperCase() + tipo.slice(1) : 'Mecánico'}
        </Tag>
      ),
      filters: [
        { text: 'Mecánico', value: 'mecánico' },
        { text: 'Eléctrico', value: 'eléctrico' },
        { text: 'Neumático', value: 'neumático' },
        { text: 'Limpieza', value: 'limpieza' },
      ],
      onFilter: (value, record) => (record.tipo || 'mecánico') === value,
    },
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 70,
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: 'Nombre del Producto',
      dataIndex: 'product_name',
      key: 'product_name',
      ellipsis: { showTitle: false },
      sorter: (a, b) => (a.product_name || '').localeCompare(b.product_name || '', 'es', { sensitivity: 'base' }),
    },
    {
      title: 'Cantidad',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      align: 'center',
      sorter: (a, b) => (a.quantity || 0) - (b.quantity || 0),
      render: (quantity) => quantity || 0,
    },
    {
      title: 'Precio Unit. (€)',
      dataIndex: 'price',
      key: 'price',
      width: 120,
      align: 'right',
      sorter: (a, b) => (parseFloat(a.price || 0)) - (parseFloat(b.price || 0)),
      render: (price) => `${parseFloat(price || 0).toFixed(2)}€`,
    },
    {
      title: 'Descuento (%)',
      dataIndex: 'discount',
      key: 'discount',
      width: 110,
      align: 'center',
      sorter: (a, b) => (parseFloat(a.discount || 0)) - (parseFloat(b.discount || 0)),
      render: (discount) => `${parseFloat(discount || 0).toFixed(1)}%`,
    },
    {
      title: 'Valor Total Línea (€)',
      key: 'total_value',
      width: 130,
      align: 'right',
      render: (_, record) => {
        const price = parseFloat(record.price || 0);
        const quantity = parseInt(record.quantity || 0, 10);
        const discount = parseFloat(record.discount || 0);
        const netPrice = price * (1 - discount / 100);
        return quantity > 0 ? `${(quantity * netPrice).toFixed(2)}€` : '-';
      },
      sorter: (a, b) => {
        const valueA = (a.quantity || 0) * (a.price || 0) * (1 - (a.discount || 0) / 100);
        const valueB = (b.quantity || 0) * (b.price || 0) * (1 - (b.discount || 0) / 100);
        return valueA - valueB;
      }
    },
    {
      title: 'Almacén',
      dataIndex: 'almacen',
      key: 'almacen',
      render: (almacen) => almacen?.name || '-',
      filters: useMemo(() => {
        if (!inventoryData) return [];
        const uniqueWarehouses = [...new Map(inventoryData.map(item => [item.almacen?.id, item.almacen?.name || 'N/A'])).values()];
        return uniqueWarehouses.map(name => ({ text: name, value: name }));
      }, [inventoryData]),
      onFilter: (value, record) => (record.almacen?.name || 'N/A') === value,
    },
    {
      title: 'Proveedor',
      dataIndex: 'proveedor',
      key: 'proveedor',
      render: (proveedor) => proveedor || '-',
      filters: useMemo(() => {
        if (!inventoryData) return [];
        const uniqueSuppliers = [...new Set(inventoryData.map(item => item.proveedor || 'N/A'))];
        return uniqueSuppliers.map(s => ({ text: s, value: s }));
      }, [inventoryData]),
      onFilter: (value, record) => (record.proveedor || 'N/A') === value,
    },
  ];

  // --- FUNCIÓN DE EXPORTACIÓN CON DETECCIÓN AUTOMÁTICA DE IDIOMA ---
  const handleExport = () => {
    if (!isAuthorized) return;
    if (selectedRowKeys.length === 0) {
      message.warning('Seleccione al menos una fila para exportar.');
      return;
    }

    // Detectar idioma del usuario
    const langConfig = detectLanguageAndFormulas();
    
    message.loading({ 
      content: `Generando Excel con fórmulas (${langConfig.language})...`, 
      key: 'export' 
    });

    const selectedData = filteredData.filter(item => selectedRowKeys.includes(item.key));

    // Agrupar por tipo para el reporte
    const dataByType = {
      mecánico: [],
      eléctrico: [],
      neumático: [],
      limpieza: []
    };

    selectedData.forEach(item => {
      const tipo = item.tipo || 'mecánico';
      const exportItem = {
        'ID': item.id,
        'Tipo': tipo.charAt(0).toUpperCase() + tipo.slice(1),
        'Nombre Producto': item.product_name,
        'Cantidad': parseInt(item.quantity || 0, 10),
        'Almacén': item.almacen?.name || '-',
        'Proveedor': item.proveedor || '-',
        'Precio Unitario (€)': parseFloat(item.price || 0),
        'Descuento (%)': parseFloat(item.discount || 0),
        'Valor Total Línea (€)': 0  // Se calculará con fórmula
      };

      if (dataByType[tipo]) {
        dataByType[tipo].push(exportItem);
      } else {
        dataByType.mecánico.push(exportItem);
      }
    });

    try {
      const workbook = XLSX.utils.book_new();
      const sheetSummaryData = [];

      // Crear una hoja por cada tipo que tenga datos
      Object.keys(dataByType).forEach(tipo => {
        if (dataByType[tipo].length > 0) {
          const worksheet = XLSX.utils.json_to_sheet(dataByType[tipo]);
          
          // === Mejoras para evitar @ y asegurar formatos ===
          // Desactivar la detección de tabla implícita por Excel
          // Esto ayuda a evitar el '@' en las fórmulas
          worksheet['!autofilter'] = { ref: XLSX.utils.encode_range(XLSX.utils.decode_range(worksheet['!ref'])) };
          // Esto es más complejo y no siempre necesario, pero puede ayudar si el problema persiste.
          // let Rels = worksheet['!rels'];
          // if (Rels && Array.isArray(Rels)) {
          //     worksheet['!rels'] = Rels.filter(r => !r.Target.includes('table'));
          // }
          
          const range = XLSX.utils.decode_range(worksheet['!ref']);
          
          // Columna I (índice 8) = Valor Total Línea
          for (let R = range.s.r + 1; R <= range.e.r; ++R) {
            const cellD = XLSX.utils.encode_cell({r: R, c: 3}); // Cantidad (Columna D)
            const cellG = XLSX.utils.encode_cell({r: R, c: 6}); // Precio (Columna G)
            const cellH = XLSX.utils.encode_cell({r: R, c: 7}); // Descuento (Columna H)
            const cellI = XLSX.utils.encode_cell({r: R, c: 8}); // Valor Total (Columna I)

            // Fórmula: Cantidad * Precio * (1 - Descuento/100)
            worksheet[cellI] = { 
              f: `=${cellD}*${cellG}*(1-${cellH}/100)`,
              z: '#,##0.00€',
              t: 'n' // Set type to number for clarity
            };
            // Asegurarnos de que las celdas de origen sean números
            if (worksheet[cellD]) worksheet[cellD].t = 'n';
            if (worksheet[cellG]) worksheet[cellG].t = 'n';
            if (worksheet[cellH]) worksheet[cellH].t = 'n';
          }

          // Agregar fila de totales con fórmulas adaptadas al idioma
          const totalRow = range.e.r + 2;
          worksheet[XLSX.utils.encode_cell({r: totalRow, c: 2})] = { v: 'TOTALES:' };
          
          // Total cantidad - Usar la función SUMA/SUM detectada
          worksheet[XLSX.utils.encode_cell({r: totalRow, c: 3})] = { 
            f: `=${langConfig.sumFunction}(D2:D${range.e.r + 1})`,
            t: 'n'
          };
          
          // Total valor - Usar la función SUMA/SUM detectada
          worksheet[XLSX.utils.encode_cell({r: totalRow, c: 8})] = { 
            f: `=${langConfig.sumFunction}(I2:I${range.e.r + 1})`,
            z: '#,##0.00€',
            t: 'n'
          };

          // Actualizar el rango para incluir totales
          worksheet['!ref'] = XLSX.utils.encode_range({
            s: { c: 0, r: 0 },
            e: { c: 8, r: totalRow }
          });

          // Formatos para las columnas
          for (let R = range.s.r + 1; R <= range.e.r; ++R) {
            let cellG = worksheet[XLSX.utils.encode_cell({r: R, c: 6})]; // Precio
            if(cellG) cellG.z = '#,##0.00€';
            let cellH = worksheet[XLSX.utils.encode_cell({r: R, c: 7})]; // Descuento
            if(cellH) cellH.z = '0.0"%"';
            let cellD = worksheet[XLSX.utils.encode_cell({r: R, c: 3})]; // Cantidad
            if(cellD) cellD.z = '0'; // Asegurar formato de número entero
          }

          // Anchos de columna
          worksheet['!cols'] = [
            { wch: 5 }, { wch: 12 }, { wch: 30 }, { wch: 10 }, 
            { wch: 15 }, { wch: 20 }, { wch: 15 }, { wch: 12 }, { wch: 18 }
          ];

          XLSX.utils.book_append_sheet(workbook, worksheet, tipo.charAt(0).toUpperCase() + tipo.slice(1));
          
          // Recopilar datos para hoja resumen
          sheetSummaryData.push({
            tipo: tipo.charAt(0).toUpperCase() + tipo.slice(1),
            count: dataByType[tipo].length,
            sheetName: tipo.charAt(0).toUpperCase() + tipo.slice(1) 
          });
        }
      });

      // ===== HOJA RESUMEN CON FÓRMULAS ADAPTADAS AL IDIOMA Y SINTAXIS DE HOJA CORRECTA =====
      if (sheetSummaryData.length > 0) { 
        const summaryData = [
          ['RESUMEN GENERAL DE INVENTARIO'],
          [''],
          ['Tipo', 'Cantidad Items', 'Cantidad Total', 'Valor Total (€)'],
        ];

        sheetSummaryData.forEach((data) => {
          summaryData.push([
            data.tipo,
            data.count,
            '', // Se llenará con fórmula
            ''  // Se llenará con fórmula
          ]);
        });

        // Fila de totales generales
        summaryData.push(['']);
        summaryData.push(['TOTAL GENERAL', '', '', '']);

        const summarySheet = XLSX.utils.aoa_to_sheet(summaryData);
        // Desactivar la detección de tabla implícita por Excel para la hoja de resumen
        summarySheet['!autofilter'] = { ref: XLSX.utils.encode_range(XLSX.utils.decode_range(summarySheet['!ref'])) };


        // Agregar fórmulas a la hoja resumen adaptadas al idioma
        sheetSummaryData.forEach((data, index) => {
          const rowIndex = index + 3; 
          const sheetName = data.sheetName; 
          
          // CLAVE: Usar '!' como separador de hoja y rodear el nombre de la hoja con comillas simples si tiene espacios o caracteres especiales (como tildes)
          summarySheet[XLSX.utils.encode_cell({r: rowIndex, c: 2})] = {
            f: `=${langConfig.sumFunction}('${sheetName}'!D:D)`, // Referencia a la columna Cantidad (D) de la hoja de tipo
            t: 'n'
          };
          
          summarySheet[XLSX.utils.encode_cell({r: rowIndex, c: 3})] = {
            f: `=${langConfig.sumFunction}('${sheetName}'!I:I)`, // Referencia a la columna Valor Total Línea (€) (I) de la hoja de tipo
            z: '#,##0.00€',
            t: 'n'
          };
        });

        // Totales generales - Usar la función SUMA/SUM detectada
        const totalGeneralRow = 3 + sheetSummaryData.length + 1;
        summarySheet[XLSX.utils.encode_cell({r: totalGeneralRow, c: 2})] = {
          f: `=${langConfig.sumFunction}(C4:C${3 + sheetSummaryData.length})`, // Suma de la columna "Cantidad Total" de la hoja resumen
          t: 'n'
        };
        summarySheet[XLSX.utils.encode_cell({r: totalGeneralRow, c: 3})] = {
          f: `=${langConfig.sumFunction}(D4:D${3 + sheetSummaryData.length})`, // Suma de la columna "Valor Total (€)" de la hoja resumen
          z: '#,##0.00€',
          t: 'n'
        };

        // Anchos para hoja resumen
        summarySheet['!cols'] = [
          { wch: 15 }, { wch: 15 }, { wch: 15 }, { wch: 18 }
        ];

        XLSX.utils.book_append_sheet(workbook, summarySheet, 'Resumen');
      }

      const filename = selectedType === 'todos' 
        ? `reporte_inventario_todos_tipos_${langConfig.language}.xlsx`
        : `reporte_inventario_${selectedType}_${langConfig.language}.xlsx`;
        
      XLSX.writeFile(workbook, filename);
      message.success({ 
        content: `Excel con fórmulas (${langConfig.language}) generado con éxito!`, 
        key: 'export', 
        duration: 3 
      });
    } catch (exportError) {
      console.error("Error generating Excel file:", exportError);
      message.error({ content: 'Error al generar el archivo Excel.', key: 'export', duration: 2 });
    }
  };


  // --- Renderizado Condicional ---
  if (loading && !inventoryData.length) {
    return <Spin tip="Cargando..." style={{ display: 'block', marginTop: '50px' }} />;
  }

  if (!isAuthorized) {
    return (
      <Result
        status="403"
        title="403 - Acceso Denegado"
        subTitle="Lo sentimos, no tienes permiso para acceder a esta página. Contacta al administrador."
        extra={<Button type="primary" onClick={() => navigate('/')}>Volver al Dashboard</Button>}
      />
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Reporte de Inventario por Tipo / Auditoría</Title>
      <Text type="secondary">
        Selecciona el tipo de producto y marca los items que deseas incluir en el reporte de auditoría.
      </Text>

      {/* Estadísticas Generales por Tipo */}
      <Card title="Resumen por Tipo de Producto" style={{ margin: '16px 0' }}>
        <Row gutter={16}>
          <Col xs={24} sm={12} md={5}>
            <Statistic 
              title="Total Items" 
              value={statisticsByType.todos.count}
              prefix={<SettingOutlined style={{ color: '#52c41a' }} />}
            />
          </Col>
          <Col xs={24} sm={12} md={5}>
            <Statistic 
              title="Mecánicos" 
              value={statisticsByType.mecánico.count}
              prefix={<SettingOutlined style={{ color: '#52c41a' }} />}
            />
          </Col>
          <Col xs={24} sm={12} md={5}>
            <Statistic 
              title="Eléctricos" 
              value={statisticsByType.eléctrico.count}
              prefix={<ThunderboltOutlined style={{ color: '#faad14' }} />}
            />
          </Col>
          <Col xs={24} sm={12} md={5}>
            <Statistic 
              title="Neumáticos" 
              value={statisticsByType.neumático.count}
              prefix={<CloudOutlined style={{ color: '#1890ff' }} />}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Statistic 
              title="Limpieza" 
              value={statisticsByType.limpieza.count}
              prefix={<ToolOutlined style={{ color: '#722ed1' }} />}
            />
          </Col>
        </Row>
      </Card>

      {/* Selector de Tipo y Estadísticas de Selección */}
      <Card style={{ margin: '16px 0' }}>
        <Row gutter={16} align="middle">
          <Col xs={24} md={8}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>Filtrar por Tipo:</Text>
              <Select
                value={selectedType}
                onChange={(value) => {
                  setSelectedType(value);
                  setSelectedRowKeys([]);
                  setPagination({...pagination, current: 1});
                }}
                style={{ width: '100%' }}
              >
                <Option value="todos">Todos los Tipos</Option>
                <Option value="mecánico">
                  <Space><SettingOutlined /> Mecánico</Space>
                </Option>
                <Option value="eléctrico">
                  <Space><ThunderboltOutlined /> Eléctrico</Space>
                </Option>
                <Option value="neumático">
                  <Space><CloudOutlined /> Neumático</Space>
                </Option>
                <Option value="limpieza">
                  <Space><ToolOutlined /> Limpieza</Space>
                </Option>
              </Select>
            </Space>
          </Col>
          <Col xs={24} md={16}>
            <Row gutter={16}>
              <Col xs={24} sm={8}>
                <Statistic 
                  title="Items Seleccionados" 
                  value={selectedRowKeys.length} 
                  suffix={`/ ${filteredData.length}`} 
                />
              </Col>
              <Col xs={24} sm={8}>
                <Statistic title="Cantidad Total Seleccionada" value={totalQuantity} />
              </Col>
              <Col xs={24} sm={8}>
                <Statistic
                  title="Valor Total Seleccionado"
                  value={totalValue}
                  precision={2}
                  suffix="€"
                />
              </Col>
            </Row>
          </Col>
        </Row>
      </Card>

      {/* Tabla con Filtros */}
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={handleExport}
            disabled={selectedRowKeys.length === 0 || loading}
          >
            Exportar Selección a Excel (Auto-Detección)
          </Button>
          <Text type="secondary">
            Mostrando {filteredData.length} productos
            {selectedType !== 'todos' && ` de tipo ${selectedType}`}
          </Text>
        </Space>

        {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />}

        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={filteredData}
          pagination={pagination}
          onChange={handleTableChange}
          scroll={{ x: 'max-content' }}
          size="small"
          locale={{ 
            emptyText: loading 
              ? 'Cargando datos...' 
              : `No hay productos ${selectedType !== 'todos' ? `de tipo ${selectedType}` : ''} para mostrar.`
          }}
        />
      </Card>
    </div>
  );
};

export default InventoryReport;