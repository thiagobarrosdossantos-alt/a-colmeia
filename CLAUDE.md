# CLAUDE.md - AI Assistant Guide for A Colmeia

## Project Overview

**A Colmeia** (The Hive) is an autonomous multi-AI agent system for automated code review on GitHub Pull Requests. The system coordinates three specialized AI agents that analyze code from different perspectives in parallel, providing comprehensive feedback on architecture, performance, and DevOps practices.

### Key Facts
- **Primary Language:** Python 3.11+
- **Deployment:** GitHub Actions (serverless, event-driven)
- **AI Platforms:** Anthropic Claude (Vertex AI), Google Gemini (Vertex AI)
- **Repository:** `thiagobarrosdossantos-alt/a-colmeia`
- **Main Branch:** `main`
- **Current Working Branch:** `claude/claude-md-mioig1pwlmgk32zv-011M2TkUnLwQDgdwDNT2h1ws`

### Three Specialized AI Agents

1. **Claude Opus 4.5** (`claude-opus-4-5-20251101`)
   - Focus: Software Architecture & Security
   - Analyzes: SOLID principles, Clean Code, Design Patterns, OWASP Top 10

2. **Gemini 2.5 Pro** (`gemini-2.5-pro`)
   - Focus: Performance & Optimization
   - Analyzes: Algorithmic complexity (Big O), resource usage, concurrency patterns

3. **Jules** (powered by `gemini-2.5-pro`)
   - Focus: DevOps & CI/CD
   - Analyzes: Pipeline efficiency, containerization, testing strategy, observability

---

## Repository Structure

```
/home/user/a-colmeia/
├── .git/                                    # Git version control
├── .github/
│   ├── scripts/
│   │   ├── claude_worker.py                 # 143 lines - Claude-specific worker
│   │   └── multi_ai_worker.py               # 303 lines - Multi-agent orchestrator
│   └── workflows/
│       ├── claude-worker.yml                # Claude-specific workflow
│       └── multi-ai-review.yml              # Main multi-agent workflow
├── .vscode/
│   └── settings.json                        # Claude Code extension config
├── a-colmeia/                               # Empty directory (future expansion)
├── README.md                                # Portuguese documentation
├── chatgpt_app.py                           # 47 lines - Standalone ChatGPT example
└── CLAUDE.md                                # This file
```

### Key File Descriptions

#### Core Workers

**`.github/scripts/multi_ai_worker.py`** (303 lines)
- **Purpose:** Orchestrates parallel execution of three AI agents
- **Key Features:**
  - Async parallel execution using `asyncio.gather()`
  - Retry logic with exponential backoff (2s, 4s, 8s)
  - Automatic model fallback on 404 errors
  - Intelligent file filtering (priority extensions, size limits)
  - Token usage tracking and logging
  - GitHub comment truncation (65,000 char limit)
- **Constraints:**
  - Max 50 files per PR
  - Skips files with >2000 line changes
  - Priority extensions: `.py`, `.ts`, `.tsx`, `.jsx`, `.vue`
  - Also handles: `.js`, `.yml`, `.yaml`, `.json`, `.md`, `.html`, `.css`, `.java`, `.go`

**`.github/scripts/claude_worker.py`** (143 lines)
- **Purpose:** Dedicated Claude Opus 4.5 worker for PRs and issues
- **Use Case:** Can be used independently for Claude-only reviews
- **Features:** Simpler than multi_ai_worker, focuses on architecture and security

#### Workflows

**`.github/workflows/multi-ai-review.yml`**
- **Triggers:** PR opened/synchronize/reopened, manual dispatch
- **Runtime:** Ubuntu latest, Python 3.11
- **Timeout:** 20 minutes
- **Permissions:** Read contents, write to PRs/issues

**`.github/workflows/claude-worker.yml`**
- **Triggers:** PR events, issues, issue comments
- **Use Case:** Alternative Claude-only workflow

#### Standalone Examples

**`chatgpt_app.py`** (47 lines)
- **Purpose:** Demonstration of OpenAI ChatGPT integration
- **Model:** `Gpt-5.1-2025-11-13` (note: this may be a future/custom model)
- **Not used in production workflows**

