import sys
import os
from sqlalchemy import create_engine, text

# --- CONFIGURAÇÃO DE SEGURANÇA (VARIÁVEIS AMBIENTE) ---
DB_URL = os.environ.get("DB_URL")
TARGET_USER = os.environ.get("DB_UPDATE_USER")
TARGET_PASS = os.environ.get("DB_UPDATE_PASS")

def run_daily_update():
    print("A iniciar o ping diário ao Supabase...")
    
    # Validação rápida de segurança antes de tentar a ligação
    if not all([DB_URL, TARGET_USER, TARGET_PASS]):
        print("❌ Erro Crítico: Faltam variáveis de ambiente obrigatórias (DB_URL, DB_UPDATE_USER ou DB_UPDATE_PASS).")
        sys.exit(1)
        
    engine = create_engine(DB_URL)
    
    # Query parametrizada de forma segura
    query = """
        UPDATE users 
        SET password = :p 
        WHERE username = :u;
    """
    
    try:
        with engine.connect() as conn:
            # Executa a query injetando de forma segura as variáveis secretas
            result = conn.execute(text(query), {"u": TARGET_USER, "p": TARGET_PASS})
            conn.commit()
            
            if result.rowcount > 0:
                print(f"Sucesso! O utilizador '{TARGET_USER}' foi atualizado. Supabase acordado.")
            else:
                print(f"Ligação estabelecida com sucesso, mas o utilizador '{TARGET_USER}' não foi encontrado na tabela.")
                
    except Exception as e:
        print(f"Erro crítico na ligação à Base de Dados: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_daily_update()
