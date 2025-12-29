# Pokemon FireRed AI Assistant Instructions

## Purpose

This is an experiment to test AI assistant performance in autonomous Pokemon FireRed gameplay using an MCP server.

**Goal:** Play Pokemon FireRed autonomously, making strategic decisions for both navigation and battles.

**You control:** Everything - overworld navigation and battle decisions

**User controls:** Can intervene at any time by pressing keys in the emulator

## How It Works

**Architecture:** AI Assistant (e.g., Claude Desktop) → MCP Server → mGBA Emulator → Pokemon FireRed

- **Gameplay Modes:**
  - Overworld: Navigate using screenshots and button presses
  - Battles: Use high-level functions for strategic combat
- **All actions are synchronous:** Wait for completion before next action
- **User can intervene:** Manual control via emulator keyboard at any time

## Understanding Game State

### For Overworld Navigation

- `get_screenshot()` - Returns 240x160 pixel PNG image
- **Use for:** Navigating routes, towns, buildings, menus
- **Resolution:** Low (Game Boy Advance native), but sufficient for navigation
- **Frequency:** Capture regularly to understand your location and surroundings

### For Battle State (More Efficient)

- `get_current_pokemon_state()` - Your active Pokemon's full stats (species, level, HP, moves, PP)
- `get_enemy_pokemon_state()` - Enemy visible info only (species, level, HP bar color, approximate HP%)
- `get_team_state()` - All party Pokemon including fainted (check can_battle field)
- `get_battle_status()` - Battle metadata (wild/trainer, can_flee, enemy party count)

**Note:** In battles, prefer specific MCP functions over screenshots for efficiency

## Taking Actions

### Navigation (Overworld)

- `press_buttons(buttons, delay_ms)` - Send button sequences for movement and menu interaction
- **Valid buttons:** A, B, Start, Select, L, R, Up, Down, Left, Right
- **Use for:** Walking, running, interacting with NPCs, opening menus, navigating dialogs
- **Strategy:** Combine with screenshots to understand where you are and where to go

### Battle Commands (High-Level)

- `use_attack(move_index)` - Execute attack (1-4), returns damage dealt/received, faint status
- `switch_pokemon(pokemon_slot)` - Switch to Pokemon (1-6), enemy gets free turn
- **Advantage:** Abstracted functions handle menu navigation and turn completion automatically

## MCP Tool Reference

### Query Tools (5)

#### 1. get_screenshot()

- **Returns:** Image (240x160 PNG)
- **Use:** Overworld navigation, visual confirmation, menu navigation, dialog reading

#### 2. get_current_pokemon_state()

- **Returns:** active_slot, species, level, current_hp, max_hp, attack, defense, speed, sp_attack, sp_defense, status, can_battle, moves (with PP)
- **Use:** Your Pokemon's complete battle stats

#### 3. get_enemy_pokemon_state()

- **Returns:** species, level, hp_color (green/yellow/red), hp_percentage, status
- **Note:** Intentionally limited to visible info only (realistic gameplay)
- **Use:** Enemy assessment

#### 4. get_team_state()

- **Returns:** party (array of all Pokemon), party_size, active_slot
- **Note:** Includes fainted Pokemon (can_battle=False), party order context-dependent
- **Use:** Team overview, switching decisions

#### 5. get_battle_status()

- **Returns:** in_battle, battle_type (wild/trainer), can_flee, enemy_party_count, enemy_alive_count
- **Use:** Battle context and metadata

### Battle Command Tools (2)

#### 6. use_attack(move_index: 1-4)

- **Returns:** success, damage_dealt, damage_received, player_hp_remaining, enemy_hp_remaining, player_fainted, enemy_fainted, error
- **Use:** Execute attacks during battles, get turn results
- **Advantage:** Handles menu navigation automatically

#### 7. switch_pokemon(pokemon_slot: 1-6)

- **Returns:** success, switched_to_pokemon, damage_received, player_hp_remaining, error
- **Note:** Enemy gets free turn after switch
- **Use:** Switch Pokemon during battle
- **Advantage:** Handles menu navigation automatically

### Navigation Tool (1)

#### 8. press_buttons(buttons: list, delay_ms: int = 100)

- **Returns:** success, buttons_pressed, button_count, total_delay_ms, error
- **Use:** Overworld navigation, menu interaction, dialog progression, NPC interaction
- **Valid buttons:** A, B, Start, Select, L, R, Up, Down, Left, Right

## Important Notes

- Enemy information is limited to what a human player would see (no exact HP/stats/moves)
- Fainted Pokemon appear in party with can_battle=False, cannot be switched to
- Party order in get_team_state() depends on context (battle menu vs switching menu)
- All actions wait for completion before returning
- Type advantages, status effects, and strategic decisions rely on your Pokemon knowledge

## Example Autonomous Gameplay Workflow

### Navigation Phase
1. Use `get_screenshot()` to see current location
2. Identify destination (e.g., Pokemon Center, next route, gym)
3. Use `press_buttons()` to move in that direction
4. Repeat screenshot → navigate until destination reached

### Battle Phase (When Encountered)
1. Battle starts (detected automatically or via screenshot)
2. Use `get_battle_status()` to confirm battle state and type (wild/trainer)
3. Use `get_current_pokemon_state()` to check your Pokemon
4. Use `get_enemy_pokemon_state()` to assess opponent
5. Use `get_team_state()` to view full party if considering switch
6. Decide: `use_attack(move_index)` or `switch_pokemon(slot)`
7. Action executes, turn completes, results returned
8. Repeat steps 3-7 until battle ends (player_fainted or enemy_fainted = true)
9. Return to navigation phase

### Dialog/Menu Phase
1. Use `get_screenshot()` to see dialog or menu
2. Use `press_buttons()` to progress dialog or select menu options
3. Continue based on goal (e.g., talk to NPC, heal at Pokemon Center, buy items)
