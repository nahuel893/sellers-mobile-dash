import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import type { Cliente } from '../types/api';

// Fix default marker icon (Leaflet + bundlers issue)
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

interface CustomerMapProps {
  clientes: Cliente[];
}

export default function CustomerMap({ clientes }: CustomerMapProps) {
  if (clientes.length === 0) return null;

  const center: [number, number] = [
    clientes.reduce((sum, c) => sum + c.latitud, 0) / clientes.length,
    clientes.reduce((sum, c) => sum + c.longitud, 0) / clientes.length,
  ];

  return (
    <MapContainer
      center={center}
      zoom={12}
      className="h-[500px] w-full rounded-lg"
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {clientes.map((c, i) => (
        <Marker key={i} position={[c.latitud, c.longitud]}>
          <Popup>
            <strong>{c.fantasia || c.razon_social}</strong>
            {c.des_localidad && <br />}
            {c.des_localidad && <span className="text-gray-500">{c.des_localidad}</span>}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
