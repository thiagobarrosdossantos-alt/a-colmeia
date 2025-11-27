#!/usr/bin/env python3
import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel
from github import Github

# ==================== CONFIG ====================
PROJECT_ID = os.getenv('GCP_PROJECT_ID')
LOCATION = 'us-central1'
MODEL = 'claude-opus-4-5@20251101'

# Inicializar
vertexai.init(project=PROJECT_ID, location=LOCATION)
claude = GenerativeModel(MODEL)

# GitHub
g = Github(os.getenv('GITHUB_TOKEN'))
repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))

# ==================== FUNÇÕES ====================

def ask_claude(prompt: str) -> str:
    """Pergunta para o Claude"""
    response = claude.generate_content(prompt)
    return response.text

def review_pull_request():
    """Revisa Pull Request"""
    event = json.loads(os.getenv('GITHUB_EVENT_PATH', '{}'))
    
    if 'pull_request' not in event:
        return
    
    pr_number = event['pull_request']['number']
    pr = repo.get_pull(pr_number)
    
    # Pegar arquivos modificados
    files = pr.get_files()
    
    review_comments = []
    
    for file in files:
        if file.filename.endswith(('.py', '.js', '.ts', '.tsx', '.jsx', '.md')):
            
            prompt = f"""
Você é o Arquiteto da A Colmeia - sistema de desenvolvimento autônomo.

Revise este código do projeto A Colmeia:

**Arquivo**: {file.filename}
**Mudanças**:
{file.patch if file.patch else "Arquivo novo"}
Forneça análise DIRETA e PRÁTICA:

1. **Qualidade**: Avalie código (0-10)
2. **Problemas**: Liste bugs/vulnerabilidades
3. **Otimizações**: Melhorias específicas de performance
4. **Padrões A Colmeia**: Verificar conformidade com:
   - TypeScript strict mode
   - Error handling completo
   - Validação Zod
   - Comentários JSDoc
5. **Ação Recomendada**: APROVAR / SOLICITAR MUDANÇAS / COMENTAR

Seja técnico e direto. Sem enrolação.
"""
            
            analysis = ask_claude(prompt)
            
            review_comments.append(f"""
## 🤖 Claude Opus 4.5 - Análise de {file.filename}

{analysis}

---
*Análise automática via Vertex AI*
""")
    
    # Postar review
    if review_comments:
        pr.create_issue_comment('\n\n'.join(review_comments))
        print(f"✅ Review completo no PR #{pr_number}")

def respond_to_issue():
    """Responde Issues"""
    event = json.loads(os.getenv('GITHUB_EVENT_PATH', '{}'))
    
    if 'issue' not in event:
        return
    
    issue = repo.get_issue(event['issue']['number'])
    
    # Só responde se tiver label 'claude' ou 'help'
    labels = [l.name for l in issue.labels]
    if not any(l in labels for l in ['claude', 'help', 'question']):
        return
    
    prompt = f"""
Você é o Comandante da A Colmeia.

**Issue**: {issue.title}
**Descrição**:
{issue.body}

Forneça resposta TÉCNICA e ACIONÁVEL:
- Solução direta
- Código exemplo se aplicável
- Próximos passos concretos

Seja prático. Foco em resolver.
"""
    
    response = ask_claude(prompt)
    
    issue.create_comment(f"""
## 🐝 Comandante A Colmeia - Claude Opus 4.5

{response}

---
*Resposta automática via Vertex AI - Para desativar, remova a label 'claude'*
""")
    
    print(f"✅ Respondido issue #{issue.number}")

# ==================== MAIN ====================

if __name__ == "__main__":
    event_name = os.getenv('GITHUB_EVENT_NAME')
    
    print(f"🐝 Claude Worker iniciado - Evento: {event_name}")
    
    if event_name == 'pull_request':
        review_pull_request()
    elif event_name in ['issues', 'issue_comment']:
        respond_to_issue()
    
    print("✅ Claude Worker finalizado")
