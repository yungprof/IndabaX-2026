"""
agent/core.py
─────────────────────────────────────────────────────────────────────────────
AMA Health Agent — Core reasoning loop.

AMA = "Ama" (a common Ghanaian name) / Agentic Medical Assistant

This module contains the main Agent class that orchestrates the
reasoning–planning–action loop you studied in the theory session.

YOUR TASKS (see EXERCISE comments throughout this file):
  REQUIRED  Ex 1 — Complete the tool registry
  REQUIRED  Ex 2 — Implement the reasoning loop
  REQUIRED  Ex 3 — Build the message history manager
  OPTIONAL  Ex 4 — Add step-level logging (observability)
  OPTIONAL  Ex 5 — Implement max_steps guard + graceful shutdown
─────────────────────────────────────────────────────────────────────────────
"""

import json
from typing import Any
from agent.openrouter import chat # see agent/openrouter.py
from tools.symptom_checker import check_symptoms
from tools.facility_locator import find_facility
from tools.escalation_trigger import evaluate_escalation
from agent.prompts import SYSTEM_PROMPT


# ─── Tool registry ────────────────────────────────────────────────────────────
# Maps the tool name the LLM will call to the actual Python function.
# The schema list is passed to the LLM so it knows what tools exist.

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  EXERCISE 1 (REQUIRED) — Complete the tool registry                 ║
# ║                                                                      ║
# ║  Two tools are registered below. You must add the third:            ║
# ║    • escalation_trigger — evaluate_escalation function              ║
# ║                                                                      ║
# ║  Each entry in TOOL_SCHEMAS must follow OpenAI function-calling     ║
# ║  format: name, description, parameters (JSON Schema).               ║
# ║                                                                      ║
# ║  Hint: look at the existing two schemas as a template.              ║
# ║  Hint: look at tools/escalation_trigger.py for the function         ║
# ║        signature and what parameters it expects.                    ║
# ╚══════════════════════════════════════════════════════════════════════╝

TOOL_FUNCTIONS: dict[str, callable] = {
    "symptom_checker": check_symptoms,
    "facility_locator": find_facility,
    # TODO (Exercise 1): add "escalation_trigger": evaluate_escalation
}

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "symptom_checker",
            "description": (
                "Look up a list of reported symptoms against the Ghana condition database. "
                "Returns possible conditions, urgency level, triage notes, and recommended "
                "facility tier. Use this as the FIRST tool when a patient describes symptoms. "
                "Do NOT use for administrative questions or facility lookups."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symptoms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "List of symptom keywords extracted from the patient's message. "
                            "Use simple lowercase English terms, e.g. ['fever', 'headache', 'chills']. "
                            "Include both primary and any mentioned secondary symptoms."
                        ),
                    },
                    "patient_context": {
                        "type": "object",
                        "description": "Optional: known patient context to improve matching.",
                        "properties": {
                            "age_group": {
                                "type": "string",
                                "enum": ["child", "adult", "elderly"],
                                "description": "Approximate age group if mentioned.",
                            },
                            "is_pregnant": {
                                "type": "boolean",
                                "description": "True if the patient is pregnant.",
                            },
                        },
                    },
                },
                "required": ["symptoms"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "facility_locator",
            "description": (
                "Find the most appropriate health facility for a patient given their district/region "
                "and the required care level. Use this AFTER symptom_checker has determined the "
                "recommended facility level. Also use when a patient explicitly asks where to go."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "district": {
                        "type": "string",
                        "description": "Patient's district name as mentioned in conversation, e.g. 'Kumasi' or 'Ningo Prampram'.",
                    },
                    "region": {
                        "type": "string",
                        "description": "Patient's region in Ghana, e.g. 'Ashanti', 'Greater Accra'.",
                    },
                    "required_level": {
                        "type": "integer",
                        "enum": [1, 2, 3, 4],
                        "description": (
                            "Minimum facility level needed: 1=CHPS, 2=Health Centre, "
                            "3=District Hospital, 4=Regional/Teaching Hospital."
                        ),
                    },
                    "needs_emergency": {
                        "type": "boolean",
                        "description": "True if the patient needs a facility with emergency services.",
                    },
                },
                "required": ["required_level"],
            },
        },
    },
    # TODO (Exercise 1): Add the escalation_trigger schema here.
    #
    # The function signature is:
    #   evaluate_escalation(condition_id: str, severity: str, patient_context: dict) -> dict
    #
    # It returns: { "escalate": bool, "reason": str, "action": str }
    #
    # Think about:
    #   - What description tells the model WHEN to call this tool?
    #   - What parameters are required vs optional?
    #   - What enum values make sense for "severity"?
]


# ─── Agent class ──────────────────────────────────────────────────────────────

