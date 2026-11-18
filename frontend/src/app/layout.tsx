import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Query-Court",
  description: "SQL generation with visible review and evidence.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
