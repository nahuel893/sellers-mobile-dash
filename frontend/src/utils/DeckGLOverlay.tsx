/**
 * DeckGLOverlay — monta MapboxOverlay de @deck.gl/mapbox dentro de un <Map>
 * de react-map-gl usando el hook useControl.
 *
 * Ref: https://deck.gl/docs/api-reference/mapbox/mapbox-overlay
 */
import { useEffect } from 'react';
import { useControl } from 'react-map-gl/maplibre';
import { MapboxOverlay } from '@deck.gl/mapbox';
import type { MapboxOverlayProps } from '@deck.gl/mapbox';

interface DeckGLOverlayProps extends MapboxOverlayProps {
  interleaved?: boolean;
}

export function DeckGLOverlay({ interleaved, ...props }: DeckGLOverlayProps) {
  const overlay = useControl<MapboxOverlay>(
    () => new MapboxOverlay({ interleaved, ...props }),
    { position: 'top-left' },
  );

  useEffect(() => {
    overlay.setProps(props);
  });

  return null;
}
