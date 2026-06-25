import React, { useCallback, useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import { api } from "../api/client";
import type { Reports } from "../api/types";
import { Header } from "../components/Header";
import {
  Card,
  ErrorState,
  Loading,
  ProgressBar,
  StatCard,
} from "../components/ui";
import { colors, compactKES, formatKES, spacing } from "../theme";

export default function ReportsScreen() {
  const [data, setData] = useState<Reports | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setData(await api.get<Reports>("/api/reports/"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load reports");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <Loading label="Crunching the numbers…" />;

  const net = parseFloat(data.net_cash_flow);
  const maxVal = Math.max(
    1,
    ...data.cashflow_trend.flatMap((m) => [
      parseFloat(m.income),
      parseFloat(m.expenses),
    ])
  );

  return (
    <View style={styles.screen}>
      <Header title="Reports" subtitle="Cashflow & category insights" />
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.row}>
          <StatCard
            label="Health Score"
            value={String(data.health_score)}
            valueColor={colors.primary}
          />
          <StatCard
            label="Net Cash Flow"
            value={(net >= 0 ? "+" : "") + compactKES(net)}
            valueColor={net >= 0 ? colors.success : colors.danger}
          />
        </View>
        <View style={styles.row}>
          <StatCard label="Savings Rate" value={`${data.savings_rate}%`} />
          <StatCard label="Spend Pace" value={`${data.spend_pace}%`} />
        </View>

        <Card>
          <Text style={styles.cardTitle}>Cashflow — last 6 months</Text>
          <View style={styles.chart}>
            {data.cashflow_trend.map((m) => {
              const inc = parseFloat(m.income);
              const exp = parseFloat(m.expenses);
              return (
                <View key={`${m.year}-${m.month}`} style={styles.barGroup}>
                  <View style={styles.bars}>
                    <View
                      style={[
                        styles.bar,
                        {
                          height: `${(inc / maxVal) * 100}%`,
                          backgroundColor: colors.primary,
                        },
                      ]}
                    />
                    <View
                      style={[
                        styles.bar,
                        {
                          height: `${(exp / maxVal) * 100}%`,
                          backgroundColor: colors.danger,
                        },
                      ]}
                    />
                  </View>
                  <Text style={styles.barLabel}>{m.label}</Text>
                </View>
              );
            })}
          </View>
          <View style={styles.legend}>
            <View style={styles.legendItem}>
              <View style={[styles.dot, { backgroundColor: colors.primary }]} />
              <Text style={styles.legendText}>Income</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.dot, { backgroundColor: colors.danger }]} />
              <Text style={styles.legendText}>Expenses</Text>
            </View>
            <Text style={styles.avgText}>
              Avg margin {formatKES(data.average_monthly_margin)}
            </Text>
          </View>
        </Card>

        <Card>
          <Text style={styles.cardTitle}>Spending by category</Text>
          <View style={{ gap: spacing(3), marginTop: spacing(2) }}>
            {data.category_breakdown.slice(0, 6).map((c) => (
              <View key={c.category}>
                <View style={styles.catTop}>
                  <Text style={styles.catLabel}>{c.label}</Text>
                  <Text style={styles.catAmount}>{formatKES(c.amount)}</Text>
                </View>
                <View style={{ marginTop: spacing(1.5) }}>
                  <ProgressBar pct={c.pct} />
                </View>
              </View>
            ))}
          </View>
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing(4), gap: spacing(3), paddingBottom: spacing(8) },
  row: { flexDirection: "row", gap: spacing(3) },
  cardTitle: { fontSize: 15, fontWeight: "800", color: colors.text },
  chart: {
    flexDirection: "row",
    alignItems: "flex-end",
    height: 160,
    marginTop: spacing(4),
    gap: spacing(2),
  },
  barGroup: { flex: 1, alignItems: "center", height: "100%", justifyContent: "flex-end" },
  bars: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 3,
    height: "85%",
  },
  bar: { width: 9, borderRadius: 3, minHeight: 2 },
  barLabel: { color: colors.muted, fontSize: 11, marginTop: spacing(1.5) },
  legend: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing(4),
    marginTop: spacing(3),
  },
  legendItem: { flexDirection: "row", alignItems: "center", gap: spacing(1.5) },
  dot: { width: 10, height: 10, borderRadius: 5 },
  legendText: { color: colors.muted, fontSize: 12 },
  avgText: { color: colors.muted, fontSize: 12, marginLeft: "auto" },
  catTop: { flexDirection: "row", justifyContent: "space-between" },
  catLabel: { color: colors.text, fontWeight: "600" },
  catAmount: { color: colors.text, fontWeight: "700" },
});
