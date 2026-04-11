import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { PanelLeftClose, PanelLeftOpen, AudioWaveform, Mic } from 'lucide-react';
import { cn } from '@/lib/utils';

const SIDEBAR_COLLAPSED_KEY = 'voiceaudition.sidebar.collapsed';

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const saved = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
    if (saved !== null) {
      setIsCollapsed(saved === 'true');
    } else if (window.matchMedia('(max-width: 1024px)').matches) {
      setIsCollapsed(true);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(isCollapsed));
  }, [isCollapsed]);

  return (
    <aside
      className={cn(
        'h-screen sticky top-0 bg-sidebar-bg border-r border-border flex flex-col shrink-0 transition-[width] duration-200 ease-out',
        isCollapsed ? 'w-[72px]' : 'w-60',
      )}
    >
      {/* Header */}
      <div className={cn('py-4', isCollapsed ? 'px-2' : 'px-4')}>
        {isCollapsed ? (
          <div className="flex justify-center">
            <button
              type="button"
              onClick={() => setIsCollapsed(false)}
              title="Expand sidebar"
              className="h-8 w-8 rounded border border-border text-text-secondary hover:text-text-primary hover:bg-border/30 flex items-center justify-center transition-colors"
            >
              <PanelLeftOpen className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between gap-2">
            <Link to="/" className="flex items-center gap-2 text-base text-text-primary font-semibold truncate">
              <AudioWaveform className="w-5 h-5" />
              VoiceAudition
            </Link>
            <button
              type="button"
              onClick={() => setIsCollapsed(true)}
              title="Collapse sidebar"
              className="h-7 w-7 rounded border border-border text-text-secondary hover:text-text-primary hover:bg-border/30 flex items-center justify-center transition-colors shrink-0"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      <div className={cn('border-t border-border mb-3', isCollapsed ? 'mx-2' : 'mx-4')} />

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-2 pb-4">
        <ul className="space-y-0.5">
          <li>
            <Link
              to="/"
              title="Voices"
              className={cn(
                'flex items-center h-9 rounded text-sm transition-colors leading-tight',
                isCollapsed ? 'justify-center' : 'gap-2 px-3',
                location.pathname === '/' || location.pathname.startsWith('/voices')
                  ? 'bg-border/60 font-medium text-text-primary'
                  : 'text-text-secondary hover:bg-border/30 hover:text-text-primary',
              )}
            >
              <Mic className="w-4 h-4" />
              {!isCollapsed && 'Voice Catalog'}
            </Link>
          </li>
        </ul>
      </nav>

      {/* Footer */}
      <div className={cn('py-3 border-t border-border', isCollapsed ? 'px-2' : 'px-4')}>
        <p className={cn('text-xs text-text-secondary', isCollapsed ? 'text-center' : '')}>
          {isCollapsed ? 'v0.5' : 'v0.5.0 — 697 voices'}
        </p>
      </div>
    </aside>
  );
}
