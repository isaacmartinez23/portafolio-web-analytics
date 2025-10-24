import os

from dotenv import load_dotenv

load_dotenv()

# Configuración GA4
GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "123456789")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH", "credentials.json")

# Configuración Streamlit
PAGE_CONFIG = {
    "page_title": "Dashboard Sitio Web",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Fechas predeterminadas
DEFAULT_DATE_RANGE = 30  # días

# Métricas disponibles
AVAILABLE_METRICS = {
    "sessions": "Sesiones",
    "totalUsers": "Usuarios Totales",
    "activeUsers": "Usuarios Activos",
    "screenPageViews": "Vistas de Página",
    "bounceRate": "Tasa de Rebote",
    "averageSessionDuration": "Duración Promedio de Sesión",
    "conversions": "Conversiones",
    "eventCount": "Eventos Totales",
}

# Dimensiones disponibles
AVAILABLE_DIMENSIONS = {
    "date": "Fecha",
    "country": "País",
    "city": "Ciudad",
    "deviceCategory": "Categoría de Dispositivo",
    "browser": "Navegador",
    "operatingSystem": "Sistema Operativo",
    "sessionDefaultChannelGroup": "Canal de Tráfico",
    "pagePath": "Ruta de Página",
    "pageTitle": "Título de Página",
}
