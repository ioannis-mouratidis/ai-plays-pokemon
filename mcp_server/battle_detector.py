"""
Battle state detection for Pokemon FireRed
Monitors memory to detect when battles are active
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from .mgba_client import MGBAClient


class BattleDetector:
    """Detects and monitors battle state in Pokemon FireRed"""

    def __init__(self, client: MGBAClient, config_path: Optional[str] = None):
        self.client = client
        self.last_battle_state = False
        self.turn_count = 0

        # Load memory addresses
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "memory_addresses.json"

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.battle_flags_addr = int(self.config["battle"]["flags"], 16)
        self.battle_type_addr = int(self.config["battle"]["type"], 16)
        self.enemy_pokemon_addr = int(self.config["enemy_pokemon"][0], 16)

    def is_in_battle(self) -> bool:
        """
        Check if currently in a battle

        Returns:
            True if battle is active
        """
        try:
            # Read battle flags
            battle_flags = self.client.read_byte(self.battle_flags_addr)
            battle_type = self.client.read_dword(self.battle_type_addr)

            # Battle is active if flags are non-zero
            flags_active = battle_flags != 0 or battle_type != 0

            # Also verify by checking if enemy Pokemon has HP
            try:
                enemy_hp = self.client.read_word(self.enemy_pokemon_addr + 86)
                has_enemy = enemy_hp > 0
            except Exception:
                has_enemy = False

            # Battle is active if either flags are set or enemy has HP
            in_battle = flags_active or has_enemy

            return in_battle

        except Exception as e:
            print(f"Error checking battle state: {e}")
            return False

    def get_battle_type(self) -> str:
        """
        Determine type of battle

        Returns:
            "wild", "trainer", or "none"
        """
        if not self.is_in_battle():
            return "none"

        try:
            battle_type = self.client.read_dword(self.battle_type_addr)

            # Bit 3 (0x8) typically indicates trainer battle
            # This may vary by game version
            if battle_type & 0x8:
                return "trainer"
            else:
                return "wild"

        except Exception:
            return "unknown"

    def can_flee(self) -> bool:
        """
        Check if player can flee from battle

        Returns:
            True if flee is possible
        """
        battle_type = self.get_battle_type()

        # Can flee from wild battles, not trainer battles
        return battle_type == "wild"

    def detect_battle_transition(self) -> Optional[str]:
        """
        Detect when battle starts or ends

        Returns:
            "battle_started", "battle_ended", or None
        """
        current_state = self.is_in_battle()
        transition = None

        if current_state and not self.last_battle_state:
            transition = "battle_started"
            self.turn_count = 0
        elif not current_state and self.last_battle_state:
            transition = "battle_ended"
            self.turn_count = 0

        self.last_battle_state = current_state
        return transition

    def increment_turn(self):
        """Increment turn counter"""
        self.turn_count += 1

    def get_battle_status(self) -> Dict[str, Any]:
        """
        Get comprehensive battle status

        Returns:
            Dictionary with battle state information
        """
        in_battle = self.is_in_battle()

        if not in_battle:
            return {
                "in_battle": False,
                "battle_type": "none",
                "turn_number": 0,
                "can_flee": False
            }

        return {
            "in_battle": True,
            "battle_type": self.get_battle_type(),
            "turn_number": self.turn_count,
            "can_flee": self.can_flee()
        }

    def wait_for_battle_start(self, timeout_seconds: int = 30, poll_interval: float = 0.5) -> bool:
        """
        Wait for battle to start

        Args:
            timeout_seconds: Maximum time to wait
            poll_interval: How often to check (seconds)

        Returns:
            True if battle started, False if timeout
        """
        import time

        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            if self.is_in_battle():
                return True
            time.sleep(poll_interval)

        return False

    def wait_for_battle_end(self, timeout_seconds: int = 120, poll_interval: float = 0.5) -> bool:
        """
        Wait for battle to end

        Args:
            timeout_seconds: Maximum time to wait
            poll_interval: How often to check (seconds)

        Returns:
            True if battle ended, False if timeout
        """
        import time

        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            if not self.is_in_battle():
                return True
            time.sleep(poll_interval)

        return False
