-- Notas Públicas CND CD Bávaro
-- Una fila por nota pública (histórico de Excel + respuestas nuevas del Forms)
CREATE TABLE IF NOT EXISTS notas (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  ext_id             TEXT NOT NULL UNIQUE,   -- clave anti-duplicados: 'hist-…' o 'forms-<Id>'
  origen             TEXT NOT NULL,          -- 'historico' | 'forms'
  codigo_np          TEXT,
  fecha              TEXT,                   -- YYYY-MM-DD
  centro             TEXT,
  ruta               TEXT,
  chofer             TEXT,                   -- nombre normalizado (Headcount)
  chofer_original    TEXT,                   -- tal como venía en la fuente
  supervisor         TEXT,
  vehiculo           TEXT,
  codigo_cliente     TEXT,
  nombre_cliente     TEXT,
  categoria          TEXT,                   -- En ruta | Pre ruta
  tipo_reclamo       TEXT,
  situacion          TEXT,
  vendedor           TEXT,
  ruta_preventa      TEXT,
  coordinador_ventas TEXT,
  tipo_impacto       TEXT,
  status             TEXT,
  fecha_inicio       TEXT,
  plazo              TEXT,
  fecha_cierre       TEXT,
  comentario         TEXT,
  reasignada_de      TEXT,                   -- chofer anterior si la nota se redistribuyó
  creado_en          TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_notas_fecha  ON notas(fecha);
CREATE INDEX IF NOT EXISTS idx_notas_chofer ON notas(chofer);
CREATE INDEX IF NOT EXISTS idx_notas_ruta   ON notas(ruta);

-- Análisis 5 porqués (hoja KPIS)
CREATE TABLE IF NOT EXISTS analisis (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  ext_id           TEXT NOT NULL UNIQUE,
  fecha            TEXT,
  ruta             TEXT,
  codigo_cliente   TEXT,
  nombre_cliente   TEXT,
  situacion        TEXT,
  tipo_reclamo     TEXT,
  kpi              TEXT,
  porque1 TEXT, porque2 TEXT, porque3 TEXT, porque4 TEXT, porque5 TEXT,
  accion_correctiva TEXT,
  nota_id          INTEGER,                -- nota pública a la que pertenece
  responsable      TEXT,
  actualizado_en   TEXT,
  creado_en        TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_analisis_nota ON analisis(nota_id) WHERE nota_id IS NOT NULL;

-- Respaldo crudo de la hoja "PEGAR DATA ROADMAP" (para no perder nada)
CREATE TABLE IF NOT EXISTS roadmap_raw (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  ext_id    TEXT NOT NULL UNIQUE,
  fila_json TEXT NOT NULL
);

-- Choferes del Headcount (activo=0 si ya no está en la empresa)
CREATE TABLE IF NOT EXISTS choferes (
  nombre         TEXT PRIMARY KEY,
  activo         INTEGER NOT NULL DEFAULT 1,
  ruta           TEXT,
  actualizado_en TEXT NOT NULL DEFAULT (datetime('now'))
);
