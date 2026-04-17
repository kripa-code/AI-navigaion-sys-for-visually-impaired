/**
 * BlindBuddy — API Service Layer
 * REST helpers for navigation, voice transcription, and TTS.
 */
import * as FileSystem from 'expo-file-system';
import { BACKEND_URL } from './config';

/**
 * Transcribe an audio recording URI using Whisper.
 * @param {string} audioUri - Local file URI from expo-av recording
 * @returns {Promise<string>} Transcribed text
 */
export async function transcribeAudio(audioUri) {
  const formData = new FormData();
  formData.append('audio', {
    uri: audioUri,
    type: 'audio/m4a',
    name: 'recording.m4a',
  });

  const response = await fetch(`${BACKEND_URL}/voice/transcribe`, {
    method: 'POST',
    body: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  if (!response.ok) {
    throw new Error(`Transcription failed: ${response.status}`);
  }

  const data = await response.json();
  return data.text || '';
}

/**
 * Start a navigation session for a given destination.
 * @param {string} destination - Voice-provided destination string
 * @param {number} lat - Current latitude
 * @param {number} lng - Current longitude
 * @returns {Promise<object>} Route object with steps, ETA, and distance
 */
export async function startNavigation(destination, lat, lng) {
  const response = await fetch(`${BACKEND_URL}/navigate/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ destination, lat, lng }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Navigation failed: ${response.status}`);
  }

  const data = await response.json();
  return data.route;
}

/**
 * Synthesize text to speech, returns base64 MP3.
 * @param {string} text
 * @returns {Promise<string>} base64 audio string
 */
export async function synthesizeSpeech(text) {
  const response = await fetch(`${BACKEND_URL}/voice/synthesize-base64`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) throw new Error(`TTS failed: ${response.status}`);
  const data = await response.json();
  return data.audio || '';
}
