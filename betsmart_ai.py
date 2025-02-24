import requests
import pandas as pd
import numpy as np
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
    data = response.json()
    return data['response']

# Obtener cuotas de apuestas
def obtener_cuotas(partido_id):
    url = API_URL + "odds"
    params = {"fixture": partido_id, "bookmaker": 1}  # Bet365
    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()
    return data['response']

# Calcular valor esperado de una apuesta
def calcular_valor_esperado(probabilidad_real, cuota):
    probabilidad_casa = 1 / cuota
    return (probabilidad_real - probabilidad_casa) * 100

# Convertir la hora del partido a la zona horaria local
def convertir_hora(hora_utc, zona_usuario='America/Bogota'):
    utc_time = datetime.strptime(hora_utc, "%Y-%m-%dT%H:%M:%S%z")
    local_tz = pytz.timezone(zona_usuario)
    return utc_time.astimezone(local_tz).strftime('%H:%M %p')

# Interfaz en Streamlit
st.title("⚽ BetSmart AI - Predicción de Apuestas Deportivas")
st.sidebar.header("📅 Configuración")

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
        if cuotas:
            # Verificar si la API devolvió cuotas
if not cuotas:
    st.error("⚠️ No se encontraron cuotas para este partido.")
    st.stop()  # Detiene la ejecución del programa

# Verificar si 'odd' está presente en los datos
if isinstance(cuotas, list) and len(cuotas) > 0:
    if 'odd' not in cuotas[0]:
        st.error("⚠️ Error: La clave 'odd' no está en los datos de cuotas.")
        st.write("📌 Datos devueltos por la API:", cuotas)  # Mostrar los datos para ver qué trae la API
        st.stop()
else:
    st.error("⚠️ No se recibieron datos de cuotas en el formato esperado.")
    st.stop()

# Obtener la mejor cuota si los datos son válidos
# Obtener la mejor cuota si los datos son válidos
mejor_cuota = max(cuotas, key=lambda x: x['odd'])
            valor_esperado = calcular_valor_esperado(0.60, float(mejor_cuota['odd']))
            color = "green" if valor_esperado > 5 else "yellow" if valor_esperado > 0 else "red"
            st.markdown(f"**📊 Cuota: {mejor_cuota['odd']} - Valor Esperado: {valor_esperado:.2f}%**", unsafe_allow_html=True)
            st.markdown(f"<span style='color:{color}'>⚠️ Riesgo: {'Bajo' if color=='green' else 'Moderado' if color=='yellow' else 'Alto'}</span>", unsafe_allow_html=True)
        else:
            st.write("No se encontraron cuotas para este partido.")

# Simulador de Bankroll
st.sidebar.subheader("💰 Calculadora de Bankroll")
capital_inicial = st.sidebar.number_input("Capital Inicial ($):", value=1000)
ganancias = st.sidebar.number_input("Ganancias Totales ($):", value=0)
perdidas = st.sidebar.number_input("Pérdidas Totales ($):", value=0)
capital_final = capital_inicial + ganancias - perdidas
st.sidebar.write(f"**📈 Estado Financiero: ${capital_final}**")
