export type ArcGisBasemapStyle = 'Imagery' | 'Topographic';

const arcgisTileServices: Record<ArcGisBasemapStyle, string> = {
  Imagery: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile',
  Topographic: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile',
};

export function arcgisBasemapTileUrl(style: ArcGisBasemapStyle, apiKey: string | undefined): string | undefined {
  const token = apiKey?.trim();
  if (!token) return undefined;
  return `${arcgisTileServices[style]}/{z}/{y}/{x}?token=${encodeURIComponent(token)}`;
}

export function arcgisBasemapAttribution(style: ArcGisBasemapStyle): string {
  return style === 'Imagery'
    ? 'Tiles &copy; Esri, Maxar, Earthstar Geographics, and the GIS User Community'
    : 'Tiles &copy; Esri, HERE, Garmin, FAO, NOAA, USGS, EPA, and the GIS User Community';
}
