// src/utils/exportLegalReports.js - VERSIÓN CORREGIDA PARA PDF
// Utilidades para exportar informes de mantenimiento legal

import * as XLSX from 'xlsx';
import { jsPDF } from 'jspdf';
import dayjs from 'dayjs';

// Función principal para exportar informes
export const exportLegalReport = async (legalMaintenances, format = 'excel') => {
  try {
    const timestamp = dayjs().format('YYYY-MM-DD_HH-mm');
    const fileName = `Informe_Mantenimiento_Legal_${timestamp}`;

    if (format === 'excel') {
      await exportToExcel(legalMaintenances, fileName);
    } else if (format === 'pdf') {
      await exportToPDF(legalMaintenances, fileName);
    }
  } catch (error) {
    console.error('Error en exportLegalReport:', error);
    throw error;
  }
};

// =============================================================================
// EXPORTACIÓN A EXCEL (ESTA FUNCIONA BIEN)
// =============================================================================

const exportToExcel = async (data, fileName) => {
  const workbook = XLSX.utils.book_new();
  
  // 1. HOJA RESUMEN EJECUTIVO
  const summaryData = generateSummaryData(data);
  const summaryWS = XLSX.utils.aoa_to_sheet([
    ['INFORME DE CUMPLIMIENTO LEGAL Y REGULATORIO'],
    ['Fecha de Generación:', dayjs().format('DD/MM/YYYY HH:mm')],
    [''],
    ['RESUMEN EJECUTIVO'],
    ['Total Inspecciones:', summaryData.total],
    ['Elementos Vencidos:', summaryData.vencidos],
    ['Próximos a Vencer (30 días):', summaryData.proximos],
    ['Vigentes:', summaryData.vigentes],
    ['Nivel de Cumplimiento:', `${summaryData.porcentajeCumplimiento}%`],
    [''],
    ['DISTRIBUCIÓN POR CATEGORÍAS'],
    ['Categoría', 'Total', 'Vencidos'],
    ...summaryData.categorias.map(cat => [cat.nombre, cat.cantidad, cat.vencidos])
  ]);
  
  XLSX.utils.book_append_sheet(workbook, summaryWS, 'Resumen Ejecutivo');

  // 2. HOJA DETALLE COMPLETO
  const detailData = data.map(item => ({
    'ID': item.id,
    'Inspección/Certificación': item.title,
    'Equipo/Instalación': item.maquina_nombre || 'N/A',
    'Categoría': item.tipo_regulacion || 'General',
    'Frecuencia': item.frecuencia,
    'Última Inspección': item.fechaInicio ? dayjs(item.fechaInicio).format('DD/MM/YYYY') : 'N/A',
    'Próxima Inspección': item.next_maintenance_date ? dayjs(item.next_maintenance_date).format('DD/MM/YYYY') : 'N/A',
    'Días Restantes': item.next_maintenance_date ? dayjs(item.next_maintenance_date).diff(dayjs(), 'day') : 'N/A',
    'Estado': getStatusText(item.next_maintenance_date),
    'Nivel Criticidad': getCriticalityLevel(item.next_maintenance_date),
    'Organismo': item.organismo_certificador || 'N/A',
    'Nº Certificado': item.numero_certificado || 'N/A',
    'Normativa': item.normativa_aplicable || 'N/A',
    'Observaciones': item.description || 'N/A'
  }));
  
  const detailWS = XLSX.utils.json_to_sheet(detailData);
  XLSX.utils.book_append_sheet(workbook, detailWS, 'Detalle Completo');

  // 3. HOJA ELEMENTOS CRÍTICOS
  const criticalData = data.filter(item => {
    const days = dayjs(item.next_maintenance_date).diff(dayjs(), 'day');
    return days <= 30;
  }).map(item => ({
    'Prioridad': dayjs(item.next_maintenance_date).diff(dayjs(), 'day') <= 0 ? 'CRÍTICA' : 'ALTA',
    'Inspección': item.title,
    'Equipo': item.maquina_nombre || 'N/A',
    'Vencimiento': dayjs(item.next_maintenance_date).format('DD/MM/YYYY'),
    'Días': dayjs(item.next_maintenance_date).diff(dayjs(), 'day'),
    'Acción Requerida': dayjs(item.next_maintenance_date).diff(dayjs(), 'day') <= 0 ? 'RENOVAR INMEDIATAMENTE' : 'PROGRAMAR RENOVACIÓN',
    'Organismo': item.organismo_certificador || 'N/A'
  }));
  
  const criticalWS = XLSX.utils.json_to_sheet(criticalData);
  XLSX.utils.book_append_sheet(workbook, criticalWS, 'Elementos Críticos');

  // 4. HOJA CRONOGRAMA ANUAL
  const scheduleData = generateAnnualSchedule(data);
  const scheduleWS = XLSX.utils.json_to_sheet(scheduleData);
  XLSX.utils.book_append_sheet(workbook, scheduleWS, 'Cronograma Anual');

  // 5. HOJA ORGANISMOS CERTIFICADORES
  const organismsData = generateOrganismsData(data);
  const organismsWS = XLSX.utils.json_to_sheet(organismsData);
  XLSX.utils.book_append_sheet(workbook, organismsWS, 'Organismos Certificadores');

  // Exportar archivo
  XLSX.writeFile(workbook, `${fileName}.xlsx`);
};

