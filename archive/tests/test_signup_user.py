from src.services_old import auth_service


class FakeAuth:
    def __init__(self, storage):
        self.storage = storage

    def sign_up(self, payload):
        # Simulate a Supabase auth.sign_up response and record the user
        user = {
            "id": "user_123",
            "email": payload.get("email"),
            "user_metadata": payload.get("options", {}).get("data", {}),
        }
        self.storage.append(user)
        return {"user": user, "error": None}


class FakeSupabase:
    def __init__(self):
        self._storage = []
        self.auth = FakeAuth(self._storage)

    def get_storage(self):
        return self._storage


def test_signup_creates_user(monkeypatch):
    """Ensure AuthService.signup calls the Supabase client and stores the user."""
    fake = FakeSupabase()
    # Patch the module-level `supabase` used by AuthService
    monkeypatch.setattr("src.services.auth_service.supabase", fake)

    from src.services_old.auth_service import AuthService

    svc = AuthService()
    resp = svc.signup("alice@example.com", "secret", username="alice")

    assert "user" in resp and resp["error"] is None
    user = resp["user"]
    assert user["email"] == "alice@example.com"
    assert user["user_metadata"].get("username") == "alice"

    # Confirm the fake storage received the new user
    stored = fake.get_storage()
    assert len(stored) == 1
    assert stored[0]["email"] == "alice@example.com"
