import os
import logging
import time
import json

def make_save_tokens(token_file):
    """Return a save_tokens() function for the given filename."""
    def save_tokens(token_info):
        if "expires_at" not in token_info and "expires_in" in token_info:
            token_info["expires_at"] = time.time() + token_info["expires_in"]
        logging.info("### Saving new tokens to %s", token_file)
        oldmask = os.umask(0o077)
        try:
            with open(token_file, "w") as f:
                json.dump(token_info, f)
        except OSError as e:
            logging.warning("Failed to save new tokens: %s: %s",
                    type(e).__name__, str(e))
        os.umask(oldmask)

    return save_tokens
