import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { fetchRecords, RecordSummary } from "../api/client";

export default function MyPageScreen() {
  const [records, setRecords] = useState<RecordSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRecords();
      setRecords(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "오류");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (loading && records.length === 0) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#2563eb" />
        <Text style={styles.hint}>기록 불러오는 중…</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.error}>{error}</Text>
        <Text style={styles.hint}>
          PC에서 run_api.bat 실행 후 API_BASE_URL을 PC IP로 설정하세요.
        </Text>
      </View>
    );
  }

  return (
    <FlatList
      style={styles.container}
      data={records}
      keyExtractor={(item) => item.id}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
      ListEmptyComponent={
        <Text style={styles.hint}>저장된 분석 기록이 없습니다.</Text>
      }
      renderItem={({ item }) => {
        const s = item.stage_scores || {};
        return (
          <View style={styles.card}>
            <Text style={styles.date}>{item.recorded_at}</Text>
            <Text style={styles.song}>{item.song_title || "미지정"}</Text>
            <Text style={styles.score}>종합 {item.overall_score?.toFixed(0) ?? "-"}점</Text>
            <Text style={styles.detail}>
              음정 {s["1"] ?? s[1] ?? "-"} · 박자 {s["2"] ?? s[2] ?? "-"} · 호흡{" "}
              {s["3"] ?? s[3] ?? "-"}
            </Text>
          </View>
        );
      }}
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8fafc", padding: 16 },
  center: { flex: 1, justifyContent: "center", alignItems: "center", padding: 24 },
  card: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#e5e7eb",
  },
  date: { fontSize: 12, color: "#64748b" },
  song: { fontSize: 16, fontWeight: "600", marginTop: 4 },
  score: { fontSize: 22, fontWeight: "700", color: "#2563eb", marginTop: 8 },
  detail: { fontSize: 13, color: "#475569", marginTop: 4 },
  hint: { textAlign: "center", color: "#64748b", marginTop: 12 },
  error: { color: "#dc2626", fontWeight: "600", textAlign: "center" },
});
