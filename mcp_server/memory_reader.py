"""
Memory reader for Pokemon FireRed
Parses Pokemon data structures from raw memory
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from .mgba_client import MGBAClient


# Pokemon species names (Gen III)
SPECIES_NAMES = {
    0: "None", 1: "Bulbasaur", 2: "Ivysaur", 3: "Venusaur", 4: "Charmander",
    5: "Charmeleon", 6: "Charizard", 7: "Squirtle", 8: "Wartortle", 9: "Blastoise",
    25: "Pikachu", 26: "Raichu", 143: "Snorlax", 150: "Mewtwo",
    # Add more as needed - simplified for now
}

# Status conditions
STATUS_CONDITIONS = {
    0: "healthy",
    1: "asleep",
    2: "poisoned",
    3: "burned",
    4: "frozen",
    5: "paralyzed",
    6: "badly_poisoned"
}

# Move names (simplified - would need full list for production)
MOVE_NAMES = {
    0: "None", 1: "Pound", 2: "Karate Chop", 33: "Tackle", 52: "Ember",
    53: "Flamethrower", 63: "Hyper Beam", 94: "Psychic", 99: "Rage",
    # Add more as needed
}


class MemoryReader:
    """Reads and parses Pokemon FireRed memory"""

    def __init__(self, client: MGBAClient, config_path: Optional[str] = None):
        self.client = client

        # Load memory addresses from config
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "memory_addresses.json"

        with open(config_path, 'r') as f:
            self.config = json.load(f)

    def _hex_to_int(self, hex_str: str) -> int:
        """Convert hex string to integer"""
        return int(hex_str, 16)

    def read_pokemon_data(self, base_address: int) -> Dict[str, Any]:
        """
        Read 100-byte Pokemon data structure

        Args:
            base_address: Starting address of Pokemon data

        Returns:
            Dictionary with Pokemon information
        """
        # Read full 100-byte structure
        data = self.client.read_memory(base_address, 100)

        offsets = self.config["pokemon_structure"]

        # Parse structure
        personality = int.from_bytes(data[offsets["personality"]:offsets["personality"]+4], 'little')
        species_id = int.from_bytes(data[offsets["species"]:offsets["species"]+2], 'little')
        level = data[offsets["level"]]
        current_hp = int.from_bytes(data[offsets["current_hp"]:offsets["current_hp"]+2], 'little')
        max_hp = int.from_bytes(data[offsets["max_hp"]:offsets["max_hp"]+2], 'little')
        attack = int.from_bytes(data[offsets["attack"]:offsets["attack"]+2], 'little')
        defense = int.from_bytes(data[offsets["defense"]:offsets["defense"]+2], 'little')
        speed = int.from_bytes(data[offsets["speed"]:offsets["speed"]+2], 'little')
        sp_attack = int.from_bytes(data[offsets["sp_attack"]:offsets["sp_attack"]+2], 'little')
        sp_defense = int.from_bytes(data[offsets["sp_defense"]:offsets["sp_defense"]+2], 'little')
        status = data[offsets["status"]]

        # Get species name
        species_name = SPECIES_NAMES.get(species_id, f"Unknown ({species_id})")

        # Get status condition
        status_condition = STATUS_CONDITIONS.get(status & 0x07, "unknown")

        # Check if Pokemon exists (HP > 0 and valid species)
        exists = current_hp > 0 and species_id > 0

        return {
            "exists": exists,
            "species": species_name,
            "species_id": species_id,
            "level": level,
            "current_hp": current_hp,
            "max_hp": max_hp,
            "attack": attack,
            "defense": defense,
            "speed": speed,
            "sp_attack": sp_attack,
            "sp_defense": sp_defense,
            "status": status_condition,
            "can_battle": current_hp > 0,
            "personality": personality
        }

    def get_party_pokemon(self, slot: int) -> Dict[str, Any]:
        """
        Get player's party Pokemon by slot (1-6)

        Args:
            slot: Pokemon slot (1-6)

        Returns:
            Pokemon data dictionary
        """
        if not 1 <= slot <= 6:
            raise ValueError("Slot must be 1-6")

        address_str = self.config["party_pokemon"][slot - 1]
        address = self._hex_to_int(address_str)

        return self.read_pokemon_data(address)

    def get_enemy_pokemon(self, slot: int) -> Dict[str, Any]:
        """
        Get enemy Pokemon by slot (1-6)

        Args:
            slot: Pokemon slot (1-6)

        Returns:
            Pokemon data dictionary (filtered for visible info only)
        """
        if not 1 <= slot <= 6:
            raise ValueError("Slot must be 1-6")

        address_str = self.config["enemy_pokemon"][slot - 1]
        address = self._hex_to_int(address_str)

        full_data = self.read_pokemon_data(address)

        # Filter to only visible information (realistic gameplay)
        return self._filter_enemy_data(full_data)

    def _filter_enemy_data(self, pokemon_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter enemy Pokemon data to only what player can see

        Returns:
            Filtered dictionary with only visible info
        """
        if not pokemon_data["exists"]:
            return {"exists": False}

        # Calculate HP bar color
        hp_percent = (pokemon_data["current_hp"] / pokemon_data["max_hp"]) * 100 if pokemon_data["max_hp"] > 0 else 0

        if hp_percent > 50:
            hp_status = "green"
        elif hp_percent > 20:
            hp_status = "yellow"
        else:
            hp_status = "red"

        # Only return what player can see in-game
        return {
            "exists": True,
            "species": pokemon_data["species"],
            "level": pokemon_data["level"],
            "hp_bar_color": hp_status,
            "hp_percentage": round(hp_percent, 1),
            "status": pokemon_data["status"],
            "can_battle": pokemon_data["can_battle"]
        }

    def get_full_party(self) -> List[Dict[str, Any]]:
        """Get all 6 party Pokemon"""
        party = []
        for slot in range(1, 7):
            pokemon = self.get_party_pokemon(slot)
            if pokemon["exists"]:
                party.append({
                    "slot": slot,
                    **pokemon
                })
        return party

    def get_current_pokemon_moves(self, slot: int = 1) -> List[Dict[str, Any]]:
        """
        Get moves for a Pokemon (simplified - would need to read move data)

        Args:
            slot: Pokemon slot

        Returns:
            List of move dictionaries
        """
        # Note: Full implementation would read from Pokemon move data structure
        # For now, return placeholder
        # Move data is at offset 44-56 in Pokemon structure (4 moves, 2 bytes each + 1 PP byte)

        pokemon_addr_str = self.config["party_pokemon"][slot - 1]
        pokemon_addr = self._hex_to_int(pokemon_addr_str)

        # Read move data (moves at offset 44, PP at offset 52)
        data = self.client.read_memory(pokemon_addr + 44, 12)

        moves = []
        for i in range(4):
            move_id = int.from_bytes(data[i*2:i*2+2], 'little')
            pp = data[8 + i]  # PP starts at offset +8 from moves

            if move_id > 0:
                moves.append({
                    "move_id": move_id,
                    "name": MOVE_NAMES.get(move_id, f"Move {move_id}"),
                    "pp": pp,
                    "slot": i + 1
                })

        return moves
