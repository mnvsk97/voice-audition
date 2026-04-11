import { Routes, Route } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import VoicesPage from '@/routes/voices';
import VoiceDetailPage from '@/routes/voice-detail';
import { Link } from 'react-router-dom';

function NotFoundPage() {
  return (
    <div className="flex-1 min-h-screen flex flex-col items-center justify-center gap-4">
      <h1 className="text-4xl font-bold text-text-primary">404</h1>
      <p className="text-text-secondary">Page not found</p>
      <Link to="/" className="text-sm text-accent hover:underline">Go to Voices</Link>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<VoicesPage />} />
        <Route path="/voices/:voiceId" element={<VoiceDetailPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
