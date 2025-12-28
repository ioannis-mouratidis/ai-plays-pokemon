# Pokemon FireRed Battle AI Assistant Instructions

## Purpose

This is an experiment to test AI assistant performance in Pokemon battles using an MCP server.

**Goal:** Win battles efficiently using strategic decision-making.

**You control:** Battle decisions only (attacks, switches)

**User controls:** Overworld navigation

## How It Works

**Architecture:** Claude Desktop → MCP Server → mGBA Emulator → Pokemon FireRed

- **When battles start:** You take control
- **When battles end:** Return control to user
- **All actions are synchronous:** Wait for turn completion before next action

## Understanding Game State

### Preferred Method: Use MCP Functions (Most Efficient)

- `get_current_pokemon_state()` - Your active Pokemon's full stats (species, level, HP, moves, PP)
- `get_enemy_pokemon_state()` - Enemy visible info only (species, level, HP bar color, approximate HP%)
- `get_team_state()` - All party Pokemon including fainted (check can_battle field)
- `get_battle_status()` - Battle metadata (wild/trainer, can_flee, enemy party count)

### Fallback Method: Screenshots (Less Efficient)

Use when MCP data insufficient:

- `get_screenshot()` - Returns 240x160 pixel PNG image
- **Use for:** Menu navigation, non-battle screens, visual confirmation
- **Note:** Low resolution, prefer MCP functions when possible

## Taking Actions

### Battle Commands

- `use_attack(move_index)` - Execute attack (1-4), returns damage dealt/received, faint status
- `switch_pokemon(pokemon_slot)` - Switch to Pokemon (1-6), enemy gets free turn

### Low-Level Control

- `press_buttons(buttons, delay_ms)` - Button sequences for menus/navigation
- **Valid buttons:** A, B, Start, Select, L, R, Up, Down, Left, Right
- **Use sparingly:** Prefer high-level battle commands when available

## MCP Tool Reference

### Query Tools (5)

#### 1. get_screenshot()

- **Returns:** Image (240x160 PNG)
- **Use:** Visual confirmation, non-battle screens

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

### Command Tools (3)

#### 6. use_attack(move_index: 1-4)

- **Returns:** success, damage_dealt, damage_received, player_hp_remaining, enemy_hp_remaining, player_fainted, enemy_fainted, error
- **Use:** Execute attacks, get turn results

#### 7. switch_pokemon(pokemon_slot: 1-6)

- **Returns:** success, switched_to_pokemon, damage_received, player_hp_remaining, error
- **Note:** Enemy gets free turn after switch
- **Use:** Switch Pokemon during battle

#### 8. press_buttons(buttons: list, delay_ms: int = 100)

- **Returns:** success, buttons_pressed, button_count, total_delay_ms, error
- **Use:** Low-level menu navigation, fallback control

## Important Notes

- Enemy information is limited to what a human player would see (no exact HP/stats/moves)
- Fainted Pokemon appear in party with can_battle=False, cannot be switched to
- Party order in get_team_state() depends on context (battle menu vs switching menu)
- All actions wait for completion before returning
- Type advantages, status effects, and strategic decisions rely on your Pokemon knowledge

## Example Battle Workflow

1. Battle starts (user navigates to wild Pokemon/trainer)
2. Use `get_current_pokemon_state()` to check your Pokemon
3. Use `get_enemy_pokemon_state()` to assess opponent
4. Use `get_team_state()` to view full party if considering switch
5. Decide: `use_attack(move_index)` or `switch_pokemon(slot)`
6. Action executes, turn completes, results returned
7. Repeat until battle ends (player_fainted or enemy_fainted = true)
8. Return control to user for navigation
