import requests
import pandas as pd
import streamlit as st
import pytz
from datetime import datetime

# Configuración de API
API_KEY = "49b84126cfmshd16c7cb8e40fca8p1244edjsn78a3b1832e7b"
API_URL = "https://api-football-v1.p.rapidapi.com/v3/"
HEADERS = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": "api-football-v1.p.rapidapi.com"}

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
    
    # Verificar si la estructura esperada está en la respuesta
    if 'response' not in data or not data['response']:
        return []

    return data['response']

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

if not partidos:
    st.write("No hay partidos disponibles hoy.")
else:
    for partido in partidos:
        equipo_local = partido['teams']['home']['name']
        equipo_visitante = partido['teams']['away']['name']
        hora_partido = convertir_hora(partido['fixture']['date'])
        st.subheader(f"{equipo_local} vs {equipo_visitante} - 🕒 {hora_partido}")

        cuotas = obtener_cuotas(partido['fixture']['id'])

        # Verificar si la API devolvió cuotas
        if not cuotas:
            st.warning("⚠️ No se encontraron cuotas para este partido.")
            continue  # Pasar al siguiente partido sin detener la ejecución

        # Extraer solo las cuotas relevantes
        cuotas_filtradas = []
        for cuota_data in cuotas:
            if 'bookmakers' in cuota_data:
                for bookmaker in cuota_data['bookmakers']:
                    for bet in bookmaker.get('bets', []):
                        for value in bet.get('values', []):
                            if 'odd' in value:
                                cuotas_filtradas.append({
                                    "Casa": bookmaker['name'],
                                    "Mercado": bet['name'],
                                    "Cuota": float(value['odd'])
                                })

        if not cuotas_filtradas:
            st.warning("⚠️ No hay cuotas con 'odd' disponibles para este partido.")
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

        # Obtener la mejor apuesta con mayor valor esperado
        df_cuotas = df_cuotas.dropna(subset=['Valor Esperado'])  # Eliminar filas sin valor esperado

        if not df_cuotas.empty:
            mejor_apuesta = df_cuotas.loc[df_cuotas['Valor Esperado'].idxmax()]
            
            # Mostrar el pronóstico recomendado
            st.markdown(f"### 🔮 **Pronóstico Recomendado**")
            st.markdown(f"📌 **Tipo de Apuesta:** {mejor_apuesta['Mercado']}")  
            st.markdown(f"💵 **Cuota:** {mejor_apuesta['Cuota']}")  
            st.markdown(f"📈 **Valor Esperado:** {mejor_apuesta['Valor Esperado']:.2f}%")  
            st.markdown(f"⚠️ **Riesgo:** {definir_color(mejor_apuesta['Valor Esperado'])}")  

            # Mostrar tabla con cuotas filtrables
            st.write("📊 **Cuotas disponibles:**")
            st.dataframe(df_cuotas[['Casa', 'Mercado', 'Cuota', 'Valor Esperado', 'Riesgo']])

