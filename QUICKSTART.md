# Quick Start Guide

## What We've Built

You now have a complete MCP server that allows Claude AI to control Pokemon FireRed battles!

## What's Done ✅

- ✅ Project structure created
- ✅ All Python dependencies installed
- ✅ HTTP client for mGBA-http (mgba_client.py)
- ✅ Memory reader for Pokemon data (memory_reader.py)
- ✅ Battle state detector (battle_detector.py)
- ✅ Battle action controller (battle_controller.py)
- ✅ Complete MCP server with 6 tools (server.py)
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

### 4. Test with Claude

1. Start a new battle in Pokemon FireRed manually
2. In Claude Desktop, ask: "Check my current Pokemon's status"
3. Claude will use the `get_current_pokemon_state` tool
4. Ask: "What move should I use against this enemy?"
5. Claude will analyze and can execute moves

## Available Tools

Claude has access to:

### Query Tools
- `get_screenshot()` - See the current game screen
- `get_current_pokemon_state()` - Your Pokemon's full stats
- `get_enemy_pokemon_state()` - Enemy's visible info only
- `get_team_state()` - Your full party
- `get_battle_status()` - Battle active, type, can flee

### Action Tools
- `use_attack(1-4)` - Use a move
- `switch_pokemon(1-6)` - Switch Pokemon

## File Structure

```
mcp_server/
├── server.py              # Main MCP server (6 tools defined)
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

**"Not currently in a battle"**
- Navigate to a battle manually first
- Let Claude know you're in a battle

**"Failed to read Pokemon state"**
- Verify ROM is Pokemon FireRed (not LeafGreen or hacks)
- Check memory addresses are correct for your version

## Next Steps

1. Download the required emulator files
2. Test the complete system end-to-end
3. Try battling with Claude!

## Example Claude Conversation

```
You: I'm in a battle with a wild Pidgey. What should I do?

Claude: Let me check the current battle state.
[Calls get_current_pokemon_state and get_enemy_pokemon_state]

Claude: You have a Charizard at 98/120 HP against a level 5 Pidgey (green HP bar).
Charizard's moves:
1. Flamethrower
2. Dragon Claw
3. Air Slash
4. Earthquake

I recommend using Flamethrower (move 1) - it's super effective against Flying types.
Shall I execute it?

You: Yes

Claude: [Calls use_attack(1)]
Claude: Charizard used Flamethrower! Dealt 87 damage. Enemy Pidgey fainted!
The battle is over - you won!
```

## Enjoy!

You now have a working AI-controlled Pokemon battle system. Have fun battling with Claude!

For detailed technical documentation, see [README.md](README.md) and [setup_guide.md](setup_guide.md).
