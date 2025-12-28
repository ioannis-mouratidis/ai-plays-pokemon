"""
MCP Server for Pokemon FireRed Battle Control
Exposes tools for Claude AI to play Pokemon battles
"""

import sys
import json
from typing import Any
from mcp.server.fastmcp import FastMCP

from .mgba_client import create_client, MGBAClient
from .memory_reader import MemoryReader
from .battle_detector import BattleDetector
from .battle_controller import BattleController


# Initialize MCP server
mcp = FastMCP("pokemon-firered-battle")

# Global instances (initialized on first tool call)
client: MGBAClient | None = None
memory_reader: MemoryReader | None = None
battle_detector: BattleDetector | None = None
battle_controller: BattleController | None = None


def initialize_components():
    """Initialize all components (called on first tool use)"""
    global client, memory_reader, battle_detector, battle_controller

    if client is not None:
        return  # Already initialized

    try:
        # Create mGBA client
        client = create_client("http://localhost:5000")

        # Initialize components
        memory_reader = MemoryReader(client)
        battle_detector = BattleDetector(client)
        battle_controller = BattleController(client, memory_reader, battle_detector)

        print("✓ Connected to mGBA-http successfully", file=sys.stderr)

    except Exception as e:
        raise ConnectionError(
            f"Failed to connect to mGBA-http: {str(e)}\n\n"
            "Please ensure:\n"
            "1. mGBA is running with Pokemon FireRed loaded\n"
            "2. mGBASocketServer.lua script is loaded in mGBA\n"
            "3. mGBA-http.exe is running and connected\n"
        )


# ============================================================================
# MCP TOOLS - Query Tools (Read-Only)
# ============================================================================

@mcp.tool()
def get_screenshot() -> str:
    """
    Capture current emulator screen as base64-encoded PNG image.

    NOTE: Uses a workaround - calls mGBA screenshot endpoint which saves to disk,
    then reads the most recent screenshot file.

    Returns:
        Base64-encoded PNG string (240x160 pixels), or error if unavailable
    """
    initialize_components()
    try:
        return client.get_screenshot_base64()
    except NotImplementedError as e:
        return json.dumps({
            "error": "Screenshot functionality not available",
            "reason": str(e),
            "workaround": "Use get_current_pokemon_state and other memory reading tools to understand battle state"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to capture screenshot",
            "reason": str(e)
        }, indent=2)


@mcp.tool()
def get_current_pokemon_state() -> dict[str, Any]:
    """
    Get the active Pokemon's full battle statistics.

    Returns detailed information about your current Pokemon including:
    - Species name and level
    - Current and max HP
    - All stats (attack, defense, speed, special attack, special defense)
    - Status condition
    - Available moves with PP

    Returns:
        Dictionary with Pokemon stats, or error if not in battle
    """
    initialize_components()

    if not battle_detector.is_in_battle():
        return {"error": "Not currently in a battle"}

    try:
        # Get the actual active slot instead of hardcoding slot 1
        active_slot = memory_reader.get_active_party_slot()
        pokemon = memory_reader.get_party_pokemon(active_slot)

        if not pokemon["exists"]:
            return {"error": "No active Pokemon found"}

        return {
            "active_slot": active_slot,
            "species": pokemon["species"],
            "level": pokemon["level"],
            "current_hp": pokemon["current_hp"],
            "max_hp": pokemon["max_hp"],
            "attack": pokemon["attack"],
            "defense": pokemon["defense"],
            "speed": pokemon["speed"],
            "sp_attack": pokemon["sp_attack"],
            "sp_defense": pokemon["sp_defense"],
            "status": pokemon["status"],
            "can_battle": pokemon["can_battle"],
            "moves": pokemon["moves"]
        }

    except Exception as e:
        return {"error": f"Failed to read Pokemon state: {str(e)}"}


@mcp.tool()
def get_enemy_pokemon_state() -> dict[str, Any]:
    """
    Get the enemy Pokemon's VISIBLE information only (realistic gameplay).

    Returns only what a player would see on screen:
    - Species name and level
    - HP bar status (color: green/yellow/red)
    - Approximate HP percentage
    - Status condition (if visible)

    Does NOT reveal:
    - Exact HP numbers
    - Stats
    - Move list
    - PP remaining

    Returns:
        Dictionary with visible enemy info, or error if not in battle
    """
    initialize_components()

    if not battle_detector.is_in_battle():
        return {"error": "Not currently in a battle"}

    try:
        enemy = memory_reader.get_enemy_pokemon(1)

        if not enemy["exists"]:
            return {"error": "No enemy Pokemon found"}

        return enemy

    except Exception as e:
        return {"error": f"Failed to read enemy state: {str(e)}"}


