# Setup Guide - AI Pokemon FireRed System

This guide will walk you through setting up the complete system for autonomous Pokemon gameplay.

## Prerequisites

- [x] Windows 10 64-bit
- [x] Python 3.10 or higher (already installed)
- [x] Python dependencies (already installed)

## Step-by-Step Setup

### 1. Download mGBA Emulator

1. Visit https://mgba.io/downloads.html
2. Download **mGBA 0.10.4** (or latest) - Windows 64-bit portable (`.7z`)
3. Extract the archive
4. Copy these files to your `emulator/` directory:
   - `mGBA.exe`
   - All `.dll` files
   - The `licenses/` folder (optional but recommended)

### 2. Download mGBA-http

1. Visit https://github.com/nikouu/mGBA-http/releases
2. Download the latest release (e.g., `mGBA-http-v1.0.0.zip`)
3. Extract the archive
4. Copy these files to your `emulator/` directory:
   - `mGBA-http.exe`
   - `mGBASocketServer.lua`
   - Any configuration files

### 3. Obtain Pokemon FireRed ROM

**IMPORTANT**: You must own a legitimate copy of Pokemon FireRed.

1. Obtain your Pokemon FireRed ROM file legally
2. Rename it to `pokemon_firered.gba`
3. Place it in the `roms/` directory

Supported versions:
- Pokemon FireRed Version 1.0 (USA)
- Pokemon FireRed Version 1.1 (USA)

### 4. Test mGBA Standalone

1. Navigate to `emulator/` folder
2. Run `mGBA.exe`
3. File → Load ROM → Select `../roms/pokemon_firered.gba`
4. Verify the game loads and runs
5. Test keyboard controls:
   - Arrow keys: D-pad
   - Z: A button
   - X: B button
   - Enter: Start
   - Backspace: Select

### 5. Load Lua Script in mGBA

1. With mGBA running and ROM loaded:
2. Go to Tools → Scripting...
3. Click "Load script" button
4. Select `mGBASocketServer.lua`
5. You should see console output indicating the script loaded:
   ```
   Socket server listening on port 8008
   ```

### 6. Test mGBA-http

1. Keep mGBA running with the Lua script loaded
2. Open a new command prompt
3. Navigate to `emulator/` folder:
   ```cmd
   cd "c:\Users\imour\Dropbox\Programming\AI plays Pokemon\emulator"
   ```
4. Run mGBA-http:
   ```cmd
   mGBA-http.exe
   ```
5. You should see:
   ```
   Connected to mGBA on port 8008
   HTTP server running on http://localhost:5000
   ```

### 7. Test HTTP API

With mGBA-http running, test the API:

**Option A: Using PowerShell**
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/game-info" -Method Get
```

**Option B: Using curl (if installed)**
```bash
curl http://localhost:5000/game-info
```

**Option C: Open in browser**
```
http://localhost:5000
```

You should see Swagger UI documentation for the API.

### 8. Test Button Press

Test sending a button press to the game:

**PowerShell:**
```powershell
$body = @{ button = "A" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:5000/button" -Method Post -Body $body -ContentType "application/json"
```

You should see the A button press execute in the game!

### 9. Test Memory Reading

Read battle flag memory:

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/memory?address=0x02022B4B&size=1" -Method Get
```

Should return a JSON response with memory data.

## Troubleshooting

### mGBA won't load ROM
- Ensure ROM file is valid Pokemon FireRed (not corrupted)
- Check file is named `pokemon_firered.gba`
- Try running mGBA as administrator

### Lua script won't load
- Ensure you selected the correct file: `mGBASocketServer.lua`
- Check mGBA console for error messages
- Verify mGBA version is 0.10.0 or higher

### mGBA-http won't connect
- Ensure mGBA is running FIRST
- Ensure Lua script is loaded in mGBA
- **Important:** Verify that the port in the Lua script (default 8008) matches the port mGBA-http is connecting to
- Check firewall isn't blocking port 8008
- Try restarting both mGBA and mGBA-http

### HTTP API returns errors
- Verify mGBA-http is running
- Check http://localhost:5000 in browser
- Ensure no other application is using port 5000
- Review mGBA-http console for error messages

### Memory addresses return wrong data
- Verify Pokemon FireRed version (v1.0 vs v1.1)
- Check if ROM is a hack/mod (addresses may differ)
- Ensure you're reading while in-game (not menu)

## Next Steps

Once everything is working:

1. Configure your AI assistant to connect to the MCP server (see [README.md](README.md))
2. Test autonomous gameplay or battle testing
3. See [AI_ASSISTANT_INSTRUCTIONS.md](AI_ASSISTANT_INSTRUCTIONS.md) for guidance on AI agent usage

## Manual Testing Checklist

- [ ] mGBA runs and loads Pokemon FireRed
- [ ] Can play game with keyboard controls
- [ ] Lua script loads without errors
- [ ] mGBA-http connects successfully
- [ ] HTTP API responds to GET requests
- [ ] Button presses work via API
- [ ] Memory reading returns valid data
- [ ] Screenshots can be captured via API
- [ ] MCP server connects to mGBA-http

You're ready to use the MCP server with your AI assistant!
