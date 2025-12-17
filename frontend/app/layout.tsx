import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SE RASNA Mirror",
  description: "Sales call analysis and reflection",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
