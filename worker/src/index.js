// API de Notas Públicas: Cloudflare Worker + D1
// La contraseña vive como secreto (DASH_PASSWORD), nunca en el repositorio.

const NOTA_COLS = [
  "ext_id", "origen", "codigo_np", "fecha", "centro", "ruta", "chofer", "chofer_original",
  "supervisor", "vehiculo", "codigo_cliente", "nombre_cliente", "categoria", "tipo_reclamo",
  "situacion", "vendedor", "ruta_preventa", "coordinador_ventas", "tipo_impacto", "status",
  "fecha_inicio", "plazo", "fecha_cierre", "comentario",
];
const TOKEN_HORAS = 12;

function cors(env, req) {
  const origin = req.headers.get("Origin") || "";
  const allowed = (env.ALLOWED_ORIGINS || "").split(",").map((s) => s.trim());
  return {
    "Access-Control-Allow-Origin": allowed.includes(origin) ? origin : allowed[0] || "",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Max-Age": "86400",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    Vary: "Origin",
  };
}

function json(data, status, headers) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...headers },
  });
}

const enc = new TextEncoder();
const b64 = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/=+$/, "").replace(/\+/g, "-").replace(/\//g, "_");

async function hmac(secret, msg) {
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return b64(await crypto.subtle.sign("HMAC", key, enc.encode(msg)));
}

function iguales(a, b) {
  if (a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

async function crearToken(env) {
  const exp = String(Date.now() + TOKEN_HORAS * 3600e3);
  return `${exp}.${await hmac(env.TOKEN_SECRET, exp)}`;
}

async function tokenValido(env, req) {
  const t = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  const [exp, firma] = t.split(".");
  if (!exp || !firma || Number(exp) < Date.now()) return false;
  return iguales(firma, await hmac(env.TOKEN_SECRET, exp));
}

export default {
  async fetch(req, env) {
    const h = cors(env, req);
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: h });
    const { pathname } = new URL(req.url);

    try {
      if (pathname === "/api/login" && req.method === "POST") {
        const { password } = await req.json().catch(() => ({}));
        if (typeof password !== "string" || !iguales(password, env.DASH_PASSWORD || "")) {
          await new Promise((r) => setTimeout(r, 800)); // frena intentos repetidos
          return json({ error: "Contraseña incorrecta" }, 401, h);
        }
        return json({ token: await crearToken(env), horas: TOKEN_HORAS }, 200, h);
      }

      if (!(await tokenValido(env, req))) return json({ error: "No autorizado" }, 401, h);

      if (pathname === "/api/notas" && req.method === "GET") {
        const { results } = await env.DB.prepare(
          `SELECT n.id, ${NOTA_COLS.map((c) => "n." + c).join(",")}, n.reasignada_de, n.creado_en, a.id AS analisis_id
           FROM notas n LEFT JOIN analisis a ON a.nota_id = n.id
           ORDER BY n.fecha DESC, n.id DESC`).all();
        return json({ notas: results }, 200, h);
      }

      if (pathname === "/api/analisis" && req.method === "GET") {
        const { results } = await env.DB.prepare(
          `SELECT a.*, n.chofer, n.fecha AS nota_fecha FROM analisis a LEFT JOIN notas n ON n.id = a.nota_id
           ORDER BY COALESCE(a.actualizado_en, a.fecha) DESC, a.id DESC`).all();
        return json({ analisis: results }, 200, h);
      }

      // Crear o actualizar el 5 porqués de una nota
      if (pathname === "/api/analisis" && req.method === "POST") {
        const b = await req.json();
        const notaId = Number(b.nota_id);
        if (!Number.isInteger(notaId) || notaId <= 0) return json({ error: "Falta la nota" }, 400, h);
        const nota = await env.DB.prepare("SELECT * FROM notas WHERE id = ?").bind(notaId).first();
        if (!nota) return json({ error: "La nota no existe" }, 404, h);
        const txt = (v) => (typeof v === "string" && v.trim() ? v.trim().slice(0, 2000) : null);
        const campos = ["kpi", "porque1", "porque2", "porque3", "porque4", "porque5", "accion_correctiva", "responsable"];
        const v = Object.fromEntries(campos.map((c) => [c, txt(b[c])]));
        if (!v.porque1 || !v.accion_correctiva) return json({ error: "Escribe al menos el 1er por qué y la acción correctiva" }, 400, h);
        await env.DB.prepare(
          `INSERT INTO analisis (ext_id, nota_id, fecha, ruta, codigo_cliente, nombre_cliente, situacion, tipo_reclamo,
             kpi, porque1, porque2, porque3, porque4, porque5, accion_correctiva, responsable, actualizado_en)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
           ON CONFLICT(ext_id) DO UPDATE SET kpi=excluded.kpi, porque1=excluded.porque1, porque2=excluded.porque2,
             porque3=excluded.porque3, porque4=excluded.porque4, porque5=excluded.porque5,
             accion_correctiva=excluded.accion_correctiva, responsable=excluded.responsable, actualizado_en=datetime('now')`
        ).bind(
          // Si la nota ya tiene análisis (p. ej. del histórico) se actualiza ese mismo registro
          (await env.DB.prepare("SELECT ext_id FROM analisis WHERE nota_id = ?").bind(notaId).first())?.ext_id || `nota-${notaId}`,
          notaId, nota.fecha, nota.ruta, nota.codigo_cliente, nota.nombre_cliente, nota.situacion, nota.tipo_reclamo,
          v.kpi, v.porque1, v.porque2, v.porque3, v.porque4, v.porque5, v.accion_correctiva, v.responsable
        ).run();
        return json({ ok: true }, 200, h);
      }

      if (pathname === "/api/importar" && req.method === "POST") {
        const { filas } = await req.json();
        if (!Array.isArray(filas) || filas.length === 0) return json({ error: "No hay filas" }, 400, h);
        if (filas.length > 2000) return json({ error: "Máximo 2000 filas por carga" }, 400, h);
        const sql = `INSERT OR IGNORE INTO notas (${NOTA_COLS.join(",")}) VALUES (${NOTA_COLS.map(() => "?").join(",")})`;
        const stmts = [];
        for (const f of filas) {
          if (!f || typeof f.ext_id !== "string" || !f.ext_id.startsWith("forms-")) continue;
          const row = { ...f, origen: "forms" };
          stmts.push(env.DB.prepare(sql).bind(...NOTA_COLS.map((c) => (row[c] === undefined || row[c] === "" ? null : String(row[c]).slice(0, 4000)))));
        }
        let nuevas = 0;
        for (let i = 0; i < stmts.length; i += 100) {
          const res = await env.DB.batch(stmts.slice(i, i + 100));
          nuevas += res.reduce((s, r) => s + (r.meta?.changes || 0), 0);
        }
        return json({ recibidas: filas.length, nuevas, repetidas: stmts.length - nuevas }, 200, h);
      }

      return json({ error: "No encontrado" }, 404, h);
    } catch (e) {
      return json({ error: "Error del servidor", detalle: String(e.message || e) }, 500, h);
    }
  },
};
