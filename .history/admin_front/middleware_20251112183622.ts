import { NextRequest, NextResponse } from 'next/server'

const PUBLIC_PATHS = new Set(['/login', '/_next', '/favicon.ico', '/tinymce'])

export function middleware(req: NextRequest) {
  // Always bypass auth in development to simplify local testing and E2E
  if (process.env.NODE_ENV !== 'production') {
    return NextResponse.next();
  }
  // Bypass auth in E2E test runs
  if (process.env.NEXT_PUBLIC_E2E === '1' || process.env.E2E === '1') {
    return NextResponse.next();
  }
  const { pathname } = req.nextUrl
  if ([...PUBLIC_PATHS].some(p => pathname.startsWith(p))) {
    return NextResponse.next()
  }
  const role = req.cookies.get('role')?.value
  // Admin-only guard for questions section
  if (pathname.startsWith('/questions')) {
    if (role === 'admin') return NextResponse.next();
    const url = req.nextUrl.clone();
    url.pathname = '/';
    return NextResponse.redirect(url);
  }
  if (role === 'admin' || role === 'teacher') {
    return NextResponse.next()
  }
  const url = req.nextUrl.clone()
  url.pathname = '/login'
  return NextResponse.redirect(url)
}

export const config = {
  matcher: ['/((?!api).*)'],
}
