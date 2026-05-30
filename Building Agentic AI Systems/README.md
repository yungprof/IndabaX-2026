# 🏥 AMA Health Agent
### Community Health Triage Assistant for Ghana

> **Workshop Project** — Building Agentic AI Systems  
> Practical session companion to the theory slides on agentic AI design.

---

## What You Are Building

**AMA** (Agentic Medical Assistant) is a health triage agent for community healthcare workers and patients in Ghana. Given a patient's symptoms and location, it:

1. Checks symptoms against a database of common Ghanaian conditions (malaria, typhoid, cholera, snakebite, and more)
2. Recommends the right level of care — CHPS compound, health centre, or hospital
3. Finds the nearest appropriate facility by district and region
4. Flags critical cases for immediate escalation

By the end of this session, you will have a working CLI agent that can hold a multi-turn conversation, call tools, and produce triage recommendations.

---

## Theory Objectives Reference

Each exercise in this project maps to one or more of the five objectives from the theory slides. Use this as a quick reference when an exercise says "Theory connection: Objective N":

| # | Objective | Core idea |
|---|---|---|
| 1 | What is an agentic system? | The reasoning–planning–action loop; the agent equation (Base Model + Memory + Tools); memory types; single vs multi-agent architectures |
| 2 | Limitations & mitigations | Six failure modes: instruction drift, wrong tool selection, hallucination, infinite loops, context exhaustion, tool call failures; also cost/latency, prompt injection, trust boundaries |
| 3 | Designing your system | Model selection; tool design (name, description, parameters); prompt engineering; orchestration patterns (single-agent, supervisor-worker, peer); state management |
| 4 | Deploy & operate | Structured logging (what to log at every step); observability tooling; human-in-the-loop (when to pause); trust boundaries enforced in code, not just prompts |
| 5 | Evaluation | Metrics beyond output quality (task completion rate, step efficiency, tool call accuracy, failure recovery rate); test case design (happy path, tool failures, adversarial, edge cases); automated vs human evaluation; iteration cycle |

---

## The Three Things to Take Away

These are the ideas from the theory session this project is designed to make concrete and permanent:

### 1. An agent is defined by its loop, not its components
A pipeline that calls three LLMs is still a pipeline. What makes AMA an agent is that **the model decides what to do next** — whether to call `symptom_checker`, `facility_locator`, `escalation_trigger`, or respond directly — based on the conversation so far. You will implement this loop yourself in `agent/core.py`.

### 2. Your system is only as capable as its tools
The agent's reasoning can be perfect, but if `symptom_checker` returns garbage, the response will be wrong. Tool design — clear names, honest descriptions, well-typed parameters — is where most real-world agent failures originate. You will write the tool implementations and their schemas.

### 3. What you cannot observe, you cannot improve
The agent maintains a `step_log` for a reason. In production, every tool call, every model decision, and every response must be logged and traceable. The optional observability exercise is not decoration — it is the difference between a demo and a deployable system.

---

## What You Will Build

| Deliverable | Description |
|---|---|
| `tools/symptom_checker.py` | Matching logic against Ghana condition DB |
| `tools/facility_locator.py` | Facility search and ranking logic |
| `tools/escalation_trigger.py` | Escalation rules for critical cases |
| `agent/core.py` | The full reasoning–planning–action loop |
| A working CLI | `python cli.py` — hold a real conversation with the agent |
| A passing test suite | `pytest tests/ -v -m unit` — all Level 1 tests green |

---

## Project Structure

