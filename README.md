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

## Tablas en D1

| Tabla | Contenido |
|---|---|
| `notas` | Histórico de la hoja *Data* (254 notas, ene–jun 2026) + respuestas del Forms |
| `analisis` | Hoja *KPIS*: análisis de 5 porqués y acciones correctivas |
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
