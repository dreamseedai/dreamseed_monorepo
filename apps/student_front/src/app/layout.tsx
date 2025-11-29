import "./globals.css";
import type { Metadata } from "next";
import { TokenSyncProvider } from "./TokenSyncProvider";

export const metadata: Metadata = {
  title: "DreamSeed Student",
  description: "Student frontend for DreamSeedAI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50">
        <TokenSyncProvider>
          {children}
        </TokenSyncProvider>
      </body>
    </html>
  );
}
