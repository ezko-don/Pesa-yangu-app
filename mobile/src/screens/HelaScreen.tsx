import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { api } from "../api/client";
import type { ChatMessage, ChatResponse } from "../api/types";
import { Header } from "../components/Header";
import { Loading } from "../components/ui";
import { colors, formatKES, radius, spacing } from "../theme";

const QUICK_PROMPTS = [
  "How am I doing this month?",
  "Where is my money going?",
  "Log 500 lunch at Java",
  "Can I afford to save more?",
];

interface Bubble {
  id: string;
  role: "user" | "assistant";
  content: string;
  logged?: ChatResponse["logged"];
}

export default function HelaScreen() {
  const [messages, setMessages] = useState<Bubble[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    (async () => {
      try {
        const history = await api.get<ChatMessage[]>("/api/hela/chat/");
        setMessages(
          history.map((m) => ({
            id: String(m.id),
            role: m.role,
            content: m.content,
          }))
        );
      } catch {
        // start empty
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const scrollToEnd = useCallback(() => {
    requestAnimationFrame(() => scrollRef.current?.scrollToEnd({ animated: true }));
  }, []);

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || sending) return;
      setInput("");
      const localId = `local-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        { id: localId, role: "user", content: trimmed },
      ]);
      setSending(true);
      scrollToEnd();
      try {
        const res = await api.post<ChatResponse>("/api/hela/chat/", {
          message: trimmed,
        });
        setMessages((prev) => [
          ...prev,
          {
            id: String(res.message_id),
            role: "assistant",
            content: res.reply,
            logged: res.logged,
          },
        ]);
      } catch (e) {
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            role: "assistant",
            content:
              e instanceof Error
                ? `I hit an error: ${e.message}`
                : "I couldn't reach the server. Please try again.",
          },
        ]);
      } finally {
        setSending(false);
        scrollToEnd();
      }
    },
    [sending, scrollToEnd]
  );

  if (loading) return <Loading label="Waking up Hela…" />;

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <Header title="Hela AI" subtitle="Your money copilot" />
      <ScrollView
        ref={scrollRef}
        style={{ flex: 1 }}
        contentContainerStyle={styles.thread}
        onContentSizeChange={scrollToEnd}
      >
        {messages.length === 0 ? (
          <View style={styles.intro}>
            <Text style={styles.introTitle}>Hi, I'm Hela 👋</Text>
            <Text style={styles.introBody}>
              Ask me about your spending, savings or goals. I can also log
              transactions for you — try “Log 500 lunch at Java”.
            </Text>
          </View>
        ) : null}

        {messages.map((m) => (
          <View
            key={m.id}
            style={[
              styles.bubble,
              m.role === "user" ? styles.bubbleUser : styles.bubbleAi,
            ]}
          >
            <Text
              style={m.role === "user" ? styles.textUser : styles.textAi}
            >
              {m.content}
            </Text>
            {m.logged && m.logged.length > 0 ? (
              <View style={styles.logged}>
                {m.logged.map((l, i) => (
                  <Text key={i} style={styles.loggedText}>
                    ✓ Logged {formatKES(l.amount)} · {l.description}
                  </Text>
                ))}
              </View>
            ) : null}
          </View>
        ))}

        {sending ? (
          <View style={[styles.bubble, styles.bubbleAi]}>
            <ActivityIndicator color={colors.primary} />
          </View>
        ) : null}
      </ScrollView>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.quickScroll}
        contentContainerStyle={styles.quickRow}
      >
        {QUICK_PROMPTS.map((q) => (
          <Pressable key={q} style={styles.quickChip} onPress={() => send(q)}>
            <Text style={styles.quickText}>{q}</Text>
          </Pressable>
        ))}
      </ScrollView>

      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          placeholder="Ask Hela anything…"
          placeholderTextColor={colors.muted}
          value={input}
          onChangeText={setInput}
          onSubmitEditing={() => send(input)}
          returnKeyType="send"
        />
        <Pressable
          style={styles.sendBtn}
          onPress={() => send(input)}
          disabled={sending}
        >
          <Text style={styles.sendText}>Send</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  thread: { padding: spacing(4), gap: spacing(2.5) },
  intro: {
    backgroundColor: colors.primaryLight,
    borderRadius: radius.lg,
    padding: spacing(4),
  },
  introTitle: { fontSize: 18, fontWeight: "800", color: colors.primaryDark },
  introBody: { color: colors.text, marginTop: spacing(2), lineHeight: 20 },
  bubble: {
    maxWidth: "85%",
    borderRadius: radius.lg,
    padding: spacing(3.5),
  },
  bubbleUser: {
    alignSelf: "flex-end",
    backgroundColor: colors.primary,
    borderBottomRightRadius: spacing(1),
  },
  bubbleAi: {
    alignSelf: "flex-start",
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderBottomLeftRadius: spacing(1),
  },
  textUser: { color: colors.white, fontSize: 15, lineHeight: 21 },
  textAi: { color: colors.text, fontSize: 15, lineHeight: 21 },
  logged: {
    marginTop: spacing(2),
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: spacing(2),
    gap: spacing(1),
  },
  loggedText: { color: colors.primaryDark, fontSize: 13, fontWeight: "600" },
  quickScroll: { flexGrow: 0 },
  quickRow: {
    paddingHorizontal: spacing(4),
    gap: spacing(2),
    paddingBottom: spacing(2),
    alignItems: "center",
  },
  quickChip: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.pill,
    paddingHorizontal: spacing(3.5),
    paddingVertical: spacing(2),
  },
  quickText: { color: colors.text, fontSize: 13, fontWeight: "600" },
  inputBar: {
    flexDirection: "row",
    gap: spacing(2),
    padding: spacing(3),
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.card,
  },
  input: {
    flex: 1,
    backgroundColor: colors.bg,
    borderRadius: radius.pill,
    paddingHorizontal: spacing(4),
    paddingVertical: spacing(3),
    color: colors.text,
  },
  sendBtn: {
    backgroundColor: colors.primary,
    borderRadius: radius.pill,
    paddingHorizontal: spacing(5),
    justifyContent: "center",
  },
  sendText: { color: colors.white, fontWeight: "800" },
});
