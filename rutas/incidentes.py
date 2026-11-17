from datetime import date

from flask import Blueprint, jsonify, request

from db import get_db

bp = Blueprint("incidentes", __name__)
SEVERIDADES = {"baja", "media", "alta", "critica"}


def incidente_json(fila):
    """Convierte el resultado de la consulta en un recurso JSON."""
    return {
        "id": fila["id"],
        "activo_id": fila["activo_id"],
        "nombre_activo": fila["nombre_activo"],
        "descripcion": fila["descripcion"],
        "severidad": fila["severidad"],
        "estado": fila["estado"],
        "fecha_reporte": fila["fecha_reporte"],
        "accion_tomada": fila["accion_tomada"],
        "fecha_resolucion": fila["fecha_resolucion"],
    }


def buscar_incidente(db, incidente_id):
    return db.execute(
        """
        SELECT incidentes.*, activos.nombre AS nombre_activo
        FROM incidentes
        JOIN activos ON activos.id = incidentes.activo_id
        WHERE incidentes.id = ?
        """,
        (incidente_id,),
    ).fetchone()


@bp.get("/api/incidentes")
def listar_incidentes():
    filas = get_db().execute(
        """
        SELECT incidentes.*, activos.nombre AS nombre_activo
        FROM incidentes
        JOIN activos ON activos.id = incidentes.activo_id
        ORDER BY incidentes.id
        """
    ).fetchall()
    return jsonify([incidente_json(fila) for fila in filas])


@bp.post("/api/incidentes")
def crear_incidente():
    datos = request.get_json(silent=True) or {}
    activo_id = datos.get("activo_id")
    descripcion = str(datos.get("descripcion", "")).strip()
    severidad = str(datos.get("severidad", "")).strip().lower()

    if not isinstance(activo_id, int) or not descripcion:
        return jsonify(error="Se requieren activo_id y descripcion"), 400
    if severidad not in SEVERIDADES:
        return jsonify(error="Severidad válida: baja, media, alta o critica"), 400

    db = get_db()
    activo = db.execute(
        "SELECT id FROM activos WHERE id = ?", (activo_id,)
    ).fetchone()
    if activo is None:
        return jsonify(error="Activo no encontrado"), 404

    cursor = db.execute(
        """
        INSERT INTO incidentes (activo_id, descripcion, severidad, fecha_reporte)
        VALUES (?, ?, ?, ?)
        """,
        (activo_id, descripcion, severidad, date.today().isoformat()),
    )
    db.commit()
    return jsonify(incidente_json(buscar_incidente(db, cursor.lastrowid))), 201