# AI-Controlled Pokemon FireRed System

An MCP server designed to evaluate agentic capabilities of vision-enabled LLMs by allowing them to play Pokemon FireRed autonomously.

## Project Goal

This project provides an MCP layer that allows LLM-based agents with vision capabilities to play Pokemon FireRed, serving as a testbed for evaluating agentic performance. Rather than relying solely on screenshots (where LLMs are weaker), the system provides as much information and capability as possible in text form (where LLMs excel), while maintaining fairness (the agent has no more information than a human player would). The agent makes every decision, but an agent harness abstracts away the need to plan every single button press, allowing it to focus on strategic gameplay.

## Architecture

```
AI Assistant (e.g., Claude Desktop) → MCP Server (Python) → HTTP API → mGBA-http → mGBA GUI
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

Ask your AI assistant to play the game autonomously. The AI can:
- Navigate the overworld by capturing screenshots and sending button presses
- Use specialized high-level functions to control battles efficiently
- Make strategic decisions about Pokemon, moves, and party management

**Example:** "Please play the game and progress through the Viridian Forest. Use screenshots to navigate and battle any trainers you encounter."

The AI will use `get_screenshot()` and `press_buttons()` for navigation, then switch to abstracted battle functions like `use_attack()` and `switch_pokemon()` during combat for easier gameplay.

While the goal is autonomous play, you can intervene at any time by taking manual control of the emulator using keyboard inputs.

## MCP Tools Available

### Query Tools
- `get_screenshot()` - Capture current game screen (240x160 PNG)
- `get_current_pokemon_state()` - Your active Pokemon's stats
- `get_enemy_pokemon_state()` - Enemy's visible info (realistic gameplay)
- `get_team_state()` - Your full party status
- `get_battle_status()` - Battle active, type, can flee

### Battle Command Tools (High-Level)
- `use_attack(move_index)` - Use move 1-4, returns turn results
- `switch_pokemon(slot)` - Switch to Pokemon 1-6

### Navigation Tool (Low-Level)
- `press_buttons(buttons, delay_ms)` - Send button sequences for overworld navigation

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

- Single Pokemon battles (no double battles)
- No item usage from bag
- Enemy data limited to visible info (realistic gameplay)
- Overworld navigation requires screenshot analysis and manual button presses (lower-level than battle controls)

## Future Enhancements

- Improved agent harness for autonomous gameplay
- Integration with other Pokemon MCPs for type effectiveness and move data
- Pathfinding algorithms for navigation to on-screen points
- Item usage from bag
- Battle text OCR
- Double battle support

## License

This project is for educational purposes. You must own a legitimate copy of Pokemon FireRed.
