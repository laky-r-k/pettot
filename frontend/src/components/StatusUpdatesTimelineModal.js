// frontend/src/components/StatusUpdatesTimelineModal.js
import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  Modal,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Platform,
} from "react-native";
import { useAuth } from "../context/AuthContext";
import { api, API_BASE_URL } from "../api/client";

export default function StatusUpdatesTimelineModal({ visible, pet, onClose }) {
  const { getIdToken } = useAuth();
  const [updates, setUpdates] = useState([]);
  const [loading, setLoading] = useState(true);

  async function loadTimeline() {
    if (!pet) return;
    setLoading(true);
    try {
      const token = await getIdToken();
      const data = await api.get(`/pets/${pet.id}/status-updates/`, token);
      setUpdates(data || []);
    } catch (err) {
      console.error("Failed to load recovery updates:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (visible && pet) {
      loadTimeline();
    }
  }, [visible, pet]);

  async function handleOpenMedia(mediaId, filename) {
    try {
      const token = await getIdToken();
      const mediaUrl = `${API_BASE_URL}/media/${mediaId}`;

      if (Platform.OS === "web") {
        // Fetch blob with Bearer token and open in new tab
        const res = await fetch(mediaUrl, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(blob);
        window.open(blobUrl, "_blank");
      } else {
        // Mobile alert
        alert(`Opening protected media #${mediaId} (${filename})`);
      }
    } catch (err) {
      alert("Failed to load protected media: " + err.message);
    }
  }

  return (
    <Modal visible={visible} transparent animationType="slide">
      <View style={styles.overlay}>
        <View style={styles.content}>
          <View style={styles.header}>
            <View>
              <Text style={styles.title}>Recovery Timeline 📜</Text>
              <Text style={styles.subtitle}>
                Pet: <Text style={styles.petName}>{pet?.name}</Text> • {updates.length} daily check-ins
              </Text>
            </View>
            <TouchableOpacity style={styles.closeBtn} onPress={onClose}>
              <Text style={styles.closeText}>✕</Text>
            </TouchableOpacity>
          </View>

          {loading ? (
            <ActivityIndicator color="#60a5fa" size="large" style={{ marginVertical: 40 }} />
          ) : updates.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyIcon}>🗓️</Text>
              <Text style={styles.emptyTitle}>No daily check-ins yet</Text>
              <Text style={styles.emptySubtitle}>
                Upload daily photos of face, incision, and walking video to track recovery!
              </Text>
            </View>
          ) : (
            <FlatList
              data={updates}
              keyExtractor={(item) => item.id.toString()}
              contentContainerStyle={styles.list}
              renderItem={({ item }) => (
                <View style={styles.updateCard}>
                  <View style={styles.cardHeader}>
                    <View style={styles.dayBadge}>
                      <Text style={styles.dayBadgeText}>Day {item.day_number}</Text>
                    </View>
                    <Text style={styles.dateText}>{item.update_date}</Text>
                    <View style={styles.statusPill}>
                      <Text style={styles.statusPillText}>
                        {item.processing_status === "completed" ? "✅ Analyzed" : "⏳ Queue: Pending"}
                      </Text>
                    </View>
                  </View>

                  {item.notes ? (
                    <Text style={styles.notesText}>"{item.notes}"</Text>
                  ) : null}

                  <Text style={styles.mediaHeading}>Attached Secure Medical Media:</Text>
                  <View style={styles.mediaGrid}>
                    {item.media_files?.map((media) => (
                      <TouchableOpacity
                        key={media.id}
                        style={styles.mediaItem}
                        onPress={() => handleOpenMedia(media.id, media.original_filename)}
                      >
                        <Text style={styles.mediaTypeIcon}>
                          {media.media_type === "face_image"
                            ? "📸 Face"
                            : media.media_type === "incision_image"
                            ? "🩹 Incision"
                            : "🎥 Walk Video"}
                        </Text>
                        <Text style={styles.mediaFilename} numberOfLines={1}>
                          {media.original_filename}
                        </Text>
                        {media.duration_seconds ? (
                          <Text style={styles.durationTag}>{media.duration_seconds}s</Text>
                        ) : null}
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}
            />
          )}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.8)",
    justifyContent: "center",
    alignItems: "center",
    padding: 16,
  },
  content: {
    backgroundColor: "#161e2e",
    borderRadius: 20,
    width: "100%",
    maxWidth: 580,
    maxHeight: "88%",
    padding: 24,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 18,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255, 255, 255, 0.08)",
    paddingBottom: 14,
  },
  title: {
    fontSize: 22,
    fontWeight: "bold",
    color: "#fff",
  },
  subtitle: {
    fontSize: 13,
    color: "#9ca3af",
    marginTop: 2,
  },
  petName: {
    color: "#60a5fa",
    fontWeight: "bold",
  },
  closeBtn: {
    padding: 8,
  },
  closeText: {
    color: "#9ca3af",
    fontSize: 20,
    fontWeight: "bold",
  },
  list: {
    paddingBottom: 20,
  },
  emptyContainer: {
    alignItems: "center",
    padding: 40,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 10,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#fff",
    marginBottom: 4,
  },
  emptySubtitle: {
    fontSize: 13,
    color: "#9ca3af",
    textAlign: "center",
  },
  updateCard: {
    backgroundColor: "rgba(255, 255, 255, 0.03)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.08)",
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginBottom: 10,
  },
  dayBadge: {
    backgroundColor: "#2563eb",
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 8,
  },
  dayBadgeText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "bold",
  },
  dateText: {
    color: "#9ca3af",
    fontSize: 13,
    flex: 1,
  },
  statusPill: {
    backgroundColor: "rgba(245, 158, 11, 0.15)",
    borderWidth: 1,
    borderColor: "rgba(245, 158, 11, 0.3)",
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 6,
  },
  statusPillText: {
    color: "#fbbf24",
    fontSize: 11,
    fontWeight: "600",
  },
  notesText: {
    color: "#e5e7eb",
    fontSize: 14,
    fontStyle: "italic",
    marginBottom: 12,
    lineHeight: 20,
  },
  mediaHeading: {
    fontSize: 12,
    color: "#9ca3af",
    fontWeight: "600",
    marginBottom: 8,
  },
  mediaGrid: {
    flexDirection: "row",
    gap: 8,
    flexWrap: "wrap",
  },
  mediaItem: {
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 10,
    flex: 1,
    minWidth: 110,
    alignItems: "center",
  },
  mediaTypeIcon: {
    color: "#60a5fa",
    fontSize: 12,
    fontWeight: "bold",
    marginBottom: 4,
  },
  mediaFilename: {
    color: "#fff",
    fontSize: 11,
    maxWidth: 100,
  },
  durationTag: {
    color: "#34d399",
    fontSize: 10,
    fontWeight: "600",
    marginTop: 2,
  },
});
