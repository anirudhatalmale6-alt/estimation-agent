# PERF Estimation Agent

A Claude Code custom agent that calculates performance test effort estimates from High-Level Design (HLD) documents using enterprise PET (Performance Estimation Template) standards.

## What It Does

- Parses HLD documents (.docx or text) to extract project scope
- Classifies project size (Small/Medium/Large) based on scope metrics
- Calculates effort across 11 PERF activities with complexity multipliers
- Applies efficiency adjustments (default 19%)
- Generates complete estimation reports matching PET ticket format
- Supports calibration mode for fine-tuning estimates
- Outputs Jira PET ticket JSON structure

## 11 PERF Activities

| Activity | Base Time (days) | Default Complexity |
|----------|------------------|--------------------|
| Analysis | 1.50 | medium |
| Assessment | 1.50 | medium |
| Batch Job Execution | 1.50 | medium |
| Data Prep | 0.88 | medium |
| Defects Management | 4.01 | medium |
| Execution - Peak Load | 1.76 | peak_load |
| Execution - Stress Test | 1.76 | stress_test |
| HP PC Support | 1.00 | hp_pc_support |
| Planning | 3.01 | medium |
| Reporting | 2.51 | medium |
| Script Design | 2.00 | complex (2x) |

## Setup

### For Copilot Team (GitHub Copilot with Claude)

1. Copy the `.github/agents/estimation-agent.md` file into your project's `.github/agents/` directory
2. Optionally copy `config/estimation_rules.yaml` as a reference
3. Open the project in VS Code with Claude Code extension installed
4. In Claude Code chat, select "PERF Estimation Agent" from the agent picker at the bottom
5. The agent uses `Claude Sonnet 4.6 (copilot)` model through your Copilot subscription

### For Bedrock Team (Claude through AWS Bedrock)

1. Copy the `.github/agents/estimation-agent-bedrock.md` file into your project's `.github/agents/` directory
2. Rename it to `estimation-agent.md` (remove the -bedrock suffix)
3. Configure Claude Code to use Bedrock as provider:
   - Open Claude Code settings
   - Set API provider to AWS Bedrock
   - Configure your AWS region and credentials
4. The agent uses `us.anthropic.claude-sonnet-4-6-20250514-v1:0` model through your Bedrock access

### Alternative: Claude Code CLI

```bash
cd your-project
claude
# Select the agent from the picker
```

## How to Use

Once the agent is selected in Claude Code:

```
# Analyze an HLD document
"Estimate effort for the HLD document in docs/HLD_ProjectX.docx"

# Provide scope directly
"Estimate PERF effort for a project with 12 endpoints, 8 use cases, and 5 data entities"

# Calibrate
"Set efficiency to 25% and recalculate"
"The total should be around 40 PD, what adjustments are needed?"

# Generate Jira ticket
"Generate a PET ticket JSON for this estimation"
```

## Configuration

The `config/estimation_rules.yaml` file contains all configurable parameters:
- PERF activity base times and complexity
- Complexity multipliers (simple=0.5x, medium=1x, complex=2x)
- Default units per project size
- Project size classification rules
- Efficiency percentage (19%)
- Cost per person-day ($250)

## Integrating Into Your Project

```bash
# From your project root
mkdir -p .github/agents
cp estimation-agent.md .github/agents/

# Optionally include the rules reference
mkdir -p config
cp estimation_rules.yaml config/
```