// =============================================================================
// EXPORTACIÓN A PDF - VERSIÓN SIMPLIFICADA SIN AUTOTABLE
// =============================================================================

const exportToPDF = async (data, fileName) => {
  try {
    console.log('Iniciando exportación PDF...');
    
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.width;
    const pageHeight = doc.internal.pageSize.height;
    let yPosition = 20;

    // ENCABEZADO PRINCIPAL
    doc.setFontSize(18);
    doc.setTextColor(25, 118, 210);
    doc.text('INFORME DE CUMPLIMIENTO LEGAL Y REGULATORIO', pageWidth / 2, yPosition, { align: 'center' });
    
    yPosition += 15;
    doc.setFontSize(12);
    doc.setTextColor(100, 100, 100);
    doc.text(`Generado el: ${dayjs().format('DD/MM/YYYY HH:mm')}`, pageWidth / 2, yPosition, { align: 'center' });
    
    yPosition += 25;

    // RESUMEN EJECUTIVO
    const summaryData = generateSummaryData(data);
    doc.setFontSize(16);
    doc.setTextColor(0, 0, 0);
    doc.text('RESUMEN EJECUTIVO', 20, yPosition);
    yPosition += 15;

    // Datos del resumen en formato simple
    doc.setFontSize(12);
    const summaryItems = [
      `Total de Inspecciones: ${summaryData.total}`,
      `Elementos Vencidos: ${summaryData.vencidos}`,
      `Próximos a Vencer (30 días): ${summaryData.proximos}`,
      `Vigentes: ${summaryData.vigentes}`,
      `Nivel de Cumplimiento: ${summaryData.porcentajeCumplimiento}%`
    ];

    summaryItems.forEach(item => {
      doc.text(item, 25, yPosition);
      yPosition += 8;
    });

    yPosition += 10;

    // ELEMENTOS CRÍTICOS
    const criticalData = data.filter(item => {
      const days = dayjs(item.next_maintenance_date).diff(dayjs(), 'day');
      return days <= 30;
    });

    if (criticalData.length > 0) {
      doc.setFontSize(16);
      doc.setTextColor(220, 53, 69);
      doc.text('⚠️ ELEMENTOS CRÍTICOS', 20, yPosition);
      yPosition += 15;

      doc.setFontSize(10);
      doc.setTextColor(0, 0, 0);

      criticalData.forEach((item, index) => {
        if (yPosition > pageHeight - 30) {
          doc.addPage();
          yPosition = 20;
        }

        const days = dayjs(item.next_maintenance_date).diff(dayjs(), 'day');
        const status = days <= 0 ? 'VENCIDO' : 'PRÓXIMO A VENCER';
        
        doc.text(`${index + 1}. ${item.title}`, 25, yPosition);
        yPosition += 6;
        doc.text(`   Equipo: ${item.maquina_nombre || 'N/A'}`, 25, yPosition);
        yPosition += 6;
        doc.text(`   Vencimiento: ${dayjs(item.next_maintenance_date).format('DD/MM/YYYY')} (${days} días)`, 25, yPosition);
        yPosition += 6;
        doc.text(`   Estado: ${status}`, 25, yPosition);
        yPosition += 10;
      });
    }

    // NUEVA PÁGINA PARA DETALLE COMPLETO
    doc.addPage();
    yPosition = 20;

    doc.setFontSize(16);
    doc.setTextColor(0, 0, 0);
    doc.text('DETALLE COMPLETO DE INSPECCIONES', 20, yPosition);
    yPosition += 15;

    doc.setFontSize(10);
    
    data.forEach((item, index) => {
      if (yPosition > pageHeight - 40) {
        doc.addPage();
        yPosition = 20;
      }

      doc.text(`${index + 1}. ${item.title}`, 20, yPosition);
      yPosition += 6;
      doc.text(`   Equipo: ${item.maquina_nombre || 'N/A'}`, 20, yPosition);
      yPosition += 6;
      doc.text(`   Frecuencia: ${item.frecuencia}`, 20, yPosition);
      yPosition += 6;
      doc.text(`   Próxima Inspección: ${item.next_maintenance_date ? dayjs(item.next_maintenance_date).format('DD/MM/YYYY') : 'N/A'}`, 20, yPosition);
      yPosition += 6;
      doc.text(`   Estado: ${getStatusText(item.next_maintenance_date)}`, 20, yPosition);
      yPosition += 6;
      doc.text(`   Organismo: ${item.organismo_certificador || 'N/A'}`, 20, yPosition);
      yPosition += 12;
    });

    // PIE DE PÁGINA EN TODAS LAS PÁGINAS
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(150, 150, 150);
      doc.text(
        `Página ${i} de ${pageCount} - Sistema de Mantenimiento Legal`,
        pageWidth / 2,
        pageHeight - 10,
        { align: 'center' }
      );
    }

    // Guardar PDF
    console.log('Guardando PDF...');
    doc.save(`${fileName}.pdf`);
    console.log('PDF guardado correctamente');

  } catch (error) {
    console.error('Error específico en exportToPDF:', error);
    throw error;
  }
};

