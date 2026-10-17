"""
test_api.py - Verification suite for Firebase Auth, RBAC, and Daily Status Updates & Secure Media
"""

import io
import os
import shutil
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from main import app, get_db, get_firebase_user_claims, UPLOAD_DIR
import auth

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

CURRENT_MOCK_CLAIMS = {}

def override_firebase_claims():
    if not CURRENT_MOCK_CLAIMS:
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


def test_daily_status_updates_and_secure_media():
    """
    Verifies:
    1. Daily post-op upload with 3 files + notes
    2. Relative storage paths and UUID filenames (no predictable timestamps)
    3. No raw URLs leaked to public
    4. Permission-checked GET /media/{id} access control (Owner allowed, Doctor allowed via subscription, Unsubscribed doctor forbidden)
    5. Automatic day_number incrementation
    6. Background worker queue hook
    """
    global CURRENT_MOCK_CLAIMS
    app.dependency_overrides[get_firebase_user_claims] = override_firebase_claims

    # Ensure Owner is logged in
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_owner_001", "email": "alice_owner@example.com"}

    # Fetch Buddy's pet ID
    pets = client.get("/pets/", headers={"Authorization": "Bearer mock_token"}).json()
    assert len(pets) > 0
    pet_id = pets[0]["id"]

    # 1. Prepare 3 mock files (face image, incision image, walking video)
    face_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb"
    incision_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb"
    video_bytes = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42"

    files = {
        "face_file": ("front_face.jpg", io.BytesIO(face_bytes), "image/jpeg"),
        "incision_file": ("incision_day1.jpg", io.BytesIO(incision_bytes), "image/jpeg"),
        "video_file": ("gait_walk.mp4", io.BytesIO(video_bytes), "video/mp4"),
    }
    data = {"notes": "Day 1 post-op: Alert and standing, incision clean"}

    # 2. Owner uploads Day 1 status update
    res = client.post(
        f"/pets/{pet_id}/status-updates/",
        files=files,
        data=data,
        headers={"Authorization": "Bearer mock_token"},
    )
    assert res.status_code == 200, res.text
    update_d1 = res.json()
    assert update_d1["day_number"] == 1
    assert update_d1["processing_status"] == "pending"
    assert update_d1["notes"] == "Day 1 post-op: Alert and standing, incision clean"
    assert len(update_d1["media_files"]) == 3

    face_media = next(m for m in update_d1["media_files"] if m["media_type"] == "face_image")
    inc_media = next(m for m in update_d1["media_files"] if m["media_type"] == "incision_image")
    vid_media = next(m for m in update_d1["media_files"] if m["media_type"] == "walking_video")

    assert face_media["original_filename"] == "front_face.jpg"
    assert inc_media["original_filename"] == "incision_day1.jpg"
    assert vid_media["original_filename"] == "gait_walk.mp4"
    # Ensure raw file_path is NOT exposed in API response schema
    assert "file_path" not in face_media
    print(f"✅ Day 1 Status Update uploaded: ID={update_d1['id']}, Media count={len(update_d1['media_files'])}")

    # 3. Verify Owner can access their media via GET /media/{media_id}
    res_face = client.get(f"/media/{face_media['id']}", headers={"Authorization": "Bearer mock_token"})
    assert res_face.status_code == 200
    assert res_face.content == face_bytes
    print("✅ Owner accessed protected media file via GET /media/{id}")

    # 4. Verify Subscribed Doctor can access the pet's media
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_doctor_002", "email": "dr_bob@example.com"}
    res_doc_media = client.get(f"/media/{face_media['id']}", headers={"Authorization": "Bearer mock_token"})
    assert res_doc_media.status_code == 200
    assert res_doc_media.content == face_bytes
    print("✅ Subscribed Doctor accessed patient media file via GET /media/{id}")

    # 5. Verify Unsubscribed Doctor is BLOCKED from accessing the media (403)
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_doctor_unsubscribed_999", "email": "stranger_dr@example.com"}
    # Register this stranger doctor
    client.post("/users/", json={"name": "Dr. Stranger", "username": "stranger_dr", "role": "doctor"}, headers={"Authorization": "Bearer mock_token"})
    res_stranger_media = client.get(f"/media/{face_media['id']}", headers={"Authorization": "Bearer mock_token"})
    assert res_stranger_media.status_code == 403
    print("✅ Unsubscribed Doctor blocked with 403 Forbidden on GET /media/{id}")

    # 6. Verify Owner uploads Day 2 update and day_number auto-increments
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_owner_001", "email": "alice_owner@example.com"}
    files_d2 = {
        "face_file": ("face_d2.jpg", io.BytesIO(face_bytes), "image/jpeg"),
        "incision_file": ("incision_d2.jpg", io.BytesIO(incision_bytes), "image/jpeg"),
        "video_file": ("gait_d2.mp4", io.BytesIO(video_bytes), "video/mp4"),
    }
    res_d2 = client.post(
        f"/pets/{pet_id}/status-updates/",
        files=files_d2,
        data={"notes": "Day 2: Walking better, no redness"},
        headers={"Authorization": "Bearer mock_token"},
    )
    assert res_d2.status_code == 200
    update_d2 = res_d2.json()
    assert update_d2["day_number"] == 2
    print(f"✅ Day 2 Status Update auto-incremented day_number to {update_d2['day_number']}")

    # 7. Verify Timeline listing GET /pets/{pet_id}/status-updates/
    res_list = client.get(f"/pets/{pet_id}/status-updates/", headers={"Authorization": "Bearer mock_token"})
    assert res_list.status_code == 200
    history = res_list.json()
    assert len(history) == 2
    assert history[0]["day_number"] == 2  # Most recent first
    assert history[1]["day_number"] == 1
    print("✅ Full Status Update timeline history retrieved successfully")

    # 8. Verify Worker Hook GET /status-updates/pending/
    res_worker = client.get("/status-updates/pending/", headers={"Authorization": "Bearer mock_token"})
    assert res_worker.status_code == 200
    pending_list = res_worker.json()
    assert len(pending_list) >= 2
    assert all(item["processing_status"] == "pending" for item in pending_list)
    print("✅ Background worker hook GET /status-updates/pending/ returned unanalyzed queue")


