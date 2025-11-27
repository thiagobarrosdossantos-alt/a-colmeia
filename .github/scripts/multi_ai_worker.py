import os
import sys
import asyncio
import time
import random
import vertexai
from vertexai.generative_models import GenerativeModel, HarmCategory, HarmBlockThreshold
from anthropic import AnthropicVertex
from github import Github

# Configuration
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'gen-lang-client-0394737170')
LOCATION = "us-central1"

# Model definitions
MODEL_CLAUDE_NAME = "claude-3-opus@20240229" # Correct Vertex AI Model ID for Claude 3 Opus
# Note: User requested "claude-opus-4-20250514", but that looks like a placeholder or unreleased model.
# I will try to use the requested name first, but use AnthropicVertex which handles Claude on Vertex.
# If the user specifically said "claude-opus-4-20250514" I will pass that to the client.
REQUESTED_CLAUDE_MODEL = "claude-opus-4-20250514"

MODEL_GEMINI_NAME = "gemini-3-pro-preview" # User requested
MODEL_GEMINI_FALLBACK = "gemini-1.5-pro-001"

# Jules Engine
MODEL_JULES_ENGINE = "gemini-1.5-pro-001" # Reliable engine for DevOps logic

def get_file_content(repo, file):
    """Fetches the content of a file from the repo."""
    try:
        content = repo.get_contents(file.filename, ref=file.sha).decoded_content.decode('utf-8')
        return content
    except Exception as e:
        print(f"Error reading {file.filename}: {e}")
        return ""

