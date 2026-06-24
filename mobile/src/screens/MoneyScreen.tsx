import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  FlatList,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { api } from "../api/client";
import type { Transaction } from "../api/types";
import { Header } from "../components/Header";
import { Badge, Card, Loading } from "../components/ui";
import { colors, formatKES, radius, spacing } from "../theme";

type Filter = "all" | "in" | "out";

interface Summary {
  money_in: string;
  money_out: string;
  count: number;
  documents_parsed: number;
}

const CATEGORIES = [
  "food",
  "transport",
  "shopping",
  "utilities",
  "airtime",
  "entertainment",
  "health",
  "education",
  "salary",
  "other",
];

function initials(text: string): string {
  const clean = text.trim();
  return clean ? clean[0].toUpperCase() : "?";
}

function badgeColors(t: Transaction): { color: string; bg: string } {
  if (t.is_auto_synced) return { color: colors.primaryDark, bg: colors.primaryLight };
  return { color: colors.muted, bg: colors.trackBg };
}

export default function MoneyScreen() {
  const [items, setItems] = useState<Transaction[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);

  const load = useCallback(async () => {
    const params = new URLSearchParams();
    if (filter !== "all") params.set("type", filter);
    if (search.trim()) params.set("search", search.trim());
    const query = params.toString();
    const [list, sum] = await Promise.all([
      api.get<Transaction[]>(`/api/transactions/${query ? `?${query}` : ""}`),
      api.get<Summary>("/api/transactions/summary/"),
    ]);
    setItems(list);
    setSummary(sum);
    setLoading(false);
  }, [filter, search]);

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load]);

  const header = useMemo(
    () => (
      <View>
        {summary ? (
          <View style={styles.row}>
            <Card style={styles.statCard}>
              <Text style={styles.statLabel}>MONEY IN</Text>
              <Text style={[styles.statValue, { color: colors.success }]}>
                {formatKES(summary.money_in, false)}
              </Text>
              <Text style={styles.statCaption}>this period</Text>
            </Card>
            <Card style={styles.statCard}>
              <Text style={styles.statLabel}>MONEY OUT</Text>
              <Text style={[styles.statValue, { color: colors.danger }]}>
                {formatKES(summary.money_out, false)}
              </Text>
              <Text style={styles.statCaption}>{summary.count} transactions</Text>
            </Card>
          </View>
        ) : null}

        <TextInput
          style={styles.searchBox}
          placeholder="Search descriptions…"
          placeholderTextColor={colors.muted}
          value={search}
          onChangeText={setSearch}
        />

        <View style={styles.chips}>
          {(["all", "in", "out"] as Filter[]).map((f) => (
            <Pressable
              key={f}
              onPress={() => setFilter(f)}
              style={[styles.chip, filter === f && styles.chipActive]}
            >
              <Text
                style={[styles.chipText, filter === f && styles.chipTextActive]}
              >
                {f === "all" ? "All" : f === "in" ? "Income" : "Expense"}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>
    ),
    [summary, search, filter]
  );

  if (loading) return <Loading label="Loading transactions…" />;

  return (
    <View style={styles.screen}>
      <Header title="Transactions" subtitle="Search, filter and export" />
      <FlatList
        data={items}
        keyExtractor={(t) => String(t.id)}
        contentContainerStyle={styles.list}
        ListHeaderComponent={header}
        ListEmptyComponent={
          <Text style={styles.empty}>No transactions match your filters.</Text>
        }
        renderItem={({ item }) => {
          const bc = badgeColors(item);
          const out = item.direction === "out";
          return (
            <Card style={styles.txn}>
              <View style={[styles.avatar, out ? styles.avatarOut : styles.avatarIn]}>
                <Text style={styles.avatarText}>{initials(item.description)}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.txnTitle} numberOfLines={1}>
                  {item.description}
                </Text>
                <Text style={styles.txnMeta}>
                  {new Date(item.occurred_at).toLocaleDateString("en-KE", {
                    day: "numeric",
                    month: "short",
                  })}{" "}
                  · {item.category_label}
                </Text>
                <View style={{ marginTop: spacing(1.5) }}>
                  <Badge label={item.source_badge} color={bc.color} bg={bc.bg} />
                </View>
              </View>
              <Text
                style={[
                  styles.txnAmount,
                  { color: out ? colors.danger : colors.success },
                ]}
              >
                {out ? "−" : "+"}
                {formatKES(item.amount)}
              </Text>
            </Card>
          );
        }}
      />

      <Pressable style={styles.fab} onPress={() => setModalOpen(true)}>
        <Text style={styles.fabText}>+  Add Transaction</Text>
      </Pressable>

      <AddTransactionModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSaved={() => {
          setModalOpen(false);
          load();
        }}
      />
    </View>
  );
}

function AddTransactionModal({
  open,
  onClose,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [direction, setDirection] = useState<"out" | "in">("out");
  const [category, setCategory] = useState("food");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setDescription("");
    setAmount("");
    setDirection("out");
    setCategory("food");
    setError(null);
  };

  const save = async () => {
    if (!description.trim() || !amount.trim()) {
      setError("Description and amount are required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.post("/api/transactions/", {
        description: description.trim(),
        amount,
        direction,
        category,
        occurred_at: new Date().toISOString(),
        source_type: "manual",
      });
      reset();
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save transaction");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal visible={open} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.modalOverlay}>
        <View style={styles.modalSheet}>
          <Text style={styles.modalTitle}>Add Transaction</Text>

          <TextInput
            style={styles.input}
            placeholder="Description (e.g. Naivas groceries)"
            placeholderTextColor={colors.muted}
            value={description}
            onChangeText={setDescription}
          />
          <TextInput
            style={styles.input}
            placeholder="Amount (KES)"
            placeholderTextColor={colors.muted}
            keyboardType="numeric"
            value={amount}
            onChangeText={setAmount}
          />

          <View style={styles.chips}>
            {(["out", "in"] as const).map((d) => (
              <Pressable
                key={d}
                onPress={() => setDirection(d)}
                style={[styles.chip, direction === d && styles.chipActive]}
              >
                <Text
                  style={[
                    styles.chipText,
                    direction === d && styles.chipTextActive,
                  ]}
                >
                  {d === "out" ? "Expense" : "Income"}
                </Text>
              </Pressable>
            ))}
          </View>

          <View style={styles.catWrap}>
            {CATEGORIES.map((c) => (
              <Pressable
                key={c}
                onPress={() => setCategory(c)}
                style={[styles.catChip, category === c && styles.chipActive]}
              >
                <Text
                  style={[
                    styles.chipText,
                    category === c && styles.chipTextActive,
                  ]}
                >
                  {c}
                </Text>
              </Pressable>
            ))}
          </View>

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <View style={styles.modalActions}>
            <Pressable style={[styles.btn, styles.btnGhost]} onPress={onClose}>
              <Text style={styles.btnGhostText}>Cancel</Text>
            </Pressable>
            <Pressable
              style={[styles.btn, styles.btnPrimary]}
              onPress={save}
              disabled={saving}
            >
              <Text style={styles.btnPrimaryText}>
                {saving ? "Saving…" : "Save"}
              </Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  list: { padding: spacing(4), paddingBottom: spacing(24), gap: spacing(2.5) },
  row: { flexDirection: "row", gap: spacing(3), marginBottom: spacing(3) },
  statCard: { flex: 1 },
  statLabel: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  statValue: { fontSize: 22, fontWeight: "800", marginTop: spacing(1) },
  statCaption: { color: colors.muted, fontSize: 12, marginTop: spacing(0.5) },
  searchBox: {
    backgroundColor: colors.card,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing(4),
    paddingVertical: spacing(3),
    color: colors.text,
    marginBottom: spacing(3),
  },
  chips: { flexDirection: "row", gap: spacing(2), marginBottom: spacing(2) },
  chip: {
    paddingHorizontal: spacing(4),
    paddingVertical: spacing(2),
    borderRadius: radius.pill,
    backgroundColor: colors.trackBg,
  },
  chipActive: { backgroundColor: colors.primary },
  chipText: { color: colors.muted, fontWeight: "700", fontSize: 13 },
  chipTextActive: { color: colors.white },
  txn: { flexDirection: "row", alignItems: "center", gap: spacing(3) },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarOut: { backgroundColor: colors.dangerBg },
  avatarIn: { backgroundColor: colors.successBg },
  avatarText: { fontWeight: "800", color: colors.text },
  txnTitle: { color: colors.text, fontWeight: "700", fontSize: 15 },
  txnMeta: { color: colors.muted, fontSize: 12, marginTop: 2 },
  txnAmount: { fontWeight: "800", fontSize: 15 },
  empty: { color: colors.muted, textAlign: "center", padding: spacing(8) },
  fab: {
    position: "absolute",
    left: spacing(4),
    right: spacing(4),
    bottom: spacing(4),
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    paddingVertical: spacing(4),
    alignItems: "center",
  },
  fabText: { color: colors.white, fontWeight: "800", fontSize: 15 },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.45)",
    justifyContent: "flex-end",
  },
  modalSheet: {
    backgroundColor: colors.bg,
    borderTopLeftRadius: radius.xl,
    borderTopRightRadius: radius.xl,
    padding: spacing(5),
    gap: spacing(3),
  },
  modalTitle: { fontSize: 18, fontWeight: "800", color: colors.text },
  input: {
    backgroundColor: colors.card,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing(4),
    paddingVertical: spacing(3),
    color: colors.text,
  },
  catWrap: { flexDirection: "row", flexWrap: "wrap", gap: spacing(2) },
  catChip: {
    paddingHorizontal: spacing(3),
    paddingVertical: spacing(1.5),
    borderRadius: radius.pill,
    backgroundColor: colors.trackBg,
  },
  error: { color: colors.danger, fontSize: 13 },
  modalActions: { flexDirection: "row", gap: spacing(3), marginTop: spacing(2) },
  btn: {
    flex: 1,
    paddingVertical: spacing(3.5),
    borderRadius: radius.md,
    alignItems: "center",
  },
  btnGhost: { backgroundColor: colors.trackBg },
  btnGhostText: { color: colors.text, fontWeight: "700" },
  btnPrimary: { backgroundColor: colors.primary },
  btnPrimaryText: { color: colors.white, fontWeight: "800" },
});
