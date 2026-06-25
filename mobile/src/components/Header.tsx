import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing } from "../theme";

export function Header({
  title,
  subtitle,
  right,
}: {
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
}) {
  return (
    <View style={styles.header}>
      <View style={{ flex: 1 }}>
        <Text style={styles.title}>{title}</Text>
        {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
      </View>
      {right}
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing(5),
    paddingTop: spacing(6),
    paddingBottom: spacing(5),
    borderBottomLeftRadius: radius.xl,
    borderBottomRightRadius: radius.xl,
    flexDirection: "row",
    alignItems: "center",
  },
  title: { color: colors.white, fontSize: 22, fontWeight: "800" },
  subtitle: {
    color: "rgba(255,255,255,0.85)",
    fontSize: 13,
    marginTop: spacing(1),
  },
});
