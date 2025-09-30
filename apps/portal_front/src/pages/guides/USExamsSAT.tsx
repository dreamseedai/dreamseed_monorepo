import React from 'react';
import Header from '../../components/Header';
import raw from '../../content/guides/us/exams/sat.json';

type GuideSection = { id: string; title: string; body: string };
type GuideData = { slug: string; title: string; summary: string; intro: string; sections: GuideSection[] };
const data = raw as GuideData;

export default function USExamsSAT() {
  return (
    <div>
      <Header />
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h2 className="text-2xl font-bold mb-2">{data.title}</h2>
        <p className="text-gray-600 mb-4">{data.summary}</p>
        <div className="prose dark:prose-invert max-w-none">
          <p>{data.intro}</p>
          {data.sections.map((s: GuideSection) => (
            <section key={s.id} id={s.id}>
              <h3>{s.title}</h3>
              <p>{s.body}</p>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
