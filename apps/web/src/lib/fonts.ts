import { Barlow_Condensed, Be_Vietnam_Pro, Noto_Sans_SC } from "next/font/google";

export const bodyFont = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
  display: "swap",
});

export const displayFont = Barlow_Condensed({
  subsets: ["latin", "vietnamese"],
  weight: ["600", "700", "800"],
  variable: "--font-display",
  display: "swap",
});

export const zhFont = Noto_Sans_SC({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-zh",
  display: "swap",
});

export const fontClassName = `${bodyFont.variable} ${displayFont.variable} ${zhFont.variable}`;
