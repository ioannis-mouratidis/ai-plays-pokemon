# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-controlled Pokemon FireRed battle system using MCP (Model Context Protocol). Claude Desktop connects via MCP server to control Pokemon battles through mGBA emulator + mGBA-http HTTP API. User maintains manual control for navigation; AI only controls during battles.

**Architecture chain**: Claude Desktop → MCP Server (Python) → HTTP REST API → mGBA-http → mGBA Lua script → mGBA emulator

## Development Commands

### Start MCP Server
```bash
python -m mcp_server
```

### Test MCP Server Locally
```bash
python -m mcp dev mcp_server/server.py
```

### Run Tests
```bash
pytest tests/
```

### Install Package (Development Mode)
```bash
pip install -e .
```

### mGBA-http API Documentation
Complete API documentation for mGBA-http is available in [emulator/mgba-http-documentation/](emulator/mgba-http-documentation/), including endpoint references and examples.

### Test Individual Components
```bash
# Test mGBA-http connection
python -c "from mcp_server.mgba_client import create_client; client = create_client(); print('Connected:', client.is_connected())"

# Test screenshot capture
python -c "from mcp_server.mgba_client import create_client; client = create_client(); img = client.get_screenshot(); print(f'Screenshot: {img.size}')"

# Test memory reading
python -c "from mcp_server.mgba_client import create_client; from mcp_server.memory_reader import MemoryReader; client = create_client(); reader = MemoryReader(client); pokemon = reader.get_party_pokemon(1); print(pokemon)"
```

## Architecture & Data Flow

### MCP Server Tools (7 tools exposed to Claude)

**Query Tools** (read-only):
- `get_screenshot()` - Captures screen via POST to `/core/screenshot?path=<path>`, saves to `screenshots/`, returns base64 PNG
- `get_current_pokemon_state()` - Reads party Pokemon #1 from memory address 0x02024284
- `get_enemy_pokemon_state()` - Reads enemy Pokemon #1 from 0x0202402C, **filters to visible info only** (species, level, HP bar color, status)
- `get_team_state()` - Reads all 6 party Pokemon (addresses 0x02024284 through 0x02024478, 100 bytes each)
- `get_battle_status()` - Reads battle flags at 0x02022B4B and type at 0x02022B4C

**Command Tools** (actions):
- `use_attack(move_index)` - Navigates menu, presses buttons, waits for turn completion via HP change detection
- `switch_pokemon(slot)` - Opens Pokemon menu, selects target, executes switch

### Component Responsibilities

**MGBAClient** ([mgba_client.py](mcp_server/mgba_client.py)):
- HTTP wrapper for mGBA-http v0.8.1 REST API
- Endpoints use mixed capitalization: `/Core/Read8`, `/Mgba-Http/Button/Tap`, `/core/screenshot` (lowercase)
- Read/write memory byte-by-byte using `/Core/Read8` and `/Core/Write8` with `?address=<addr>` param
- Button presses via POST to `/Mgba-Http/Button/Tap?button=<Button>` (capitalized button name)
- Screenshot saves to disk via POST `/core/screenshot?path=<url_encoded_path>`, then reads file back

