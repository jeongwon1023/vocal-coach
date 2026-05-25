import { Audio } from "expo-av";
import React, { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { analyzeAudio, AnalyzeResult } from "../api/client";

export default function RecordScreen() {
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [uri, setUri] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalyzeResult | null>(null);

  const startRecording = async () => {
    try {
      const perm = await Audio.requestPermissionsAsync();
      if (!perm.granted) {
        Alert.alert("권한 필요", "마이크 권한을 허용해 주세요.");
        return;
      }
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });
      const { recording: rec } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      setRecording(rec);
      setResult(null);
    } catch (e) {
      Alert.alert("녹음 오류", String(e));
    }
  };

  const stopRecording = async () => {
    if (!recording) return;
    await recording.stopAndUnloadAsync();
    const fileUri = recording.getURI();
    setUri(fileUri);
    setRecording(null);
  };

  const sendAnalyze = async () => {
    if (!uri) return;
    setAnalyzing(true);
    try {
      const data = await analyzeAudio(uri, "recording.m4a", { useGpt: false });
      setResult(data);
    } catch (e) {
      Alert.alert("분석 실패", e instanceof Error ? e.message : String(e));
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>녹음 & 분석</Text>
      <Text style={styles.sub}>
        MR은 이어폰으로 듣고, 마이크에는 목소리만 녹음하세요.
      </Text>

      <TouchableOpacity
        style={[styles.btn, recording ? styles.btnStop : styles.btnPrimary]}
        onPress={recording ? stopRecording : startRecording}
      >
        <Text style={styles.btnText}>
          {recording ? "녹음 중지" : "녹음 시작"}
        </Text>
      </TouchableOpacity>

      {uri && !recording && (
        <>
          <Text style={styles.hint}>녹음 완료. 서버로 전송할 준비됨.</Text>
          <TouchableOpacity
            style={[styles.btn, styles.btnPrimary]}
            onPress={sendAnalyze}
            disabled={analyzing}
          >
            {analyzing ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.btnText}>분석 시작</Text>
            )}
          </TouchableOpacity>
        </>
      )}

      {result && (
        <View style={styles.result}>
          <Text style={styles.scoreLabel}>종합 점수</Text>
          <Text style={styles.score}>{result.overall_score.toFixed(0)}</Text>
          {result.mr_message ? (
            <Text style={styles.warn}>{result.mr_message}</Text>
          ) : null}
          {result.compare_text ? (
            <Text style={styles.compare}>{result.compare_text}</Text>
          ) : null}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, paddingBottom: 40 },
  title: { fontSize: 22, fontWeight: "700" },
  sub: { color: "#64748b", marginTop: 8, marginBottom: 24 },
  btn: {
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
    marginBottom: 12,
  },
  btnPrimary: { backgroundColor: "#2563eb" },
  btnStop: { backgroundColor: "#dc2626" },
  btnText: { color: "#fff", fontWeight: "600", fontSize: 16 },
  hint: { color: "#64748b", marginBottom: 12 },
  result: {
    marginTop: 24,
    padding: 16,
    backgroundColor: "#f1f5f9",
    borderRadius: 12,
  },
  scoreLabel: { color: "#64748b" },
  score: { fontSize: 48, fontWeight: "800", color: "#2563eb" },
  warn: { color: "#b45309", marginTop: 8 },
  compare: { marginTop: 12, fontSize: 13, color: "#334155" },
});
