import { Hono } from 'hono';
import { db } from './db.js';

// Schema enums (mirrored from audition/schema.py)
const GENDERS = ['female', 'male', 'neutral'];
const AGE_GROUPS = ['mature', 'middle', 'young'];
const TEXTURES = ['breathy', 'crisp', 'gravelly', 'raspy', 'rich', 'smooth', 'thin', 'warm'];
const PITCHES = ['high', 'low', 'medium', 'medium-high', 'medium-low'];
const USE_CASES = [
  'advertisement', 'assistant', 'audiobook', 'customer_support', 'education',
  'entertainment', 'finance', 'gaming', 'healthcare', 'ivr', 'meditation',
  'navigation', 'podcast', 'sales', 'storytelling', 'voicemail',
];

interface VoiceRow {
  payload_json: string;
  enrichment_status: string | null;
  enrichment_attempts: number;
}

function shape(row: VoiceRow) {
  const v = JSON.parse(row.payload_json);
  return {
    id: v.id,
    provider: v.provider,
    provider_voice_id: v.provider_voice_id,
    name: v.name,
    description: v.description ?? null,
    gender: v.gender ?? 'unknown',
    age_group: v.age_group ?? 'unknown',
    accent: v.accent ?? null,
    language: v.language ?? 'en',
    provider_model: v.provider_model ?? null,
    texture: v.texture ?? null,
    pitch: v.pitch ?? null,
    traits: v.traits ?? {},
    use_cases: v.use_cases ?? [],
    personality_tags: v.personality_tags ?? [],
    style_tags: v.style_tags ?? [],
    cost_per_min_usd: v.cost_per_min_usd ?? null,
    latency_tier: v.latency_tier ?? null,
    preview_url: v.preview_url ?? null,
    status: v.status ?? 'active',
    metadata_source: v.metadata_source ?? null,
    enrichment_status: row.enrichment_status,
    enrichment_attempts: row.enrichment_attempts ?? 0,
  };
}

export const voices = new Hono();

// List all voices — enriched first, then unenriched marked as disabled
voices.get('/voices', (c) => {
  const rows = db().prepare(
    `SELECT payload_json, enrichment_status, enrichment_attempts
     FROM voices WHERE status IS NULL OR status != 'deprecated'
     ORDER BY
       CASE WHEN enrichment_status = 'completed' THEN 0 ELSE 1 END,
       provider, name`
  ).all() as VoiceRow[];

  const providers = db().prepare(
    'SELECT DISTINCT provider FROM voices WHERE enrichment_status = \'completed\' ORDER BY provider'
  ).all() as { provider: string }[];

  const shaped = rows.map((r) => {
    const v = shape(r);
    v.ready = r.enrichment_status === 'completed';
    return v;
  });

  return c.json({
    voices: shaped,
    total: shaped.length,
    ready_count: shaped.filter((v: any) => v.ready).length,
    providers: providers.map((r) => r.provider),
  });
});

// Filter options
voices.get('/voices/filters', (c) => {
  const providers = db().prepare(
    'SELECT DISTINCT provider FROM voices ORDER BY provider'
  ).all() as { provider: string }[];

  return c.json({
    genders: GENDERS,
    age_groups: AGE_GROUPS,
    textures: TEXTURES,
    pitches: PITCHES,
    use_cases: USE_CASES,
    enrichment_statuses: ['completed', 'pending', 'failed'],
    providers: providers.map((r) => r.provider),
  });
});

