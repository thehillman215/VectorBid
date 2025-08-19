import React, { useEffect, useState } from 'react';

interface PreferencePreviewProps {
  persona: string;
}

export default function PreferencePreview({ persona }: PreferencePreviewProps) {
  const [text, setText] = useState('');
  const [json, setJson] = useState<any | null>(null);

  useEffect(() => {
    const handle = setTimeout(async () => {
      if (!text.trim()) {
        setJson(null);
        return;
      }
      try {
        const res = await fetch('/api/parse_preview', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, persona }),
        });
        const data = await res.json();
        setJson(data.preference_schema);
      } catch (err) {
        console.error('preview failed', err);
      }
    }, 300);
    return () => clearTimeout(handle);
  }, [text, persona]);

  return (
    <div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Describe your preferences"
        style={{ width: '100%', minHeight: '4rem', padding: '0.5rem', border: '1px solid #ccc', borderRadius: 4 }}
      />
      {json && (
        <pre style={{ marginTop: '0.5rem', background: '#f5f5f5', padding: '0.5rem', fontSize: '0.8rem', overflowX: 'auto' }}>
          {JSON.stringify(json, null, 2)}
        </pre>
      )}
    </div>
  );
}
