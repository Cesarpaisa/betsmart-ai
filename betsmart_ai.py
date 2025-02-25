import streamlit as st
import pandas as pd
import requests
import datetime
from streamlit_autorefresh import st_autorefresh  # pip install streamlit-autorefresh

# Título de la aplicación
st.title("BetSmart AI: Predicción de Apuestas Deportivas")

# Inicialización de variables en session_state
if "query_count" not in st.session_state:
    st.session_state.query_count = 0
if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.datetime.now()

# Función para simular la consulta a la API‑Football.
# En producción, reemplaza este bloque por una llamada real a la API utilizando requests.
@st.cache_data(ttl=8*3600)
def fetch_api_data():
    # Incrementa el contador de consultas cada vez que se realiza una llamada real a la API
    st.session_state.query_count += 1

    # Ejemplo de llamada real (descomentar y configurar):
    # url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    # headers = {
    #     "X-RapidAPI-Key": "49b84126cfmshd16c7cb8e40fca8p1244edjsn78a3b1832e7b",
    #     "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    # }
    # response = requests.get(url, headers=headers)
    # data = response.json()
    # return data

    # Datos simulados para 4 mercados y comparación de cuotas entre distintas casas (Bet365, William Hill, Pinnacle, Betfair Exchange)
    matches = [
        {
            "Liga": "Premier League",
            "Local": "Liverpool",
            "Visitante": "Manchester City",
            "Hora (Local)": "15:00",
            "Casa de Apuestas": "Pinnacle",
            "Mercado": "Doble Oportunidad (1X)",
            "Recomendación": "Liverpool o Empate",
            "Mejor Cuota": 1.90,
            "Valor Esperado (%)": 12,
            "Probabilidad Real (%)": 72,
            "Probabilidad de la Cuota (%)": 58,
            "Riesgo": "🟢"  # Alta probabilidad (>65%) y +EV
        },
        {
            "Liga": "La Liga",
            "Local": "Real Madrid",
            "Visitante": "Barcelona",
            "Hora (Local)": "20:00",
            "Casa de Apuestas": "Bet365",
            "Mercado": "Value Betting",
            "Recomendación": "Real Madrid",
            "Mejor Cuota": 2.00,
            "Valor Esperado (%)": 25,
            "Probabilidad Real (%)": 68,
            "Probabilidad de la Cuota (%)": 60,
            "Riesgo": "🟢"  # Alta probabilidad (>65%) y +EV
        },
        {
            "Liga": "Serie A",
            "Local": "Juventus",
            "Visitante": "Inter",
            "Hora (Local)": "18:30",
            "Casa de Apuestas": "William Hill",
            "Mercado": "Asian Handicap",
            "Recomendación": "Juventus -0.25",
            "Mejor Cuota": 1.95,
            "Valor Esperado (%)": 8,
            "Probabilidad Real (%)": 60,
            "Probabilidad de la Cuota (%)": 55,
            "Riesgo": "🟡"  # Probabilidad media (50%-65%) y riesgo moderado
        },
        {
            "Liga": "Bundesliga",
            "Local": "Bayern",
            "Visitante": "Dortmund",
            "Hora (Local)": "16:00",
            "Casa de Apuestas": "Betfair Exchange",
            "Mercado": "Over/Under (Más/Menos Goles)",
            "Recomendación": "Over 2.5",
            "Mejor Cuota": 1.85,
            "Valor Esperado (%)": -5,
            "Probabilidad Real (%)": 48,
            "Probabilidad de la Cuota (%)": 52,
            "Riesgo": "🔴"  # Probabilidad baja (<50%) y riesgo alto
        }
    ]
    return {"matches": matches}

# Configuración de refresco automático para actualizar el temporizador cada segundo
st_autorefresh(interval=1000, key="timer_refresh")

# Cálculo del tiempo restante para el reinicio de la API (caché de 8 horas)
time_elapsed = datetime.datetime.now() - st.session_state.last_update
time_reset = datetime.timedelta(hours=8)
remaining_time = time_reset - time_elapsed
if remaining_time.total_seconds() < 0:
    remaining_time = datetime.timedelta(seconds=0)

# Mostrar temporizador y contador de consultas en la barra lateral
st.sidebar.markdown("### ⏳ Tiempo restante para restablecimiento de la API:")
st.sidebar.write(str(remaining_time).split(".")[0])
st.sidebar.markdown("### 🔎 Consultas realizadas:")
st.sidebar.write(st.session_state.query_count)

