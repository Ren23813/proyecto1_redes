# Proyecto 1 — MCP Chatbot Implementation

A hands-on implementation of the **Model Context Protocol (MCP)** — an open standard for connecting AI models to external tools and data sources. This project builds a chatbot that orchestrates multiple MCP servers (Filesystem, Git, and a custom Pharmacy/Clinic service) to demonstrate protocol understanding at the networking layer.

> **Important**: This is an educational project for understanding MCP architecture, JSON-RPC 2.0 communication, and LLM tool-calling patterns. The pharmacy dataset is simulated for demonstration purposes and should not be treated as medical guidance.

## Features

*  **Hands-on MCP implementation** — JSON-RPC 2.0 protocol built from scratch (no MCP SDK)  
*  **Multiple tool servers** — Filesystem, Git (official), and custom Pharmacy/Clinic server  
 * **LLM provider flexibility** — Swap between Ollama (local) and Anthropic without code changes  
*  **Context persistence** — Multi-turn conversations with grounded tool data in history  
*  **Full protocol logging** — Every MCP exchange captured in `logs/interactions.jsonl` for analysis  
*  **Deterministic validation** — Test scripts that exercise tools without LLM involvement  

## Project Phases
By today's date (27/08/2026), the projects current status is:
| Phase | Requirement | Status |
|-------|---|---|
| **1** | LLM connection + context + logging | ✅ Complete |
| **2** | Manual MCP client + JSON-RPC protocol | ✅ Complete |
| **3** | Filesystem + Git official servers | ✅ Complete |
| **4** | Custom local server (Pharmacy/Clinic) | ✅ Complete |
| **5** | Remote server deployment | — Pending |
| **6** | Wireshark analysis | — Pending |
| **7** | Final report + presentation | ... WIP |

## Quick Start

### Prerequisites