---

## Architecture & Design Patterns

### 1. Multi-Agent Parallel Execution

The system uses Python's `asyncio` for concurrent AI agent execution:

```python
results = await asyncio.gather(
    analyze_with_model("Claude Opus 4.5", model_config, prompt, code),
    analyze_with_model("Gemini 2.5 Pro", model_config, prompt, code),
    analyze_with_model("Jules", model_config, prompt, code)
)
```

**Benefits:**
- 3x faster than sequential execution
- Independent failure handling per agent
- Shared context (PR diff) for all agents

### 2. Resilience Pattern: Retry with Exponential Backoff

Both Claude and Gemini calls implement retry logic:

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        # API call
        return result
    except Exception as e:
        if attempt < max_retries - 1:
            sleep_time = 2 ** (attempt + 1)  # 2s, 4s, 8s
            await asyncio.sleep(sleep_time)
        else:
            # Fallback or raise
```

**Key Points:**
- Handles transient network failures
- Delays: 2s, 4s, 8s
- Automatic model fallback on 404 errors

### 3. Graceful Degradation

- If one agent fails, others continue
- Errors logged but don't block overall workflow
- Empty/error analysis results are skipped during comment posting

### 4. Smart File Filtering

**Priority System:**
1. Priority extensions analyzed first: `.py`, `.ts`, `.tsx`, `.jsx`, `.vue`
2. Other relevant extensions: `.js`, `.yml`, `.yaml`, `.json`, `.md`, `.html`, `.css`, `.java`, `.go`
3. Removed files are skipped
4. Files with >2000 line changes are skipped
5. Maximum 50 files analyzed per PR

**Location:** Lines 184-223 in `multi_ai_worker.py`

---

## Development Workflows

### 1. Making Changes to AI Agent Logic

**File to Edit:** `.github/scripts/multi_ai_worker.py`

**Common Tasks:**

#### A. Modify System Prompts
- **Location:** Lines 232-269
- **Variables:** `prompt_claude`, `prompt_gemini`, `prompt_jules`
- **Format:** String with clear focus areas and instructions
- **Convention:** Use Portuguese for prompts (matches user-facing comments)

#### B. Adjust File Analysis Limits
```python
MAX_FILES = 50        # Line 180 - Total files to analyze
MAX_LINES = 2000      # Line 182 - Max line changes per file
```

#### C. Add New File Extensions
```python
PRIORITY_EXTS = ('.py', '.ts', '.tsx', '.jsx', '.vue')  # Line 185
OTHER_EXTS = ('.js', '.yml', '.yaml', ...)              # Line 186
```

#### D. Change AI Models
```python
MODEL_CLAUDE_NAME = "claude-opus-4-5-20251101"     # Line 16
MODEL_GEMINI_NAME = "gemini-2.5-pro"               # Line 20
MODEL_JULES_ENGINE = "gemini-2.5-pro"              # Line 24
```

### 2. Testing Changes Locally

**Challenge:** No local test suite exists.

**Current Testing Strategy:** Production testing via GitHub Actions

**Recommended Approach for Manual Testing:**
1. Create a test branch
2. Open a draft PR with sample code changes
3. Trigger workflow via PR event or `workflow_dispatch`
4. Check GitHub Actions logs for execution details
5. Review posted comments for accuracy

**Future Improvement:** Consider adding unit tests for:
- File filtering logic
- Comment formatting
- Error handling
- Retry mechanisms

### 3. Adding a New AI Agent

**Steps:**
1. Add model configuration constants (lines 15-24)
2. Create system prompt variable (lines 232-269)
3. Add to `asyncio.gather()` call (lines 274-278)
4. Add agent name to `agents` list (line 283)
5. Update README.md to document new agent

**Example:**
```python
# 1. Configuration
MODEL_NEWAGENT_NAME = "model-id-here"

# 2. Prompt
prompt_newagent = """Your specialized prompt here..."""

