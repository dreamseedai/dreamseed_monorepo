/**
 * Card.tsx
 * 
 * DreamSeed Admin UI - Reusable card component
 * 
 * Usage:
 *   <Card>
 *     <h2>Title</h2>
 *     <p>Content</p>
 *   </Card>
 */

import React, { ReactNode } from "react";
import clsx from "clsx";

type CardProps = {
  children: ReactNode;
  className?: string;
};

export const Card: React.FC<CardProps> = ({ children, className }) => (
  <div
    className={clsx(
      "rounded-2xl border border-slate-200 bg-white shadow-sm",
      "dark:border-gray-700 dark:bg-gray-800",
      "p-4 md:p-5",
      "transition-all hover:shadow-md",
      className
    )}
  >
    {children}
  </div>
);
