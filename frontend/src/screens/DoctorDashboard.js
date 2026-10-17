// frontend/src/screens/DoctorDashboard.js
import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from "react-native";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/client";
import StatusUpdatesTimelineModal from "../components/StatusUpdatesTimelineModal";

export default function DoctorDashboard() {
  const { userProfile, logout, getIdToken } = useAuth();
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPetForTimeline, setSelectedPetForTimeline] = useState(null);

  async function loadSubscriptions() {
    setLoading(true);
    try {
      const token = await getIdToken();
      const data = await api.get("/doctors/me/subscriptions/", token);
      setSubscriptions(data || []);
    } catch (err) {
      console.error("Failed to load doctor subscriptions:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSubscriptions();
  }, []);

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Dr. {userProfile?.name} 🩺</Text>
          <Text style={styles.licenseBadge}>
            License: {userProfile?.license_number || "Verified Veterinarian"}
          </Text>
          <Text style={styles.doctorIdTag}>
            Your Doctor ID: <Text style={styles.highlight}>{userProfile?.id}</Text> (Share this ID with pet owners to subscribe)
          </Text>
        </View>
        <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
      </View>

      {/* Main Content */}
      <View style={styles.content}>
        <View style={styles.titleRow}>
          <Text style={styles.sectionTitle}>
            Subscribed Patients & Pet Owners ({subscriptions.length})
          </Text>
          <TouchableOpacity onPress={loadSubscriptions} style={styles.refreshBtn}>
            <Text style={styles.refreshText}>🔄 Refresh</Text>
          </TouchableOpacity>
        </View>

        {loading ? (
          <ActivityIndicator color="#60a5fa" size="large" style={{ marginTop: 40 }} />
        ) : subscriptions.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyIcon}>📋</Text>
            <Text style={styles.emptyTitle}>No Subscribed Patients Yet</Text>
            <Text style={styles.emptySub}>
              Share your Doctor ID (#{userProfile?.id}) with pet owners so they can grant you access to their pet profiles.
            </Text>
          </View>
        ) : (
          <FlatList
            data={subscriptions}
            keyExtractor={(item) => item.subscription_id.toString()}
            contentContainerStyle={{ paddingBottom: 40 }}
            renderItem={({ item }) => (
              <View style={styles.ownerCard}>
                <View style={styles.ownerHeader}>
                  <Text style={styles.ownerName}>👤 Owner: {item.owner_name}</Text>
                  <Text style={styles.ownerId}>Owner ID #{item.owner_id}</Text>
                </View>

                <Text style={styles.petsHeader}>
                  Registered Patient Pets ({item.pets?.length || 0}):
                </Text>

                {item.pets && item.pets.length > 0 ? (
                  item.pets.map((pet) => (
                    <View key={pet.id} style={styles.patientRow}>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.petName}>
                          {pet.species === "Cat" ? "🐱" : "🐶"} {pet.name}
                        </Text>
                        <Text style={styles.petDetails}>
                          Species: {pet.species} • Age: {pet.age} yrs
                        </Text>
                      </View>
                      <TouchableOpacity
                        style={styles.viewTimelineBtn}
                        onPress={() => setSelectedPetForTimeline(pet)}
                      >
                        <Text style={styles.viewTimelineBtnText}>📜 View Timeline</Text>
                      </TouchableOpacity>
                    </View>
                  ))
                ) : (
                  <Text style={styles.noPetsText}>No pets registered by this owner yet.</Text>
                )}
              </View>
            )}
          />
        )}
      </View>

      {/* Recovery Timeline Viewer Modal */}
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
    alignItems: "flex-start",
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255, 255, 255, 0.08)",
  },
  greeting: {
    fontSize: 22,
    fontWeight: "bold",
    color: "#fff",
  },
  licenseBadge: {
    fontSize: 13,
    color: "#10b981",
    marginTop: 4,
    fontWeight: "600",
  },
  doctorIdTag: {
    fontSize: 13,
    color: "#9ca3af",
    marginTop: 6,
  },
  highlight: {
    color: "#60a5fa",
    fontWeight: "bold",
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
  content: {
    flex: 1,
    marginTop: 20,
  },
  titleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: "600",
    color: "#e5e7eb",
  },
  refreshBtn: {
    paddingVertical: 6,
    paddingHorizontal: 10,
    backgroundColor: "rgba(255, 255, 255, 0.06)",
    borderRadius: 6,
  },
  refreshText: {
    color: "#60a5fa",
    fontSize: 13,
    fontWeight: "500",
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
    maxWidth: 380,
    lineHeight: 20,
  },
  ownerCard: {
    backgroundColor: "#161e2e",
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.06)",
  },
  ownerHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255, 255, 255, 0.05)",
    paddingBottom: 8,
  },
  ownerName: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#60a5fa",
  },
  ownerId: {
    fontSize: 12,
    color: "#9ca3af",
  },
  petsHeader: {
    fontSize: 13,
    color: "#9ca3af",
    marginBottom: 10,
    fontWeight: "600",
  },
  patientRow: {
    backgroundColor: "rgba(255, 255, 255, 0.03)",
    padding: 12,
    borderRadius: 10,
    marginBottom: 8,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  petName: {
    fontSize: 15,
    fontWeight: "600",
    color: "#fff",
    marginBottom: 2,
  },
  petDetails: {
    fontSize: 13,
    color: "#9ca3af",
  },
  viewTimelineBtn: {
    backgroundColor: "rgba(59, 130, 246, 0.15)",
    borderWidth: 1,
    borderColor: "#3b82f6",
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
  },
  viewTimelineBtnText: {
    color: "#60a5fa",
    fontSize: 12,
    fontWeight: "600",
  },
  noPetsText: {
    fontSize: 13,
    color: "#6b7280",
    fontStyle: "italic",
  },
});
