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
MODEL_CLAUDE_NAME = "claude-opus-4-5-20251101"
REQUESTED_CLAUDE_MODEL = "claude-opus-4-5-20251101"

# Updated to gemini-2.5-pro
MODEL_GEMINI_NAME = "gemini-2.5-pro"
MODEL_GEMINI_FALLBACK = "gemini-2.5-pro"

# Jules Engine
MODEL_JULES_ENGINE = "gemini-2.5-pro"

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

    # Retry logic with exponential backoff [2, 4, 8]
    max_retries = 3
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                max_tokens=4096,
                model=model_name,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_content,
                    }
                ],
            )
            # Log usage if available (Anthropic structure might vary on Vertex)
            if hasattr(message, 'usage'):
                print(f"📊 [Claude] Token Usage: Input={message.usage.input_tokens}, Output={message.usage.output_tokens}")

            return message.content[0].text
        except Exception as e:
            print(f"⚠️ [Claude] Attempt {attempt+1} failed: {e}")

            # Check for 429 or other retryable errors
            if attempt < max_retries - 1:
                # Delays: 0->2s, 1->4s, 2->8s
                sleep_time = 2 ** (attempt + 1)
                print(f"⏳ Waiting {sleep_time}s before retry...")
                await asyncio.sleep(sleep_time)
            else:
                # Fallback to standard Opus ID if custom one fails
                if model_name != "claude-opus-4-5-20251101" and ("404" in str(e) or "not found" in str(e).lower()):
                    print("⚠️ [Claude] Requested model not found. Falling back to standard Claude Opus 4.5.")
                    return await call_claude_vertex("claude-opus-4-5-20251101", system_prompt, user_content)
                raise e