```
ama-health/
│
├── agent/
│   ├── core.py            ← EXERCISES 2, 3 — the agent loop & memory
│   ├── openrouter.py      ← provided — OpenRouter API wrapper
│   └── prompts.py         ← provided — system prompt (read carefully)
│
├── tools/
│   ├── symptom_checker.py ← EXERCISE 1 — implement _match_conditions
│   ├── facility_locator.py← EXERCISE 1 — implement _find_best_facility
│   └── escalation_trigger.py ← EXERCISE 1 — implement evaluate_escalation
│
├── data/
│   ├── symptoms.json      ← Ghana condition + symptom database
│   ├── facilities.json    ← CHPS compounds and hospitals by region
│   └── referral_tiers.json← GHS tier system explanation
│
├── tests/
│   └── test_agent.py      ← LEVEL 1 unit tests + LEVEL 2/3 integration tests
│
├── cli.py                 ← entry point — run this to talk to your agent
├── requirements.txt
├── .env.example
└── pytest.ini
```

---

## Exercises

### Required Exercises — Complete these to get a working agent

---

#### Exercise 1 — Implement the Three Tools
**Files:** `tools/symptom_checker.py`, `tools/facility_locator.py`, `tools/escalation_trigger.py`  
**Time estimate:** 25–30 minutes  
**Theory connection:** Objective 3 — Tool design; the agent equation (tools component)

You will implement the core logic inside each tool file. Each file has a detailed `EXERCISE` block explaining exactly what to build. Read the docstrings carefully — the test suite validates your implementation.

**symptom_checker — `_match_conditions`**  
Score each condition in `data/symptoms.json` against the reported symptoms. Primary symptom match = 2 pts, secondary = 1 pt, severe indicator = 3 pts. Return ranked results. Fallback to the "unknown" condition if nothing matches.

**facility_locator — `_find_best_facility`**  
Search `data/facilities.json` for the best matching facility. Never return a facility below the required level. Prefer district matches over region-only matches. Return `None` if nothing qualifies.

**escalation_trigger — `evaluate_escalation`**  
Apply escalation rules: always escalate snakebites and hypertensive crises; escalate severe/critical cases; escalate moderate+ cases in pregnant patients or children. Return a structured dict with `escalate`, `reason`, `action`, and `contact`.

**Also in Exercise 1:** Add the `escalation_trigger` tool schema to `TOOL_SCHEMAS` in `agent/core.py`. The two existing schemas are your template.

✅ **Done when:** `pytest tests/ -v -m unit` passes all Level 1 tests.

---

#### Exercise 3 — Build the Message History Manager
**File:** `agent/core.py` — `_add_message` and `_get_messages` methods  
**Time estimate:** 10 minutes  
**Theory connection:** Objective 1 — Memory (in-context type); Objective 3 — State management

> **Do this before Exercise 2.** The reasoning loop calls `_get_messages()` — if you implement the loop first, it will send an empty message list to the LLM and produce nothing.

`_add_message` appends `{"role": role, "content": content}` to `self.history`.

`_get_messages` returns the **full** message list to send to the LLM: the system prompt as the **first** message, then all of `self.history`. `_run_loop` calls this method and does **not** pass the system prompt separately — `_get_messages` is the single place it appears.

The system prompt lives in `agent/prompts.py` as `SYSTEM_PROMPT`.

```python
# What _get_messages should return:
[
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user",   "content": "I have fever..."},
    {"role": "assistant", "content": "..."},
    # ... rest of self.history
]
```

✅ **Done when:** The agent remembers what was said earlier in the conversation. Test: tell it your district in one message, then describe symptoms in the next — it should use the district when calling `facility_locator`.

---

#### Exercise 2 — Implement the Reasoning Loop
**File:** `agent/core.py` — `_run_loop` method  
**Time estimate:** 20–25 minutes  
**Theory connection:** Objective 1 — The reasoning–planning–action loop; Objective 3 — Orchestration

> **Complete Exercise 3 first** — this loop calls `self._get_messages()`.

This is the heart of the agent. `_run_loop` must:

1. Call `chat()` from `agent/openrouter.py` using `self._get_messages()` for the messages argument and `TOOL_SCHEMAS` for tools
2. If the model returns `tool_calls` — execute each tool, append the result to history with `role="tool"`, and loop
3. If the model returns plain text — extract and return it as the final response

