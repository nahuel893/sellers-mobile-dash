import { Routes, Route } from 'react-router';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
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
            <Route path="/" element={<HomePage />} />
            <Route path="/vendedor/:slug" element={<VendedorPage />} />
            <Route path="/supervisor/:slug" element={<SupervisorPage />} />
            <Route path="/sucursal/:id" element={<SucursalPage />} />
            <Route path="/mapa/:slug" element={<MapaPage />} />
            <Route path="/paneo" element={<PaneoPage />} />
            <Route path="/supervisor/:slug/paneo" element={<PaneoPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </div>
    </AuthProvider>
  );
}
