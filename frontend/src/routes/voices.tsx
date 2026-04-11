import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useVoices, useFilters } from '@/hooks/use-queries';
import { Search, Loader2, Mic, X, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Voice } from '@/lib/types';

function TraitBar({ value }: { value: number | null }) {
  if (value == null) return <span className="text-xs text-text-secondary">--</span>;
  return (
    <div className="w-16 h-1.5 bg-border rounded-full overflow-hidden">
      <div className="h-full bg-accent rounded-full" style={{ width: `${value * 100}%` }} />
    </div>
  );
}

function FilterSelect({ label, value, options, onChange }: {
  label: string; value: string; options: string[]; onChange: (v: string) => void;
}) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          'appearance-none pl-3 pr-7 py-1.5 text-xs rounded-md border border-border bg-background',
          'focus:outline-none focus:ring-2 focus:ring-accent/50 cursor-pointer',
          value ? 'text-text-primary font-medium' : 'text-text-secondary',
        )}
      >
        <option value="">{label}</option>
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
      <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-text-secondary pointer-events-none" />
    </div>
  );
}

function VoiceRow({ voice, onClick }: { voice: Voice; onClick: () => void }) {
  const disabled = !voice.ready;
  return (
    <tr
      className={cn(
        'border-b border-border transition-colors',
        disabled
          ? 'opacity-40 cursor-default'
          : 'hover:bg-muted/30 cursor-pointer',
      )}
      onClick={disabled ? undefined : onClick}
    >
      <td className="px-5 py-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-text-primary">{voice.name}</span>
          {disabled && (
            <span className="text-[10px] font-medium text-text-secondary bg-muted px-1.5 py-0.5 rounded">
              not enriched
            </span>
          )}
        </div>
      </td>
      <td className="px-5 py-3">
        <span className="text-xs font-medium text-text-secondary bg-muted px-2 py-0.5 rounded capitalize">
          {voice.provider}
        </span>
      </td>
      <td className="px-5 py-3 text-sm text-text-primary capitalize">{voice.gender}</td>
      <td className="px-5 py-3 text-sm text-text-primary capitalize">{voice.age_group}</td>
      <td className="px-5 py-3 text-sm text-text-primary capitalize">{voice.accent || '--'}</td>
      <td className="px-5 py-3 text-sm text-text-primary capitalize">{voice.texture || '--'}</td>
      <td className="px-5 py-3 text-sm text-text-primary capitalize">{voice.pitch || '--'}</td>
      <td className="px-5 py-3">
        <div className="flex gap-1.5 items-center">
          <TraitBar value={voice.traits?.warmth} />
        </div>
      </td>
      <td className="px-5 py-3">
        <div className="flex flex-wrap gap-1 max-w-[180px]">
          {voice.use_cases?.slice(0, 2).map((uc) => (
            <span key={uc} className="text-[10px] font-medium bg-primary/5 text-text-primary px-1.5 py-0.5 rounded">
              {uc}
            </span>
          ))}
          {(voice.use_cases?.length ?? 0) > 2 && (
            <span className="text-[10px] text-text-secondary">+{voice.use_cases.length - 2}</span>
          )}
        </div>
      </td>
    </tr>
  );
}

