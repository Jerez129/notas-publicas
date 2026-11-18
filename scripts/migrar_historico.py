"""Convierte el Excel histórico de Notas Públicas en un archivo SQL para D1.

Uso:
    python scripts/migrar_historico.py "C:/ruta/nota1.xlsx"

Genera data/seed.sql (no se sube a GitHub). Es idempotente: cada fila lleva un
ext_id estable y se inserta con INSERT OR IGNORE, así que correrlo dos veces no
duplica nada.
"""
import datetime as dt
import hashlib
import json
import sys
import unicodedata
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "seed.sql"

# Nombres oficiales (Headcount Dist. 11.02.2026) = opciones del Forms
CHOFERES = [
    "Adrian Antonio De La Rosa De La Cruz", "Alexander Estrella Brito",
    "Anlleo Joner Pacheco Valera", "Denny's Zapata Peguero",
    "Edifo Antonio Pache Pache", "Emmanuel Cedano Santana",
    "Gilbert Martínez Cuevas", "Hensy Emmanuel Guilamo",
    "Joaquín Alberto Mateo Encarnación", "Jonathan Sánchez",
    "Juan Edward Ibert Encarnación", "Miguel Ángel De Jesús",
    "Ramón Antonio Escarlante Carrasco", "Reye Ferrera",
    "Rikelvin Cedeño Shepard", "Rubén Esteban Schleider Mercedes",
    "Salvador Santo De La Rosa", "Samuel De La Cruz Nuñez",
    "Tomás Alberto De Jesús Cayetano", "Tony Sierra",
    "William Encarnación Soriano",
]


