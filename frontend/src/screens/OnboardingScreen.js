// frontend/src/screens/OnboardingScreen.js
import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
} from "react-native";
import { useAuth } from "../context/AuthContext";

export default function OnboardingScreen() {
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [role, setRole] = useState("owner"); // "owner" or "doctor"
  const [licenseNumber, setLicenseNumber] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { registerProfile, logout, currentUser } = useAuth();

  async function handleCompleteProfile() {
    if (!name.trim() || !username.trim()) {
      setError("Please enter your name and username.");
      return;
    }
    if (role === "doctor" && !licenseNumber.trim()) {
      setError("Veterinary license number is required for doctors.");
      return;
    }

    setError("");
    setSubmitting(true);
    try {
      await registerProfile({
        name: name.trim(),
        username: username.trim(),
        role,
        license_number: role === "doctor" ? licenseNumber.trim() : null,
      });
    } catch (err) {
      setError(err.message || "Failed to register profile. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      <View style={styles.card}>
        <Text style={styles.title}>Complete Your Profile 📋</Text>
        <Text style={styles.subtitle}>
          Logged in as: <Text style={styles.emailHighlight}>{currentUser?.email}</Text>
        </Text>

        {error ? <Text style={styles.errorBanner}>{error}</Text> : null}

        <Text style={styles.sectionHeading}>I am a:</Text>
        <View style={styles.roleSelector}>
          <TouchableOpacity
            style={[styles.roleOption, role === "owner" && styles.roleOptionActive]}
            onPress={() => setRole("owner")}
          >
            <Text style={styles.roleIcon}>🐾</Text>
            <Text style={[styles.roleLabel, role === "owner" && styles.roleLabelActive]}>
              Pet Owner
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.roleOption, role === "doctor" && styles.roleOptionActive]}
            onPress={() => setRole("doctor")}
          >
            <Text style={styles.roleIcon}>🩺</Text>
            <Text style={[styles.roleLabel, role === "doctor" && styles.roleLabelActive]}>
              Veterinary Doctor
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Full Name</Text>
          <TextInput
            style={styles.input}
            placeholder="Dr. Jane Doe / John Smith"
            placeholderTextColor="#9ca3af"
            value={name}
            onChangeText={setName}
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Username</Text>
          <TextInput
            style={styles.input}
            placeholder="johndoe"
            placeholderTextColor="#9ca3af"
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
          />
        </View>

        {role === "doctor" ? (
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Veterinary License Number</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g. VET-987654"
              placeholderTextColor="#9ca3af"
              value={licenseNumber}
              onChangeText={setLicenseNumber}
            />
          </View>
        ) : null}

        <TouchableOpacity
          style={styles.primaryButton}
          onPress={handleCompleteProfile}
          disabled={submitting}
        >
          {submitting ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Complete Registration</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.logoutButton} onPress={logout}>
          <Text style={styles.logoutText}>Sign in with a different account</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0b0f19",
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  card: {
    width: "100%",
    maxWidth: 480,
    backgroundColor: "#161e2e",
    borderRadius: 20,
    padding: 32,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.08)",
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#fff",
    textAlign: "center",
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    color: "#9ca3af",
    textAlign: "center",
    marginBottom: 20,
  },
  emailHighlight: {
    color: "#60a5fa",
    fontWeight: "600",
  },
  errorBanner: {
    backgroundColor: "rgba(239, 68, 68, 0.15)",
    color: "#f87171",
    padding: 12,
    borderRadius: 10,
    marginBottom: 16,
    fontSize: 13,
    textAlign: "center",
    borderWidth: 1,
    borderColor: "#ef4444",
  },
  sectionHeading: {
    color: "#e5e7eb",
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 12,
  },
  roleSelector: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 20,
  },
  roleOption: {
    flex: 1,
    backgroundColor: "rgba(255, 255, 255, 0.04)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
  },
  roleOptionActive: {
    backgroundColor: "rgba(37, 99, 235, 0.15)",
    borderColor: "#3b82f6",
  },
  roleIcon: {
    fontSize: 28,
    marginBottom: 6,
  },
  roleLabel: {
    color: "#9ca3af",
    fontSize: 14,
    fontWeight: "600",
  },
  roleLabelActive: {
    color: "#60a5fa",
  },
  inputGroup: {
    marginBottom: 18,
  },
  label: {
    color: "#e5e7eb",
    fontSize: 13,
    fontWeight: "600",
    marginBottom: 8,
  },
  input: {
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.12)",
    borderRadius: 10,
    padding: 14,
    color: "#fff",
    fontSize: 15,
  },
  primaryButton: {
    backgroundColor: "#2563eb",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
    marginTop: 10,
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "bold",
  },
  logoutButton: {
    marginTop: 16,
    alignItems: "center",
  },
  logoutText: {
    color: "#9ca3af",
    fontSize: 13,
  },
});
