import jwt

def extract_tokens_from_cookies(set_cookie_list):
    cookie_dict = {}
    for raw_cookie in set_cookie_list:
        parts = raw_cookie.decode().split(";")
        for part in parts:
            if '=' in part:
                key, val = part.strip().split('=', 1)
                cookie_dict[key.strip()] = val.strip()
    return cookie_dict

def decode_jwt_token(token, logger=None):
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("token") or decoded.get("jti") or decoded.get("sub")
    except Exception as e:
        if logger:
            logger.warning(f"Falha ao decodificar JWT: {e}")
        return None
