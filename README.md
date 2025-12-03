# A Colmeia - Integração Multi-IA

Este repositório utiliza **A Colmeia**, um sistema autônomo de agentes de IA, para realizar revisões de código automatizadas e especializadas em Pull Requests.

## Agentes Ativos

O sistema integra três modelos de IA avançados, cada um com um foco específico:

### 1. Claude Opus 4.5
- **Modelo:** `claude-opus-4-5-20251101`
- **Foco:** Arquitetura de Software e Segurança.
- **Responsabilidade:** Analisar padrões de projeto (SOLID, Clean Code) e identificar vulnerabilidades de segurança.

### 2. Gemini 2.5 Pro
- **Modelo:** `gemini-2.5-pro` (via Vertex AI)
- **Foco:** Performance e Otimização.
- **Responsabilidade:** Analisar complexidade algorítmica, uso de recursos e sugerir otimizações de código.

### 3. Jules
- **Agente:** DevOps e CI/CD (Engine: `gemini-2.5-pro`)
- **Foco:** Infraestrutura e Pipelines.
- **Responsabilidade:** Validar arquivos de configuração, testes automatizados e impactos no pipeline de CI/CD.

## Como Funciona

1. **Gatilho:** Quando um Pull Request é aberto ou atualizado.
2. **Execução:** O workflow `.github/workflows/multi-ai-review.yml` é acionado.
3. **Análise:** O script Python conecta-se à Vertex AI e envia o diff do código para os três agentes simultaneamente (em paralelo).
4. **Resultado:** Cada agente publica um comentário independente no PR com sua análise especializada.

## Configuração

Requer as seguintes Secrets no GitHub:
- `GCP_CREDENTIALS`: JSON da Service Account do Google Cloud.
- `GCP_PROJECT_ID`: ID do projeto no GCP.
- `GITHUB_TOKEN`: Token automático do Actions (já configurado).

---
*A Colmeia - Sistema Autônomo de Agentes IA*
