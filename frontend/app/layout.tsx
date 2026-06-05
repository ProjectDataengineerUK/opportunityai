import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import { Sparkles } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "OpportunityAI",
  description: "Seleção inteligente de vagas freelance em IA, Dados e Programação",
};

// Set the theme class before paint to avoid a flash of the wrong theme.
const themeScript = `(function(){try{var t=localStorage.getItem('theme');var d=t?t==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches;if(d)document.documentElement.classList.add('dark');}catch(e){}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className={`${inter.className} min-h-screen`}>
        <header className="sticky top-0 z-30 border-b border-border bg-background/80 backdrop-blur-md">
          <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Sparkles className="h-4 w-4" />
              </span>
              OpportunityAI
            </Link>
            <ThemeToggle />
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