export default function VoicesPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [provider, setProvider] = useState('');
  const [gender, setGender] = useState('');
  const [ageGroup, setAgeGroup] = useState('');
  const [texture, setTexture] = useState('');
  const [pitch, setPitch] = useState('');
  const [useCase, setUseCase] = useState('');
  const [showAll, setShowAll] = useState(false);

  const { data: filtersData } = useFilters();
  const { data, isLoading, error } = useVoices();
  const voices = data?.voices ?? [];
  const readyCount = data?.ready_count ?? 0;

  const hasFilters = !!(provider || gender || ageGroup || texture || pitch || useCase);

  const filtered = useMemo(() => {
    let result = voices;
    if (!showAll) result = result.filter((v) => v.ready);
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter((v) =>
        v.name.toLowerCase().includes(q) ||
        v.provider.toLowerCase().includes(q) ||
        (v.description ?? '').toLowerCase().includes(q) ||
        (v.accent ?? '').toLowerCase().includes(q)
      );
    }
    if (provider) result = result.filter((v) => v.provider === provider);
    if (gender) result = result.filter((v) => v.gender === gender);
    if (ageGroup) result = result.filter((v) => v.age_group === ageGroup);
    if (texture) result = result.filter((v) => v.texture === texture);
    if (pitch) result = result.filter((v) => v.pitch === pitch);
    if (useCase) result = result.filter((v) => v.use_cases?.includes(useCase));
    return result;
  }, [voices, search, provider, gender, ageGroup, texture, pitch, useCase, showAll]);

  const clearFilters = () => {
    setProvider(''); setGender(''); setAgeGroup(''); setTexture('');
    setPitch(''); setUseCase(''); setSearch('');
  };

  return (
    <div className="flex-1 min-h-screen bg-background">
      <header className="px-8 py-6 border-b border-border">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-text-primary">Voice Catalog</h1>
            <p className="text-sm text-text-secondary mt-1">
              {readyCount} ready voices across {data?.providers?.length ?? 0} providers
              {voices.length > readyCount && (
                <span className="text-text-secondary"> ({voices.length - readyCount} not enriched)</span>
              )}
            </p>
          </div>
        </div>
      </header>

      <main className="px-8 py-6">
        {/* Search + Filters */}
        <div className="flex flex-wrap items-center gap-3 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary pointer-events-none" />
            <input
              type="text"
              placeholder="Search voices..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-64 pl-9 pr-4 py-2 text-sm rounded-md border border-border bg-background text-text-primary placeholder:text-text-secondary focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>

          <FilterSelect label="Provider" value={provider} options={filtersData?.providers ?? []} onChange={setProvider} />
          <FilterSelect label="Gender" value={gender} options={filtersData?.genders ?? []} onChange={setGender} />
          <FilterSelect label="Age" value={ageGroup} options={filtersData?.age_groups ?? []} onChange={setAgeGroup} />
          <FilterSelect label="Texture" value={texture} options={filtersData?.textures ?? []} onChange={setTexture} />
          <FilterSelect label="Pitch" value={pitch} options={filtersData?.pitches ?? []} onChange={setPitch} />
          <FilterSelect label="Use Case" value={useCase} options={filtersData?.use_cases ?? []} onChange={setUseCase} />

          <button
            onClick={() => setShowAll(!showAll)}
            className={cn(
              'px-3 py-1.5 text-xs rounded-md border transition-colors',
              showAll
                ? 'border-accent bg-accent/5 text-text-primary font-medium'
                : 'border-border text-text-secondary hover:text-text-primary',
            )}
          >
            {showAll ? 'Showing all' : 'Show all'}
          </button>

          {hasFilters && (
            <button
              onClick={clearFilters}
              className="inline-flex items-center gap-1 px-2 py-1.5 text-xs font-medium text-text-secondary hover:text-text-primary transition-colors"
            >
              <X className="w-3 h-3" />
              Clear
            </button>
          )}
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-6 h-6 animate-spin text-text-secondary" />
          </div>
        )}

        {/* Error */}
        {error && !isLoading && (
          <div className="rounded-lg border border-red-500/20 bg-red-500/5 px-5 py-4 text-sm text-red-600">
            {error.message}
          </div>
        )}

        {/* Empty */}
        {!isLoading && !error && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
            <Mic className="w-8 h-8 text-text-secondary" />
            <p className="text-sm text-text-secondary">
              {search || hasFilters ? 'No voices match your filters' : 'No voices in catalog'}
            </p>
          </div>
        )}

        {/* Table */}
        {!isLoading && !error && filtered.length > 0 && (
          <div className="rounded-lg border border-border bg-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    {['Name', 'Provider', 'Gender', 'Age', 'Accent', 'Texture', 'Pitch', 'Warmth', 'Use Cases'].map((h) => (
                      <th
                        key={h}
                        className="px-5 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((voice) => (
                    <VoiceRow
                      key={voice.id}
                      voice={voice}
                      onClick={() => navigate(`/voices/${encodeURIComponent(voice.id)}`)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Count */}
        {!isLoading && filtered.length > 0 && (
          <p className="text-xs text-text-secondary mt-3">
            {filtered.length} voice{filtered.length !== 1 ? 's' : ''}
            {(search || hasFilters) && ` (filtered)`}
          </p>
        )}
      </main>
    </div>
  );
}
