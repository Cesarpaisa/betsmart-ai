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
    except ValueError:
        return None

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
        
        # Verificar si la API devolvió cuotas
        if not cuotas:
            st.error("⚠️ No se encontraron cuotas para este partido.")
            continue  # Pasar al siguiente partido sin detener la ejecución

        # Filtrar solo las cuotas que contienen la clave 'odd'
        cuotas_filtradas = [c for c in cuotas if 'odd' in c]

        # Verificar que haya cuotas válidas
        if not cuotas_filtradas:
            st.error("⚠️ No se encontraron cuotas válidas con 'odd'.")
            st.write("📌 Datos de cuotas recibidos:", cuotas)
            continue  # Pasar al siguiente partido sin detener la ejecución

        # Obtener la mejor cuota
        mejor_cuota = max(cuotas_filtradas, key=lambda x: x['odd'])

        # Calcular el valor esperado
        valor_esperado = calcular_valor_esperado(0.60, mejor_cuota['odd'])
        
        if valor_esperado is None:
            st.error("⚠️ Error al calcular el valor esperado: Cuota inválida.")
            continue  # Pasar al siguiente partido

        # Determinar el color de la apuesta según el valor esperado
        color = "green" if valor_esperado > 5 else "yellow" if valor_esperado > 0 else "red"

        # Mostrar resultados en Streamlit
        st.markdown(f"**📊 Cuota: {mejor_cuota['odd']} - Valor Esperado: {valor_esperado:.2f}%**", unsafe_allow_html=True)
        st.markdown(f"<span style='color:{color}'>⚠️ Riesgo: {'Bajo' if color=='green' else 'Moderado' if color=='yellow' else 'Alto'}</span>", unsafe_allow_html=True)

# Simulador de Bankroll
st.sidebar.subheader("💰 Calculadora de Bankroll")
capital_inicial = st.sidebar.number_input("Capital Inicial ($):", value=1000)
ganancias = st.sidebar.number_input("Ganancias Totales ($):", value=0)
perdidas = st.sidebar.number_input("Pérdidas Totales ($):", value=0)
capital_final = capital_inicial + ganancias - perdidas
st.sidebar.write(f"**📈 Estado Financiero: ${capital_final}**")
