// src/components/ExportButton.js
// Componente de botón para exportar informes de mantenimiento legal

import React from 'react';
import { Button, Dropdown, Menu, message } from 'antd';
import { FileExcelOutlined, FilePdfOutlined, DownloadOutlined } from '@ant-design/icons';
import { exportLegalReport } from '../utils/exportLegalReports';

export const ExportButton = ({ legalMaintenances }) => {
  const handleExport = async (format) => {
    try {
      // Validar que hay datos para exportar
      if (!legalMaintenances || legalMaintenances.length === 0) {
        message.warning('No hay datos de mantenimiento legal para exportar');
        return;
      }

      message.loading('Generando informe...', 0);
      
      await exportLegalReport(legalMaintenances, format);
      
      message.destroy();
      message.success(`Informe ${format.toUpperCase()} generado correctamente`);
    } catch (error) {
      message.destroy();
      message.error('Error al generar el informe');
      console.error('Export error:', error);
    }
  };

  const exportMenu = (
    <Menu>
      <Menu.Item 
        key="excel" 
        icon={<FileExcelOutlined />} 
        onClick={() => handleExport('excel')}
      >
        Exportar a Excel
        <div style={{ fontSize: '11px', color: '#666', marginTop: 2 }}>
          5 hojas con análisis completo
        </div>
      </Menu.Item>
      <Menu.Item 
        key="pdf" 
        icon={<FilePdfOutlined />} 
        onClick={() => handleExport('pdf')}
      >
        Exportar a PDF
        <div style={{ fontSize: '11px', color: '#666', marginTop: 2 }}>
          Informe ejecutivo profesional
        </div>
      </Menu.Item>
    </Menu>
  );

  return (
    <Dropdown overlay={exportMenu} trigger={['click']}>
      <Button icon={<DownloadOutlined />}>
        Exportar Informe
      </Button>
    </Dropdown>
  );
};