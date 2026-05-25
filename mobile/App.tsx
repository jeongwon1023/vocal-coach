import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import React from "react";
import { StatusBar } from "expo-status-bar";
import MyPageScreen from "./src/screens/MyPageScreen";
import RecordScreen from "./src/screens/RecordScreen";

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <>
      <StatusBar style="dark" />
      <NavigationContainer>
        <Tab.Navigator
          screenOptions={{
            tabBarActiveTintColor: "#2563eb",
            headerStyle: { backgroundColor: "#f8fafc" },
            headerTitleStyle: { fontWeight: "600" },
          }}
        >
          <Tab.Screen
            name="Record"
            component={RecordScreen}
            options={{ title: "녹음·분석", tabBarLabel: "분석" }}
          />
          <Tab.Screen
            name="MyPage"
            component={MyPageScreen}
            options={{ title: "마이 페이지", tabBarLabel: "마이" }}
          />
        </Tab.Navigator>
      </NavigationContainer>
    </>
  );
}
