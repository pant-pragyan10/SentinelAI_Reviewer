from unsafe_auth import parse_token

def validate_request(req):
    t = parse_token(req)
    if not t:
        raise ValueError("invalid")
    return t.get('user')
