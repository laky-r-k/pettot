"""
test_api.py - Verification suite for Firebase Auth & Role-Based Access Control
"""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from main import app, get_db, get_firebase_user_claims
import auth

from sqlalchemy.pool import StaticPool

# Use an in-memory SQLite database with StaticPool so all sessions share the same database
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# Mock token claims to simulate Firebase authenticated requests
CURRENT_MOCK_CLAIMS = {}

def override_firebase_claims():
    if not CURRENT_MOCK_CLAIMS:
        # If no mock claims set, fall back to real token verification to test rejection
        raise auth.HTTPException(status_code=401, detail="No token provided")
    return CURRENT_MOCK_CLAIMS


def test_health():
    """Verify health endpoint is publicly accessible."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "online"
    assert res.json()["auth"] == "Firebase"
    print("✅ Health check passed")


def test_unauthenticated_request_rejected():
    """Verify protected endpoints reject requests without a Bearer token."""
    res = client.get("/me")
    assert res.status_code in [401, 403]
    print("✅ Unauthenticated request rejected (401/403)")


def test_invalid_token_rejected():
    """Verify malformed / fake Firebase token is rejected by real verify_firebase_token."""
    res = client.get("/me", headers={"Authorization": "Bearer fake_invalid_token_12345"})
    assert res.status_code == 401
    print("✅ Invalid Firebase token rejected (401)")


def test_user_onboarding_and_rbac_flow():
    """End-to-end test simulating Firebase authenticated Owner and Doctor users."""
    global CURRENT_MOCK_CLAIMS
    app.dependency_overrides[get_firebase_user_claims] = override_firebase_claims

    # 1. Register Owner
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_owner_001", "email": "alice_owner@example.com"}
    owner_payload = {
        "name": "Alice Smith",
        "username": "alice",
        "role": "owner"
    }
    res = client.post("/users/", json=owner_payload, headers={"Authorization": "Bearer mock_token"})
    assert res.status_code == 200, res.text
    owner_data = res.json()
    assert owner_data["firebase_uid"] == "firebase_owner_001"
    assert owner_data["role"] == "owner"
    owner_id = owner_data["id"]
    print(f"✅ Owner registered: ID={owner_id}, UID={owner_data['firebase_uid']}")

    # 2. Duplicate registration check
    res_dup = client.post("/users/", json=owner_payload, headers={"Authorization": "Bearer mock_token"})
    assert res_dup.status_code == 400
    print("✅ Duplicate Firebase registration prevented (400)")

    # 3. Register Doctor
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_doctor_002", "email": "dr_bob@example.com"}
    doctor_payload = {
        "name": "Dr. Bob",
        "username": "dr_bob",
        "role": "doctor",
        "license_number": "VET-12345"
    }
    res_doc = client.post("/users/", json=doctor_payload, headers={"Authorization": "Bearer mock_token"})
    assert res_doc.status_code == 200, res_doc.text
    doctor_data = res_doc.json()
    doctor_id = doctor_data["id"]
    print(f"✅ Doctor registered: ID={doctor_id}, License={doctor_data['license_number']}")

    # 4. Check /me for Doctor
    res_me = client.get("/me", headers={"Authorization": "Bearer mock_token"})
    assert res_me.status_code == 200
    assert res_me.json()["username"] == "dr_bob"
    print("✅ GET /me returns current user profile")

    # 5. Doctor tries to create a pet (Forbidden: only owners can)
    res_doc_pet = client.post("/pets/", json={"name": "Ghost", "species": "Cat", "age": 2}, headers={"Authorization": "Bearer mock_token"})
    assert res_doc_pet.status_code == 403
    print("✅ Doctor creating pet is forbidden (403)")

    # 6. Switch to Owner and create Pet
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_owner_001", "email": "alice_owner@example.com"}
    pet_payload = {"name": "Buddy", "species": "Dog", "age": 3, "is_adopted": True}
    res_pet = client.post("/pets/", json=pet_payload, headers={"Authorization": "Bearer mock_token"})
    assert res_pet.status_code == 200, res_pet.text
    pet_id = res_pet.json()["id"]
    print(f"✅ Owner successfully created pet ID={pet_id} (Buddy)")

    # 7. Doctor tries to view Owner's pet BEFORE subscribing (Forbidden)
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_doctor_002", "email": "dr_bob@example.com"}
    res_unsub = client.get(f"/pets/{pet_id}", headers={"Authorization": "Bearer mock_token"})
    assert res_unsub.status_code == 403
    print("✅ Doctor cannot access pet without active subscription (403)")

    # 8. Owner subscribes to Doctor
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_owner_001", "email": "alice_owner@example.com"}
    res_sub = client.post("/subscriptions/", json={"doctor_id": doctor_id}, headers={"Authorization": "Bearer mock_token"})
    assert res_sub.status_code == 200, res_sub.text
    print(f"✅ Owner successfully subscribed to Doctor ID={doctor_id}")

    # 9. Doctor now views Owner's pet (Allowed via subscription!)
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_doctor_002", "email": "dr_bob@example.com"}
    res_doc_view = client.get(f"/pets/{pet_id}", headers={"Authorization": "Bearer mock_token"})
    assert res_doc_view.status_code == 200, res_doc_view.text
    assert res_doc_view.json()["name"] == "Buddy"
    print("✅ Doctor successfully accessed pet after subscription (200)")

    # 10. Doctor views their subscription roster
    res_doc_subs = client.get("/doctors/me/subscriptions/", headers={"Authorization": "Bearer mock_token"})
    assert res_doc_subs.status_code == 200
    subs_list = res_doc_subs.json()
    assert len(subs_list) == 1
    assert subs_list[0]["owner_name"] == "Alice Smith"
    assert subs_list[0]["pets"][0]["name"] == "Buddy"
    print("✅ Doctor subscription roster lists Owner and associated pets")

    # 11. Owner updates Pet
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_owner_001", "email": "alice_owner@example.com"}
    res_update = client.put(f"/pets/{pet_id}", json={"name": "Buddy Jr.", "species": "Dog", "age": 4, "is_adopted": True}, headers={"Authorization": "Bearer mock_token"})
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Buddy Jr."
    print("✅ Owner updated pet successfully")

    # 12. Owner deletes Pet
    res_del = client.delete(f"/pets/{pet_id}", headers={"Authorization": "Bearer mock_token"})
    assert res_del.status_code == 200
    print("✅ Owner deleted pet successfully")


if __name__ == "__main__":
    print("\n--- Running PetTot Firebase Auth & RBAC Verification Suite ---\n")
    test_health()
    test_unauthenticated_request_rejected()
    test_invalid_token_rejected()
    test_user_onboarding_and_rbac_flow()
    print("\n🎉 ALL 12 VERIFICATION CHECKS PASSED SUCCESSFULLY!\n")
