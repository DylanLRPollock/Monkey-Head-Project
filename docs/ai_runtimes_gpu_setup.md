# Phase 5 — AI runtimes & GPU selection

## Vulkan fallback for Ollama
- Exported `OLLAMA_LLM_LIBRARY=vulkan`.
- Exported `VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/radeon_icd.x86_64.json`.
- Attempted to run `ollama serve`, but the command is unavailable in the current environment (`bash: command not found: ollama`).

## ROCm verification
- Exported `OLLAMA_LLM_LIBRARY=rocm`.
- Attempted to run `ollama serve`, but the command remains unavailable (`bash: command not found: ollama`).

## Model downloads
- Attempted to pull `mistral:7b-instruct-q4_K_M` and `llama3.1:8b-instruct-q4_K_M` with `ollama pull`.
- Both commands failed because `ollama` is not installed on this system.

> ℹ️ Install Ollama or provide the binary in the PATH before re-running these steps.
