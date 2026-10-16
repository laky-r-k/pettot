// frontend/src/context/AuthContext.js
import React, { createContext, useContext, useState, useEffect } from "react";
import { 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged 
} from "firebase/auth";
import { auth } from "../firebaseConfig";
import { api } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch local user profile from backend database via GET /me
  async function fetchProfile(firebaseUser) {
    if (!firebaseUser) {
      setUserProfile(null);
      return;
    }
    try {
      const token = await firebaseUser.getIdToken();
      const profile = await api.get("/me", token);
      setUserProfile(profile);
    } catch (err) {
      // If 404, user exists in Firebase but hasn't completed local onboarding (/users/)
      if (err.status === 404) {
        setUserProfile(null);
      } else {
        console.error("Failed to fetch user profile:", err);
      }
    }
  }

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setCurrentUser(user);
      if (user) {
        await fetchProfile(user);
      } else {
        setUserProfile(null);
      }
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  async function login(email, password) {
    const cred = await signInWithEmailAndPassword(auth, email, password);
    await fetchProfile(cred.user);
    return cred.user;
  }

  async function signup(email, password) {
    const cred = await createUserWithEmailAndPassword(auth, email, password);
    setCurrentUser(cred.user);
    return cred.user;
  }

  async function logout() {
    await signOut(auth);
    setCurrentUser(null);
    setUserProfile(null);
  }

  async function registerProfile({ name, username, role, license_number }) {
    if (!currentUser) throw new Error("Must be logged in with Firebase first");
    const token = await currentUser.getIdToken();
    const newProfile = await api.post("/users/", {
      name,
      username,
      email: currentUser.email,
      role,
      license_number: license_number || null,
    }, token);
    setUserProfile(newProfile);
    return newProfile;
  }

  async function getIdToken() {
    if (!currentUser) return null;
    return await currentUser.getIdToken();
  }

  const value = {
    currentUser,
    userProfile,
    loading,
    login,
    signup,
    logout,
    registerProfile,
    refreshProfile: () => fetchProfile(currentUser),
    getIdToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
