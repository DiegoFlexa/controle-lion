import streamlit as st
import datetime
import pandas as pd
import io
import sqlite3

# Configuração da página do aplicativo
st.set_page_config(page_title="Controle Lion v2", page_icon="🚚", layout="wide")

st.title("🚚 Controle Lion v2 - Gerenciamento de Pátio")
st.write("Registre entradas e saídas de veículos com inserção manual de horas e minutos.")

# -----------------------------------------------------------------------------
# BANCO DE DADOS PERMANENTE E ONLINE (SQLite)
# -----------------------------------------------------------------------------
def conectar_banco():
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

conectar_banco()

def carregar_dados():
    conn = sqlite3.connect("dados_patio.db")
    df = pd.read_sql_query("SELECT * FROM patio", conn)
    conn.close()
    if df.empty:
        return pd.DataFrame(columns=["id", "Data_Entrada", "Hora_Entrada", "Placa", "Peso_Entrada", "Nota_Fiscal", "Data_Saida", "Hora_Saida", "Status"])
    return df

def calcular_tempo_descarregamento(data_ent, hora_ent, data_sai, hora_sai):
    try:
        inicio = datetime.datetime.strptime(f"{data_ent} {hora_ent.strip()}", "%Y-%m-%d %H:%M")
        fim = datetime.datetime.strptime(f"{data_sai} {hora_sai.strip()}", "%Y-%m-%d %H:%M")
        
        diferenca = fim - inicio
        total_segundos = int(diferenca.total_seconds())
        
        if total_segundos < 0:
            return "Erro: Saída antes da Entrada"
            
        horas, resto = divmod(total_segundos, 3600)
        minutos, _ = divmod(resto, 60)
        return f"{horas:02d}:{minutos:02d} hs"
    except Exception:
        return "Erro no cálculo"

base_dados = carregar_dados()

# Pegando a hora e minuto atual do sistema para sugerir nos campos
agora = datetime.datetime.now()
hora_atual = agora.hour
minuto_atual = agora.minute

col1, col2 = st.columns(2)

# ==========================================
# COLUNA 1: REGISTRAR NOVA ENTRADA
# ==========================================
with col1:
    st.header("📥 Registrar Entrada")
    
    with st.form(key='form_entrada'):
        data_entrada = st.date_input("Data de Entrada", datetime.date.today())
        
        # Campos separados para digitação manual de Hora e Minuto
        st.write("**Horário de Entrada Manual:**")
        c_hora_ent, c_min_ent = st.columns(2)
        with c_hora_ent:
            h_entrada = st.number_input("Hora (00-23)", min_value=0, max_value=23, value=hora_atual, step=1, key="h_ent")
        with c_min_ent:
            m_entrada = st.number_input("Minuto (00-59)", min_value=0, max_value=59, value=minuto_atual, step=1, key="m_ent")
        
        placa = st.text_input("Placa do Veículo (Obrigatório)").upper().strip()
        peso_entrada = st.text_input("Peso de Entrada (Opcional)").strip()
        numero_nota = st.text_input("Número da Nota Fiscal (Opcional)").strip()
        
        botao_salvar_entrada = st.form_submit_button(label='Confirmar Entrada')

    if botao_salvar_entrada:
        if placa:
            # Formata a hora digitada para o padrão HH:MM
            hora_entrada_formatada = f"{h_entrada:02d}:{m_entrada:02d}"
            peso_final = peso_entrada if peso_entrada else "Não Informado"
            nota_final = numero_nota if numero_nota else "Não Informada"
            
            conn = sqlite3.connect("dados_patio.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO patio (Data_Entrada, Hora_Entrada, Placa, Peso_Entrada, Nota_Fiscal, Data_Saida, Hora_Saida, Status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(data_entrada), hora_entrada_formatada, placa, peso_final, nota_final, "", "", "No Pátio"))
            conn.commit()
            conn.close()
            
            st.success(f"✅ Veículo {placa} registrado às {hora_entrada_formatada} com sucesso!")
            st.rerun()
        else:
            st.error("⚠️ Erro: A Placa é obrigatória!")

# ==========================================
# COLUNA 2: REGISTRAR SAÍDA
# ==========================================
with col2:
    st.header("📤 Registrar Saída")
    
    veiculos_no_patio = base_dados[base_dados["Status"] == "No Pátio"]
    
    if veiculos_no_patio.empty:
        st.info("Não há veículos no pátio aguardando saída no momento.")
    else:
        mapeamento_veiculos = {}
        lista_selecao = []
        
        for _, row in veiculos_no_patio.iterrows():
            texto = f"{row['Placa']} (Entrada: {row['Data_Entrada']} às {row['Hora_Entrada']})"
            lista_selecao.append(texto)
            mapeamento_veiculos[texto] = row['id']
        
        with st.form(key='form_saida'):
            opcao_selecionada = st.selectbox("Selecione o veículo que está saindo:", lista_selecao)
            data_saida = st.date_input("Data de Saída", datetime.date.today())
            
            # Campos separados para digitação manual de Hora e Minuto na saída
            st.write("**Horário de Saída Manual:**")
            c_hora_sai, c_min_sai = st.columns(2)
            with c_hora_sai:
                h_saida = st.number_input("Hora (00-23)", min_value=0, max_value=23, value=hora_atual, step=1, key="h_sai")
            with c_min_sai:
                m_saida = st.number_input("Minuto (00-59)", min_value=0, max_value=59, value=minuto_atual, step=1, key="m_sai")
                
            botao_confirmar_saida = st.form_submit_button(label='Confirmar Saída')
            
        if botao_confirmar_saida:
            id_selecionado = mapeamento_veiculos[opcao_selecionada]
            placa_saida = opcao_selecionada.split(" (")[0]
            # Formata a hora digitada para o padrão HH:MM
            hora_saida_formatada = f"{h_saida:02d}:{m_saida:02d}"
            
            conn = sqlite3.connect("dados_patio.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE patio 
                SET Data_Saida = ?, Hora_Saida = ?, Status = ?
                WHERE id = ?
            """, (str(data_saida), hora_saida_formatada, "Liberado", id_selecionado))
            conn.commit()
            conn.close()
            
            st.warning(f"🚩 Saída do veículo {placa_saida} gravada às {hora_saida_formatada}!")
            st.rerun()

# ==========================================
# PAINEL GERAL: HISTÓRICO E EXPORTAÇÃO EXCEL
# ==========================================
st.write("---")
st.header("📋 Monitoramento do Pátio & Relatórios")

if base_dados.empty:
    st.write("Nenhum veículo movimentado hoje.")
else:
    base_dados["Tempo_Descarregamento"] = base_dados.apply(
        lambda row: calcular_tempo_descarregamento(
            row["Data_Entrada"], row["Hora_Entrada"], row["Data_Saida"], row["Hora_Saida"]
        ) if row["Status"] == "Liberado" else "No Pátio", axis=1
    )
    
    colunas_ordenadas = [
        "Data_Entrada", "Hora_Entrada", "Placa", "Peso_Entrada", 
        "Nota_Fiscal", "Data_Saida", "Hora_Saida", "Tempo_Descarregamento", "Status"
    ]
    
    df_exibicao = base_dados[colunas_ordenadas]
    st.dataframe(df_exibicao, use_container_width=True)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_exibicao.to_excel(writer, index=False, sheet_name='Controle_Patio_Completo')
    
    buffer.seek(0)
    
    st.download_button(
        label="📥 Baixar Relatório do Excel com Tempo de Descarregamento (.xlsx)",
        data=buffer,
        file_name=f"relatorio_patio_completo_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
