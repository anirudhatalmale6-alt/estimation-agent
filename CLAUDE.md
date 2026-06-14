# PERF Estimation Agent

This project contains a Claude Code custom agent for performance test effort estimation.

## Agent

- estimation-agent.md - Calculates PERF effort estimates from HLD documents using enterprise PET standards

## Usage

Select "PERF Estimation Agent" from the agent picker in Claude Code, then:
- Provide an HLD document (.docx or paste text) for analysis
- Ask for estimation with specific parameters
- Use calibration mode to adjust results

## Reference

- config/estimation_rules.yaml contains all PERF activity definitions, complexity multipliers, and default units
- 11 PERF activities with base times and complexity multipliers
- 3 project sizes (small/medium/large) with automatic classification
- 19% default efficiency factor
- $250/PD default cost
