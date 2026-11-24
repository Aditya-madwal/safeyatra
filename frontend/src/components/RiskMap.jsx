// The Leaflet map: risk-coloured roads, hazard layers, routes and markers.

import L from 'leaflet'
import { useEffect, useMemo, useRef } from 'react'
import {
  CircleMarker, GeoJSON, LayerGroup, LayersControl, MapContainer, Marker, Polyline, Popup,
  TileLayer, Tooltip, useMap, useMapEvents,
} from 'react-leaflet'
import { CHAMOLI_CENTER, POI_COLORS, POI_LABELS, RISK_COLORS, RISK_LABELS } from '../constants'
import { useIsDark } from './ui.jsx'

const ROAD_WEIGHT = { trunk: 4, primary: 3.5, secondary: 3, tertiary: 2.5 }
const ROUTE_COLOR = '#2c4a6b'
const ROUTE_COLOR_DARK = '#9cc0e6'
const LANDSLIDE_COLORS = { NASA: '#7a5a9e', NEWS: '#a3456f' }
const canvas = L.canvas({ padding: 0.5 }) // fast drawing for ~6,000 road pieces

// calm gray base map so the risk colours carry the information (free, no key)
const ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas'
const ESRI_ATTR = 'Tiles &copy; Esri, HERE, Garmin, &copy; OpenStreetMap contributors'

function roadStyle(feature, dimmed) {
  const p = feature.properties
  const base = (p.highway || '').replace('_link', '')
  if (p.closed) return { color: '#27272a', weight: 3.5, dashArray: '5 5', opacity: 0.9 }
  return { color: RISK_COLORS[p.cls], weight: ROAD_WEIGHT[base] || 1.6, opacity: dimmed ? 0.35 : 0.9 }
}

// Leaflet measures its size once; re-measure whenever the container changes size
function AutoResize() {
  const map = useMap()
  useEffect(() => {
    const observer = new ResizeObserver(() => map.invalidateSize())
    observer.observe(map.getContainer())
    return () => observer.disconnect()
  }, [map])
  return null
}

function ClickHandler({ onClick }) {
  useMapEvents({ click: (e) => onClick?.(e.latlng) })
  return null
}

// Moves the map when `focus` changes: {bounds} or {center, zoom}
function FocusOn({ focus }) {
  const map = useMap()
  useEffect(() => {
    if (!focus) return
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (focus.bounds) map.fitBounds(focus.bounds, { padding: [48, 48], animate: !reduce })
    else if (reduce) map.setView(focus.center, focus.zoom || 14)
    else map.flyTo(focus.center, focus.zoom || 14, { duration: 0.6 })
  }, [focus, map])
  return null
}

