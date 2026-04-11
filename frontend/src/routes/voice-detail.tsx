import { useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useVoice } from '@/hooks/use-queries';
import { generateSpeech } from '@/lib/api';
import { ArrowLeft, Loader2, Play, Square, Mic } from 'lucide-react';
import { cn } from '@/lib/utils';

function Badge({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded text-xs font-medium', className)}>
      {children}
    </span>
  );
}

function TraitRow({ name, value }: { name: string; value: number | null }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-text-secondary w-24 capitalize">{name}</span>
      {value != null ? (
        <>
          <div className="flex-1 h-2 bg-border rounded-full overflow-hidden max-w-[200px]">
            <div className="h-full bg-accent rounded-full transition-all" style={{ width: `${value * 100}%` }} />
          </div>
          <span className="text-xs text-text-secondary w-8 text-right">{(value * 100).toFixed(0)}%</span>
        </>
      ) : (
        <span className="text-xs text-text-secondary">Not scored</span>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <h3 className="text-sm font-semibold text-text-primary uppercase tracking-wider mb-4">{title}</h3>
      {children}
    </div>
  );
}

export default function VoiceDetailPage() {
  const { voiceId } = useParams<{ voiceId: string }>();
  const { data: voice, isLoading, error } = useVoice(voiceId!);

  const [text, setText] = useState('Hello, this is a sample of my voice. How does it sound to you?');
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleGenerate = async () => {
    if (!voiceId || !text.trim()) return;
    setGenerating(true);
    setGenError(null);
    try {
      const blob = await generateSpeech(voiceId, text);
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
    } catch (err) {
      setGenError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
      setPlaying(false);
    } else {
      audioRef.current.play();
      setPlaying(true);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 min-h-screen bg-background">
        <div className="px-8 py-6 border-b border-border animate-pulse space-y-2">
          <div className="h-7 bg-border rounded w-48" />
          <div className="h-4 bg-border rounded w-72" />
        </div>
      </div>
    );
  }

  if (error || !voice) {
    return (
      <div className="flex-1 min-h-screen flex items-center justify-center p-8">
        <div className="text-center">
          <p className="text-text-secondary mb-4">Voice not found</p>
          <Link to="/" className="text-sm text-accent underline">Back to catalog</Link>
        </div>
      </div>
    );
  }

  const enriched = voice.enrichment_status === 'completed';

  return (
    <div className="flex-1 min-h-screen bg-background">
      {/* Header */}
      <header className="px-8 py-6 border-b border-border">
        <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors mb-4">
          <ArrowLeft className="w-4 h-4" />
          Back to catalog
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold text-text-primary">{voice.name}</h1>
              <Badge className="bg-muted text-text-secondary border border-border capitalize">
                {voice.provider}
              </Badge>
              {enriched ? (
                <Badge className="bg-pass/10 text-pass border border-pass/20">Enriched</Badge>
              ) : voice.enrichment_status?.startsWith('failed') ? (
                <Badge className="bg-fail/10 text-fail border border-fail/20">Failed</Badge>
              ) : (
                <Badge className="bg-muted text-text-secondary border border-border">Pending</Badge>
              )}
            </div>
            {voice.description && (
              <p className="text-sm text-text-secondary mt-2 max-w-2xl">{voice.description}</p>
            )}
          </div>
        </div>
      </header>

      <main className="px-8 py-6 space-y-6">
        {/* Voice Generation */}
        <Section title="Try this voice">
          <div className="space-y-3">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={3}
              placeholder="Type something to hear this voice say it..."
              className="w-full px-4 py-3 text-sm rounded-md border border-border bg-background text-text-primary placeholder:text-text-secondary focus:outline-none focus:ring-2 focus:ring-accent/50 resize-none"
            />
            <div className="flex items-center gap-3">
              <button
                onClick={handleGenerate}
                disabled={generating || !text.trim()}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md bg-accent text-white hover:bg-accent/90 transition-colors disabled:opacity-50"
              >
                {generating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Mic className="w-4 h-4" />
                )}
                {generating ? 'Generating...' : 'Generate'}
              </button>

              {audioUrl && (
                <>
                  <button
                    onClick={togglePlay}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md border border-border bg-card hover:bg-muted transition-colors"
                  >
                    {playing ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    {playing ? 'Stop' : 'Play'}
                  </button>
                  <audio
                    ref={audioRef}
                    src={audioUrl}
                    onEnded={() => setPlaying(false)}
                  />
                </>
              )}
            </div>
            {genError && (
              <p className="text-sm text-fail">{genError}</p>
            )}
          </div>
        </Section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Basic Info */}
          <Section title="Voice Properties">
            <dl className="grid grid-cols-2 gap-x-6 gap-y-3">
              {[
                ['Provider', voice.provider],
                ['Model', voice.provider_model],
                ['Gender', voice.gender],
                ['Age Group', voice.age_group],
                ['Accent', voice.accent],
                ['Language', voice.language],
                ['Texture', voice.texture],
                ['Pitch', voice.pitch],
                ['Cost/min', voice.cost_per_min_usd != null ? `$${voice.cost_per_min_usd.toFixed(4)}` : null],
                ['Latency', voice.latency_tier],
              ].map(([label, value]) => (
                <div key={label as string}>
                  <dt className="text-xs text-text-secondary">{label}</dt>
                  <dd className="text-sm text-text-primary capitalize">{(value as string) || '--'}</dd>
                </div>
              ))}
            </dl>
          </Section>

          {/* Traits */}
          <Section title="Voice Traits">
            {voice.traits && Object.values(voice.traits).some((v) => v != null) ? (
              <div className="space-y-3">
                {Object.entries(voice.traits).map(([name, value]) => (
                  <TraitRow key={name} name={name} value={value} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-secondary">No trait scores yet — voice needs enrichment</p>
            )}
          </Section>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Use Cases */}
          <Section title="Use Cases">
            {voice.use_cases?.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {voice.use_cases.map((uc) => (
                  <Badge key={uc} className="bg-primary/5 text-text-primary border border-border capitalize">
                    {uc.replace('_', ' ')}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-secondary">--</p>
            )}
          </Section>

          {/* Personality */}
          <Section title="Personality">
            {voice.personality_tags?.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {voice.personality_tags.map((tag) => (
                  <Badge key={tag} className="bg-primary/5 text-text-primary border border-border capitalize">
                    {tag}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-secondary">--</p>
            )}
          </Section>

          {/* Style */}
          <Section title="Style">
            {voice.style_tags?.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {voice.style_tags.map((tag) => (
                  <Badge key={tag} className="bg-primary/5 text-text-primary border border-border capitalize">
                    {tag}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-secondary">--</p>
            )}
          </Section>
        </div>
      </main>
    </div>
  );
}
