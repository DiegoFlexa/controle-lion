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
        
        # OPCIONAIS: Peso e Nota Fiscal
        peso_entrada = st.text_input("Peso de Entrada (Opcional)").strip()
        numero_nota = st.text_input("Número da Nota Fiscal (Opcional)").strip()
        
        botao_salvar_entrada = st.form_submit_button(label='Confirmar Entrada')

    # Lógica ao clicar em Salvar Entrada
    if botao_salvar_entrada:
        if placa and hora_entrada:  # Valida se a placa e a hora foram informadas
            peso_final = peso_entrada if peso_entrada else "Não Informado"
            nota_final = numero_nota if numero_nota else "Não Informada"
            
            # Monta a nova linha do veículo
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
            
            # Adiciona na tabela
            st.session_state.base_dados = pd.concat(
                [st.session_state.base_dados, pd.DataFrame([nova_entrada])], 
                ignore_index=True
            )
            st.success(f"✅ Veículo {placa} registrado às {hora_entrada} com sucesso!")
            st.rerun()
        else:
            st.error("⚠️ Erro: A Placa e o Horário de Entrada são obrigatórios!")

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
        # Monta a lista visual de seleção mostrando a placa e detalhes da entrada
        lista_selecao = veiculos_no_patio.apply(
            lambda r: f"{r['Placa']} (Entrada: {r['Data_Entrada']} às {r['Hora_Entrada']})", axis=1
        ).tolist()
        
        # Formulário de Saída
        with st.form(key='form_saida'):
            opcao_selecionada = st.selectbox("Selecione o veículo que está saindo:", lista_selecao)
            
            data_saida = st.date_input("Data de Saída", datetime.date.today())
            
            # SUGESTÃO DE HORÁRIO ATUAL PARA A SAÍDA
            hora_saida_sugerida = datetime.datetime.now().strftime("%H:%M")
            
            # ALTERAÇÃO: Campo de texto para digitar o horário de saída manualmente
            hora_saida = st.text_input("Horário de Saída (Ex: 22:45)", value=hora_saida_sugerida).strip()
            
            botao_confirmar_saida = st.form_submit_button(label='Confirmar Saída')
            
        if botao_confirmar_saida:
            if hora_saida:
                # Separa o texto para conseguir a placa pura isolada
                placa_saida = opcao_selecionada.split(" (")[0]
                
                # Encontra o índice exato desse veículo que está "No Pátio"
                idx = st.session_state.base_dados[
                    (st.session_state.base_dados["Placa"] == placa_saida) & 
                    (st.session_state.base_dados["Status"] == "No Pátio")
                ].index
                
                if len(idx) > 0:
                    # Preenche a data e hora de saída digitadas e altera o status
                    st.session_state.base_dados.loc[idx[0], "Data_Saida"] = str(data_saida)
                    st.session_state.base_dados.loc[idx[0], "Hora_Saida"] = hora_saida
                    st.session_state.base_dados.loc[idx[0], "Status"] = "Liberado"
                    
                    st.warning(f"🚩 Saída do veículo {placa_saida} confirmada às {hora_saida}!")
                    st.rerun()
            else:
                st.error("⚠️ Erro: O Horário de Saída é obrigatório!")

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
