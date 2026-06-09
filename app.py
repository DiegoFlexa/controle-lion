import streamlit as st
import datetime
import pandas as pd

# Configuração da página do aplicativo
st.set_page_config(page_title="Controle Lion v2", page_icon="🚚", layout="wide")

st.title("🚚 Controle Lion v2 - Gerenciamento de Pátio")
st.write("Registre entradas e saídas de veículos de forma simultânea.")

# -----------------------------------------------------------------------------
# BANCO DE DADOS EM MEMÓRIA (st.session_state)
# -----------------------------------------------------------------------------
if 'base_dados' not in st.session_state:
    st.session_state.base_dados = pd.DataFrame(
        columns=["Data", "Placa", "Motorista", "Nota_Fiscal", "Hora_Entrada", "Peso_Entrada", "Hora_Saida", "Status"]
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
        data_hoje = st.date_input("Data de Entrada", datetime.date.today())
        
        # NOVO: Campo para o Horário de Entrada (já puxa a hora atual do sistema)
        hora_sugerida = datetime.datetime.now().time()
        hora_entrada = st.time_input("Horário de Entrada", hora_sugerida)
        
        placa = st.text_input("Placa do Caminhão (Obrigatório)").upper().strip()
        motorista = st.text_input("Nome do Motorista (Obrigatório)").strip()
        
        # NOVO: Campo para o Peso na Entrada (Opcional)
        peso_entrada = st.text_input("Peso de Entrada (Opcional)").strip()
        
        # O número da nota fiscal (Opcional)
        numero_nota = st.text_input("Número da Nota Fiscal (Opcional)").strip()
        
        botao_salvar_entrada = st.form_submit_button(label='Confirmar Entrada')

    # Lógica ao clicar em Salvar Entrada
    if botao_salvar_entrada:
        if placa and motorista:  # Valida apenas os campos obrigatórios
            # Formata a hora escolhida para o formato de texto padrão (HH:MM:SS)
            hora_formatada = hora_entrada.strftime("%H:%M:%S")
            
            nota_final = numero_nota if numero_nota else "Não Informada"
            peso_final = peso_entrada if peso_entrada else "Não Informado"
            
            # Monta a nova linha do caminhão
            nova_entrada = {
                "Data": str(data_hoje),
                "Placa": placa,
                "Motorista": motorista,
                "Nota_Fiscal": nota_final,
                "Hora_Entrada": hora_formatada,
                "Peso_Entrada": peso_final,
                "Hora_Saida": "",
                "Status": "No Pátio"
            }
            
            # Adiciona na tabela
            st.session_state.base_dados = pd.concat(
                [st.session_state.base_dados, pd.DataFrame([nova_entrada])], 
                ignore_index=True
            )
            st.success(f"✅ Caminhão {placa} registrado com sucesso às {hora_formatada}!")
        else:
            st.error("⚠️ Erro: Placa e Motorista são obrigatórios para dar entrada!")

# ==========================================
# COLUNA 2: REGISTRAR SAÍDA (HORAS DEPOIS)
