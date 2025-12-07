# CodeSage — Vim AI Assistant

CodeSage is a local-first AI assistant that runs next to Vim/Neovim. It exposes
a lightweight TCP broker that the Vim plugin talks to, and the broker streams
tokens from llama.cpp-powered models.

## Status

- ✅ Project scaffolding landed
- ✅ Minimal asyncio broker (STEP 2)
- ✅ llama.cpp backend wired in (STEP 3)
- ✅ Streaming completion protocol (STEP 4)
- ⏳ Vim plugin integration + UX polish (STEP 5+)

## Build llama.cpp (STEP 3)

```bash
./scripts/build_llama_cpp.sh
```

This script toggles CUDA support automatically when `nvidia-smi`/`nvcc` is
available. The compiled binary ends up in `llama_cpp/build/bin/main`.

## Download a model

Grab the default Phi-3 mini quantized GGUF (or point at your own file):

```bash
./scripts/download_models.sh
```

By default, models live under `./models`. Override with `MODELS_DIR=/abs/path`.

## Run the broker

```bash
./scripts/start_broker.sh --host 127.0.0.1 --port 5555
```

Send a streaming request from another terminal:

```bash
printf '{"type":"completion","prompt":"Hello","stream":true}\n' | nc 127.0.0.1 5555
```

You will first receive multiple `{"type":"token"}` events followed by the final
`{"type":"completion"}` payload once aggregation finishes.

## Configuration knobs

| Variable | Description | Default |
| --- | --- | --- |
| `MODELS_DIR` | Directory containing `.gguf` files | `./models` |
| `BROKER_MODEL_BACKEND` | `llama` or `echo` (fallback) | `llama` |
| `BROKER_MODEL_FILE` | Filename under `MODELS_DIR` | `code-llama-7b.gguf` |
| `BROKER_MODEL_PATH` | Absolute path to model (overrides file) | _unset_ |
| `BROKER_CONTEXT` | Context window for llama.cpp | `4096` |
| `BROKER_THREADS` | CPU threads fed to llama.cpp | `4` |

If `llama-cpp-python` or the model file is missing, the broker automatically
falls back to the echo backend so development can continue.

## Tests

```bash
python -m unittest tests.test_broker
```

## Project Roadmap

Development follows the staged plan in `STEPS.txt`. With STEPS 2–4 complete,
the next milestone is connecting the Vim plugin to the streaming protocol and
layering richer commands (:AI, :AIRefactor, etc.).
