"""
Battle controller for Pokemon FireRed
Executes battle actions and parses turn results
"""

import sys
import time
from typing import Dict, Any, List

from .mgba_client import MGBAClient
from .memory_reader import MemoryReader
from .battle_detector import BattleDetector


class BattleController:
    """
    Controls battle actions and parses results
    """

    def __init__(self, client: MGBAClient, memory_reader: MemoryReader, battle_detector: BattleDetector):
        self.client = client
        self.memory = memory_reader
        self.detector = battle_detector

    def capture_battle_state(self) -> Dict[str, Any]:
        """
        Capture current battle state (before action)

        Returns:
            Dictionary with HP and status for player and enemy, or None if failed
        """
        try:
            player = self.memory.get_party_pokemon(1)
            enemy_full = self.memory.read_pokemon_data(
                int(self.memory.config["enemy_pokemon"][0], 16)
            )

            return {
                "player_hp": player["current_hp"],
                "player_max_hp": player["max_hp"],
                "player_status": player["status"],
                "enemy_hp": enemy_full["current_hp"],
                "enemy_max_hp": enemy_full["max_hp"],
                "enemy_status": enemy_full["status"],
                "timestamp": time.time()
            }
        except Exception as e:
            print(f"Error capturing battle state: {e}", file=sys.stderr)
            return None

    def wait_for_turn_completion(self, pre_state: Dict[str, Any], max_wait_seconds: int = 10) -> bool:
        """
        Wait for turn to complete by detecting HP changes

        Args:
            pre_state: State before action
            max_wait_seconds: Maximum time to wait

        Returns:
            True if turn completed, False if timeout
        """
        start_time = time.time()
        poll_interval = 0.1  # Check every 100ms

        while time.time() - start_time < max_wait_seconds:
            time.sleep(poll_interval)

            current_state = self.capture_battle_state()

            # Check if HP changed (indicates turn completed)
            if current_state:
                hp_changed = (
                    current_state["player_hp"] != pre_state["player_hp"] or
                    current_state["enemy_hp"] != pre_state["enemy_hp"]
                )

                # Also check if battle ended
                battle_ended = not self.detector.is_in_battle()

                if hp_changed or battle_ended:
                    # Wait a bit more for animations to finish
                    time.sleep(0.5)
                    return True

        return False  # Timeout

    def calculate_turn_results(self, pre_state: Dict[str, Any], post_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate what happened during the turn by comparing states

        Args:
            pre_state: State before action
            post_state: State after action

        Returns:
            Dictionary with damage and status changes
        """
        damage_dealt = max(0, pre_state["enemy_hp"] - post_state["enemy_hp"])
        damage_received = max(0, pre_state["player_hp"] - post_state["player_hp"])

        return {
            "damage_dealt": damage_dealt,
            "damage_received": damage_received,
            "player_hp_remaining": post_state["player_hp"],
            "player_max_hp": post_state["player_max_hp"],
            "enemy_hp_remaining": post_state["enemy_hp"],
            "enemy_max_hp": post_state["enemy_max_hp"],
            "player_fainted": post_state["player_hp"] == 0,
            "enemy_fainted": post_state["enemy_hp"] == 0,
            "player_status_changed": pre_state["player_status"] != post_state["player_status"],
            "enemy_status_changed": pre_state["enemy_status"] != post_state["enemy_status"],
            "new_player_status": post_state["player_status"],
            "new_enemy_status": post_state["enemy_status"]
        }

    def execute_attack(self, move_index: int) -> Dict[str, Any]:
        """
        Execute an attack move

        Args:
            move_index: Move slot (1-4)

        Returns:
            Dictionary with turn results
        """
        if not 1 <= move_index <= 4:
            return {"success": False, "error": "Invalid move index (must be 1-4)"}

        if not self.detector.is_in_battle():
            return {"success": False, "error": "Not in battle"}

        try:
            # Capture state before action
            pre_state = self.capture_battle_state()
            if not pre_state:
                return {"success": False, "error": "Failed to capture battle state"}

            # Navigate to move and select it
            # Move layout in FireRed:
            # [1] [2]
            # [3] [4]

            # First, press A to confirm "FIGHT" option (usually default)
            self.client.press_button("A")
            time.sleep(0.3)  # Wait for menu to appear

            # Navigate to move
            if move_index == 1:
                # Top-left (default position)
                pass
            elif move_index == 2:
                # Top-right
                self.client.press_button("RIGHT")
                time.sleep(0.1)
            elif move_index == 3:
                # Bottom-left
                self.client.press_button("DOWN")
                time.sleep(0.1)
            elif move_index == 4:
                # Bottom-right
                self.client.press_button("DOWN")
                time.sleep(0.1)
                self.client.press_button("RIGHT")
                time.sleep(0.1)

            # Confirm move selection
            self.client.press_button("A")
            time.sleep(0.2)

            # Wait for turn to complete
            turn_completed = self.wait_for_turn_completion(pre_state, max_wait_seconds=15)

            if not turn_completed:
                return {
                    "success": False,
                    "error": "Turn did not complete (timeout)",
                    "pre_state": pre_state
                }

            # Capture post-turn state
            post_state = self.capture_battle_state()
            if not post_state:
                return {"success": False, "error": "Failed to capture post-turn state"}

            # Calculate results
            results = self.calculate_turn_results(pre_state, post_state)

            # Increment turn counter
            self.detector.increment_turn()

            return {
                "success": True,
                "move_index": move_index,
                **results
            }

        except Exception as e:
            return {"success": False, "error": f"Exception during attack: {str(e)}"}

    def execute_switch(self, pokemon_slot: int) -> Dict[str, Any]:
        """
        Switch to a different Pokemon

        Args:
            pokemon_slot: Pokemon slot (1-6)

        Returns:
            Dictionary with switch results
        """
        if not 1 <= pokemon_slot <= 6:
            return {"success": False, "error": "Invalid Pokemon slot (must be 1-6)"}

        if not self.detector.is_in_battle():
            return {"success": False, "error": "Not in battle"}

        try:
            # Check if target Pokemon can battle
            target_pokemon = self.memory.get_party_pokemon(pokemon_slot)
            if not target_pokemon["exists"]:
                return {"success": False, "error": f"No Pokemon in slot {pokemon_slot}"}

            if not target_pokemon["can_battle"]:
                return {"success": False, "error": f"Pokemon in slot {pokemon_slot} has fainted"}

            # Capture state before switch
            pre_state = self.capture_battle_state()

            # Navigate to Pokemon menu
            # From battle menu: DOWN to select "POKEMON", then A
            self.client.press_button("DOWN")
            time.sleep(0.2)
            self.client.press_button("A")
            time.sleep(0.5)  # Wait for Pokemon menu to open

            # Navigate to target Pokemon (slots are vertical list)
            for _ in range(pokemon_slot - 1):
                self.client.press_button("DOWN")
                time.sleep(0.1)

            # Select Pokemon
            self.client.press_button("A")
            time.sleep(0.3)

            # Confirm switch (cursor on "SWITCH" option)
            self.client.press_button("A")
            time.sleep(0.3)

            # Wait for switch animation and enemy turn
            turn_completed = self.wait_for_turn_completion(pre_state, max_wait_seconds=10)

            if not turn_completed:
                return {"success": False, "error": "Switch did not complete (timeout)"}

            # Capture post-switch state
            post_state = self.capture_battle_state()
            results = self.calculate_turn_results(pre_state, post_state)

            # Increment turn counter
            self.detector.increment_turn()

            return {
                "success": True,
                "switched_to_slot": pokemon_slot,
                "switched_to_pokemon": target_pokemon["species"],
                **results
            }

        except Exception as e:
            return {"success": False, "error": f"Exception during switch: {str(e)}"}

    def use_item(self, item_slot: int) -> Dict[str, Any]:
        """
        Use an item from bag (future implementation)

        Args:
            item_slot: Item slot

        Returns:
            Dictionary with results
        """
        return {"success": False, "error": "Item usage not yet implemented"}
