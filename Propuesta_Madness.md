# Propuesta de Solución Tecnológica para Madness Light

---

## 1. Resumen Ejecutivo

Cada semana, decenas de personas le escriben a Madness Light con las mismas preguntas: cuándo es la próxima fiesta, cuánto cuesta la entrada, dónde es, cómo funciona lo de RRPP. El equipo hace lo que puede, pero no da abasto — y mientras tanto, toda esa información sobre qué quieren los clientes, qué les frena o qué les interesa se pierde.

Lo que hemos montado es un sistema que resuelve todo eso de golpe: un agente de IA que atiende en Telegram y en WhatsApp las 24 horas, un panel de control donde se gestiona todo (eventos, clientes, estadísticas, mensajes) y automatizaciones inteligentes como felicitaciones de cumpleaños por WhatsApp. Todo conectado a una misma base de datos, todo funcionando solo.

---

## 2. Qué problemas resuelve

**Nadie puede contestar a todo, todo el rato.** Hay preguntas que llegan a las 2 de la madrugada un viernes. Para cuando alguien las ve el sábado por la mañana, esa persona ya perdió el interés o compró en otro lado. Ahora hay un bot que responde al instante, con la info correcta, a cualquier hora.

**Las mismas preguntas una y otra vez.** Dónde es, cuánto cuesta, puedo entrar con deportivas, cómo funciona lo de RRPP. El bot se encarga de eso para que el equipo pueda centrarse en lo que importa.

**No había datos de nada.** Antes no se sabía qué preguntan los clientes, qué eventos generan más interés ni qué objeciones tienen con el programa de RRPP. Ahora cada conversación se analiza y se convierte en datos útiles: rankings de dudas, sentimiento, sugerencias de mejora.

**Captar RRPP era lento.** Explicar el programa entero a cada persona que pregunta lleva tiempo. El bot lo hace solo, adaptándose a lo que pregunta cada uno, y lo hace bien.

**No había una base de datos de clientes.** No existía un sitio donde ver quién ha venido a las fiestas, cuántas veces, cuándo cumple años o cómo contactarle. Ahora sí, y además esa base de datos alimenta las automatizaciones.

---

## 3. Qué se ha construido

### 3.1. Bot de Telegram con IA

Un agente que habla con los usuarios de Madness Light en Telegram como si fuera un colega del equipo. No es un menú con botones: entiende lo que le dicen y responde de forma natural.

Qué hace:
- Informa sobre fiestas, precios, salas y horarios con datos actualizados en tiempo real
- Envía los pósters oficiales de cada evento directamente al chat
- Comparte enlaces de compra en Elite Events
- Explica el programa de RRPP con rangos, beneficios y sistema de puntos
- Recuerda conversaciones anteriores del mismo usuario
- Responde consultas sobre normativa, dress code y acceso
- Filtra preguntas fuera de tema para no comprometer la imagen de marca

Funciona con GPT-4o de OpenAI y se conecta en tiempo real a la base de datos. Si se crea un evento nuevo en el panel, el bot ya lo sabe al instante.

### 3.2. Bot de WhatsApp con IA + Cumpleaños

El mismo agente, pero en WhatsApp. Misma inteligencia, misma base de datos, misma calidad de respuesta. Esto cubre los dos canales de mensajería principales en España.

Además de atender consultas, el canal de WhatsApp tiene automatizaciones propias:

- **Felicitaciones de cumpleaños:** Cada día a partir de las 8 de la mañana, el sistema revisa la base de datos de clientes. Si hoy es el cumpleaños de alguien, le manda una felicitación personalizada por WhatsApp. El día de antes, le manda un pre-aviso para generar expectativa. Cada persona solo recibe un mensaje al año, sin duplicados.
- **Preparado para más:** Sobre esta misma base se pueden montar recordatorios de eventos, ofertas especiales, notificaciones segmentadas o cualquier otra cosa que se necesite.

### 3.3. Panel de control web

Una aplicación web a la que se accede desde el navegador, sin instalar nada. Tiene once secciones:

- **Dashboard:** Números clave en tiempo real — mensajes, usuarios, retención, interés en RRPP, gráficos de tendencia.
- **Fiestas:** Crear, editar y gestionar eventos. Calendario visual. Analytics por fiesta. Exportación a CSV.
- **Estadísticas:** Retención, usuarios nuevos vs recurrentes, horas pico, dudas frecuentes, objeciones RRPP, sentimiento y sugerencias de mejora generadas por IA.
- **Agente de IA:** Estado del agente, qué datos consulta, análisis automático de conversaciones.
- **Conversaciones:** Todo el historial de chat con usuarios de Telegram y WhatsApp. Búsqueda y filtros por fecha.
- **Clientes:** Base de datos completa — nombre, fecha de nacimiento, teléfono, chat ID, fiestas asistidas, estado activo/inactivo. Buscador, filtros y estadísticas. Es la base que alimenta las automatizaciones de cumpleaños y futuras campañas.
- **Usuarios:** Gestión de quién puede acceder al panel, con tres niveles de permisos.
- **Actividad:** Registro de todo lo que pasa en el panel — quién hizo qué y cuándo.
- **Salas:** Alta y gestión de los locales donde se hacen las fiestas.
- **Mensajes:** Envío de mensajes masivos por Telegram, con segmentación por actividad.
- **Ajustes:** Configuración de la información de empresa que usan los bots.

