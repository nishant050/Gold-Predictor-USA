import "./globals.css";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";

export const metadata = {
  title: "GoldSight — Gold Price Tracker & Analogy Predictor",
  description: "Comprehensive dashboard correlating 20+ years of gold prices with macroeconomic indicators and world events. Features machine learning and LLM-powered analogy predictions.",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
};


export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', width: '100%' }}>
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
