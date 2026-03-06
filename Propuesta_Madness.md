# Propuesta de Solución Tecnológica para Madness Light

---

## 1. Resumen Ejecutivo

Madness Light gestiona cada semana un volumen considerable de consultas repetitivas por parte de su audiencia: precios, ubicaciones, horarios, dress code, información sobre el programa de RRPP. Este volumen crece con cada evento y el equipo no puede atenderlo todo a tiempo. Pero el problema real no es solo la carga de trabajo: es que todas esas conversaciones contienen información valiosa sobre lo que los clientes quieren, lo que les frena y lo que les interesa — y esa información se pierde.

Esta propuesta documenta la solución implementada: un agente de IA en Telegram que atiende a los clientes 24/7 y, al mismo tiempo, extrae estadísticas de cada conversación. El sistema genera automáticamente rankings de dudas frecuentes, análisis de objeciones sobre RRPP, métricas de interés por evento, sentimiento de los usuarios y sugerencias de mejora. Todo acompañado de un panel de control web completo con 10 módulos de gestión.

---

## 2. Problemas que resuelve

El equipo de Madness Light se enfrentaba a cuatro problemas concretos:

**Sobrecarga de mensajes repetitivos.** Decenas de personas preguntaban cada semana lo mismo: dónde es la fiesta, cuánto cuesta, si se puede entrar con deportivas, cómo funciona lo de los RRPP. El equipo respondía a mano, lo que consumía tiempo y generaba inconsistencias.

**Retrasos en la atención.** Un usuario que pregunta a las 2 de la madrugada del viernes no recibe respuesta hasta el sábado por la mañana. Para entonces, el momento de intención de compra ya pasó.

**Decisiones a ciegas.** No había forma de saber qué preguntan los clientes, qué dudas les frenan, qué eventos generan más interés ni qué objeciones tienen sobre el programa RRPP. Cada conversación era información valiosa que se perdía sin generar ningún dato útil.

**Captación de RRPP manual y lenta.** Explicar el programa a cada interesado consume tiempo del equipo. Sin automatización, el proceso no escala.

---

## 3. Qué se ha construido

La solución tiene tres componentes principales:

### 3.1. Bot de Telegram con IA

Un agente conversacional que atiende a los usuarios de Madness Light en Telegram, las 24 horas del día. No usa menús ni respuestas predefinidas: genera respuestas dinámicas interpretando la intención y el contexto de cada conversación.

Funcionalidades principales:
- Informa sobre fiestas, precios, salas y horarios con datos actualizados en tiempo real
- Envía los pósters oficiales de cada evento directamente al chat
- Comparte enlaces de compra en Elite Events
- Explica el programa de RRPP con todos los rangos y beneficios (Base, Embajador, Elite)
- Mantiene el contexto de conversaciones anteriores del mismo usuario
- Responde consultas sobre normativa, dress code y políticas de acceso
- Filtra preguntas fuera de tema para no comprometer la imagen de marca

El agente está construido sobre GPT-4o de OpenAI y se conecta en tiempo real a la base de datos de eventos de Madness Light. Cuando se crea o modifica un evento en el panel, el bot ya tiene esa información disponible al instante.

### 3.2. Panel de control web (Dashboard)

Una aplicación web accesible desde cualquier navegador, sin necesidad de instalar nada. Tiene diez módulos de gestión:

- **Dashboard principal:** KPIs en tiempo real (mensajes, usuarios únicos, retención), resumen RRPP con tasa de interés, funnel de conversión (usuarios → recurrentes → interesados RRPP), gráficos de tendencia diaria y distribución por horas.
- **Fiestas:** CRUD completo de eventos. Calendario visual mensual. Analytics por fiesta (menciones, usuarios interesados). Exportación a CSV.
- **Estadísticas:** Métricas de retención, usuarios nuevos vs recurrentes, horas pico, análisis de dudas frecuentes, objeciones RRPP, sentimiento general y sugerencias de mejora por IA. Exportación a CSV.
- **Agente de IA:** Estado del agente, fuentes de datos que consulta, análisis automático de conversaciones con sugerencias de mejora.
- **Conversaciones:** Historial completo de todos los usuarios que han interactuado con el bot. Búsqueda por nombre o ID. Vista del chat completo con filtros por fecha.
- **Usuarios:** Gestión de accesos al panel con tres roles (Admin, Editor, Viewer). Crear, editar, activar o desactivar cuentas.
- **Actividad:** Log de auditoría de todo lo que ocurre en el panel. Quién hizo qué y cuándo.
- **Salas:** Gestión de los locales donde se celebran las fiestas. Alta, edición y activación de salas.
- **Mensajes:** Envío de mensajes masivos a la audiencia vía Telegram. Segmentación por actividad reciente (todos, activos en 7 días, activos en 30 días). Vista previa antes de enviar.
- **Ajustes:** Configuración de la información de empresa que el bot usa como contexto.