# Botón de actualización manual: limpia la caché, reinicia el temporizador y refresca la página
if st.sidebar.button("Actualizar Datos"):
    st.cache_data.clear()
    st.session_state.last_update = datetime.datetime.now()
    st.experimental_rerun()

# Obtención de los datos (con caché de 8 horas)
data = fetch_api_data()

# Conversión de los datos a DataFrame para mostrar la consulta general de partidos y cuotas
st.header("Consulta en Tiempo Real de Partidos y Cuotas de Apuestas")
df_matches = pd.DataFrame(data["matches"])
st.dataframe(df_matches)

# Función auxiliar para mostrar cada mercado en una tabla filtrable
def mostrar_mercado(nombre_mercado, filtro_exacto=True):
    st.subheader(f"Mercado: {nombre_mercado}")
    if filtro_exacto:
        df_filtrado = df_matches[df_matches["Mercado"] == nombre_mercado]
    else:
        # Permite incluir variantes del nombre, por ejemplo "Doble Oportunidad (1X)" o "Doble Oportunidad (X2)"
        df_filtrado = df_matches[df_matches["Mercado"].str.contains(nombre_mercado, case=False)]
    if df_filtrado.empty:
        st.info(f"No hay datos para {nombre_mercado} (se muestran datos de ejemplo).")
    else:
        st.dataframe(df_filtrado)

# Mostrar tablas por cada uno de los 4 mercados
# 1. Value Betting
mostrar_mercado("Value Betting")
# 2. Doble Oportunidad (se busca de forma parcial para incluir variantes)
mostrar_mercado("Doble Oportunidad", filtro_exacto=False)
# 3. Asian Handicap
mostrar_mercado("Asian Handicap")
# 4. Over/Under (Más/Menos Goles)
mostrar_mercado("Over/Under (Más/Menos Goles)")

# Sistema de Alertas Automáticas: alerta si se detecta un Valor Esperado elevado (por ejemplo, >20%)
alertas = df_matches[df_matches["Valor Esperado (%)"] > 20]
if not alertas.empty:
    for index, row in alertas.iterrows():
        st.warning(
            f"📢 Alerta: Se ha detectado una apuesta con +{row['Valor Esperado (%)']}% de Valor Esperado en "
            f"{row['Liga']} ({row['Local']} vs {row['Visitante']})."
        )

# Sección explicativa para el usuario
st.markdown("---")
st.subheader("ℹ️ Cómo usar BetSmart AI")
st.markdown("""
1. **Consulta los partidos disponibles:** Se muestran los partidos del día con sus cuotas y análisis.
2. **Filtra los mercados y evalúa el riesgo:** Cada mercado tiene su propia tabla filtrable.
3. **Analiza el valor esperado de las apuestas:** Cuanto mayor el Valor Esperado (%), mayor la rentabilidad potencial.
4. **Utiliza el sistema de colores para tomar decisiones:**  
   - 🟢 **Verde:** Alta probabilidad de éxito (>65%) y valor esperado positivo (+EV).  
   - 🟡 **Amarillo:** Probabilidad media (50%-65%) y riesgo moderado.  
   - 🔴 **Rojo:** Probabilidad baja (<50%) y riesgo alto.
5. **Actualiza los datos manualmente cuando lo necesites:** Usa el botón "Actualizar Datos" en la barra lateral.
6. **Monitorea el tiempo restante para la reactivación de la API:** Se muestra en la barra lateral.
7. **Recibe alertas automáticas:** El sistema notificará cuando se detecten apuestas con alto valor esperado.
8. **Apuesta en la mejor casa de apuestas disponible:** Se comparan cuotas de Bet365, William Hill, Pinnacle y Betfair Exchange para maximizar tu ganancia.

**Recomendación:** Apuesta de forma responsable y utiliza BetSmart AI como herramienta de apoyo, no como garantía de éxito.
""")

st.subheader("🤖 Futuras Integraciones con Machine Learning")
st.markdown("""
El código está preparado para la integración de modelos de **Machine Learning** en el futuro, por ejemplo:
- Redes Neuronales para la predicción de goles esperados.
- Random Forest para evaluar patrones y detectar apuestas rentables.

Esta integración permitirá mejorar la precisión de las predicciones y, por ende, optimizar tus apuestas.
""")
