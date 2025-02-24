import requests
import pandas as pd
import streamlit as st
import pytz
from datetime import datetime

# Configuración de la API
API_KEY = "TU_CLAVE_DE_API"
API_URL = "https://api-football-v1.p.rapidapi.com/v3/"
HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}

# Traducción de los mercados de apuestas al español
TRADUCCION_MERCADOS = {
    "Match Winner": "Ganador del Partido",
    "Over/Under Goals": "Más/Menos Goles",
    "Both Teams to Score": "Ambos Equipos Marcan",
    "Handicap": "Hándicap",
}

# Lista de mercados a evaluar
MERCADOS_A_EVALUAR = ["Match Winner", "Over/Under Goals", "Both Teams to Score", "Handicap"]

# Obtener partidos del día
def obtener_partidos():
    url = API_URL + "fixtures"
    params = {"date": datetime.now().strftime('%Y-%m-%d')}
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code != 200:
        st.error(f"⚠️ Error en la API de partidos: {response.json()}")
        return []
    data = response.json()
    return data.get('response', [])

# Obtener cuotas de apuestas
def obtener_cuotas(partido_id):
    url = API_URL + "odds"
    params = {"fixture": partido_id, "bookmaker": 1}  # Bet365
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code != 200:
        return []
    data = response.json()
    return data.get('response', [])

# Calcular valor esperado de una apuesta
def calcular_valor_esperado(probabilidad_real, cuota):
    try:
        probabilidad_casa = 1 / float(cuota)
        return (probabilidad_real - probabilidad_casa) * 100
    except (ValueError, ZeroDivisionError):
        return None

# Convertir la hora del partido a la zona horaria local
def convertir_hora(hora_utc, zona_usuario='America/Bogota'):
    utc_time = datetime.strptime(hora_utc, "%Y-%m-%dT%H:%M:%S%z")
    local_tz = pytz.timezone(zona_usuario)
    return utc_time.astimezone(local_tz).strftime('%H:%M %p')

# Interfaz en Streamlit
st.title("⚽ BetSmart AI - Predicción de Apuestas Deportivas")

# Obtener partidos
partidos = obtener_partidos()

# Diccionario para almacenar tablas de mercados
tablas_mercados = {mercado: [] for mercado in MERCADOS_A_EVALUAR}

if not partidos:
    st.write("No hay partidos disponibles hoy.")
else:
    for partido in partidos:
        equipo_local = partido['teams']['home']['name']
        equipo_visitante = partido['teams']['away']['name']
        liga = partido['league']['name']
        hora_partido = convertir_hora(partido['fixture']['date'])
        
        cuotas = obtener_cuotas(partido['fixture']['id'])

        # Procesar cada mercado
        for mercado in MERCADOS_A_EVALUAR:
            mercado_esp = TRADUCCION_MERCADOS.get(mercado, mercado)  # Traducción al español
            cuota_encontrada = False

            if cuotas:
                for cuota_data in cuotas:
                    if 'bookmakers' in cuota_data:
                        for bookmaker in cuota_data['bookmakers']:
                            for bet in bookmaker.get('bets', []):
                                if bet['name'] == mercado:
                                    for value in bet.get('values', []):
                                        if 'odd' in value and 'value' in value:
                                            cuota_encontrada = True
                                            valor_esperado = calcular_valor_esperado(0.50, float(value['odd']))  # Suponiendo una probabilidad real del 50%
                                            tablas_mercados[mercado].append({
                                                "Liga": liga,
                                                "Equipo Local": equipo_local,
                                                "Equipo Visitante": equipo_visitante,
                                                "Hora Local": hora_partido,
                                                "Casa de Apuestas": bookmaker['name'],
                                                "Mercado": mercado_esp,
                                                "Apuesta Recomendada": value['value'],
                                                "Cuota": float(value['odd']),
                                                "Valor Esperado": valor_esperado,
                                                "Riesgo": definir_riesgo(valor_esperado)
                                            })

            # Si no se encontró cuota para el mercado, agregar un pronóstico por defecto
            if not cuota_encontrada:
                tablas_mercados[mercado].append({
                    "Liga": liga,
                    "Equipo Local": equipo_local,
                    "Equipo Visitante": equipo_visitante,
                    "Hora Local": hora_partido,
                    "Casa de Apuestas": "N/A",
                    "Mercado": mercado_esp,
                    "Apuesta Recomendada": "Sin datos",
                    "Cuota": None,
                    "Valor Esperado": None,
                    "Riesgo": "Indeterminado"
                })

# Función para definir el riesgo basado en el valor esperado
def definir_riesgo(valor):
    if valor is None:
        return '🔘 Indeterminado'
    elif valor > 5:
        return '🟢 Bajo'
    elif valor > 0:
        return '🟡 Moderado'
    else:
        return '🔴 Alto'

# Mostrar cada tabla por mercado
for mercado, datos in tablas_mercados.items():
    if datos:
        df = pd.DataFrame(datos)
        st.markdown(f"## 📊 Tabla de Apuestas: {TRADUCCION_MERCADOS.get(mercado, mercado)}")
        st.dataframe(df[['Liga', 'Equipo Local', 'Equipo Visitante', 'Hora Local', 'Casa de Apuestas', 'Apuesta Recomendada', 'Cuota', 'Valor Esperado', 'Riesgo']])
    else:
        st.markdown(f"## 📊 Tabla de Apuestas: {TRADUCCION_MERCADOS.get(mercado, mercado)}")
        st.write("No hay datos disponibles para este mercado.")
