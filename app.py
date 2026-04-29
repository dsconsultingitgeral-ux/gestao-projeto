import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LUX Business Suite", layout="wide", page_icon="💎")

# CSS para Estética Dark & Moderna
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { color: #00FFC8; font-family: 'Inter', sans-serif; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #1f2235; color: white; border: 1px solid #3e4461; }
    .stButton>button:hover { border-color: #00FFC8; color: #00FFC8; }
    div[data-testid="metric-container"] { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- LIGAÇÃO À BASE DE DADOS ---
# SUBSTITUI AQUI PELO TEU DIRECT_URL DO SUPABASE
DB_URL = "postgresql://postgres.mhckrjhvfeckdprntirb:Digital*Solutions!IT26@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"
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
    st.markdown("<h1 style='text-align: center; color: #00FFC8;'>💎 LUX MANAGER LOGIN</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("Utilizador")
            password = st.text_input("Palavra-passe", type="password")
            if st.form_submit_button("Aceder ao Sistema"):
                res = run_query("SELECT * FROM users WHERE username = :u AND password = :p", {"u": user, "p": password}).fetchone()
                if res:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Credenciais incorretas.")

# --- INTERFACE PRINCIPAL ---
else:
    st.sidebar.markdown("<h2 style='color: #00FFC8;'>💎 LUX Suite</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "👥 Clientes", "🏗️ Projetos", "📄 Relatórios"])
    
    if st.sidebar.button("Terminar Sessão"):
        st.session_state.logged_in = False
        st.rerun()

    # --- DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("📊 Painel de Controlo Executivo")
        df_p = pd.read_sql("SELECT * FROM projetos", engine)
        
        if not df_p.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Projetos Totais", len(df_p))
            c2.metric("Ativos", len(df_p[df_p['estado'] != 'Concluído']))
            total_orc = df_p['orcamento'].sum()
            c3.metric("Faturação Total", f"{total_orc:,.2f} €")
            pago = df_p['valor_pago'].sum()
            c4.metric("Por Receber", f"{(total_orc - pago):,.2f} €", delta_color="inverse")
            
            st.subheader("Análise Financeira por Projeto")
            st.bar_chart(df_p.set_index('nome_projeto')[['orcamento', 'valor_pago']])
        else:
            st.info("Bem-vindo! Comece por registar clientes e projetos para ver as métricas.")

    # --- CLIENTES ---
    elif menu == "👥 Clientes":
        st.title("Gestão de Clientes")
        with st.expander("➕ Adicionar Novo Cliente"):
            with st.form("new_client"):
                nome = st.text_input("Nome Comercial/Cliente")
                email = st.text_input("Email de Contacto")
                tel = st.text_input("Telefone")
                doc = st.text_input("NIF / Documento")
                if st.form_submit_button("Registar Cliente"):
                    run_query("INSERT INTO clientes (nome_cliente, email, telefone, num_documento) VALUES (:n, :e, :t, :d)", 
                             {"n":nome, "e":email, "t":tel, "d":doc})
                    st.success("Cliente registado com sucesso!")
                    st.rerun()
        
        df_c = pd.read_sql("SELECT id, nome_cliente, email, telefone FROM clientes", engine)
        st.dataframe(df_c, use_container_width=True)

    # --- PROJETOS ---
    elif menu == "🏗️ Projetos":
        st.title("Gestão de Projetos e Oficinas")
        df_cl = pd.read_sql("SELECT id, nome_cliente FROM clientes", engine)
        
        with st.expander("🚀 Lançar Novo Projeto"):
            if not df_cl.empty:
                with st.form("new_project"):
                    p_nome = st.text_input("Nome do Projeto/Serviço")
                    p_cli = st.selectbox("Selecionar Cliente", options=df_cl['nome_cliente'].tolist())
                    col_a, col_b = st.columns(2)
                    p_orc = col_a.number_input("Orçamento (€)", min_value=0.0)
                    p_est = col_b.selectbox("Estado", ["Por começar", "Em desenvolvimento", "Concluído"])
                    if st.form_submit_button("Criar Projeto"):
                        cli_id = int(df_cl[df_cl['nome_cliente'] == p_cli]['id'].values[0])
                        run_query("INSERT INTO projetos (nome_projeto, cliente_id, orcamento, estado) VALUES (:n, :c, :o, :e)",
                                 {"n":p_nome, "c":cli_id, "o":p_orc, "e":p_est})
                        st.success("Projeto lançado!")
                        st.rerun()
            else:
                st.warning("Crie primeiro um cliente antes de lançar um projeto.")

        st.subheader("Trabalhos Atuais")
        df_p_view = pd.read_sql("""
            SELECT p.id, p.nome_projeto, c.nome_cliente, p.orcamento, p.estado 
            FROM projetos p JOIN clientes c ON p.cliente_id = c.id
        """, engine)
        st.table(df_p_view)

    # --- RELATÓRIOS ---
    elif menu == "📄 Relatórios":
        st.title("Exportação de PDF")
        df_p_all = pd.read_sql("SELECT id, nome_projeto FROM projetos", engine)
        target_p = st.selectbox("Escolha o Projeto para Gerar Relatório", options=df_p_all['nome_projeto'].tolist())
        
        if st.button("Gerar PDF"):
            # Lógica simplificada de PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, f"Relatorio de Projeto - LUX Manager", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.ln(10)
            pdf.cell(200, 10, f"Projeto: {target_p}", ln=True)
            pdf.cell(200, 10, f"Data de Emissao: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
            
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button(label="Descarregar Relatório PDF", data=pdf_output, file_name=f"Relatorio_{target_p}.pdf", mime="application/pdf")
