import streamlit as st
import pulp
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import itertools
from scipy.spatial import ConvexHull

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
    sentido = pulp.LpMaximize if objetivo == "Maximizar" else pulp.LpMinimize
    prob = pulp.LpProblem("Problema_PLC", sentido)
    variables = [pulp.LpVariable(f"X{i+1}", lowBound=0, cat='Continuous') for i in range(num_vars)]
    prob += pulp.lpSum([coef_objetivo[i] * variables[i] for i in range(num_vars)]), "Z"

    for i in range(num_restricciones):
        expr = pulp.lpSum([matriz_restricciones[i][j] * variables[j] for j in range(num_vars)])
        if simbolos_restricciones[i] == "<=":
            prob += (expr <= limites_restricciones[i], f"Restriccion_{i+1}")
        elif simbolos_restricciones[i] == ">=":
            prob += (expr >= limites_restricciones[i], f"Restriccion_{i+1}")
        else:
            prob += (expr == limites_restricciones[i], f"Restriccion_{i+1}")

    prob.solve()
    estado = pulp.LpStatus[prob.status]
    
    if estado == "Optimal":
        st.success("¡Solución Óptima encontrada!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Valor de la Función Objetivo (Z)", value=round(pulp.value(prob.objective), 4))
            st.write("**Variables de Decisión:**")
            var_data = [{"Variable": v.name, "Valor": round(v.varValue, 4)} for v in prob.variables()]
            st.table(pd.DataFrame(var_data))
            
        with col2:
            st.write("**Análisis de Saturación:**")
            rest_data = []
            for name, c in prob.constraints.items():
                holgura = round(c.slack, 4)
                saturada = "Sí" if holgura == 0 else "No"
                rest_data.append({"Restricción": name, "Saturada": saturada, "Holgura/Exceso": abs(holgura), "Precio Sombra": round(c.pi, 4)})
            st.table(pd.DataFrame(rest_data))
            
        # Generar gráfica solo si hay 2 variables
        if num_vars == 2:
            st.subheader("Análisis Gráfico (2D)")
            fig = go.Figure()
            
            x1_opt = prob.variables()[0].varValue
            x2_opt = prob.variables()[1].varValue
            
            # --- Ajuste dinámico de la escala X ---
            cortes_x = [x1_opt * 2, 10] # Mínimos por defecto
            for i in range(num_restricciones):
                if matriz_restricciones[i][0] > 0:
                    cortes_x.append(limites_restricciones[i] / matriz_restricciones[i][0])
            max_x1 = max(cortes_x) * 1.1 # 10% de margen a la derecha
            x1_vals = np.linspace(0, max_x1, 400)
            
            # --- 1. Calcular Vértices de la Región Factible ---
            lineas = [(1, 0, 0), (0, 1, 0)] # Ejes x1=0, x2=0
            for i in range(num_restricciones):
                lineas.append((matriz_restricciones[i][0], matriz_restricciones[i][1], limites_restricciones[i]))
                
            puntos_factibles = []
            for l1, l2 in itertools.combinations(lineas, 2):
                A = np.array([[l1[0], l1[1]], [l2[0], l2[1]]])
                b = np.array([l1[2], l2[2]])
                try:
                    pt = np.linalg.solve(A, b)
                    x1, x2 = round(pt[0], 5), round(pt[1], 5)
                    
                    if x1 >= -1e-5 and x2 >= -1e-5: # Condición de no negatividad
                        valido = True
                        for i in range(num_restricciones):
                            val = matriz_restricciones[i][0]*x1 + matriz_restricciones[i][1]*x2
                            lim = limites_restricciones[i]
                            sim = simbolos_restricciones[i]
                            if sim == "<=" and val > lim + 1e-4: valido = False
                            elif sim == ">=" and val < lim - 1e-4: valido = False
                            elif sim == "=" and abs(val - lim) > 1e-4: valido = False
                        
                        if valido:
                            puntos_factibles.append([x1, x2])
                except np.linalg.LinAlgError:
                    pass # Rectas paralelas
            
            # --- 2. Dibujar Región Factible ---
            if len(puntos_factibles) >= 3:
                puntos_unicos = np.unique(puntos_factibles, axis=0)
                if len(puntos_unicos) >= 3:
                    hull = ConvexHull(puntos_unicos)
                    vertices = puntos_unicos[hull.vertices]
                    vertices = np.vstack((vertices, vertices[0])) # Cerrar el polígono
                    
                    fig.add_trace(go.Scatter(
                        x=vertices[:,0], y=vertices[:,1], 
                        fill='toself', fillcolor='rgba(0, 255, 128, 0.3)', 
                        line=dict(color='rgba(255,255,255,0)'),
                        name='Región Factible'
                    ))

            # --- 3. Dibujar rectas de restricciones ---
            for i in range(num_restricciones):
                c1, c2 = matriz_restricciones[i][0], matriz_restricciones[i][1]
                limite = limites_restricciones[i]
                
                if c2 != 0:
                    x2_vals = (limite - c1 * x1_vals) / c2
                    valid = x2_vals >= 0
                    fig.add_trace(go.Scatter(x=x1_vals[valid], y=x2_vals[valid], mode='lines', name=f'Restricción {i+1}'))
                elif c1 != 0:
                    fig.add_vline(x=limite/c1, line_dash="dash", line_color="grey", annotation_text=f'Restricción {i+1}')
            
            # --- 4. Dibujar Punto Óptimo ---
            fig.add_trace(go.Scatter(
                x=[x1_opt], y=[x2_opt], 
                mode='markers+text', 
                marker=dict(color='red', size=12, symbol='star'), 
                text=[f'Óptimo ({round(x1_opt,2)}, {round(x2_opt,2)})'],
                textposition="top right",
                name='Punto Óptimo'
            ))
            
            fig.update_layout(xaxis_title="X1", yaxis_title="X2", xaxis=dict(rangemode='tozero'), yaxis=dict(rangemode='tozero'), height=600)
            st.plotly_chart(fig, use_container_width=True)
            
    else:
        st.error(f"El modelo no tiene una solución óptima válida. Estado: {estado}")
