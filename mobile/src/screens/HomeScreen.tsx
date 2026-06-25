import React, { useCallback, useEffect, useState } from "react";
import {
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { api } from "../api/client";
import type { Dashboard } from "../api/types";
import {
  Card,
  ErrorState,
  Loading,
  SignalRow,
  StatCard,
} from "../components/ui";
import { useAuth } from "../auth/AuthContext";
import { colors, compactKES, spacing } from "../theme";

function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

export default function HomeScreen() {
  const { user } = useAuth();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      const d = await api.get<Dashboard>("/api/dashboard/");
      setData(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load dashboard");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <Loading label="Loading your money…" />;

  const net = parseFloat(data.net_cash_flow);
  const conc = data.signals.spend_concentration;
  const name = user?.first_name || "there";

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.hero}>
        <Text style={styles.heroGreeting}>
          {greeting()}, {name}
        </Text>
        <Text style={styles.heroValue}>{compactKES(net)}</Text>
        <Text style={styles.heroCaption}>
          Net cash flow ·{" "}
          {data.auto_sync.active ? "Synced just now" : "Sync paused"}
        </Text>
      </View>

      <View style={styles.body}>
        <View style={styles.row}>
          <StatCard
            label="Health Score"
            value={String(data.health_score)}
            caption={data.health_score >= 80 ? "Strong month" : "Building"}
            valueColor={colors.primary}
          />
          <StatCard
            label="Net Cash Flow"
            value={(net >= 0 ? "+" : "") + compactKES(net)}
            caption="this period"
            valueColor={net >= 0 ? colors.success : colors.danger}
          />
        </View>
        <View style={styles.row}>
          <StatCard
            label="Savings Rate"
            value={`${data.savings_rate}%`}
            caption={data.savings_rate >= 20 ? "Strong pace" : "Watch"}
          />
          <StatCard
            label="Spend Pace"
            value={`${data.spend_pace}%`}
            caption="of income"
          />
        </View>

        {data.auto_sync.active ? (
          <Card style={styles.syncBanner}>
            <Text style={styles.syncDot}>⚡</Text>
            <Text style={styles.syncText}>
              <Text style={styles.syncStrong}>Auto-sync active</Text> ·{" "}
              {data.auto_sync.today_count} new transactions from{" "}
              {data.auto_sync.sources.slice(0, 2).join(" & ") || "your sources"}{" "}
              today
            </Text>
          </Card>
        ) : null}

        <Text style={styles.sectionLabel}>SIGNAL CARDS</Text>
        <View style={{ gap: spacing(2.5) }}>
          <SignalRow
            tone={data.signals.save === "healthy" ? "good" : "watch"}
            title="Save signal"
            subtitle={
              data.signals.save === "healthy"
                ? "Savings rate in healthy range for goals"
                : "Savings rate is below target this month"
            }
          />
          <SignalRow
            tone={conc.pct >= 50 ? "watch" : "good"}
            title="Spend concentration"
            subtitle={`${conc.top_label ?? "Top category"} is ${conc.pct}% of tracked spending`}
          />
          <SignalRow
            tone="good"
            title="Emergency runway"
            subtitle={`${data.signals.emergency_runway_months} months of expenses covered`}
          />
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { paddingBottom: spacing(8) },
  hero: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing(5),
    paddingTop: spacing(7),
    paddingBottom: spacing(7),
    borderBottomLeftRadius: spacing(6),
    borderBottomRightRadius: spacing(6),
  },
  heroGreeting: { color: "rgba(255,255,255,0.9)", fontSize: 15 },
  heroValue: {
    color: colors.white,
    fontSize: 36,
    fontWeight: "800",
    marginTop: spacing(1),
  },
  heroCaption: { color: "rgba(255,255,255,0.85)", marginTop: spacing(1) },
  body: { padding: spacing(4), gap: spacing(3), marginTop: -spacing(4) },
  row: { flexDirection: "row", gap: spacing(3) },
  syncBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing(2),
    backgroundColor: colors.primaryLight,
    borderColor: "transparent",
  },
  syncDot: { fontSize: 16 },
  syncText: { flex: 1, color: colors.text, fontSize: 13 },
  syncStrong: { fontWeight: "700", color: colors.primaryDark },
  sectionLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.6,
    marginTop: spacing(2),
  },
});
