import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import { TokenSyncProvider } from "./TokenSyncProvider";

export const metadata: Metadata = {
  title: "DreamSeed Parent Portal",
  description: "Parent portal for DreamSeedAI learning reports",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50 text-gray-900">
        <TokenSyncProvider>
          <header className="border-b bg-white">
            <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
              <Link href="/" className="text-xl font-bold">
                DreamSeed Parent
              </Link>
              <nav className="flex gap-4 text-sm">
                <Link href="/parent/reports" className="hover:underline">
                  리포트
                </Link>
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
        </TokenSyncProvider>
      </body>
    </html>
  );
}
