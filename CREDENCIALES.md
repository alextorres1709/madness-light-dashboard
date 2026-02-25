# Madness Light — Panel de Administración

## Datos de Inicio de Sesión

- **URL:** http://127.0.0.1:5000
- **Email:** admin@madnesslight.com
- **Contraseña:** admin123

## Cómo Arrancar

```bash
cd ~/Documents/madness-light-dashboard
source venv/bin/activate
python app.py
```

Luego abre http://127.0.0.1:5000 en tu navegador.

## Secciones del Panel

| Sección | Ruta | Descripción |
|---------|------|-------------|
| Dashboard | `/dashboard` | Vista general con KPIs y gráficos |
| Fiestas | `/events` | Gestión de eventos y fiestas |
| Estadísticas | `/estadisticas` | Análisis detallado del agente |
| Agente de IA | `/agente` | Estado y configuración del agente |
| Ajustes | `/settings` | Información de la empresa |
