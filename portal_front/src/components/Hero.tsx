import React from 'react';

export default function Hero() {
  return (
    <section style={{ padding: '40px 16px', background: '#f8fafc' }}>
      <div style={{ maxWidth: 960, margin: '0 auto', textAlign: 'center' }}>
        <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 12 }}>Plan your path with DreamSeedAI</h1>
        <p style={{ fontSize: 16, color: '#4b5563', marginBottom: 16 }}>
          Personalized guides, study plans, and expert recommendations for US/CA students.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 12 }}>
          <a href="#profile" className="border px-3 py-2" style={{ textDecoration: 'none', borderRadius: 8, background: '#111827', color: '#fff' }}>내 전략 보기</a>
          <a href="/guides/us" className="border px-3 py-2" style={{ textDecoration: 'none', borderRadius: 8 }}>US Guides</a>
        </div>
      </div>
    </section>
  );
}


