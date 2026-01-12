from src.command_parser import parse_natural_language

def test_parser():
    assert parse_natural_language("list files") == "ls"
