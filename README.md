# Notas Públicas · CND CD Bávaro

Dashboard de notas públicas reportadas por los choferes de distribución.

- **Dashboard**: `index.html`, publicado con GitHub Pages.
- **API**: Cloudflare Worker `notas-publicas-api` (`worker/`), protegido con contraseña.
- **Base de datos**: Cloudflare D1 `notas-publicas-db`.
- **Captura**: Microsoft Forms «Reporte de novedades en ruta - CND CD Bávaro».

Los datos de clientes **no** están en este repositorio; solo se leen desde D1 tras iniciar sesión.

## Cargar respuestas nuevas del Forms

1. En Forms → *Ver respuestas* → *Abrir en Excel* y descarga el archivo.
2. En el dashboard → **Subir Excel del Forms**.
3. Solo se agregan las respuestas nuevas (se reconoce cada una por su `Id`), así que puedes subir el mismo archivo completo cada vez.

## 5 porqués

En **Detalle de notas** cada nota tiene un botón **Hacer** (o **✓ Ver** si ya tiene análisis). Se guarda KPI, los 5 porqués, la acción correctiva y el responsable en la tabla `analisis`, ligado a la nota por `nota_id`. El filtro «5 porqués» muestra las pendientes.

## Choferes que salen del Headcount

`scripts/redistribuir.py` reparte sus notas entre los choferes activos (al que tenga menos notas). El nombre anterior queda en `reasignada_de` y en el dashboard la nota aparece marcada como «reasignada». Para actualizar la lista de choferes activos, edita `CHOFERES` en `scripts/migrar_historico.py`.

## Tablas en D1

| Tabla | Contenido |
|---|---|
| `notas` | Histórico de la hoja *Data* de «Notas Públicas BVR V2» (349 notas, ene–oct 2026) + respuestas del Forms |
| `analisis` | Hoja *KPIS*: 170 análisis de 5 porqués ligados a su nota, más los que se hagan desde el dashboard |
| `roadmap_raw` | Respaldo crudo de la hoja *PEGAR DATA ROADMAP* |

## Mantenimiento

```bash
cd worker
npx wrangler deploy                          # publicar cambios de la API
npx wrangler secret put DASH_PASSWORD        # cambiar la contraseña
npx wrangler d1 execute notas-publicas-db --remote --command "SELECT count(*) FROM notas"
```

Volver a cargar el histórico (no duplica, usa `INSERT OR IGNORE`):

```bash
python scripts/migrar_historico.py "ruta/a/nota1.xlsx"
cd worker && npx wrangler d1 execute notas-publicas-db --remote --file=../data/seed.sql
```

Después de cargar, ligar los 5 porqués con su nota y reasignar notas de choferes que ya no están
(ver las instrucciones dentro de `scripts/ligar_analisis.py` y `scripts/redistribuir.py`).
