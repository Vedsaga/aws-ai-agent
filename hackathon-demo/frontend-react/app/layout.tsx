import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { AppProvider } from "@/contexts/AppContext";

export const metadata: Metadata = {
  title: "Multi-Agent Orchestration System",
  description: "AI-powered civic engagement and disaster response platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="antialiased h-full m-0 p-0 overflow-hidden">
        <AppProvider>
          {children}
          <Toaster />
        </AppProvider>
      </body>
    </html>
  );
}
