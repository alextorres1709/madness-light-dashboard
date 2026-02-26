-- =====================================================
-- Madness Light — Unified Database Schema (Supabase)
-- =====================================================
-- Run this in Supabase SQL Editor (supabase.com → SQL Editor)
-- This schema is shared between the Flask dashboard and
-- the Telegram bot (n8n workflow).
-- =====================================================

-- 1. EVENTS — Shared between dashboard + bot
-- Dashboard creates/edits events, bot reads them
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    date TIMESTAMPTZ NOT NULL,
    venue VARCHAR(300) NOT NULL,
    theme VARCHAR(100) DEFAULT 'Normal',
    description TEXT DEFAULT '',
    dj_info VARCHAR(300) DEFAULT '',
    capacity INTEGER DEFAULT 0,
    entry_price VARCHAR(100) DEFAULT '',
    entry_link VARCHAR(500) DEFAULT '',
    image_url VARCHAR(500) DEFAULT '',
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for bot queries (active + future events)
CREATE INDEX IF NOT EXISTS idx_events_active_date
    ON events (active, date)
    WHERE active = true;


-- 2. CONVERSATIONS — Bot chat history
-- Bot writes conversation turns, dashboard reads for stats
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for loading user history (bot) and stats (dashboard)
CREATE INDEX IF NOT EXISTS idx_conversations_user_id
    ON conversations (user_id, created_at DESC);


-- 3. MESSAGES — Dashboard message log
-- Stores aggregated bot interactions for dashboard KPIs
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    user_name VARCHAR(200) DEFAULT 'Unknown',
    message TEXT NOT NULL,
    response TEXT DEFAULT '',
    platform VARCHAR(50) DEFAULT 'telegram',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Index for dashboard time-based queries
CREATE INDEX IF NOT EXISTS idx_messages_timestamp
    ON messages (timestamp DESC);


-- 4. COMPANY_INFO — Dashboard company settings
-- Stores company info editable from the dashboard
CREATE TABLE IF NOT EXISTS company_info (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) DEFAULT 'Madness Light',
    description TEXT DEFAULT 'Empresa de fiestas y eventos en Madrid',
    phone VARCHAR(50) DEFAULT '',
    email VARCHAR(200) DEFAULT '',
    address VARCHAR(300) DEFAULT '',
    hours VARCHAR(200) DEFAULT '',
    extra_info TEXT DEFAULT ''
);

-- Seed default company info
INSERT INTO company_info (name, description, phone, email, address, hours, extra_info)
SELECT
    'Madness Light',
    'Madness Light es una empresa de organización de fiestas light para jóvenes en Madrid. Se centra en eventos de tarde, con temáticas especiales, DJs y animación, ofreciendo una experiencia de ocio segura y organizada.',
    '',
    'info@madnesslight.com',
    'Madrid, España',
    'Fiestas de tarde, cada 1-2 semanas',
    E'COMPRA DE ENTRADAS:\nLas entradas se compran exclusivamente a través de la app de Elite Events. Desde la app se puede: comprar entradas, introducir códigos de RRPP y ver info del evento. El acceso se controla mediante la entrada digital de la app.\n\nTIPO DE FIESTAS:\nFiestas light (sin alcohol). Horario habitual de tarde. Fiestas cada 1 o 2 semanas. Temáticas especiales (Halloween, Carnaval, Hawaiana, etc.). DJs y animación. Eventos puntuales ''fiestas tochas'' (Halloween, Carnaval, etc.).\n\nSALAS ACTIVAS:\nLab (Madrid), Shôko Madrid, Jowke (Madrid), Nazca (Madrid), Tiffany''s (Madrid). Teatro Barceló ya no se utiliza (cerrado). Las salas pueden variar según la temporada.\n\nPROGRAMA RRPP:\nMadness Light dispone de un programa de RRPP orientado a la promoción de sus eventos. Info secundaria, solo se explica si el usuario pregunta específicamente.'
WHERE NOT EXISTS (SELECT 1 FROM company_info);