// =============================================================================
// FUNCIONES AUXILIARES (IGUAL QUE ANTES)
// =============================================================================

const generateSummaryData = (data) => {
  const total = data.length;
  let vencidos = 0;
  let proximos = 0;
  let vigentes = 0;

  const categorias = {};

  data.forEach(item => {
    const days = dayjs(item.next_maintenance_date).diff(dayjs(), 'day');
    
    if (days < 0) vencidos++;
    else if (days <= 30) proximos++;
    else vigentes++;

    const categoria = item.tipo_regulacion || 'General';
    if (!categorias[categoria]) {
      categorias[categoria] = { nombre: categoria, cantidad: 0, vencidos: 0 };
    }
    categorias[categoria].cantidad++;
    if (days < 0) categorias[categoria].vencidos++;
  });

  const porcentajeCumplimiento = total > 0 ? Math.round(((vigentes + proximos) / total) * 100) : 0;

  return {
    total,
    vencidos,
    proximos,
    vigentes,
    porcentajeCumplimiento,
    categorias: Object.values(categorias)
  };
};

const generateAnnualSchedule = (data) => {
  const schedule = [];
  const currentYear = dayjs().year();
  
  data.forEach(item => {
    if (item.next_maintenance_date) {
      const date = dayjs(item.next_maintenance_date);
      if (date.year() === currentYear) {
        schedule.push({
          Mes: date.format('MMMM'),
          Día: date.format('DD'),
          Inspección: item.title,
          Equipo: item.maquina_nombre || 'N/A',
          Frecuencia: item.frecuencia,
          Organismo: item.organismo_certificador || 'N/A'
        });
      }
    }
  });

  return schedule.sort((a, b) => dayjs(`${a.Mes} ${a.Día}`).diff(dayjs(`${b.Mes} ${b.Día}`)));
};

const generateOrganismsData = (data) => {
  const organisms = {};
  
  data.forEach(item => {
    const org = item.organismo_certificador || 'Sin asignar';
    if (!organisms[org]) {
      organisms[org] = {
        Organismo: org,
        'Total Inspecciones': 0,
        'Próximas 30 días': 0,
        'Vencidas': 0
      };
    }
    
    organisms[org]['Total Inspecciones']++;
    
    const days = dayjs(item.next_maintenance_date).diff(dayjs(), 'day');
    if (days < 0) organisms[org]['Vencidas']++;
    else if (days <= 30) organisms[org]['Próximas 30 días']++;
  });

  return Object.values(organisms);
};

const getStatusText = (nextDate) => {
  if (!nextDate) return 'Sin fecha';
  
  const days = dayjs(nextDate).diff(dayjs(), 'day');
  
  if (days < 0) return `VENCIDO (${Math.abs(days)} días)`;
  if (days <= 15) return `CRÍTICO (${days} días)`;
  if (days <= 30) return `PRÓXIMO (${days} días)`;
  return `VIGENTE (${days} días)`;
};

const getCriticalityLevel = (nextDate) => {
  if (!nextDate) return 'DESCONOCIDO';
  
  const days = dayjs(nextDate).diff(dayjs(), 'day');
  
  if (days < 0) return 'CRÍTICA';
  if (days <= 15) return 'ALTA';
  if (days <= 30) return 'MEDIA';
  return 'BAJA';
};