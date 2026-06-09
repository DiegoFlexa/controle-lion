import streamlit as st
import datetime
import pandas as pd
import io

# Configuração da página do aplicativo
st.set_page_config(page_title="Controle Lion v2", page_icon="🚚", layout="wide")

st.title("🚚 Controle Lion v2 - Gerenciamento de Pátio")
st.write("Registre entradas e saídas de veículos com geração de relatório em Excel.")

# -----------------------------------------------------------------------------
# BANCO DE DADOS EM MEMÓRIA (st.session_state)
# -----------------------------------------------------------------------------
if 'base_dados' not in st.session_state:
    st.session_state.base_dados = pd.DataFrame(
        columns=[
            "Data_Entrada", "Hora_Entrada", "Placa", 
            "Peso_Entrada", "Nota_Fiscal", 
            "Data_Saida", "Hora_Saida", "Status"
        ]
    )

# Criando duas colunas na tela: Lado esquerdo (Entrada) | Lado direito (Saída)
col1, col2 = st.columns(2)

# ==========================================
# COLUNA 1: REGISTRAR NOVA ENTRADA
# ==========================================
with col1:
    st.header("📥 Registrar Entrada")
    
    with st.form(key='form_entrada', clear_on_submit=True):
        data_entrada = st.date_input("Data de Entrada", datetime.date.today())
        
        # Sugestão do horário atual em formato de texto
        hora_atual_sugerida = datetime.datetime.now().strftime("%H:%M")
        
        # ALTERAÇÃO: Campo de texto para digitar a hora manualmente
        hora_entrada = st.text_input("Horário de Entrada (Ex: 19:30)", value=hora_atual_sugerida).strip()
        
        # OBRIGATÓRIO: Placa
        placa = st.text_input("Placa do Veículo (Obrigatório)").upper().strip()
        
        # OPCIONAIS: Peso e Nota Fiscal
        peso_entrada = st.text_input("Peso de Entrada (Opcional)").strip()
        numero_nota = st.text_input("Número da Nota Fiscal (Opcional)").strip()
        
        botao_salvar_entrada = st.form_submit_button(label='Confirmar Entrada')

    if botao_salvar_entrada:
        if placa and hora_entrada:  # Valida os campos obrigatórios para entrada
            peso_final = peso_entrada if peso_entrada else "Não Informado"
            nota_final = numero_nota if numero_nota else "Não Informada"
            
            nova_entrada = {
                "Data_Entrada": str(data_entrada),
                "Hora_Entrada": hora_entrada,
                "Placa": placa,
                "Peso_Entrada": peso_final,
                "Nota_Fiscal": nota_final,
                "Data_Saida": "",
                "Hora_Saida": "",
                "Status": "No Pátio"
            }
            
            st.session_state.base_dados = pd.concat(
                [st.session_state.base_dados, pd.DataFrame([nova_entrada])], 
                ignore_index=True
            )
            st.success(f"✅ Veículo {placa} registrado com sucesso
            
