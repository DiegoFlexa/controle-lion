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
        
        hora_sugerida = datetime.datetime.now().time()
        hora_entrada = st.time_input("Horário de Entrada", hora_sugerida)
        
        # OBRIGATÓRIO: Placa
        placa = st.text_input("Placa do Veículo (Obrigatório)").upper().strip()
        
        # OPCIONAIS: Peso e Nota Fiscal (Sem campo de motorista)
        peso_entrada = st.text_input("Peso de Entrada (Opcional)").strip()
        numero_nota = st.text_input("Número da Nota Fiscal (Opcional)").strip()
        
        botao_salvar_entrada = st.form_submit_button(label='Confirmar Entrada')

    # Lógica ao clicar em Salvar Entrada
    if botao_salvar_entrada:
        if placa:  # Valida apenas o campo obrigatório (Placa)
            hora_formatada = hora_entrada.strftime("%H:%M:%S")
            peso_final = peso_entrada if peso_entrada else "Não Informado"
            nota_final = numero_nota if numero_nota else "Não Informada"
            
            # Monta a nova linha do veículo
            nova_entrada = {
                "Data_Entrada": str(data_entrada),
                "Hora_Entrada": hora_formatada,
                "Placa": placa,
                "Peso_Entrada": peso_final,
                "Nota_Fiscal": nota_final,
                "Data_Saida": "",
                "Hora_Saida": "",
                "Status": "No Pátio"
            }
            
            # Adiciona na tabela
            st.session_state.base_dados = pd.concat(
                [st.session_state.base_dados, pd.DataFrame([nova_entrada])], 
                ignore_index=True
            )
            st.success(f"✅ Veículo {placa} registrado no pátio com sucesso!")
            st.rerun()
        else:
            st.error("⚠️ Erro: A Placa é obrigatória para dar entrada!")

# ==========================================
# COLUNA 2: REGISTRAR SAÍDA (HORAS/DIAS DEPOIS)
# ==========================================
with col2:
    st.header("📤 Registrar Saída")
    
    # Filtra a tabela para mostrar APENAS quem ainda está "No Pátio"
    veiculos_no_patio = st.session_state.base_dados[st.session_state.base_dados["Status"] == "No Pátio"]
    
    if veiculos_no_patio.empty:
        st.info("Não há veículos no pátio aguardando saída no momento.")
    else:
        # Monta a lista visual de seleção mostrando a placa e detalhes da entrada correspondente
        lista_selecao = veiculos_no_patio.apply(
            lambda r: f"{r['Placa']} (Entrada: {r['Data_Entrada']} às {r['Hora_Entrada']})", axis=1
        ).tolist()
        
        # Formulário de Saída
        with st.form(key='form_saida'):
            opcao_selecionada = st.selectbox("Selecione o veículo que está saindo:", lista_selecao)
            
            # Campos manuais para Data e Hora de Saída (já vêm na hora atual)
            data_saida = st.date_input("Data de Saída", datetime.date.today())
            hora_saida_sugerida = datetime.datetime.now().time()
            hora_saida = st.time_input("Horário de Saída", hora_saida_sugerida)
            
            botao_confirmar_saida = st.form_submit_button(label='Confirmar Saída')
            
        if botao_confirmar_saida:
            # Separa o texto para conseguir a placa pura isolada
            placa_saida = opcao_selecionada.split(" (")[0]
            
            # Encontra o índice exato desse veículo que está "No Pátio"
            idx = st.session_state.base_dados[
                (st.session_state.base_dados["Placa"] == placa_saida) & 
                (st.session_state.base_dados["Status"] == "No Pátio")
            ].index
            
            if len(idx) > 0:
                # Preenche a data e hora de saída escolhidas e altera o status
                st.session_state.base_dados.loc[idx[0], "Data_Saida"] = str(data_saida)
                st.session_state.base_dados.loc[idx[0], "Hora_Saida"] = hora_saida.strftime("%H:%M:%S")
                st.session_state.base_dados.loc[idx[0], "Status"] = "Liberado"
                
                st.warning(f"🚩 Saída do veículo {placa_saida} confirmada!")
                st.rerun()

# ==========================================
# PAINEL GERAL: HISTÓRICO E EXPORTAÇÃO EXCEL
# ==========================================
st.write("---")
st.header("📋 Monitoramento do Pátio & Relatórios")

if st.session_state.base_dados.empty:
    st.write("Nenhum veículo movimentado hoje.")
else:
    # Exibe a tabela completa em tempo real
    st.dataframe(st.session_state.base_dados, use_container_width=True)
    
    # -------------------------------------------------------------------------
    # GERAÇÃO DO ARQUIVO EXCEL
    # -------------------------------------------------------------------------
    # Cria o arquivo em memória para disponibilizar para download no navegador
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        st.session_state.base_dados.to_excel(writer, index=False, sheet_name='Controle_Patio')
    
    buffer.seek(0)
    
    # Botão azul nativo do Streamlit para baixar a planilha
    st.download_button(
        label="📥 Baixar Relatório do Excel (.xlsx)",
        data=buffer,
        file_name=f"relatorio_patio_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
