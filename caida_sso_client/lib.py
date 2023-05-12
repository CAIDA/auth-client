import os
import time
import json

def make_save_tokens(token_file):
    """Return a save_tokens() function for the given filename."""
    def save_tokens(token_info):
        if "expires_at" not in token_info and "expires_in" in token_info:
            token_info["expires_at"] = time.time() + token_info["expires_in"]
        oldmask = os.umask(0o077)
        with open(token_file, "w") as f:
            json.dump(token_info, f)
        os.umask(oldmask)

    return save_tokens
