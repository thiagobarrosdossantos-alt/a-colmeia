import os
from openai import OpenAI

# =================================================================
# 1. Configurações e Autenticação
# =================================================================

MODEL_NAME = 'Gpt-5.1-2025-11-13' # ID de modelo EXATO solicitado
API_KEY_ENV = os.getenv("OPENAI_API_KEY")

try:
    # O cliente OpenAI lê a chave automaticamente da variável OPENAI_API_KEY
    client = OpenAI(api_key=API_KEY_ENV)
except Exception as e:
    print(f"Erro ao inicializar o cliente OpenAI: {e}")
    exit()


def chamar_chatgpt(prompt_usuario: str):
    """
    Função para chamar o modelo GPT-5.1-2025-11-13 da OpenAI.
    """
    
    print(f"\n--- Chamando o Modelo: {MODEL_NAME} ---")

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt_usuario}
            ]
        )
        return response.choices[0].message.content
        
    except Exception as e:
        # ATENÇÃO: Se ocorrer um erro 404, a solução é mudar o MODEL_NAME para 'gpt-5.1'
        return f"Erro ao chamar o ChatGPT: {e}. Verifique se a chave OPENAI_API_KEY está correta."


# --- EXEMPLO DE USO ---
if __name__ == "__main__":
    prompt_para_ia = "Como Personal Trainer, dê uma análise comparativa dos pontos fortes de GPT-5.1-2025-11-13, Claude 4.5 e Gemini 2.5 Pro para a criação de rotinas de treino dinâmicas."
    
    resposta_chatgpt = chamar_chatgpt(prompt_usuario=prompt_para_ia)
    
    print("\n" + "="*50)
    print(f"\n[RESPOSTA - {MODEL_NAME}]:")
    print(resposta_chatgpt)