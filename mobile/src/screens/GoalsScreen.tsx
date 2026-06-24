import React, { useCallback, useEffect, useState } from "react";
import {
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { api } from "../api/client";
import type { Goal } from "../api/types";
import { Header } from "../components/Header";
import { Badge, Card, ErrorState, Loading, ProgressBar } from "../components/ui";
import { colors, formatKES, spacing } from "../theme";

const STATUS_STYLE: Record<
  Goal["status"],
  { label: string; color: string; bg: string }
> = {
  ahead: { label: "Ahead", color: colors.success, bg: colors.successBg },
  on_track: { label: "On track", color: colors.primaryDark, bg: colors.primaryLight },
  behind: { label: "Behind", color: colors.warning, bg: colors.warningBg },
  at_risk: { label: "At risk", color: colors.danger, bg: colors.dangerBg },
  completed: { label: "Completed", color: colors.success, bg: colors.successBg },
};

function barColor(status: Goal["status"]): string {
  if (status === "at_risk") return colors.danger;
  if (status === "behind") return colors.warning;
  return colors.primary;
}

export default function GoalsScreen() {
  const [goals, setGoals] = useState<Goal[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      const data = await api.get<Goal[]>("/api/goals/");
      setGoals(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load goals");
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
  if (!goals) return <Loading label="Loading your goals…" />;

  const active = goals.filter((g) => !g.is_completed);

  return (
    <View style={styles.screen}>
      <Header
        title="Goals & Plans"
        subtitle={`${active.length} active · ${goals.length - active.length} completed`}
      />
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {goals.length === 0 ? (
          <Text style={styles.empty}>No goals yet. Create one to start saving.</Text>
        ) : null}

        {goals.map((g) => {
          const st = STATUS_STYLE[g.status];
          return (
            <Card key={g.id} style={styles.goal}>
              <View style={styles.goalTop}>
                <Text style={styles.goalTitle}>{g.title}</Text>
                <Badge label={st.label} color={st.color} bg={st.bg} />
              </View>
              <Text style={styles.goalAmount}>
                {formatKES(g.saved_amount)}{" "}
                <Text style={styles.goalTarget}>of {formatKES(g.target_amount)}</Text>
              </Text>
              <View style={{ marginTop: spacing(2.5) }}>
                <ProgressBar pct={g.progress_pct} color={barColor(g.status)} />
              </View>
              <View style={styles.goalFooter}>
                <Text style={styles.goalPct}>{Math.round(g.progress_pct)}%</Text>
                {g.target_date ? (
                  <Text style={styles.goalDate}>
                    Target{" "}
                    {new Date(g.target_date).toLocaleDateString("en-KE", {
                      month: "short",
                      year: "numeric",
                    })}
                  </Text>
                ) : null}
              </View>
            </Card>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing(4), gap: spacing(3), paddingBottom: spacing(8) },
  empty: { color: colors.muted, textAlign: "center", padding: spacing(8) },
  goal: { gap: spacing(1) },
  goalTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  goalTitle: { fontSize: 16, fontWeight: "800", color: colors.text, flex: 1 },
  goalAmount: { fontSize: 18, fontWeight: "800", color: colors.text, marginTop: spacing(2) },
  goalTarget: { fontSize: 14, fontWeight: "600", color: colors.muted },
  goalFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: spacing(2),
  },
  goalPct: { color: colors.primaryDark, fontWeight: "800" },
  goalDate: { color: colors.muted, fontSize: 13 },
});
