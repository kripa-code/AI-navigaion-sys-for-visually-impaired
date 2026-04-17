/**
 * BlindBuddy — Navigation Screen
 * Active guidance mode: captures frames, sends via WebSocket, plays TTS audio.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  SafeAreaView, Animated, Easing, Alert, ScrollView,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Audio } from 'expo-av';
import * as Haptics from 'expo-haptics';
import { WS_URL } from '../services/config';

const URGENCY_COLORS = {
  HIGH: '#ef4444',
  MEDIUM: '#f59e0b',
  LOW: '#22c55e',
};

const URGENCY_LABELS = {
  HIGH: '🚨 STOP',
  MEDIUM: '⚠️ CAUTION',
  LOW: '✅ CLEAR',
};

export default function NavigationScreen({ navigation, route: navRoute }) {
  const { route, destination, location } = navRoute.params;
  const [permission, requestPermission] = useCameraPermissions();
  const [guidance, setGuidance] = useState('Starting navigation…');
  const [urgency, setUrgency] = useState('LOW');
  const [stepIndex, setStepIndex] = useState(0);
  const [stepInfo, setStepInfo] = useState({});
  const [detections, setDetections] = useState([]);
  const [connected, setConnected] = useState(false);
  const [arrived, setArrived] = useState(false);
  const cameraRef = useRef(null);
  const wsRef = useRef(null);
  const soundRef = useRef(null);
  const frameLoopRef = useRef(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const steps = route?.steps || [];

  // Pulsing indicator animation for urgency
  useEffect(() => {
    const shouldPulse = urgency === 'HIGH';
    if (shouldPulse) {
      const loop = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.15, duration: 300, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1.0, duration: 300, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        ])
      );
      loop.start();
      return () => loop.stop();
    } else {
      pulseAnim.setValue(1);
    }
  }, [urgency]);

  // Connect WebSocket on mount
  useEffect(() => {
    if (!permission?.granted) {
      requestPermission();
    }
    connectWebSocket();
    return () => {
      cleanup();
    };
  }, []);

  const connectWebSocket = () => {
    const ws = new WebSocket(`${WS_URL}/ws/session`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      setGuidance('Connected. Starting guidance…');
      startFrameLoop();
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'guidance') {
          setGuidance(msg.text || '');
          setUrgency(msg.urgency || 'LOW');
          setDetections(msg.detections || []);
          if (msg.step_info?.advance) {
            setStepIndex((prev) => Math.min(prev + 1, steps.length - 1));
          }
          if (msg.step_info) setStepInfo(msg.step_info);
          // Haptics on urgency
          if (msg.urgency === 'HIGH') {
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
          } else if (msg.urgency === 'MEDIUM') {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          }
          // Play audio
          if (msg.audio) {
            playBase64Audio(msg.audio);
          }
        } else if (msg.type === 'arrived') {
          setArrived(true);
          setGuidance('You have arrived at your destination!');
          cleanup();
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        }
      } catch (e) {
        console.error('WS parse error:', e);
      }
    };

    ws.onerror = (e) => {
      setConnected(false);
      setGuidance('Connection error. Reconnecting…');
      setTimeout(connectWebSocket, 3000);
    };

    ws.onclose = () => {
      setConnected(false);
    };
  };

  const startFrameLoop = () => {
    frameLoopRef.current = setInterval(async () => {
      if (!cameraRef.current || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
      try {
        const photo = await cameraRef.current.takePictureAsync({
          base64: true,
          quality: 0.4,
          skipProcessing: true,
        });
        const currentStep = steps[stepIndex];
        const navInstruction = currentStep?.instruction || 'Continue forward.';
        wsRef.current.send(JSON.stringify({
          type: 'frame',
          image: photo.base64,
          lat: location?.latitude || 0,
          lng: location?.longitude || 0,
          step_index: stepIndex,
          steps: steps,
          nav_instruction: navInstruction,
        }));
      } catch (e) {
        console.warn('Frame capture error:', e);
      }
    }, 1500);
  };

  const playBase64Audio = async (b64Audio) => {
    try {
      if (soundRef.current) {
        await soundRef.current.unloadAsync();
        soundRef.current = null;
      }
      await Audio.setAudioModeAsync({ playsInSilentModeIOS: true, staysActiveInBackground: true });
      const { sound } = await Audio.Sound.createAsync(
        { uri: `data:audio/mpeg;base64,${b64Audio}` },
        { shouldPlay: true, volume: 1.0 }
      );
      soundRef.current = sound;
    } catch (e) {
      console.warn('Audio playback error:', e);
    }
  };

  const cleanup = () => {
    if (frameLoopRef.current) clearInterval(frameLoopRef.current);
    if (wsRef.current) wsRef.current.close();
    if (soundRef.current) soundRef.current.unloadAsync();
  };

  const handleStop = () => {
    Alert.alert('Stop Navigation', 'End this navigation session?', [
      { text: 'Continue', style: 'cancel' },
      { text: 'Stop', style: 'destructive', onPress: () => { cleanup(); navigation.goBack(); } },
    ]);
  };

  const urgencyColor = URGENCY_COLORS[urgency] || URGENCY_COLORS.LOW;
  const distRemaining = stepInfo?.distance_remaining_m;

  return (
    <SafeAreaView style={styles.container}>
      {/* Camera preview (background, small) */}
      {permission?.granted && !arrived && (
        <CameraView
          ref={cameraRef}
          style={styles.camera}
          facing="back"
        />
      )}

      {/* Overlay */}
      <View style={styles.overlay}>

        {/* Top bar */}
        <View style={styles.topBar}>
          <View style={[styles.dot, { backgroundColor: connected ? '#22c55e' : '#ef4444' }]} />
          <Text style={styles.destinationText} numberOfLines={1}>
            📍 {destination}
          </Text>
          <TouchableOpacity onPress={handleStop} style={styles.stopBtn}>
            <Text style={styles.stopBtnText}>✕</Text>
          </TouchableOpacity>
        </View>

        {/* Urgency badge */}
        <Animated.View style={[
          styles.urgencyBadge,
          { backgroundColor: urgencyColor + '22', borderColor: urgencyColor, transform: [{ scale: pulseAnim }] }
        ]}>
          <Text style={[styles.urgencyLabel, { color: urgencyColor }]}>{URGENCY_LABELS[urgency]}</Text>
        </Animated.View>

        {/* Main guidance card */}
        <View style={styles.guidanceCard}>
          <Text style={styles.guidanceText}>{guidance}</Text>
          {distRemaining !== undefined && distRemaining > 0 && (
            <Text style={styles.distanceText}>
              🚶 {distRemaining}m remaining in this step
            </Text>
          )}
        </View>

        {/* Detections */}
        {detections.length > 0 && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.detectionsRow}>
            {detections.slice(0, 5).map((d, i) => (
              <View key={i} style={[styles.detectionChip, {
                borderColor: d.distance_m < 2 ? '#ef4444' : d.distance_m < 4 ? '#f59e0b' : '#6366f1',
              }]}>
                <Text style={styles.detectionText}>
                  {d.object} · {d.direction} · {d.distance}
                </Text>
              </View>
            ))}
          </ScrollView>
        )}

        {/* Step progress */}
        <View style={styles.stepCard}>
          <Text style={styles.stepLabel}>Step {stepIndex + 1} / {steps.length}</Text>
          <Text style={styles.stepInstruction} numberOfLines={2}>
            {steps[stepIndex]?.instruction || 'Route loaded.'}
          </Text>
        </View>

        {arrived && (
          <View style={styles.arrivedBanner}>
            <Text style={styles.arrivedText}>🎉 Arrived!</Text>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.doneBtn}>
              <Text style={styles.doneBtnText}>Done</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a1a' },
  camera: { ...StyleSheet.absoluteFillObject, opacity: 0.25 },
  overlay: {
    flex: 1, padding: 20, justifyContent: 'space-between'
  },
  topBar: {
    flexDirection: 'row', alignItems: 'center', marginTop: 10,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 12, padding: 12, gap: 10,
  },
  dot: { width: 10, height: 10, borderRadius: 5 },
  destinationText: { flex: 1, color: '#e0e0ff', fontSize: 14, fontWeight: '600' },
  stopBtn: {
    backgroundColor: 'rgba(239,68,68,0.2)', borderRadius: 20,
    paddingHorizontal: 12, paddingVertical: 6,
  },
  stopBtnText: { color: '#ef4444', fontWeight: '700', fontSize: 16 },
  urgencyBadge: {
    alignSelf: 'center', borderWidth: 1.5, borderRadius: 24,
    paddingVertical: 8, paddingHorizontal: 24, marginTop: 10,
  },
  urgencyLabel: { fontSize: 16, fontWeight: '800', letterSpacing: 1 },
  guidanceCard: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 20, padding: 22,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)',
    minHeight: 110, justifyContent: 'center',
  },
  guidanceText: {
    color: '#f0f0ff', fontSize: 20, fontWeight: '700',
    lineHeight: 30, textAlign: 'center',
  },
  distanceText: { color: '#9090c0', fontSize: 13, textAlign: 'center', marginTop: 8 },
  detectionsRow: { marginTop: 4, maxHeight: 50 },
  detectionChip: {
    borderWidth: 1, borderRadius: 16, paddingHorizontal: 12, paddingVertical: 6,
    marginRight: 8, backgroundColor: 'rgba(0,0,0,0.4)',
  },
  detectionText: { color: '#c4c4e0', fontSize: 11 },
  stepCard: {
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderRadius: 16, padding: 16,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.07)',
  },
  stepLabel: { color: '#7070a0', fontSize: 11, fontWeight: '600', marginBottom: 4 },
  stepInstruction: { color: '#c4c4f0', fontSize: 14, lineHeight: 20 },
  arrivedBanner: {
    backgroundColor: 'rgba(34,197,94,0.15)', borderRadius: 20,
    borderWidth: 1, borderColor: '#22c55e',
    padding: 20, alignItems: 'center',
  },
  arrivedText: { color: '#22c55e', fontSize: 26, fontWeight: '800', marginBottom: 12 },
  doneBtn: {
    backgroundColor: '#22c55e', borderRadius: 12,
    paddingHorizontal: 30, paddingVertical: 10,
  },
  doneBtnText: { color: '#fff', fontWeight: '700', fontSize: 16 },
});
