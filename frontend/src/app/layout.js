import localFont from "next/font/local";
import { Inter } from "next/font/google";
import "./globals.css";
import Provider from "./Provider";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { Toaster } from "@/components/ui/toaster"

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});

const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "AI Ticket Assistant",
  description: "An intelligent assistant to help with code analysis, task management, and development best practices",
  keywords: "AI, development, code analysis, task management, best practices",
  authors: [{ name: "Ovidiu Bachmatchi" }],
  viewport: "width=device-width, initial-scale=1",
  robots: "index, follow",
  manifest: "/manifest.json"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} ${geistSans.variable} ${geistMono.variable} min-h-screen bg-background`}>
        <Provider>
          <ThemeProvider>
            {children}
            <Toaster />
          </ThemeProvider>
        </Provider>
      </body>
    </html>
  );
}