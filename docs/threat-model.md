# Threat Model

The adversary may influence direct instructions, retrieved documents, messages,
or synthetic tool output. The adversary does not compromise the guard or tool
implementation. The security objective is to prevent unauthorized consequential
actions while preserving legitimate task completion.

Initial classes include direct and indirect prompt injection, unauthorized tool
invocation, exfiltration, tool-output poisoning, destination substitution,
multi-hop drift, and cumulative or temporal violations.

