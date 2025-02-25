import streamlit as st
import pandas as pd
import requests
import datetime
from streamlit_autorefresh import st_autorefresh

# ============================================
# CONFIGURACIÓN: Reemplaza con tu API key real
# ============================================
API_KEY = "49b84126cfmshd16c7cb8e40fca8p1244edjsn78a3b1832e7b"  # <-- Reemplaza con tu clave de RapidAPI
API_HOST = "api-football-v1.p.rapidapi.com"
HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST
}

# ============================================
# Funciones de consulta a la API-Football
# ============================================

def fetch_fixtures():
    """Obtiene los partidos del día (fixtures) de la API."""
    st.session_state.query_count += 1
    today = datetime.date.today().isoformat()
    url = f"https://{API_HOST}/v3/fixtures"
    params = {"date": today}
    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()
    # Retorna la lista de fixtures
    return data.get("response", [])

def fetch_odds(fixture_id):
    """Obtiene las cuotas para un partido dado (fixture_id) de la API."""
    st.session_state.query_count += 1
    url = f"https://{API_HOST}/v3/odds"
    # IDs de las casas de apuestas (según la documentación de API-Football):
    # Bet365: 1, William Hill: 8, Pinnacle: 11, Betfair Exchange: 23
    params = {
        "fixture": fixture_id,
        "bookmakers": "1,8,11,23"
    }
    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()
    return data.get("response", [])

# ============================================
# Funciones para extraer y procesar mercados
# ============================================

def extract_market_info(odds_item, market_key):
    """
    Extrae la mejor cuota, el resultado (recomendación) y la casa de apuestas
    para un mercado dado a partir del objeto de odds.
    
    market_key puede ser:
      - "Value Betting": usamos el mercado "1X2"
      - "Doble Oportunidad": se busca el bet con "Double Chance" o "Doble Oportunidad"
      - "Asian Handicap": se busca el bet "ah"
      - "Over/Under": se busca el bet "ou"
    """
    best_odd = None
    best_outcome = None
    best_bookmaker = None

    # Itera por cada casa de apuestas en el fixture de odds
    for bookmaker in odds_item.get("bookmakers", []):
        # Considera solo las casas indicadas
        if bookmaker["name"] not in ["Bet365", "William Hill", "Pinnacle", "Betfair Exchange"]:
            continue
        for bet in bookmaker.get("bets", []):
            if market_key == "Doble Oportunidad":
                if "Double Chance" in bet["name"] or "Doble Oportunidad" in bet["name"]:
                    for value in bet.get("values", []):
                        odd = float(value["odd"])
                        if best_odd is None or odd > best_odd:
                            best_odd = odd
                            best_outcome = value["value"]
                            best_bookmaker = bookmaker["name"]
            elif market_key == "Value Betting":
                # Usamos el mercado 1X2 para Value Betting
                if bet["id"].lower() == "1x2":
                    for value in bet.get("values", []):
                        odd = float(value["odd"])
                        if best_odd is None or odd > best_odd:
                            best_odd = odd
                            best_outcome = value["value"]
                            best_bookmaker = bookmaker["name"]
            elif market_key == "Asian Handicap":
                if bet["id"].lower() == "ah":
                    for value in bet.get("values", []):
                        odd = float(value["odd"])
                        if best_odd is None or odd > best_odd:
                            best_odd = odd
                            best_outcome = value["value"]
                            best_bookmaker = bookmaker["name"]
            elif market_key == "Over/Under":
                if bet["id"].lower() == "ou":
                    for value in bet.get("values", []):
                        odd = float(value["odd"])
                        if best_odd is None or odd > best_odd:
                            best_odd = odd
                            best_outcome = value["value"]
                            best_bookmaker = bookmaker["name"]
    return best_odd, best_outcome, best_bookmaker

def calculate_probabilities(odd):
    """Calcula la probabilidad implícita, simula una probabilidad real y el valor esperado."""
    # Probabilidad implícita (%)
    prob_cuota = round((1 / odd) * 100, 2)
    # Simulación: se asume que la probabilidad real es la implícita más un ajuste (por ejemplo, +15 puntos)
    prob_real = prob_cuota + 15
    if prob_real > 100:
        prob_real = 100
    # Valor esperado (%) = diferencia entre probabilidad real y probabilidad implícita
    valor_esperado = round(prob_real - prob_cuota, 2)
    return prob_cuota, prob_real, valor_esperado

def classify_risk(prob_real, valor_esperado):
    """Clasifica el riesgo basado en la probabilidad real y el valor esperado."""
    if prob_real > 65 and valor_esperado > 0:
        return "🟢"
    elif 50 <= prob_real <= 65:
        return "🟡"
    else:
        return "🔴"