function pinIcon(label, color) {
  return L.divIcon({
    className: '',
    html: `<div style="width:26px;height:26px;border-radius:50%;background:${color};color:#fff;
      display:grid;place-items:center;font:600 12px/1 'Inter Variable',system-ui;
      border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.35)">${label}</div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  })
}

export function Pin({ position, label, color }) {
  const icon = useMemo(() => pinIcon(label, color), [label, color])
  if (!position) return null
  return <Marker position={position} icon={icon} interactive={false} />
}

const toLatLngs = (coords) => coords.map(([lon, lat]) => [lat, lon])

export default function RiskMap({
  layers, route, from, to, onMapClick, onSegmentClick, focus, pickMode, children,
  className = 'h-full w-full',
}) {
  const dark = useIsDark()
  // road click handlers are bound once, so they read the latest values from refs
  const pickRef = useRef(pickMode)
  const segClickRef = useRef(onSegmentClick)
  useEffect(() => {
    pickRef.current = pickMode
    segClickRef.current = onSegmentClick
  }, [pickMode, onSegmentClick])

  const dimmed = Boolean(route)
  const routeColor = dark ? ROUTE_COLOR_DARK : ROUTE_COLOR
  const { segments, boundary, landslides, rivers, pois, reports } = layers || {}
  const riverLayers = useMemo(() => rivers && {
    river: { ...rivers, features: rivers.features.filter((f) => f.properties.kind === 'river') },
    stream: { ...rivers, features: rivers.features.filter((f) => f.properties.kind === 'stream') },
  }, [rivers])

  return (
    <MapContainer center={CHAMOLI_CENTER} zoom={9} className={className} preferCanvas zoomControl
      style={{ cursor: pickMode ? 'crosshair' : undefined }}>
      <AutoResize />
      <ClickHandler onClick={onMapClick} />
      <FocusOn focus={focus} />
      {/* re-created on theme change so the matching base map is selected */}
      <LayersControl position="topright" key={dark ? 'dark' : 'light'}>
        <LayersControl.BaseLayer checked name={dark ? 'Dark' : 'Light'}>
          <LayerGroup>
            <TileLayer maxZoom={19} maxNativeZoom={16} attribution={ESRI_ATTR}
              url={`${ESRI}/${dark ? 'World_Dark_Gray_Base' : 'World_Light_Gray_Base'}/MapServer/tile/{z}/{y}/{x}`} />
            <TileLayer maxZoom={19} maxNativeZoom={16} zIndex={2}
              url={`${ESRI}/${dark ? 'World_Dark_Gray_Reference' : 'World_Light_Gray_Reference'}/MapServer/tile/{z}/{y}/{x}`} />
          </LayerGroup>
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Streets">
          <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" maxZoom={19}
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Terrain">
          <TileLayer url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png" maxZoom={17}
            attribution='&copy; OpenStreetMap contributors, SRTM | &copy; <a href="https://opentopomap.org">OpenTopoMap</a>' />
        </LayersControl.BaseLayer>

        {boundary && (
          <LayersControl.Overlay checked name="District boundary">
            <GeoJSON data={boundary} interactive={false}
              style={{ color: dark ? '#a1a1aa' : '#52525b', weight: 1.5, dashArray: '6 5', fill: false }} />
          </LayersControl.Overlay>
        )}
        {riverLayers && (
          <LayersControl.Overlay checked name="Rivers">
            <GeoJSON data={riverLayers.river} interactive={false} renderer={canvas}
              style={{ color: '#5b8fc9', weight: 1.6, opacity: 0.7 }} />
          </LayersControl.Overlay>
        )}
        {riverLayers && (
          <LayersControl.Overlay name="Streams">
            <GeoJSON data={riverLayers.stream} interactive={false} renderer={canvas}
              style={{ color: '#7ba7d6', weight: 0.8, opacity: 0.6 }} />
          </LayersControl.Overlay>
        )}
        {segments && (
          <LayersControl.Overlay checked name="Road risk">
            <GeoJSON
              key={`${segments.version}-${dimmed}`}
              data={segments.data}
              renderer={canvas}
              style={(f) => roadStyle(f, dimmed)}
              onEachFeature={(feature, layer) => {
                layer.on('click', (e) => {
                  if (pickRef.current) return // let the map click pick a point
                  L.DomEvent.stopPropagation(e)
                  segClickRef.current?.(feature.properties.id)
                })
              }}
            />
          </LayersControl.Overlay>
        )}
        {landslides && (
          <LayersControl.Overlay checked name="Past landslides">
            <LayerGroup>
              {landslides.features.map((f) => {
                const p = f.properties
                const news = p.source === 'NEWS'
                return (
                  <CircleMarker key={p.id} center={[f.geometry.coordinates[1], f.geometry.coordinates[0]]}
                    radius={4.5} pathOptions={{ color: '#fff', weight: 1, fillColor: LANDSLIDE_COLORS[news ? 'NEWS' : 'NASA'], fillOpacity: 0.95 }}>
                    <Popup>
                      <div className="text-[11px] text-base-content/55">
                        {news ? 'News report' : 'NASA landslide catalogue'} · {p.event_date?.slice(0, 10) || 'Date unknown'}
                      </div>
                      <div className="mt-1">{p.description?.slice(0, 240)}</div>
                      {p.fatalities ? <div className="mt-1 text-base-content/70">Fatalities: {p.fatalities}</div> : null}
                      {p.source_url && <a className="mt-1 inline-block" href={p.source_url} target="_blank" rel="noreferrer">Read source</a>}
                    </Popup>
                  </CircleMarker>
                )
              })}
            </LayerGroup>
          </LayersControl.Overlay>
        )}
        {pois && (
          <LayersControl.Overlay name="Hospitals, police, fuel">
            <LayerGroup>
              {pois.features.filter((f) => POI_COLORS[f.properties.category]).map((f) => {
                const p = f.properties
                return (
                  <CircleMarker key={p.id} center={[f.geometry.coordinates[1], f.geometry.coordinates[0]]}
                    radius={4.5} pathOptions={{ color: '#fff', weight: 1.5, fillColor: POI_COLORS[p.category], fillOpacity: 1 }}>
                    <Popup>
                      <div className="font-medium">{p.name || POI_LABELS[p.category]}</div>
                      <div className="text-base-content/60">{POI_LABELS[p.category]}</div>
                      {p.phone && <a href={`tel:${p.phone}`}>{p.phone}</a>}
                    </Popup>
                  </CircleMarker>
                )
              })}
            </LayerGroup>
          </LayersControl.Overlay>
        )}
        {reports && (
          <LayersControl.Overlay checked name="User reports">
            <LayerGroup>
              {reports.map((r) => (
                <CircleMarker key={r.id} center={[r.lat, r.lon]} radius={7}
                  pathOptions={{ color: r.status === 'verified' ? '#27272a' : '#e07b28', weight: 2.5,
                    fillColor: '#fff', fillOpacity: 0.95, dashArray: r.status === 'pending' ? '3 3' : null }}>
                  <Popup>
                    <div className="text-[11px] text-base-content/55">
                      {r.status === 'verified' ? 'Verified · road closed' : 'Unverified report'} · {new Date(r.created_at).toLocaleString()}
                    </div>
                    <div className="mt-1 font-medium capitalize">{r.type.replace('_', ' ')}</div>
                    {r.description && <div>{r.description}</div>}
                    {r.photo && <img src={`/api/uploads/${r.photo}`} alt="Reported blockage" className="mt-2 max-w-[220px] rounded" />}
                  </Popup>
                </CircleMarker>
              ))}
            </LayerGroup>
          </LayersControl.Overlay>
        )}
      </LayersControl>

      {route?.shortest && !route.same && (
        <Polyline positions={toLatLngs(route.shortest.geometry.coordinates)}
          pathOptions={{ color: dark ? '#a1a1aa' : '#71717a', weight: 4, dashArray: '6 7', opacity: 0.9 }}>
          <Tooltip sticky>Shortest route · {route.shortest.distance_km} km</Tooltip>
        </Polyline>
      )}
      {route?.safe && (
        <>
          <Polyline positions={toLatLngs(route.safe.geometry.coordinates)} interactive={false}
            pathOptions={{ color: dark ? '#17171a' : '#ffffff', weight: 8, opacity: 0.95 }} />
          <Polyline positions={toLatLngs(route.safe.geometry.coordinates)}
            pathOptions={{ color: routeColor, weight: 4.5 }}>
            <Tooltip sticky>Recommended route · {route.safe.distance_km} km</Tooltip>
          </Polyline>
          {route.safe.hazard_stretches.map((h, i) => (
            <CircleMarker key={i} center={[h.location[1], h.location[0]]} radius={6}
              pathOptions={{ color: '#fff', weight: 2, fillColor: RISK_COLORS[h.risk_class], fillOpacity: 1 }}>
              <Tooltip>
                <span className="font-medium">km {h.start_km}–{h.end_km}</span> · {RISK_LABELS[h.risk_class]}
                <br />{h.reasons.join(', ')}
              </Tooltip>
            </CircleMarker>
          ))}
        </>
      )}
      <Pin position={from} label="A" color="#2f7d55" />
      <Pin position={to} label="B" color="#b4413a" />
      {children}
    </MapContainer>
  )
}
