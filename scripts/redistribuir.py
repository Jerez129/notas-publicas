"""Reparte las notas de choferes que ya no están en el Headcount entre los activos.

Cada nota huérfana va al chofer activo con menos notas en ese momento (empate:
orden alfabético), así la carga queda pareja. El nombre anterior se guarda en
`reasignada_de`, y `chofer_original` no se toca, así que se puede deshacer.

Uso:
    python scripts/redistribuir.py data/_n.json > data/redistribuir.sql
    (data/_n.json = respuesta de GET /api/notas)
"""
import json
import sys
from collections import Counter

from migrar_historico import CHOFERES


def sql(v):
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


def main(path):
    notas = json.load(open(path, encoding="utf-8"))["notas"]
    activos = set(CHOFERES)
    carga = Counter({c: 0 for c in CHOFERES})
    carga.update(n["chofer"] for n in notas if n["chofer"] in activos)
    huerfanas = sorted((n for n in notas if n["chofer"] and n["chofer"] not in activos),
                       key=lambda n: (n["fecha"] or "", n["id"]))
    for n in huerfanas:
        nuevo = min(CHOFERES, key=lambda c: (carga[c], c))
        carga[nuevo] += 1
        print(f"UPDATE notas SET reasignada_de={sql(n['chofer'])}, chofer={sql(nuevo)} WHERE id={n['id']};")
        print(f"-- nota {n['id']} ({n['fecha']}, {n['ruta']}): {n['chofer']} -> {nuevo}", file=sys.stderr)
    if not huerfanas:
        print("-- No hay notas de choferes fuera del Headcount", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1])
