-- ─────────────────────────────────────────────────────────────
-- Migración: tabla wa_processed_messages
-- Necesaria para el nodo "🧹 Deduplicar (msg.id)" del workflow.
--
-- WhatsApp Cloud API reintenta los webhooks si no recibe 200 a
-- tiempo. Sin esta tabla, cada reintento generaría una respuesta
-- duplicada al usuario y filas duplicadas en `conversations`.
--
-- Ejecutar UNA SOLA VEZ contra la base de datos de Supabase
-- (la misma que usa el dashboard y el workflow n8n).
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS wa_processed_messages (
    wa_msg_id    TEXT        PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Limpieza automática de IDs antiguos (>7 días) — opcional pero
-- evita que la tabla crezca sin control. Se puede ejecutar a mano
-- o programar como cron en n8n.
--
-- DELETE FROM wa_processed_messages WHERE processed_at < NOW() - INTERVAL '7 days';

CREATE INDEX IF NOT EXISTS idx_wa_processed_messages_at
    ON wa_processed_messages (processed_at);
