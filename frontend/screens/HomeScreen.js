/**
 * BlindBuddy — Home Screen
 * Voice-first entry point. User taps mic to speak their destination.
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, Animated,
  Easing, Alert, ActivityIndicator, SafeAreaView,
} from 'react-native';
import * as Location from 'expo-location';
import * as Haptics from 'expo-haptics';
import { Audio } from 'expo-av';
import { transcribeAudio, startNavigation } from '../services/api';
import { BACKEND_URL } from '../services/config';

const PULSE_IDLE_COLOR = '#4f46e5';
const PULSE_RECORDING_COLOR = '#ef4444';

export default function HomeScreen({ navigation }) {
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState('Tap mic to speak your destination');
  const [loading, setLoading] = useState(false);
  const [location, setLocation] = useState(null);
  const recordingRef = useRef(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const glowAnim = useRef(new Animated.Value(0)).current;

  // Pulse animation loop for idle / recording states
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.12, duration: 800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1.0, duration: 800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, []);

  // Glow while recording
  useEffect(() => {
    Animated.timing(glowAnim, {
      toValue: isRecording ? 1 : 0,
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [isRecording]);

  // Get location on mount
  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Required', 'Location access is needed for navigation.');
        return;
      }
      const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High });
      setLocation(loc.coords);
    })();
  }, []);

  const startRecording = async () => {
    try {
      await Audio.requestPermissionsAsync();
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      recordingRef.current = recording;
      setIsRecording(true);
      setStatus('Listening… Speak your destination');
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    } catch (e) {
      Alert.alert('Microphone Error', e.message);
    }
  };

  const stopRecording = async () => {
    if (!recordingRef.current) return;
    setIsRecording(false);
    setStatus('Processing your voice…');
    setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    try {
      await recordingRef.current.stopAndUnloadAsync();
      await Audio.setAudioModeAsync({ allowsRecordingIOS: false });
      const uri = recordingRef.current.getURI();
      recordingRef.current = null;

      // Transcribe
      const transcript = await transcribeAudio(uri);
      if (!transcript || transcript.trim() === '') {
        setStatus("Couldn't catch that. Tap mic and try again.");
        setLoading(false);
        return;
      }

      setStatus(`Routing to: "${transcript}"…`);

      // Get route
      if (!location) {
        Alert.alert('Location Unavailable', 'Waiting for GPS signal…');
        setLoading(false);
        return;
      }
      const route = await startNavigation(transcript, location.latitude, location.longitude);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

      // Navigate to navigation screen
      navigation.navigate('Navigation', {
        route,
        destination: transcript,
        location,
      });
    } catch (e) {
      setStatus('Error: ' + e.message + '. Try again.');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setLoading(false);
    }
  };

  const handleMicPress = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const glowColor = glowAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['rgba(79,70,229,0.3)', 'rgba(239,68,68,0.5)'],
  });

  const micBgColor = isRecording ? PULSE_RECORDING_COLOR : PULSE_IDLE_COLOR;

  return (
    <SafeAreaView style={styles.container}>
      {/* Background orbs */}
      <View style={[styles.orb, styles.orb1]} />
      <View style={[styles.orb, styles.orb2]} />

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.appName}>BlindBuddy</Text>
        <Text style={styles.tagline}>Your AI navigation companion</Text>
      </View>

      {/* Status indicator */}
      <View style={styles.statusCard}>
        <Text style={styles.statusText}>{status}</Text>
        {loading && <ActivityIndicator color="#6366f1" style={{ marginTop: 12 }} />}
      </View>

      {/* Mic button */}
      <View style={styles.micWrapper}>
        {/* Outer glow ring */}
        <Animated.View style={[styles.glowRing, { backgroundColor: glowColor }]} />
        <Animated.View style={[styles.pulseRing, {
          transform: [{ scale: pulseAnim }],
          borderColor: micBgColor,
        }]} />
        <TouchableOpacity
          style={[styles.micButton, { backgroundColor: micBgColor }]}
          onPress={handleMicPress}
          activeOpacity={0.85}
          accessibilityLabel={isRecording ? 'Stop recording' : 'Start recording destination'}
          accessibilityRole="button"
        >
          <Text style={styles.micIcon}>{isRecording ? '⏹' : '🎤'}</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.hint}>
        {isRecording ? 'Tap to stop' : 'Tap the mic and say your destination'}
      </Text>

      {/* Feature pills */}
      <View style={styles.featurePills}>
        {['🗺️ Navigation', '👁️ Obstacle Detection', '🔊 Voice Guidance'].map((f) => (
          <View key={f} style={styles.pill}>
            <Text style={styles.pillText}>{f}</Text>
          </View>
        ))}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a1a',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 40,
    paddingHorizontal: 24,
  },
  orb: {
    position: 'absolute',
    borderRadius: 999,
    opacity: 0.15,
  },
  orb1: {
    width: 300, height: 300,
    backgroundColor: '#4f46e5',
    top: -80, left: -80,
  },
  orb2: {
    width: 200, height: 200,
    backgroundColor: '#7c3aed',
    bottom: 100, right: -50,
  },
  header: {
    alignItems: 'center',
    marginTop: 20,
  },
  appName: {
    fontSize: 38,
    fontWeight: '800',
    color: '#f0f0ff',
    letterSpacing: 1,
  },
  tagline: {
    fontSize: 14,
    color: '#9090c0',
    marginTop: 4,
    letterSpacing: 0.5,
  },
  statusCard: {
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderRadius: 16,
    paddingVertical: 18,
    paddingHorizontal: 24,
    width: '100%',
    minHeight: 70,
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  statusText: {
    color: '#c4c4f0',
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 24,
  },
  micWrapper: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 20,
  },
  glowRing: {
    position: 'absolute',
    width: 160,
    height: 160,
    borderRadius: 80,
  },
  pulseRing: {
    position: 'absolute',
    width: 130,
    height: 130,
    borderRadius: 65,
    borderWidth: 2,
    borderColor: '#4f46e5',
  },
  micButton: {
    width: 110,
    height: 110,
    borderRadius: 55,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#4f46e5',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.6,
    shadowRadius: 20,
    elevation: 12,
  },
  micIcon: {
    fontSize: 40,
  },
  hint: {
    color: '#7070a0',
    fontSize: 13,
    textAlign: 'center',
    marginTop: -10,
  },
  featurePills: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 10,
  },
  pill: {
    backgroundColor: 'rgba(79,70,229,0.15)',
    borderWidth: 1,
    borderColor: 'rgba(99,102,241,0.3)',
    borderRadius: 20,
    paddingVertical: 8,
    paddingHorizontal: 14,
  },
  pillText: {
    color: '#a5b4fc',
    fontSize: 12,
    fontWeight: '600',
  },
});