# 3. Parallel execution
results = await asyncio.gather(
    analyze_with_model("Claude Opus 4.5", ...),
    analyze_with_model("Gemini 2.5 Pro", ...),
    analyze_with_model("Jules", ...),
    analyze_with_model("New Agent", MODEL_NEWAGENT_NAME, prompt_newagent, code_context)
)

# 4. Agent list
agents = ["Claude Opus 4.5", "Gemini 2.5 Pro", "Jules", "New Agent"]
```

### 4. Modifying Workflow Triggers

**File:** `.github/workflows/multi-ai-review.yml`

**Current Triggers:**
```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
  workflow_dispatch:
```

**Additional Options:**
- `pull_request.types`: `edited`, `closed`, `labeled`
- `push`: Trigger on specific branches
- `schedule`: Cron-based execution
- `issue_comment`: Respond to PR comments

**Reference:** [GitHub Actions Events](https://docs.github.com/en/actions/reference/events-that-trigger-workflows)

---

## Key Conventions & Standards

### Code Style

1. **Language:** Python 3.11+ features allowed
2. **Async/Await:** Use for I/O-bound operations (API calls)
3. **Error Handling:** Try-except blocks with informative logging
4. **Logging:** Use emoji prefixes for visual parsing
   - 🤖 Agent operations
   - 📊 Metrics/usage
   - ⚠️ Warnings
   - ❌ Errors
   - ✅ Success
   - 🚀 Starting operations
   - 🏁 Completion
   - 🔍 Analysis
   - ⏳ Waiting/delays

5. **Comments:** Inline comments for complex logic, docstrings for functions

### Environment Variables

**Required:**
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions
- `GCP_CREDENTIALS` - Google Cloud Service Account JSON (secret)
- `GCP_PROJECT_ID` - GCP Project ID (secret, default: `gen-lang-client-0394737170`)
- `GITHUB_REPOSITORY` - Repository name (auto-provided)
- `PR_NUMBER` - Pull request number (auto-provided)

**Optional:**
- `OPENAI_API_KEY` - Only for standalone chatgpt_app.py

**Setting in Workflow:**
```yaml
env:
  GOOGLE_APPLICATION_CREDENTIALS: /tmp/gcp-key.json
  GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### API Configuration

#### Claude (Anthropic Vertex)
```python
client = AnthropicVertex(region="us-central1", project_id=PROJECT_ID)
message = client.messages.create(
    max_tokens=4096,
    model="claude-opus-4-5-20251101",
    system=system_prompt,
    messages=[{"role": "user", "content": user_content}]
)
```

#### Gemini (Vertex AI)
```python
vertexai.init(project=PROJECT_ID, location="us-central1")
model = GenerativeModel(
    "gemini-2.5-pro",
    system_instruction=[system_prompt]
)
response = model.generate_content(
    user_content,
    generation_config={"max_output_tokens": 8192, "temperature": 0.2},
    safety_settings={...}
)
```

### Safety Settings (Gemini)

All harm categories set to `BLOCK_ONLY_HIGH`:
- `HARM_CATEGORY_HATE_SPEECH`
- `HARM_CATEGORY_DANGEROUS_CONTENT`
- `HARM_CATEGORY_SEXUALLY_EXPLICIT`
- `HARM_CATEGORY_HARASSMENT`

**Rationale:** Code review context requires flexibility; overly strict filtering may block legitimate technical discussions.

---

## Git & GitHub Conventions

### Branch Naming

- **Main branch:** `main`
- **Feature branches:** `claude/claude-md-{session-id}` (AI assistant branches)
- **Convention:** Use descriptive names for human-created branches

### Commit Guidelines

1. **Language:** Portuguese or English (Portuguese preferred to match documentation)
2. **Format:** Conventional commits style
   ```
   feat: Nova funcionalidade X
   fix: Corrige bug Y
   docs: Atualiza documentação Z
   refactor: Refatora módulo W
   ```

3. **Scope:** Keep commits focused and atomic

### Pull Request Process

