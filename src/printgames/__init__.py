"""PrintGames: Beautiful, strictly page-fitted printable games via MCP."""

from .cli import main
from .games import GAME_REGISTRY, produce_booklet, produce_game, produce_game_from_dict
from .server import mcp

__all__ = [
    "GAME_REGISTRY",
    "main",
    "mcp",
    "produce_booklet",
    "produce_game",
    "produce_game_from_dict",
]
