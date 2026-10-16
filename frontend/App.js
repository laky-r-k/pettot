// frontend/App.js
import React from "react";
import { View, ActivityIndicator, StyleSheet } from "react-native";
import { StatusBar } from "expo-status-bar";
import { AuthProvider, useAuth } from "./src/context/AuthContext";
import AuthScreen from "./src/screens/AuthScreen";
import OnboardingScreen from "./src/screens/OnboardingScreen";
import OwnerDashboard from "./src/screens/OwnerDashboard";
import DoctorDashboard from "./src/screens/DoctorDashboard";

function MainNavigator() {
  const { currentUser, userProfile, loading } = useAuth();

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  // 1. Not signed in with Firebase -> Show Login/Signup
  if (!currentUser) {
    return <AuthScreen />;
  }

  // 2. Signed in with Firebase but hasn't set role in FastAPI backend -> Show Onboarding
  if (!userProfile) {
    return <OnboardingScreen />;
  }

  // 3. Role-based Dashboard routing
  if (userProfile.role === "doctor") {
    return <DoctorDashboard />;
  }

  // Default to Owner Dashboard
  return <OwnerDashboard />;
}

export default function App() {
  return (
    <AuthProvider>
      <StatusBar style="light" />
      <MainNavigator />
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: "#0b0f19",
    justifyContent: "center",
    alignItems: "center",
  },
});
