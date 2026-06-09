import streamlit as st
import datetime
import pandas as pd
import io

# Configuração da página do aplicativo
st.set_page_config(page_title="Controle Lion v2", page_icon="🚚", layout="wide")

st.title("🚚 Controle Lion v2 - Gerenciamento de Pátio")
st.write("Registre entradas e saídas de veículos digitando os horários manualmente.")

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
    
    # Formulário de Entrada
    with st.form(key='form_entrada', clear_on_submit=True):
        data_entrada = st.date_input("Data de Entrada", datetime.date.today())
        
        # SUGESTÃO DE HORÁRIO ATUAL: Já deixa o horário atual escrito, mas você pode apagar e digitar por cima
        hora_atual_sugerida = datetime.datetime.now().strftime("%H:%M")
        
        # ALTERAÇÃO: Campo de texto para digitar o horário manualmente
        hora_entrada = st.text_input("Horário de Entrada (Ex: 19:30)", value=hora_atual_sugerida).strip()
        
        # OBRIGATÓRIO: Placa
        placa = st.text_input("Placa do Veículo (Obrigatório)").upper().strip()
        
