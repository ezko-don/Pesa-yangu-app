import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { useAuth } from "../auth/AuthContext";
import { Loading } from "../components/ui";
import BudgetsScreen from "../screens/BudgetsScreen";
import ConnectedAccountsScreen from "../screens/ConnectedAccountsScreen";
import GoalsScreen from "../screens/GoalsScreen";
import HelaScreen from "../screens/HelaScreen";
import HomeScreen from "../screens/HomeScreen";
import LoginScreen from "../screens/LoginScreen";
import MoneyScreen from "../screens/MoneyScreen";
import MoreScreen from "../screens/MoreScreen";
import ProfileScreen from "../screens/ProfileScreen";
import ReportsScreen from "../screens/ReportsScreen";
import { colors, spacing } from "../theme";
import type { MoreStackParams, RootTabParams } from "./types";

const Tab = createBottomTabNavigator<RootTabParams>();
const MoreStack = createNativeStackNavigator<MoreStackParams>();

const TAB_ICONS: Record<keyof RootTabParams, string> = {
  Home: "⌂",
  Money: "≡",
  Hela: "✦",
  Goals: "◎",
  More: "⋯",
};

function TabIcon({
  name,
  focused,
}: {
  name: keyof RootTabParams;
  focused: boolean;
}) {
  return (
    <View style={styles.tabIcon}>
      <Text
        style={[styles.tabIconText, { color: focused ? colors.primary : colors.muted }]}
      >
        {TAB_ICONS[name]}
      </Text>
    </View>
  );
}

function MoreNavigator() {
  return (
    <MoreStack.Navigator screenOptions={{ headerShown: false }}>
      <MoreStack.Screen name="MoreHome" component={MoreScreen} />
      <MoreStack.Screen name="Budgets" component={BudgetsScreen} />
      <MoreStack.Screen name="Reports" component={ReportsScreen} />
      <MoreStack.Screen
        name="ConnectedAccounts"
        component={ConnectedAccountsScreen}
      />
      <MoreStack.Screen name="Profile" component={ProfileScreen} />
    </MoreStack.Navigator>
  );
}

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: styles.tabBar,
        tabBarLabelStyle: styles.tabLabel,
        tabBarIcon: ({ focused }) => (
          <TabIcon name={route.name} focused={focused} />
        ),
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Money" component={MoneyScreen} />
      <Tab.Screen
        name="Hela"
        component={HelaScreen}
        options={{ tabBarLabel: "Hela AI" }}
      />
      <Tab.Screen name="Goals" component={GoalsScreen} />
      <Tab.Screen name="More" component={MoreNavigator} />
    </Tab.Navigator>
  );
}

export default function RootNavigator() {
  const { user, loading } = useAuth();

  if (loading) return <Loading label="Starting Pesa Yangu…" />;

  return (
    <NavigationContainer>
      {user ? <MainTabs /> : <LoginScreen />}
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: colors.card,
    borderTopColor: colors.border,
    height: 64,
    paddingBottom: spacing(2),
    paddingTop: spacing(1.5),
  },
  tabLabel: { fontSize: 11, fontWeight: "600" },
  tabIcon: { alignItems: "center", justifyContent: "center" },
  tabIconText: { fontSize: 20 },
});
