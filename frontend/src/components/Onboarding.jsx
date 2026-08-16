import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function Onboarding({ onComplete }) {
  const { updatePreferences, updateProfile } = useAuth();
  const [step, setStep] = useState(1);
  const [market, setMarket] = useState("US");
  const [sectors, setSectors] = useState([]);
  const [companies, setCompanies] = useState("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(null);   // { current, total, name }
  const [failed, setFailed] = useState([]);

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
    setFailed([]);
    try {
      // 1. Save preferences. dashboard_layout doubles as the server-side signal
      //    that this user has completed onboarding.
      await updatePreferences({
        market_region: market,
        dashboard_layout: sectors.join(",") || "none",
      });

      // 2. Set preferred market
      await updateProfile({
        preferred_market: market
      });

      // 3. Seed the watchlist.
      //    Each company is added independently: previously a single failure
      //    aborted the whole loop and silently dropped the remaining entries.
      //    analyze:false keeps this fast — the watchlist page runs the AI
      //    analysis on demand rather than blocking signup on ~3 LLM calls each.
      if (companies.trim()) {
        const compsList = companies
          .split(",")
          .map((c) => c.trim())
          .filter(Boolean);

        const api = (await import("../services/api")).default;
        const failures = [];

        for (let i = 0; i < compsList.length; i++) {
          const name = compsList[i];
          setProgress({ current: i + 1, total: compsList.length, name });
          try {
            await api.post("/api/watchlist/add", { keyword: name, analyze: false });
          } catch (we) {
            console.warn(`Could not add "${name}" to watchlist`, we);
            failures.push(name);
          }
        }

        setProgress(null);
        if (failures.length) {
          // Surface the problem instead of silently losing the user's input.
          setFailed(failures);
          setLoading(false);
          return;
        }
      }

      onComplete();
    } catch (e) {
      console.error("Onboarding preference save failed", e);
      onComplete(); // proceed anyway to not block the user
    } finally {
      setProgress(null);
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
              <p className="field-hint">
                Optional — you can add, edit, or remove these anytime from your watchlist.
              </p>
            </div>

            {progress && (
              <p className="field-hint" style={{ color: "#06b6d4" }}>
                Adding {progress.name}… ({progress.current} of {progress.total})
              </p>
            )}

            {failed.length > 0 && (
              <div
                style={{
                  padding: "10px 12px",
                  marginTop: 12,
                  fontSize: 12,
                  lineHeight: 1.5,
                  color: "#fbbf24",
                  background: "#fbbf2412",
                  border: "1px solid #fbbf2433",
                  borderRadius: 6,
                }}
              >
                Could not add: <strong>{failed.join(", ")}</strong>. Everything else was saved —
                you can add these from your watchlist at any time.
              </div>
            )}

            <div className="onboarding-footer">
              <button className="btn-secondary" onClick={handlePrevStep} disabled={loading}>
                ← Back
              </button>
              <button
                className="btn-primary"
                onClick={failed.length > 0 ? onComplete : handleFinish}
                disabled={loading}
              >
                {loading
                  ? "Setting up your terminal..."
                  : failed.length > 0
                    ? "Continue anyway →"
                    : "Complete Setup ✓"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
