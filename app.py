import streamlit as st
import datetime
import pandas as pd
import io
import sqlite3

# Configuração da página do aplicativo
st.set_page_config(page_title="Controle Lion v2", page_icon="🚚", layout="wide")

st.title("🚚 Controle Lion v2 - Gerenciamento de Pátio")
st.write("Registre entradas e saídas de veículos de forma simultânea com salvamento permanente e cálculo de descarregamento.")

# -----------------------------------------------------------------------------
# BANCO DE DADOS PERMANENTE E ONLINE (SQLite)
# -----------------------------------------------------------------------------
def conectar_banco():
    # Cria ou conecta ao arquivo de banco de dados para nunca perder os registros
    conn = sqlite3.connect("dados_patio.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Data_Entrada TEXT,
            Hora_Entrada TEXT,
            Placa TEXT,
            Peso_Entrada TEXT,
            Nota_Fiscal TEXT,
            Data_Saida TEXT,
            Hora_Saida TEXT,
            Status TEXT
        )
    """)
    conn.commit()
    return conn

# Inicializa o banco de dados
conn = conectar_banco()

# Função para carregar os dados salvos do banco para o aplicativo
def carregar_dados():
    conn = sqlite3.connect("dados_patio.db")
    df = pd.read_sql_query("SELECT * FROM patio", conn)
    conn.close()
    if df.empty:
        return pd.DataFrame(columns=["id", "Data_Entrada", "Hora_Entrada", "Placa", "Peso_Entrada", "Nota_Fiscal", "Data_Saida", "Hora_Saida", "Status"])
    return df

# Função para calcular a diferença de tempo de descarregamento
def calcular_tempo_descarregamento(hora_ent, hora_sai):
    try:
        # Tenta converter os textos digitados em formato de hora
        t_ent = datetime.datetime.strptime(hora_ent.strip(), "%H:%M")
        t_sai = datetime.datetime.strptime(hora_sai.strip(), "%H:%M")
        
        # Caso a saída tenha sido após a meia-noite (no dia seguinte)
        if t_sai < t_ent:
            t_sai += datetime.timedelta(days=1)
            
        diferenca = t_sai - t_ent
        horas, resto = divmod(diferenca.seconds, 3600)
        minutos, _ = divmod(resto, 60)
        return f"{horas:02d}:{minutos:02d} hs"
    except:
        return "Em andamento"

# Recarrega a base ativa a cada atualização da página
base_dados = carregar_dados()

# Criando duas colunas na tela: Lado esquerdo (Entrada) | Lado direito (Saída)
col1, col2 = st.columns(2)

# ==========================================
# COLUNA 1: REGISTRAR NOVA ENTRADA
# ==========================================
with col1:
    st.header("📥 Registrar Entrada")
    
    with st.form(key='form_entrada', clear_on_submit=True):
        data_entrada = st.date_input("Data de Entrada", datetime.date.today())
        
        hora_atual_sugerida = datetime.datetime.now().strftime("%H:%M")
        hora_entrada = st.text_input("Horário de Entrada (Ex: 19:30)", value=hora_atual_sugerida).strip()
        
        placa = st.text_input("Placa do Veículo (Obrigatório)").upper().strip()
        
        peso_entrada = st.text_input("Peso de Entrada (Opcional)").strip()
        numero_nota = st.text_input("Número da Nota Fiscal (Opcional)").strip()
        
        botao_salvar_entrada = st.form_submit_button(label='Confirmar Entrada')

    if botao_salvar_entrada:
        if placa and hora_entrada:
            peso_final = peso_entrada if peso_entrada else "Não Informado"
            nota_final = numero_nota if numero_nota else "Não Informada"
            
            # SALVAMENTO SALVO DIRETO NO BANCO ONLINE/PERMANENTE
            conn = sqlite3.connect("dados_patio.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO patio (Data_Entrada, Hora_Entrada, Placa, Peso_Entrada, Nota_Fiscal, Data_Saida, Hora_Saida, Status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(data_entrada), hora_entrada, placa, peso_final, nota_final, "", "", "No Pátio"))
            conn.commit()
            conn.close()
            
            st.success(f"✅ Veículo {placa} salvo permanentemente no sistema!")
            st.rerun()
        else:
            st.error("⚠️ Erro: A Placa e o Horário de Entrada são obrigatórios!")

# ==========================================
# COLUNA 2: REGISTRAR SAÍDA (HORAS/DIAS DEPOIS)
# ==========================================
with col2:
    st.header("📤 Registrar Saída")
    
    # Filtra puxando do banco apenas quem está "No Pátio"
    veiculos_no_patio = base_dados[base_dados["Status"] == "No Pátio"]
    
    if veiculos_no_patio.empty:
        st.info("Não há veículos no pátio aguardando saída no momento.")
    else:
        lista_selecao = veiculos_no_patio.apply(
            lambda r: f"{r['Placa']} (Entrada: {r['Data_Entrada']} às {r['Hora_Entrada']})", axis=1
        ).tolist()
        
        with st.form(key='form_saida'):
            opcao_selecionada = st.selectbox("Selecione o veículo que está saindo:", lista_selecao)
            
            data_saida = st.date_input("Data de Saída", datetime.date.today())
            
            hora_saida_sugerida = datetime.datetime.now().strftime("%H:%M")
            hora_saida = st.text_input("Horário de Saída (Ex: 22:45)", value=hora_saida_sugerida).strip()
            
            botao_confirmar_saida = st.form_submit_button(label='Confirmar Saída')
            
        if botao_confirmar_saida:
            if hora_saida:
                placa_saida = opcao_selecionada.split(" (")[0]
                
                # ATUALIZAÇÃO DIRETA NO BANCO DE DADOS PERMANENTE
                conn = sqlite3.connect("dados_patio.db")
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE patio 
                    SET Data_Saida = ?, Hora_Saida = ?, Status = ?
                    WHERE Placa = ? AND Status = 'No Pátio'
                """, (str(data_saida), hora_saida, "Liberado", placa_saida))
                conn.commit()
                conn.close()
                
                st.warning(f"🚩 Saída do veículo {placa_saida} gravada com sucesso!")
                st.rerun()
            else:
                st.error("⚠️ Erro: O Horário de Saída é obrigatório!")

