import requests
import pandas as pd
import streamlit as st
import pytz
from datetime import datetime

# Configuración de API
API_KEY = "49b84126cfmshd16c7cb8e40fca8p1244edjsn78a3b1832e7b"
API_URL = "https://api-football-v1.p.rapidapi.com/v3/"
HEADERS = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": "api-football-v1.p.rapidapi.com"}

# Traducción de los mercados de apuestas al español
TRADUCCION_MERCADOS = {
    "Match Winner": "Ganador del Partido",
    "Over/Under Goals": "Más/Menos Goles",
    "Both Teams to Score": "Ambos Equipos Marcan",
    "Handicap": "Hándicap",
}

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
        st.error(f"⚠️ Error en la API de cuotas: {response.json()}")
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
tablas_mercados = {}

if not partidos:
    st.write("No hay partidos disponibles hoy.")
else:
    for partido in partidos:
        equipo_local = partido['teams']['home']['name']
        equipo_visitante = partido['teams']['away']['name']
        liga = partido['league']['name']
        hora_partido = convertir_hora(partido['fixture']['date'])
        
        cuotas = obtener_cuotas(partido['fixture']['id'])

        # Verificar si la API devolvió cuotas
        if not cuotas:
            st.warning(f"⚠️ No se encontraron cuotas para {equipo_local} vs {equipo_visitante}.")
            continue

        # Extraer solo las cuotas relevantes
        cuotas_filtradas = []
        for cuota_data in cuotas:
            if 'bookmakers' in cuota_data:
                for bookmaker in cuota_data['bookmakers']:
                    for bet in bookmaker.get('bets', []):
                        mercado = bet['name']
                        mercado_esp = TRADUCCION_MERCADOS.get(mercado, mercado)  # Traducción al español

                        for value in bet.get('values', []):
                            if 'odd' in value:
                                cuotas_filtradas.append({
                                    "Liga": liga,
                                    "Equipo Local": equipo_local,
                                    "Equipo Visitante": equipo_visitante,
                                    "Hora Local": hora_partido,
                                    "Casa de Apuestas": bookmaker['name'],
                                    "Mercado": mercado_esp,
                                    "Apuesta Recomendada": value['value'],  # Nombre de la apuesta específica
                                    "Cuota": float(value['odd'])
                                })

        if not cuotas_filtradas:
            st.warning(f"⚠️ No hay cuotas válidas para {equipo_local} vs {equipo_visitante}.")
            continue

        # Crear DataFrame con cuotas organizadas
        df_cuotas = pd.DataFrame(cuotas_filtradas)

        # Calcular valor esperado y riesgo
        df_cuotas['Valor Esperado'] = df_cuotas['Cuota'].apply(lambda x: calcular_valor_esperado(0.60, x))

        # Definir color según el valor esperado
        def definir_color(valor):
            if valor is None:
                return '🔘 Indeterminado'
            elif valor > 5:
                return '🟢 Bajo'
            elif valor > 0:
                return '🟡 Moderado'
            else:
                return '🔴 Alto'

        df_cuotas['Riesgo'] = df_cuotas['Valor Esperado'].apply(definir_color)

        # Guardar en el diccionario de tablas por mercado
        for mercado in df_cuotas['Mercado'].unique():
            df_filtrado = df_cuotas[df_cuotas['Mercado'] == mercado]
            if mercado not in tablas_mercados:
                tablas_mercados[mercado] = df_filtrado
            else:
                tablas_mercados[mercado] = pd.concat([tablas_mercados[mercado], df_filtrado])

# Mostrar cada tabla por mercado
for mercado, tabla in tablas_mercados.items():
    st.markdown(f"## 📊 Tabla de Apuestas: {mercado}")
    st.dataframe(tabla[['Liga', 'Equipo Local', 'Equipo Visitante', 'Hora Local', 'Casa de Apuestas', 'Mercado', 'Apuesta Recomendada', 'Cuota', 'Valor Esperado', 'Riesgo']])
