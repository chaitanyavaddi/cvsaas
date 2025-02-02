from app.users.models import UserProfile
# from utils.auth import supabase
from utils.auth import get_supabase_client

async def get_user_data(user: dict) -> UserProfile:
    supabase = get_supabase_client()
    user_data = await supabase.auth.get_user(user["id"])
    return UserProfile(
        id=user_data.id,
        email=user_data.email,
        full_name=user_data.user_metadata.get("full_name", ""),
        avatar_url=user_data.user_metadata.get("avatar_url", "")
    )