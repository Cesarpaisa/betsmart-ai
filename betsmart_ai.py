import streamlit as st
import requests
import time
import pandas as pd
import datetime
from datetime import timedelta
import pytz
import json

# Configuración de API
API_KEY = "49b84126cfmshd16c7cb8e40fca8p1244edjsn78a3b1832e7b"
API_URL = "https://api-football-v1.p.rapidapi.com/v3/"
HEADERS = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": "api-football-v1.p.rapidapi.com"}

# Función para obtener el tiempo restante hasta la reactivación de la API
def obtener_tiempo_restante():
    ahora = datetime.datetime.utcnow()
    reinicio_diario = datetime.datetime.combine(ahora.date(), datetime.time(0, 0)) + timedelta(days=1)
    tiempo_restante = reinicio_diario - ahora
    return tiempo_restante

# Función para obtener partidos
@st.cache_data(ttl=28800)  # Caché con tiempo de expiración de 8 horas
def obtener_partidos():
    url = API_URL + "fixtures"
    params = {"date": datetime.datetime.utcnow().strftime('%Y-%m-%d')}
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()['response']
    return None

# Función para obtener cuotas
@st.cache_data(ttl=28800)
def obtener_cuotas(partido_id):
    url = API_URL + "odds"
    params = {"fixture": partido_id, "bookmaker": 1}  # Bet365
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()['response']
    return None

# Función para convertir hora a zona local
def convertir_hora(hora_utc, zona_usuario='America/Bogota'):
    utc_time = datetime.datetime.strptime(hora_utc, "%Y-%m-%dT%H:%M:%S%z")
    local_tz = pytz.timezone(zona_usuario)
    return utc_time.astimezone(local_tz).strftime('%H:%M %p')

# Interfaz Streamlit
st.title("⚽ BetSmart AI - Predicción de Apuestas Deportivas")

# Temporizador para reinicio de API
tiempo_restante = obtener_tiempo_restante()
st.sidebar.write(f"⏳ Tiempo restante para restablecimiento de API: {str(tiempo_restante).split('.')[0]}")

# Botón de actualización
if st.sidebar.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.experimental_rerun()

# Obtener partidos
partidos = obtener_partidos()
if not partidos:
    st.error("⚠️ No hay partidos disponibles hoy o la API ha alcanzado su límite de consultas.")
else:
    for partido in partidos:
        equipo_local = partido['teams']['home']['name']
        equipo_visitante = partido['teams']['away']['name']
        liga = partido['league']['name']
        hora_partido = convertir_hora(partido['fixture']['date'])
        
        st.subheader(f"{equipo_local} vs {equipo_visitante} - 🏆 {liga} - 🕒 {hora_partido}")
        
        cuotas = obtener_cuotas(partido['fixture']['id'])
        if cuotas:
            df_cuotas = pd.DataFrame(cuotas)
            st.dataframe(df_cuotas)
        else:
            st.warning(f"⚠️ No se encontraron cuotas para {equipo_local} vs {equipo_visitante}.")

# Información sobre cómo usar la herramienta
st.markdown("""
## ℹ️ Cómo usar BetSmart AI
1. **Consulta los partidos disponibles**: Se muestran los partidos del día con sus respectivas cuotas.
2. **Filtros y recomendaciones**: Puedes filtrar mercados y ver la mejor cuota recomendada.
3. **Actualizar Datos**: Si deseas obtener la última información, presiona el botón de actualización en la barra lateral.
4. **Tiempo restante**: El tiempo restante para la próxima actualización automática está indicado en la barra lateral.
5. **Advertencias**: Si la API alcanza su límite diario de consultas, se mostrará un mensaje de alerta.

📌 *Usa la información con precaución y gestiona bien tu bankroll al apostar.*
""")
