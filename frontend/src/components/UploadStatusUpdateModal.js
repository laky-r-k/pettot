// frontend/src/components/UploadStatusUpdateModal.js
import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Modal,
  Image,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  Alert,
  Platform,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useAuth } from "../context/AuthContext";
import { API_BASE_URL } from "../api/client";

export default function UploadStatusUpdateModal({ visible, pet, onClose, onSuccess }) {
  const { getIdToken } = useAuth();

  const [faceAsset, setFaceAsset] = useState(null);
  const [incisionAsset, setIncisionAsset] = useState(null);
  const [videoAsset, setVideoAsset] = useState(null);
  const [notes, setNotes] = useState("");
  const [uploading, setUploading] = useState(false);

  function resetForm() {
    setFaceAsset(null);
    setIncisionAsset(null);
    setVideoAsset(null);
    setNotes("");
  }

  function alertMsg(title, message) {
    if (Platform.OS === "web") {
      window.alert(`${title}: ${message}`);
    } else {
      Alert.alert(title, message);
    }
  }

  async function pickImage(setter) {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") {
      alertMsg("Permission Denied", "Camera roll permissions are required to select photos.");
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      quality: 0.8,
      allowsEditing: true,
    });

    if (!result.canceled && result.assets && result.assets.length > 0) {
      setter(result.assets[0]);
    }
  }

  async function pickVideo() {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") {
      alertMsg("Permission Denied", "Camera roll permissions are required to select videos.");
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["videos"],
      videoMaxDuration: 10,
    });

    if (!result.canceled && result.assets && result.assets.length > 0) {
      const asset = result.assets[0];
      // Duration in milliseconds (asset.duration is in ms on web/mobile) or seconds
      let durationSec = asset.duration ? (asset.duration > 100 ? asset.duration / 1000 : asset.duration) : 0;
      if (durationSec > 10.5) {
        alertMsg("Video Exceeds Limit", `The selected video is ${durationSec.toFixed(1)}s. Maximum allowed is 10.0 seconds.`);
        return;
      }
      setVideoAsset(asset);
    }
  }

  async function handleUpload() {
    if (!faceAsset) {
      alertMsg("Missing Photo", "Please select a Pet Face Photo.");
      return;
    }
    if (!incisionAsset) {
      alertMsg("Missing Photo", "Please select a Surgical Incision Photo.");
      return;
    }
    if (!videoAsset) {
      alertMsg("Missing Video", "Please select a 10-second Walking Video.");
      return;
    }

    setUploading(true);
    try {
      const token = await getIdToken();
      const formData = new FormData();

      // Helper to append file for cross-platform FormData
      const appendFile = async (key, asset, defaultName, defaultMime) => {
        const uri = asset.uri;
        const name = asset.fileName || defaultName;
        const type = asset.mimeType || defaultMime;

        if (Platform.OS === "web") {
          // On Web, fetch the blob from object URL
          const res = await fetch(uri);
          const blob = await res.blob();
          formData.append(key, blob, name);
        } else {
          // On React Native Mobile
          formData.append(key, {
            uri,
            name,
            type,
          });
        }
      };

      await appendFile("face_file", faceAsset, "face.jpg", "image/jpeg");
      await appendFile("incision_file", incisionAsset, "incision.jpg", "image/jpeg");
      await appendFile("video_file", videoAsset, "walking.mp4", "video/mp4");

      if (notes.trim()) {
        formData.append("notes", notes.trim());
      }

      const response = await fetch(`${API_BASE_URL}/pets/${pet.id}/status-updates/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/json",
        },
        body: formData,
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Upload failed with status ${response.status}`);
      }

      alertMsg("Check-In Saved!", "Daily recovery status update and media files uploaded successfully.");
      resetForm();
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      alertMsg("Upload Error", err.message || "Failed to upload daily status update.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <Modal visible={visible} transparent animationType="slide">
      <View style={styles.overlay}>
        <View style={styles.content}>
          <ScrollView contentContainerStyle={styles.scroll}>
            <Text style={styles.title}>📋 Daily Recovery Check-in</Text>
            <Text style={styles.subtitle}>
              Pet: <Text style={styles.petHighlight}>{pet?.name}</Text> ({pet?.species})
            </Text>

            {/* 1. Face Photo */}
            <View style={styles.uploadSection}>
              <Text style={styles.sectionLabel}>1. Pet Facial Photo 📸</Text>
              <Text style={styles.hint}>Front-facing photo of pet's face (eyes, ears, muzzle).</Text>
              {faceAsset ? (
                <View style={styles.previewContainer}>
                  <Image source={{ uri: faceAsset.uri }} style={styles.previewImg} />
                  <TouchableOpacity style={styles.changeBtn} onPress={() => pickImage(setFaceAsset)}>
                    <Text style={styles.changeText}>Replace Photo</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <TouchableOpacity style={styles.pickButton} onPress={() => pickImage(setFaceAsset)}>
                  <Text style={styles.pickButtonText}>+ Select Face Photo</Text>
                </TouchableOpacity>
              )}
            </View>

            {/* 2. Incision Photo */}
            <View style={styles.uploadSection}>
              <Text style={styles.sectionLabel}>2. Surgical Incision Photo 🩹</Text>
              <Text style={styles.hint}>Clear, close-up photo of the surgical wound or sutures.</Text>
              {incisionAsset ? (
                <View style={styles.previewContainer}>
                  <Image source={{ uri: incisionAsset.uri }} style={styles.previewImg} />
                  <TouchableOpacity style={styles.changeBtn} onPress={() => pickImage(setIncisionAsset)}>
                    <Text style={styles.changeText}>Replace Photo</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <TouchableOpacity style={styles.pickButton} onPress={() => pickImage(setIncisionAsset)}>
                  <Text style={styles.pickButtonText}>+ Select Incision Photo</Text>
                </TouchableOpacity>
              )}
            </View>

            {/* 3. Walking Video */}
            <View style={styles.uploadSection}>
              <Text style={styles.sectionLabel}>3. Walking Video (Max 10s) 🎥</Text>
              <Text style={styles.hint}>Record a short clip of the pet walking across the room.</Text>
              {videoAsset ? (
                <View style={styles.videoSelectedBox}>
                  <Text style={styles.videoIcon}>🎬</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.videoName} numberOfLines={1}>
                      {videoAsset.fileName || "Walking Video Selected"}
                    </Text>
                    <Text style={styles.videoDuration}>
                      Duration: {videoAsset.duration ? (videoAsset.duration > 100 ? (videoAsset.duration / 1000).toFixed(1) : videoAsset.duration.toFixed(1)) : "<10"}s
                    </Text>
                  </View>
                  <TouchableOpacity style={styles.changeBtn} onPress={pickVideo}>
                    <Text style={styles.changeText}>Replace</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <TouchableOpacity style={styles.pickButton} onPress={pickVideo}>
                  <Text style={styles.pickButtonText}>+ Select 10s Walking Video</Text>
                </TouchableOpacity>
              )}
            </View>

            {/* 4. Notes */}
            <View style={styles.uploadSection}>
              <Text style={styles.sectionLabel}>4. Daily Observations 📝</Text>
              <TextInput
                style={styles.notesInput}
                placeholder="Appetite, energy levels, walking posture, or general mood..."
                placeholderTextColor="#9ca3af"
                value={notes}
                onChangeText={setNotes}
                multiline
                numberOfLines={3}
              />
            </View>

            {/* Action Buttons */}
            <View style={styles.actionRow}>
              <TouchableOpacity
                style={styles.cancelBtn}
                onPress={() => {
                  resetForm();
                  onClose();
                }}
                disabled={uploading}
              >
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.submitBtn}
                onPress={handleUpload}
                disabled={uploading}
              >
                {uploading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.submitText}>Save Daily Update</Text>
                )}
              </TouchableOpacity>
            </View>
          </ScrollView>
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
    maxWidth: 520,
    maxHeight: "90%",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
  },
  scroll: {
    padding: 24,
  },
  title: {
    fontSize: 22,
    fontWeight: "bold",
    color: "#fff",
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: "#9ca3af",
    marginBottom: 20,
  },
  petHighlight: {
    color: "#60a5fa",
    fontWeight: "bold",
  },
  uploadSection: {
    marginBottom: 18,
    backgroundColor: "rgba(255, 255, 255, 0.02)",
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.06)",
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: "#e5e7eb",
    marginBottom: 4,
  },
  hint: {
    fontSize: 12,
    color: "#9ca3af",
    marginBottom: 10,
  },
  pickButton: {
    backgroundColor: "rgba(59, 130, 246, 0.12)",
    borderWidth: 1,
    borderColor: "rgba(59, 130, 246, 0.3)",
    borderStyle: "dashed",
    borderRadius: 10,
    padding: 14,
    alignItems: "center",
  },
  pickButtonText: {
    color: "#60a5fa",
    fontWeight: "600",
    fontSize: 14,
  },
  previewContainer: {
    alignItems: "center",
    gap: 8,
  },
  previewImg: {
    width: "100%",
    height: 160,
    borderRadius: 10,
    objectFit: "cover",
  },
  changeBtn: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    backgroundColor: "rgba(255, 255, 255, 0.08)",
    borderRadius: 6,
  },
  changeText: {
    color: "#9ca3af",
    fontSize: 12,
  },
  videoSelectedBox: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(16, 185, 129, 0.1)",
    borderWidth: 1,
    borderColor: "rgba(16, 185, 129, 0.3)",
    borderRadius: 10,
    padding: 12,
    gap: 12,
  },
  videoIcon: {
    fontSize: 26,
  },
  videoName: {
    color: "#fff",
    fontSize: 13,
    fontWeight: "600",
  },
  videoDuration: {
    color: "#34d399",
    fontSize: 12,
    marginTop: 2,
  },
  notesInput: {
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
    borderRadius: 10,
    padding: 12,
    color: "#fff",
    fontSize: 14,
    minHeight: 70,
    textAlignVertical: "top",
  },
  actionRow: {
    flexDirection: "row",
    justifyContent: "flex-end",
    gap: 12,
    marginTop: 10,
  },
  cancelBtn: {
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 10,
  },
  cancelText: {
    color: "#9ca3af",
    fontSize: 14,
  },
  submitBtn: {
    backgroundColor: "#2563eb",
    paddingVertical: 12,
    paddingHorizontal: 22,
    borderRadius: 10,
    alignItems: "center",
  },
  submitText: {
    color: "#fff",
    fontWeight: "bold",
    fontSize: 14,
  },
});
