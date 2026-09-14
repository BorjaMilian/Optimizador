import streamlit as st

# 1. Configuración de la página
st.set_page_config(page_title="Optimizador PLC", layout="wide")

st.title("Calculadora de Programación Lineal")
st.write("Usa el menú lateral para ajustar el tamaño de tu problema.")

# 2. Panel lateral (Sidebar)
st.sidebar.header("Parámetros del Modelo")
objetivo = st.sidebar.selectbox("Tipo de optimización", ["Maximizar", "Minimizar"])
num_vars = st.sidebar.number_input("Número de variables", min_value=2, max_value=10, value=2, step=1)
num_restricciones = st.sidebar.number_input("Número de restricciones", min_value=1, max_value=20, value=2, step=1)

st.divider()

# 3. Entradas para la Función Objetivo
st.subheader("1. Función Objetivo (Z)")
st.write("Introduce los coeficientes de cada variable para la función que quieres optimizar:")

# Creamos columnas dinámicas según el número de variables elegido
cols_obj = st.columns(num_vars)
coef_objetivo = []
for i in range(num_vars):
    with cols_obj[i]:
        # Cada caja de texto se genera automáticamente
        coef = st.number_input(f"Coeficiente de X{i+1}", value=0.0, step=1.0, key=f"obj_{i}")
        coef_objetivo.append(coef)

# 4. Entradas para las Restricciones
st.subheader("2. Restricciones")
st.write("Introduce los coeficientes, el símbolo y el valor límite para cada restricción:")

matriz_restricciones = []
simbolos_restricciones = []
limites_restricciones = []

# Creamos tantas filas como restricciones haya elegido el usuario
for i in range(num_restricciones):
    st.write(f"**Restricción {i+1}**")
    # Columnas: variables + símbolo + límite
    cols_rest = st.columns(num_vars + 2)
    
    fila_coef = []
    for j in range(num_vars):
        with cols_rest[j]:
            coef = st.number_input(f"X{j+1}", value=0.0, step=1.0, key=f"rest_{i}_x{j}")
            fila_coef.append(coef)
    
    with cols_rest[num_vars]:
        simbolo = st.selectbox("Símbolo", ["<=", ">=", "="], key=f"simbolo_{i}")
    
    with cols_rest[num_vars + 1]:
        limite = st.number_input("Límite", value=0.0, step=1.0, key=f"limite_{i}")
        
    matriz_restricciones.append(fila_coef)
    simbolos_restricciones.append(simbolo)
    limites_restricciones.append(limite)

st.divider()

# 5. Botón de Ejecución
if st.button("🚀 Resolver Modelo", type="primary"):
    st.success("¡Los datos se han leído correctamente! En el próximo paso conectaremos el motor matemático para resolverlo.")