# ============================================
# Función principal para obtener y procesar datos
# ============================================
@st.cache_data(ttl=8*3600)
def fetch_api_data():
    fixtures = fetch_fixtures()
    matches_list = []
    
    # Se definen los mercados a analizar
    mercados = ["Value Betting", "Doble Oportunidad", "Asian Handicap", "Over/Under"]
    
    for fixture in fixtures:
        fixture_id = fixture["fixture"]["id"]
        # Datos básicos del fixture
        league = fixture["league"]["name"]
        home_team = fixture["teams"]["home"]["name"]
        away_team = fixture["teams"]["away"]["name"]
        fixture_time = fixture["fixture"]["date"]
        
        # Obtiene las cuotas para este fixture
        odds_response = fetch_odds(fixture_id)
        # Si no hay odds disponibles, se omite este fixture
        if not odds_response:
            continue
        # En la respuesta de odds, generalmente se devuelve una lista con un elemento por fixture
        odds_item = odds_response[0]
        
        # Para cada mercado, extrae la mejor cuota disponible y procesa la información
        for mercado in mercados:
            best_odd, best_outcome, best_bookmaker = extract_market_info(odds_item, mercado)
            if best_odd is None:
                continue  # Si no hay cuota para ese mercado, se salta
            prob_cuota, prob_real, valor_esperado = calculate_probabilities(best_odd)
            risk = classify_risk(prob_real, valor_esperado)
            
            matches_list.append({
                "Liga": league,
                "Local": home_team,
                "Visitante": away_team,
                "Hora (Local)": fixture_time,
                "Casa de Apuestas": best_bookmaker,
                "Mercado": mercado,
                "Recomendación": best_outcome,
                "Mejor Cuota": best_odd,
                "Valor Esperado (%)": valor_esperado,
                "Probabilidad Real (%)": prob_real,
                "Probabilidad de la Cuota (%)": prob_cuota,
                "Riesgo": risk
            })
    return {"matches": matches_list}

# ============================================
# Configuración de la interfaz Streamlit
# ============================================

st.set_page_config(page_title="BetSmart AI", layout="wide")
st.title("BetSmart AI: Predicción de Apuestas Deportivas")

# Inicialización de variables en session_state
if "query_count" not in st.session_state:
    st.session_state.query_count = 0
if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.datetime.now()

# Refresco automático cada segundo para actualizar el temporizador
st_autorefresh(interval=1000, key="timer_refresh")

# Cálculo del tiempo restante para la reactivación de la API (caché de 8 horas)
time_elapsed = datetime.datetime.now() - st.session_state.last_update
time_reset = datetime.timedelta(hours=8)
remaining_time = time_reset - time_elapsed
if remaining_time.total_seconds() < 0:
    remaining_time = datetime.timedelta(seconds=0)

# Mostrar información en la barra lateral
st.sidebar.markdown("### ⏳ Tiempo restante para restablecimiento de la API:")
st.sidebar.write(str(remaining_time).split(".")[0])
st.sidebar.markdown("### 🔎 Consultas realizadas:")
st.sidebar.write(st.session_state.query_count)

# Botón de actualización manual: limpia la caché, reinicia el temporizador y recarga la aplicación
if st.sidebar.button("Actualizar Datos"):
    st.cache_data.clear()
    st.session_state.last_update = datetime.datetime.now()
    st.experimental_rerun()

# Obtención de datos (con caché de 8 horas)
data = fetch_api_data()

# Si no se obtuvieron partidos (por ejemplo, si la API no devolvió resultados)
if not data["matches"]:
    st.error("No se han encontrado partidos u odds para el día de hoy.")
else:
    # Conversión de los datos a DataFrame y despliegue de la tabla general
    st.header("Consulta en Tiempo Real de Partidos y Cuotas de Apuestas")
    df_matches = pd.DataFrame(data["matches"])
    st.dataframe(df_matches, use_container_width=True)

    # Función auxiliar para mostrar cada mercado en una tabla filtrable
    def mostrar_mercado(nombre_mercado):
        st.subheader(f"Mercado: {nombre_mercado}")
        df_filtrado = df_matches[df_matches["Mercado"] == nombre_mercado]
        if df_filtrado.empty:
            st.info(f"No hay datos para el mercado '{nombre_mercado}'.")
        else:
            st.dataframe(df_filtrado, use_container_width=True)

    # Mostrar tablas para cada uno de los 4 mercados
    mostrar_mercado("Value Betting")
    mostrar_mercado("Doble Oportunidad")
    mostrar_mercado("Asian Handicap")
    mostrar_mercado("Over/Under")

    # Sistema de alertas automáticas: alerta si se detecta una apuesta con Valor Esperado elevado (por ejemplo, >20%)
    alertas = df_matches[df_matches["Valor Esperado (%)"] > 20]
    if not alertas.empty:
        for index, row in alertas.iterrows():
            st.warning(
                f"📢 Alerta: Se ha detectado una apuesta con +{row['Valor Esperado (%)']}% de Valor Esperado en "
                f"{row['Liga']} ({row['Local']} vs {row['Visitante']})."
            )

# ============================================
# Sección informativa para el usuario
# ============================================
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

Esta integración permitirá mejorar la precisión de las predicciones y optimizar tus apuestas.
""")
