import streamlit as st
import pulp
import pandas as pd

st.set_page_config(page_title="Optimizador PLC", layout="wide")

st.title("Calculadora de Programación Lineal")
st.write("Usa el menú lateral para ajustar el tamaño de tu problema.")

st.sidebar.header("Parámetros del Modelo")
objetivo = st.sidebar.selectbox("Tipo de optimización", ["Maximizar", "Minimizar"])
num_vars = st.sidebar.number_input("Número de variables", min_value=2, max_value=10, value=2, step=1)
num_restricciones = st.sidebar.number_input("Número de restricciones", min_value=1, max_value=20, value=2, step=1)

st.divider()

st.subheader("1. Función Objetivo (Z)")
cols_obj = st.columns(num_vars)
coef_objetivo = []
for i in range(num_vars):
    with cols_obj[i]:
        coef = st.number_input(f"Coeficiente X{i+1}", value=0.0, step=1.0, key=f"obj_{i}")
        coef_objetivo.append(coef)

st.subheader("2. Restricciones")
matriz_restricciones = []
simbolos_restricciones = []
limites_restricciones = []

for i in range(num_restricciones):
    st.write(f"**Restricción {i+1}**")
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

if st.button("🚀 Resolver Modelo", type="primary"):
    # 1. Crear el problema
    sentido = pulp.LpMaximize if objetivo == "Maximizar" else pulp.LpMinimize
    prob = pulp.LpProblem("Problema_PLC", sentido)

    # 2. Crear variables continuas (X >= 0)
    variables = [pulp.LpVariable(f"X{i+1}", lowBound=0, cat='Continuous') for i in range(num_vars)]

    # 3. Añadir función objetivo
    prob += pulp.lpSum([coef_objetivo[i] * variables[i] for i in range(num_vars)]), "Z"

    # 4. Añadir restricciones
    for i in range(num_restricciones):
        expr = pulp.lpSum([matriz_restricciones[i][j] * variables[j] for j in range(num_vars)])
        if simbolos_restricciones[i] == "<=":
            prob += (expr <= limites_restricciones[i], f"Restriccion_{i+1}")
        elif simbolos_restricciones[i] == ">=":
            prob += (expr >= limites_restricciones[i], f"Restriccion_{i+1}")
        else:
            prob += (expr == limites_restricciones[i], f"Restriccion_{i+1}")

    # 5. Resolver el modelo
    prob.solve()

    # 6. Mostrar Resultados
    st.subheader("3. Resultados")
    estado = pulp.LpStatus[prob.status]
    
    if estado == "Optimal":
        st.success("¡Solución Óptima encontrada!")
        st.metric(label="Valor de la Función Objetivo (Z)", value=round(pulp.value(prob.objective), 4))
        
        # Tabla de variables
        st.write("**Variables de Decisión:**")
        var_data = [{"Variable": v.name, "Valor": round(v.varValue, 4)} for v in prob.variables()]
        st.table(pd.DataFrame(var_data))
        
        # Tabla de saturación (Precios sombra y holgura)
        st.write("**Análisis de Saturación:**")
        rest_data = []
        for name, c in prob.constraints.items():
            holgura = round(c.slack, 4)
            saturada = "Sí" if holgura == 0 else "No"
            rest_data.append({"Restricción": name, "Saturada": saturada, "Holgura/Exceso": abs(holgura), "Precio Sombra": round(c.pi, 4)})
        st.table(pd.DataFrame(rest_data))
    else:
        st.error(f"El modelo no tiene una solución óptima válida. Estado: {estado}")
