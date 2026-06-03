import os
import sys
from sqlalchemy import create_engine, text

# Carrega as variáveis de ambiente com os dados confidenciais
DB_URL = os.environ.get("SUPABASE_DB_URL")
TARGET_USER = os.environ.get("DB_TARGET_USER")
TARGET_PASSWORD = os.environ.get("DB_TARGET_PASSWORD")

# Validação para garantir que todas as variáveis existem
if not all([DB_URL, TARGET_USER, TARGET_PASSWORD]):
    print("Erro: Uma ou mais variáveis de ambiente (SUPABASE_DB_URL, DB_TARGET_USER, DB_TARGET_PASSWORD) não foram configuradas.")
    sys.exit(1)

def run_daily_update():
    print("A iniciar o ping diário ao Supabase...")
    engine = create_engine(DB_URL)
    
    # Query para atualizar o utilizador
    query = """
        UPDATE users 
        SET password = :p 
        WHERE username = :u;
    """
    
    try:
        with engine.connect() as conn:
            # Substituição das strings fixas pelas variáveis carregadas do ambiente
            result = conn.execute(text(query), {"u": TARGET_USER, "p": TARGET_PASSWORD})
            conn.commit()
            
            if result.rowcount > 0:
                print(f"Sucesso! O utilizador '{TARGET_USER}' foi atualizado. Supabase acordado.")
            else:
                print(f"Ligação estabelecida com sucesso, mas o utilizador '{TARGET_USER}' não foi encontrado na tabela.")
                
    except Exception as e:
        print(f"Erro crítico na ligação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_daily_update()
