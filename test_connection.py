import os

from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest

# Cargar variables de entorno
load_dotenv()


def test_ga4_connection():
    try:
        # Obtener configuración
        property_id = os.getenv("GA4_PROPERTY_ID")
        credentials_path = os.getenv("CREDENTIALS_PATH")

        print(f"🔍 Property ID: {property_id}")
        print(f"🔍 Credentials: {credentials_path}")

        # Crear cliente
        client = BetaAnalyticsDataClient.from_service_account_json(credentials_path)
        print("✅ Cliente GA4 creado exitosamente")

        # Hacer prueba simple
        request = RunReportRequest(
            property=f"properties/{property_id}",
            metrics=[Metric(name="activeUsers")],
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        )

        response = client.run_report(request)
        print("✅ Conexión exitosa a GA4!")

        if response.rows:
            users = response.rows[0].metric_values[0].value
            print(f"📊 Usuarios activos últimos 7 días: {users}")
        else:
            print("⚠️  No hay datos disponibles")

    except FileNotFoundError:
        print("❌ Error: No se encontró el archivo credentials.json")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    test_ga4_connection()
