# Architecture

IntentGuard sits between agent reasoning and tool execution. The agent proposes
an action; the guard evaluates deterministic task scope and, in later phases,
semantic alignment, instruction provenance, and trajectory state. Only allowed
actions reach synthetic tools. Ambiguous high-impact actions may require user
confirmation.

