"""caida_oidc_client functions"""

from typing import Callable, Dict, Any

import os
import logging
import time
import json
import binascii

def make_save_tokens(token_file: str) -> Callable[[Dict[str, Any]], None]:
    """Return a save_tokens() function for the given filename."""
    def save_tokens(token_info: Dict[str, Any]) -> None:
        if "expires_at" not in token_info:
            try:
                token_info["expires_at"] = jwt_decode(token_info["access_token"])["exp"]
            except (TypeError, KeyError):
                if "expires_in" in token_info:
                    token_info["expires_at"] = int(time.time()) - 1 + token_info["expires_in"]
        logging.info("### Saving new tokens to %s", token_file)
        oldmask = os.umask(0o077)
        try:
            with open(token_file, "w", encoding="ascii") as f:
                json.dump(token_info, f)
        except OSError as e:
            logging.warning("Failed to save new tokens: %s: %s",
                    type(e).__name__, str(e))
        os.umask(oldmask)

    return save_tokens

def jwt_decode(jwt: str) -> Any:
    """Decode a JSON Web Token"""
    code = jwt.split(".")[1]
    code += "="*((4-len(code))%4) # add padding needed by binascii
    return json.loads(binascii.a2b_base64(code))
