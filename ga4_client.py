import os

import pandas as pd
import streamlit as st
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunRealtimeReportRequest,
    RunReportRequest,
)


class GA4Client:
    def __init__(self, property_id: str, credentials_path: str):
        self.property_id = property_id

        try:
            # 1. Lógica para Cloud (st.secrets)
            if "ga4" in st.secrets:
                st.info("Usando credenciales seguras de Streamlit Secrets (Producción)")

                # SOLUCIÓN: Convertir el objeto AttrDict de Streamlit a un diccionario estándar de Python.
                # El método from_dict() o .to_dict() o simplemente usar dict() en el objeto lo resuelve.
                creds_dict = dict(st.secrets["ga4"])

                # Usar from_service_account_info que acepta un diccionario estándar
                self.client = BetaAnalyticsDataClient.from_service_account_info(
                    creds_dict
                )

            # 2. Lógica para Desarrollo Local (ruta de archivo)
            elif os.path.exists(credentials_path):
                st.warning(
                    f"Usando ruta de archivo local: {credentials_path} (Desarrollo)"
                )
                self.client = BetaAnalyticsDataClient.from_service_account_json(
                    credentials_path
                )
            else:
                st.error("❌ ERROR: No se encontraron credenciales válidas.")
                st.stop()

        except Exception as e:
            st.error(f"Error al conectar con GA4: {type(e).__name__} - {str(e)}")
            st.stop()

    def get_basic_report(
        self,
        start_date: str,
        end_date: str,
        metrics: list,
        dimensions: list = None,
        limit: int = 100,
    ):
        """Obtiene reporte básico de GA4"""
        try:
            # Construir métricas
            metric_objects = [Metric(name=metric) for metric in metrics]

            # Construir dimensiones
            dimension_objects = []
            if dimensions:
                dimension_objects = [Dimension(name=dim) for dim in dimensions]

            # Crear request
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=dimension_objects,
                metrics=metric_objects,
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                limit=limit,
            )

            # Ejecutar request
            response = self.client.run_report(request)
            return self._response_to_dataframe(response)

        except Exception as e:
            st.error(f"Error al obtener datos: {str(e)}")
            return pd.DataFrame()

    def get_realtime_report(
        self, metrics: list, dimensions: list = None, limit: int = 50
    ):
        """Obtiene datos en tiempo real"""
        try:
            metric_objects = [Metric(name=metric) for metric in metrics]
            dimension_objects = []
            if dimensions:
                dimension_objects = [Dimension(name=dim) for dim in dimensions]

            request = RunRealtimeReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=dimension_objects,
                metrics=metric_objects,
                limit=limit,
            )

            response = self.client.run_realtime_report(request)
            return self._response_to_dataframe(response, realtime=True)

        except Exception as e:
            st.error(f"Error al obtener datos en tiempo real: {str(e)}")
            return pd.DataFrame()

    def get_top_pages(self, start_date: str, end_date: str, limit: int = 10):
        """Obtiene las páginas más visitadas"""
        return self.get_basic_report(
            start_date=start_date,
            end_date=end_date,
            metrics=["screenPageViews", "sessions", "totalUsers"],
            dimensions=["pagePath", "pageTitle"],
            limit=limit,
        )

    def get_traffic_sources(self, start_date: str, end_date: str, limit: int = 10):
        """Obtiene fuentes de tráfico"""
        return self.get_basic_report(
            start_date=start_date,
            end_date=end_date,
            metrics=["sessions", "totalUsers", "conversions"],
            dimensions=["sessionDefaultChannelGroup"],
            limit=limit,
        )

    def get_geographic_data(self, start_date: str, end_date: str, limit: int = 20):
        """Obtiene datos geográficos"""
        return self.get_basic_report(
            start_date=start_date,
            end_date=end_date,
            metrics=["sessions", "totalUsers", "screenPageViews"],
            dimensions=["country", "city"],
            limit=limit,
        )

    def get_device_data(self, start_date: str, end_date: str):
        """Obtiene datos de dispositivos"""
        return self.get_basic_report(
            start_date=start_date,
            end_date=end_date,
            metrics=["sessions", "totalUsers", "screenPageViews"],
            dimensions=["deviceCategory", "browser", "operatingSystem"],
            limit=50,
        )

    def _response_to_dataframe(self, response, realtime=False):
        """Convierte respuesta GA4 a DataFrame"""
        if not hasattr(response, "rows") or not response.rows:
            return pd.DataFrame()

        data = []

        for row in response.rows:
            row_data = {}

            # Procesar dimensiones
            if hasattr(response, "dimension_headers"):
                for i, dimension in enumerate(response.dimension_headers):
                    row_data[dimension.name] = row.dimension_values[i].value

            # Procesar métricas
            metric_headers = (
                response.metric_headers if hasattr(response, "metric_headers") else []
            )
            for i, metric in enumerate(metric_headers):
                value = row.metric_values[i].value
                try:
                    # Convertir a número si es posible
                    row_data[metric.name] = float(value) if "." in value else int(value)
                except (ValueError, TypeError):
                    row_data[metric.name] = value

            data.append(row_data)

        df = pd.DataFrame(data)

        # Procesar columna de fecha si existe
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")

        return df
