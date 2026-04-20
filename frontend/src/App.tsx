import { Routes, Route } from 'react-router';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import PlatformHome from './pages/PlatformHome';
import HomePage from './pages/HomePage';
import VendedorPage from './pages/VendedorPage';
import SupervisorPage from './pages/SupervisorPage';
import SucursalPage from './pages/SucursalPage';
import MapaPage from './pages/MapaPage';
import PaneoPage from './pages/PaneoPage';
import NotFoundPage from './pages/NotFoundPage';

export default function App() {
  return (
    <AuthProvider>
      <div className="max-w-[480px] mx-auto min-h-screen bg-[#f0f2f5] md:max-w-[900px] xl:max-w-[1400px]">
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes — all require authentication */}
          <Route element={<ProtectedRoute />}>
            {/* Platform home: cards to each dashboard */}
            <Route path="/" element={<PlatformHome />} />

            {/* Sellers dashboard and sub-pages */}
            <Route path="/sellers" element={<HomePage />} />
            <Route path="/sellers/vendedor/:slug" element={<VendedorPage />} />
            <Route path="/sellers/supervisor/:slug" element={<SupervisorPage />} />
            <Route path="/sellers/sucursal/:id" element={<SucursalPage />} />
            <Route path="/sellers/mapa/:slug" element={<MapaPage />} />
            <Route path="/sellers/paneo" element={<PaneoPage />} />
            <Route path="/sellers/supervisor/:slug/paneo" element={<PaneoPage />} />

            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </div>
    </AuthProvider>
  );
}
