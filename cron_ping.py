import sys
from sqlalchemy import create_engine, text

# Link direto inserido no código
DB_URL = "postgresql://postgres.mhckrjhvfeckdprntirb:Digital*Solutions!IT26@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

def run_daily_update():
    print("A iniciar o ping diário ao Supabase...")
    engine = create_engine(DB_URL)
    
    # Query para atualizar o utilizador 'test' com a pass 'ds12345'
    query = """
        UPDATE users 
        SET password = :p 
        WHERE username = :u;
    """
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), {"u": "test", "p": "ds12345"})
            conn.commit()
            
            if result.rowcount > 0:
                print("Sucesso! O utilizador 'test' foi atualizado. Supabase acordado.")
            else:
                print("Ligação estabelecida com sucesso, mas o utilizador 'test' não foi encontrado na tabela.")
                
    except Exception as e:
        print(f"Erro crítico na ligação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_daily_update()