1. **Automatic Review:** Multi-AI review triggers on PR open/update
2. **Expected Comments:** 3 comments (one per agent) within ~5 minutes
3. **Review Focus:**
   - Claude: Architecture & Security
   - Gemini: Performance & Optimization
   - Jules: DevOps & CI/CD

4. **Manual Review:** Human review still recommended for final approval

### Working with GitHub Actions

**View Logs:**
```bash
# In GitHub UI
Actions tab → Select workflow run → Select job → Expand steps
```

**Debugging Failed Runs:**
1. Check "Run Multi-AI Worker" step for Python errors
2. Look for retry attempts (⚠️ warnings)
3. Check token usage logs (📊)
4. Verify GCP authentication succeeded
5. Ensure PR_NUMBER is set

**Manual Trigger:**
1. Go to Actions tab
2. Select "Multi-AI Review - A Colmeia"
3. Click "Run workflow"
4. Select branch and PR number

---

## Dependencies & Installation

### Production Dependencies

**Installed via pip in workflows:**
```bash
pip install --upgrade \
  google-cloud-aiplatform \
  PyGithub \
  anthropic \
  google-auth \
  requests \
  --break-system-packages
```

### Dependency Versions

**Note:** No version pinning currently implemented.

**Risk:** Breaking changes in dependencies could cause failures.

**Recommendation:** Consider adding `requirements.txt`:
```txt
google-cloud-aiplatform>=1.40.0
PyGithub>=2.1.1
anthropic>=0.8.0
google-auth>=2.25.0
requests>=2.31.0
```

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/thiagobarrosdossantos-alt/a-colmeia.git
cd a-colmeia

# Install dependencies
pip install google-cloud-aiplatform PyGithub anthropic google-auth requests

# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/gcp-key.json"
export GITHUB_TOKEN="your-github-token"
export GITHUB_REPOSITORY="owner/repo"
export PR_NUMBER="123"

# Run worker
python3 .github/scripts/multi_ai_worker.py
```

---

## Testing Strategy

### Current State: No Automated Tests

**Why:**
- Small codebase (493 lines total)
- Production testing via real PR reviews
- Rapid iteration prioritized over test coverage

### Manual Testing Checklist

When modifying worker scripts:

- [ ] Syntax check: `python3 -m py_compile .github/scripts/multi_ai_worker.py`
- [ ] Linting: `pylint .github/scripts/multi_ai_worker.py` (if available)
- [ ] Test PR: Create draft PR with sample changes
- [ ] Check logs: Verify no Python exceptions in Actions logs
- [ ] Validate output: Review posted comments for correctness
- [ ] Edge cases: Test with binary files, large PRs, empty PRs
- [ ] Error handling: Simulate API failures (modify code temporarily)

### Future Test Recommendations

**Unit Tests (pytest):**
```python
# tests/test_file_filtering.py
def test_priority_extensions():
    files = [mock_file('.py'), mock_file('.txt')]
    filtered = filter_files_by_priority(files)
    assert filtered[0].filename.endswith('.py')

def test_max_files_limit():
    files = [mock_file('.py') for _ in range(100)]
    filtered = filter_files(files, max_files=50)
    assert len(filtered) == 50
```

**Integration Tests:**
```python
# tests/test_api_integration.py
@pytest.mark.asyncio
async def test_claude_vertex_call():
    response = await call_claude_vertex(
        "claude-opus-4-5-20251101",
        "Test prompt",
        "Test content"
    )
    assert response is not None
    assert len(response) > 0
