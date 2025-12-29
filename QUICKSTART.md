# Quick Start Guide

This projects aims to build a complete MCP server designed to evaluate agentic capabilities of vision-enabled LLMs by allowing them to play Pokemon FireRed autonomously.

**The Approach:** Rather than relying solely on screenshots (where LLMs are weaker), this system provides as much information and capability as possible in text form (where LLMs excel), while maintaining fairness (the agent has no more information than a human player would). The agent makes every decision, but an agent harness abstracts away the need to plan every single button press.

## What's Done ✅

- ✅ Project structure created
- ✅ All Python dependencies installed
- ✅ HTTP client for mGBA-http (mgba_client.py)
- ✅ Memory reader for Pokemon data (memory_reader.py)
- ✅ Battle state detector (battle_detector.py)
- ✅ Battle action controller (battle_controller.py)
- ✅ Complete MCP server with 8 tools (server.py)
- ✅ Configuration files
- ✅ Documentation

## What You Need to Do

### 1. Download Emulator Files

You still need to manually download:

**mGBA Emulator:**
- Go to: https://mgba.io/downloads.html
- Download: Windows 64-bit portable (`.7z` file)
- Extract to: `emulator/` folder
- Files needed: `mGBA.exe` and all `.dll` files

**mGBA-http:**
- Go to: https://github.com/nikouu/mGBA-http/releases
- Download: Latest release ZIP
- Extract to: `emulator/` folder
- Files needed: `mGBA-http.exe` and `mGBASocketServer.lua`

**Pokemon FireRed ROM:**
- Obtain legally (you must own the game)
- Place in: `roms/pokemon_firered.gba`

### 2. Test the System

**Step 1: Start mGBA**
```
1. Run emulator/mGBA.exe
2. File → Load ROM → Select roms/pokemon_firered.gba
3. Tools → Scripting → Load script → Select mGBASocketServer.lua
4. You should see "Socket server listening on port 8008"
```

**Step 2: Start mGBA-http**
```
1. Open command prompt in emulator/ folder
2. Run: mGBA-http.exe
3. You should see "HTTP server running on http://localhost:5000"
```

**Step 3: Test MCP Server**
```bash
cd "c:\Users\imour\Dropbox\Programming\AI plays Pokemon"
python -m mcp_server
```

If everything works, you'll see:
```
Starting Pokemon FireRed Battle MCP Server...
✓ Connected to mGBA-http successfully
```

### 3. Connect to Claude Desktop

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pokemon-firered-battle": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "c:\\Users\\imour\\Dropbox\\Programming\\AI plays Pokemon"
    }
  }
}
```

Restart Claude Desktop.

### 4. Test with Your AI Assistant

**Option A: Autonomous Play**
1. Load your Pokemon FireRed save game
2. Ask: "Please play the game and navigate to the nearest Pokemon Center"
3. The AI will capture screenshots, navigate using button presses, and handle any battles
4. You can intervene at any time by pressing keys directly in the emulator

**Option B: Battle Testing**
1. Navigate to a battle manually
2. Ask: "Check my current Pokemon's status"
3. The AI will use the `get_current_pokemon_state` tool
4. Ask: "What move should I use against this enemy?"
5. The AI will analyze and execute moves using high-level battle functions

## Available Tools

Your AI assistant has access to:

### Query Tools
- `get_screenshot()` - See the current game screen (240x160 PNG)
- `get_current_pokemon_state()` - Your Pokemon's full stats
- `get_enemy_pokemon_state()` - Enemy's visible info only
- `get_team_state()` - Your full party
- `get_battle_status()` - Battle active, type, can flee

### Battle Action Tools (High-Level)
- `use_attack(1-4)` - Use a move, returns turn results
- `switch_pokemon(1-6)` - Switch Pokemon

### Navigation Tool (Low-Level)
- `press_buttons(buttons, delay_ms)` - Send button sequences for overworld navigation

## File Structure

```
mcp_server/
├── server.py              # Main MCP server (8 tools defined)
├── mgba_client.py         # HTTP wrapper for mGBA-http API
├── memory_reader.py       # Parses Pokemon data from RAM
├── battle_detector.py     # Detects when battles are active
├── battle_controller.py   # Executes attacks/switches
└── __main__.py            # Entry point

config/
└── memory_addresses.json  # Pokemon FireRed RAM addresses

emulator/                  # [YOU NEED TO ADD FILES HERE]
├── mGBA.exe              # Download from mgba.io
├── mGBA-http.exe         # Download from GitHub
└── mGBASocketServer.lua  # Included with mGBA-http

roms/                     # [YOU NEED TO ADD ROM HERE]
└── pokemon_firered.gba   # Your legitimate ROM file
```

## Troubleshooting

**"Unable to connect to mGBA-http"**
- Ensure mGBA is running FIRST
- Ensure Lua script is loaded
- Ensure mGBA-http is running
- Check http://localhost:5000 in browser
- **Important:** Verify that the port in the Lua script (default 8008) matches the port mGBA-http is connecting to

**"Failed to read Pokemon state"**
- Verify ROM is Pokemon FireRed (not LeafGreen or hacks)
- Check memory addresses are correct for your version

## Next Steps

1. Download the required emulator files
2. Test the complete system end-to-end
3. Try autonomous gameplay or battle testing with your AI assistant!

## Enjoy!

You now have a working testbed for evaluating LLM agentic capabilities through autonomous Pokemon gameplay!

For detailed technical documentation, see [README.md](README.md) and [setup_guide.md](setup_guide.md).
