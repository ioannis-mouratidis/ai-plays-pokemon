"""
Memory reader for Pokemon FireRed
Parses Pokemon data structures from raw memory
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from .mgba_client import MGBAClient


# Substructure order lookup table (24 possible orders based on personality % 24)
SUBSTRUCTURE_ORDER = [
    [0, 1, 2, 3], [0, 1, 3, 2], [0, 2, 1, 3], [0, 2, 3, 1], [0, 3, 1, 2], [0, 3, 2, 1],
    [1, 0, 2, 3], [1, 0, 3, 2], [1, 2, 0, 3], [1, 2, 3, 0], [1, 3, 0, 2], [1, 3, 2, 0],
    [2, 0, 1, 3], [2, 0, 3, 1], [2, 1, 0, 3], [2, 1, 3, 0], [2, 3, 0, 1], [2, 3, 1, 0],
    [3, 0, 1, 2], [3, 0, 2, 1], [3, 1, 0, 2], [3, 1, 2, 0], [3, 2, 0, 1], [3, 2, 1, 0],
]

# Pokemon species names (Gen III - FireRed/LeafGreen national dex)
SPECIES_NAMES = {
    0: "None", 1: "Bulbasaur", 2: "Ivysaur", 3: "Venusaur", 4: "Charmander",
    5: "Charmeleon", 6: "Charizard", 7: "Squirtle", 8: "Wartortle", 9: "Blastoise",
    10: "Caterpie", 11: "Metapod", 12: "Butterfree", 13: "Weedle", 14: "Kakuna",
    15: "Beedrill", 16: "Pidgey", 17: "Pidgeotto", 18: "Pidgeot", 19: "Rattata",
    20: "Raticate", 21: "Spearow", 22: "Fearow", 23: "Ekans", 24: "Arbok",
    25: "Pikachu", 26: "Raichu", 27: "Sandshrew", 28: "Sandslash", 29: "Nidoran♀",
    30: "Nidorina", 31: "Nidoqueen", 32: "Nidoran♂", 33: "Nidorino", 34: "Nidoking",
    35: "Clefairy", 36: "Clefable", 37: "Vulpix", 38: "Ninetales", 39: "Jigglypuff",
    40: "Wigglytuff", 41: "Zubat", 42: "Golbat", 43: "Oddish", 44: "Gloom",
    45: "Vileplume", 46: "Paras", 47: "Parasect", 48: "Venonat", 49: "Venomoth",
    50: "Diglett", 51: "Dugtrio", 52: "Meowth", 53: "Persian", 54: "Psyduck",
    55: "Golduck", 56: "Mankey", 57: "Primeape", 58: "Growlithe", 59: "Arcanine",
    60: "Poliwag", 61: "Poliwhirl", 62: "Poliwrath", 63: "Abra", 64: "Kadabra",
    65: "Alakazam", 66: "Machop", 67: "Machoke", 68: "Machamp", 69: "Bellsprout",
    70: "Weepinbell", 71: "Victreebel", 72: "Tentacool", 73: "Tentacruel", 74: "Geodude",
    75: "Graveler", 76: "Golem", 77: "Ponyta", 78: "Rapidash", 79: "Slowpoke",
    80: "Slowbro", 81: "Magnemite", 82: "Magneton", 83: "Farfetch'd", 84: "Doduo",
    85: "Dodrio", 86: "Seel", 87: "Dewgong", 88: "Grimer", 89: "Muk",
    90: "Shellder", 91: "Cloyster", 92: "Gastly", 93: "Haunter", 94: "Gengar",
    95: "Onix", 96: "Drowzee", 97: "Hypno", 98: "Krabby", 99: "Kingler",
    100: "Voltorb", 101: "Electrode", 102: "Exeggcute", 103: "Exeggutor", 104: "Cubone",
    105: "Marowak", 106: "Hitmonlee", 107: "Hitmonchan", 108: "Lickitung", 109: "Koffing",
    110: "Weezing", 111: "Rhyhorn", 112: "Rhydon", 113: "Chansey", 114: "Tangela",
    115: "Kangaskhan", 116: "Horsea", 117: "Seadra", 118: "Goldeen", 119: "Seaking",
    120: "Staryu", 121: "Starmie", 122: "Mr. Mime", 123: "Scyther", 124: "Jynx",
    125: "Electabuzz", 126: "Magmar", 127: "Pinsir", 128: "Tauros", 129: "Magikarp",
    130: "Gyarados", 131: "Lapras", 132: "Ditto", 133: "Eevee", 134: "Vaporeon",
    135: "Jolteon", 136: "Flareon", 137: "Porygon", 138: "Omanyte", 139: "Omastar",
    140: "Kabuto", 141: "Kabutops", 142: "Aerodactyl", 143: "Snorlax", 144: "Articuno",
    145: "Zapdos", 146: "Moltres", 147: "Dratini", 148: "Dragonair", 149: "Dragonite",
    150: "Mewtwo", 151: "Mew", 152: "Chikorita", 153: "Bayleef", 154: "Meganium",
    155: "Cyndaquil", 156: "Quilava", 157: "Typhlosion", 158: "Totodile", 159: "Croconaw",
    160: "Feraligatr", 161: "Sentret", 162: "Furret", 163: "Hoothoot", 164: "Noctowl",
    165: "Ledyba", 166: "Ledian", 167: "Spinarak", 168: "Ariados", 169: "Crobat",
    170: "Chinchou", 171: "Lanturn", 172: "Pichu", 173: "Cleffa", 174: "Igglybuff",
    175: "Togepi", 176: "Togetic", 177: "Natu", 178: "Xatu", 179: "Mareep",
    180: "Flaaffy", 181: "Ampharos", 182: "Bellossom", 183: "Marill", 184: "Azumarill",
    185: "Sudowoodo", 186: "Politoed", 187: "Hoppip", 188: "Skiploom", 189: "Jumpluff",
    190: "Aipom", 191: "Sunkern", 192: "Sunflora", 193: "Yanma", 194: "Wooper",
    195: "Quagsire", 196: "Espeon", 197: "Umbreon", 198: "Murkrow", 199: "Slowking",
    200: "Misdreavus", 201: "Unown", 202: "Wobbuffet", 203: "Girafarig", 204: "Pineco",
    205: "Forretress", 206: "Dunsparce", 207: "Gligar", 208: "Steelix", 209: "Snubbull",
    210: "Granbull", 211: "Qwilfish", 212: "Scizor", 213: "Shuckle", 214: "Heracross",
    215: "Sneasel", 216: "Teddiursa", 217: "Ursaring", 218: "Slugma", 219: "Magcargo",
    220: "Swinub", 221: "Piloswine", 222: "Corsola", 223: "Remoraid", 224: "Octillery",
    225: "Delibird", 226: "Mantine", 227: "Skarmory", 228: "Houndour", 229: "Houndoom",
    230: "Kingdra", 231: "Phanpy", 232: "Donphan", 233: "Porygon2", 234: "Stantler",
    235: "Smeargle", 236: "Tyrogue", 237: "Hitmontop", 238: "Smoochum", 239: "Elekid",
    240: "Magby", 241: "Miltank", 242: "Blissey", 243: "Raikou", 244: "Entei",
    245: "Suicune", 246: "Larvitar", 247: "Pupitar", 248: "Tyranitar", 249: "Lugia",
    250: "Ho-Oh", 251: "Celebi", 252: "Treecko", 253: "Grovyle", 254: "Sceptile",
    255: "Torchic", 256: "Combusken", 257: "Blaziken", 258: "Mudkip", 259: "Marshtomp",
    260: "Swampert", 261: "Poochyena", 262: "Mightyena", 263: "Zigzagoon", 264: "Linoone",
    265: "Wurmple", 266: "Silcoon", 267: "Beautifly", 268: "Cascoon", 269: "Dustox",
    270: "Lotad", 271: "Lombre", 272: "Ludicolo", 273: "Seedot", 274: "Nuzleaf",
    275: "Shiftry", 276: "Taillow", 277: "Swellow", 278: "Wingull", 279: "Pelipper",
    280: "Ralts", 281: "Kirlia", 282: "Gardevoir", 283: "Surskit", 284: "Masquerain",
    285: "Shroomish", 286: "Breloom", 287: "Slakoth", 288: "Vigoroth", 289: "Slaking",
    290: "Nincada", 291: "Ninjask", 292: "Shedinja", 293: "Whismur", 294: "Loudred",
    295: "Exploud", 296: "Makuhita", 297: "Hariyama", 298: "Azurill", 299: "Nosepass",
    300: "Skitty", 301: "Delcatty", 302: "Sableye", 303: "Mawile", 304: "Aron",
    305: "Lairon", 306: "Aggron", 307: "Meditite", 308: "Medicham", 309: "Electrike",
    310: "Manectric", 311: "Plusle", 312: "Minun", 313: "Volbeat", 314: "Illumise",
    315: "Roselia", 316: "Gulpin", 317: "Swalot", 318: "Carvanha", 319: "Sharpedo",
    320: "Wailmer", 321: "Wailord", 322: "Numel", 323: "Camerupt", 324: "Torkoal",
    325: "Spoink", 326: "Grumpig", 327: "Spinda", 328: "Trapinch", 329: "Vibrava",
    330: "Flygon", 331: "Cacnea", 332: "Cacturne", 333: "Swablu", 334: "Altaria",
    335: "Zangoose", 336: "Seviper", 337: "Lunatone", 338: "Solrock", 339: "Barboach",
    340: "Whiscash", 341: "Corphish", 342: "Crawdaunt", 343: "Baltoy", 344: "Claydol",
    345: "Lileep", 346: "Cradily", 347: "Anorith", 348: "Armaldo", 349: "Feebas",
    350: "Milotic", 351: "Castform", 352: "Kecleon", 353: "Shuppet", 354: "Banette",
    355: "Duskull", 356: "Dusclops", 357: "Tropius", 358: "Chimecho", 359: "Absol",
    360: "Wynaut", 361: "Snorunt", 362: "Glalie", 363: "Spheal", 364: "Sealeo",
    365: "Walrein", 366: "Clamperl", 367: "Huntail", 368: "Gorebyss", 369: "Relicanth",
    370: "Luvdisc", 371: "Bagon", 372: "Shelgon", 373: "Salamence", 374: "Beldum",
    375: "Metang", 376: "Metagross", 377: "Regirock", 378: "Regice", 379: "Registeel",
    380: "Latias", 381: "Latios", 382: "Kyogre", 383: "Groudon", 384: "Rayquaza",
    385: "Jirachi", 386: "Deoxys",
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

# Move names (Gen III - common moves)
MOVE_NAMES = {
    0: "None", 1: "Pound", 2: "Karate Chop", 3: "Double Slap", 4: "Comet Punch",
    5: "Mega Punch", 6: "Pay Day", 7: "Fire Punch", 8: "Ice Punch", 9: "Thunder Punch",
    10: "Scratch", 11: "Vice Grip", 12: "Guillotine", 13: "Razor Wind", 14: "Swords Dance",
    15: "Cut", 16: "Gust", 17: "Wing Attack", 18: "Whirlwind", 19: "Fly",
    20: "Bind", 21: "Slam", 22: "Vine Whip", 23: "Stomp", 24: "Double Kick",
    25: "Mega Kick", 26: "Jump Kick", 27: "Rolling Kick", 28: "Sand Attack", 29: "Headbutt",
    30: "Horn Attack", 31: "Fury Attack", 32: "Horn Drill", 33: "Tackle", 34: "Body Slam",
    35: "Wrap", 36: "Take Down", 37: "Thrash", 38: "Double-Edge", 39: "Tail Whip",
    40: "Poison Sting", 41: "Twineedle", 42: "Pin Missile", 43: "Leer", 44: "Bite",
    45: "Growl", 46: "Roar", 47: "Sing", 48: "Supersonic", 49: "Sonic Boom",
    50: "Disable", 51: "Acid", 52: "Ember", 53: "Flamethrower", 54: "Mist",
    55: "Water Gun", 56: "Hydro Pump", 57: "Surf", 58: "Ice Beam", 59: "Blizzard",
    60: "Psybeam", 61: "Bubble Beam", 62: "Aurora Beam", 63: "Hyper Beam", 64: "Peck",
    65: "Drill Peck", 66: "Submission", 67: "Low Kick", 68: "Counter", 69: "Seismic Toss",
    70: "Strength", 71: "Absorb", 72: "Mega Drain", 73: "Leech Seed", 74: "Growth",
    75: "Razor Leaf", 76: "Solar Beam", 77: "Poison Powder", 78: "Stun Spore", 79: "Sleep Powder",
    80: "Petal Dance", 81: "String Shot", 82: "Dragon Rage", 83: "Fire Spin", 84: "Thunder Shock",
    85: "Thunderbolt", 86: "Thunder Wave", 87: "Thunder", 88: "Rock Throw", 89: "Earthquake",
    90: "Fissure", 91: "Dig", 92: "Toxic", 93: "Confusion", 94: "Psychic",
    95: "Hypnosis", 96: "Meditate", 97: "Agility", 98: "Quick Attack", 99: "Rage",
    100: "Teleport", 101: "Night Shade", 102: "Mimic", 103: "Screech", 104: "Double Team",
    105: "Recover", 106: "Harden", 107: "Minimize", 108: "Smokescreen", 109: "Confuse Ray",
    110: "Withdraw", 111: "Defense Curl", 112: "Barrier", 113: "Light Screen", 114: "Haze",
    115: "Reflect", 116: "Focus Energy", 117: "Bide", 118: "Metronome", 119: "Mirror Move",
    120: "Self-Destruct", 121: "Egg Bomb", 122: "Lick", 123: "Smog", 124: "Sludge",
    125: "Bone Club", 126: "Fire Blast", 127: "Waterfall", 128: "Clamp", 129: "Swift",
    130: "Skull Bash", 131: "Spike Cannon", 132: "Constrict", 133: "Amnesia", 134: "Kinesis",
    135: "Soft-Boiled", 136: "High Jump Kick", 137: "Glare", 138: "Dream Eater", 139: "Poison Gas",
    140: "Barrage", 141: "Leech Life", 142: "Lovely Kiss", 143: "Sky Attack", 144: "Transform",
    145: "Bubble", 146: "Dizzy Punch", 147: "Spore", 148: "Flash", 149: "Psywave",
    150: "Splash", 151: "Acid Armor", 152: "Crabhammer", 153: "Explosion", 154: "Fury Swipes",
    155: "Bonemerang", 156: "Rest", 157: "Rock Slide", 158: "Hyper Fang", 159: "Sharpen",
    160: "Conversion", 161: "Tri Attack", 162: "Super Fang", 163: "Slash", 164: "Substitute",
    165: "Struggle", 166: "Sketch", 167: "Triple Kick", 168: "Thief", 169: "Spider Web",
    170: "Mind Reader", 171: "Nightmare", 172: "Flame Wheel", 173: "Snore", 174: "Curse",
    175: "Flail", 176: "Conversion 2", 177: "Aeroblast", 178: "Cotton Spore", 179: "Reversal",
    180: "Spite", 181: "Powder Snow", 182: "Protect", 183: "Mach Punch", 184: "Scary Face",
    185: "Feint Attack", 186: "Sweet Kiss", 187: "Belly Drum", 188: "Sludge Bomb", 189: "Mud-Slap",
    190: "Octazooka", 191: "Spikes", 192: "Zap Cannon", 193: "Foresight", 194: "Destiny Bond",
    195: "Perish Song", 196: "Icy Wind", 197: "Detect", 198: "Bone Rush", 199: "Lock-On",
    200: "Outrage", 201: "Sandstorm", 202: "Giga Drain", 203: "Endure", 204: "Charm",
    205: "Rollout", 206: "False Swipe", 207: "Swagger", 208: "Milk Drink", 209: "Spark",
    210: "Fury Cutter", 211: "Steel Wing", 212: "Mean Look", 213: "Attract", 214: "Sleep Talk",
    215: "Heal Bell", 216: "Return", 217: "Present", 218: "Frustration", 219: "Safeguard",
    220: "Pain Split", 221: "Sacred Fire", 222: "Magnitude", 223: "Dynamic Punch", 224: "Megahorn",
    225: "Dragon Breath", 226: "Baton Pass", 227: "Encore", 228: "Pursuit", 229: "Rapid Spin",
    230: "Sweet Scent", 231: "Iron Tail", 232: "Metal Claw", 233: "Vital Throw", 234: "Morning Sun",
    235: "Synthesis", 236: "Moonlight", 237: "Hidden Power", 238: "Cross Chop", 239: "Twister",
    240: "Rain Dance", 241: "Sunny Day", 242: "Crunch", 243: "Mirror Coat", 244: "Psych Up",
    245: "Extreme Speed", 246: "Ancient Power", 247: "Shadow Ball", 248: "Future Sight", 249: "Rock Smash",
    250: "Whirlpool", 251: "Beat Up", 252: "Fake Out", 253: "Uproar", 254: "Stockpile",
    255: "Spit Up", 256: "Swallow", 257: "Heat Wave", 258: "Hail", 259: "Torment",
    260: "Flatter", 261: "Will-O-Wisp", 262: "Memento", 263: "Facade", 264: "Focus Punch",
    265: "Smelling Salts", 266: "Follow Me", 267: "Nature Power", 268: "Charge", 269: "Taunt",
    270: "Helping Hand", 271: "Trick", 272: "Role Play", 273: "Wish", 274: "Assist",
    275: "Ingrain", 276: "Superpower", 277: "Magic Coat", 278: "Recycle", 279: "Revenge",
    280: "Brick Break", 281: "Yawn", 282: "Knock Off", 283: "Endeavor", 284: "Eruption",
    285: "Skill Swap", 286: "Imprison", 287: "Refresh", 288: "Grudge", 289: "Snatch",
    290: "Secret Power", 291: "Dive", 292: "Arm Thrust", 293: "Camouflage", 294: "Tail Glow",
    295: "Luster Purge", 296: "Mist Ball", 297: "Feather Dance", 298: "Teeter Dance", 299: "Blaze Kick",
    300: "Mud Sport", 301: "Ice Ball", 302: "Needle Arm", 303: "Slack Off", 304: "Hyper Voice",
    305: "Poison Fang", 306: "Crush Claw", 307: "Blast Burn", 308: "Hydro Cannon", 309: "Meteor Mash",
    310: "Astonish", 311: "Weather Ball", 312: "Aromatherapy", 313: "Fake Tears", 314: "Air Cutter",
    315: "Overheat", 316: "Odor Sleuth", 317: "Rock Tomb", 318: "Silver Wind", 319: "Metal Sound",
    320: "Grass Whistle", 321: "Tickle", 322: "Cosmic Power", 323: "Water Spout", 324: "Signal Beam",
    325: "Shadow Punch", 326: "Extrasensory", 327: "Sky Uppercut", 328: "Sand Tomb", 329: "Sheer Cold",
    330: "Muddy Water", 331: "Bullet Seed", 332: "Aerial Ace", 333: "Icicle Spear", 334: "Iron Defense",
    335: "Block", 336: "Howl", 337: "Dragon Claw", 338: "Frenzy Plant", 339: "Bulk Up",
    340: "Bounce", 341: "Mud Shot", 342: "Poison Tail", 343: "Covet", 344: "Volt Tackle",
    345: "Magical Leaf", 346: "Water Sport", 347: "Calm Mind", 348: "Leaf Blade", 349: "Dragon Dance",
    350: "Rock Blast", 351: "Shock Wave", 352: "Water Pulse", 353: "Doom Desire", 354: "Psycho Boost",
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

    def _decrypt_pokemon_data(self, encrypted_data: bytes, personality: int, otid: int) -> bytes:
        """
        Decrypt the 48-byte Pokemon data section

        Args:
            encrypted_data: 48 bytes of encrypted data (offset 32-79)
            personality: Pokemon's personality value
            otid: Original Trainer ID

        Returns:
            Decrypted 48 bytes
        """
        # Calculate decryption key
        key = personality ^ otid

        # Convert key to 4 bytes
        key_bytes = key.to_bytes(4, byteorder='little')

        # Decrypt data by XORing with repeating key
        decrypted = bytearray()
        for i in range(len(encrypted_data)):
            decrypted.append(encrypted_data[i] ^ key_bytes[i % 4])

        return bytes(decrypted)

    def _unshuffle_substructures(self, data: bytes, personality: int) -> bytes:
        """
        Unshuffle the 4 substructures based on personality value

        The 48 bytes are divided into 4 substructures of 12 bytes each:
        - Growth (G): species, exp, friendship
        - Attacks (A): moves and PP
        - EVs (E): EVs and contest stats
        - Misc (M): status, level, ribbons

        Args:
            data: 48 bytes of decrypted but shuffled data
            personality: Pokemon's personality value

        Returns:
            48 bytes in standard order [G, A, E, M]
        """
        # Get shuffle order based on personality % 24
        order = SUBSTRUCTURE_ORDER[personality % 24]

        # Split into 4 substructures of 12 bytes each
        substructures = [
            data[0:12],   # Current position 0
            data[12:24],  # Current position 1
            data[24:36],  # Current position 2
            data[36:48],  # Current position 3
        ]

        # Reorder to standard [G, A, E, M] layout
        # order tells us where each piece currently is
        # We need to reverse the mapping
        unshuffled = [None] * 4
        for actual_pos, shuffled_pos in enumerate(order):
            unshuffled[shuffled_pos] = substructures[actual_pos]

        return b''.join(unshuffled)

    def read_pokemon_data(self, base_address: int) -> Dict[str, Any]:
        """
        Read 100-byte Pokemon data structure with proper decryption

        Args:
            base_address: Starting address of Pokemon data

        Returns:
            Dictionary with Pokemon information
        """
        # Read full 100-byte structure
        data = self.client.read_memory(base_address, 100)

        offsets = self.config["pokemon_structure"]

        # Read unencrypted header (offsets 0-31)
        personality = int.from_bytes(data[0:4], 'little')
        otid = int.from_bytes(data[4:8], 'little')

        # Read encrypted data section (offsets 32-79, 48 bytes)
        encrypted_data = data[32:80]

        # Decrypt and unshuffle
        decrypted = self._decrypt_pokemon_data(encrypted_data, personality, otid)
        unshuffled = self._unshuffle_substructures(decrypted, personality)

        # Now parse from unshuffled data
        # Growth substructure (bytes 0-11): species at offset 0
        species_id = int.from_bytes(unshuffled[0:2], 'little')

        # Attacks substructure (bytes 12-23): moves at 0-7, PP at 8-11
        move1_id = int.from_bytes(unshuffled[12:14], 'little')
        move2_id = int.from_bytes(unshuffled[14:16], 'little')
        move3_id = int.from_bytes(unshuffled[16:18], 'little')
        move4_id = int.from_bytes(unshuffled[18:20], 'little')
        move1_pp = unshuffled[20]
        move2_pp = unshuffled[21]
        move3_pp = unshuffled[22]
        move4_pp = unshuffled[23]

        # Misc substructure is at bytes 36-47
        # Status ailment is at offset 0 of Misc substructure
        status = unshuffled[36]

        # Battle stats are stored unencrypted at the end (offsets 80-99)
        level = data[offsets["level"]]
        current_hp = int.from_bytes(data[offsets["current_hp"]:offsets["current_hp"]+2], 'little')
        max_hp = int.from_bytes(data[offsets["max_hp"]:offsets["max_hp"]+2], 'little')
        attack = int.from_bytes(data[offsets["attack"]:offsets["attack"]+2], 'little')
        defense = int.from_bytes(data[offsets["defense"]:offsets["defense"]+2], 'little')
        speed = int.from_bytes(data[offsets["speed"]:offsets["speed"]+2], 'little')
        sp_attack = int.from_bytes(data[offsets["sp_attack"]:offsets["sp_attack"]+2], 'little')
        sp_defense = int.from_bytes(data[offsets["sp_defense"]:offsets["sp_defense"]+2], 'little')

        # Get species name
        species_name = SPECIES_NAMES.get(species_id, f"Unknown ({species_id})")

        # Get status condition
        status_condition = STATUS_CONDITIONS.get(status & 0x07, "unknown")

        # Check if Pokemon exists (HP > 0 and valid species)
        exists = current_hp > 0 and species_id > 0 and species_id <= 386

        # Build moves list with names
        moves = []
        for move_id, pp, slot in [
            (move1_id, move1_pp, 1),
            (move2_id, move2_pp, 2),
            (move3_id, move3_pp, 3),
            (move4_id, move4_pp, 4),
        ]:
            if move_id > 0:
                moves.append({
                    "move_id": move_id,
                    "name": MOVE_NAMES.get(move_id, f"Move {move_id}"),
                    "pp": pp,
                    "slot": slot
                })

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
            "personality": personality,
            "moves": moves
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