### 3.4. Base de datos de clientes

Un registro centralizado de todos los asistentes y contactos de Madness Light. Es el núcleo de todo el sistema:

- Los bots registran automáticamente a las personas que interactúan
- Desde el panel se puede buscar, filtrar y consultar cualquier cliente
- Las automatizaciones (cumpleaños, campañas) tiran de estos datos en tiempo real
- Cada cliente tiene su ficha: nombre, fecha de nacimiento, teléfono, ID de chat, historial y estado

### 3.5. Motor de análisis con IA

Cada conversación que tiene el bot se convierte en datos útiles de forma automática:

- **Ranking de dudas:** qué preguntan más y con qué frecuencia
- **Interés por evento:** cuánta gente pregunta por cada fiesta, evolución en el tiempo
- **Análisis de RRPP:** dudas, objeciones y nivel de interés en el programa
- **Sentimiento:** cómo se sienten los usuarios respecto a la marca
- **Retención:** cuántos vuelven, cuántos son nuevos, tasa semanal
- **Sugerencias:** recomendaciones generadas por IA a partir de las conversaciones reales

---

## 4. Roles y permisos

El panel tiene tres niveles de acceso:

- **Admin:** Todo. Gestión de usuarios, clientes, salas, mensajes masivos, ajustes.
- **Editor:** Gestión de eventos, acceso a conversaciones, clientes y estadísticas.
- **Viewer:** Solo consulta. No puede modificar nada.

Todo queda registrado en el log de actividad.

---

## 5. Tecnología

| Componente | Tecnología |
|---|---|
| Inteligencia artificial | OpenAI GPT-4o |
| Base de datos | Supabase (PostgreSQL) |
| Automatizaciones | n8n |
| Canal Telegram | Telegram Bot API |
| Canal WhatsApp | WhatsApp Business Cloud API (Meta) |
| Panel web | Flask + Chart.js |
| Hosting | Vercel (serverless) |

Todo está en la nube, sin servidores dedicados. Disponibilidad superior al 99,9%. Las actualizaciones no requieren tiempo de inactividad. Telegram y WhatsApp comparten la misma base de datos, así que la información es siempre consistente.

---

## 6. Automatizaciones

| Qué hace | Canal | Cuándo | Detalle |
|---|---|---|---|
| Atención al cliente con IA | Telegram | 24/7, tiempo real | Responde al instante con datos actualizados |
| Atención al cliente con IA | WhatsApp | 24/7, tiempo real | Mismo agente, mismo nivel de calidad |
| Felicitación de cumpleaños | WhatsApp | Día del cumpleaños, desde las 8:00h | Mensaje personalizado automático |
| Pre-aviso de cumpleaños | WhatsApp | Día anterior al cumpleaños | Genera expectativa con un mensaje previo |
| Mensajes masivos | Telegram | Cuando se necesite | Envío segmentado desde el panel |

Todo orquestado desde n8n y conectado a Supabase en tiempo real.

---

## 7. Seguridad

- Comunicaciones cifradas por SSL
- Los bots solo acceden a los datos que necesitan para responder
- APIs protegidas por clave de acceso
- Sistema de roles para que cada persona vea solo lo que le corresponde
- Log de auditoría permanente de todas las acciones en el panel
- Filtros de contenido para que los bots no se salgan del guion de Madness Light
- Datos de clientes almacenados conforme a la normativa de protección de datos

---

## 8. Impacto esperado

- **Más ventas de entradas:** Responder al instante cuando alguien está interesado cambia completamente la tasa de conversión. No se pierde el momento.
- **El equipo se libera:** El bot se encarga de las preguntas repetitivas en dos canales. El equipo puede dedicar su tiempo a lo que realmente mueve el negocio.
- **Más alcance:** Estar en WhatsApp además de Telegram cubre prácticamente a toda la audiencia joven en España.
- **Datos reales para decidir:** Por primera vez hay visibilidad total de lo que preguntan los clientes, qué les frena, qué eventos generan más interés y cómo evoluciona el sentimiento.
- **Los clientes se sienten cuidados:** Una felicitación de cumpleaños personalizada por WhatsApp es un detalle pequeño que genera un vínculo real con la marca. Y es completamente automático.

---

## 9. Estado actual y próximos pasos

La plataforma está en producción. Los bots funcionan en Telegram y WhatsApp, el panel de control está operativo, la base de datos de clientes está conectada y las automatizaciones de cumpleaños están activas.

Lo que viene ahora:
- Ajustar el tono del bot según el estilo de Madness Light
- Formar al equipo en el uso del panel
- Monitorizar el sistema durante las primeras fiestas
- Ampliar automatizaciones: recordatorios de eventos, ofertas personalizadas, campañas por perfil de cliente
- Lo que vaya surgiendo sobre la marcha