@mcp.tool()
def get_team_state() -> dict[str, Any]:
    """
    Get status of all Pokemon in your party, including fainted ones.

    Returns information for all party Pokemon including:
    - Species and level
    - Current/max HP
    - Status condition
    - Whether they can battle (fainted Pokemon have can_battle=False)
    - Which slot is currently active in battle

    IMPORTANT: The party array includes ALL Pokemon, even fainted ones.
    Fainted Pokemon are included because they appear in the switching menu
    (grayed out) and affect cursor positions. Check the 'can_battle' field
    to determine if a Pokemon can be switched to.

    The party array order depends on context:
    - During normal battle (main menu): Returns DEFAULT PARTY ORDER (slots 1-6)
    - During Pokemon switching menu: Returns CURRENT MENU DISPLAY ORDER

    The menu display order changes based on previous switches during battle.
    The 'active_slot' field indicates which Pokemon (by default slot number)
    is currently battling.

    Returns:
        Dictionary with party array (including fainted), active_slot, and party_size
    """
    initialize_components()

    if not battle_detector.is_in_battle():
        return {"error": "Not currently in a battle"}

    try:
        party = memory_reader.get_full_party()
        active_slot = memory_reader.get_active_party_slot()

        return {
            "party": party,
            "party_size": len(party),
            "active_slot": active_slot
        }

    except Exception as e:
        return {"error": f"Failed to read party state: {str(e)}"}


@mcp.tool()
def get_battle_status() -> dict[str, Any]:
    """
    Get current battle status and metadata.

    Returns:
        Dictionary with:
        - in_battle: Whether currently in a battle
        - battle_type: "wild", "trainer", or "none"
        - can_flee: Whether fleeing is possible
        - enemy_party_count: Number of Pokemon in enemy's party
        - enemy_alive_count: Number of enemy Pokemon that can still battle
    """
    initialize_components()

    try:
        status = battle_detector.get_battle_status()

        # Add enemy party information if in battle
        if status["in_battle"]:
            # Count enemy Pokemon
            enemy_party_count = 0
            enemy_alive_count = 0

            for slot in range(1, 7):
                try:
                    enemy_pokemon = memory_reader.get_enemy_pokemon(slot)
                    if enemy_pokemon.get("exists"):
                        enemy_party_count += 1
                        if enemy_pokemon.get("can_battle"):
                            enemy_alive_count += 1
                except Exception:
                    # Stop counting when we hit an invalid slot
                    break

            status["enemy_party_count"] = enemy_party_count
            status["enemy_alive_count"] = enemy_alive_count
        else:
            status["enemy_party_count"] = 0
            status["enemy_alive_count"] = 0

        return status

    except Exception as e:
        return {"error": f"Failed to get battle status: {str(e)}"}


# ============================================================================
# MCP TOOLS - Command Tools (Actions)
# ============================================================================

@mcp.tool()
def use_attack(move_index: int) -> dict[str, Any]:
    """
    Use one of your Pokemon's attacks.

    Executes the selected move and waits for the turn to complete.
    Returns comprehensive results including damage dealt/received.

    Args:
        move_index: Which move to use (1-4)

    Returns:
        Dictionary with:
        - success: Whether action completed
        - damage_dealt: Damage to enemy
        - damage_received: Damage from enemy's counter
        - player_hp_remaining: Your HP after turn
        - enemy_hp_remaining: Enemy HP after turn
        - player_fainted: Whether you fainted
        - enemy_fainted: Whether enemy fainted
        - error: Error message if failed
    """
    initialize_components()

    if not 1 <= move_index <= 4:
        return {"success": False, "error": "move_index must be 1-4"}

    if not battle_detector.is_in_battle():
        return {"success": False, "error": "Not currently in a battle"}

    try:
        result = battle_controller.execute_attack(move_index)
        return result

    except Exception as e:
        return {"success": False, "error": f"Exception during attack: {str(e)}"}


@mcp.tool()
def switch_pokemon(pokemon_slot: int) -> dict[str, Any]:
    """
    Switch to a different Pokemon from your party.

    Switches out your current Pokemon and brings in another.
    Enemy gets a free turn after you switch.

    Args:
        pokemon_slot: Which Pokemon to switch to (1-6)

    Returns:
        Dictionary with:
        - success: Whether switch completed
        - switched_to_pokemon: Name of new Pokemon
        - damage_received: Damage from enemy's free turn
        - player_hp_remaining: New Pokemon's HP
        - error: Error message if failed
    """
    initialize_components()

    if not 1 <= pokemon_slot <= 6:
        return {"success": False, "error": "pokemon_slot must be 1-6"}

    if not battle_detector.is_in_battle():
        return {"success": False, "error": "Not currently in a battle"}

    try:
        result = battle_controller.execute_switch(pokemon_slot)
        return result

    except Exception as e:
        return {"success": False, "error": f"Exception during switch: {str(e)}"}


# ============================================================================
# Server Entry Point
# ============================================================================

def main():
    """Run the MCP server"""
    print("Starting Pokemon FireRed Battle MCP Server...", file=sys.stderr)

    # Test connection on startup
    try:
        test_client = create_client("http://localhost:5000")
        print("✓ Successfully connected to mGBA-http", file=sys.stderr)
        print("✓ MCP Server ready - tools available for Claude", file=sys.stderr)
    except Exception as e:
        print(f"⚠ Warning: Could not connect to mGBA-http: {e}", file=sys.stderr)
        print("  Server will start anyway. Connection will be attempted when tools are used.", file=sys.stderr)

    # Start server
    mcp.run()


if __name__ == "__main__":
    main()
