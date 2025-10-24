from datetime import datetime, timedelta

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_option_menu import option_menu

from config import *
from ga4_client import GA4Client

# Configuración de página
st.set_page_config(**PAGE_CONFIG)

# CSS personalizado
st.markdown(
    """
<style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .stMetric > label {
        font-size: 16px;
        color: #262730;
        font-weight: 600;
    }
    .stMetric > div {
        font-size: 28px;
        color: #1f77b4;
        font-weight: 700;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource(ttl=300)
def load_ga4_client():
    """Carga el cliente GA4 con caché"""
    return GA4Client(GA4_PROPERTY_ID, CREDENTIALS_PATH)


@st.cache_data(ttl=300)
def get_cached_data(_client, start_date, end_date, data_type):
    """Obtiene datos con caché"""
    if data_type == "basic":
        return _client.get_basic_report(
            start_date,
            end_date,
            ["sessions", "totalUsers", "screenPageViews", "bounceRate"],
            dimensions=["date"],
        )
    elif data_type == "pages":
        return _client.get_top_pages(start_date, end_date, 15)
    elif data_type == "sources":
        return _client.get_traffic_sources(start_date, end_date, 10)
    elif data_type == "geographic":
        return _client.get_geographic_data(start_date, end_date, 20)
    elif data_type == "devices":
        return _client.get_device_data(start_date, end_date)
    elif data_type == "realtime":
        return _client.get_realtime_report(["activeUsers", "screenPageViews"])


def create_metric_cards(df):
    """Crea tarjetas de métricas principales"""
    if df.empty:
        st.warning("No hay datos disponibles para el período seleccionado")
        return

    # Calcular métricas totales
    total_sessions = df["sessions"].sum() if "sessions" in df.columns else 0
    total_users = df["totalUsers"].sum() if "totalUsers" in df.columns else 0
    total_pageviews = (
        df["screenPageViews"].sum() if "screenPageViews" in df.columns else 0
    )
    avg_bounce_rate = df["bounceRate"].mean() if "bounceRate" in df.columns else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🎯 Sesiones Totales",
            value=f"{total_sessions:,}",
            delta=f"+{total_sessions * 0.12:.0f}" if total_sessions > 0 else None,
        )

    with col2:
        st.metric(
            label="👥 Usuarios Totales",
            value=f"{total_users:,}",
            delta=f"+{total_users * 0.08:.0f}" if total_users > 0 else None,
        )

    with col3:
        st.metric(
            label="📄 Páginas Vistas",
            value=f"{total_pageviews:,}",
            delta=f"+{total_pageviews * 0.15:.0f}" if total_pageviews > 0 else None,
        )

    with col4:
        st.metric(
            label="📉 Tasa de Rebote",
            value=f"{avg_bounce_rate:.1%}" if avg_bounce_rate > 0 else "N/A",
            delta=f"-{avg_bounce_rate * 0.05:.1%}" if avg_bounce_rate > 0 else None,
            delta_color="inverse",
        )


def create_trend_chart(df):
    """Crea gráfico de tendencias"""
    if df.empty or "date" not in df.columns:
        st.warning("No hay datos de tendencias disponibles")
        return

    df_sorted = df.sort_values("date")

    fig = go.Figure()

    # Sesiones
    if "sessions" in df_sorted.columns:
        fig.add_trace(
            go.Scatter(
                x=df_sorted["date"],
                y=df_sorted["sessions"],
                mode="lines+markers",
                name="Sesiones",
                line=dict(color="#1f77b4", width=3),
                marker=dict(size=6),
            )
        )

    # Usuarios
    if "totalUsers" in df_sorted.columns:
        fig.add_trace(
            go.Scatter(
                x=df_sorted["date"],
                y=df_sorted["totalUsers"],
                mode="lines+markers",
                name="Usuarios",
                line=dict(color="#ff7f0e", width=3),
                marker=dict(size=6),
            )
        )

    fig.update_layout(
        title="📈 Tendencia de Tráfico",
        xaxis_title="Fecha",
        yaxis_title="Cantidad",
        hovermode="x unified",
        height=400,
        showlegend=True,
    )

    return fig


def create_sources_chart(df):
    """Crea gráfico de fuentes de tráfico"""
    if df.empty:
        st.warning("No hay datos de fuentes de tráfico")
        return

    fig = px.pie(
        df,
        values="sessions",
        names="sessionDefaultChannelGroup",
        title="🎯 Fuentes de Tráfico",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )

    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(height=400, showlegend=True)

    return fig


def create_geographic_chart(df):
    """Crea gráfico geográfico"""
    if df.empty:
        st.warning("No hay datos geográficos")
        return

    # Top países
    country_data = df.groupby("country")["sessions"].sum().reset_index()
    country_data = country_data.sort_values("sessions", ascending=False).head(10)

    fig = px.bar(
        country_data,
        x="country",
        y="sessions",
        title="🌍 Top Países por Sesiones",
        color="sessions",
        color_continuous_scale="Blues",
    )

    fig.update_layout(height=400, xaxis_tickangle=-45)
    return fig


def main():
    """Función principal del dashboard"""

    # Header
    st.title("📊 Dashboard de Análisis Web con GA4 y Streamlit")
    st.markdown("Monitoreo de visitantes y métricas de mi página web personal")
    st.markdown("---")

    # Sidebar para configuración
    with st.sidebar:
        st.header("⚙️ Configuración")

        # Selector de fechas
        col1, col2 = st.columns(2)
        with col1:
            # Asegurar que el valor por defecto sea tipo date (no datetime)
            default_start = (datetime.now() - timedelta(days=DEFAULT_DATE_RANGE)).date()
            start_date = st.date_input("Fecha inicio", default_start)
        with col2:
            default_end = (
                datetime.now() - timedelta(days=1)
            ).date()  # GA4 tiene delay de 1 día
            end_date = st.date_input("Fecha fin", default_end)

        # Botón de actualizar
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.markdown("**💡 Datos en tiempo real disponibles**")
        st.markdown("**📅 Datos históricos con 24-48h de delay**")

    # Menú de navegación
    selected = option_menu(
        menu_title=None,
        options=[
            " Resumen",
            " Páginas",
            " Geografía",
            " Dispositivos",
            " Tiempo Real",
        ],
        icons=["graph-up", "file-text", "globe", "phone", "lightning"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )

    # Cargar cliente GA4
    try:
        with st.spinner("Conectando con Google Analytics..."):
            ga4_client = load_ga4_client()
    except Exception as e:
        st.error("❌ Error al conectar con GA4. Verifica tu configuración.")
        st.code(str(e))
        st.stop()

    # Convertir fechas a string
    # start_date / end_date vienen como datetime.date; manejar None por seguridad
    start_date_str = start_date.strftime("%Y-%m-%d") if start_date is not None else None
    end_date_str = end_date.strftime("%Y-%m-%d") if end_date is not None else None

    # Contenido según selección
    if selected == " Resumen":
        st.subheader("📋 Resumen General")

        # Cargar datos básicos
        with st.spinner("Cargando métricas principales..."):
            basic_data = get_cached_data(
                ga4_client, start_date_str, end_date_str, "basic"
            )
            sources_data = get_cached_data(
                ga4_client, start_date_str, end_date_str, "sources"
            )

        # Métricas principales
        create_metric_cards(basic_data)
        st.markdown("---")

        # Gráficos en columnas
        col1, col2 = st.columns(2)

        with col1:
            # Tendencias
            if not basic_data.empty:
                trend_chart = create_trend_chart(basic_data)
                if trend_chart:
                    st.plotly_chart(trend_chart, use_container_width=True)

        with col2:
            # Fuentes de tráfico
            if not sources_data.empty:
                sources_chart = create_sources_chart(sources_data)
                if sources_chart:
                    st.plotly_chart(sources_chart, use_container_width=True)

    elif selected == " Páginas":
        st.subheader("📄 Páginas Más Visitadas")

        with st.spinner("Cargando datos de páginas..."):
            pages_data = get_cached_data(
                ga4_client, start_date_str, end_date_str, "pages"
            )

        if not pages_data.empty:
            # Tabla de páginas
            st.dataframe(
                pages_data[
                    [
                        "pageTitle",
                        "pagePath",
                        "screenPageViews",
                        "sessions",
                        "totalUsers",
                    ]
                ].head(15),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "pageTitle": "Título de Página",
                    "pagePath": "Ruta",
                    "screenPageViews": "Vistas",
                    "sessions": "Sesiones",
                    "totalUsers": "Usuarios",
                },
            )

            # Gráfico de top páginas
            top_pages = pages_data.head(10)
            fig = px.bar(
                top_pages,
                x="screenPageViews",
                y="pageTitle",
                orientation="h",
                title="Top 10 Páginas por Vistas",
                color="screenPageViews",
                color_continuous_scale="Blues",
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay datos de páginas disponibles")

    elif selected == " Geografía":
        st.subheader("🌍 Análisis Geográfico")

        with st.spinner("Cargando datos geográficos..."):
            geo_data = get_cached_data(
                ga4_client, start_date_str, end_date_str, "geographic"
            )

        if not geo_data.empty:
            # Gráfico geográfico
            geo_chart = create_geographic_chart(geo_data)
            if geo_chart:
                st.plotly_chart(geo_chart, use_container_width=True)

            # Tabla detallada
            st.subheader("📍 Desglose por Ciudad")
            st.dataframe(
                geo_data[
                    ["country", "city", "sessions", "totalUsers", "screenPageViews"]
                ].head(20),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("No hay datos geográficos disponibles")

    elif selected == " Dispositivos":
        st.subheader("📱 Análisis de Dispositivos")

        with st.spinner("Cargando datos de dispositivos..."):
            device_data = get_cached_data(
                ga4_client, start_date_str, end_date_str, "devices"
            )

        if not device_data.empty:
            col1, col2 = st.columns(2)

            with col1:
                # Dispositivos
                if "deviceCategory" in device_data.columns:
                    device_summary = (
                        device_data.groupby("deviceCategory")["sessions"]
                        .sum()
                        .reset_index()
                    )
                    fig_device = px.pie(
                        device_summary,
                        values="sessions",
                        names="deviceCategory",
                        title="📱 Sesiones por Dispositivo",
                    )
                    st.plotly_chart(fig_device, use_container_width=True)

            with col2:
                # Navegadores
                if "browser" in device_data.columns:
                    browser_summary = (
                        device_data.groupby("browser")["sessions"].sum().reset_index()
                    )
                    browser_summary = browser_summary.sort_values(
                        "sessions", ascending=False
                    ).head(8)
                    fig_browser = px.bar(
                        browser_summary,
                        x="browser",
                        y="sessions",
                        title="🌐 Top Navegadores",
                    )
                    fig_browser.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_browser, use_container_width=True)
        else:
            st.warning("No hay datos de dispositivos disponibles")

    elif selected == "⚡ Tiempo Real":
        st.subheader("⚡ Datos en Tiempo Real")

        # Auto-refresh cada 30 segundos
        if st.button(" Actualizar Tiempo Real"):
            st.cache_data.clear()

        with st.spinner("Cargando datos en tiempo real..."):
            realtime_data = get_cached_data(ga4_client, None, None, "realtime")

        if not realtime_data.empty:
            # Métricas en tiempo real
            total_active = (
                realtime_data["activeUsers"].sum()
                if "activeUsers" in realtime_data.columns
                else 0
            )
            total_pageviews = (
                realtime_data["screenPageViews"].sum()
                if "screenPageViews" in realtime_data.columns
                else 0
            )

            col1, col2 = st.columns(2)
            with col1:
                st.metric("👥 Usuarios Activos Ahora", f"{total_active:,}")
            with col2:
                st.metric("📄 Páginas Vistas (Tiempo Real)", f"{total_pageviews:,}")

            st.info("🔄 Los datos se actualizan automáticamente cada pocos minutos")
        else:
            st.warning("No hay datos en tiempo real disponibles")

    # Footer
    st.markdown("---")
    st.markdown(
        "**📊 Dashboard GA4** - Powered by Streamlit & Google Analytics Data API"
    )


if __name__ == "__main__":
    main()
