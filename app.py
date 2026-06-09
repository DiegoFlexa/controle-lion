import streamlit as st
import datetime
import pandas as pd
import io

# Configuração da página do aplicativo
st.set_page_config(page_title="Controle Lion v2", page_icon="🚚", layout="wide")

st.title("🚚 Controle Lion v2 - Gerenciamento de Pátio")
st.write("Registre entradas e saídas de veículos de forma simultânea com relatório para Excel.")

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
        
        # Sugestão automática do horário atual em formato de texto (HH:MM)
        hora_atual_sugerida = datetime.datetime.now().strftime("%H:%M")
        
        # MODIFICAÇÃO AQUI: Mudado para text
