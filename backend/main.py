from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncio
import json
from starlette.websockets import WebSocket
from fastapi import Request
from pydantic import BaseModel
from datetime import datetime
from fastapi import HTTPException
from typing import Optional
from fastapi.responses import JSONResponse
from pyproj import Transformer
from psycopg2.extras import RealDictCursor


app = FastAPI()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Variable globale (à éviter en production, mais acceptable en développement)
DB_CONFIG = {}

class DBConfig(BaseModel):
    dbname: str
    user: str
    password: str
    host: str
    port: str

@app.post("/api/connect-db")
def connect_db(config: DBConfig):
    global DB_CONFIG
    try:
        # Test de la connexion
        conn = psycopg2.connect(
            dbname=config.dbname,
            user=config.user,
            password=config.password,
            host=config.host,
            port=config.port
        )
        conn.close()

        # Sauvegarde de la config dans une variable globale
        DB_CONFIG = config.dict()

        return {"status": "connected"}
    except Exception as e:
        print(f"Connection failed: {e}")
        return {"status": "error", "detail": str(e)}

def get_db_connection():
    if not DB_CONFIG:
        raise Exception("Database not configured. Please call /api/connect-db first.")
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


@app.get("/alertes")
def get_alertes():
    """Récupérer la liste des alertes triées par ID"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, type_alerte, message, date, entity_id AS id_depart
        FROM alertes
        ORDER BY id DESC;
        """
    )
    alertes = cur.fetchall()
    conn.close()
    return alertes


@app.websocket("/ws/alertes")
async def websocket_alertes(websocket: WebSocket):
    """WebSocket pour les mises à jour des alertes"""
    await websocket.accept()
    while True:
        await asyncio.sleep(5)  # Rafraîchir toutes les 5s
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, type_alerte, message, date, entity_id AS id_depart
            FROM alertes
            ORDER BY id DESC;
            """
        )
        alertes = cur.fetchall()
        conn.close()
        # Convertir les objets datetime en chaînes de caractères
        alertes = [
            {
                **alerte,
                'date': alerte['date'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(alerte['date'], datetime) else alerte['date']
            }
            for alerte in alertes
        ]
        await websocket.send_text(json.dumps(alertes))


@app.get("/statistiques")
def get_statistiques():
    """Récupérer les statistiques des départs."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, nom, energie_consomme_mva
        FROM departs
        ORDER BY id ASC;
        """
    )
    statistiques = cur.fetchall()
    conn.close()
    return statistiques


@app.websocket("/ws/statistiques")
async def websocket_statistiques(websocket: WebSocket):
    """WebSocket pour mises à jour en temps réel des statistiques."""
    await websocket.accept()
    while True:
        await asyncio.sleep(5)  # Rafraîchir toutes les 5s
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, nom, energie_consomme_mva
            FROM departs
            ORDER BY id ASC;
            """
        )
        statistiques = cur.fetchall()
        conn.close()
        await websocket.send_text(json.dumps(statistiques, default=str))


@app.get("/disjoncteurs")
def get_disjoncteurs():
    """Récupérer la liste des disjoncteurs"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, nom, etat
        FROM disjoncteurs
        ORDER BY id ASC;
        """
    )
    disjoncteurs = cur.fetchall()
    conn.close()
    return disjoncteurs


@app.put("/disjoncteurs/{id}")
def update_disjoncteur(id: int, data: dict):
    """Mettre à jour l'état d'un disjoncteur"""
    new_etat = data.get("etat")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE disjoncteurs
        SET etat = %s
        WHERE id = %s
        RETURNING id, nom, etat;
        """,
        (new_etat, id),
    )
    updated_disjoncteur = cur.fetchone()
    conn.commit()
    conn.close()
    return updated_disjoncteur


@app.websocket("/ws/disjoncteurs")
async def websocket_disjoncteurs(websocket: WebSocket):
    """WebSocket pour mises à jour en temps réel"""
    await websocket.accept()
    while True:
        await asyncio.sleep(5)  # Rafraîchir toutes les 5s
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, nom, etat
            FROM disjoncteurs
            ORDER BY id ASC;
            """
        )
        disjoncteurs = cur.fetchall()
        conn.close()
        await websocket.send_text(json.dumps(disjoncteurs,{"ping": "pong"}))


@app.get("/Départs")
def get_Départs():
    """Récupérer la liste des départs avec état des disjoncteurs"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT d.depart_id, d.depart_nom, d.energie_consomme_mva, d.etat,
                d.disjoncteur_prioritaire, d.disjoncteur_prioritaire_etat, 
                d.disjoncteur_secours, disjoncteur_secours_etat,
               d.poste_source,d.tension_kv,d.longueur_km, ST_AsGeoJSON(d.geom) AS geom
        FROM departs_vue d
        ORDER BY d.depart_nom ASC;
        """
    )
    Départs = cur.fetchall()
    conn.close()
    return Départs


@app.get("/Départs/{depart_id}")
def get_depart_details(depart_id: int):
    """Récupérer les détails d'un départ avec état des disjoncteurs"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT d.depart_nom, d.energie_consomme_mva, d.etat,
               d.disjoncteur_prioritaire, d.disjoncteur_prioritaire_etat, 
               d.disjoncteur_secours, d.disjoncteur_secours_etat,
               d.poste_source, d.tension_kv, d.longueur_km
        FROM departs_vue d
        WHERE d.depart_id = %s;
        """, (depart_id,)
    )
    depart = cur.fetchone()
    conn.close()
    return depart