```

---

## Security Considerations

### Secrets Management

**DO:**
- Store all credentials in GitHub Secrets
- Use temporary files in `/tmp/` for credentials
- Clear credentials after workflow completion (handled by runner cleanup)
- Rotate GCP service account keys regularly

**DON'T:**
- Commit API keys, tokens, or credentials to repository
- Log credential values in workflows
- Store credentials in environment variables visible in logs

### API Key Security

**GCP Service Account:**
- Minimal required permissions (Vertex AI, no broader access)
- Dedicated service account per environment
- Enable audit logging for API usage

**GitHub Token:**
- Automatically provided by Actions
- Limited to repository scope
- Permissions explicitly defined in workflow (`contents: read`, `pull-requests: write`)

### Code Execution Safety

**Worker scripts:**
- Do not execute arbitrary code from PRs
- Only analyze diff content (read-only)
- No eval(), exec(), or subprocess with PR content
- All file reads are from GitHub API (not direct filesystem access)

### Dependency Security

**Risks:**
- Supply chain attacks via compromised packages
- Dependency vulnerabilities

**Mitigations:**
- Use official package sources (PyPI)
- Consider: Dependabot for vulnerability alerts
- Consider: Pinning dependency versions
- Consider: Using `pip-audit` in workflows

---

## Troubleshooting Guide

### Common Issues

#### 1. Workflow Fails: "Missing Environment Variables"

**Symptoms:**
```
Error: Missing Environment Variables (GITHUB_TOKEN, REPO, PR_NUMBER).
```

**Causes:**
- Workflow triggered outside PR context
- Secrets not configured

**Solutions:**
- Check workflow trigger: Must be PR event or manual dispatch with PR_NUMBER
- Verify GitHub Secrets are set: Settings → Secrets and variables → Actions
- Ensure `PR_NUMBER` is passed in workflow YAML

#### 2. GCP Authentication Fails

**Symptoms:**
```
google.auth.exceptions.DefaultCredentialsError
```

**Causes:**
- `GCP_CREDENTIALS` secret not set or invalid JSON
- `GOOGLE_APPLICATION_CREDENTIALS` not exported properly

**Solutions:**
```yaml
# Verify in workflow:
- name: Authenticate GCP
  env:
    GCP_CREDENTIALS: ${{ secrets.GCP_CREDENTIALS }}
  run: |
    echo "$GCP_CREDENTIALS" > /tmp/gcp-key.json
    export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-key.json
