import React, { useCallback, useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import { api } from "../api/client";
import type { Budget } from "../api/types";
import { Header } from "../components/Header";
import { Card, ErrorState, Loading, ProgressBar } from "../components/ui";
import { colors, formatKES, spacing } from "../theme";

export default function BudgetsScreen() {
  const [budgets, setBudgets] = useState<Budget[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setBudgets(await api.get<Budget[]>("/api/budgets/"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load budgets");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!budgets) return <Loading label="Loading budgets…" />;

  const totalSpent = budgets.reduce((s, b) => s + parseFloat(b.spent), 0);
  const totalLimit = budgets.reduce((s, b) => s + parseFloat(b.monthly_limit), 0);
  const overall = totalLimit > 0 ? (totalSpent / totalLimit) * 100 : 0;

  return (
    <View style={styles.screen}>
      <Header title="Budgets" subtitle="Track spending against limits" />
      <ScrollView contentContainerStyle={styles.content}>
        <Card>
          <Text style={styles.summaryLabel}>TOTAL SPENT THIS MONTH</Text>
          <Text style={styles.summaryValue}>
            {formatKES(totalSpent)}{" "}
            <Text style={styles.summaryLimit}>of {formatKES(totalLimit)}</Text>
          </Text>
          <View style={{ marginTop: spacing(3) }}>
            <ProgressBar
              pct={overall}
              color={overall > 100 ? colors.danger : colors.primary}
              height={10}
            />
          </View>
          <Text
            style={[
              styles.summaryStatus,
              { color: overall > 100 ? colors.danger : colors.success },
            ]}
          >
            {overall > 100 ? "Over budget" : "On track"}
          </Text>
        </Card>

        {budgets.map((b) => {
          const over = b.status === "over_budget";
          return (
            <Card key={b.id} style={styles.budget}>
              <View style={styles.budgetTop}>
                <Text style={styles.budgetName}>{b.category_label}</Text>
                <Text
                  style={[
                    styles.budgetPct,
                    { color: over ? colors.danger : colors.muted },
                  ]}
                >
                  {Math.round(b.pct_used)}%
                </Text>
              </View>
              <Text style={styles.budgetAmount}>
                {formatKES(b.spent)}{" "}
                <Text style={styles.budgetLimit}>of {formatKES(b.monthly_limit)}</Text>
              </Text>
              <View style={{ marginTop: spacing(2) }}>
                <ProgressBar
                  pct={b.pct_used}
                  color={over ? colors.danger : colors.primary}
                />
              </View>
              <Text style={styles.budgetRemaining}>
                {parseFloat(b.remaining) >= 0
                  ? `${formatKES(b.remaining)} left`
                  : `${formatKES(Math.abs(parseFloat(b.remaining)))} over`}
              </Text>
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
  summaryLabel: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  summaryValue: {
    color: colors.text,
    fontSize: 26,
    fontWeight: "800",
    marginTop: spacing(1),
  },
  summaryLimit: { fontSize: 15, fontWeight: "600", color: colors.muted },
  summaryStatus: { fontWeight: "700", marginTop: spacing(2) },
  budget: { gap: spacing(1) },
  budgetTop: { flexDirection: "row", justifyContent: "space-between" },
  budgetName: { fontSize: 15, fontWeight: "800", color: colors.text },
  budgetPct: { fontWeight: "800" },
  budgetAmount: { fontSize: 15, fontWeight: "700", color: colors.text, marginTop: spacing(1) },
  budgetLimit: { color: colors.muted, fontWeight: "600" },
  budgetRemaining: { color: colors.muted, fontSize: 13, marginTop: spacing(2) },
});