class AmaAgent:
    """
    The core agentic loop for the AMA health triage assistant.

    Follows the Reasoning–Planning–Action loop from the theory session:
      1. Receive patient message
      2. Reason: decide whether to call a tool or respond directly
      3. Plan: if tool needed, select and call it
      4. Act: append result to context, loop back to step 2
      5. Respond: when reasoning is complete, return final message to patient
    """

    def __init__(self, max_steps: int = 10, verbose: bool = False):
        self.max_steps = max_steps
        self.verbose = verbose
        self.history: list[dict] = []   # conversation message history
        self.step_log: list[dict] = []  # observability log (Exercise 4)

    # ── Public interface ──────────────────────────────────────────────────────

    def chat(self, user_message: str) -> str:
        """
        Accept one patient message and return the agent's response.
        This is the entry point called by the CLI and test suite.
        """
        self._add_message("user", user_message)
        response = self._run_loop()
        self._add_message("assistant", response)
        return response

    def reset(self):
        """Clear history to start a fresh conversation."""
        self.history = []
        self.step_log = []

    # ── Internal loop ─────────────────────────────────────────────────────────

    # ╔══════════════════════════════════════════════════════════════════════╗
    # ║  EXERCISE 2 (REQUIRED) — Implement the reasoning loop              ║
    # ║                                                                      ║
    # ║  ⚠ Complete Exercise 3 first — this loop calls _get_messages(),    ║
    # ║    which you implement there.                                        ║
    # ║                                                                      ║
    # ║  Complete the _run_loop method below. It must:                      ║
    # ║                                                                      ║
    # ║  1. Call the LLM with the current message history and tool schemas  ║
    # ║  2. If the model returns a tool_call:                               ║
    # ║     a. Parse the tool name and arguments                            ║
    # ║     b. Call the matching function from TOOL_FUNCTIONS               ║
    # ║     c. Append the tool result to self.history                       ║
    # ║     d. Loop again (the model will reason on the new context)        ║
    # ║  3. If the model returns a plain text response:                     ║
    # ║     a. Return that text as the final answer                         ║
    # ║                                                                      ║
    # ║  Look at agent/openrouter.py to understand what chat() returns.    ║
    # ║  The return object has: .content (str), .tool_calls (list|None)     ║
    # ║                                                                      ║
    # ║  OPTIONAL (Exercise 5): enforce self.max_steps — if the loop       ║
    # ║  exceeds this limit, return a safe fallback message instead of      ║
    # ║  looping forever.                                                   ║
    # ╚══════════════════════════════════════════════════════════════════════╝

    def _run_loop(self) -> str:
        """
        The reasoning–planning–action loop.
        Returns the final text response to send back to the patient.
        """
        steps = 0

        while True:
            steps += 1

            # TODO (Exercise 5 — OPTIONAL): add a max_steps guard here.
            # If steps > self.max_steps, return a safe fallback like:
            # "I'm having trouble processing your request. Please visit your nearest health facility."

            # Step 1: call the LLM
            # TODO (Exercise 2): call chat() from agent/openrouter.py
            # Use self._get_messages() for the messages argument — it prepends
            # the system prompt for you (Exercise 3). Do NOT also pass
            # system_prompt= here, or the system prompt will be sent twice.
            #   response = chat(messages=self._get_messages(), tools=TOOL_SCHEMAS)
            response = None  # replace this line

            # Step 2: check if the model wants to call a tool
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_result = self._execute_tool(tool_call)

                    # Step 3: append the tool result to history so the model
                    # can reason on it in the next iteration
                    # TODO (Exercise 2): append a message with role="tool"
                    # Structure: {"role": "tool", "tool_call_id": ..., "content": ...}
                    pass  # replace this line

                # Loop continues — the model will reason on the tool results
                continue

            # Step 4: no tool call → the model has a final answer
            # TODO (Exercise 2): extract and return the text response
            return ""  # replace this line

    def _execute_tool(self, tool_call) -> str:
        """
        Dispatch a tool call from the model to the right Python function.
        Returns the tool result as a JSON string.
        """
        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid tool arguments: {e}"})

        if name not in TOOL_FUNCTIONS:
            return json.dumps({"error": f"Unknown tool: {name}"})

        # ── OPTIONAL (Exercise 4): log every tool call ────────────────────
        # Append a structured entry to self.step_log before calling:
        # {
        #   "step": <current step number>,
        #   "tool": name,
        #   "args": args,
        #   "result": <will be filled after call>
        # }
        # ─────────────────────────────────────────────────────────────────

        try:
            result = TOOL_FUNCTIONS[name](**args)
            result_str = json.dumps(result)
        except Exception as e:
            result_str = json.dumps({"error": f"Tool execution failed: {e}"})

        if self.verbose:
            print(f"\n[TOOL CALL] {name}({json.dumps(args, indent=2)})")
            print(f"[TOOL RESULT] {result_str}\n")

        return result_str

    # ── History management ────────────────────────────────────────────────────

    # ╔══════════════════════════════════════════════════════════════════════╗
    # ║  EXERCISE 3 (REQUIRED) — Build the message history manager         ║
    # ║                                                                      ║
    # ║  ⚠ Do this BEFORE Exercise 2 — _run_loop calls _get_messages().    ║
    # ║                                                                      ║
    # ║  _add_message appends to self.history — a list of dicts in the     ║
    # ║  OpenAI message format: {"role": ..., "content": ...}              ║
    # ║                                                                      ║
    # ║  _get_messages should return the FULL message list to send to      ║
    # ║  the LLM: the system prompt as the FIRST message, followed by      ║
    # ║  self.history. _run_loop calls this method — it does NOT pass      ║
    # ║  system_prompt separately, so this is the only place it appears.  ║
    # ║                                                                      ║
    # ║  Why does this matter? Review the "memory" section of the theory   ║
    # ║  slides — self.history IS the agent's in-context memory (Obj 1).  ║
    # ║                                                                      ║
    # ║  OPTIONAL extension: implement a summarisation strategy to handle  ║
    # ║  very long conversations (context window exhaustion, Obj 2).       ║
    # ╚══════════════════════════════════════════════════════════════════════╝

    def _add_message(self, role: str, content: str) -> None:
        """Append a message to conversation history."""
        # TODO (Exercise 3): append {"role": role, "content": content}
        pass  # replace this line

    def _get_messages(self) -> list[dict]:
        """
        Return the full message list to send to the LLM.
        Must include the system prompt as the first message.
        """
        # TODO (Exercise 3): prepend the system prompt, then return self.history
        return []  # replace this line
