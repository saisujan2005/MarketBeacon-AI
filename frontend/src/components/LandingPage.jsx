import React from "react";

export default function LandingPage({ onGetStarted, onLogin }) {
  return (
    <div className="landing-container">
      {/* Glow effects background */}
      <div className="glow-bg glow-bg-1"></div>
      <div className="glow-bg glow-bg-2"></div>

      {/* Header / Navbar */}
      <header className="landing-header">
        <div className="brand">
          <span className="brand-logo">📊</span>
          <span className="brand-name">MarketBeacon AI</span>
        </div>
        <div className="header-actions">
          <button className="btn-secondary" onClick={onLogin}>
            Sign In
          </button>
          <button className="btn-primary" onClick={onGetStarted}>
            Get Started
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="badge-promo">⚡ Powered by Next-Gen RAG & LLMs</div>
          <h1 className="hero-title">
            MarketBeacon AI
            <span className="hero-subtitle-primary">
              Your Personal Financial Intelligence Platform
            </span>
          </h1>
          <p className="hero-description">
            Analyze companies. Track markets. Monitor news. Research investments. All powered by AI.
          </p>
          <div className="hero-actions">
            <button className="btn-primary btn-large" onClick={onGetStarted}>
              Get Started Free →
            </button>
            <button className="btn-secondary btn-large" onClick={onLogin}>
              Access Dashboard
            </button>
          </div>
        </div>
      </section>

      {/* Product Preview Mockup Cards */}
      <section className="preview-section">
        <h2 className="section-title">The Terminal of the Future</h2>
        <p className="section-subtitle">A state-of-the-art interface tailored for high-speed financial analytics.</p>
        
        <div className="preview-grid">
          <div className="preview-card glass-panel">
            <div className="preview-header">
              <span className="dot dot-red"></span>
              <span className="dot dot-yellow"></span>
              <span className="dot dot-green"></span>
              <span className="preview-title">Dashboard</span>
            </div>
            <div className="preview-body mock-dashboard">
              <div className="mock-stat-row">
                <div className="mock-stat"><span>PROFIT</span> <strong className="green">+12.4%</strong></div>
                <div className="mock-stat"><span>LATENCY</span> <strong>320ms</strong></div>
                <div className="mock-stat"><span>CONFIDENCE</span> <strong className="orange">85%</strong></div>
              </div>
              <div className="mock-chart">
                <div className="mock-bar" style={{ height: "40%" }}></div>
                <div className="mock-bar" style={{ height: "60%" }}></div>
                <div className="mock-bar" style={{ height: "80%" }}></div>
                <div className="mock-bar" style={{ height: "55%" }}></div>
                <div className="mock-bar" style={{ height: "90%" }}></div>
              </div>
            </div>
          </div>

          <div className="preview-card glass-panel">
            <div className="preview-header">
              <span className="dot dot-red"></span>
              <span className="dot dot-yellow"></span>
              <span className="dot dot-green"></span>
              <span className="preview-title">MarketBeacon AI Copilot</span>
            </div>
            <div className="preview-body mock-copilot">
              <div className="chat-bubble user">Analyze Nvidia's valuation relative to AMD.</div>
              <div className="chat-bubble assistant">
                Nvidia (NVDA) trades at a 32x P/E, while AMD trades at 28x. RAG evidence suggests Nvidia retains a stronger hardware moat in AI accelerator units...
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <h2 className="section-title text-gradient">Designed for Professional Investors</h2>
        
        <div className="features-grid">
          {/* Card 1 */}
          <div className="feature-card glass-panel">
            <div className="feature-icon">🧠</div>
            <h3>AI Copilot</h3>
            <p>Conversational financial research powered by robust Retrieval-Augmented Generation (RAG) and advanced LLMs.</p>
          </div>

          {/* Card 2 */}
          <div className="feature-card glass-panel">
            <div className="feature-icon">📈</div>
            <h3>Smart Alerts</h3>
            <p>Real-time macro and equity market alerts embedded with automated AI reasoning and portfolio impact metrics.</p>
          </div>

          {/* Card 3 */}
          <div className="feature-card glass-panel">
            <div className="feature-icon">📰</div>
            <h3>News Intelligence</h3>
            <p>Aggregated worldwide financial news and institutional sentiment feeds with real-time NLP importance scoring.</p>
          </div>

          {/* Card 4 */}
          <div className="feature-card glass-panel">
            <div className="feature-icon">📚</div>
            <h3>Research Library</h3>
            <p>Securely upload earnings summaries, 10-K filings, annual reports, or research notes. Isolated entirely to your account.</p>
          </div>

          {/* Card 5 */}
          <div className="feature-card glass-panel">
            <div className="feature-icon">📊</div>
            <h3>Company Dossiers</h3>
            <p>Instantly compile institutional-grade company dossiers containing peer matrices, timelines, and fundamental metrics.</p>
          </div>

          {/* Card 6 */}
          <div className="feature-card glass-panel">
            <div className="feature-icon">⭐</div>
            <h3>Watchlists</h3>
            <p>Monitor high-priority tickers and keywords, and receive automated briefings whenever catalysts occur.</p>
          </div>
        </div>
      </section>

      {/* CTA Footer Wrapper */}
      <section className="cta-section">
        <h2 className="cta-title">Upgrade Your Investment Strategy Today</h2>
        <p className="cta-description">Join institutional analysts, traders, and investors utilizing MarketBeacon AI daily.</p>
        <button className="btn-primary btn-large" onClick={onGetStarted}>
          Get Started for Free
        </button>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-links">
          <a href="#about">About</a>
          <a href="#features">Features</a>
          <a href="#privacy">Privacy</a>
          <a href="#terms">Terms</a>
          <a href="#github">GitHub</a>
          <a href="#contact">Contact</a>
        </div>
        <div className="footer-meta">
          <span>MarketBeacon AI V1.0.0</span>
          <span>© 2026 saisujan2005. All Rights Reserved.</span>
        </div>
      </footer>
    </div>
  );
}
