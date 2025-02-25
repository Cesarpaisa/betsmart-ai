import streamlit as st
import requests
import datetime
import pandas as pd
import pytz
from datetime import timedelta

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
        return response.json().get('response', [])
    return []

# Función para obtener cuotas
@st.cache_data(ttl=28800)
def obtener_cuotas(partido_id):
    url = API_URL + "odds"
    params = {"fixture": partido_id, "bookmaker": 1}  # Bet365
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json().get('response', [])
    return []

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
    mercados = {"Ganador del Partido": [], "Más/Menos Goles": [], "Ambos Equipos Marcan": []}
    
    for partido in partidos:
        equipo_local = partido['teams']['home']['name']
        equipo_visitante = partido['teams']['away']['name']
        liga = partido['league']['name']
        hora_partido = convertir_hora(partido['fixture']['date'])
        partido_id = partido['fixture']['id']
        
        cuotas = obtener_cuotas(partido_id)
        if cuotas:
            for cuota in cuotas:
                mercado = cuota.get('market', '')
                odd = cuota.get('odd', None)
                
                if mercado and odd:
                    if "Match Winner" in mercado:
                        mercados["Ganador del Partido"].append([liga, equipo_local, equipo_visitante, hora_partido, mercado, odd])
                    elif "Over/Under" in mercado:
                        mercados["Más/Menos Goles"].append([liga, equipo_local, equipo_visitante, hora_partido, mercado, odd])
                    elif "Both Teams to Score" in mercado:
                        mercados["Ambos Equipos Marcan"].append([liga, equipo_local, equipo_visitante, hora_partido, mercado, odd])
    
    for mercado, datos in mercados.items():
        st.subheader(f"📊 Tabla de Apuestas: {mercado}")
        if datos:
            df = pd.DataFrame(datos, columns=["Liga", "Local", "Visitante", "Hora", "Mercado", "Cuota"])
            st.dataframe(df)
        else:
            st.warning(f"No hay datos disponibles para este mercado.")

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
