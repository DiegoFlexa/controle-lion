import streamlit as st
import datetime
import pandas as pd

# Configuração da página do aplicativo
st.set_page_config(page_title="Controle Lion v2", page_icon="🚚", layout="wide")

st.title("🚚 Controle Lion v2 - Gerenciamento de Pátio")
st.write("Registre entradas e saídas de veículos de forma simultânea.")

# -----------------------------------------------------------------------------
# BANCO DE DADOS EM MEMÓRIA (st.session_state)
# Nota: Mantém os dados enquanto o app estiver aberto. Para salvar permanentemente,
# o ideal depois é conectar a uma Planilha do Google ou Banco de Dados SQL.
# -----------------------------------------------------------------------------
if 'base_dados' not in st.session_state:
    st.session_state.base_dados = pd.DataFrame(
        columns=["Data", "Placa", "Motorista", "Nota_Fiscal", "Hora_Entrada", "Hora_Saida", "Status"]
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
        placa = st.text_input("Placa do Caminhão (Obrigatório)").upper().strip()
        motorista = st.text_input("Nome do Motorista (Obrigatório)").strip()
        
        # ALTERAÇÃO: O número da nota agora é explicitamente opcional aqui
        numero_nota = st.text_input("Número da Nota Fiscal (Opcional)").strip()
        
        # CORREÇÃO DO ERRO ANTERIOR: Função de submit correta do Streamlit
        botao_salvar_entrada = st.form_submit_button(label='Confirmar Entrada')

    # Lógica ao clicar em Salvar Entrada
    if botao_salvar_entrada:
        if placa and motorista:  # Valida apenas os campos obrigatórios
            hora_atual = datetime.datetime.now().strftime("%H:%M:%S")
            
            # Se o usuário não digitou a nota, define um texto padrão
            nota_final = numero_nota if numero_nota else "Não Informada"
            
            # Monta a nova linha do caminhão que acabou de chegar
            nova_entrada = {
                "Data": str(data_hoje),
                "Placa": placa,
                "Motorista": motorista,
                "Nota_Fiscal": nota_final,
                "Hora_Entrada": hora_atual,
                "Hora_Saida": "",
                "Status": "No Pátio"
            }
            
            # Adiciona na tabela
            st.session_state.base_dados = pd.concat(
                [st.session_state.base_dados, pd.DataFrame([nova_entrada])], 
                ignore_index=True
            )
            st.success(f"✅ Caminhão {placa} registrado com sucesso às {hora_atual}!")
        else:
            st.error("⚠️ Erro: Placa e Motorista são obrigatórios para dar entrada!")

# ==========================================
# COLUNA 2: REGISTRAR SAÍDA (HORAS DEPOIS)
# ==========================================
with col2:
    st.header("📤 Registrar Saída")
    
    # Filtra a tabela para mostrar APENAS quem ainda está "No Pátio"
    caminhoes_no_patio = st.session_state.base_dados[st.session_state.base_dados["Status"] == "No Pátio"]
    
    if caminhoes_no_patio.empty:
        st.info("Não há caminhões no pátio aguardando saída no momento.")
    else:
        # Monta a lista visual de seleção (ex: "ABC1D23 - Motorista: João (Entrada: 14:30)")
        lista_selecao = caminhoes_no_patio.apply(
            lambda r: f"{r['Placa']} - {r['Motorista']} (NF: {r['Nota_Fiscal']})", axis=1
        ).tolist()
        
        # Formulário de Saída
        with st.form(key='form_saida'):
            opcao_selecionada = st.selectbox("Selecione o veículo que está saindo:", lista_selecao)
            
            # Opcional: Se não colocou a nota na entrada, pode preencher agora na saída!
            nota_na_saida = st.text_input("Atualizar/Inserir Nota Fiscal na Saída (Opcional)").strip()
            
            botao_confirmar_saida = st.form_submit_button(label='Confirmar Saída')
            
        if _:= botao_confirmar_saida:
            # Pega a placa isolada (primeiro termo antes do hífen)
            placa_saida = opcao_selecionada.split(" - ")[0]
            hora_saida_atual = datetime.datetime.now().strftime("%H:%M:%S")
            
            # Encontra o índice exato desse caminhão no banco de dados que ainda está "No Pátio"
            idx = st.session_state.base_dados[
                (st.session_state.base_dados["Placa"] == placa_saida) & 
                (st.session_state.base_dados["Status"] == "No Pátio")
            ].index
            
            if len(idx) > 0:
                # Se digitou uma nota agora na saída, atualiza o campo da nota
                if nota_na_saida:
                    st.session_state.base_dados.loc[idx[0], "Nota_Fiscal"] = nota_na_saida
                
                # Registra o horário de saída e muda o status para Liberado
                st.session_state.base_dados.loc[idx[0], "Hora_Saida"] = hora_saida_atual
                st.session_state.base_dados.loc[idx[0], "Status"] = "Liberado"
                
                st.warning(f"🚩 Saída do caminhão {placa_saida} confirmada às {hora_saida_atual}!")
                st.rerun()  # Recarrega a tela para atualizar a lista de quem sobrou no pátio

# ==========================================
# PAINEL GERAL: HISTÓRICO / MONITORAMENTO
# ==========================================
st.write("---")
st.header("📋 Monitoramento do Pátio (Histórico Geral)")

if st.session_state.base_dados.empty:
    st.write("Nenhum registro movimentado hoje.")
else:
    # Exibe a tabela completa na tela para você acompanhar em tempo real
    st.dataframe(st.session_state.base_dados, use_container_width=True)
    