# ==========================================
# PAINEL GERAL: HISTÓRICO E EXPORTAÇÃO EXCEL
# ==========================================
st.write("---")
st.header("📋 Monitoramento do Pátio & Relatórios")

if base_dados.empty:
    st.write("Nenhum veículo movimentado hoje.")
else:
    # Exibe a tabela completa em tempo real (Sem mostrar a coluna interna do 'id')
    st.dataframe(base_dados.drop(columns=["id"], errors="ignore"), use_container_width=True)
    
    # -------------------------------------------------------------------------
    # GERAÇÃO DO ARQUIVO EXCEL COM HORAS DE DESCARREGAMENTO
    # -------------------------------------------------------------------------
    # Copia a base de dados para injetar o cálculo sem alterar a tabela visual pura
    dados_excel = base_dados.copy()
    
    # Aplica a função de cálculo linha por linha nas colunas de hora
    dados_excel["Tempo_Descarregamento"] = dados_excel.apply(
        lambda row: calcular_tempo_descarregamento(row["Hora_Entrada"], row["Hora_Saida"]) if row["Status"] == "Liberado" else "No Pátio", axis=1
    )
    
    # Remove a coluna id para ficar limpo no Excel
    if "id" in dados_excel.columns:
        dados_excel = dados_excel.drop(columns=["id"])
        
    # Reorganiza a ordem para que o Tempo de Descarregamento fique logo após a Hora de Saída
    colunas_ordenadas = [
        "Data_Entrada", "Hora_Entrada", "Placa", "Peso_Entrada", 
        "Nota_Fiscal", "Data_Saida", "Hora_Saida", "Tempo_Descarregamento", "Status"
    ]
    dados_excel = dados_excel[colunas_ordenadas]

    # Transforma em planilha Excel para download
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        dados_excel.to_excel(writer, index=False, sheet_name='Controle_Patio_Completo')
    
    buffer.seek(0)
    
    st.download_button(
        label="📥 Baixar Relatório do Excel com Tempo de Descarregamento (.xlsx)",
        data=buffer,
        file_name=f"relatorio_patio_completo_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