**MemoryReader** ([memory_reader.py](mcp_server/memory_reader.py)):
- Parses 100-byte Pokemon data structures from raw memory
- Offsets defined in [config/memory_addresses.json](config/memory_addresses.json)
- **Critical**: `_filter_enemy_data()` restricts enemy Pokemon to visible info only (realistic gameplay - AI shouldn't know hidden stats/moves)
- Species/move names use simplified dictionaries (not full Gen III database)

**BattleDetector** ([battle_detector.py](mcp_server/battle_detector.py)):
- Polls memory flags to detect battle state
- Battle active when: flags at 0x02022B4B ≠ 0 OR enemy HP > 0
- Distinguishes wild vs trainer battles via bit 3 of type flags
- Maintains turn counter

**BattleController** ([battle_controller.py](mcp_server/battle_controller.py)):
- Executes attacks/switches via button press sequences
- **Critical timing**: Move menu layout is 2x2 grid: [1][2] / [3][4]
- Turn completion detected via **state diffing** (compares pre/post HP), NOT text parsing
- Waits up to 15 seconds for HP changes to detect turn completion
- Returns synchronous turn results (damage dealt/received, faint status)

**Server** ([server.py](mcp_server/server.py)):
- FastMCP server with 7 tools
- Lazy initialization - connects to mGBA-http on first tool call
- Global instances: client, memory_reader, battle_detector, battle_controller

### Memory Address Constants (Pokemon FireRed v1.0 US)

From [config/memory_addresses.json](config/memory_addresses.json):
- Battle flags: 0x02022B4B
- Battle type: 0x02022B4C
- Party Pokemon: 0x02024284, 0x020242E8, 0x0202434C, 0x020243B0, 0x02024414, 0x02024478 (100 bytes each)
- Enemy Pokemon: 0x0202402C, 0x02024090, 0x020240F4, 0x02024158, 0x020241BC, 0x02024220 (100 bytes each)

Pokemon structure offsets (within 100-byte block):
- Species ID: +32 (2 bytes, little-endian)
- Level: +84 (1 byte)
- Current HP: +86 (2 bytes)
- Max HP: +88 (2 bytes)
- Stats (Attack/Defense/Speed/SpAtk/SpDef): +90 through +98 (2 bytes each)
- Status: +80 (1 byte)
- Moves: +44 (8 bytes = 4 moves × 2 bytes)
- PP: +52 (4 bytes = 4 moves × 1 byte)

## Critical Implementation Details

### Screenshot Implementation
**IMPORTANT**: mGBA-http screenshot endpoint requires POST with `path` parameter:
```python
response = requests.post(
    "http://localhost:5000/core/screenshot",
    params={"path": screenshot_path}  # requests library URL-encodes this
)
```
- Does NOT return image data directly
- Saves PNG to specified path on disk
- Must read file back after ~300ms delay
- Screenshots saved to `screenshots/` in project root with timestamp: `mgba_screenshot_{timestamp}.png`

### Memory Reading Pattern
All memory reads are byte-by-byte (no bulk read endpoint in v0.8.1):
```python
for offset in range(size):
    response = session.get(f"{base_url}/Core/Read8", params={"address": address + offset})
    byte_value = int(response.text.strip())  # Response is plain text number
```

### Battle Turn Detection
Uses **state diffing**, not text parsing:
1. Capture pre-turn state (HP values)
2. Execute button sequence
3. Poll memory every 100ms for HP changes
4. Detect turn completion when HP differs OR battle ends
5. Wait 500ms after detection for animations
6. Calculate damage: `pre_hp - post_hp`

### Enemy Data Filtering (Realistic Gameplay)
**Critical design decision**: Enemy Pokemon data is intentionally limited to prevent AI from having unfair knowledge:
- ✅ Visible: species, level, HP bar color (green/yellow/red), HP percentage, status condition
- ❌ Hidden: exact HP numbers, stats, move list, PP

This is enforced in `MemoryReader._filter_enemy_data()`.

### Python Path for Claude Desktop Config
Must use actual Python executable, NOT Windows Store wrapper:
```json
{
  "mcpServers": {
    "pokemon-firered-battle": {
      "command": "C:\\Users\\imour\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
      "args": ["-m", "mcp_server"],
      "cwd": "c:\\Users\\imour\\Dropbox\\Programming\\AI plays Pokemon"
    }
  }
}
```

## External Dependencies (Manual Setup Required)

The MCP server requires external files that must be downloaded separately:

1. **mGBA Emulator** - Download from https://mgba.io/downloads.html (Windows 64-bit portable)
   - Extract to `emulator/` directory
   - Needs: `mGBA.exe` and all `.dll` files

2. **mGBA-http** - Download from https://github.com/nikouu/mGBA-http/releases
   - Extract to `emulator/` directory
   - Needs: `mGBA-http.exe` and `mGBASocketServer.lua`

3. **Pokemon FireRed ROM** - User must provide legal copy
   - Place at: `roms/pokemon_firered.gba`
   - Must be FireRed v1.0 or v1.1 (US) - memory addresses differ for other versions

### Startup Sequence
1. Start mGBA.exe → Load ROM → Tools → Scripting → Load `mGBASocketServer.lua`
2. Start `mGBA-http.exe` (connects to mGBA on port 8008)
3. Start MCP server: `python -m mcp_server` (connects to mGBA-http on localhost:5000)
4. Claude Desktop auto-starts MCP server when configured

## Common Issues & Solutions

### "No module named mcp_server"
Package not installed. Run: `pip install -e .`

### Screenshot 404 errors
- Correct endpoint: POST `/core/screenshot` (lowercase)
- Must include `path` parameter
- Endpoint saves to disk, does NOT return image data

### "Unable to connect to mGBA-http"
Verify startup sequence:
1. mGBA running with Lua script loaded first
2. mGBA-http.exe running and connected
3. Check http://localhost:5000 in browser

### Memory reads return wrong data
- Verify ROM is Pokemon FireRed v1.0 (US), not LeafGreen or ROM hacks
- Addresses in config are version-specific

### Turn completion timeouts
- Increase `max_wait_seconds` in `wait_for_turn_completion()`
- Some moves (multi-turn, status effects) take longer than standard attacks
- HP change detection may fail if attack misses or does 0 damage

## Design Constraints

### What This Does
- Battle control only (AI makes decisions during active battles)
- Single Pokemon battles (1v1)
- Basic attacks and switching
- Synchronous turn-based actions with results

### What This Does NOT Do
- Overworld navigation (user does this manually)
- Item usage from bag (not implemented)
- Double battles (not supported)
- Battle text parsing/OCR (uses state diffing instead)
- Auto-save management
- Multi-turn move handling (Fly, Dig, Hyper Beam recharge)

### Intentional Limitations
- ~20-100ms HTTP latency (acceptable for turn-based battles)
- Simplified species/move name dictionaries (would need full Gen III database for production)
- Enemy data filtered to visible info only (realistic competitive gameplay)
- Screenshots saved to disk (mGBA-http limitation, not streaming)

## When Modifying This Codebase

### Adding New Memory Addresses
1. Update [config/memory_addresses.json](config/memory_addresses.json)
2. Addresses must be hex strings: `"0x02024284"`
3. Use `_hex_to_int()` to convert before passing to client

### Adding New MCP Tools
1. Define tool in [server.py](mcp_server/server.py) with `@mcp.tool()` decorator
2. Call `initialize_components()` first
3. Check battle state if tool requires active battle
4. Return dict with structured data, include `"error"` key on failure

### Modifying Battle Actions
- Update button sequences in [battle_controller.py](mcp_server/battle_controller.py)
- Respect menu layouts (2x2 move grid, vertical Pokemon list)
- Always capture pre/post state for turn results
- Wait for turn completion via `wait_for_turn_completion()`
- Increment turn counter via `detector.increment_turn()`

### Testing Without Full Setup
Use pytest mocks for `MGBAClient` HTTP calls. Example:
```python
@pytest.fixture
def mock_client():
    client = MGBAClient()
    client.is_connected = lambda: True
    client.read_memory = lambda addr, size: b'\x00' * size
    return client
```