def key(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


CANON = {key(n): n for n in CHOFERES}
ALIAS = {
    "REYE FERRERA DELGADO": "Reye Ferrera",
    "RUBEN ESTEBAN MERCEDES": "Rubén Esteban Schleider Mercedes",
    "JOAQUIN MATEO ENCARNAION": "Joaquín Alberto Mateo Encarnación",
    "THOMAS ALBERTO DE JESUS CAYETANO": "Tomás Alberto De Jesús Cayetano",
    "WILLIAN ENCARNACION SORIANO": "William Encarnación Soriano",
    "SAMUEL DE LA CRUZ": "Samuel De La Cruz Nuñez",
    "EMMANUEL CEDANO": "Emmanuel Cedano Santana",
}


def chofer_norm(raw):
    k = key(raw)
    if not k:
        return None
    return CANON.get(k) or ALIAS.get(k) or " ".join(w.capitalize() for w in str(raw).split())


def clean(v):
    if v is None:
        return None
    if isinstance(v, (dt.datetime, dt.date)):
        return v.strftime("%Y-%m-%d")
    s = str(v).strip()
    if s in ("", "#REF!", "N/A", "0", "."):
        return None
    return s


def dtime(v):
    if isinstance(v, dt.datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    return clean(v)


def categoria(v):
    v = clean(v)
    if not v:
        return None
    return "Pre ruta" if key(v) == "PRE RUTA" else "En ruta" if key(v) == "EN RUTA" else v


def sql(v):
    if v is None:
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"


def ext_id(prefix, *parts, seen):
    h = hashlib.sha1("|".join(str(p or "") for p in parts).encode()).hexdigest()[:16]
    n = seen.get(h, 0)
    seen[h] = n + 1
    return f"{prefix}-{h}" + (f"-{n}" if n else "")


def rows(ws):
    it = ws.iter_rows(values_only=True)
    header = None
    for r in it:
        if header is None:
            if r and any(c is not None for c in r):
                header = [str(c).strip() if c is not None else "" for c in r]
            continue
        if any(c is not None for c in r):
            yield dict(zip(header, r))


def main(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = []
    seen = {}

    # --- Data: histórico principal -------------------------------------
    n_notas = 0
    for r in rows(wb["Data"]):
        fecha = r.get("Fecha")
        if not fecha and not r.get("Nombre Cliente"):
            continue
        # En el Excel el encabezado viene dañado ("Queja del Cliente ó Chofer"),
        # así que se busca por la palabra "QUEJA".
        queja = next((v for k, v in r.items() if "QUEJA" in key(k)), None)
        vals = {
            # El 4º componente queda en None a propósito: así se generó la carga
            # original y cambiarlo duplicaría las notas ya cargadas en D1.
            "ext_id": ext_id("hist", r.get("Codigo NP"), fecha, r.get("Código Cliente"),
                             None, seen=seen),
            "origen": "historico",
            "codigo_np": clean(r.get("Codigo NP")),
            "fecha": clean(fecha),
            "centro": clean(r.get("Centro")),
            "ruta": clean(r.get("Ruta Entrega")) or clean(r.get("Ruta2")),
            "chofer": chofer_norm(clean(r.get("Chofer"))),
            "chofer_original": clean(r.get("Chofer")),
            "supervisor": clean(r.get("Supervisor Distribución")),
            "codigo_cliente": clean(r.get("Código Cliente")),
            "nombre_cliente": clean(r.get("Nombre Cliente")),
            "categoria": categoria(r.get("Categoria")),
            "tipo_reclamo": clean(r.get("Tipo de Reclamo")),
            "situacion": clean(queja),
            "vendedor": clean(r.get("Asesores")),
            "ruta_preventa": clean(r.get("Ruta Preventa")),
            "coordinador_ventas": clean(r.get("Coordinador de Ventas")),
            "tipo_impacto": clean(r.get("Tipo de Impacto")),
            "status": clean(r.get("STATUS")),
            "fecha_inicio": dtime(r.get("Fecha de Inicio Nota Pública")),
            "plazo": dtime(r.get("Plazo")),
            "fecha_cierre": dtime(r.get("Fecha de Cierre Nota Pública")),
            "comentario": clean(r.get("Comentario")),
        }
        cols = ",".join(vals)
        out.append(f"INSERT OR IGNORE INTO notas ({cols}) VALUES ({','.join(sql(v) for v in vals.values())});")
        if vals["situacion"]:
            out.append(f"UPDATE notas SET situacion={sql(vals['situacion'])} WHERE ext_id={sql(vals['ext_id'])} AND situacion IS NULL;")
        n_notas += 1

    # --- KPIS: análisis 5 porqués --------------------------------------
    n_an = 0
    for r in rows(wb["KPIS"]):
        if not r.get("Fecha") and not r.get("Cliente"):
            continue
        vals = {
            "ext_id": ext_id("kpi", r.get("Fecha"), r.get("Cod Cliente"), r.get("Situacion"), seen=seen),
            "fecha": clean(r.get("Fecha")),
            "ruta": clean(r.get("Ruta")),
            "codigo_cliente": clean(r.get("Cod Cliente")),
            "nombre_cliente": clean(r.get("Cliente")),
            "situacion": clean(r.get("Situacion")),
            "tipo_reclamo": clean(r.get("Tipo Reclamo")),
            "kpi": clean(r.get("KPI Asignado")),
            "porque1": clean(r.get("1 Por que")), "porque2": clean(r.get("2 Por que")),
            "porque3": clean(r.get("3 Por que")), "porque4": clean(r.get("4 Por que")),
            "porque5": clean(r.get("5 Por que")),
            "accion_correctiva": clean(r.get("Accion Correctiva")),
        }
        cols = ",".join(vals)
        out.append(f"INSERT OR IGNORE INTO analisis ({cols}) VALUES ({','.join(sql(v) for v in vals.values())});")
        n_an += 1

    # --- PEGAR DATA ROADMAP: respaldo crudo ----------------------------
    n_rm = 0
    for r in rows(wb["PEGAR DATA ROADMAP"]):
        data = {k: clean(v) for k, v in r.items() if k and clean(v) is not None}
        if not data:
            continue
        eid = ext_id("rm", r.get("grupo"), r.get("fecha_registro"), r.get("observacion"), seen=seen)
        out.append(f"INSERT OR IGNORE INTO roadmap_raw (ext_id, fila_json) VALUES ({sql(eid)},{sql(json.dumps(data, ensure_ascii=False))});")
        n_rm += 1

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"notas={n_notas} analisis={n_an} roadmap_raw={n_rm} -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\japf2\Downloads\nota1.xlsx")
