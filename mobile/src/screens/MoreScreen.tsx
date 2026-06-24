import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import React from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { Header } from "../components/Header";
import { Card } from "../components/ui";
import { useAuth } from "../auth/AuthContext";
import { colors, radius, spacing } from "../theme";
import type { MoreStackParams } from "../navigation/types";

interface Item {
  key: keyof MoreStackParams;
  title: string;
  subtitle: string;
  icon: string;
}

const ITEMS: Item[] = [
  { key: "Budgets", title: "Budgets", subtitle: "Limits & tracking", icon: "◎" },
  { key: "Reports", title: "Reports", subtitle: "Cashflow & insights", icon: "▦" },
  {
    key: "ConnectedAccounts",
    title: "Connected Accounts",
    subtitle: "SMS sources & sync",
    icon: "⚡",
  },
  { key: "Profile", title: "Profile & Settings", subtitle: "Account & security", icon: "☺" },
];

export default function MoreScreen() {
  const navigation =
    useNavigation<NativeStackNavigationProp<MoreStackParams>>();
  const { user, signOut } = useAuth();

  return (
    <View style={styles.screen}>
      <Header
        title="More"
        subtitle={user ? user.email : undefined}
      />
      <ScrollView contentContainerStyle={styles.content}>
        {ITEMS.map((it) => (
          <Pressable key={it.key} onPress={() => navigation.navigate(it.key)}>
            <Card style={styles.row}>
              <View style={styles.iconWrap}>
                <Text style={styles.icon}>{it.icon}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.title}>{it.title}</Text>
                <Text style={styles.subtitle}>{it.subtitle}</Text>
              </View>
              <Text style={styles.chev}>›</Text>
            </Card>
          </Pressable>
        ))}

        <Pressable onPress={signOut}>
          <Card style={styles.logout}>
            <Text style={styles.logoutText}>Log out</Text>
          </Card>
        </Pressable>

        <Text style={styles.version}>Pesa Yangu · Phase 1 MVP</Text>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing(4), gap: spacing(3), paddingBottom: spacing(8) },
  row: { flexDirection: "row", alignItems: "center", gap: spacing(3) },
  iconWrap: {
    width: 44,
    height: 44,
    borderRadius: radius.md,
    backgroundColor: colors.primaryLight,
    alignItems: "center",
    justifyContent: "center",
  },
  icon: { fontSize: 20, color: colors.primaryDark },
  title: { fontSize: 16, fontWeight: "700", color: colors.text },
  subtitle: { color: colors.muted, fontSize: 13, marginTop: 2 },
  chev: { fontSize: 24, color: colors.muted },
  logout: { alignItems: "center" },
  logoutText: { color: colors.danger, fontWeight: "800", fontSize: 15 },
  version: { color: colors.muted, textAlign: "center", fontSize: 12 },
});
