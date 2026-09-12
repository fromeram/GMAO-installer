// App.js (Modificado para incluir Audit Trail)
import 'antd/dist/reset.css';
import './styles/Layout.css';
import './styles/Mobile.css';
import './styles/MainLayout.css';
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import InfoPlanta from './pages/InfoPlanta';
import Mantenimiento from './pages/Mantenimiento';
import MantenimientoPreventivo from './pages/MantenimientoPreventivo';
import Maquinas from './pages/Maquinas';
import Ordenes from './pages/Ordenes';
import Partes from './pages/Partes';
import Secciones from './pages/Secciones';
import Almacenes from './pages/Almacenes';
import Inventario from './pages/Inventario';
import Usuarios from './pages/Usuarios';
import ShiftPatternManagement from './pages/ShiftPatternManagement';
import ProtectedRoute from './components/ProtectedRoute';
import Productos from './pages/Productos';
import MainLayout from './components/MainLayout';
import Suppliers from './pages/Suppliers';
import DocumentManager from './pages/DocumentManager';
import DocumentVerification from './pages/DocumentVerification';
import InventoryReport from './pages/InventoryReport';
import GestionCodigos from './pages/GestionCodigos';
import MachineBOM from './pages/MachineBOM';
import TaskListManagement from './pages/TaskListManagement';
import TaskStepManagement from './pages/TaskStepManagement';
import MachineHistory from './pages/MachineHistory';
import CalendarioTurnos from './pages/CalendarioTurnos';
import CalendarioVacaciones from './pages/CalendarioVacaciones';
import PriceComparator from './pages/PriceComparator';
import LowStockInventory from './pages/LowStockInventory';
import ProductoDetalle from './pages/ProductoDetalle';
import MaintenanceBacklog from './pages/MaintenanceBacklog';
import MachineDetailFixed from './pages/MachineDetailFixed';
import QRGenerator from './pages/QRGenerator';
import QRScanner from './pages/QRScanner';
import DocumentAttachmentManager from './components/DocumentAttachmentManager';
import SchedulerAdmin from './pages/SchedulerAdmin';
// ✅ NUEVO: Import de Audit Trail
import AuditTrail from './pages/AuditTrail';
import Gamification from './pages/Gamification';
import GamificationSetup from './pages/GamificationSetup';
import FormatManager from './pages/FormatManager';
import FormatChangesList from './pages/FormatChangesList';
import FormatReports from './pages/FormatReports';
import AIDashboard from './pages/AIDashboard';
import AIChat from './pages/AIChat';
import AIPredictions from './pages/AIPredictions';
import AIAdmin from './pages/AIAdmin';
import Communications from './pages/Communications';
import CommunicationAdmin from './pages/CommunicationAdmin';
import PlanAnualMantenimiento from './pages/PlanAnualMantenimiento';
import MantenimientoLegal from './pages/MantenimientoLegal'; 


export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="info-planta" element={<InfoPlanta />} />
                    <Route path="mantenimiento" element={<Mantenimiento />} />
                    <Route path="mantenimiento/preventivo" element={<MantenimientoPreventivo />} />
                    <Route path="mantenimiento/legal" element={<MantenimientoLegal />} /> 
                    <Route path="plan-anual" element={<PlanAnualMantenimiento />} />
                    <Route path="maquinas" element={<Maquinas />} />
                    <Route path="maquinas/:machineId/detail" element={<MachineDetailFixed />} />
                    <Route path="maquinas/:machineId/bom" element={<MachineDetailFixed />} />
                    <Route path="maquinas/:machineId/history" element={<MachineDetailFixed />} />
                    <Route path="listas-tareas" element={<TaskListManagement />} />
                    <Route path="listas-tareas/:listId/pasos" element={<TaskStepManagement />} />
                    <Route path="gestion-codigos" element={<GestionCodigos />} />
                    <Route path="ordenes" element={<Ordenes />} />
                    <Route path="partes" element={<Partes />} />
                    <Route path="proveedores" element={<Suppliers />} />
                    <Route path="secciones" element={<Secciones />} />
                    <Route path="almacenes" element={<Almacenes />} />
                    <Route path="inventario" element={<Inventario />} />
                    <Route path="usuarios" element={<Usuarios />} />
                    <Route path="gestion-patrones" element={<ShiftPatternManagement />} />
                    <Route path="calendario-turnos" element={<CalendarioTurnos />} />
                    <Route path="calendario-vacaciones" element={<CalendarioVacaciones />} />
                    <Route path="productos" element={<Productos />} />
                    <Route path="documentos" element={<DocumentManager />} />
                    <Route path="documentos/:id/verificar" element={<DocumentVerification />} />
                    <Route path="reporte-inventario" element={<InventoryReport />} />
                    <Route path="/inventario/bajo-stock" element={<LowStockInventory />} />
                    <Route path="productos/:productId" element={<ProductoDetalle />} />
                    <Route path="backlog-mantenimiento" element={<MaintenanceBacklog />} />
                    <Route path="maquinas/qr" element={<QRGenerator />} />
                    <Route path="maquinas/scan" element={<QRScanner />} />
                    <Route path="documentos/:entityType/:entityId" element={<DocumentAttachmentManager entityType="*" entityId="*" title="Documentos Asociados" />} />
                    <Route path="scheduler-admin" element={<SchedulerAdmin />} />
                    <Route path="comparar-precios" element={<PriceComparator />} />
                    <Route path="/gamification" element={<Gamification />} />
                    <Route path="/gamification-admin" element={<GamificationSetup />} />
                    <Route path="/formatos" element={<FormatManager />} />
                    <Route path="/cambios-formato" element={<FormatChangesList />} />
                    <Route path="/reportes-formato" element={<FormatReports />} />
                    <Route path="/ai-dashboard" element={<AIDashboard />} />
                    <Route path="/ai-chat" element={<AIChat />} />
                    <Route path="/ai-predictions" element={<AIPredictions />} />
                    <Route path="/ai-admin" element={<AIAdmin />} />
                    <Route path="/communications" element={<Communications />} />
                    <Route path="/communication-admin" element={<CommunicationAdmin />} />  
                    
                    {/* ✅ NUEVA RUTA: Audit Trail */}
                    <Route path="audit-trail" element={<AuditTrail />} />
                  </Routes>
                </MainLayout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}