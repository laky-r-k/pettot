// frontend/src/screens/OwnerDashboard.js
import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  Modal,
  Alert,
  Platform,
} from "react-native";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/client";
import UploadStatusUpdateModal from "../components/UploadStatusUpdateModal";
import StatusUpdatesTimelineModal from "../components/StatusUpdatesTimelineModal";

export default function OwnerDashboard() {
  const { userProfile, logout, getIdToken } = useAuth();
  const [pets, setPets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [subModalVisible, setSubModalVisible] = useState(false);

  // Status Update & Timeline State
  const [selectedPetForUpload, setSelectedPetForUpload] = useState(null);
  const [selectedPetForTimeline, setSelectedPetForTimeline] = useState(null);

  // New Pet Form State
  const [name, setName] = useState("");
  const [species, setSpecies] = useState("Dog");
  const [age, setAge] = useState("");
  const [isAdopted, setIsAdopted] = useState(false);
  const [saving, setSaving] = useState(false);

  // Subscribe Doctor State
  const [doctorId, setDoctorId] = useState("");
  const [subscribing, setSubscribing] = useState(false);

  async function loadPets() {
    setLoading(true);
    try {
      const token = await getIdToken();
      const data = await api.get("/pets/", token);
      setPets(data || []);
    } catch (err) {
      console.error("Failed to load pets:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPets();
  }, []);

  async function handleAddPet() {
    if (!name.trim() || !age.trim()) {
      alertMsg("Validation Error", "Please fill in pet name and age.");
      return;
    }
    setSaving(true);
    try {
      const token = await getIdToken();
      await api.post("/pets/", {
        name: name.trim(),
        species: species.trim(),
        age: parseInt(age.trim(), 10) || 1,
        is_adopted: isAdopted,
      }, token);

      setName("");
      setAge("");
      setModalVisible(false);
      await loadPets();
      alertMsg("Success", "Pet registered successfully!");
    } catch (err) {
      alertMsg("Error", err.message || "Failed to add pet");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeletePet(petId) {
    try {
      const token = await getIdToken();
      await api.delete(`/pets/${petId}`, token);
      await loadPets();
    } catch (err) {
      alertMsg("Error", err.message || "Failed to delete pet");
    }
  }

  async function handleSubscribeDoctor() {
    if (!doctorId.trim()) {
      alertMsg("Validation Error", "Please enter a Doctor ID.");
      return;
    }
    setSubscribing(true);
    try {
      const token = await getIdToken();
      await api.post("/subscriptions/", {
        doctor_id: parseInt(doctorId.trim(), 10),
      }, token);
      setDoctorId("");
      setSubModalVisible(false);
      alertMsg("Subscribed!", "Successfully shared your pet records with the doctor.");
    } catch (err) {
      alertMsg("Subscription Error", err.message || "Could not subscribe to doctor.");
    } finally {
      setSubscribing(false);
    }
  }

  function alertMsg(title, message) {
    if (Platform.OS === "web") {
      window.alert(`${title}: ${message}`);
    } else {
      Alert.alert(title, message);
    }
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Welcome, {userProfile?.name} 🐾</Text>
          <Text style={styles.roleBadge}>Pet Owner Account</Text>
        </View>
        <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
      </View>

      {/* Action Buttons */}
      <View style={styles.actionBar}>
        <TouchableOpacity
          style={styles.actionBtnPrimary}
          onPress={() => setModalVisible(true)}
        >
          <Text style={styles.actionBtnText}>+ Register New Pet</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.actionBtnSecondary}
          onPress={() => setSubModalVisible(true)}
        >
          <Text style={styles.actionBtnSecondaryText}>🩺 Link with Doctor</Text>
        </TouchableOpacity>
      </View>

      {/* Pet List */}
      <View style={styles.listContainer}>
        <Text style={styles.sectionTitle}>My Registered Pets ({pets.length})</Text>

        {loading ? (
          <ActivityIndicator color="#60a5fa" size="large" style={{ marginTop: 40 }} />
        ) : pets.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyIcon}>🐶🐱</Text>
            <Text style={styles.emptyTitle}>No pets registered yet</Text>
            <Text style={styles.emptySub}>
              Tap the button above to register your first pet profile!
            </Text>
          </View>
        ) : (
          <FlatList
            data={pets}
            keyExtractor={(item) => item.id.toString()}
            contentContainerStyle={{ paddingBottom: 40 }}
            renderItem={({ item }) => (
              <View style={styles.petCard}>
                <View style={styles.petTopRow}>
                  <View style={styles.petInfo}>
                    <Text style={styles.petName}>
                      {item.name} {item.species === "Cat" ? "🐱" : "🐶"}
                    </Text>
                    <Text style={styles.petMeta}>
                      Species: <Text style={styles.metaVal}>{item.species}</Text> • Age: <Text style={styles.metaVal}>{item.age} yrs</Text>
                    </Text>
                    {item.is_adopted ? (
                      <Text style={styles.adoptedBadge}>❤️ Rescued / Adopted</Text>
                    ) : null}
                  </View>
                  <TouchableOpacity
                    style={styles.deleteBtn}
                    onPress={() => handleDeletePet(item.id)}
                  >
                    <Text style={styles.deleteBtnText}>Remove</Text>
                  </TouchableOpacity>
                </View>

                {/* Daily Recovery Actions */}
                <View style={styles.recoveryActionsRow}>
                  <TouchableOpacity
                    style={styles.checkInBtn}
                    onPress={() => setSelectedPetForUpload(item)}
                  >
                    <Text style={styles.checkInBtnText}>📸 + Daily Check-In</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.historyBtn}
                    onPress={() => setSelectedPetForTimeline(item)}
                  >
                    <Text style={styles.historyBtnText}>📜 Recovery Timeline</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          />
        )}
      </View>

      {/* Modal: Add Pet */}
      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Register Pet 🐾</Text>

            <Text style={styles.inputLabel}>Pet Name</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="e.g. Luna"
              placeholderTextColor="#9ca3af"
              value={name}
              onChangeText={setName}
            />

            <Text style={styles.inputLabel}>Species</Text>
            <View style={styles.speciesRow}>
              {["Dog", "Cat", "Other"].map((sp) => (
                <TouchableOpacity
                  key={sp}
                  style={[styles.speciesBtn, species === sp && styles.speciesBtnActive]}
                  onPress={() => setSpecies(sp)}
                >
                  <Text style={[styles.speciesBtnText, species === sp && styles.speciesBtnTextActive]}>
                    {sp}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.inputLabel}>Age (years)</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="e.g. 3"
              placeholderTextColor="#9ca3af"
              value={age}
              onChangeText={setAge}
              keyboardType="numeric"
            />

            <TouchableOpacity
              style={styles.adoptedToggle}
              onPress={() => setIsAdopted(!isAdopted)}
            >
              <Text style={styles.adoptedToggleText}>
                {isAdopted ? "✅ Adopted / Rescue Pet" : "⬜ Adopted / Rescue Pet"}
              </Text>
            </TouchableOpacity>

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.cancelBtn}
                onPress={() => setModalVisible(false)}
              >
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.saveBtn}
                onPress={handleAddPet}
                disabled={saving}
              >
                {saving ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.saveText}>Save Pet</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Modal: Subscribe Doctor */}
      <Modal visible={subModalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Link Veterinary Doctor 🩺</Text>
            <Text style={styles.modalSubtitle}>
              Give your licensed veterinarian access to view your pets for clinical monitoring.
            </Text>

            <Text style={styles.inputLabel}>Doctor ID</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="e.g. 2"
              placeholderTextColor="#9ca3af"
              value={doctorId}
              onChangeText={setDoctorId}
              keyboardType="numeric"
            />

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.cancelBtn}
                onPress={() => setSubModalVisible(false)}
              >
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.saveBtn}
                onPress={handleSubscribeDoctor}
                disabled={subscribing}
              >
                {subscribing ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.saveText}>Subscribe</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Modal: Upload Daily Status Update */}
      {selectedPetForUpload ? (
        <UploadStatusUpdateModal
          visible={!!selectedPetForUpload}
          pet={selectedPetForUpload}
          onClose={() => setSelectedPetForUpload(null)}
          onSuccess={() => {}}
        />
      ) : null}

      {/* Modal: Status Updates Timeline */}
      {selectedPetForTimeline ? (
        <StatusUpdatesTimelineModal
          visible={!!selectedPetForTimeline}
          pet={selectedPetForTimeline}
          onClose={() => setSelectedPetForTimeline(null)}
        />
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0b0f19",
    padding: 24,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255, 255, 255, 0.08)",
  },
  greeting: {
    fontSize: 22,
    fontWeight: "bold",
    color: "#fff",
  },
  roleBadge: {
    fontSize: 13,
    color: "#60a5fa",
    marginTop: 4,
    fontWeight: "500",
  },
  logoutBtn: {
    backgroundColor: "rgba(239, 68, 68, 0.15)",
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "rgba(239, 68, 68, 0.3)",
  },
  logoutText: {
    color: "#f87171",
    fontSize: 13,
    fontWeight: "600",
  },
  actionBar: {
    flexDirection: "row",
    gap: 12,
    marginVertical: 20,
  },
  actionBtnPrimary: {
    backgroundColor: "#2563eb",
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 10,
  },
  actionBtnText: {
    color: "#fff",
    fontWeight: "600",
    fontSize: 14,
  },
  actionBtnSecondary: {
    backgroundColor: "rgba(255, 255, 255, 0.06)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.12)",
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 10,
  },
  actionBtnSecondaryText: {
    color: "#e5e7eb",
    fontWeight: "600",
    fontSize: 14,
  },
  listContainer: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: "600",
    color: "#e5e7eb",
    marginBottom: 14,
  },
  emptyCard: {
    backgroundColor: "#161e2e",
    borderRadius: 16,
    padding: 40,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.06)",
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 17,
    fontWeight: "600",
    color: "#fff",
    marginBottom: 6,
  },
  emptySub: {
    fontSize: 14,
    color: "#9ca3af",
    textAlign: "center",
  },
  petCard: {
    backgroundColor: "#161e2e",
    borderRadius: 14,
    padding: 18,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.06)",
  },
  petTopRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  petInfo: {
    flex: 1,
  },
  petName: {
    fontSize: 17,
    fontWeight: "bold",
    color: "#fff",
    marginBottom: 4,
  },
  petMeta: {
    fontSize: 13,
    color: "#9ca3af",
  },
  metaVal: {
    color: "#e5e7eb",
    fontWeight: "500",
  },
  adoptedBadge: {
    fontSize: 12,
    color: "#34d399",
    marginTop: 6,
    fontWeight: "600",
  },
  deleteBtn: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    backgroundColor: "rgba(239, 68, 68, 0.12)",
    borderRadius: 6,
  },
  deleteBtnText: {
    color: "#f87171",
    fontSize: 12,
    fontWeight: "600",
  },
  recoveryActionsRow: {
    flexDirection: "row",
    gap: 10,
    marginTop: 14,
    borderTopWidth: 1,
    borderTopColor: "rgba(255, 255, 255, 0.05)",
    paddingTop: 12,
  },
  checkInBtn: {
    backgroundColor: "rgba(37, 99, 235, 0.15)",
    borderWidth: 1,
    borderColor: "#3b82f6",
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
  },
  checkInBtnText: {
    color: "#60a5fa",
    fontSize: 13,
    fontWeight: "600",
  },
  historyBtn: {
    backgroundColor: "rgba(255, 255, 255, 0.04)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
  },
  historyBtnText: {
    color: "#e5e7eb",
    fontSize: 13,
    fontWeight: "500",
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.75)",
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  modalContent: {
    backgroundColor: "#161e2e",
    borderRadius: 18,
    padding: 26,
    width: "100%",
    maxWidth: 420,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: "bold",
    color: "#fff",
    marginBottom: 16,
  },
  modalSubtitle: {
    fontSize: 13,
    color: "#9ca3af",
    marginBottom: 16,
    lineHeight: 18,
  },
  inputLabel: {
    fontSize: 13,
    color: "#e5e7eb",
    fontWeight: "600",
    marginBottom: 6,
  },
  modalInput: {
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.12)",
    borderRadius: 10,
    padding: 12,
    color: "#fff",
    fontSize: 15,
    marginBottom: 14,
  },
  speciesRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 14,
  },
  speciesBtn: {
    flex: 1,
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: "center",
  },
  speciesBtnActive: {
    borderColor: "#3b82f6",
    backgroundColor: "rgba(59, 130, 246, 0.2)",
  },
  speciesBtnText: {
    color: "#9ca3af",
    fontSize: 13,
    fontWeight: "600",
  },
  speciesBtnTextActive: {
    color: "#60a5fa",
  },
  adoptedToggle: {
    marginVertical: 8,
  },
  adoptedToggleText: {
    color: "#e5e7eb",
    fontSize: 14,
  },
  modalActions: {
    flexDirection: "row",
    justifyContent: "flex-end",
    gap: 12,
    marginTop: 20,
  },
  cancelBtn: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  cancelText: {
    color: "#9ca3af",
    fontSize: 14,
  },
  saveBtn: {
    backgroundColor: "#2563eb",
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  saveText: {
    color: "#fff",
    fontWeight: "bold",
    fontSize: 14,
  },
});
