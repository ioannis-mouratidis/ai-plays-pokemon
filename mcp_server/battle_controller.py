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
            # Get the actual active slot instead of hardcoding slot 1
            active_slot = self.memory.get_active_party_slot()
            player = self.memory.get_party_pokemon(active_slot)
            enemy_full = self.memory.read_pokemon_data(
                int(self.memory.config["enemy_pokemon"][0], 16)
            )

            return {
                "active_slot": active_slot,
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

    def get_move_cursor_position(self) -> int:
        """
        Read current move cursor position from memory

        Returns:
            Current cursor position (1-4), or 1 if read fails
        """
        try:
            cursor_address = int(self.memory.config["battle"]["move_menu_cursor"], 16)
            cursor_value = self.client.read_memory(cursor_address, 1)[0]
            # Memory stores 0-3, convert to 1-4
            return cursor_value + 1 if 0 <= cursor_value <= 3 else 1
        except Exception as e:
            print(f"Warning: Could not read move cursor position: {e}", file=sys.stderr)
            return 1  # Default to position 1 on error

    def get_battle_menu_cursor_position(self) -> int:
        """
        Read current battle menu cursor position from memory

        Returns:
            Current cursor position (1-4), or 1 if read fails
            1 = FIGHT (top-left)
            2 = BAG (top-right)
            3 = POKEMON (bottom-left)
            4 = RUN (bottom-right)
        """
        try:
            cursor_address = int(self.memory.config["battle"]["battle_menu_cursor"], 16)
            cursor_value = self.client.read_memory(cursor_address, 1)[0]
            # Memory stores 0-3, convert to 1-4
            return cursor_value + 1 if 0 <= cursor_value <= 3 else 1
        except Exception as e:
            print(f"Warning: Could not read battle menu cursor position: {e}", file=sys.stderr)
            return 1  # Default to position 1 (FIGHT) on error

    def get_pokemon_menu_cursor_position(self) -> int:
        """
        Read current Pokemon menu cursor position from memory

        Returns:
            Current cursor position (0-5 for Pokemon, 7 for Cancel), or 0 if read fails
        """
        try:
            cursor_address = int(self.memory.config["battle"]["pokemon_menu_cursor"], 16)
            cursor_value = self.client.read_memory(cursor_address, 1)[0]

            # Valid values: 0-5 (Pokemon slots) or 7 (Cancel button)
            if cursor_value in list(range(6)) + [7]:
                return cursor_value
            else:
                return 0  # Default to first position

        except Exception as e:
            print(f"Warning: Could not read Pokemon menu cursor: {e}", file=sys.stderr)
            return 0

    def navigate_to_battle_menu_option(self, current_pos: int, target_pos: int):
        """
        Navigate from current cursor position to target battle menu option

        Args:
            current_pos: Current cursor position (1-4)
            target_pos: Target option position (1-4)

        Battle menu grid:
        [1: FIGHT]    [2: BAG]
        [3: POKEMON]  [4: RUN]

        Position mapping:
        1 = (row 0, col 0) - FIGHT
        2 = (row 0, col 1) - BAG
        3 = (row 1, col 0) - POKEMON
        4 = (row 1, col 1) - RUN
        """
        if current_pos == target_pos:
            return  # Already at target

        # Convert positions to (row, col)
        def pos_to_coords(pos):
            return ((pos - 1) // 2, (pos - 1) % 2)

        current_row, current_col = pos_to_coords(current_pos)
        target_row, target_col = pos_to_coords(target_pos)

        # Navigate vertically first
        if target_row > current_row:
            self.client.press_button("DOWN")
            time.sleep(0.1)
        elif target_row < current_row:
            self.client.press_button("UP")
            time.sleep(0.1)

        # Navigate horizontally
        if target_col > current_col:
            self.client.press_button("RIGHT")
            time.sleep(0.1)
        elif target_col < current_col:
            self.client.press_button("LEFT")
            time.sleep(0.1)

    def select_battle_menu_option(self, option: str) -> bool:
        """
        Navigate to and select a battle menu option

        Args:
            option: One of "FIGHT", "BAG", "POKEMON", "RUN"

        Returns:
            True if successful, False on error
        """
        # Map option names to positions
        option_map = {
            "FIGHT": 1,
            "BAG": 2,
            "POKEMON": 3,
            "RUN": 4
        }

        # Wait times after pressing A for each option
        wait_times = {
            "FIGHT": 0.3,    # Wait for move menu to appear
            "BAG": 0.4,      # Wait for item menu
            "POKEMON": 0.5,  # Wait for party menu to appear
            "RUN": 0.2       # Wait for flee attempt
        }

        option_upper = option.upper()

        # Validate option
        if option_upper not in option_map:
            print(f"Error: Invalid battle menu option '{option}'. Must be one of: FIGHT, BAG, POKEMON, RUN", file=sys.stderr)
            return False

        try:
            # Get target position
            target_pos = option_map[option_upper]

            # Read current cursor position
            current_pos = self.get_battle_menu_cursor_position()

            # Navigate to target option
            self.navigate_to_battle_menu_option(current_pos, target_pos)

            # Press A to confirm selection
            self.client.press_button("A")

            # Wait appropriate time for submenu to appear
            time.sleep(wait_times[option_upper])

            return True

        except Exception as e:
            print(f"Error selecting battle menu option '{option}': {e}", file=sys.stderr)
            return False

    def navigate_to_move(self, current_pos: int, target_pos: int):
        """
        Navigate from current cursor position to target move

        Args:
            current_pos: Current cursor position (1-4)
            target_pos: Target move index (1-4)

        Move grid:
        [1] [2]
        [3] [4]

        Position mapping:
        1 = (row 0, col 0)
        2 = (row 0, col 1)
        3 = (row 1, col 0)
        4 = (row 1, col 1)
        """
        if current_pos == target_pos:
            return  # Already at target

        # Convert positions to (row, col)
        def pos_to_coords(pos):
            return ((pos - 1) // 2, (pos - 1) % 2)

        current_row, current_col = pos_to_coords(current_pos)
        target_row, target_col = pos_to_coords(target_pos)

        # Navigate vertically first
        if target_row > current_row:
            self.client.press_button("DOWN")
            time.sleep(0.1)
        elif target_row < current_row:
            self.client.press_button("UP")
            time.sleep(0.1)

        # Navigate horizontally
        if target_col > current_col:
            self.client.press_button("RIGHT")
            time.sleep(0.1)
        elif target_col < current_col:
            self.client.press_button("LEFT")
            time.sleep(0.1)

    def navigate_to_pokemon_position(self, target_position: int) -> bool:
        """
        Navigate the Pokemon menu cursor to a specific position.

        Strategy:
        1. Read current cursor position
        2. Calculate number of presses needed and which direction
        3. Press UP or DOWN that many times
        4. Verify we reached the target
        5. Retry up to 2 times if verification fails

        Args:
            target_position: Target position (0-5)

        Returns:
            True if successfully navigated, False otherwise
        """
        if not 0 <= target_position <= 5:
            return False

        max_retries = 2

        for attempt in range(max_retries + 1):
            # Read current position
            current_pos = self.get_pokemon_menu_cursor_position()

            # Calculate how many presses needed and which direction
            if current_pos < target_position:
                # Need to go down
                button = "DOWN"
                presses_needed = target_position - current_pos
            elif current_pos > target_position:
                # Need to go up
                button = "UP"
                presses_needed = current_pos - target_position
            else:
                # Already at target
                return True

            # Press the button the calculated number of times
            for _ in range(presses_needed):
                self.client.press_button(button)
                time.sleep(0.1)

            # Wait for cursor to settle
            time.sleep(0.2)

            # Verify we reached the target
            final_pos = self.get_pokemon_menu_cursor_position()
            if final_pos == target_position:
                return True

            # If not at target and we have retries left, try again
            print(f"Navigation attempt {attempt + 1} failed: at position {final_pos}, expected {target_position}", file=sys.stderr)

        return False  # Failed after all retries

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

            # Navigate to FIGHT option and select it
            if not self.select_battle_menu_option("FIGHT"):
                return {"success": False, "error": "Failed to select FIGHT option"}

            # Read current cursor position in move menu from memory
            current_cursor_pos = self.get_move_cursor_position()

            # Navigate from current position to target move
            self.navigate_to_move(current_cursor_pos, move_index)

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

            # Check if trying to switch to already active Pokemon
            active_slot = self.memory.get_active_party_slot()
            if pokemon_slot == active_slot:
                return {"success": False, "error": "Pokemon is already active in battle"}

            # Read party BEFORE opening menu to identify target Pokemon
            # (at this point, get_full_party() returns default slot order)
            party_before_menu = self.memory.get_full_party()

            # Find target Pokemon by slot number
            target_pokemon_data = None
            for pokemon in party_before_menu:
                if pokemon['slot'] == pokemon_slot:
                    target_pokemon_data = pokemon
                    break

            # Validate (this is redundant with checks above, but defensive)
            if not target_pokemon_data:
                return {"success": False, "error": f"Pokemon slot {pokemon_slot} not found"}
            if not target_pokemon_data['can_battle']:
                return {"success": False, "error": f"Pokemon in slot {pokemon_slot} cannot battle"}

            # Capture state before switch
            pre_state = self.capture_battle_state()

            # Navigate to POKEMON option and select it
            if not self.select_battle_menu_option("POKEMON"):
                return {"success": False, "error": "Failed to select POKEMON option"}

            # Wait for menu to open
            time.sleep(0.2)

            # Read party AFTER opening menu - now returns menu display order
            # (which may differ from default slot order after previous switches)
            # This always includes fainted Pokemon since the menu shows them
            party_in_menu = self.memory.get_full_party()

            # Find target Pokemon in menu by comparing entire Pokemon object
            # This handles duplicate species correctly (e.g., two Rattata)
            target_position = None
            for i, pokemon in enumerate(party_in_menu):
                # Compare all identifying fields to ensure exact match
                if (pokemon['species_id'] == target_pokemon_data['species_id'] and
                    pokemon['level'] == target_pokemon_data['level'] and
                    pokemon['current_hp'] == target_pokemon_data['current_hp'] and
                    pokemon['max_hp'] == target_pokemon_data['max_hp']):
                    target_position = i
                    break

            if target_position is None:
                return {"success": False, "error": f"Target Pokemon not found in menu"}

            # Navigate cursor to target position
            if not self.navigate_to_pokemon_position(target_position):
                return {"success": False, "error": f"Failed to navigate to position {target_position}"}

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