```

- Validate GCP_CREDENTIALS is valid JSON
- Ensure service account has Vertex AI permissions

#### 3. Model 404 Errors

**Symptoms:**
```
⚠️ [Claude] Model not found. Falling back to standard Claude Opus 4.5.
```

**Causes:**
- Model ID incorrect or not available in region
- Model not enabled in GCP project

**Solutions:**
- Verify model ID: `claude-opus-4-5-20251101`, `gemini-2.5-pro`
- Check model availability in `us-central1` region
- Enable models in GCP Console: Vertex AI → Model Garden
- Fallback mechanism will attempt alternative model ID automatically

#### 4. No Comments Posted on PR

**Causes:**
- All agents failed (check logs for errors)
- `GITHUB_TOKEN` lacks `pull-requests: write` permission
- PR number not passed correctly

**Debug Steps:**
1. Check Actions logs for agent execution
2. Look for "Posting comments to PR..." message
3. Verify analysis results are not empty/error messages
4. Check workflow permissions in YAML:
   ```yaml
   permissions:
     pull-requests: write
   ```

#### 5. Timeout After 20 Minutes

**Causes:**
- Very large PR (>50 files or >2000 lines per file)
- API rate limiting or slow responses
- Network issues

**Solutions:**
- Increase timeout in workflow:
  ```yaml
  timeout-minutes: 30  # Increase from 20
  ```
- Reduce `MAX_FILES` or `MAX_LINES` in worker script
- Check GCP quotas: Vertex AI API limits

#### 6. Comment Truncated Warning

**Symptoms:**
```
... [Truncated due to GitHub Comment Limit]
```

**Cause:**
- Analysis exceeds 65,000 characters (GitHub limit)

**Solutions:**
- Expected behavior for very detailed analyses
- Consider summarizing prompt instructions
- Alternative: Split into multiple comments (requires code changes)

---

## Performance Optimization

### Current Performance Profile

**Typical PR Review:**
- File analysis: ~10-30 seconds
- 3x parallel API calls: ~60-120 seconds
- Comment posting: ~5-10 seconds
- **Total:** ~2-3 minutes for average PR

### Optimization Opportunities

1. **Reduce Context Size:**
   ```python
   # Current: Full patch for each file
   # Optimization: Intelligent truncation for very long patches
   if len(file.patch) > 10000:
       code_context += file.patch[:10000] + "\n... [truncated]"
   ```

2. **Parallel Comment Posting:**
   ```python
   # Current: Sequential
   for i, analysis in enumerate(results):
       pr.create_issue_comment(...)

   # Optimized: Parallel
   await asyncio.gather(*[
       post_comment(pr, agents[i], results[i])
       for i in range(len(results))
   ])
   ```

3. **Caching Strategy:**
   - Cache file content for repeated analysis
   - Store previous PR analysis to detect duplicate comments
   - Consider: Vertex AI caching (not currently implemented)

4. **Smart File Selection:**
   - Further prioritize files with highest change complexity
   - Skip generated files (lock files, build artifacts)
   - Focus on files with specific keywords (TODO, FIXME, HACK)

---

## AI-Specific Prompt Engineering

### Crafting Effective System Prompts

**Current Structure:**
```python
prompt = """
You are [Agent Name], [Expertise Description].
Perform a DEEP, DETAILED, COMPLETE analysis.

Focus:
1. [Area 1] - [Details]
2. [Area 2] - [Details]
3. [Area 3] - [Details]

[Additional Instructions]
"""
```

**Best Practices:**

1. **Clear Identity:** Define role and expertise level
   ```python
   "You are Claude Opus 4.5, a Senior Software Architecture and Security Expert."
   ```

2. **Explicit Depth:** Specify analysis thoroughness
   ```python
   "Perform a DEEP, DETAILED, COMPLETE analysis. Do not economize on explanation."
   ```

3. **Numbered Focus Areas:** Structure analysis dimensions
   ```python
   """
   Focus:
   1. Architecture Patterns (SOLID, Clean Code) - Explain WHY.
   2. Security (OWASP Top 10) - Be rigorous.
   """
   ```

4. **Actionable Output:** Request concrete suggestions
   ```python
   "Provide correction examples where applicable."
   "Suggest concrete refactorings for maximum performance."
   ```

5. **Language Consistency:** Match user-facing documentation (Portuguese for this project)

### Balancing Analysis Depth vs. Token Costs

**Current Configuration:**
- Claude: `max_tokens=4096`
- Gemini: `max_output_tokens=8192`

**Trade-offs:**
- Higher tokens = More detailed analysis = Higher cost
- Lower tokens = Faster response = May truncate important findings

**Recommendation:**
- Monitor token usage logs (📊 markers)
- Adjust based on typical PR complexity
- Consider adaptive limits based on PR size

---

## Future Improvements & Roadmap

### Short-Term (Quick Wins)

1. **Add requirements.txt** - Pin dependency versions
2. **Create .gitignore** - Standard Python .gitignore patterns
3. **Add CONTRIBUTING.md** - Contributor guidelines
4. **Implement parallel comment posting** - Faster PR feedback
5. **Add workflow status badges** - Display in README.md

### Medium-Term (Quality Enhancements)

1. **Unit test suite** - pytest coverage for core functions
2. **Integration tests** - Mock API calls for testing
3. **Pre-commit hooks** - Linting and formatting automation
4. **Structured logging** - JSON logs for better parsing
5. **Metrics dashboard** - Track review counts, response times, token usage

### Long-Term (Advanced Features)

1. **Comment threading** - Reply to specific code lines
2. **Incremental analysis** - Only analyze changed files since last review
3. **Learning system** - Track which suggestions get accepted
4. **Custom agent specializations** - User-defined focus areas
5. **Multi-language support** - English/Portuguese toggle
6. **Webhook integration** - Slack/Discord notifications

---

## VS Code Configuration (.vscode/settings.json)

**Purpose:** Optimizes VS Code for Claude Code extension usage

```json
{
    "claudeCode.respectGitIgnore": true,
    "claudeCode.useCtrlEnterToSend": true,
    "claudeCode.useTerminal": false,
    "claudeCode.selectedModel": "claude-opus-4-5-20251101",
    "claudeCode.claudeProcessWrapper": "python"
}
```

**Key Settings:**
- `respectGitIgnore`: Prevents indexing ignored files
- `useCtrlEnterToSend`: Keyboard shortcut for sending prompts
- `selectedModel`: Default Claude model for coding assistance
- `claudeProcessWrapper`: Python environment for code execution

---

## Quick Reference: Common Commands

### View Recent Activity
```bash
git log --oneline -10
```

### Check Workflow Status
```bash
gh run list --workflow=multi-ai-review.yml
```

### Manually Trigger Workflow (GitHub CLI)
```bash
gh workflow run multi-ai-review.yml
```

### View Specific Workflow Run
```bash
gh run view <run-id>
```

### Check Python Syntax
```bash
python3 -m py_compile .github/scripts/multi_ai_worker.py
```

### Test Import
```bash
python3 -c "import sys; sys.path.insert(0, '.github/scripts'); import multi_ai_worker"
```

### View Environment in Workflow
```bash
# Add to workflow step:
run: env | sort
```

---

## Contact & Resources

### Project Maintainer
- Repository: `thiagobarrosdossantos-alt/a-colmeia`
- Primary documentation: `README.md` (Portuguese)

### Useful Links

**Anthropic Claude:**
- [Vertex AI Integration](https://docs.anthropic.com/en/api/claude-on-vertex-ai)
- [Claude Model Documentation](https://docs.anthropic.com/en/docs/models-overview)

**Google Vertex AI:**
- [Generative AI Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/learn/overview)
- [Gemini Models](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)

**GitHub Actions:**
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Events That Trigger Workflows](https://docs.github.com/en/actions/reference/events-that-trigger-workflows)

**PyGithub:**
- [Documentation](https://pygithub.readthedocs.io/)
- [Pull Request API](https://pygithub.readthedocs.io/en/latest/github_objects/PullRequest.html)

---

## Appendix: System Prompt Templates

### Template: Architecture Agent

```python
"""
You are [Agent Name], a [Seniority Level] [Specialization] Expert.
Perform a DEEP, DETAILED, COMPLETE analysis of the provided code.
Do not economize on explanation. Prioritize technical quality and robustness.

Focus Areas:
1. [Primary Focus] - [Specific Aspects]
2. [Secondary Focus] - [Specific Aspects]
3. [Tertiary Focus] - [Specific Aspects]

Output Requirements:
- Explain the WHY, not just the WHAT
- Provide concrete correction examples
- Reference industry standards where applicable
- Be rigorous but constructive

Format your response in clear markdown with sections.
"""
```

### Template: Performance Agent

```python
"""
You are [Agent Name], a [Seniority Level] Performance Engineer.
Conduct an exhaustive performance analysis.
Hunt for every millisecond of latency and every byte of wasted memory.

Analysis Dimensions:
1. Algorithmic Complexity (Big O notation)
2. Resource Usage (Memory, CPU, I/O, Database)
3. Concurrency & Parallelism Patterns

For Each Finding:
- Identify the bottleneck
- Quantify the impact
- Suggest specific refactorings
- Provide optimized code examples

Be thorough and data-driven in your assessment.
"""
```

### Template: DevOps Agent

```python
"""
You are [Agent Name], a Principal DevOps Engineer and SRE.
Evaluate this code from an infrastructure and delivery perspective.
Enforce production-grade standards.

Review Checklist:
1. CI/CD Pipeline (Efficiency, Security, Caching)
2. Containerization (Dockerfile optimization, multi-stage builds)
3. Testing Strategy (Coverage gaps, E2E scenarios)
4. Observability (Logging, Metrics, Tracing)
5. Configuration Management (Secrets, Environment Variables)

Be demanding with production standards. Flag any deployment risks.
Provide actionable recommendations for operational excellence.
"""
```

---

## Version History

- **v1.0.0** - Initial CLAUDE.md creation (2025-12-02)
  - Comprehensive codebase documentation
  - Architecture and workflow descriptions
  - Development guidelines for AI assistants
  - Troubleshooting guide
  - Future improvement roadmap

---

**Last Updated:** 2025-12-02
**Document Maintainer:** AI Assistant (Claude)
**Next Review:** When significant codebase changes occur
