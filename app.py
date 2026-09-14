import streamlit as st

# 1. Configuración de la página
st.set_page_config(page_title="Optimizador PLC", layout="wide")

st.title("Calculadora de Programación Lineal")
st.write("Usa el menú lateral para ajustar el tamaño de tu problema.")

# 2. Panel lateral (Sidebar)
st.sidebar.header("Parámetros del Modelo")

objetivo = st.sidebar.selectbox("Tipo de optimización", ["Maximizar", "Minimizar"])

# Controles para el número de variables y restricciones
num_vars = st.sidebar.number_input("Número de variables", min_value=2, max_value=10, value=2, step=1)
num_restricciones = st.sidebar.number_input("Número de restricciones", min_value=1, max_value=20, value=2, step=1)

# 3. Mostrar resumen en la pantalla principal
st.divider()
st.subheader("Resumen de tu modelo")
st.info(f"Vamos a **{objetivo.lower()}** una función con **{num_vars} variables** sujeta a **{num_restricciones} restricciones**.")
