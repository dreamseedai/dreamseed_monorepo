// Minimal route helper.
// Currently used to build internal links like `/questions` or `/questions/[id]/edit`.
// If later you need locale/basePath handling, extend this function.

export function route(path: string): string {
  if (!path) return '/';
  // Normalize to always start with a single leading slash
  if (!path.startsWith('/')) path = `/${path}`;
  return path.replace(/\/+/g, '/');
}
