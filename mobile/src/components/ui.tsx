import React from "react";
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  View,
  ViewStyle,
} from "react-native";

import { colors, radius, shadow, spacing } from "../theme";

export function Card({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: ViewStyle;
}) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function StatCard({
  label,
  value,
  caption,
  valueColor,
}: {
  label: string;
  value: string;
  caption?: string;
  valueColor?: string;
}) {
  return (
    <Card style={styles.statCard}>
      <Text style={styles.statLabel}>{label.toUpperCase()}</Text>
      <Text style={[styles.statValue, valueColor ? { color: valueColor } : null]}>
        {value}
      </Text>
      {caption ? <Text style={styles.statCaption}>{caption}</Text> : null}
    </Card>
  );
}

export function ProgressBar({
  pct,
  color = colors.primary,
  height = 8,
}: {
  pct: number;
  color?: string;
  height?: number;
}) {
  const clamped = Math.max(0, Math.min(100, pct));
  return (
    <View style={[styles.track, { height, borderRadius: height }]}>
      <View
        style={{
          width: `${clamped}%`,
          height,
          backgroundColor: color,
          borderRadius: height,
        }}
      />
    </View>
  );
}

export function Badge({
  label,
  color = colors.primary,
  bg = colors.primaryLight,
}: {
  label: string;
  color?: string;
  bg?: string;
}) {
  return (
    <View style={[styles.badge, { backgroundColor: bg }]}>
      <Text style={[styles.badgeText, { color }]}>{label}</Text>
    </View>
  );
}

export function SignalRow({
  tone,
  title,
  subtitle,
}: {
  tone: "good" | "watch";
  title: string;
  subtitle: string;
}) {
  const accent = tone === "good" ? colors.success : colors.danger;
  const bg = tone === "good" ? colors.successBg : colors.dangerBg;
  return (
    <View style={[styles.signal, { backgroundColor: bg }]}>
      <View style={[styles.signalBar, { backgroundColor: accent }]} />
      <View style={{ flex: 1 }}>
        <Text style={styles.signalTitle}>{title}</Text>
        <Text style={styles.signalSub}>{subtitle}</Text>
      </View>
    </View>
  );
}

export function SectionTitle({ children }: { children: React.ReactNode }) {
  return <Text style={styles.sectionTitle}>{children}</Text>;
}

export function Loading({ label }: { label?: string }) {
  return (
    <View style={styles.loading}>
      <ActivityIndicator color={colors.primary} size="large" />
      {label ? <Text style={styles.loadingText}>{label}</Text> : null}
    </View>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <View style={styles.loading}>
      <Text style={styles.errorTitle}>Something went wrong</Text>
      <Text style={styles.loadingText}>{message}</Text>
      {onRetry ? (
        <Text style={styles.retry} onPress={onRetry}>
          Tap to retry
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    padding: spacing(4),
    borderWidth: 1,
    borderColor: colors.border,
    ...shadow,
  },
  statCard: { flex: 1, padding: spacing(3.5) },
  statLabel: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  statValue: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "800",
    marginTop: spacing(1),
  },
  statCaption: { color: colors.muted, fontSize: 12, marginTop: spacing(0.5) },
  track: { backgroundColor: colors.trackBg, width: "100%", overflow: "hidden" },
  badge: {
    paddingHorizontal: spacing(2.5),
    paddingVertical: spacing(1),
    borderRadius: radius.pill,
    alignSelf: "flex-start",
  },
  badgeText: { fontSize: 12, fontWeight: "700" },
  signal: {
    flexDirection: "row",
    borderRadius: radius.md,
    padding: spacing(3),
    gap: spacing(3),
    alignItems: "center",
  },
  signalBar: { width: 4, alignSelf: "stretch", borderRadius: 2 },
  signalTitle: { color: colors.text, fontWeight: "700", fontSize: 14 },
  signalSub: { color: colors.muted, fontSize: 12, marginTop: 2 },
  sectionTitle: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.6,
    marginBottom: spacing(2),
  },
  loading: { padding: spacing(10), alignItems: "center", gap: spacing(2) },
  loadingText: { color: colors.muted, textAlign: "center" },
  errorTitle: { color: colors.text, fontWeight: "700", fontSize: 16 },
  retry: { color: colors.primary, fontWeight: "700", marginTop: spacing(2) },
});