- **Python 3.9+**
- **Node.js + Bun** (for Filesystem server via `bunx`)
- **UV** (`pip install uv` or [official installer](https://docs.astral.sh/uv/))
- **Git** (for local commits)
- **Ollama** (if using local LLM) — download at [ollama.com](https://ollama.com)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd proyecto1-mcp

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env: set LLM_PROVIDER, API keys, model names, etc.
```

### Configuration (`.env`)

```bash
# LLM Provider: "ollama" (local) or "anthropic"
LLM_PROVIDER=ollama

# Ollama settings (if using local model)
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434

# Anthropic settings (if using API)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-5

# Workspace for Filesystem/Git servers
MCP_WORKSPACE_DIR=mcp_workspace
```

### Running the Chatbot

```bash
# Start Ollama server in a separate terminal (if using local LLM)
ollama serve

# Then in your project directory:
python main.py
```

Chat with the bot naturally — it can:
- **Search and buy medications** — "I have allergies, what do you recommend?"
- **Schedule clinic appointments** — "I need to see a pediatrician on Sept 1st"
- **Create files and commit** — "Create a README.md with this content and commit it"
- **Maintain conversation context** — Ask follow-ups without repeating context

Example interaction:
```
Tú: tengo alergia, ¿qué me recomiendas?
Claude: Encontré Loratadina 10mg, cuesta $22.75. ¿Quieres comprarla?

Tú: sí, dame 5 paquetes
Claude: Listo, compré 5 Loratadina 10mg por $113.75. Orden: ord-0001
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                              │
│                   (orchestrator)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐   ┌─────▼────┐   ┌─────▼────┐
    │ LLMClient│   │MCPTool   │   │Workspace │
    │          │   │Router    │   │(init git)│
    └─────┬────┘   └─────┬────┘   └──────────┘
          │              │
    ┌─────▼────────────┐ │
    │ LLMProvider      │ │
    │ (Ollama/API)     │ │
    └──────────────────┘ │
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌────▼─────┐   ┌────▼──────┐
    │MCPClient │    │MCPClient │   │MCPClient  │
    │Filesystem│    │   Git    │   │ Pharmacy  │
    └─────┬────┘    └─────┬────┘   └────┬──────┘
          │               │             │
    ┌─────▼──────┐  ┌─────▼──────┐  ┌──▼──────────┐
    │ stdio_      │  │ stdio_     │  │ stdio_      │
    │ transport  │  │ transport  │  │ transport   │
    │ (npx)      │  │ (uvx)      │  │ (python)    │
    └─────┬──────┘  └─────┬──────┘  └──┬──────────┘
          │               │            │
    ┌─────▼──────────────────────┬────▼─────────┐
    │ JSON-RPC 2.0               │              │
    │ (newline-delimited)        │              │
    └────────────────────────────┴──────────────┘
```

**Layer breakdown:**
1. **LLM Layer**: `LLMProvider` (Anthropic/Ollama) — handles tool-calling loop
2. **Orchestration Layer**: `LLMClient` + `MCPToolRouter` — context + tool dispatch
3. **Protocol Layer**: `MCPClient` + transport — JSON-RPC 2.0 over stdio/HTTP
4. **Tool Servers**: Official (Filesystem, Git) + custom (Pharmacy)

## Project Structure

```
proyecto1-mcp/
├── README.md                          # This file
├── requirements.txt
├── .env.example
├── .gitignore
├── main.py                            # Entry point
│
├── src/
│   ├── config.py                      # Load .env configuration
│   ├── workspace.py                   # Bootstrap git/fs workspace
│   ├── interaction_logger.py          # Log all MCP + LLM exchanges
│   ├── llm_client.py                  # Chatbot session (context + tool routing)
│   │
│   ├── llm/                           # LLM provider abstraction
│   │   ├── base.py                    # LLMProvider interface
│   │   ├── types.py                   # ToolSpec, ToolCall, CompletionResult
│   │   ├── anthropic_provider.py      # Anthropic API implementation
│   │   ├── ollama_provider.py         # Ollama local LLM implementation
│   │   └── factory.py                 # Provider factory (Anthropic vs Ollama)
│   │
│   └── mcp/                           # MCP protocol (hand-implemented)
│       ├── jsonrpc.py                 # JSON-RPC 2.0 utilities
│       ├── stdio_transport.py         # Subprocess stdio communication
│       ├── client.py                  # MCPClient (initialize → tools/list → tools/call)
│       └── tool_router.py             # Aggregate tools, prefix names, execute
│
├── server_local/
│   ├── server.py                  # JSON-RPC protocol + tool handlers
│   ├── store.py                   # Business logic (medications, appointments)
│   └── data/
│           ├── catalog_seed.json      # Initial dataset (git-tracked)
│           └── pharmacy_data.json     # Runtime state (generated, git-ignored)
│
├── server_externo/
│      #WIP  #WIP #WIP #WIP #WIP #WIP #WIP
|  
├── scripts/                           # Validation & testing (not deliverables)
│   ├── echo_server.py                 # Minimal test server (Fase 2)
│   ├── test_mcp_client.py             # Validate MCPClient protocol
│   ├── test_filesystem_git.py         # Validate official servers
│   └── test_pharmacy_server.py        # Validate custom server (all 8 tools)
│
├── logs/
│   └── interactions.jsonl             # MCP + LLM request/response log (gitignored)
├── docs/
│   └── Proyecto1_Redes.pdf             # Written report
│
└── mcp_workspace/                     # Filesystem/Git working directory (gitignored)
```

## Detailed Component Overview

### 1. LLM Abstraction (`src/llm/`)

The project supports multiple LLM backends without code changes:

**Anthropic (`anthropic_provider.py`)**:
- Uses official Anthropic SDK
- Supports native tool-calling with Claude
- Handles `stop_reason == "tool_use"` and `tool_use` blocks in responses

**Ollama (`ollama_provider.py`)**:
- HTTP POST to local Ollama server (`http://localhost:11434/api/chat`)
- Supports OpenAI-compatible tool-calling format
- Handles `tool_calls` array in response messages

Both implement the same `LLMProvider` interface:
```python
def complete(
    messages: List[Dict],
    tools: Optional[List[ToolSpec]],
    tool_executor: Optional[Callable],
    max_tokens: int
) -> CompletionResult
```

### 2. MCP Protocol Implementation (`src/mcp/`)

**Implemented by hand** — no official MCP SDK used. Follows [JSON-RPC 2.0](https://www.jsonrpc.org/specification) and [MCP specification](https://modelcontextprotocol.io/specification/2025-11-25).

**Key protocol aspects:**
- **Framing**: One JSON-RPC message per line (newline-delimited)
- **Lifecycle**: `initialize` → `notifications/initialized` → `tools/list` → `tools/call` (loop)
- **Error handling**: Business errors (`isError: true`) vs protocol errors (`error` object)
- **Threading**: Separate thread reads server stdout to handle async notifications

### 3. Tool Routing (`src/mcp/tool_router.py`)

Aggregates multiple `MCPClient` servers and exposes unified tool list to the LLM:

- **Prefix naming**: `filesystem__write_file`, `git__git_commit`, `pharmacy__search_medications`
- **Dispatch**: Parses tool name, finds owner server, executes `tools/call`
- **Result handling**: Extracts `content[0].text` from MCP result, formats as string

### 4. Custom Pharmacy/Clinic Server (`servers/custom_server/`)

**8 tools:**
- `search_medications(query)` — find drugs by symptom/name
- `get_medication_details(medication_id)` — price, stock, prescription requirement
- `purchase_medication(medication_id, quantity, customer_name)` — decrement stock, create order
- `cancel_order(order_id)` — cancel and restore stock
- `list_available_slots(specialty?, date?)` — clinic openings
- `schedule_appointment(patient_name, specialty, slot_id)` — book slot
- `cancel_appointment(appointment_id)` — cancel and free slot
- `get_customer_history(customer_name)` — orders + appointments

**Data persistence**: File-based (`catalog_seed.json` → `pharmacy_data.json`)

## Usage Examples

### Example 1: Search and Buy Medication

```
Tú: tengo dolor de cabeza, ¿qué me recomiendas?

Claude: Para el dolor de cabeza, te recomiendo:
- Paracetamol 500mg ($15.50) - analgésico general
- Ibuprofeno 400mg ($18.00) - antiinflamatorio

¿Quieres comprar alguno?

Tú: sí, dame 2 Paracetamol

Claude: Listo, compré 2 Paracetamol 500mg por $31.00. Orden: ord-0001
```

### Example 2: Schedule Appointment + Create Documentation

```
Tú: necesito agendar una cita de oftalmología y crear un archivo de registro

Claude: Horarios disponibles de Oftalmología:
- slot-oft-1: 2026-09-01 09:00
- slot-oft-2: 2026-09-01 10:00

¿Cuál prefieres?

Tú: la primera, a nombre de Juan García. Y crea un archivo llamado "cita_oftalmo.txt"

Claude: Listo:
1. Cita agendada: apt-0001 (Juan García, Oftalmología, 2026-09-01 09:00)
2. Archivo creado y commiteado al repo
```

## Validation Scripts

Run these to test components in isolation (without LLM):

```bash
# Validate MCPClient protocol against minimal echo server
python scripts/test_mcp_client.py

# Validate Filesystem + Git official servers work together
python scripts/test_filesystem_git.py

# Validate custom Pharmacy server (all 8 tools)
python scripts/test_pharmacy_server.py
```

All should complete with "OK" messages. These are useful for debugging:
- If the LLM behaves oddly, run these first to confirm servers are fine
- Check `logs/interactions.jsonl` to see exact JSON-RPC exchanges

## Logging & Debugging

Every MCP exchange + LLM call is logged to `logs/interactions.jsonl`:

```jsonl
{"timestamp":"2026-08-24T19:44:31.006341+00:00","direction":"request","source":"mcp:filesystem","method":"tools/list","payload":{...}}
{"timestamp":"2026-08-24T19:44:31.058554+00:00","direction":"response","source":"mcp:filesystem","method":"tools/list","payload":{...}}
```

Use this for:
- **Debugging**: See exact requests/responses
- **Network analysis**: Feed to Wireshark for OSI layer analysis
- **Evidence**: Screenshot key exchanges for your final report

## Known Limitations & Design Decisions

1. **Tool ID grounding**: To prevent the LLM from inventing medication/appointment IDs in follow-up turns, tool results are embedded in the conversation history (invisible to the user). See `src/llm_client.py` for details.

2. **Pharmacy `git_init` workaround**: The official MCP git server doesn't expose `git_init` as a tool, and it fails on non-repo directories. Solution: `src/workspace.py` initializes the repo before launching the server. This is handled transparently when you run `python main.py`.

3. **Single-writer persistence**: The Pharmacy server uses a file-based store with basic locking. Fine for a demo; in production you'd use a real database.

4. **No concurrent sessions**: One chatbot session at a time. The LLM provider (Ollama/Anthropic) is shared.

5. **Model-dependent tool quality**: Ollama small models (qwen2.5:7b) sometimes struggle with tool-calling logic. If you see incorrect arguments or made-up IDs, try Claude or a larger local model.

## Development Notes

### Adding a New MCP Server

1. **Implement protocol**: Create `server.py` that reads JSON-RPC, responds to `initialize`, `tools/list`, `tools/call`
2. **Implement business logic**: Separate from protocol (like `store.py` in the Pharmacy server)
3. **Test in isolation**: Write a validation script like `test_pharmacy_server.py`
4. **Register in main.py**: Add an `MCPClient` entry in `connect_mcp_servers()`
5. **Document**: Add a README to your server's folder with tool specs

### Switching LLM Providers

Change `.env`:
```bash
LLM_PROVIDER=anthropic        # instead of "ollama"
ANTHROPIC_API_KEY=sk-ant-...  # add your key
```

No code changes needed — `LLMFactory` handles it.

### Monitoring Network Traffic (Wireshark)

When running the remote server (Fase 5), you can capture MCP traffic:

```bash
# In a separate terminal
sudo tcpdump -i lo -w mcp_traffic.pcap tcp port <remote_port>
# Run chatbot, then Ctrl+C
# Open .pcap in Wireshark, filter: tcp.stream eq 0
```

## Project Phases Reference

**Fase 1** (10%): Basic chatbot — LLM connection, context maintenance, logging  
**Fase 2** (30%): MCP protocol — manual JSON-RPC client, stdio transport, tool discovery + calling  
**Fase 3** (30%): Official servers — Filesystem + Git, end-to-end demo (README + add + commit)  
**Fase 4** (15% + partial delivery): Custom server — Pharmacy/Clinic, 8 tools, persistence  
**Fase 5** (25%): Remote deployment — Cloud Run or Cloudflare, HTTP transport  
**Fase 6** (25%): Network analysis — Wireshark capture, OSI layer breakdown  
**Fase 7** (10%): Final report — Server specs, network analysis, conclusions  

## References

- [Model Context Protocol Spec](https://modelcontextprotocol.io/specification/2025-11-25)
- [JSON-RPC 2.0](https://www.jsonrpc.org/specification)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Anthropic Claude API](https://docs.anthropic.com)
- [MCP Architecture](https://modelcontextprotocol.io/docs/learn/architecture)

## License

Educational project for university coursework (Redes — Networks). 

## Disclaimer

The Pharmacy/Clinic dataset and recommendations are **simulated for demonstration purposes**. This is not a real medical system and should never be used for actual healthcare decisions.
