export type ArcGisBasemapStyle = 'Imagery' | 'Topographic';

const arcgisTileService = 'https://basemaps-api.arcgis.com/arcgis/rest/services/styles';

export function arcgisBasemapTileUrl(style: ArcGisBasemapStyle, apiKey: string | undefined): string | undefined {
  const token = apiKey?.trim();
  if (!token) return undefined;
  return `${arcgisTileService}/ArcGIS:${style}/MapServer/tile/{z}/{y}/{x}?token=${encodeURIComponent(token)}`;
}

export function arcgisBasemapAttribution(style: ArcGisBasemapStyle): string {
  return style === 'Imagery'
    ? 'Tiles &copy; Esri, Maxar, Earthstar Geographics, and the GIS User Community'
    : 'Tiles &copy; Esri, HERE, Garmin, FAO, NOAA, USGS, EPA, and the GIS User Community';
}
