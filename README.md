# CodeSage — Vim AI Assistant

CodeSage is a local-first AI assistant that runs next to Vim/Neovim. It exposes
a lightweight TCP broker that the Vim plugin talks to, and the broker will
eventually stream tokens from llama.cpp-powered models.

## Status

- ✅ Project scaffolding landed
- ✅ Minimal asyncio broker that echoes JSON requests (STEP 2)
- ⏳ Model backend + Vim streaming integration (future STEPS)

## Quick Start

```bash
./scripts/start_broker.sh --host 127.0.0.1 --port 5555
```

Send a test JSON line from another terminal:

```bash
printf '{"type":"completion","prompt":"Hello"}\n' | nc 127.0.0.1 5555
```

You should receive an echoed payload that proves the broker loop works.

## Project Roadmap

Development follows the staged plan in `STEPS.txt`. We just completed STEP 2,
which covers the echo broker. Next up: integrate llama.cpp (STEP 3) and hook
the Vim plugin into the new broker APIs (STEP 5).
