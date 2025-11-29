import Link from "next/link";
import { route } from "../lib/route";

export type Crumb = { label: string; href?: string };

// Minimal design tokens for easy theming
export type BreadcrumbTokens = {
  root?: string;      // wrapper <ol>
  sep?: string;       // separator
  link?: string;      // link item
  current?: string;   // current item
};

const defaultTokens: Required<BreadcrumbTokens> = {
  root: "flex flex-wrap items-center gap-1 text-sm text-gray-600 dark:text-gray-400",
  sep: "mx-2 text-gray-400 dark:text-gray-500",
  link: "text-blue-600 dark:text-blue-400 hover:underline",
  current: "font-medium text-gray-800 dark:text-gray-200",
};

export function Breadcrumbs({ items, className, tokens }: { items: Crumb[]; className?: string; tokens?: Partial<BreadcrumbTokens> }) {
  if (!items || items.length === 0) return null;
  const t = { ...defaultTokens, ...(tokens || {}) };
  return (
    <nav aria-label="breadcrumb" className={className}>
      <ol className={t.root}>
        {items.map((it, idx) => {
          const isLast = idx === items.length - 1;
          return (
            <li key={idx} className="inline-flex items-center">
              {it.href && !isLast ? (
                <Link href={route(it.href)} className={t.link}>
                  {it.label}
                </Link>
              ) : (
                <span className={isLast ? t.current : undefined}>{it.label}</span>
              )}
              {!isLast && <span className={t.sep}>›</span>}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
