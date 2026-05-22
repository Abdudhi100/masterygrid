import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AuthProvider } from "@/hooks/useAuth";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "MasteryGrid",
  description:
    "AI-powered assignment and assessment platform for smarter schools."
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
