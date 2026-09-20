// src/pages/Inventario.js (Con Fórmulas Excel - DETECCIÓN AUTOMÁTICA DE IDIOMA y MEJORA EN RESUMEN)
import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Modal, Form, Input, Select, message, Space, Spin, Alert, Typography, Popconfirm, Row, Col, Statistic, Card, Tag, AutoComplete, Tooltip } from 'antd';
import { 
  DeleteOutlined, EditOutlined, PlusOutlined, SearchOutlined, 
  FileExcelOutlined, EyeOutlined, ToolOutlined,
  SettingOutlined, ThunderboltOutlined, CloudOutlined,
  DollarOutlined, DatabaseOutlined, FilterOutlined, ClockCircleOutlined  // ← NUEVOS ICONOS
} from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';
import * as XLSX from 'xlsx';
import { useAuth } from '../contexts/AuthContext';
import '../styles/CommonPage.css';

const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

const Inventario = () => {
  const [inventario, setInventario] = useState({ items: [], total_value: 0 });
  const [inventarioFiltered, setInventarioFiltered] = useState({ items: [], total_value: 0 });
  const [loading, setLoading] = useState(true);
  const { currentUser } = useAuth();
  
  // Estados para búsqueda
  const [searchTerm, setSearchTerm] = useState('');
  const [searchOptions, setSearchOptions] = useState([]);
  const [selectedType, setSelectedType] = useState('todos');
  
  // Estados para Modal "Donde se Usa"
  const [usageModalVisible, setUsageModalVisible] = useState(false);
  const [partUsageData, setPartUsageData] = useState([]);
  const [loadingUsage, setLoadingUsage] = useState(false);
  const [viewingPart, setViewingPart] = useState(null);

  // Estados para paginación
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 15,
    showSizeChanger: true,
    showQuickJumper: true,
    pageSizeOptions: ['10', '15', '30', '50', '100'],
    showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} productos`,
  });

  // === FUNCIÓN PARA DETECTAR IDIOMA Y CONFIGURAR FÓRMULAS ===
  const detectLanguageAndFormulas = () => {
    const userLang = navigator.language || navigator.userLanguage || 'en';
    const isSpanish = userLang.startsWith('es') || userLang.includes('ES');
    
    console.log(`Idioma detectado: ${userLang}, Excel en español: ${isSpanish}`);
    
    return {
      isSpanish,
      sumFunction: isSpanish ? 'SUMA' : 'SUM',
      sheetSeparator: isSpanish ? '!' : '.', // Keep this flexible for now, but will use '!' in formulas
      language: isSpanish ? 'ES' : 'EN'
    };
  };

  // --- Constantes para tipos de producto ---
  const PRODUCT_TYPES = [
    { value: 'mecánico', label: 'Mecánico', icon: <SettingOutlined />, color: 'green' },
    { value: 'eléctrico', label: 'Eléctrico', icon: <ThunderboltOutlined />, color: 'gold' },
    { value: 'neumático', label: 'Neumático', icon: <CloudOutlined />, color: 'blue' },
    { value: 'limpieza', label: 'Limpieza', icon: <ToolOutlined />, color: 'purple' }
  ];

  // Función helper para obtener información del tipo
  const getTypeInfo = (tipo) => {
    return PRODUCT_TYPES.find(t => t.value === tipo) || PRODUCT_TYPES[0];
  };

  // Función para manejar cambios en la paginación
  const handleTableChange = (pag, filters, sorter) => {
    console.log('Cambio en paginación inventario:', pag);
    setPagination({
      ...pagination,
      current: pag.current,
      pageSize: pag.pageSize,
    });
  };

  // Verificar permisos - incluir Contabilidad y Administradores
  const userRole = currentUser?.role?.nombre || (typeof currentUser?.role === 'string' ? currentUser?.role : '');
  const canViewInventory = ['Administrador', 'Contabilidad', 'Calidad', 'Jefe de Mantenimiento', 'Técnico'].includes(userRole);
  const canModifyInventory = ['Administrador', 'Jefe de Mantenimiento'].includes(userRole);

  // --- Carga inicial de datos ---
  useEffect(() => {
    if (currentUser && canViewInventory) {
      fetchInventarioData();
    }
  }, [currentUser, canViewInventory]);

  const fetchInventarioData = async () => {
    setLoading(true);
    try {
      const data = await fetchWithAuth('/inventario');
      console.log("Datos de inventario recibidos:", data);
      
      if (data && Array.isArray(data.items)) {
        // Asegurar que cada item tenga un tipo definido
        const itemsWithTypes = data.items.map(item => ({
          ...item,
          tipo: item.tipo || 'mecánico'
        }));
        
        const inventarioData = {
          items: itemsWithTypes,
          total_value: data.total_value || 0
        };
        
        setInventario(inventarioData);
        setInventarioFiltered(inventarioData);
      } else {
        console.warn("Estructura de datos inesperada:", data);
        setInventario({ items: [], total_value: 0 });
        setInventarioFiltered({ items: [], total_value: 0 });
      }
    } catch (error) {
      console.error("Error al cargar inventario:", error);
      message.error(`Error al cargar inventario: ${error.message || 'Error desconocido'}`);
      setInventario({ items: [], total_value: 0 });
      setInventarioFiltered({ items: [], total_value: 0 });
    } finally {
      setLoading(false);
    }
  };

  // --- Función de filtrado ---
  useEffect(() => {
    let filtered = inventario.items;

    // Filtrar por tipo
    if (selectedType !== 'todos') {
      filtered = filtered.filter(item => (item.tipo || 'mecánico') === selectedType);
    }

    // Filtrar por término de búsqueda
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase().trim();
      filtered = filtered.filter(item => 
        (item.nombre && item.nombre.toLowerCase().includes(term)) ||
        (item.id && item.id.toString().includes(term))
      );
    }

    // Calcular valor total de items filtrados
    const totalValueFiltered = filtered.reduce((sum, item) => {
      const precio = parseFloat(item.precio) || 0;
      const cantidad = parseInt(item.cantidad) || 0;
      return sum + (precio * cantidad);
    }, 0);

    setInventarioFiltered({
      items: filtered,
      total_value: totalValueFiltered
    });

    // Reset pagination when filters change
    setPagination(prev => ({
      ...prev,
      current: 1
    }));
  }, [inventario, searchTerm, selectedType]);

  // Función para filtrar por tipo desde estadísticas
  const handleTypeStatClick = (tipo) => {
    console.log(`Filtro por tipo desde estadística: ${tipo}`);
    setSelectedType(tipo);
    setSearchTerm('');
  };

  // Función para limpiar filtros
  const handleClearFilters = () => {
    setSelectedType('todos');
    setSearchTerm('');
  };

  // Función para obtener opciones de autocompletado
  const getSearchSuggestions = (value) => {
    if (!value) {
      return inventario.items.slice(0, 10).map(item => ({
        value: item.nombre,
        label: `${item.nombre} (ID: ${item.id})${item.tipo ? ` - ${item.tipo}` : ''}`
      }));
    }

    const filtered = inventario.items
      .filter(item => item.nombre?.toLowerCase().includes(value.toLowerCase()))
      .slice(0, 10)
      .map(item => ({
        value: item.nombre,
        label: `${item.nombre} (ID: ${item.id})${item.tipo ? ` - ${item.tipo}` : ''}`
      }));

    return filtered.length > 0 ? filtered : [{ 
      value: value, 
      label: `No se encontraron resultados para "${value}"` 
    }];
  };

  // Función para búsqueda en autocompletado
  const handleAutoCompleteSearch = (value) => {
    if (!value) {
      const recentOptions = inventario.items.slice(0, 10).map(item => ({ value: item.nombre }));
      setSearchOptions(recentOptions);
      return;
    }

    const filtered = inventario.items
      .filter(item => item.nombre?.toLowerCase().includes(value.toLowerCase()))
      .sort((a, b) => (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' }))
      .slice(0, 10)
      .map(item => ({ value: item.nombre }));

    setSearchOptions(filtered);
  };

  // Función para mostrar uso
  const handleShowUsage = useCallback(async (record) => {
    const partName = record.nombre || `ID ${record.id}`;
    console.log(`Mostrando uso para repuesto: ${partName} (ID: ${record.id})`);
    setViewingPart({ id: record.id, nombre: partName });
    setPartUsageData([]);
    setLoadingUsage(true);
    setUsageModalVisible(true);
    try {
      const usageData = await fetchWithAuth(`/inventory/${record.id}/usage`);
      setPartUsageData(usageData || []);
      console.log("Usage data received:", usageData);
      if (!usageData || usageData.length === 0) {
        message.info(`El repuesto "${partName}" no está actualmente asociado a ninguna máquina en el BOM.`);
      }
    } catch (error) {
      console.error("Error fetching usage data:", error);
      message.error(`Error al cargar datos de uso: ${error.message || 'Error desconocido'}`);
      setUsageModalVisible(false);
    } finally {
      setLoadingUsage(false);
    }
  }, []);

  // === FUNCIÓN PARA EXPORTAR EXCEL CON FÓRMULAS ===
  const handleExportExcel = () => {
    console.log("Exportando inventario a Excel con fórmulas...");
    if (!inventarioFiltered || inventarioFiltered.items.length === 0) {
      message.warning("No hay datos de inventario para exportar.");
      return;
    }
    
    // Detectar idioma del usuario para las fórmulas
    const langConfig = detectLanguageAndFormulas();

    message.loading({ 
      content: `Generando Excel con fórmulas (${langConfig.language})...`, 
      key: 'exportExcelInv' 
    });
    
    // Agrupar por tipo para el reporte
    const dataByType = {
      mecánico: [],
      eléctrico: [],
      neumático: [],
      limpieza: []
    };

    inventarioFiltered.items.forEach(item => {
      const tipo = item.tipo || 'mecánico';
      const exportItem = {
        'ID': item.id,
        'Tipo': tipo.charAt(0).toUpperCase() + tipo.slice(1),
        'Producto': item.nombre,
        'Cantidad': parseInt(item.cantidad) || 0,
        'Almacén': item.almacen,
        'Precio Unitario (€)': parseFloat(item.precio) || 0,
        'Proveedor': item.proveedor || '-',
        'Valor Total (€)': 0  // Se calculará con fórmula
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
          // Considerar eliminar relaciones de tabla si existen. A veces, XLSX genera XML que Excel interpreta como tablas.
          // let Rels = worksheet['!rels']; // Not directly available this way
          // if (Rels && Array.isArray(Rels)) { // This is more complex, might need to delve into workbook.rels if needed
          //     worksheet['!rels'] = Rels.filter(r => !r.Target.includes('table'));
          // }

          const range = XLSX.utils.decode_range(worksheet['!ref']);
          
          // Columna H (índice 7) = Valor Total
          for (let R = range.s.r + 1; R <= range.e.r; ++R) {
            const cellD = XLSX.utils.encode_cell({r: R, c: 3}); // Cantidad (Columna D)
            const cellF = XLSX.utils.encode_cell({r: R, c: 5}); // Precio (Columna F)
            const cellH = XLSX.utils.encode_cell({r: R, c: 7}); // Valor Total (Columna H)

            // Fórmula: Cantidad * Precio
            worksheet[cellH] = { 
              f: `=${cellD}*${cellF}`,
              z: '#,##0.00€',
              t: 'n' // Explicitly set type to number
            };
            // Asegurarse de que las celdas de origen sean números para evitar #VALUE! en Excel
            if (worksheet[cellD]) worksheet[cellD].t = 'n';
            if (worksheet[cellF]) worksheet[cellF].t = 'n';
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
          worksheet[XLSX.utils.encode_cell({r: totalRow, c: 7})] = { 
            f: `=${langConfig.sumFunction}(H2:H${range.e.r + 1})`,
            z: '#,##0.00€',
            t: 'n'
          };

          // Actualizar el rango para incluir totales
          worksheet['!ref'] = XLSX.utils.encode_range({
            s: { c: 0, r: 0 },
            e: { c: 7, r: totalRow }
          });

          // Formatos para las columnas
          for (let R = range.s.r + 1; R <= range.e.r; ++R) {
            let cellF = worksheet[XLSX.utils.encode_cell({r: R, c: 5})]; // Precio
            if(cellF) cellF.z = '#,##0.00€';
            let cellD = worksheet[XLSX.utils.encode_cell({r: R, c: 3})]; // Cantidad
            if(cellD) cellD.z = '0'; // Ensure integer format for quantity
          }

          // Anchos de columna
          worksheet['!cols'] = [
            { wch: 8 }, { wch: 12 }, { wch: 35 }, { wch: 10 }, 
            { wch: 20 }, { wch: 15 }, { wch: 25 }, { wch: 18 }
          ];

          XLSX.utils.book_append_sheet(workbook, worksheet, tipo.charAt(0).toUpperCase() + tipo.slice(1));
          
          // Recopilar datos para hoja resumen
          sheetSummaryData.push({
            tipo: tipo.charAt(0).toUpperCase() + tipo.slice(1),
            count: dataByType[tipo].length,
            sheetName: tipo.charAt(0).toUpperCase() + tipo.slice(1) // Keep the sheet name consistent for referencing
          });
        }
      });

      // ===== HOJA RESUMEN CON FÓRMULAS ADAPTADAS AL IDIOMA Y SINTAXIS DE HOJA CORRECTA =====
      if (sheetSummaryData.length > 0) { // Should be > 0 to create if there's any data
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
          const rowIndex = index + 3; // Filas de datos empiezan en índice 3
          const sheetName = data.sheetName; // Get the actual sheet name
          
          // Fórmulas en hoja resumen - Usar la función SUMA/SUM detectada
          // CLAVE: Usar '!' como separador de hoja y rodear el nombre de la hoja con comillas simples si tiene espacios o caracteres especiales (como tildes)
          summarySheet[XLSX.utils.encode_cell({r: rowIndex, c: 2})] = {
            f: `=${langConfig.sumFunction}('${sheetName}'!D:D)`, // Referencia a la columna Cantidad (D)
            t: 'n'
          };
          
          summarySheet[XLSX.utils.encode_cell({r: rowIndex, c: 3})] = {
            f: `=${langConfig.sumFunction}('${sheetName}'!H:H)`, // Referencia a la columna Valor Total (€) (H)
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
        ? `Inventario_General_Todos_Tipos_${langConfig.language}.xlsx`
        : `Inventario_General_${selectedType}_${langConfig.language}.xlsx`;
        
      XLSX.writeFile(workbook, filename);
      message.success({ 
        content: `Exportación a Excel con fórmulas (${langConfig.language}) completada.`, 
        key: 'exportExcelInv', 
        duration: 3 
      });
    } catch (error) {
      console.error("Error al generar Excel:", error);
      message.error({ content: 'Error al generar el archivo Excel.', key: 'exportExcelInv', duration: 3 });
    }
  };
  // Calculate statistics by type
  const statisticsByType = () => {
    const stats = {
      todos: { count: 0 },
      mecánico: { count: 0 },
      eléctrico: { count: 0 },
      neumático: { count: 0 },
      limpieza: { count: 0 }
    };

    inventario.items.forEach(item => {
      const tipo = item.tipo || 'mecánico';
      stats.todos.count++;
      if (stats[tipo]) {
        stats[tipo].count++;
      }
    });

    return stats;
  };

  const stats = statisticsByType();

  // Columnas de la tabla
  const columns = [
    {
      title: 'Tipo',
      dataIndex: 'tipo',
      key: 'tipo',
      width: 100,
      align: 'center',
      render: (tipo) => {
        const typeInfo = getTypeInfo(tipo);
        return (
          <Tag color={typeInfo.color} icon={typeInfo.icon}>
            {typeInfo.label}
          </Tag>
        );
      },
      filters: PRODUCT_TYPES.map(type => ({
        text: type.label,
        value: type.value
      })),
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
      title: 'Nombre',
      dataIndex: 'nombre',
      key: 'nombre',
      sorter: (a, b) => (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' }),
    },
    {
      title: 'Cantidad',
      dataIndex: 'cantidad',
      key: 'cantidad',
      width: 100,
      align: 'center',
      sorter: (a, b) => (a.cantidad || 0) - (b.cantidad || 0),
      render: (cantidad) => {
        if (cantidad <= 0) {
          return <span style={{ color: '#ff4d4f', fontWeight: 'bold' }}>{cantidad || 0}</span>;
        }
        return cantidad || 0;
      },
    },
    {
      title: 'Almacén',
      dataIndex: 'almacen',
      key: 'almacen',
      render: (almacen) => almacen || '-',
    },
    {
      title: 'Precio (€)',
      dataIndex: 'precio',
      key: 'precio',
      width: 120,
      align: 'right',
      sorter: (a, b) => (parseFloat(a.precio) || 0) - (parseFloat(b.precio) || 0),
      render: (precio) => {
        if (precio === '****') return 'No autorizado';
        const numPrice = parseFloat(precio) || 0;
        return `${numPrice.toFixed(2)}€`;
      },
    },
    {
      title: 'Valor Total (€)',
      key: 'valor_total',
      width: 130,
      align: 'right',
      sorter: (a, b) => {
        const valueA = (parseFloat(a.precio) || 0) * (parseInt(a.cantidad) || 0);
        const valueB = (parseFloat(b.precio) || 0) * (parseInt(b.cantidad) || 0);
        return valueA - valueB;
      },
      render: (_, record) => {
        if (record.precio === '****') return 'No autorizado';
        const precio = parseFloat(record.precio) || 0;
        const cantidad = parseInt(record.cantidad) || 0;
        const total = precio * cantidad;
        return `${total.toFixed(2)}€`;
      },
    },
    {
      title: 'Proveedor',
      dataIndex: 'proveedor',
      key: 'proveedor',
      render: (proveedor) => proveedor || '-',
    },
    {
      title: 'Acciones',
      key: 'acciones',
      width: 120,
      align: 'center',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="Ver dónde se usa">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => handleShowUsage(record)}
              size="small"
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  if (!currentUser) {
    return (
      <div className="page-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <Spin size="large" tip="Cargando..." />
      </div>
    );
  }

  // Si no tiene permisos, mostrar mensaje
  if (!canViewInventory) {
    return (
      <div className="page-container">
        <Alert
          message="Acceso Denegado"
          description="No tienes permisos para acceder al inventario. Contacta al administrador."
          type="warning"
          showIcon
          style={{ margin: '20px' }}
        />
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2} className="page-title">
          <ToolOutlined className="page-icon" /> Inventario General
        </Title>
        <Text type="secondary" className="page-description">
          Consulta y gestión del inventario completo. Total de productos: {inventarioFiltered.items.length}
        </Text>
      </div>

      {/* Estadísticas por Tipo */}
      <Card title="Resumen por Tipo de Producto" className="stats-card">
        <Row gutter={16}>
          <Col xs={24} sm={12} md={4}>
            <Statistic
              title="Total Items"
              value={stats.todos.count}
              prefix={<SettingOutlined style={{ color: '#52c41a' }} />}
              className="clickable-stat"
              onClick={() => handleTypeStatClick('todos')}
            />
          </Col>
          <Col xs={24} sm={12} md={5}>
            <Statistic
              title="Mecánicos"
              value={stats.mecánico.count}
              prefix={<SettingOutlined style={{ color: '#52c41a' }} />}
              className="clickable-stat"
              onClick={() => handleTypeStatClick('mecánico')}
            />
          </Col>
          <Col xs={24} sm={12} md={5}>
            <Statistic
              title="Eléctricos"
              value={stats.eléctrico.count}
              prefix={<ThunderboltOutlined style={{ color: '#faad14' }} />}
              className="clickable-stat"
              onClick={() => handleTypeStatClick('eléctrico')}
            />
          </Col>
          <Col xs={24} sm={12} md={5}>
            <Statistic
              title="Neumáticos"
              value={stats.neumático.count}
              prefix={<CloudOutlined style={{ color: '#1890ff' }} />}
              className="clickable-stat"
              onClick={() => handleTypeStatClick('neumático')}
            />
          </Col>
          <Col xs={24} sm={12} md={5}>
            <Statistic
              title="Limpieza"
              value={stats.limpieza.count}
              prefix={<ToolOutlined style={{ color: '#722ed1' }} />}
              className="clickable-stat"
              onClick={() => handleTypeStatClick('limpieza')}
            />
          </Col>
        </Row>
        
        {/* NUEVA FILA CON VALOR TOTAL */}
        <Row gutter={16} style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #f0f0f0' }}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Valor Total del Inventario"
              value={inventarioFiltered.total_value}
              precision={2}
              suffix="€"
              prefix={<DollarOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff', fontSize: '24px', fontWeight: 'bold' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Productos Mostrados"
              value={inventarioFiltered.items.length}
              suffix={`/ ${inventario.items.length}`}
              prefix={<DatabaseOutlined style={{ color: '#52c41a' }} />}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Filtros Aplicados"
              value={selectedType === 'todos' ? 'Ninguno' : selectedType}
              prefix={<FilterOutlined style={{ color: '#faad14' }} />}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Última Actualización"
              value={new Date().toLocaleTimeString()}
              prefix={<ClockCircleOutlined style={{ color: '#722ed1' }} />}
            />
          </Col>
        </Row>
      </Card>

      {/* Controles de Búsqueda y Filtros */}
      <Card className="filter-card">
        <Row gutter={16} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>Buscar Producto:</Text>
              <AutoComplete
                style={{ width: '100%' }}
                options={getSearchSuggestions(searchTerm)}
                onSearch={setSearchTerm}
                onSelect={(value) => setSearchTerm(value)}
                value={searchTerm}
                placeholder="Buscar por nombre o ID..."
              >
                <Input
                  prefix={<SearchOutlined />}
                  allowClear
                  onClear={() => setSearchTerm('')}
                />
              </AutoComplete>
            </Space>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>Filtrar por Tipo:</Text>
              <Select
                value={selectedType}
                onChange={setSelectedType}
                style={{ width: '100%' }}
              >
                <Option value="todos">Todos los Tipos</Option>
                {PRODUCT_TYPES.map(type => (
                  <Option key={type.value} value={type.value}>
                    <Space>{type.icon} {type.label}</Space>
                  </Option>
                ))}
              </Select>
            </Space>
          </Col>
          <Col xs={24} sm={24} md={10}>
            <Space wrap>
              <Button
                type="primary"
                icon={<FileExcelOutlined />}
                onClick={handleExportExcel}
                disabled={inventarioFiltered.items.length === 0}
              >
                Exportar a Excel (Auto-Detección)
              </Button>
              {(searchTerm || selectedType !== 'todos') && (
                <Button onClick={handleClearFilters} icon={<SearchOutlined />}>
                  Limpiar Filtros
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Tabla de Inventario */}
      <Card className="table-card">
        <Table
          columns={columns}
          dataSource={inventarioFiltered.items}
          rowKey="id"
          loading={loading}
          pagination={pagination}
          onChange={handleTableChange}
          scroll={{ x: 'max-content' }}
          size="small"
          locale={{
            emptyText: loading
              ? 'Cargando datos...'
              : 'No hay productos que coincidan con los filtros aplicados'
          }}
        />
      </Card>

      {/* Modal para mostrar dónde se usa */}
      <Modal
        title={`¿Dónde se usa el repuesto "${viewingPart?.nombre}"?`}
        open={usageModalVisible}
        onCancel={() => setUsageModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setUsageModalVisible(false)}>
            Cerrar
          </Button>
        ]}
        width={800}
      >
        {loadingUsage ? (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin size="large" tip="Cargando datos de uso..." />
          </div>
        ) : (
          <div>
            {partUsageData.length === 0 ? (
              <Alert
                message="Este repuesto no está asociado a ninguna máquina"
                description="El repuesto no aparece en ningún BOM (Bill of Materials) actual."
                type="info"
                showIcon
              />
            ) : (
              <Table
                dataSource={partUsageData}
                rowKey="machine_id"
                pagination={false}
                columns={[
                  { title: 'ID Máquina', dataIndex: 'machine_id', key: 'machine_id' },
                  { title: 'Nombre Máquina', dataIndex: 'machine_name', key: 'machine_name' },
                  { title: 'Cantidad Requerida', dataIndex: 'quantity_required', key: 'quantity_required' },
                  { title: 'Ubicación', dataIndex: 'location', key: 'location' },
                ]}
                size="small"
              />
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Inventario;