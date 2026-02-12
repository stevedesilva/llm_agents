"""Rich-based markdown console output for the arena."""

from rich.console import Console
from rich.markdown import Markdown

console = Console()


def display(content: str) -> None:
    """Display markdown content in the console using rich."""
    console.print(Markdown(content))
