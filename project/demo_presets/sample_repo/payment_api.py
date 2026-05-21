from token_service import validate_request

def process_payment(req):
    user = validate_request(req)
    # simplified payment flow
    if not user:
        return {"status": "error"}
    return {"status": "ok", "user": user}
