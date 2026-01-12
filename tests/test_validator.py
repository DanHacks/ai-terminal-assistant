from src.validator import is_blacklisted, is_whitelisted

def test_blacklist():
    blacklist = ["rm -rf"]
    assert is_blacklisted("rm -rf /", blacklist)

def test_whitelist():
    whitelist = ["ls"]
    assert is_whitelisted("ls", whitelist)
