import type { Voice, VoiceListResponse, FilterOptions } from './types';

const BASE = '/api';

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export async function getVoices(params?: Record<string, string>): Promise<VoiceListResponse> {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetchJSON(`${BASE}/voices${qs}`);
}

export async function getVoice(id: string): Promise<Voice> {
  return fetchJSON(`${BASE}/voices/${encodeURIComponent(id)}`);
}

export async function getFilters(): Promise<FilterOptions> {
  return fetchJSON(`${BASE}/voices/filters`);
}

export async function generateSpeech(voiceId: string, text: string): Promise<Blob> {
  const res = await fetch(`${BASE}/voices/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ voice_id: voiceId, text }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.blob();
}
