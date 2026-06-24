import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import { Header } from "../components/Header";
import { Badge, Card } from "../components/ui";
import { useAuth } from "../auth/AuthContext";
import { colors, spacing } from "../theme";

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

export default function ProfileScreen() {
  const { user } = useAuth();
  if (!user) return null;

  const name =
    [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username;

  return (
    <View style={styles.screen}>
      <Header title="Profile & Settings" subtitle="Account and security" />
      <ScrollView contentContainerStyle={styles.content}>
        <Card style={styles.identity}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {name.charAt(0).toUpperCase()}
            </Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.name}>{name}</Text>
            <Text style={styles.email}>{user.email}</Text>
            <View style={{ marginTop: spacing(2) }}>
              <Badge label={user.account_type || "Free"} />
            </View>
          </View>
        </Card>

        <Card>
          <Text style={styles.sectionTitle}>Account</Text>
          <Row label="Phone" value={user.phone_masked || "—"} />
          <Row label="Country" value={user.country || "KE"} />
          <Row label="Currency" value={user.currency || "KES"} />
          <Row
            label="Email verified"
            value={user.email_verified ? "Yes" : "No"}
          />
        </Card>

        <Card>
          <Text style={styles.sectionTitle}>Security</Text>
          <Row
            label="Two-factor auth"
            value={user.two_factor_enabled ? "Enabled" : "Disabled"}
          />
          <Row
            label="Biometric unlock"
            value={user.biometric_enabled ? "Enabled" : "Disabled"}
          />
        </Card>

        <Card>
          <Text style={styles.sectionTitle}>Channels</Text>
          <Row
            label="WhatsApp"
            value={user.whatsapp_connected ? "Connected" : "Not connected"}
          />
          <Row
            label="Telegram"
            value={user.telegram_connected ? "Connected" : "Not connected"}
          />
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing(4), gap: spacing(3), paddingBottom: spacing(8) },
  identity: { flexDirection: "row", alignItems: "center", gap: spacing(4) },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarText: { color: colors.white, fontSize: 24, fontWeight: "800" },
  name: { fontSize: 18, fontWeight: "800", color: colors.text },
  email: { color: colors.muted, marginTop: 2 },
  sectionTitle: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.5,
    color: colors.muted,
    marginBottom: spacing(2),
  },
  infoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: spacing(2),
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  infoLabel: { color: colors.muted },
  infoValue: { color: colors.text, fontWeight: "600" },
});
