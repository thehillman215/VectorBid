import { useEffect, useState } from 'react';

interface FAQItem {
  id: string;
  question: string;
  answer: string;
  rationale?: string | null;
}

export default function FAQPage() {
  const [items, setItems] = useState<FAQItem[]>([]);
  const [query, setQuery] = useState('');

  useEffect(() => {
    fetch('/faq')
      .then((res) => res.json())
      .then((data) => setItems(data));
  }, []);

  const filtered = query
    ? items.filter(
        (i) =>
          i.question.toLowerCase().includes(query.toLowerCase()) ||
          i.answer.toLowerCase().includes(query.toLowerCase())
      )
    : items;

  return (
    <div>
      <h1>FAQ</h1>
      <input
        type="search"
        placeholder="Search FAQ"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <ul>
        {filtered.map((item) => (
          <li key={item.id} id={item.id}>
            <a href={`#${item.id}`}>{item.question}</a>
            <p>
              {item.answer}{' '}
              {item.rationale && (
                <a href={item.rationale} target="_blank" rel="noopener noreferrer">
                  Learn more
                </a>
              )}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
