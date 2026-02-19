import { Routes, Route } from 'react-router';
import HomePage from './pages/HomePage';
import VendedorPage from './pages/VendedorPage';
import SupervisorPage from './pages/SupervisorPage';
import SucursalPage from './pages/SucursalPage';
import MapaPage from './pages/MapaPage';
import NotFoundPage from './pages/NotFoundPage';

export default function App() {
  return (
    <div className="max-w-[480px] mx-auto min-h-screen bg-[#f0f2f5] md:max-w-[900px] xl:max-w-[1400px]">
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/vendedor/:slug" element={<VendedorPage />} />
        <Route path="/supervisor/:slug" element={<SupervisorPage />} />
        <Route path="/sucursal/:id" element={<SucursalPage />} />
        <Route path="/mapa/:slug" element={<MapaPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  );
}
