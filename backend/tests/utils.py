from app.security import create_token


def auth_header(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, 'access')}"}
