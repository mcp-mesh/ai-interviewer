import type { Metadata } from "next";
import "./globals.css";
import { ReactQueryProvider } from "@/components/providers/react-query-provider";
import { ErrorBoundary } from "@/components/ui/error-boundary";

export const metadata: Metadata = {
  title: "AI Interviewer - Find Your Perfect Career with AI",
  description: "Experience intelligent job matching powered by AI. Get personalized recommendations, auto-filled applications, and AI-powered interview preparation.",
  keywords: "AI jobs, job matching, interview preparation, career advancement, resume optimization, job applications",
  authors: [{ name: "S Corp." }],
  creator: "S Corp.",
  publisher: "S Corp.",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'https://localhost:3000'),
  openGraph: {
    title: "AI Interviewer - Find Your Perfect Career with AI",
    description: "Experience intelligent job matching powered by AI. Get personalized recommendations, auto-filled applications, and AI-powered interview preparation.",
    url: "/",
    siteName: "AI Interviewer",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "AI Interviewer - Find Your Perfect Career with AI",
    description: "Experience intelligent job matching powered by AI. Get personalized recommendations, auto-filled applications, and AI-powered interview preparation.",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: process.env.GOOGLE_SITE_VERIFICATION,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "AI Interviewer by S Corp.",
    "url": process.env.NEXT_PUBLIC_APP_URL || "https://localhost:3000",
    "description": "Experience intelligent job matching powered by AI. Get personalized recommendations, auto-filled applications, and AI-powered interview preparation.",
    "sameAs": [],
    "contactPoint": {
      "@type": "ContactPoint",
      "contactType": "customer service",
      "availableLanguage": "English"
    }
  }

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
        />
      </head>
      <body className="antialiased">
        <ErrorBoundary>
          <ReactQueryProvider>
            {children}
          </ReactQueryProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
