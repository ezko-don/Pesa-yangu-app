import { StatusBar } from "expo-status-bar";
import React from "react";
import { StyleSheet, View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { AuthProvider } from "./src/auth/AuthContext";
import RootNavigator from "./src/navigation";
import { colors } from "./src/theme";

export default function App() {
  return (
    <SafeAreaProvider>
      <View style={styles.root}>
        <StatusBar style="light" />
        <AuthProvider>
          <RootNavigator />
        </AuthProvider>
      </View>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
});
