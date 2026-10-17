# ReasonNotesKvantum

Shared Forge/Qwen engineering project.

## Workspace ownership

- Forge: /home/reason/Codex-Projects/ReasonNotesKvantum
- Qwen: /home/reason/Temporary/QwenProjects/ReasonNotesKvantum
- Neutral exchange: /home/reason/Temporary/AgentHandoff/ReasonNotesKvantum.git
- Durable GitHub mirror: https://github.com/Reason7322/ReasonNotesKvantum

Use the handoff remote for agent-to-agent transfer.
Use the github remote for durable off-machine checkpoints.
Every meaningful checkpoint must push and verify the same branch/SHA on both remotes.
Do not merge into main merely to checkpoint.
Do not copy working directories between Forge and Qwen.
