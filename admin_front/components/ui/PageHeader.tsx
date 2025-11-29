/**
 * PageHeader.tsx
 * 
 * DreamSeed Admin UI - Page header component
 * 
 * Usage:
 *   <PageHeader
 *     title="Dashboard"
 *     subtitle="View your class performance"
 *     rightSlot={<button>Action</button>}
 *   />
 */

import React from "react";

type PageHeaderProps = {
  title: string;
  subtitle?: string;
  rightSlot?: React.ReactNode;
};

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  rightSlot,
}) => (
  <header className="mb-6 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
    <div>
      <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-slate-900 dark:text-gray-100">
        {title}
      </h1>
      {subtitle && (
        <p className="mt-1 text-sm text-slate-500 dark:text-gray-400">
          {subtitle}
        </p>
      )}
    </div>
    {rightSlot && <div className="mt-2 md:mt-0">{rightSlot}</div>}
  </header>
);
