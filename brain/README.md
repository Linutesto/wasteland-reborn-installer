# Wasteland Brain

Local HTTP service that lets Fallout 2 CE NPCs answer free-text player lines
through the local LLM (llama.cpp `qwen38` on :8093). Contract:
[`docs/BRAIN-API.md`](../docs/BRAIN-API.md). Python 3 stdlib only.

## Run

    cd <repo root>
    python3 brain/server.py --host 127.0.0.1 --port 8820 \
        --llm http://127.0.0.1:8093 --db brain/brain.db

On first start a random bearer token is written to `brain/token` (mode 0600).
The engine sends `Authorization: Bearer <token>`.

    TOK=$(cat brain/token)
    curl -s localhost:8820/v1/health
    curl -s -H "Authorization: Bearer $TOK" localhost:8820/v1/npc/personas
    curl -s -H "Authorization: Bearer $TOK" \
      "localhost:8820/v1/npc/memory?campaign=qa-1&pid=16777278"

> **Port clash:** on this workstation 127.0.0.1:8820 is currently used by
> another service (`cascreen.ops`). Use `--port 8822` or free 8820.

systemd user unit (not installed): `brain/wasteland-brain.service`.

## Test

    cd <repo root> && python3 -m unittest discover -s brain/tests -v

Tests use a fake LLM server; they don't touch qwen38, `brain/brain.db` or
`brain/token`.

## Config

| Env var | Default | Meaning |
|---|---|---|
| `BRAIN_TOKEN` | (unset) | bearer token; overrides the token file |
| `BRAIN_TOKEN_FILE` | `brain/token` | token file (`--token-file`) |
| `BRAIN_LLM_URL` | `http://127.0.0.1:8093` | llama.cpp base URL (`--llm`) |
| `BRAIN_LLM_MODEL` | `qwen38` | model id (`--model`) |
| `BRAIN_LLM_TIMEOUT` | `25` | seconds; total budget per talk, then canned fallback |
| `BRAIN_SUMMARY_TIMEOUT` | `60` | seconds for a background summary call |
| `BRAIN_SUMMARY_RETRY` | `120` | seconds to wait before retrying a failed summary |
| `BRAIN_PERSONAS` | `brain/personas` | persona dir (`--personas`) |
| `BRAIN_LOG_DIR` | `brain/logs` | `talk.jsonl` (+ `prompts.jsonl`) (`--log-dir`) |
| `BRAIN_LOG_PROMPTS` | off | `1` = also log every full LLM prompt to `prompts.jsonl` |

## Personas

`brain/personas/*.json`: `id`, `pids`, `name`, `role`, `fallback_lines` are
required; optional `background` (list of facts the NPC is sure of), `voice`,
`knows`, `never`, `companion_address` (what they call the player while in the
party, e.g. Vic → "Boss"). PIDs come from `docs/critter-pids.tsv`. Restart the
service after editing.

## Native NPC coverage

Free talk now covers every character that opens a scripted dialogue, including
nonparty and mod-added characters. Native name, description and current
dialogue ground a generic persona; Vic and Maida retain their curated ones.
Set `[ai] content_id=ettu` for Et Tu (default: `fallout2`). Memories use saved
unique object IDs and remain isolated by campaign and content. Humanoid flavor NPCs with only floating text get a free-talk-only screen
after their original script runs. Its only actions are talking and leaving;
barter stays unavailable. Combat, inactive and fleeing actors are excluded.
