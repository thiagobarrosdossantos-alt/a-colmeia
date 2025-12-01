#!/usr/bin/env python3
import os
import json
from vertexai.generative_models import GenerativeModel
from anthropic import AnthropicVertex
import vertexai
from github import Github

# ================== CONFIG ==================
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'gen-lang-client-0394737170')
LOCATION = "us-central1"
MODEL = "claude-3-5-sonnet-v2@20241022"

# Inicializar Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)
claude = GenerativeModel(MODEL)

# GitHub
g = Github(os.getenv('GITHUB_TOKEN'))

# ================== FUNÇÕES ==================

def ask_claude(prompt: str) -> str:
    """Pergunta para o Claude"""
    try:
        message = client.messages.create(
            max_tokens=4096,
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        return message.content[0].text
    except Exception as e:
        return f"Error: {e}"

def review_pull_request():
    """Revisa Pull Request"""
    repo_name = os.getenv('GITHUB_REPOSITORY')
    pr_number = os.getenv('PR_NUMBER')
    
    if not repo_name or not pr_number:
        print("⚠️ Variáveis de ambiente ausentes")
        return
    
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(int(pr_number))
    
    # Pegar arquivos modificados
    files = pr.get_files()
    
    review_comments = []
    for file in files:
        if file.filename.endswith(('.py', '.js', '.ts', '.tsx', '.jsx')):
            prompt = f"""
Você é o revisor de código de A Colmeia - Sistema de Agentes de IA.

Analise este arquivo modificado:
Arquivo: {file.filename}
Mudanças: +{file.additions} -{file.deletions}

Forneça análise DIRETA e PRÁTICA:
- Erros ou bugs críticos
- Problemas de segurança
- Melhorias de código
- Comandos exatos

Seja DIRETO.
"""
            analysis = ask_claude(prompt)
            review_comments.append(f"**📝 {file.filename}**\n\n{analysis}")
    
    # Postar review
    if review_comments:
        comment_body = "\n\n---\n\n".join(review_comments)
        pr.create_issue_comment(f"""
🤖 **Revisão Automática via Vertex AI - Claude Opus 4.5**

{comment_body}

---

*Análise automática via A Colmeia - Sistema de Agentes de IA*
""")
        print("✅ Revisão postada!")
    else:
        print("⚠️ Nenhum arquivo para revisar")

def respond_to_issue():
    """Responde issue"""
    repo_name = os.getenv('GITHUB_REPOSITORY')
    issue_number = os.getenv('ISSUE_NUMBER')
    
    if not repo_name or not issue_number:
        print("⚠️ Variáveis ausentes")
        return
    
    repo = g.get_repo(repo_name)
    issue = repo.get_issue(int(issue_number))
    
    prompt = f"""
Issue: {issue.title}

{issue.body}

Você é Claude Worker - Agente Autônomo de A Colmeia.

Forneça resposta DIRETA e PRÁTICA com comandos exatos se aplicável.
"""
    
    response = ask_claude(prompt)
    
    issue.create_comment(f"""
🤖 **Resposta Automática - Claude Opus 4.5**

{response}

---

*Resposta automática via A Colmeia*
""")
    print("✅ Resposta postada!")

# ================== MAIN ==================

if __name__ == "__main__":
    event_name = os.getenv('GITHUB_EVENT_NAME')
    
    print(f"🚀 Claude Worker iniciado - Evento: {event_name}")
    
    if event_name == 'pull_request':
        review_pull_request()
    elif event_name in ['issues', 'issue_comment']:
        respond_to_issue()
    else:
        print(f"⚠️ Evento não suportado: {event_name}")
    
    print("✅ Claude Worker finalizado")
