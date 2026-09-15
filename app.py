import streamlit as st
import pulp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("Solucionador de Programación Lineal")
st.write("Configura tu modelo, añade los coeficientes y resuélvelo.")

# 1. Configuración de dimensiones
col1, col2 = st.columns(2)
with col1:
    num_vars = st.number_input("Número de variables", min_value=2, value=2, step=1)
with col2:
    num_rest = st.number_input("Número de restricciones", min_value=1, value=2, step=1)

st.divider()

# 2. Interfaz para la Función Objetivo
st.subheader("Función Objetivo")
tipo_opt = st.selectbox("¿Qué deseas hacer?", ["Maximizar", "Minimizar"])

st.write("Introduce los coeficientes (C):")
cols_obj = st.columns(num_vars)
coeficientes_z = []

for i in range(num_vars):
    with cols_obj[i]:
        valor = st.number_input(f"X{i+1}", value=0.0, key=f"obj_{i}")
        coeficientes_z.append(valor)

st.divider()

# 3. Interfaz para las Restricciones
st.subheader("Restricciones")
st.write("Introduce los coeficientes, el signo y el término independiente (b).")

datos_restricciones = []

for i in range(num_rest):
    st.markdown(f"**Restricción {i+1}**")
    cols_rest = st.columns(num_vars + 2)
    
    coefs_r = []
    for j in range(num_vars):
        with cols_rest[j]:
            val = st.number_input(f"X{j+1}", value=0.0, key=f"r_{i}_v_{j}")
            coefs_r.append(val)
            
    with cols_rest[num_vars]:
        signo = st.selectbox("Signo", ["<=", ">=", "="], key=f"signo_{i}")
        
    with cols_rest[num_vars + 1]:
        limite = st.number_input("Límite (b)", value=0.0, key=f"limite_{i}")
        
    datos_restricciones.append({"coefs": coefs_r, "signo": signo, "limite": limite})

st.caption("Nota: Se asume la condición de no negatividad para todas las variables (Xi ≥ 0).")

st.divider()

# 4. Botón y lógica de resolución
if st.button("Resolver Modelo", type="primary"):
    # Crear el problema en PuLP
    sentido = pulp.LpMaximize if tipo_opt == "Maximizar" else pulp.LpMinimize
    problema = pulp.LpProblem("Modelo_Usuario", sentido)
    
    # Crear las variables de decisión (con límite inferior 0)
    variables = [pulp.LpVariable(f"X{j+1}", lowBound=0) for j in range(num_vars)]
    
    # Añadir la Función Objetivo
    problema += pulp.lpSum([coeficientes_z[j] * variables[j] for j in range(num_vars)]), "Z"
    
    # Añadir las Restricciones
    for i, rest in enumerate(datos_restricciones):
        expresion = pulp.lpSum([rest["coefs"][j] * variables[j] for j in range(num_vars)])
        if rest["signo"] == "<=":
            problema += (expresion <= rest["limite"]), f"Restriccion_{i+1}"
        elif rest["signo"] == ">=":
            problema += (expresion >= rest["limite"]), f"Restriccion_{i+1}"
        else:
            problema += (expresion == rest["limite"]), f"Restriccion_{i+1}"
            
    # Resolver
    problema.solve()
    estado = pulp.LpStatus[problema.status]
    
    if estado == "Optimal":
        st.success("¡Solución Óptima encontrada!")
        st.metric(label=f"Valor de Z ({tipo_opt})", value=round(pulp.value(problema.objective), 4))
        
        col_res1, col_res2 = st.columns(2)
        
        with col_res1:
            st.subheader("Variables de Decisión")
            vars_data = [{"Variable": v.name, "Valor Óptimo": v.varValue} for v in variables]
            st.dataframe(pd.DataFrame(vars_data), hide_index=True)
            
        with col_res2:
            st.subheader("Análisis de Restricciones")
            rest_data = []
            for name, constraint in problema.constraints.items():
                rest_data.append({
                    "Restricción": name.replace("Restriccion_", "R"),
                    "Holgura / Exceso": abs(round(constraint.slack, 4)) if constraint.slack is not None else 0,
                    "Precio Sombra": round(constraint.pi, 4) if constraint.pi is not None else 0,
                    "Saturada": "Sí" if abs(constraint.slack) <= 1e-5 else "No"
                })
            st.dataframe(pd.DataFrame(rest_data), hide_index=True)
            
        # 5. Gráfica de la Región Factible (Solo para 2 variables)
        if num_vars == 2:
            st.divider()
            st.subheader("Visualización del Modelo (2 Variables)")
            
            max_val = 10.0 
            for rest in datos_restricciones:
                a, b_coef = rest["coefs"][0], rest["coefs"][1]
                c = rest["limite"]
                if a > 0: max_val = max(max_val, (c / a) * 1.2)
                if b_coef > 0: max_val = max(max_val, (c / b_coef) * 1.2)
                
            opt_x1, opt_x2 = variables[0].varValue, variables[1].varValue
            max_val = max(max_val, opt_x1 * 1.2, opt_x2 * 1.2)

            x = np.linspace(0, max_val, 400)
            y = np.linspace(0, max_val, 400)
            X, Y = np.meshgrid(x, y)
            
            factible = np.ones_like(X, dtype=bool)
            fig, ax = plt.subplots(figsize=(8, 6))

            for i, rest in enumerate(datos_restricciones):
                a, b_coef = rest["coefs"][0], rest["coefs"][1]
                c, signo = rest["limite"], rest["signo"]
                
                Z_eval = a * X + b_coef * Y
                
                if signo == "<=":
                    factible = factible & (Z_eval <= c)
                elif signo == ">=":
                    factible = factible & (Z_eval >= c)
                else:
                    factible = factible & (np.abs(Z_eval - c) < (max_val * 0.005))
                    
                ax.contour(X, Y, Z_eval, levels=[c], colors=[f'C{i}'], linewidths=2, label=f'R{i+1}')

            ax.imshow(factible.astype(int), extent=(0, max_val, 0, max_val), 
                      origin='lower', cmap='Greens', alpha=0.3)

            ax.plot(opt_x1, opt_x2, marker='*', color='red', markersize=15, label='Punto Óptimo')
            
            ax.set_xlim(0, max_val)
            ax.set_ylim(0, max_val)
            ax.set_xlabel("Variable X1")
            ax.set_ylabel("Variable X2")
            ax.grid(True, linestyle='--', alpha=0.6)
            
            # Evitar warnings si no hay etiquetas en las restricciones
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend()
            
            st.pyplot(fig)
            
        elif num_vars > 2:
            st.info("La gráfica de la región factible solo está disponible para modelos de 2 variables, ya que no podemos representar geometrías de 3 o más dimensiones de forma plana.")
            
    else:
        st.error(f"El solucionador no encontró una solución óptima. Estado del modelo: {estado}")
            