Look at `agent/openrouter.py` to understand the `ChatResponse` object. The `response.tool_calls` field is either a list of `ToolCall` objects or `None`.

The tool result must be appended to `self.history` as:
```python
{"role": "tool", "tool_call_id": tool_call.id, "content": result_str}
```

Do **not** pass `system_prompt=` to `chat()` here — `_get_messages()` already prepends it. Passing it again would send the system prompt twice.

✅ **Done when:** `python cli.py` starts, and typing "I have fever and headache" produces a real response.

---

### Optional Exercises — For advanced students and extended learning

---

#### Exercise 4 — Add Structured Step Logging
**File:** `agent/core.py` — `_execute_tool` method  
**Time estimate:** 10 minutes  
**Theory connection:** Objective 4 — Structured logging and observability

After every tool call, append a structured entry to `self.step_log`:
```python
{
    "step": <step_number>,
    "tool": tool_name,
    "args": args_dict,
    "result": result_dict,
}
```

The `step_log` is already initialised as an empty list in `__init__`. Run `python cli.py --verbose` to see your logs printed live.

✅ **Done when:** `test_step_log_populated_after_tool_call` passes in the advanced test suite.

---

#### Exercise 5 — Enforce the Max Steps Guard
**File:** `agent/core.py` — top of `_run_loop`  
**Time estimate:** 5 minutes  
**Theory connection:** Objective 2 — Infinite loop failure mode and mitigation

Add a check at the top of the while loop: if `steps > self.max_steps`, return a safe fallback message instead of looping. This prevents runaway agents from draining your API quota.

Safe fallback:
```python
"I'm having trouble processing your request. Please visit your nearest CHPS compound or health centre for help."
```

✅ **Done when:** `test_max_steps_guard_prevents_infinite_loop` passes.

---

#### Exercise 6 — Improve the System Prompt
**File:** `agent/prompts.py`  
**Time estimate:** 15–20 minutes  
**Theory connection:** Objective 3 — Prompt engineering; Objective 5 — Evaluation and iteration

The current system prompt is functional but not optimal. Your task:

1. Add a section that instructs the agent to handle Twi or Ghanaian Pidgin input gracefully (respond in English, acknowledge the language)
2. Add guidance on how to ask for clarification when symptoms are too vague to run `symptom_checker`
3. Run the evaluation test suite before and after: `pytest tests/ -v -m "integration and advanced"`
4. Document whether your changes improved or degraded the responses, and why

This exercise mirrors the iteration cycle from Objective 5.

---

#### Exercise 7 — Fuzzy Symptom Matching
**File:** `tools/symptom_checker.py` — `_match_conditions`  
**Time estimate:** 15 minutes  
**Theory connection:** Objective 3 — Tool reliability; Objective 2 — Wrong tool selection mitigation

Real patients don't type perfect symptom names. "headche", "feva", "stomack pain" should still match. Use Python's `difflib.get_close_matches()` (standard library, no install) to add fuzzy matching.

```python
from difflib import get_close_matches
# Example:
get_close_matches("headche", ["headache", "fever", "chills"], n=1, cutoff=0.7)
# → ["headache"]
```

Run the unit tests after — they should still pass.

---

#### Exercise 8 — Distance-Based Facility Ranking
**File:** `tools/facility_locator.py` — `_find_best_facility`  
**Time estimate:** 20 minutes  
**Theory connection:** Objective 3 — Tool design; real-world data integration

Each facility in `data/facilities.json` has a `coordinates` field with `lat` and `lng`. If the agent knows the patient's approximate location, it can rank facilities by distance.

Add a `patient_lat` / `patient_lng` parameter to `find_facility` and implement a simple distance score using the Haversine formula or a Euclidean approximation. Update the tool schema in `agent/core.py` to accept these new parameters.

---

#### Exercise 9 — Design and Run Your Own Evaluation Suite
**File:** `tests/test_agent.py` — `EVALUATION_CASES`  
**Time estimate:** 20 minutes  
**Theory connection:** Objective 5 — All evaluation sub-objectives

