import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";

export default function Profile() {
  const { user } = useAuth();
  
  // Local state for profile stats
  const [stats, setStats] = useState({
    documentsCount: 0,
    chatsCount: 0,
    watchlistCount: 0,
    metricsCount: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        // Fetch document library count
        const docRes = await api.get("/api/research/documents");
        const docCount = docRes.data?.length || 0;

        // Fetch chat sessions count
        const chatRes = await api.get("/api/chat/sessions");
        const chatCount = chatRes.data?.length || 0;

        // Fetch watchlist count
        const watchRes = await api.get("/api/watchlists");
        const watchCount = watchRes.data?.length || 0;

        // Fetch aggregate query metrics log count
        const metRes = await api.get("/api/research/metrics/aggregate");
        const metCount = metRes.data?.total_queries || 0;

        setStats({
          documentsCount: docCount,
          chatsCount: chatCount,
          watchlistCount: watchCount,
          metricsCount: metCount
        });
      } catch (err) {
        console.error("Failed to load profile metrics stats", err);
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, []);

  const memberSince = user?.created_at
    ? new Date(user.created_at).toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "June 2026";

  const getPlanBadgeClass = (plan) => {
    if (plan?.toLowerCase() === "pro") return "plan-badge pro";
    if (plan?.toLowerCase() === "enterprise") return "plan-badge enterprise";
    return "plan-badge free";
  };

  return (
    <div className="profile-page-container">
      {/* Top Banner Cover */}
      <div className="profile-banner glow-panel">
        <div className="profile-header-info">
          <div className="profile-avatar-large">
            {user?.profile_picture ? (
              <img src={user.profile_picture} alt={user.full_name} className="avatar-img" />
            ) : (
              <span className="avatar-placeholder">{user?.full_name?.charAt(0).toUpperCase() || "S"}</span>
            )}
          </div>
          <div className="profile-details-title">
            <h2>{user?.full_name || "Sujan"}</h2>
            <div className="profile-plan-row">
              <span className={getPlanBadgeClass(user?.subscription_plan)}>
                {(user?.subscription_plan || "free").toUpperCase()} PLAN
              </span>
              <span className="member-since">Member since {memberSince}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid of Stats Cards */}
      <div className="profile-stats-grid">
        <div className="stat-card glass-panel">
          <span className="stat-icon">📚</span>
          <div className="stat-info">
            <span className="stat-label">Research Library</span>
            <h3>{loading ? "..." : stats.documentsCount}</h3>
            <span className="stat-desc">Documents uploaded</span>
          </div>
        </div>

        <div className="stat-card glass-panel">
          <span className="stat-icon">💬</span>
          <div className="stat-info">
            <span className="stat-label">AI Chat Copilot</span>
            <h3>{loading ? "..." : stats.chatsCount}</h3>
            <span className="stat-desc">Chat sessions opened</span>
          </div>
        </div>

        <div className="stat-card glass-panel">
          <span className="stat-icon">⭐</span>
          <div className="stat-info">
            <span className="stat-label">Active Watchlist</span>
            <h3>{loading ? "..." : stats.watchlistCount}</h3>
            <span className="stat-desc">Companies tracked</span>
          </div>
        </div>

        <div className="stat-card glass-panel">
          <span className="stat-icon">🔬</span>
          <div className="stat-info">
            <span className="stat-label">AI Queries Logged</span>
            <h3>{loading ? "..." : stats.metricsCount}</h3>
            <span className="stat-desc">Valuation research iterations</span>
          </div>
        </div>
      </div>

      {/* Bottom Profile Details Row */}
      <div className="profile-details-row">
        <div className="profile-card-details glass-panel">
          <h3>Account Metadata</h3>
          <div className="meta-list">
            <div className="meta-item">
              <span>Primary Email</span>
              <strong>{user?.email}</strong>
            </div>
            <div className="meta-item">
              <span>Role Privilege</span>
              <strong>{(user?.role || "user").toUpperCase()}</strong>
            </div>
            <div className="meta-item">
              <span>Preferred Region</span>
              <strong>{user?.preferred_market || "US"}</strong>
            </div>
            <div className="meta-item">
              <span>User ID (UUID)</span>
              <strong className="text-small">{user?.id}</strong>
            </div>
            <div className="meta-item">
              <span>Last Login Time</span>
              <strong>
                {user?.last_login
                  ? new Date(user.last_login).toLocaleString()
                  : "Just now"}
              </strong>
            </div>
          </div>
        </div>

        <div className="profile-card-details glass-panel">
          <h3>Available Features in {user?.subscription_plan === "pro" ? "Pro" : "Free"} Plan</h3>
          <ul className="plan-features-list">
            <li className="enabled">✓ Unlimited LLM Copilot Interactions</li>
            <li className="enabled">✓ Real-time News Feed Processing</li>
            <li className="enabled">✓ Heatmaps & Timeline Analytics</li>
            <li className={user?.subscription_plan === "pro" ? "enabled" : "disabled"}>
              {user?.subscription_plan === "pro" ? "✓" : "✗"} Deep Research Mode (Pro Only)
            </li>
            <li className={user?.subscription_plan === "pro" ? "enabled" : "disabled"}>
              {user?.subscription_plan === "pro" ? "✓" : "✗"} Custom PDF Ingestion & Vector Search (Pro Only)
            </li>
            <li className={user?.subscription_plan === "pro" ? "enabled" : "disabled"}>
              {user?.subscription_plan === "pro" ? "✓" : "✗"} Advanced Valuation Metrics Evaluation (Pro Only)
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