async def call_claude_vertex(model_name, system_prompt, user_content):
    """
    Calls Claude on Vertex AI using AnthropicVertex SDK.
    """
    client = AnthropicVertex(region=LOCATION, project_id=PROJECT_ID)

    # Retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                max_tokens=4096,
                model=model_name, # Try user model, might need fallback to "claude-3-opus@20240229"
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_content,
                    }
                ],
            )
            return message.content[0].text
        except Exception as e:
            print(f"⚠️ [Claude] Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.random()
                await asyncio.sleep(sleep_time)
            else:
                # Fallback to standard Opus ID if custom one fails
                if model_name != "claude-3-opus@20240229" and ("404" in str(e) or "not found" in str(e).lower()):
                    print("⚠️ [Claude] Requested model not found. Falling back to standard Claude 3 Opus.")
                    return await call_claude_vertex("claude-3-opus@20240229", system_prompt, user_content)
                raise e

async def call_gemini_vertex(model_name, system_prompt, user_content):
    """
    Calls Gemini on Vertex AI.
    """
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # Retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            model = GenerativeModel(
                model_name,
                system_instruction=[system_prompt]
            )

            generation_config = {
                "max_output_tokens": 8192,
                "temperature": 0.2,
            }

            # Safety settings
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            }

            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: model.generate_content(
                    user_content,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    stream=False
                )
            )
            return response.text
        except Exception as e:
            print(f"⚠️ [Gemini] Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.random()
                await asyncio.sleep(sleep_time)
            else:
                # Fallback
                if model_name != MODEL_GEMINI_FALLBACK and ("404" in str(e) or "not found" in str(e).lower()):
                     print(f"⚠️ [Gemini] Model {model_name} not found. Falling back to {MODEL_GEMINI_FALLBACK}.")
                     return await call_gemini_vertex(MODEL_GEMINI_FALLBACK, system_prompt, user_content)
                raise e

async def analyze_with_model(agent_name: str, model_name: str, system_prompt: str, user_content: str):
    """
    Wrapper to select correct SDK based on agent/model.
    """
    print(f"🤖 [{agent_name}] Starting analysis with {model_name}...")

    try:
        if "claude" in agent_name.lower() or "claude" in model_name.lower():
            return await call_claude_vertex(model_name, system_prompt, user_content)
        else:
            return await call_gemini_vertex(model_name, system_prompt, user_content)
    except Exception as e:
        print(f"❌ [{agent_name}] Failed: {e}")
        return f"Error executing analysis: {str(e)}"

def format_comment(agent_name: str, analysis: str) -> str:
    return f"""
🤖 **{agent_name} - Análise Automática**

{analysis}

---
*Análise via A Colmeia - Sistema Autônomo de Agentes IA*
"""

async def main():
    # 1. Setup GitHub
    github_token = os.getenv('GITHUB_TOKEN')
    repo_name = os.getenv('GITHUB_REPOSITORY')
    pr_number = os.getenv('PR_NUMBER')

    if not github_token or not repo_name or not pr_number:
        print("Error: Missing Environment Variables (GITHUB_TOKEN, REPO, PR_NUMBER).")
        sys.exit(1)

    g = Github(github_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(int(pr_number))

    print(f"Processing PR #{pr_number} in {repo_name}...")

    # 2. Collect Context (Files)
    files = pr.get_files()
    code_context = ""
    MAX_CHARS = 100000

    for file in files:
        if file.filename.endswith(('.py', '.js', '.ts', '.tsx', '.jsx', '.yml', '.yaml', '.json', '.md', '.html', '.css', '.java', '.go')):
            if file.status == "removed":
                continue

            content = file.patch if file.patch else "Binary or Large file changed."
            code_context += f"\n\n--- File: {file.filename} ---\n"
            code_context += content

            if len(code_context) > MAX_CHARS:
                code_context += "\n\n[... Truncated due to size ...]"
                break

    if not code_context.strip():
        print("No analyzable changes found.")
        sys.exit(0)

    # 3. Define Prompts
    prompt_claude = """
    Você é Claude Opus 4.5, especialista em Arquitetura de Software e Segurança.
    Analise o código fornecido (diffs do PR) focando EXCLUSIVAMENTE em:
    1. Padrões de Arquitetura (SOLID, Clean Code, Design Patterns)
    2. Segurança (Vulnerabilidades, exposição de dados, inputs não sanitizados)
    Seja conciso. Liste Pontos Principais.
    """

    prompt_gemini = """
    Você é Gemini 3 Pro, especialista em Performance e Otimização de Código.
    Analise o código fornecido (diffs do PR) focando EXCLUSIVAMENTE em:
    1. Complexidade Ciclomática e Algorítmica (Big O)
    2. Uso de recursos (Memória, CPU, Latência)
    3. Sugestões de otimização
    Seja conciso. Liste Pontos Principais.
    """

    prompt_jules = """
    Você é Jules, o Engenheiro DevOps e Especialista em CI/CD de A Colmeia.
    Analise o código fornecido (diffs do PR) focando EXCLUSIVAMENTE em:
    1. Impactos no Pipeline de Build/Deploy
    2. Estrutura de arquivos de configuração (Docker, K8s, GitHub Actions)
    3. Testes Automatizados (Cobertura, tipos de testes)
    4. Boas práticas de Versionamento e Commits
    Seja conciso. Liste Pontos Principais.
    """

    # 4. Run Analysis in Parallel
    print("🚀 Iniciando análise multi-agente...")

    results = await asyncio.gather(
        analyze_with_model("Claude Opus 4.5", REQUESTED_CLAUDE_MODEL, prompt_claude, code_context),
        analyze_with_model("Gemini 3 Pro", MODEL_GEMINI_NAME, prompt_gemini, code_context),
        analyze_with_model("Jules", MODEL_JULES_ENGINE, prompt_jules, code_context)
    )

    # 5. Post Comments
    print("Posting comments to PR...")

    agents = ["Claude Opus 4.5", "Gemini 3 Pro", "Jules"]
    for i, analysis in enumerate(results):
        if analysis and "Error executing analysis" not in analysis:
            try:
                pr.create_issue_comment(format_comment(agents[i], analysis))
                print(f"✅ {agents[i]} comment posted.")
            except Exception as e:
                print(f"❌ Failed to post comment for {agents[i]}: {e}")
        else:
            print(f"⚠️ Skipping comment for {agents[i]} due to analysis failure.")

    print("🏁 Review cycle complete.")

if __name__ == "__main__":
    asyncio.run(main())