@app.websocket("/ws/Départs")
async def websocket_Départs(websocket: WebSocket):
    """WebSocket pour les mises à jour des départs"""
    await websocket.accept()
    while True:
        await asyncio.sleep(5)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
             SELECT d.depart_id, d.depart_nom, d.energie_consomme_mva, d.etat,
                d.disjoncteur_prioritaire, d.disjoncteur_prioritaire_etat, 
                d.disjoncteur_secours, disjoncteur_secours_etat,
               d.poste_source,d.tension_kv,d.longueur_km, ST_AsGeoJSON(d.geom) AS geom
        FROM departs_vue d
        ORDER BY d.depart_nom ASC;
            """
        )
        Départs = cur.fetchall()
        conn.close()
        await websocket.send_text(json.dumps(Départs))


class PosteTransformation(BaseModel):
    nom: str
    puissance_total: Optional[float] = 0  # Valeur par défaut
    geom: str                             # Champ obligatoire

@app.post("/ajouter_poste_transformation")
def ajouter_poste_transformation(poste: PosteTransformation):
    """Ajouter uniquement un poste de transformation"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("BEGIN;")

        # Synchronisation de la séquence
        cur.execute("SELECT MAX(id) FROM postes_transformation;")
        max_poste_id = cur.fetchone()[0] or 0
        cur.execute("SELECT setval('postes_transformation_id_seq', %s, true);", (max_poste_id,))

        # Extraire les coordonnées de geom (format POINT(lon lat))
        geom_data = poste.geom.strip("POINT()").split()
        lon, lat = float(geom_data[0]), float(geom_data[1])

        # Conversion WGS84 -> UTM32N (EPSG:32632)
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:32632", always_xy=True)
        utm_x, utm_y = transformer.transform(lon, lat)

        # Insertion dans la table postes_transformation
        cur.execute(
            """
            INSERT INTO postes_transformation 
            (nom, geom, propr, local, observ, rapport_tc, telec, "code gto", dms, milieu, usage, ref_abon, mod_racc)
            VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 32632), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
                poste.nom,
                utm_x, utm_y,  # <-- coordonnées converties
                None, None, None, None, None, None, None, None, None, None, None
            )
        )
        poste_id = cur.fetchone()[0]

        if not poste_id:
            conn.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": "Erreur lors de l'insertion dans la base."
            })

        conn.commit()
        return JSONResponse(content={
            "success": True,
            "message": "Poste de transformation ajouté avec succès.",
            "poste_id": poste_id
        })

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'insertion : {str(e)}")

    finally:
        cur.close()
        conn.close()


@app.get("/postes_transformation")
def get_postes_transformation():
    """Récupérer la liste des postes de transformation avec leurs transformateurs"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pt.poste_id, pt.nom, pt.puissance_total, pt.etat, ST_AsGeoJSON(pt.geom) AS geom, pt.depart, 
        pt.poste_source, pt.secteur_id, pt.secteur_nom, pt.delegation_nom, pt.gouvernorat_nom,
        pt.district_nom, pt.direction_nom
        FROM poste_vue pt
        ORDER BY pt.nom ASC;
        """
    )
    postes = cur.fetchall()
    conn.close()
    return postes

@app.get("/postes_transformation/{poste_id}")
def get_poste_transformation(poste_id: int):
    """Récupérer les détails d'un poste de transformation"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pt.nom, pt.puissance_total, pt.etat, pt.depart, 
               pt.poste_source, pt.secteur_nom, pt.delegation_nom, 
               pt.gouvernorat_nom, pt.district_nom, pt.direction_nom
        FROM poste_vue pt
        WHERE pt.poste_id = %s;
        """, (poste_id,)
    )
    poste = cur.fetchone()
    conn.close()
    return poste


@app.websocket("/ws/postes_transformation")
async def websocket_postes_transformation(websocket: WebSocket):
    """WebSocket pour les mises à jour des postes de transformation"""
    await websocket.accept()
    while True:
        await asyncio.sleep(5)  # Rafraîchir toutes les 5s
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT pt.poste_id, pt.nom, pt.puissance_total, pt.etat, ST_AsGeoJSON(pt.geom) AS geom, pt.depart, 
            pt.poste_source, pt.secteur_id, pt.secteur_nom, pt.delegation_nom, pt.gouvernorat_nom,
            pt.district_nom, pt.direction_nom
            FROM poste_vue pt
            ORDER BY pt.nom ASC;
            """
        )
        postes = cur.fetchall()
        conn.close()
        await websocket.send_text(json.dumps(postes))


@app.get("/postes_sources")
def get_postes_sources():
    """Récupérer la liste des postes sources"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ST_AsGeoJSON(geom) AS geom, nom, energie_consomme_mva, etat
        FROM postes_sources;
        """
    )
    postes = cur.fetchall()
    conn.close()
    return postes


@app.websocket("/ws/postes_sources")
async def websocket_postes_sources(websocket: WebSocket):
    """WebSocket pour les mises à jour des postes sources"""
    await websocket.accept()
    while True:
        await asyncio.sleep(5)  # Rafraîchir toutes les 5s
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ST_AsGeoJSON(geom) AS geom, nom, energie_consomme_mva, etat
            FROM postes_sources;
            """
        )
        postes = cur.fetchall()
        conn.close()
        await websocket.send_text(json.dumps(postes))
