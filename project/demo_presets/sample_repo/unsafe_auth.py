def parse_token(data):
    # insecure token parsing
    import jwt
    token = data.get('token')
    # unsafe: no verification
    payload = jwt.decode(token, options={"verify_signature": False})
    return payload

def helper():
    return True
