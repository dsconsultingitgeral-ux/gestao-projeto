import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from fpdf import FPDF
from datetime import datetime
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="DS Business Intelligence", layout="wide", page_icon="📈")

# CSS para Estética Empresarial Dark
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { color: #00d4ff; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { width: 100%; border-radius: 4px; background-color: #161b22; color: white; border: 1px solid #30363d; height: 3em; }
    .stButton>button:hover { border-color: #00d4ff; color: #00d4ff; }
    div[data-testid="metric-container"] { background-color: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- LIGAÇÃO À BASE DE DADOS (CORRIGIDA PARA STREAMLIT CLOUD) ---
DB_URL = None

# 1. Tenta obter a variável através do método nativo do Streamlit Cloud
if "DB_URL" in st.secrets:
    DB_URL = st.secrets["DB_URL"]
# 2. Se não encontrar, tenta obter das variáveis de ambiente padrão (ex: GitHub/Local)
else:
    DB_URL = os.environ.get("DB_URL")

# Se mesmo assim não encontrar, exibe uma mensagem amigável com instruções claras
if not DB_URL:
    st.error("❌ Erro: A variável 'DB_URL' não foi configurada nos Secrets do Streamlit.")
    st.markdown("""
    ### 🛠️ Como resolver isto no painel do Streamlit:
    1. Vá ao seu painel do **Streamlit Community Cloud**.
    2. Junto à sua app `gestao-projeto-digital-solutions`, clique nos **três pontos (...)** e escolha **Settings**.
    3. No menu esquerdo, clique em **Secrets**.
    4. Cole a sua variável exatamente neste formato TOML:
    ```toml
    DB_URL = "postgresql://postgres.mhckrjhvfeckdprntirb:Digital*Solutions!IT26@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"
    ```
    5. Clique em **Save**. A aplicação vai reiniciar e funcionar automaticamente!
    """)
    st.stop()

# Inicializa o motor de ligação
engine = create_engine(DB_URL)

def run_query(query, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(query), params) if params else conn.execute(text(query))
        conn.commit()
        return result

# --- LÓGICA DE LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #00d4ff;'>CORPORATE LOGIN</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8b949e;'>DS Business Intelligence Solutions</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.2,1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("Utilizador")
            password = st.text_input("Palavra-passe", type="password")
            if st.form_submit_button("Entrar"):
                try:
                    res = run_query("SELECT * FROM users WHERE username = :u AND password = :p", {"u": user, "p": password}).fetchone()
                    if res:
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Falha na autenticação.")
                except Exception as db_err:
                    st.error(f"Erro ao consultar a base de dados. Verifique a tabela 'users'. Detalhe: {db_err}")

# --- INTERFACE PRINCIPAL ---
else:
    st.sidebar.markdown("<h2 style='color: #00d4ff;'>DS Intelligence</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("Consola de Gestão", ["📊 Dashboard", "👥 Gestão de Clientes", "🏗️ Gestão de Projetos", "📄 Relatórios Executivos"])
    
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

    # --- DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("📊 Indicadores de Performance")
        df_p = pd.read_sql("SELECT * FROM projetos", engine)
        
        if not df_p.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Projetos em Carteira", len(df_p))
            c2.metric("Projetos Ativos", len(df_p[df_p['estado'] != 'Concluído']))
            total_orc = df_p['orcamento'].sum()
            c3.metric("Volume de Negócios", f"{total_orc:,.2f} €")
            pago = df_p['valor_pago'].sum()
            c4.metric("Capital a Receber", f"{(total_orc - pago):,.2f} €")
            
            st.subheader("Performance Financeira por Conta")
            st.bar_chart(df_p.set_index('nome_projeto')[['orcamento', 'valor_pago']])
        else:
            st.info("Sistema pronto. Aguardando registo de dados.")

    # --- CLIENTES ---
    elif menu == "👥 Gestão de Clientes":
        st.title("👥 Base de Dados de Clientes")
        with st.expander("➕ Registar Nova Entidade"):
            with st.form("new_client"):
                nome = st.text_input("Nome da Entidade / Cliente")
                email = st.text_input("Email Corporativo")
                tel = st.text_input("Contacto Telefónico")
                doc = st.text_input("NIF / Identificação Fiscal")
                if st.form_submit_button("Confirmar Registo"):
                    run_query("INSERT INTO clientes (nome_cliente, email, telefone, num_documento) VALUES (:n, :e, :t, :d)", 
                               {"n":nome, "e":email, "t":tel, "d":doc})
                    st.success("Entidade registada com sucesso.")
                    st.rerun()
        
        df_c = pd.read_sql("SELECT nome_cliente, email, telefone, num_documento FROM clientes", engine)
        st.dataframe(df_c, use_container_width=True)

    # --- PROJETOS ---
    elif menu == "🏗️ Gestão de Projetos":
        st.title("🏗️ Controlo de Projetos")
        
        # Secção 1: Criar Novo
        with st.expander("🚀 Lançar Novo Projeto"):
            df_cl = pd.read_sql("SELECT id, nome_cliente FROM clientes", engine)
            if not df_cl.empty:
                with st.form("new_project"):
                    p_nome = st.text_input("Designação do Projeto")
                    p_cli = st.selectbox("Cliente Associado", options=df_cl['nome_cliente'].tolist())
                    col_a, col_b = st.columns(2)
                    p_orc = col_a.number_input("Orçamento Estimado (€)", min_value=0.0)
                    p_est = col_b.selectbox("Estado Inicial", ["Por começar", "Em desenvolvimento", "Concluído"])
                    col_c, col_d = st.columns(2)
                    p_ini = col_c.date_input("Data de Início")
                    p_fim = col_d.date_input("Previsão de Conclusão")
                    if st.form_submit_button("Validar Projeto"):
                        cli_id = int(df_cl[df_cl['nome_cliente'] == p_cli]['id'].values[0])
                        run_query("INSERT INTO projetos (nome_projeto, cliente_id, orcamento, estado, data_inicio, data_fim, valor_pago) VALUES (:n, :c, :o, :e, :di, :df, 0)",
                                  {"n":p_nome, "c":cli_id, "o":p_orc, "e":p_est, "di":p_ini, "df":p_fim})
                        st.success("Projeto integrado no sistema.")
                        st.rerun()
            else:
                st.warning("Necessário registar um cliente antes de iniciar projetos.")

        # Secção 2: Editar Projeto Existente
        st.markdown("---")
        st.subheader("📝 Atualizar Estado de Projeto")
        df_edit = pd.read_sql("SELECT id, nome_projeto, estado, valor_pago, orcamento FROM projetos", engine)
        if not df_edit.empty:
            with st.form("edit_project"):
                projeto_para_editar = st.selectbox("Selecionar Projeto para Modificar", options=df_edit['nome_projeto'].tolist())
                dados_atuais = df_edit[df_edit['nome_projeto'] == projeto_para_editar].iloc[0]
                
                col1, col2 = st.columns(2)
                novo_estado = col1.selectbox("Novo Estado", ["Por começar", "Em desenvolvimento", "Concluído"], index=["Por começar", "Em development", "Concluído"].index(dados_atuais['estado']))
                novo_pago = col2.number_input("Valor Liquidado até à data (€)", min_value=0.0, value=float(dados_atuais['valor_pago']))
                
                if st.form_submit_button("Guardar Alterações"):
                    run_query("UPDATE projetos SET estado = :e, valor_pago = :v WHERE id = :id", 
                               {"e": novo_estado, "v": novo_pago, "id": int(dados_atuais['id'])})
                    st.success("Dados atualizados.")
                    st.rerun()

        st.markdown("---")
        st.subheader("📋 Mapa Geral de Trabalhos")
        df_p_view = pd.read_sql("""
            SELECT p.nome_projeto, c.nome_cliente, p.orcamento, p.valor_pago, p.estado, p.data_inicio, p.data_fim
            FROM projetos p JOIN clientes c ON p.cliente_id = c.id
        """, engine)
        st.dataframe(df_p_view, use_container_width=True)

    # --- RELATÓRIOS ---
    elif menu == "📄 Relatórios Executivos":
        st.title("📄 Geração de Relatórios")
        df_p_all = pd.read_sql("""
            SELECT p.*, c.nome_cliente 
            FROM projetos p JOIN clientes c ON p.cliente_id = c.id
        """, engine)
        
        if not df_p_all.empty:
            target_p_name = st.selectbox("Escolha o Projeto", options=df_p_all['nome_projeto'].tolist())
            proj = df_p_all[df_p_all['nome_projeto'] == target_p_name].iloc[0]
            
            if st.button("Gerar Relatório de Status"):
                pdf = FPDF()
                pdf.add_page()
                # Cabeçalho
                pdf.set_font("Arial", 'B', 20)
                pdf.set_text_color(0, 100, 200)
                pdf.cell(200, 15, "DS BUSINESS INTELLIGENCE", ln=True, align='L')
                pdf.set_draw_color(0, 100, 200)
                pdf.line(10, 25, 200, 25)
                
                # Conteúdo
                pdf.ln(10)
                pdf.set_font("Arial", 'B', 14)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(200, 10, f"RELATORIO EXECUTIVO: {proj['nome_projeto']}", ln=True)
                
                pdf.set_font("Arial", size=11)
                pdf.ln(5)
                pdf.cell(200, 8, f"Cliente: {proj['nome_cliente']}", ln=True)
                pdf.cell(200, 8, f"Status Atual: {proj['estado'].upper()}", ln=True)
                pdf.cell(200, 8, f"Periodo: {proj['data_inicio']} ate {proj['data_fim']}", ln=True)
                
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(200, 10, "RESUMO FINANCEIRO", ln=True)
                pdf.set_font("Arial", size=11)
                pdf.cell(200, 8, f"Orcamento Total: {proj['orcamento']:.2f} EUR", ln=True)
                pdf.cell(200, 8, f"Valor Liquidado: {proj['valor_pago']:.2f} EUR", ln=True)
                pdf.cell(200, 8, f"Saldo Devedor: {(proj['orcamento'] - proj['valor_pago']):.2f} EUR", ln=True)
                
                pdf.ln(10)
                pdf.set_font("Arial", 'I', 9)
                pdf.cell(200, 10, f"Documento emitido automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
                
                pdf_output = pdf.output(dest='S').encode('latin-1')
                st.download_button(label="📥 Descarregar PDF", data=pdf_output, file_name=f"Relatorio_{proj['nome_projeto']}.pdf", mime="application/pdf")
        else:
            st.info("Sem dados disponíveis para gerar relatórios.")