Four evaluation cases are already defined in the test file. Add at least three more that cover:
- A case specific to Northern Ghana (a region with different disease patterns)
- A child patient with a common childhood illness
- A case that should NOT trigger escalation (mild presentation)

Run them: `pytest tests/ -v -m "advanced and integration"` and review the printed responses manually. This is the "human evaluation" method from the theory session.

---

## Getting Started

### 1. Set up your environment

```bash
# Clone or unzip the project
cd ama-health

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Get your OpenRouter API key

1. Go to [openrouter.ai](https://openrouter.ai) and create a free account
2. Generate an API key from your dashboard
3. Copy `.env.example` to `.env` and paste your key:

```bash
cp .env.example .env
# Then edit .env and replace 'your_openrouter_api_key_here'
```

Free models that work for this project: `meta-llama/llama-3.3-70b-instruct:free`, `mistralai/mistral-nemo:free`

### 3. Understand the data files

Before writing any code, read:
- `data/symptoms.json` — the condition and symptom database your tools use
- `data/referral_tiers.json` — the Ghana Health Service tier system
- `data/facilities.json` — CHPS compounds and hospitals by region

Understanding the data structure is essential for implementing the tools correctly.

### 4. Work through exercises in order

```
Exercise 1 → Exercise 3 → Exercise 2 → run the CLI → run the tests
```

**Why this order?** Exercise 2 (the reasoning loop) calls `_get_messages()`, which you implement in Exercise 3. If you write the loop before the history manager, the loop will send an empty message list to the LLM and produce no output. Exercise 3 only takes 10 minutes — do it before Exercise 2.

Don't skip to Exercise 3 before Exercise 1 — the agent loop calls the tools, so working tool implementations come first.

### 5. Validate with unit tests at each step

```bash
# After Exercise 1: should pass all Level 1 tests
pytest tests/ -v -m unit

# After Exercises 3 & 2: run the CLI
python cli.py

# After all required exercises: run integration tests
pytest tests/ -v -m integration

# Advanced students: full suite
pytest tests/ -v
```

### 6. Try the CLI

```bash
python cli.py
# or with tool call visibility:
python cli.py --verbose
```

**Example prompts to try:**
- `"I have fever and headache and chills. I am in Kumasi."`
- `"My child has been vomiting and has watery stool since this morning."`
- `"A snake bit my brother on his arm."`
- `"I feel a bit weak and my stomach is paining me a little."`
- `"Where is the nearest hospital to Tamale?"`

---

## Framework Note

This project uses **no agentic framework** (no LangChain, no LlamaIndex, no AutoGen). The agent loop in `agent/core.py` is written from first principles using only the OpenRouter HTTP API.

This is intentional. Frameworks are useful in production, but building without them first means you understand what they are abstracting — and you will know when they are failing you.

Once you have completed this project, the same patterns translate directly to LangGraph, LangChain agents, AutoGen, or any other framework. The concepts are identical; only the syntax changes.

---

## Reflection Prompts

At the end of the session, think about:

1. **Which failure mode did you hit first?** Wrong tool selection? A loop? A hallucinated symptom match? How did you diagnose it?
2. **Where is your system prompt doing work that should be in code?** Are there constraints in the prompt that should be enforced in `evaluate_escalation` instead?
3. **What would break first in production?** If 1,000 patients used this simultaneously, which part of your implementation would fail?
4. **What tool is missing?** What would you add to make this genuinely useful in a rural Ghanaian health context?

---

## Important Disclaimer

This project is for **educational purposes only**. It is not a clinical tool and must not be used for real medical decisions. The symptom database is simplified and incomplete. Always consult a qualified health professional for medical advice.

In a real deployment, this agent would require clinical validation, regulatory approval, integration with live GHS data systems, and significant safety testing.

---

*Built for the "Building Agentic AI Systems" workshop.*  
*Data references: Ghana Health Service public documentation.*
