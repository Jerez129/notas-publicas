-- Lista de choferes (Headcount). Activos aparecen en el dashboard aunque no tengan notas.
CREATE TABLE IF NOT EXISTS choferes (
  nombre         TEXT PRIMARY KEY,
  activo         INTEGER NOT NULL DEFAULT 1,
  ruta           TEXT,
  actualizado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR REPLACE INTO choferes (nombre, activo, ruta) VALUES
  ('Adrian Antonio De La Rosa De La Cruz', 1, 'DO0176'),
  ('Alexander Estrella Brito', 1, 'DO0820'),
  ('Anlleo Joner Pacheco Valera', 1, NULL),
  ('Denny''s Zapata Peguero', 1, 'DO0183'),
  ('Edifo Antonio Pache Pache', 1, NULL),
  ('Emmanuel Cedano Santana', 1, 'DO0819'),
  ('Gilbert Martínez Cuevas', 1, NULL),
  ('Hensy Emmanuel Guilamo', 1, 'DO0316'),
  ('Joaquín Alberto Mateo Encarnación', 1, 'DO0651'),
  ('Jonathan Sánchez', 1, 'DO0175'),
  ('Miguel Ángel De Jesús', 1, 'DO0331'),
  ('Ramón Antonio Escarlante Carrasco', 1, 'DO0652'),
  ('Reye Ferrera', 1, 'DO0182'),
  ('Rikelvin Cedeño Shepard', 1, 'DO0660'),
  ('Rubén Esteban Schleider Mercedes', 1, 'DO0692'),
  ('Salvador Santo De La Rosa', 1, 'DO0679'),
  ('Samuel De La Cruz Nuñez', 1, 'DO0698'),
  ('Tomás Alberto De Jesús Cayetano', 1, 'DO0309'),
  ('Tony Sierra', 1, 'DO0821'),
  ('William Encarnación Soriano', 1, 'DO0608'),
  ('Juan Edward Ibert Encarnación', 0, 'DO0683'),
  ('Alexander Antonio Salazar Bastardo', 0, 'DO0298');
