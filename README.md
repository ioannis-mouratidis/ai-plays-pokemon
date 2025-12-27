# AI-Controlled Pokemon FireRed Battle System

An MCP server that allows Claude AI to play Pokemon FireRed battles while you maintain manual control for navigation.

## Architecture

```
Claude Desktop → MCP Server (Python) → HTTP API → mGBA-http → mGBA GUI
```

## Quick Start

### 1. Download Required Software

**mGBA Emulator:**
- Download from: https://mgba.io/downloads.html
- Get the Windows 64-bit portable `.7z` version
- Extract to `emulator/` directory

**mGBA-http:**
- Download from: https://github.com/nikouu/mGBA-http/releases
- Get the latest release (both .exe and .lua files)
- Place in `emulator/` directory

### 2. Setup Pokemon FireRed ROM

- Obtain a legitimate Pokemon FireRed ROM file
- Place it in `roms/pokemon_firered.gba`
- This project does NOT include ROM files

### 3. Start the System

**Step 1: Start mGBA**
```
1. Run emulator/mGBA.exe
2. Load roms/pokemon_firered.gba
3. Tools → Scripting → Load Script → Select mGBASocketServer.lua
4. Verify script loaded (should see console output)
```

**Step 2: Start mGBA-http**
```
1. Run emulator/mGBA-http.exe
2. It will connect to mGBA on port 8008
3. HTTP API will be available at http://localhost:5000
```

**Step 3: Start MCP Server**
```bash
cd "c:\Users\imour\Dropbox\Programming\AI plays Pokemon"
python -m mcp_server.server
```

**Step 4: Configure Claude Desktop**

Add to `%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "pokemon-firered-battle": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "c:\\Users\\imour\\Dropbox\\Programming\\AI plays Pokemon"
    }
  }
}
```

### 4. Usage

1. Manually navigate your Pokemon to a battle
2. Ask Claude: "Check my current Pokemon's status"
3. Ask Claude: "What move should I use?"
4. Claude will analyze and execute battle commands
5. Take manual control at any time by pressing keyboard keys

## MCP Tools Available

### Query Tools
- `get_screenshot()` - Capture current game screen
- `get_current_pokemon_state()` - Your active Pokemon's stats
- `get_enemy_pokemon_state()` - Enemy's visible info (realistic gameplay)
- `get_team_state()` - Your full party status
- `get_battle_status()` - Battle active, type, can flee

### Command Tools
- `use_attack(move_index)` - Use move 1-4
- `switch_pokemon(slot)` - Switch to Pokemon 1-6

## Project Structure

```
AI plays Pokemon/
├── mcp_server/          # MCP server code
│   ├── server.py        # Main MCP server
│   ├── mgba_client.py   # HTTP client for mGBA-http
│   ├── memory_reader.py # Parse Pokemon data from memory
│   ├── battle_controller.py # Battle action execution
│   └── battle_detector.py   # Detect battle state
├── emulator/            # Downloaded emulator files
│   ├── mGBA.exe
│   ├── mGBA-http.exe
│   └── mGBASocketServer.lua
├── roms/                # Your ROM files
│   └── pokemon_firered.gba
├── config/              # Configuration
│   └── memory_addresses.json
└── tests/               # Unit tests
```

## Development

### Run Tests
```bash
pytest tests/
```

### Test MCP Server Locally
```bash
python -m mcp dev mcp_server/server.py
```

## Technical Details

- **Language**: Python 3.10+
- **MCP SDK**: 0.5.0+
- **Emulator**: mGBA (standalone)
- **Communication**: HTTP REST API (20-100ms latency)
- **Memory Access**: Pokemon FireRed RAM addresses
- **Battle Detection**: Memory flag polling

## Limitations

- Battle screen only (manual overworld navigation)
- Single Pokemon battles (no double battles yet)
- No item usage from bag (Phase 1)
- Enemy data limited to visible info (realistic gameplay)

## Future Enhancements

- Battle text OCR
- Type effectiveness calculator
- Strategic AI layer
- Multi-battle campaigns
- Web UI for live streaming
- Battle replay system

## License

This project is for educational purposes. You must own a legitimate copy of Pokemon FireRed.