### 3.3. Estadísticas de dudas y tendencias (Motor de análisis con IA)

Además de atender clientes, el sistema convierte cada conversación en datos accionables. Cada vez que un usuario pregunta algo, esa duda queda registrada, clasificada y cuantificada. El análisis se genera automáticamente y se actualiza cada hora:

- **Ranking de dudas frecuentes:** qué preguntan más los clientes (precios, ubicación, dress code, RRPP) con porcentajes exactos
- **Interés por evento:** cuántas veces se menciona cada fiesta en el chat, cuántos usuarios distintos preguntan y evolución temporal
- **Análisis RRPP completo:** dudas principales sobre el programa, objeciones frecuentes (comisiones, compromiso, requisitos), nivel de interés y sugerencias de conversión
- **Sentimiento general:** cómo se sienten los usuarios respecto a la marca y los eventos
- **Métricas de retención:** cuántos usuarios vuelven a hablar con el bot, cuántos son nuevos, tasa de retención semanal
- **Funnel de conversión:** usuarios totales → recurrentes → interesados en RRPP
- **Sugerencias de mejora:** recomendaciones concretas generadas por IA basadas en el histórico real de conversaciones

---

## 4. Sistema de usuarios y control de acceso

El panel implementa un sistema de roles para que distintas personas del equipo puedan acceder con los permisos que les corresponden:

- **Admin:** Acceso completo a todos los módulos, incluyendo gestión de usuarios, salas, mensajes masivos y ajustes.
- **Editor:** Puede gestionar eventos, ver conversaciones y estadísticas. No accede a la configuración ni a la gestión de usuarios.
- **Viewer:** Solo puede consultar información. No puede crear, editar ni eliminar nada.

Cada acción realizada en el panel queda registrada en el log de actividad con el usuario responsable, la fecha y el detalle de lo que se hizo.

---

## 5. Infraestructura y tecnología

| Componente | Tecnología |
|---|---|
| Bot de IA | OpenAI GPT-4o |
| Base de datos | Supabase PostgreSQL |
| Automatización de flujos | n8n |
| Mensajería | Telegram Bot API |
| Panel web | Flask + Chart.js |
| Hosting | Vercel (cloud serverless) |

La arquitectura es serverless, lo que elimina los costes de servidor dedicado y garantiza disponibilidad superior al 99,9%. Las actualizaciones del panel no requieren tiempo de inactividad.

---

## 6. Seguridad

- Todas las comunicaciones van cifradas por SSL.
- El bot solo tiene acceso de lectura a los datos que necesita para responder.
- El sistema de roles garantiza que cada usuario ve únicamente lo que le corresponde.
- El log de auditoría registra cada acción en el panel de forma permanente.
- El agente incluye filtros de contenido que impiden que sea manipulado para generar respuestas fuera del guion de Madness Light.

---

## 7. Impacto estimado

Los datos proyectados parten del volumen de consultas observado y los tiempos de respuesta habituales del equipo:

- **+40% en conversión de entradas:** Responder al instante cuando el usuario está activo y con intención de compra mejora la tasa de conversión de forma directa.
- **-80% en carga de soporte:** El bot resuelve el 80% de las consultas recurrentes sin intervención humana.
- **100% visibilidad de datos:** Por primera vez, estadísticas completas de lo que preguntan los clientes, qué les frena, qué eventos generan más interés y cómo evoluciona el sentimiento. Cada decisión se toma con datos reales, no con intuición.

---

## 8. Estado actual y próximos pasos

La plataforma está desplegada en producción. El bot está operativo en Telegram y el panel de control es accesible por el equipo de Madness Light.

El siguiente paso es la fase de ajuste y expansión:
- Calibración del tono conversacional según el manual de identidad de Madness Light
- Formación del equipo en el uso del panel (gestión de eventos, lectura de métricas, envío de mensajes)
- Monitorización activa durante las primeras fiestas con el sistema en marcha
- Incorporación de nuevas funcionalidades según las necesidades que vayan surgiendo
