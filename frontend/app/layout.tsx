import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "OpportunityAI",
  description: "Seleção inteligente de vagas freelance em IA, Dados e Programação",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className={`${inter.className} bg-gray-50 min-h-screen`}>{children}</body>
    </html>
  );
}
