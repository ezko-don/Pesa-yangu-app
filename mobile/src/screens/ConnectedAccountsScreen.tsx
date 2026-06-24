import React, { useCallback, useEffect, useState } from "react";
import { ScrollView, StyleSheet, Switch, Text, View } from "react-native";

import { api } from "../api/client";
import type { SmsSource } from "../api/types";
import { Header } from "../components/Header";
import { Badge, Card, ErrorState, Loading } from "../components/ui";
import { colors, spacing } from "../theme";

export default function ConnectedAccountsScreen() {
  const [sources, setSources] = useState<SmsSource[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setSources(await api.get<SmsSource[]>("/api/auth/sms-sources/"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load accounts");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const toggle = useCallback(
    async (src: SmsSource) => {
      setSources((prev) =>
        prev
          ? prev.map((s) =>
              s.id === src.id ? { ...s, enabled: !s.enabled } : s
            )
          : prev
      );
      try {
        await api.patch(`/api/auth/sms-sources/${src.id}/`, {
          enabled: !src.enabled,
        });
      } catch {
        load();
      }
    },
    [load]
  );

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!sources) return <Loading label="Loading accounts…" />;

  return (
    <View style={styles.screen}>
      <Header title="Connected Accounts" subtitle="SMS sources for auto-sync" />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.note}>
          Pesa Yangu parses transaction SMS on your device. We store the
          structured amount and merchant — never the raw message.
        </Text>
        {sources.map((s) => (
          <Card key={s.id} style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={styles.name}>{s.name}</Text>
              <Text style={styles.meta}>
                {s.short_code} · {s.transaction_count} transactions
              </Text>
              <View style={{ marginTop: spacing(1.5) }}>
                <Badge
                  label={s.enabled ? "Syncing" : "Paused"}
                  color={s.enabled ? colors.success : colors.muted}
                  bg={s.enabled ? colors.successBg : colors.trackBg}
                />
              </View>
            </View>
            <Switch
              value={s.enabled}
              onValueChange={() => toggle(s)}
              trackColor={{ true: colors.primary, false: colors.trackBg }}
              thumbColor={colors.white}
            />
          </Card>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing(4), gap: spacing(3), paddingBottom: spacing(8) },
  note: { color: colors.muted, fontSize: 13, lineHeight: 19 },
  row: { flexDirection: "row", alignItems: "center", gap: spacing(3) },
  name: { fontSize: 16, fontWeight: "800", color: colors.text },
  meta: { color: colors.muted, fontSize: 13, marginTop: 2 },
});
