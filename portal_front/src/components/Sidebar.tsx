import React, { useState } from 'react';

export default function Sidebar() {
  const [open, setOpen] = useState(false);
  return (
    <aside aria-label="Sidebar" className="md:w-56 md:shrink-0">
      <button
        className="md:hidden border px-3 py-1 rounded m-2"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        aria-controls="side-nav"
      >
        {open ? 'Close' : 'Menu'}
      </button>
      <nav id="side-nav" className={`bg-white/80 backdrop-blur border-r md:block ${open ? 'block' : 'hidden'}`}>
        <ul className="p-3 text-sm space-y-1">
          <li><a href="/" className="block px-2 py-1 rounded hover:bg-gray-50">Home</a></li>
          <li><a href="/guides/us" className="block px-2 py-1 rounded hover:bg-gray-50">US Guides</a></li>
          <li><a href="/guides/us/exams-admissions" className="block px-2 py-1 rounded hover:bg-gray-50">Exams & Admissions</a></li>
          <li><a href="/content/list" className="block px-2 py-1 rounded hover:bg-gray-50">Content</a></li>
          <li className="pt-2 text-gray-500 text-xs">IRT</li>
          <li>
            <a href="/admin/irt/docs" className="block px-2 py-1 rounded hover:bg-gray-50">
              IRT 문서 (Docs)
            </a>
          </li>
          <li>
            <a
              href="https://github.com/dreamseedai/dreamseed_monorepo/blob/staging/attempt-view-lock-v1/shared/irt/docs/06_DEPLOYMENT_GUIDE.md"
              target="_blank"
              rel="noreferrer"
              className="block px-2 py-1 rounded hover:bg-gray-50"
            >
              배포 가이드 (GitHub)
            </a>
          </li>
          <li className="pt-2 text-gray-500 text-xs">Explore</li>
          <li><a href="/guides/us/extracurricular" className="block px-2 py-1 rounded hover:bg-gray-50">Extracurricular</a></li>
          <li><a href="/guides/us/personal-skills" className="block px-2 py-1 rounded hover:bg-gray-50">Personal Skills & Well‑being</a></li>
          <li><a href="/guides/us/scholarship-finances" className="block px-2 py-1 rounded hover:bg-gray-50">Scholarship & Finances</a></li>
        </ul>
      </nav>
    </aside>
  );
}


