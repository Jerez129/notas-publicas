-- 5 porqués ligados a cada nota + marca de notas reasignadas
ALTER TABLE analisis ADD COLUMN nota_id INTEGER;
ALTER TABLE analisis ADD COLUMN responsable TEXT;
ALTER TABLE analisis ADD COLUMN actualizado_en TEXT;
ALTER TABLE notas ADD COLUMN reasignada_de TEXT;

-- Ligar el histórico de la hoja KPIS a su nota: mismo cliente, fecha más cercana
UPDATE analisis SET nota_id = (
  SELECT n.id FROM notas n
  WHERE n.codigo_cliente = analisis.codigo_cliente
  ORDER BY abs(julianday(n.fecha) - julianday(analisis.fecha)), n.id
  LIMIT 1
);
