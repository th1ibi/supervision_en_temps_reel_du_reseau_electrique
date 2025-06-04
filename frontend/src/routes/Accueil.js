import React, { useEffect, useState } from "react";
import "../App.css";
import "leaflet/dist/leaflet.css";
import { MapContainer, TileLayer, Marker, Popup, Polygon, Polyline, CircleMarker } from "react-leaflet";
import L from "leaflet";
import proj4 from "proj4";

// Définir la projection UTM 32N (EPSG:32632) si elle n'existe pas déjà
proj4.defs("EPSG:32632", "+proj=utm +zone=32 +datum=WGS84 +units=m +no_defs");

export default function Accueil() {
  const [postesSources, setPostesSources] = useState([]);
  const [postesTransformation, setPostesTransformation] = useState([]);
  const [departs, setDeparts] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/postes_sources")
      .then((res) => res.json())
      .then((data) => setPostesSources(data));

    fetch("http://localhost:8000/postes_transformation")
      .then((res) => res.json())
      .then((data) => setPostesTransformation(data));

    fetch("http://localhost:8000/Départs")
      .then((res) => res.json())
      .then((data) => setDeparts(data));
  }, []);

  const convertCoordinates = ([x, y]) => {
    const [lng, lat] = proj4("EPSG:32632", "EPSG:4326", [x, y]);
    return [lat, lng]; // leaflet uses [lat, lng]
  };

  return (
    <div className="map-container">
      <MapContainer center={[34.739, 10.76]} zoom={10} className="map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Postes Sources */}
        {postesSources.map((poste, idx) => {
          let geom = null;
          try {
            geom = poste.geom && JSON.parse(poste.geom);
          } catch (e) {
            console.error("Erreur parsing GeoJSON:", e);
            return null;
          }
          if (!geom || geom.type !== "MultiPolygon") return null;

          return geom.coordinates.map((polygon, index) => (
            <Polygon
              key={`source-${idx}-poly-${index}`}
              positions={polygon[0].map(convertCoordinates)}
              pathOptions={{ color: "blue" }}
            >
              <Popup>
                <strong>Poste Source:</strong> {poste.nom} <br />
                Energie Consommée: {poste.energie_consomme_mva} MVA <br />
                Etat: {poste.etat ? "Actif" : "Inactif"}
              </Popup>
            </Polygon>
          ));
        })}

        {/* Postes de Transformation */}
        {postesTransformation.map((poste, idx) => {
          let geom = null;
          try {
            geom = poste.geom && JSON.parse(poste.geom);
          } catch (e) {
            console.error("Erreur parsing GeoJSON:", e);
            return null;
          }
          if (!geom || geom.type !== "Point") return null;

          const position = convertCoordinates(geom.coordinates);

          return (
            <CircleMarker
              key={`transfo-${idx}`}
              center={position}
              radius={8}
              pathOptions={{
                color: poste.etat === "true" || poste.etat === true ? "green" : "red",
                fillColor: poste.etat === "true" || poste.etat === true ? "green" : "red",
                fillOpacity: 0.8,
              }}
            >
              <Popup>
                <strong>Poste Transformation:</strong> {poste.nom} <br />
                Poste Source: {poste.poste_source} <br />
                Puissance: {poste.puissance_total} kVA <br />
                Etat: {poste.etat === "true" || poste.etat === true ? "Actif" : "Inactif"} <br />
                Département: {poste.depart} <br />
                Secteur: {poste.secteur_nom} <br />
                Gouvernorat: {poste.gouvernorat_nom}
              </Popup>
            </CircleMarker>
          );
        })}

        {/* Départs */}
        {departs.map((depart, idx) => {
          let geom = null;
          try {
            geom = depart.geom && JSON.parse(depart.geom);
          } catch (e) {
            console.error("Erreur parsing GeoJSON:", e);
            return null;
          }
          if (!geom || geom.type !== "MultiLineString") return null;

          return geom.coordinates.map((line, index) => (
            <Polyline
              key={`depart-${idx}-${index}`}
              positions={line.map(convertCoordinates)}
              pathOptions={{
                color: depart.etat ? "green" : "red",
                weight: 4,
              }}
            >
              <Popup>
                <strong>Départ:</strong> {depart.depart_nom} <br />
                Etat: {depart.etat ? "Actif" : "Inactif"} <br />
                Consommation: {depart.energie_consomme_mva} MVA
              </Popup>
            </Polyline>
          ));
        })}
      </MapContainer>
    </div>
  );
}
