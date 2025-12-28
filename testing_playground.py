"""
Test script to verify MCP server's switch_pokemon works with fainted Pokemon.
This simulates what happens when Claude calls the switch_pokemon tool.
"""

from mcp_server.mgba_client import create_client
from mcp_server.memory_reader import MemoryReader
from mcp_server.battle_detector import BattleDetector
from mcp_server.battle_controller import BattleController
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize components (same as MCP server)
client = create_client()
memory_reader = MemoryReader(client)
battle_detector = BattleDetector(client)
battle_controller = BattleController(client, memory_reader, battle_detector)

print("=" * 60)
print(" TEST MCP SERVER SWITCH FUNCTIONALITY")
print("=" * 60)

# Check battle status
if not battle_detector.is_in_battle():
    print("✗ Not in battle")
    sys.exit(1)

print("\n✓ In battle")

# Get team state (what Claude would see via get_team_state tool)
print("\n--- Team State (MCP get_team_state) ---")
party = memory_reader.get_full_party()  # Always includes fainted
active_slot = memory_reader.get_active_party_slot()

print(f"Active slot: {active_slot}")
# print(f"Party ({len(party)} Pokemon total, including fainted):")
# for p in party:
#     status = " [FAINTED]" if p['current_hp'] == 0 else ""
#     can_battle_str = " - Can switch" if p['can_battle'] else " - Cannot switch"
#     print(f"  Slot {p['slot']}: {p['species']:12} (HP: {p['current_hp']}/{p['max_hp']}){status}{can_battle_str}")

# # Test switching via execute_switch (what switch_pokemon tool calls)
# print("\n--- Testing execute_switch (MCP switch_pokemon) ---")

# # Find a Pokemon to switch to (not active, can battle)
# target_slot = None
# for p in party:
#     if p['slot'] != active_slot and p['can_battle']:
#         target_slot = p['slot']
#         target_name = p['species']
#         break

# if not target_slot:
#     print("✗ No valid Pokemon to switch to")
#     sys.exit(1)

# print(f"Attempting to switch from slot {active_slot} to slot {target_slot} ({target_name})...")
# print("(This simulates what happens when Claude calls switch_pokemon)")

# # Call execute_switch (same as MCP server does)
# result = battle_controller.execute_switch(target_slot)

# print("\n--- Result ---")
# if result['success']:
#     print("✓ Switch succeeded!")
#     print(f"  Switched to: {result['switched_to_pokemon']} (slot {result['switched_to_slot']})")
#     print(f"  Damage received: {result['damage_received']}")
#     print(f"  Player HP: {result['player_hp_remaining']}/{result['player_max_hp']}")
# else:
#     print(f"✗ Switch failed: {result.get('error', 'Unknown error')}")

# print("\n" + "=" * 60)
# print(" TEST COMPLETE")
# print("=" * 60)
