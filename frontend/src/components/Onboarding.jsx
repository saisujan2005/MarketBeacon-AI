import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function Onboarding({ onComplete }) {
  const { updatePreferences, updateProfile } = useAuth();
  const [step, setStep] = useState(1);
  const [market, setMarket] = useState("US");
  const [sectors, setSectors] = useState([]);
  const [companies, setCompanies] = useState("");
  const [loading, setLoading] = useState(false);

  const toggleSector = (sec) => {
    if (sectors.includes(sec)) {
      setSectors(sectors.filter((s) => s !== sec));
    } else {
      setSectors([...sectors, sec]);
    }
  };

  const handleNextStep = () => {
    setStep(step + 1);
  };

  const handlePrevStep = () => {
    setStep(step - 1);
  };

  const handleFinish = async () => {
    setLoading(true);
    try {
      // 1. Save preferences
      await updatePreferences({
        market_region: market,
        dashboard_layout: sectors.join(","),
      });

      // 2. Set preferred market
      await updateProfile({
        preferred_market: market
      });

      // 3. Auto-populate watchlists for favorites (optional, mock or simple request)
      if (companies.trim()) {
        const compsList = companies.split(",").map((c) => c.trim()).filter(Boolean);
        // We can send these to watchlist add api
        try {
          const api = (await import("../services/api")).default;
          for (const c of compsList) {
            await api.post("/api/watchlist/add", { keyword: c });
          }
        } catch (we) {
          console.warn("Could not save watchlist items", we);
        }
      }

      onComplete();
    } catch (e) {
      console.error("Onboarding preference save failed", e);
      onComplete(); // proceed anyway to not block user
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="onboarding-wrapper">
      <div className="onboarding-card glass-panel animate-fade-in">
        {/* Step Indicator */}
        <div className="onboarding-progress">
          <div className={`progress-dot ${step >= 1 ? "active" : ""}`}></div>
          <div className="progress-line"></div>
          <div className={`progress-dot ${step >= 2 ? "active" : ""}`}></div>
          <div className="progress-line"></div>
          <div className={`progress-dot ${step >= 3 ? "active" : ""}`}></div>
        </div>

        {step === 1 && (
          <div className="onboarding-step-content animate-slide-in">
            <h2 className="onboarding-title">Welcome to MarketBeacon AI</h2>
            <p className="onboarding-subtitle">
              Let's tailor your terminal. First, what is your primary geographic market focus?
            </p>
            
            <div className="market-options-grid">
              <div
                className={`market-card ${market === "US" ? "selected" : ""}`}
                onClick={() => setMarket("US")}
              >
                <div className="market-flag">🇺🇸</div>
                <div className="market-name">United States</div>
                <div className="market-desc">Wall Street, SEC reports, Fed decisions</div>
              </div>
              <div
                className={`market-card ${market === "India" ? "selected" : ""}`}
                onClick={() => setMarket("India")}
              >
                <div className="market-flag">🇮🇳</div>
                <div className="market-name">India</div>
                <div className="market-desc">NSE/BSE equities, RBI briefs, SEBI orders</div>
              </div>
              <div
                className={`market-card ${market === "Crypto" ? "selected" : ""}`}
                onClick={() => setMarket("Crypto")}
              >
                <div className="market-flag">₿</div>
                <div className="market-name">Crypto Markets</div>
                <div className="market-desc">BTC/ETH, Layer 1s, DeFi sentiment, on-chain news</div>
              </div>
              <div
                className={`market-card ${market === "Global" ? "selected" : ""}`}
                onClick={() => setMarket("Global")}
              >
                <div className="market-flag">🌐</div>
                <div className="market-name">Global Markets</div>
                <div className="market-desc">Multi-region coverage, commodities & forex</div>
              </div>
            </div>

            <div className="onboarding-footer">
              <div></div>
              <button className="btn-primary" onClick={handleNextStep}>
                Next Step →
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="onboarding-step-content animate-slide-in">
            <h2 className="onboarding-title">Select Favorite Sectors</h2>
            <p className="onboarding-subtitle">
              Choose the sectors you follow closely to personalize your news feed and smart alerts.
            </p>

            <div className="sectors-options-grid">
              {[
                { id: "Technology", label: "Technology & Software", icon: "💻" },
                { id: "Banking", label: "Banking & Financials", icon: "🏛️" },
                { id: "Energy", label: "Energy & Infrastructure", icon: "⚡" },
                { id: "Healthcare", label: "Healthcare & Biotech", icon: "🧬" },
                { id: "Retail", label: "Consumer Goods & Retail", icon: "🛒" },
                { id: "Automotive", label: "Automotive & Electric Vehicles", icon: "🚗" },
                { id: "Real Estate", label: "Real Estate & REITs", icon: "🏢" },
                { id: "Crypto", label: "Cryptocurrency & Web3", icon: "🪙" },
              ].map((sec) => (
                <div
                  key={sec.id}
                  className={`sector-chip-card ${sectors.includes(sec.id) ? "selected" : ""}`}
                  onClick={() => toggleSector(sec.id)}
                >
                  <span className="sector-icon">{sec.icon}</span>
                  <span className="sector-label">{sec.label}</span>
                </div>
              ))}
            </div>

            <div className="onboarding-footer">
              <button className="btn-secondary" onClick={handlePrevStep}>
                ← Back
              </button>
              <button className="btn-primary" onClick={handleNextStep}>
                Next Step →
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="onboarding-step-content animate-slide-in">
            <h2 className="onboarding-title">Companies of Interest</h2>
            <p className="onboarding-subtitle">
              Which specific companies are you tracking? We'll automatically add them to your watchlist.
            </p>

            <div className="form-group">
              <label htmlFor="companiesInput">Enter company names or tickers (comma-separated)</label>
              <input
                type="text"
                id="companiesInput"
                placeholder="e.g. Nvidia, HDFC Bank, Tesla, Reliance"
                value={companies}
                onChange={(e) => setCompanies(e.target.value)}
                autoFocus
              />
              <p className="field-hint">You can add, edit, or remove these anytime from watchlists.</p>
            </div>

            <div className="onboarding-footer">
              <button className="btn-secondary" onClick={handlePrevStep}>
                ← Back
              </button>
              <button
                className="btn-primary"
                onClick={handleFinish}
                disabled={loading}
              >
                {loading ? "Saving Profile..." : "Complete Setup ✓"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