async def call_gemini_vertex(model_name, system_prompt, user_content):
    """
    Calls Gemini on Vertex AI.
    """
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # Retry logic with exponential backoff [2, 4, 8]
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

            # Log usage
            if hasattr(response, 'usage_metadata'):
                print(f"📊 [Gemini] Token Usage: Input={response.usage_metadata.prompt_token_count}, Output={response.usage_metadata.candidates_token_count}")

            return response.text
        except Exception as e:
            print(f"⚠️ [Gemini] Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                # Delays: 0->2s, 1->4s, 2->8s
                sleep_time = 2 ** (attempt + 1)
                print(f"⏳ Waiting {sleep_time}s before retry...")
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
🤖 **{agent_name} - Análise Automática (Modo Avançado)**

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
    # "Analise até 50 arquivos por PR"
    MAX_FILES = 50
    # "Ignorar apenas arquivos maiores que 2000 linhas"
    MAX_LINES = 2000

    # Priority extensions
    PRIORITY_EXTS = ('.py', '.ts', '.tsx', '.jsx', '.vue')
    OTHER_EXTS = ('.js', '.yml', '.yaml', '.json', '.md', '.html', '.css', '.java', '.go')

    analyzed_files = []

    # Sort files: priority first
    all_files = list(files)
    priority_files = [f for f in all_files if f.filename.endswith(PRIORITY_EXTS)]
    other_files = [f for f in all_files if f.filename.endswith(OTHER_EXTS) and f not in priority_files]
    sorted_files = priority_files + other_files

    count = 0
    for file in sorted_files:
        if count >= MAX_FILES:
            break

        if file.status == "removed":
            continue

        # Check line count roughly via patch lines
        # This is an approximation. Ideally we check file content size, but patch is what we have handy.
        # Alternatively, file.additions can be a proxy for change size,
        # but to check total file size we need to fetch content.
        # Since we use patch for context, checking patch size is most relevant.
        # If user meant "total file lines", we'd need to fetch full content.
        # Assuming patch additions is the constraint for "review".
        # But instructions say "ignorar arquivos maiores que 2000 linhas".
        # Let's assume this means "files whose change is huge" or "the source file is huge".
        # Let's use patch additions as a safety proxy for now to avoid fetching huge files.
        if file.additions > MAX_LINES:
             print(f"⚠️ Skipping {file.filename} (Change > {MAX_LINES} lines)")
             continue

        content = file.patch if file.patch else "Binary or Large file changed."

        analyzed_files.append(file.filename)
        code_context += f"\n\n--- File: {file.filename} ---\n"
        code_context += content
        count += 1

    if not code_context.strip():
        print("No analyzable changes found.")
        sys.exit(0)

    print(f"🔍 Analyzing {len(analyzed_files)} files: {', '.join(analyzed_files[:5])}...")

    # 3. Define Prompts (Updated for Deep Analysis)
    prompt_claude = """
    Você é Claude Opus 4.5, especialista Sênior em Arquitetura de Software e Segurança.
    Realize uma ANÁLISE PROFUNDA, DETALHADA e COMPLETA do código fornecido.
    Não economize na explicação. Priorize a qualidade técnica e robustez.

    Foco:
    1. Padrões de Arquitetura (SOLID, Clean Code, Design Patterns) - Explique O PORQUÊ.
    2. Segurança (OWASP Top 10, Injection, Data Exposure) - Seja rigoroso.
    3. Manutenibilidade e Escalabilidade.

    Forneça exemplos de correção onde aplicável.
    """

    prompt_gemini = """
    Você é Gemini 2.5 Pro, especialista Sênior em Performance e Engenharia de Software.
    Realize uma ANÁLISE PROFUNDA, DETALHADA e COMPLETA.
    Busque cada milissegundo de latência e cada byte de memória desperdiçado.

    Foco:
    1. Complexidade Ciclomática e Algorítmica (Big O) - Analise loops e recursões.
    2. Uso de recursos (Memória, CPU, I/O, Database Calls).
    3. Concorrência e Paralelismo.

    Sugira refatorações concretas para performance máxima.
    """

    prompt_jules = """
    Você é Jules, Engenheiro Principal de DevOps e SRE de A Colmeia.
    Realize uma ANÁLISE PROFUNDA e CRÍTICA sobre a infraestrutura e entrega.

    Foco:
    1. Pipeline de CI/CD (Eficiência, Segurança, Caching).
    2. Containerização (Dockerfiles otimizados, Multi-stage builds).
    3. Estratégia de Testes (Unitários, Integração, E2E) - Identifique lacunas.
    4. Observabilidade (Logs, Métricas, Tracing).

    Seja exigente com padrões de produção.
    """

    # 4. Run Analysis in Parallel
    print("🚀 Iniciando análise multi-agente (Modo Alta Capacidade)...")

    results = await asyncio.gather(
        analyze_with_model("Claude Opus 4.5", REQUESTED_CLAUDE_MODEL, prompt_claude, code_context),
        analyze_with_model("Gemini 2.5 Pro", MODEL_GEMINI_NAME, prompt_gemini, code_context),
        analyze_with_model("Jules", MODEL_JULES_ENGINE, prompt_jules, code_context)
    )

    # 5. Post Comments
    print("Posting comments to PR...")

    agents = ["Claude Opus 4.5", "Gemini 2.5 Pro", "Jules"]
    for i, analysis in enumerate(results):
        if analysis and "Error executing analysis" not in analysis:
            try:
                # GitHub comment limit is roughly 65536 chars.
                # If analysis is massive (Deep analysis), we might need to truncate or split.
                # For now, let's assume it fits, but truncate safely if needed.
                if len(analysis) > 65000:
                    analysis = analysis[:65000] + "\n\n... [Truncated due to GitHub Comment Limit]"

                pr.create_issue_comment(format_comment(agents[i], analysis))
                print(f"✅ {agents[i]} comment posted.")
            except Exception as e:
                print(f"❌ Failed to post comment for {agents[i]}: {e}")
        else:
            print(f"⚠️ Skipping comment for {agents[i]} due to analysis failure.")

    print("🏁 Review cycle complete.")

if __name__ == "__main__":
    asyncio.run(main())
