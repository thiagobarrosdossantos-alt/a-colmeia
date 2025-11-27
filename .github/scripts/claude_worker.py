#!/usr/bin/env python3
import os
from vertexai.generative_models import GenerativeModel
import vertexai
from github import Github

PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'gen-lang-client-0394737170')
LOCATION = "us-central1"
MODEL = "claude-3-5-sonnet-v2@20241022"

vertexai.init(project=PROJECT_ID, location=LOCATION)
claude = GenerativeModel(MODEL)
g = Github(os.getenv('GITHUB_TOKEN'))

def ask_claude(prompt: str) -> str:
    response = claude.generate_content(prompt)
    return response.text

def review_pull_request():
    repo_name = os.getenv('GITHUB_REPOSITORY')
    pr_number = os.getenv('PR_NUMBER')
    
    if not repo_name or not pr_number:
        print("⚠️ Variáveis ausentes")
        return
    
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(int(pr_number))
    files = pr.get_files()
    
    review_comments = []
    for file in files:
        if file.filename.endswith(('.py', '.js', '.ts', '.tsx', '.jsx')):
            prompt = f"Analise código: {file.filename}\n+{file.additions} -{file.deletions}\nSeja direto."
            analysis = ask_claude(prompt)
            review_comments.append(f"**{file.filename}**\n\n{analysis}")
    
    if review_comments:
        pr.create_issue_comment(f"🤖 **Claude Opus 4.5**\n\n" + "\n\n".join(review_comments))
        print("✅ Review postado!")

if __name__ == "__main__":
    event_name = os.getenv('GITHUB_EVENT_NAME')
    print(f"🚀 Evento: {event_name}")
    
    if event_name == 'pull_request':
        review_pull_request()
    
    print("✅ Finalizado")
