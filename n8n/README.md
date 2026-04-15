# n8n — Madness Light WhatsApp

Workflow: [`birthday_whatsapp_workflow.json`](birthday_whatsapp_workflow.json)

## Variables de entorno (n8n)

| Variable | Para qué | Ejemplo |
|---|---|---|
| `WHATSAPP_TOKEN` | Token permanente de Meta Cloud API | `EAAJ…` |
| `WHATSAPP_PHONE_ID` | ID del número de WhatsApp Business | `123456789012345` |
| `WHATSAPP_VERIFY_TOKEN` | Token que pones también en el panel de Meta al registrar el webhook | `madness-verify-2026` |
| `MADNESS_API_URL` | URL pública del dashboard Flask | `https://madness.tudominio.com` |
| `MADNESS_API_KEY` | Mismo valor que `API_KEY` del Flask | `ml-api-key-…` |

## Pasos para activarlo

1. **Migración SQL** — ejecutar [`migration_dedup_table.sql`](migration_dedup_table.sql) contra la base de datos Supabase. Solo una vez.
2. **Importar el workflow** en n8n.
3. **Asignar credenciales** — placeholders `SUPABASE_POSTGRES_ID` y `OPENAI_CREDENTIAL_ID` se reemplazan con las credenciales reales en n8n.
4. **Configurar variables de entorno** (tabla de arriba).
5. **Registrar el webhook en Meta**:
   - Callback URL: `https://tu-n8n.com/webhook/whatsapp-madness`
   - Verify token: el mismo valor que pusiste en `WHATSAPP_VERIFY_TOKEN`
   - Suscribir el campo `messages`
6. **Crear plantillas** en Meta Business Manager:
   - `birthday_greeting` (Utility, var `{{1}}` = nombre)
   - `birthday_prenotice` (Utility, var `{{1}}` = nombre)
   - `event_promotion` (Marketing, vars: fecha, evento, sala)
7. **Activar el workflow** en n8n (toggle "Active").

## Cambios v2 (vs v1)

| # | Fix | Por qué |
|---|---|---|
| 1 | **Webhook GET separado** que responde al `hub.challenge` | Sin esto Meta no puede registrar el webhook → bot nunca recibe nada → stats vacías |
| 2 | **Nodo de deduplicación** con `wa_processed_messages` | WhatsApp reintenta agresivamente; sin dedup duplicaba respuestas y filas en DB |
| 3 | **Save user ANTES de llamar a IA** | Evita race condition: si el flow falla, el mensaje del usuario igual queda registrado y las stats son fiables |
| 4 | **Cron diario 10:00** en vez de cada 3 minutos | Antes mandaba 300 mensajes/persona/día → ban Meta seguro |
| 5 | **Nodo "marcar pre-felicitado"** tras cumple-mañana | Antes ese flujo no marcaba nada y se reenviaba en bucle |
| 6 | **Endpoint API filtra `whatsapp_opt_in=True`** y deduplica las últimas 48h | Cumple normas WhatsApp Business: solo opted-in para plantillas |
| 7 | **Histórico ASC dentro del SELECT** + queries parametrizadas | El bot leía el historial al revés; además había SQL injection con `'{{ userId }}'` |
| 8 | **`Cargar Eventos` filtra `active=TRUE` y `date>=NOW()`** | Antes pasaba los 10 más recientes (incluyendo pasados) al GPT |
| 9 | **Normalización E.164 de teléfonos** (función Code) | Acepta `"+34 612…"`, `"00 34…"`, `"612…"` y los convierte a `34612…` |
| 10 | **`retryOnFail` + `continueOnFail` en envíos WhatsApp** | Un error puntual con un cliente no rompe todo el lote de cumpleaños |
| 11 | **`saveDataErrorExecution: "all"`** | Las ejecuciones fallidas se guardan completas para debug |
| 12 | **`preview_url: true` en respuestas** | Los links de Elite Events generan tarjeta de previsualización |
| 13 | **Nombre de pila** en plantillas (`name.split(' ')[0]`) | Más natural ("Feliz cumple Carlos!" vs "…Carlos Martínez!") |

## Cómo verificar que las stats vuelven a contar

1. Una vez activo, manda **un mensaje** desde tu propio WhatsApp al número del bot.
2. Comprueba en Supabase:
   ```sql
   SELECT * FROM conversations ORDER BY created_at DESC LIMIT 5;
   SELECT * FROM wa_processed_messages ORDER BY processed_at DESC LIMIT 5;
   ```
   Deberías ver tu mensaje (`role='user'`) y la respuesta del bot (`role='assistant'`).
3. Abre `/estadisticas` en el dashboard — el contador "Mensajes totales" debe haber subido.
4. Si las cards de IA siguen vacías, tira de `Actualizar insights` (botón en la página); cachean 1h.
