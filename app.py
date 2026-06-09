import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference

# Configuração da página para celular
st.set_page_config(page_title="Controle Lion v2", page_icon="🚚", layout="centered")

# Conexão com o banco de dados local (SQLite)
def conectar_banco():
    conn = sqlite3.connect('registro_caminhoes.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT,
            numero_nota TEXT,
            peso_nota REAL,
            data_entrada TEXT,
            hora_entrada TEXT,
            data_saida TEXT,
            hora_saida TEXT,
            tempo_permanencia TEXT,
            minutos_permanencia REAL
        )
    ''')
    conn.commit()
    return conn

conn = conectar_banco()

# Função para calcular minutos e texto de permanência
def calcular_permanencia_detalhada(dt_e, hr_e, dt_s, hr_s):
    try:
        entrada = datetime.strptime(f"{dt_e} {hr_e}", "%Y-%m-%d %H:%M")
        saida = datetime.strptime(f"{dt_s} {hr_s}", "%Y-%m-%d %H:%M")
        diferenca = saida - entrada
        total_minutos = diferenca.total_seconds() / 60.0
        if total_minutos < 0:
            return "Erro", 0.0
        horas = int(total_minutos // 60)
        minutos = int(total_minutos % 60)
        return f"{horas:02d}:{minutos:02d}", total_minutos
    except:
        return "Erro", 0.0

# Função para transformar minutos em formato HH:MM de texto
def formatar_minutos(minutos):
    if pd.isna(minutos) or minutos <= 0:
        return "00:00"
    h = int(minutos // 60)
    m = int(minutos % 60)
    return f"{h:02d}:{m:02d}"

# Função para gerar o arquivo Excel estilizado nativamente em memória
def gerar_excel_profissional(df):
    output = io.BytesIO()
    wb = openpyxl.Workbook()
    
    # Cores (Tema Azul Corporativo)
    HEADER_FILL = PatternFill(start_color="2C4D6F", end_color="2C4D6F", fill_type="solid")
    ZEBRA_FILL = PatternFill(start_color="F4F7FA", end_color="F4F7FA", fill_type="solid")
    ACCENT_FILL = PatternFill(start_color="E6EDF5", end_color="E6EDF5", fill_type="solid")
    
    FONT_TITLE = Font(name="Segoe UI", size=16, bold=True, color="2C4D6F")
    FONT_SECTION = Font(name="Segoe UI", size=12, bold=True, color="2C4D6F")
    FONT_HEADER = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    FONT_BODY = Font(name="Segoe UI", size=10)
    
    THIN_BORDER = Border(left=Side(style='thin', color='E0E0E0'), right=Side(style='thin', color='E0E0E0'),
                         top=Side(style='thin', color='E0E0E0'), bottom=Side(style='thin', color='E0E0E0'))
    
    # --- ABA 1: DASHBOARD ---
    ws_dash = wb.active
    ws_dash.title = "Dashboard"
    ws_dash.views.sheetView[0].showGridLines = True
    
    ws_dash.merge_cells("A1:G1")
    ws_dash["A1"] = "RELATÓRIO DE CONTROLO OPERACIONAL"
    ws_dash["A1"].font = FONT_TITLE
    ws_dash["A1"].alignment = Alignment(horizontal="center", vertical="center")
    
    # KPIs Rápidos
    kpis = [
        ("Total Viagens", len(df), "A3"),
        ("Peso Total (kg)", df['peso_nota'].sum(), "C3"),
        ("Tempo Médio Pátio", formatar_minutos(df['minutos_permanencia'].mean()), "E3")
    ]
    for title, val, cell_pos in kpis:
        ws_dash[cell_pos] = title
        ws_dash[cell_pos].font = Font(name="Segoe UI", size=9, bold=True, color="555555")
        ws_dash[cell_pos].fill = ACCENT_FILL
        
        val_cell = cell_pos[0] + str(int(cell_pos[1])+1)
        ws_dash[val_cell] = val
        ws_dash[val_cell].font = Font(name="Segoe UI", size=12, bold=True)
        ws_dash[val_cell].border = THIN_BORDER
        
    # Tabela 1: Produção Diária
    ws_dash["A7"] = "PRODUÇÃO POR DIA"
    ws_dash["A7"].font = FONT_SECTION
    
    headers_dia = ["Data", "Viagens", "Peso Total (kg)"]
    for c_idx, h in enumerate(headers_dia, start=1):
        c = ws_dash.cell(row=8, column=c_idx, value=h)
        c.font = FONT_HEADER; c.fill = HEADER_FILL
        
    prod_dia = df.groupby('data_entrada').agg(v=('peso_nota','count'), p=('peso_nota','sum')).reset_index()
    r_idx = 9
    for _, r in prod_dia.iterrows():
        ws_dash.cell(row=r_idx, column=1, value=r['data_entrada']).alignment = Alignment(horizontal="center")
        ws_dash.cell(row=r_idx, column=2, value=r['v']).number_format = "#,##0"
        ws_dash.cell(row=r_idx, column=3, value=r['p']).number_format = "#,##0"
        for col in range(1, 4):
            ws_dash.cell(row=r_idx, column=col).font = FONT_BODY
            ws_dash.cell(row=r_idx, column=col).border = THIN_BORDER
        r_idx += 1
        
    # Gráfico de Viagens por Dia
    chart = BarChart()
    chart.type = "col"
    chart.title = "Viagens por Dia"
    chart.y_axis.title = "Qtd"
    data = Reference(ws_dash, min_col=2, min_row=8, max_row=8+len(prod_dia))
    cats = Reference(ws_dash, min_col=1, min_row=9, max_row=8+len(prod_dia))
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.width = 14; chart.height = 7
    ws_dash.add_chart(chart, "E7")

    # --- ABA 2: BASE DE DADOS ---
    ws_base = wb.create_sheet(title="Dados Cadastrados")
    ws_base.views.sheetView[0].showGridLines = True
    
    headers_base = ["Placa", "Nº Nota", "Peso (kg)", "Data Ent.", "Hora Ent.", "Data Saí.", "Hora Saí.", "Permanência"]
    for c_idx, h in enumerate(headers_base, start=1):
        c = ws_base.cell(row=1, column=c_idx, value=h)
        c.font = FONT_HEADER; c.fill = HEADER_FILL; c.alignment = Alignment(horizontal="center")
        
    for idx, r in df.iterrows():
        row_n = idx + 2
        ws_base.cell(row=row_n, column=1, value=r['placa']).alignment = Alignment(horizontal="center")
        ws_base.cell(row=row_n, column=2, value=r['numero_nota']).alignment = Alignment(horizontal="center")
        ws_base.cell(row=row_n, column=3, value=r['peso_nota']).number_format = "#,##0.00"
        ws_base.cell(row=row_n, column=4, value=r['data_entrada']).alignment = Alignment(horizontal="center")
        ws_base.cell(row=row_n, column=5, value=r['hora_entrada']).alignment = Alignment(horizontal="center")
        ws_base.cell(row=row_n, column=6, value=r['data_saida']).alignment = Alignment(horizontal="center")
        ws_base.cell(row=row_n, column=7, value=r['hora_saida']).alignment = Alignment(horizontal="center")
        ws_base.cell(row=row_n, column=8, value=r['tempo_permanencia']).alignment = Alignment(horizontal="center")
        
        fill_color = ZEBRA_FILL if row_n % 2 == 0 else PatternFill(fill_type=None)
        for col in range(1, 9):
            cell = ws_base.cell(row=row_n, column=col)
            cell.font = FONT_BODY; cell.border = THIN_BORDER
            if row_n % 2 == 0: cell.fill = fill_color
            
    # Auto ajustar colunas
    for ws in [ws_dash, ws_base]:
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = max(len(str(cell.value or '')) for cell in col)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 11)
            
    wb.save(output)
    return output.getvalue()

# --- INTERFACE (MENU POR ABAS - EXCELENTE PARA CELULAR) ---
aba1, aba2 = st.tabs(["📝 Lançar Dados", "📊 Relatórios & Dashboard"])

# --- ABA 1: FORMULÁRIO DE ENTRADA ---
with aba1:
    st.title("🚚 Novo Registro")
    with st.form(key="form_registro", clear_on_submit=True):
        placa = st.text_input("Placa do Carro:", placeholder="ABC1234").upper()
        num_nota = st.text_input("Número da Nota Fiscal:")
        peso_nota = st.number_input("Peso da Nota (kg):", min_value=0.0, step=50.0)
        
        st.markdown("**Horários**")
        c1, c2 = st.columns(2)
        with c1:
            dt_e = st.date_input("Data Entrada", datetime.now())
            hr_e = st.time_input("Hora Entrada", datetime.now().time())
        with c2:
            dt_s = st.date_input("Data Saída", datetime.now())
            hr_s = st.time_input("Hora Saída", datetime.now().time())
            
        botao_salvar = st.form_submit_button(label='Salvar')

    if botao_salvar:
        if placa and num_nota:
            h_e_str = hr_e.strftime("%H:%M")
            h_s_str = hr_s.strftime("%H:%M")
            txt_perm, min_perm = calcular_permanencia_detalhada(str(dt_e), h_e_str, str(dt_s), h_s_str)
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO registros (placa, numero_nota, peso_nota, data_entrada, hora_entrada, data_saida, hora_saida, tempo_permanencia, minutos_permanencia)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (placa, num_nota, peso_nota, str(dt_e), h_e_str, str(dt_s), h_s_str, txt_perm, min_perm))
            conn.commit()
            st.success(f"Sucesso! Veículo {placa} registrado. Tempo de Pátio: {txt_perm}")
        else:
            st.error("Preencha os campos obrigatórios (Placa e Nota)!")

# --- ABA 2: RELATÓRIOS E COMPILADOR EXCEL ---
with aba2:
    st.title("📊 Painel de Relatórios")
    
    # Puxa dados atuais do Banco SQLite
    df_atual = pd.read_sql_query("SELECT * FROM registros ORDER BY id DESC", conn)
    
    if not df_atual.empty:
        # Indicadores Visuais Rápidos na Tela do Celular
        col_kpi1, col_kpi2 = st.columns(2)
        col_kpi1.metric("Total de Viagens", len(df_atual))
        col_kpi2.metric("Peso Total (kg)", f"{df_atual['peso_nota'].sum():,.0f}")
        
        st.markdown("---")
        
        # 🟢 BOTÃO DA SOLICITAÇÃO: GERAR E BAIXAR RELATÓRIO EXCEL
        st.subheader("📥 Exportação de Relatório")
        dados_excel = gerar_excel_profissional(df_atual)
        
        st.download_button(
            label="🟢 GERAR RELATÓRIO EM EXCEL (.xlsx)",
            data=dados_excel,
            file_name=f"Relatorio_Movimentacao_Lion_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.markdown("---")
        
        # Rankings Rápidos na Tela do Celular
        st.subheader("🏆 Ranking de Carros (Mais Viagens)")
        rank_carros = df_atual.groupby('placa').size().reset_index(name='Viagens').sort_values(by='Viagens', ascending=False)
        st.dataframe(rank_carros, use_container_width=True, hide_index=True)
        
        st.subheader("⏱️ Últimos Registros na Base")
        st.dataframe(df_atual[['placa', 'numero_nota', 'peso_nota', 'tempo_permanencia']], use_container_width=True, hide_index=True)
    else:
        st.info("Insira o primeiro registro na aba ao lado para habilitar a extração de relatórios.")
