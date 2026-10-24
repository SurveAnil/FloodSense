import { describe, expect, it } from 'vitest';
import { arcgisBasemapAttribution, arcgisBasemapTileUrl } from './arcgis-basemap';

describe('ArcGIS basemap configuration', () => {
  it('returns authenticated imagery and topographic tile URLs', () => {
    expect(arcgisBasemapTileUrl('Imagery', ' test key '))
      .toBe('https://basemaps-api.arcgis.com/arcgis/rest/services/styles/ArcGIS:Imagery/MapServer/tile/{z}/{y}/{x}?token=test%20key');
    expect(arcgisBasemapTileUrl('Topographic', 'test-key'))
      .toBe('https://basemaps-api.arcgis.com/arcgis/rest/services/styles/ArcGIS:Topographic/MapServer/tile/{z}/{y}/{x}?token=test-key');
  });

  it('does not enable ArcGIS tiles when the key is missing', () => {
    expect(arcgisBasemapTileUrl('Imagery', undefined)).toBeUndefined();
    expect(arcgisBasemapTileUrl('Topographic', '  ')).toBeUndefined();
  });

  it('provides attribution for both Esri styles', () => {
    expect(arcgisBasemapAttribution('Imagery')).toContain('Esri');
    expect(arcgisBasemapAttribution('Topographic')).toContain('USGS');
  });
});
