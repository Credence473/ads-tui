import json
import sys
from rich.console import Console

console = Console(force_terminal=True)

with open(sys.argv[1]) as f:
    previews = json.load(f)

console.print(previews.get(sys.argv[2], f"No preview found for {sys.argv[2]}"))
