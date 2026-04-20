import { Routes, Route } from 'react-router';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { RoleGuard } from './components/RoleGuard';
import LoginPage from './pages/LoginPage';
import PlatformHome from './pages/PlatformHome';
import HomePage from './pages/HomePage';
import VendedorPage from './pages/VendedorPage';
import SupervisorPage from './pages/SupervisorPage';
import SucursalPage from './pages/SucursalPage';
import MapaPage from './pages/MapaPage';
import PaneoPage from './pages/PaneoPage';
import AdminUsersPage from './pages/admin/AdminUsersPage';
import NotFoundPage from './pages/NotFoundPage';
import VentasMapaPage from './pages/ventas-mapa/VentasMapaPage';
import VentasClientePage from './pages/ventas-mapa/VentasClientePage';
import VentasClientesPage from './pages/ventas-mapa/VentasClientesPage';

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected routes — all require authentication */}
        <Route element={<ProtectedRoute />}>
          {/* Platform home: cards to each dashboard */}
          <Route
            path="/"
            element={
              <div className="max-w-[480px] mx-auto min-h-screen bg-[#f0f2f5] md:max-w-[900px] xl:max-w-[1400px]">
                <PlatformHome />
              </div>
            }
          />

          {/* Sellers dashboard and sub-pages */}
          <Route
            path="/sellers"
            element={
              <div className="max-w-[480px] mx-auto min-h-screen bg-[#f0f2f5] md:max-w-[900px] xl:max-w-[1400px]">
                <HomePage />
              </div>
            }
          />
          <Route
            path="/sellers/vendedor/:slug"
            element={
              <div className="max-w-[480px] mx-auto min-h-screen bg-[#f0f2f5] md:max-w-[900px] xl:max-w-[1400px]">
                <VendedorPage />
              </div>
            }
          />
          <Route
            path="/sellers/supervisor/:slug"
            element={
              <div className="max-w-[480px] mx-auto min-h-screen bg-[#f0f2f5] md:max-w-[900px] xl:max-w-[1400px]">
                <SupervisorPage />
              </div>
            }
          />
          <Route
            path="/sellers/sucursal/:id"
            element={
              <div className="max-w-[480px] mx-auto min-h-screen bg-[#f0f2f5] md:max-w-[900px] xl:max-w-[1400px]">
                <SucursalPage />
              </div>
            }
          />
          <Route
            path="/sellers/mapa/:slug"
            element={
              <div className="max-w-[480px] mx-auto min-h-screen bg-[#f0f2f5] md:max-w-[900px] xl:max-w-[1400px]">
                <MapaPage />
              </div>
            }
          />
          <Route
            path="/sellers/paneo"
            element={
              <div className="max-w-[480px] mx-auto min-h-screen bg-[#f0f2f5] md:max-w-[900px] xl:max-w-[1400px]">
                <PaneoPage />
              </div>
            }
          />
          <Route
            path="/sellers/supervisor/:slug/paneo"
            element={
              <div className="max-w-[480px] mx-auto min-h-screen bg-[#f0f2f5] md:max-w-[900px] xl:max-w-[1400px]">
                <PaneoPage />
              </div>
            }
          />

          {/* Ventas Mapa — full-screen dark theme (NO wrapper con max-width) */}
          <Route path="/ventas" element={<VentasMapaPage />} />
          <Route path="/ventas/cliente/:id" element={<VentasClientePage />} />
          <Route path="/ventas/clientes" element={<VentasClientesPage />} />

          {/* Admin routes — restricted to admin role */}
          <Route
            path="/admin/usuarios"
            element={
              <div className="max-w-[480px] mx-auto min-h-screen bg-[#f0f2f5] md:max-w-[900px] xl:max-w-[1400px]">
                <RoleGuard roles={['admin']}>
                  <AdminUsersPage />
                </RoleGuard>
              </div>
            }
          />

          <Route
            path="*"
            element={
              <div className="max-w-[480px] mx-auto min-h-screen bg-[#f0f2f5] md:max-w-[900px] xl:max-w-[1400px]">
                <NotFoundPage />
              </div>
            }
          />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
