# PayScope LLM & Agent Integration Guide

## Overview

This guide documents the integration of LLMs (LLaMA 3.1 TGI + OpenAI o1) and agent frameworks (CrewAI + AutoGen) into PayScope.

## Implementation Status

### ✅ Completed
1. **LLM Clients**
   - `llm/tgi_client.py` - LLaMA 3.1 via TGI
   - `llm/openai_o1.py` - OpenAI o1 client
   - `llm/langchain_integration.py` - LangChain wrappers

2. **Enhanced Agents**
   - `agents/enhanced_base.py` - Base with LLM support
   - `agents/enhanced_fraud_agent.py` - LLM-assisted fraud detection

3. **Autonomy**
   - `autonomy/trl_integration.py` - RLHF with TRL
   - `autonomy/autogen_integration.py` - AutoGen orchestrator

4. **Integration**
   - `integration/wire_llms.py` - Wires LLMs into orchestrator
   - `ml_agents/crew_setup.py` - CrewAI setup

### ⚠️ Requires Configuration

#### Environment Variables
```bash
# OpenAI o1
OPENAI_API_KEY=sk-...

# TGI (LLaMA 3.1)
TGI_BASE_URL=http://localhost:8080

# Optional: Wandb for RLHF logging
WANDB_API_KEY=...
```

#### Dependencies
```bash
# Core LLM/Agent dependencies
pip install langchain langchain-openai langchain-community
pip install crewai
pip install pyautogen
pip install trl transformers

# Existing dependencies (already in pyproject.toml)
pip install unstructured paddleocr transformers torch
pip install prophet  # NeuralProphet replacement already implemented
```

## Usage

### 1. Basic LLM Usage

```python
from payscope_processing.llm.langchain_integration import get_llm_backend

# Use OpenAI o1
llm = get_llm_backend("openai_o1")

# Use TGI (requires TGI server running)
llm = get_llm_backend("tgi", tgi_url="http://localhost:8080")
```

### 2. Enhanced Agents

```python
from payscope_processing.agents.enhanced_fraud_agent import EnhancedFraudAgent

agent = EnhancedFraudAgent(use_llm=True)
result = agent.run(
    task_id="task_123",
    anomalies=[...],
)
```

### 3. CrewAI Multi-Agent

```python
from payscope_processing.ml_agents.crew_setup import MLAgentCrew

crew = MLAgentCrew(use_o1=True)
recommendations = crew.orchestrate_ml_pipeline(
    task_description="Fraud detection model training",
    data_summary={...},
)
```

### 4. AutoGen Autonomous Execution

```python
from payscope_processing.autonomy.autogen_integration import get_autogen_orchestrator

orchestrator = get_autogen_orchestrator()
result = orchestrator.execute_autonomous_task(
    task="Process payment data and detect fraud",
    agent_chain=["ingestion", "fraud", "forecasting"],
)
```

### 5. RLHF with TRL

```python
from payscope_processing.autonomy.trl_integration import get_rlhf_manager

manager = get_rlhf_manager()
trainer = manager.create_ppo_trainer()

# Collect feedback
rewards = manager.collect_feedback(predictions, ground_truth)

# Fine-tune
stats = manager.fine_tune_step(trainer, prompts, rewards)
```

## Integration Points

### Existing Components (No Changes Required)
- ✅ Unstructured.io parsing
- ✅ PaddleOCR
- ✅ LayoutLMv3
- ✅ Prophet/NeuralProphet
- ✅ GNN risk propagation
- ✅ Base agent structure

### New Components (Optional Enhancements)
- ⚠️ LLM-enhanced agents (backward compatible)
- ⚠️ CrewAI for ML tasks
- ⚠️ AutoGen for autonomy
- ⚠️ RLHF for improvement

## Backward Compatibility

All enhancements are **backward compatible**:
- Existing agents work without LLMs
- Enhanced agents fall back to rule-based logic if LLMs unavailable
- Orchestrator works with or without LLM wiring
- All existing functionality preserved

## Testing

### Test LLM Integration
```python
python -c "from payscope_processing.llm.langchain_integration import create_agent_llm; llm = create_agent_llm(); print('OK')"
```

### Test Enhanced Agent
```python
from payscope_processing.agents.enhanced_fraud_agent import EnhancedFraudAgent
agent = EnhancedFraudAgent(use_llm=True)
# Test with sample anomalies
```

### Test CrewAI
```python
from payscope_processing.ml_agents.crew_setup import MLAgentCrew
crew = MLAgentCrew()
# Run ML pipeline
```

## Production Deployment

1. **Configure LLM backends** (OPENAI_API_KEY or TGI server)
2. **Set use_llm flags** to enable/disable LLM features
3. **Monitor LLM usage** (costs, latency)
4. **Gradual rollout** (start with non-critical agents)
5. **Fallback handling** (ensure deterministic behavior when LLMs fail)

## Performance Considerations

- **LLM Latency**: o1 and TGI can add 1-10s per call
- **Cost**: OpenAI o1 is paid; TGI is self-hosted
- **Fallbacks**: Always have rule-based fallbacks
- **Caching**: Consider caching LLM responses for repeated queries
- **Batching**: Batch LLM calls where possible



