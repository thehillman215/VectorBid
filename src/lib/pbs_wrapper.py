"""PBS Command Wrapper for VectorBid"""
from src.lib.pbs_command_generator import PBSCommandGenerator as OriginalGenerator

class SimplePBSGenerator:
    def __init__(self):
        self.generator = OriginalGenerator()
    
    def generate_simple(self, preferences: str) -> dict:
        profile_dict = {
            "base": "EWR",
            "fleet": ["737"],
            "seniority": 50,
            "flying_style": "balanced",
            "commuter": False
        }
        
        commands = self.generator.generate(preferences, profile_dict)
        
        # Handle string commands (which is what we're getting)
        command_list = []
        for cmd in commands:
            if isinstance(cmd, str):
                command_list.append({"command": cmd, "type": "PBS"})
            else:
                try:
                    command_list.append(cmd.to_dict())
                except:
                    command_list.append({"command": str(cmd), "type": "PBS"})
        
        return {
            "commands": command_list,
            "command_count": len(commands)
        }

def generate_pbs_commands(preferences: str) -> dict:
    gen = SimplePBSGenerator()
    return gen.generate_simple(preferences)