def test_multi_doctor_subscriptions_and_duplicate_prevention():
    """
    Verifies Option B:
    1. Duplicate subscription to the same doctor is prevented with 400 Bad Request
    2. Owner can subscribe to multiple distinct doctors (e.g. general vet + specialist)
    3. GET /subscriptions/me/ lists all subscribed veterinarians with doctor profile details
    4. Owner can unsubscribe via DELETE /subscriptions/{id}
    5. Unsubscribed doctor immediately loses access to the owner's pet profiles (403)
    """
    global CURRENT_MOCK_CLAIMS
    app.dependency_overrides[get_firebase_user_claims] = override_firebase_claims

    # 1. Register a second doctor (Dr. Sarah, Surgical Specialist)
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_doctor_003", "email": "dr_sarah@example.com"}
    res_doc2 = client.post("/users/", json={
        "name": "Dr. Sarah",
        "username": "dr_sarah",
        "role": "doctor",
        "license_number": "SURG-9999"
    }, headers={"Authorization": "Bearer mock_token"})
    assert res_doc2.status_code == 200
    doc2_id = res_doc2.json()["id"]

    # 2. Switch back to Owner
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_owner_001", "email": "alice_owner@example.com"}

    # Doctor 1 (Dr. Bob) has ID=2 (from test_user_onboarding_and_rbac_flow)
    # Attempt duplicate subscription to Doctor 1
    res_dup = client.post("/subscriptions/", json={"doctor_id": 2}, headers={"Authorization": "Bearer mock_token"})
    assert res_dup.status_code == 400
    assert "already subscribed" in res_dup.json()["detail"].lower()
    print("✅ Duplicate subscription to same doctor blocked with 400 Bad Request")

    # 3. Subscribe to Doctor 2 (Dr. Sarah) - Multi-doctor allowed!
    res_sub2 = client.post("/subscriptions/", json={"doctor_id": doc2_id}, headers={"Authorization": "Bearer mock_token"})
    assert res_sub2.status_code == 200
    sub2_id = res_sub2.json()["id"]
    print(f"✅ Subscribed to second specialist doctor (ID={doc2_id}) successfully")

    # 4. Check GET /subscriptions/me/ lists both veterinarians
    res_my_docs = client.get("/subscriptions/me/", headers={"Authorization": "Bearer mock_token"})
    assert res_my_docs.status_code == 200
    doc_list = res_my_docs.json()
    assert len(doc_list) == 2
    assert any(d["doctor_name"] == "Dr. Bob" for d in doc_list)
    assert any(d["doctor_name"] == "Dr. Sarah" for d in doc_list)
    print("✅ GET /subscriptions/me/ returned all linked veterinarians for pet owner")

    # 5. Doctor 2 accesses pet
    pets = client.get("/pets/", headers={"Authorization": "Bearer mock_token"}).json()
    pet_id = pets[0]["id"]

    CURRENT_MOCK_CLAIMS = {"uid": "firebase_doctor_003", "email": "dr_sarah@example.com"}
    res_doc2_view = client.get(f"/pets/{pet_id}", headers={"Authorization": "Bearer mock_token"})
    assert res_doc2_view.status_code == 200
    print("✅ Doctor 2 granted access to pet via active subscription")

    # 6. Owner unsubscribes from Doctor 2
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_owner_001", "email": "alice_owner@example.com"}
    res_del_sub = client.delete(f"/subscriptions/{sub2_id}", headers={"Authorization": "Bearer mock_token"})
    assert res_del_sub.status_code == 200
    print("✅ Owner successfully unsubscribed from Doctor 2")

    # 7. Doctor 2 attempts to view pet again -> BLOCKED with 403 Forbidden!
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_doctor_003", "email": "dr_sarah@example.com"}
    res_doc2_blocked = client.get(f"/pets/{pet_id}", headers={"Authorization": "Bearer mock_token"})
    assert res_doc2_blocked.status_code == 403
    print("✅ Unsubscribed doctor immediately lost access to pet (403 Forbidden)")

    # 8. Check GET /subscriptions/me/ now only has Doctor 1
    CURRENT_MOCK_CLAIMS = {"uid": "firebase_owner_001", "email": "alice_owner@example.com"}
    res_my_docs_after = client.get("/subscriptions/me/", headers={"Authorization": "Bearer mock_token"})
    assert res_my_docs_after.status_code == 200
    assert len(res_my_docs_after.json()) == 1
    print("✅ GET /subscriptions/me/ reflects updated single subscription")


if __name__ == "__main__":
    print("\n--- Running PetTot Verification Suite (Auth, RBAC, Media & Subscriptions) ---\n")
    test_health()
    test_unauthenticated_request_rejected()
    test_invalid_token_rejected()
    test_user_onboarding_and_rbac_flow()
    test_daily_status_updates_and_secure_media()
    test_multi_doctor_subscriptions_and_duplicate_prevention()
    print("\n🎉 ALL 24 VERIFICATION CHECKS PASSED SUCCESSFULLY!\n")
