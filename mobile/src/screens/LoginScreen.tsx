import React, { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { useAuth } from "../auth/AuthContext";
import { colors, radius, spacing } from "../theme";

const DEMO_EMAIL = "demo@pesayangu.co.ke";
const DEMO_PASSWORD = "pesayangu";

export default function LoginScreen() {
  const { signIn, signUp } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      if (mode === "login") {
        await signIn(email.trim(), password);
      } else {
        await signUp({
          email: email.trim(),
          password,
          first_name: firstName.trim(),
        });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Authentication failed");
    } finally {
      setBusy(false);
    }
  };

  const useDemo = async () => {
    setBusy(true);
    setError(null);
    setEmail(DEMO_EMAIL);
    setPassword(DEMO_PASSWORD);
    try {
      await signIn(DEMO_EMAIL, DEMO_PASSWORD);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Demo login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.brand}>
          <View style={styles.logo}>
            <Text style={styles.logoText}>P</Text>
          </View>
          <Text style={styles.title}>Pesa Yangu</Text>
          <Text style={styles.tagline}>Your money, automatically understood</Text>
        </View>

        <View style={styles.card}>
          <View style={styles.tabs}>
            {(["login", "register"] as const).map((m) => (
              <Pressable
                key={m}
                style={[styles.tab, mode === m && styles.tabActive]}
                onPress={() => setMode(m)}
              >
                <Text style={[styles.tabText, mode === m && styles.tabTextActive]}>
                  {m === "login" ? "Sign in" : "Create account"}
                </Text>
              </Pressable>
            ))}
          </View>

          {mode === "register" ? (
            <TextInput
              style={styles.input}
              placeholder="First name"
              placeholderTextColor={colors.muted}
              value={firstName}
              onChangeText={setFirstName}
            />
          ) : null}

          <TextInput
            style={styles.input}
            placeholder="Email"
            placeholderTextColor={colors.muted}
            autoCapitalize="none"
            keyboardType="email-address"
            value={email}
            onChangeText={setEmail}
          />
          <TextInput
            style={styles.input}
            placeholder="Password"
            placeholderTextColor={colors.muted}
            secureTextEntry
            value={password}
            onChangeText={setPassword}
          />

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <Pressable
            style={[styles.btn, busy && styles.btnDisabled]}
            onPress={submit}
            disabled={busy}
          >
            <Text style={styles.btnText}>
              {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
            </Text>
          </Pressable>

          <Pressable onPress={useDemo} disabled={busy} style={styles.demoBtn}>
            <Text style={styles.demoText}>Try the demo account</Text>
          </Pressable>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.primary },
  content: { flexGrow: 1, justifyContent: "center", padding: spacing(6) },
  brand: { alignItems: "center", marginBottom: spacing(8) },
  logo: {
    width: 64,
    height: 64,
    borderRadius: radius.lg,
    backgroundColor: colors.white,
    alignItems: "center",
    justifyContent: "center",
  },
  logoText: { color: colors.primary, fontSize: 32, fontWeight: "800" },
  title: { color: colors.white, fontSize: 28, fontWeight: "800", marginTop: spacing(3) },
  tagline: { color: "rgba(255,255,255,0.85)", marginTop: spacing(1) },
  card: {
    backgroundColor: colors.bg,
    borderRadius: radius.xl,
    padding: spacing(5),
    gap: spacing(3),
  },
  tabs: {
    flexDirection: "row",
    backgroundColor: colors.trackBg,
    borderRadius: radius.pill,
    padding: 4,
  },
  tab: { flex: 1, paddingVertical: spacing(2.5), alignItems: "center", borderRadius: radius.pill },
  tabActive: { backgroundColor: colors.card },
  tabText: { color: colors.muted, fontWeight: "700" },
  tabTextActive: { color: colors.text },
  input: {
    backgroundColor: colors.card,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing(4),
    paddingVertical: spacing(3.5),
    color: colors.text,
  },
  error: { color: colors.danger, fontSize: 13 },
  btn: {
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    paddingVertical: spacing(4),
    alignItems: "center",
  },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: colors.white, fontWeight: "800", fontSize: 15 },
  demoBtn: { alignItems: "center", paddingVertical: spacing(2) },
  demoText: { color: colors.primaryDark, fontWeight: "700" },
});
