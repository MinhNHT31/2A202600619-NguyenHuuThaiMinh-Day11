# Assignment 11: Production Defense Pipeline
**Student Name**: Nguyen Huu Thai Minh
**Student ID**: 2A202600619

## Part 1: Attack Generation
The pipeline generates adversarial prompts using an LLM (Gemini 2.5 Flash Lite via OpenRouter). The `generate_ai_attacks` function queries the model to act as a red team researcher, instructing it to generate JSON containing diverse attack vectors (e.g., Prompt Injection, Role Confusion, Context Overflow, Malicious Payload, Exfiltration). This output is then robustly parsed using `json_repair`.

## Part 2: Guardrails Implementation
- **Input Guardrails**: Evaluates all incoming messages before reaching the core model. It uses Regex pattern matching to instantly block well-known injection keywords (e.g., "ignore all previous instructions"). It also uses a topic filter to check if the query falls under `ALLOWED_TOPICS` (like banking, transactions) or `BLOCKED_TOPICS` (like hack, exploit, steal).
- **Output Guardrails**: Intercepts the core model's response before sending it to the user. First, a regex-based `content_filter` detects PII (Phone numbers, emails, passwords, API keys) and replaces them with `[REDACTED]`. Second, an LLM-as-a-Judge agent explicitly evaluates the safety of the output content, returning a "safe" or "unsafe" classification with reasons. If deemed unsafe, the output is replaced with a standard block message.
- **Rate Limiting**: Implemented a sliding window limit of 10 requests per 60 seconds per user ID. Prevents DoS attacks, automated brute forcing, and controls API cost exhaustion by returning a predefined block response indicating the remaining wait time.
- **NeMo Guardrails**: Configured YAML and Colang definitions to implement semantic rules for catching Role Confusion attacks, Encoding attacks, and localized Vietnamese injections at an architectural level.
- **Audit Logging**: Recorded timestamps, latency, event types (input vs output), user IDs, and raw message texts directly into an exported `assignment_audit_log.json` to allow post-incident forensics.

## Part 3: Testing Results
*(Results based on simulated testing using the pipeline test suite)*
- **Before Guardrails**: 0% blocked. Unprotected agent leaked simulated credentials and complied with system-level instruction overriding.
- **After Guardrails**: 100% blocked on tested vectors. 
- **Top vulnerabilities fixed**:
  - Prompt Injection overriding (caught by input topic/regex filtering and Colang semantics).
  - PII Leakage (caught and replaced by `[REDACTED]` in output guardrail).
  - API Abuse/DoS (managed efficiently by Rate Limiting returning wait time headers).

## Part 4: HITL Design
- **HITL Point 1**: High-Value Transfer Review
  - **Scenario**: Customer requests a transfer > 50,000,000 VND to an unsaved payee.
  - **Model**: Human-in-the-Loop (Execution is paused until human reviewer approves after reviewing context and device IP).
- **HITL Point 2**: Suspicious Login Credential Change
  - **Scenario**: Customer asks to change password or update recovery email from an unrecognized device or with a High device risk score.
  - **Model**: Human-as-Tiebreaker (Model analyzes the request but requires a final human tiebreak decision).
- **HITL Point 3**: Complex Financial Advice Audit
  - **Scenario**: Customer asks complex questions about mortgage restructuring with moderate AI confidence (0.7 - 0.89).
  - **Model**: Human-on-the-Loop (Response is queued for review asynchronously; human audits after the fact to refine model accuracy).
