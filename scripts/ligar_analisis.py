"""Liga cada análisis de 5 porqués (hoja KPIS) con su nota pública.

Criterio: mismo código de cliente y mismo texto de situación; si no hay texto
igual, la nota del mismo cliente con la fecha más cercana (máx. 7 días).
Cada nota recibe como mucho un análisis.

Uso:
    python scripts/ligar_analisis.py data/_n.json data/_a.json > data/_link.sql
    (respuestas de GET /api/notas y GET /api/analisis)
"""
import datetime as dt
import json
import sys
import unicodedata


def k(s):
    return " ".join(unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().upper().split())


def d(s):
    return dt.date.fromisoformat(s[:10]) if s else None


def main(pn, pa):
    notas = json.load(open(pn, encoding="utf-8"))["notas"]
    analisis = json.load(open(pa, encoding="utf-8"))["analisis"]
    usados, out, stats = set(), [], {"texto": 0, "fecha": 0, "sin_nota": 0}
    for a in sorted(analisis, key=lambda a: (a["fecha"] or "", a["id"])):
        cand = [n for n in notas if n["codigo_cliente"] == a["codigo_cliente"] and n["id"] not in usados]
        igual = [n for n in cand if k(n["situacion"]) == k(a["situacion"])]
        pool, como = (igual, "texto") if igual else (cand, "fecha")
        dist = lambda n: abs((d(n["fecha"]) - d(a["fecha"])).days) if n["fecha"] and a["fecha"] else 9999
        pool.sort(key=lambda n: (dist(n), n["id"]))
        best = pool[0] if pool and (como == "texto" or dist(pool[0]) <= 7) else None
        if best:
            usados.add(best["id"])
            stats[como] += 1
            out.append(f"UPDATE analisis SET nota_id={best['id']} WHERE id={a['id']};")
        else:
            stats["sin_nota"] += 1
            out.append(f"UPDATE analisis SET nota_id=NULL WHERE id={a['id']};")
    print("\n".join(out))
    print(stats, file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