// Generate speech (must be before the catch-all GET)
voices.post('/voices/generate', async (c) => {
  const { voice_id, text } = await c.req.json<{ voice_id: string; text: string }>();
  if (!text?.trim()) return c.json({ error: 'text is required' }, 400);
  if (!voice_id) return c.json({ error: 'voice_id is required' }, 400);

  const row = db().prepare('SELECT payload_json FROM voices WHERE id = ?').get(voice_id) as { payload_json: string } | undefined;
  if (!row) return c.json({ error: 'Voice not found' }, 404);

  const voice = JSON.parse(row.payload_json);
  const provider = voice.provider;
  const pvid = voice.provider_voice_id ?? '';

  try {
    const audio = await generateAudio(provider, pvid, voice, text);
    return new Response(audio, {
      headers: { 'Content-Type': 'audio/wav', 'Content-Disposition': `inline; filename=${voice_id.replace(/:/g, '_')}.wav` },
    });
  } catch (err: any) {
    return c.json({ detail: err.message || 'Generation failed' }, 502);
  }
});

// Single voice
voices.get('/voices/:id{.+}', (c) => {
  const id = c.req.param('id');
  const row = db().prepare(
    'SELECT payload_json, enrichment_status, enrichment_attempts FROM voices WHERE id = ?'
  ).get(id) as VoiceRow | undefined;

  if (!row) return c.json({ error: 'Voice not found' }, 404);
  return c.json(shape(row));
});

async function generateAudio(provider: string, pvid: string, voice: any, text: string): Promise<ArrayBuffer> {
  if (provider === 'elevenlabs') {
    const key = process.env.ELEVEN_API_KEY || process.env.ELEVENLABS_API_KEY;
    if (!key) throw new Error('ELEVENLABS_API_KEY not set');
    const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${pvid}`, {
      method: 'POST',
      headers: { 'xi-api-key': key, 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, model_id: 'eleven_turbo_v2' }),
    });
    if (!res.ok) throw new Error(`ElevenLabs ${res.status}`);
    return res.arrayBuffer();
  }

  if (provider === 'openai') {
    const key = process.env.OPENAI_API_KEY;
    if (!key) throw new Error('OPENAI_API_KEY not set');
    const model = voice.provider_model || 'gpt-4o-mini-tts';
    const res = await fetch('https://api.openai.com/v1/audio/speech', {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, voice: pvid, input: text, response_format: 'wav' }),
    });
    if (!res.ok) throw new Error(`OpenAI ${res.status}`);
    return res.arrayBuffer();
  }

  if (provider === 'deepgram') {
    const key = process.env.DEEPGRAM_API_KEY;
    if (!key) throw new Error('DEEPGRAM_API_KEY not set');
    const res = await fetch(`https://api.deepgram.com/v1/speak?model=${pvid}&encoding=linear16&sample_rate=24000`, {
      method: 'POST',
      headers: { Authorization: `Token ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error(`Deepgram ${res.status}`);
    return res.arrayBuffer();
  }

  if (provider === 'rime') {
    const key = process.env.RIME_API_KEY;
    if (!key) throw new Error('RIME_API_KEY not set');
    const model = voice.provider_model || 'mist';
    const parts = pvid.split(':');
    const speaker = parts.length > 1 ? parts[1] : parts[0];
    const res = await fetch('https://users.rime.ai/v1/rime-tts', {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, speaker, modelId: model, audioFormat: 'wav', samplingRate: 22050 }),
    });
    if (!res.ok) throw new Error(`Rime ${res.status}`);
    const data = await res.json();
    if (!data.audioContent) throw new Error('No audioContent in Rime response');
    return Buffer.from(data.audioContent, 'base64');
  }

  if (provider === 'cartesia') {
    const key = process.env.CARTESIA_API_KEY;
    if (!key) throw new Error('CARTESIA_API_KEY not set');
    const res = await fetch('https://api.cartesia.ai/tts/bytes', {
      method: 'POST',
      headers: { 'X-API-Key': key, 'Cartesia-Version': '2024-06-10', 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_id: 'sonic-2',
        transcript: text,
        voice: { mode: 'id', id: pvid },
        output_format: { container: 'wav', encoding: 'pcm_s16le', sample_rate: 44100 },
      }),
    });
    if (!res.ok) throw new Error(`Cartesia ${res.status}`);
    return res.arrayBuffer();
  }

  throw new Error(`TTS not supported for provider: ${provider}`);
}
