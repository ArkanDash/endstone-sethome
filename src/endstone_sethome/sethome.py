from endstone.event import event_handler
from endstone.plugin import Plugin
from endstone.command import Command, CommandSender
from endstone import ColorFormat
from os import path
import json

class Sethome(Plugin):
    api_version = "0.4"

    commands = {
        "sethome": {
            "description": "Set home at your current location.",
            "usages": ["/sethome"],
            "aliases": ["sh"],
            "permissions": ["sethome.command.sethome"],
        },
        "home": {
            "description": "Teleport to your home.",
            "usages": ["/home"],
            "aliases": ["h"],
            "permissions": ["sethome.command.home"],
        }
    }

    permissions = {
        "sethome.command": {
            "description": "Allow users to use all commands provided by this plugin.",
            "default": True,
            "children": {
                "sethome.command.sethome": True,
                "sethome.command.home": True,
            }
        },
        "sethome.command.sethome": {
            "description": "Allow users to use the /sethome command.",
            "default": True,
        },
        "sethome.command.home": {
            "description": "Allow users to use the /home command.",
            "default": True,
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player_home_data = []

    def on_enable(self):
        self.save_default_config()
        home_file_path = path.join(self.data_folder, "homes.json")
        if path.exists(home_file_path):
            with open(home_file_path, "r") as read_file:
                self.player_home_data = json.load(read_file)
        self.logger.info("Sethome has been enabled!")
        self.register_events(self)

    def on_disable(self):
        self.logger.info("Sethome has been disabled!")

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        player = sender.as_player()
        if command.name == "sethome":
            if not self.is_dimension_enabled(player.location.dimension.name):
                player.send_message(f"{ColorFormat.RED}Setting home in this dimension is disabled.")
                return False
            self.set_home(player)
            player.send_message(f"{ColorFormat.GREEN}Successfully set your home.")
            self.save_homes()
            return True
        elif command.name == "home":
            home = self.get_home(player)
            if home is None:
                player.send_message(f"{ColorFormat.RED}No home set. Use /sethome to set your home first.")
                return False
            if not self.is_dimension_enabled(home["dimension"]):
                player.send_message(f"{ColorFormat.RED}Teleporting home in this dimension is disabled.")
                return False
            self.teleport_to_home(player, home)
            player.send_message(f"{ColorFormat.GREEN}Successfully teleported to your home.")
            return True
        return False

    def is_dimension_enabled(self, dimension_name: str) -> bool:
        return self.config.get(dimension_name.lower(), False)

    def set_home(self, player):
        self.player_home_data = [home for home in self.player_home_data if home["uuid"] != str(player.unique_id)]

        self.player_home_data.append({
            "player": player.name,
            "uuid": str(player.unique_id),
            "dimension": player.location.dimension.name,
            "coordinate": {
                "x": player.location.x,
                "y": player.location.y,
                "z": player.location.z,
            }
        })

    def get_home(self, player):
        for home in self.player_home_data:
            if home["uuid"] == str(player.unique_id):
                return home
        return None

    def teleport_to_home(self, player, home):
        dimension = home["dimension"].lower()
        dimension = "the_end" if dimension == "theend" else dimension
        coords = home["coordinate"]
        self.server.dispatch_command(self.server.command_sender, f"execute in {dimension} run tp {player.name} {coords['x']} {coords['y']} {coords['z']}")

    def save_homes(self):
        home_file_path = path.join(self.data_folder, "homes.json")
        with open(home_file_path, "w") as write_file:
            json.dump(self.player_home_data, write_file, indent=4)
