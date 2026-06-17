import { useEffect, useState } from "react";
import api from "./services/api";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from "recharts";

const NAV_ITEMS = [
  { id: "summary", label: "Market Summary", icon: "📰" },
  { id: "alerts", label: "Alerts", icon: "🚨" },
  { id: "trends", label: "Trends", icon: "📊" },
  { id: "notifications", label: "Notifications", icon: "🔔" },
  { id: "watchlist", label: "Watchlist", icon: "⭐" },
  { id: "ask", label: "Ask AI", icon: "🤖" },
];

const EVENT_COLORS = {
  IPO: "#6366f1",
  REGULATION: "#f59e0b",
  MARKET_FLOW: "#06b6d4",
  COMMODITY: "#10b981",
  CORPORATE: "#8b5cf6",
  OTHER: "#64748b",
};

const IMPORTANCE_COLOR = (score) => {
  if (score >= 85) return "#ef4444";
  if (score >= 70) return "#f59e0b";
  return "#10b981";
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: "#1e293b", border: "1px solid #334155",
        borderRadius: 8, padding: "10px 16px", color: "#f1f5f9", fontSize: 13
      }}>
        <div style={{ color: "#94a3b8", marginBottom: 4 }}>{label}</div>
        <div style={{ color: "#06b6d4", fontWeight: 700 }}>{payload[0].value} events</div>
      </div>
    );
  }
  return null;
};

function ImportanceBar({ score }) {
  const color = IMPORTANCE_COLOR(score);
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Importance
        </span>
        <span style={{ fontSize: 13, fontWeight: 700, color, fontFamily: "monospace" }}>
          {score}
        </span>
      </div>
      <div style={{ height: 4, background: "#1e293b", borderRadius: 99, overflow: "hidden" }}>
        <div style={{
          height: "100%", width: `${score}%`, background: color,
          borderRadius: 99, boxShadow: `0 0 8px ${color}`,
          transition: "width 1s ease"
        }} />
      </div>
    </div>
  );
}

function EventBadge({ type }) {
  const color = EVENT_COLORS[type] || EVENT_COLORS.OTHER;
  return (
    <span style={{
      display: "inline-block", padding: "2px 10px", borderRadius: 99,
      fontSize: 11, fontWeight: 600, letterSpacing: "0.06em",
      color, background: `${color}22`, border: `1px solid ${color}44`
    }}>
      {type}
    </span>
  );
}

export default function App() {
  const [activeSection, setActiveSection] = useState("summary");
  const [alerts, setAlerts] = useState([]);
  const [summary, setSummary] = useState([]);
  const [trends, setTrends] = useState({});
  const [notifications, setNotifications] = useState([]);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [watchlists, setWatchlists] = useState([]);
  const [newKeyword, setNewKeyword] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    api.get("/alerts").then(r => setAlerts(r.data)).catch(() => {});
    api.get("/market-summary").then(r => setSummary(r.data.summary || [])).catch(() => {});
    api.get("/trends").then(r => setTrends(r.data)).catch(() => {});
    api.get("/notifications").then(r => setNotifications(r.data)).catch(() => {});
    api.get("/watchlists").then(r => setWatchlists(r.data)).catch(() => {});
  }, []);

  const askMarketBeacon = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setAnswer("");
    try {
      const r = await api.post("/ask", { question });
      setAnswer(r.data.answer);
    } catch {}
    setLoading(false);
  };

  const addWatchlist = async () => {
    if (!newKeyword.trim()) return;
    try {
      await api.post("/watchlists", { keyword: newKeyword });
      const r = await api.get("/watchlists");
      setWatchlists(r.data);
      setNewKeyword("");
    } catch {}
  };

  const deleteWatchlist = async (id) => {
    try {
      await api.delete(`/watchlists/${id}`);
      const r = await api.get("/watchlists");
      setWatchlists(r.data);
    } catch {}
  };

  const trendData = Object.entries(trends).map(([name, count]) => ({ name, count }));
  const unreadCount = notifications.filter(n => !n.is_read).length;

  const s = styles;

  return (
    <div style={s.root}>
      {/* Sidebar */}
      <aside style={{ ...s.sidebar, width: sidebarOpen ? 240 : 64, transition: "width 0.25s ease" }}>
        <div style={s.logoRow} onClick={() => setSidebarOpen(v => !v)}>
          <div style={s.logoIcon}>MB</div>
          {sidebarOpen && <span style={s.logoText}>MarketBeacon</span>}
        </div>

        <nav style={{ flex: 1, paddingTop: 8 }}>
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveSection(item.id)}
              style={{
                ...s.navBtn,
                background: activeSection === item.id ? "#06b6d418" : "transparent",
                borderLeft: activeSection === item.id ? "3px solid #06b6d4" : "3px solid transparent",
                color: activeSection === item.id ? "#06b6d4" : "#94a3b8",
              }}
            >
              <span style={{ fontSize: 18, minWidth: 24, textAlign: "center" }}>{item.icon}</span>
              {sidebarOpen && (
                <span style={{ marginLeft: 12, fontSize: 14, fontWeight: 500, whiteSpace: "nowrap" }}>
                  {item.label}
                  {item.id === "notifications" && unreadCount > 0 && (
                    <span style={s.badge}>{unreadCount}</span>
                  )}
                </span>
              )}
            </button>
          ))}
        </nav>

        <div style={s.sidebarFooter}>
          {sidebarOpen && <span style={{ fontSize: 11, color: "#475569" }}>AI-powered market intel</span>}
        </div>
      </aside>

      {/* Main */}
      <main style={s.main}>
        {/* Topbar */}
        <div style={s.topbar}>
          <div>
            <div style={s.pageTitle}>
              {NAV_ITEMS.find(n => n.id === activeSection)?.icon}{" "}
              {NAV_ITEMS.find(n => n.id === activeSection)?.label}
            </div>
            <div style={s.pageSubtitle}>
              {new Date().toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
            </div>
          </div>
          <div style={s.topbarRight}>
            <div style={s.statusDot} />
            <span style={{ fontSize: 13, color: "#10b981" }}>Live</span>
          </div>
        </div>

        <div style={s.content}>

          {/* MARKET SUMMARY */}
          {activeSection === "summary" && (
            <div>
              <div style={s.statsRow}>
                <StatCard label="Total Articles" value={summary.length} color="#06b6d4" />
                <StatCard label="High Importance" value={summary.filter(i => i.importance_score >= 80).length} color="#ef4444" />
                <StatCard label="Categories" value={[...new Set(summary.map(i => i.event_type))].length} color="#8b5cf6" />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {summary.length === 0 ? <EmptyState msg="No market summary available" /> : summary.map((item, i) => (
                  <div key={i} style={s.summaryCard}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
                      <div style={{ flex: 1 }}>
                        <div style={s.summaryTitle}>{item.title}</div>
                        <div style={{ marginTop: 8 }}>
                          <EventBadge type={item.event_type} />
                        </div>
                      </div>
                      <div style={{ textAlign: "right", flexShrink: 0 }}>
                        <div style={{ fontSize: 28, fontWeight: 800, color: IMPORTANCE_COLOR(item.importance_score), fontFamily: "monospace", lineHeight: 1 }}>
                          {item.importance_score}
                        </div>
                        <div style={{ fontSize: 10, color: "#475569", marginTop: 2 }}>SCORE</div>
                      </div>
                    </div>
                    <div style={{ height: 3, background: "#1e293b", borderRadius: 99, marginTop: 14, overflow: "hidden" }}>
                      <div style={{
                        height: "100%", width: `${item.importance_score}%`,
                        background: `linear-gradient(90deg, ${IMPORTANCE_COLOR(item.importance_score)}, ${IMPORTANCE_COLOR(item.importance_score)}88)`,
                        borderRadius: 99,
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ALERTS */}
          {activeSection === "alerts" && (
            <div>
              <div style={s.statsRow}>
                <StatCard label="Total Alerts" value={alerts.length} color="#ef4444" />
                <StatCard label="Critical (≥85)" value={alerts.filter(a => a.importance_score >= 85).length} color="#f59e0b" />
                <StatCard label="Categories" value={[...new Set(alerts.map(a => a.event_type))].length} color="#06b6d4" />
              </div>
              {alerts.length === 0 ? <EmptyState msg="No alerts found" /> : (
                <div style={s.grid3}>
                  {alerts.map((alert, i) => (
                    <div key={i} style={s.alertCard}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <EventBadge type={alert.event_type} />
                        <div style={{
                          fontSize: 11, fontWeight: 700, fontFamily: "monospace",
                          color: IMPORTANCE_COLOR(alert.importance_score),
                          background: `${IMPORTANCE_COLOR(alert.importance_score)}18`,
                          padding: "2px 8px", borderRadius: 6
                        }}>
                          #{i + 1}
                        </div>
                      </div>
                      <div style={s.alertTitle}>{alert.title}</div>
                      <ImportanceBar score={alert.importance_score} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TRENDS */}
          {activeSection === "trends" && (
            <div>
              <div style={s.card}>
                <div style={s.cardHeader}>Event Distribution</div>
                <div style={s.cardSub}>Frequency of market events by category</div>
                <div style={{ marginTop: 24 }}>
                  <ResponsiveContainer width="100%" height={360}>
                    <BarChart data={trendData} barCategoryGap="30%">
                      <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 12 }} axisLine={{ stroke: "#1e293b" }} tickLine={false} />
                      <YAxis tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
                      <Tooltip content={<CustomTooltip />} cursor={{ fill: "#ffffff08" }} />
                      <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                        {trendData.map((entry, i) => (
                          <Cell key={i} fill={EVENT_COLORS[entry.name] || EVENT_COLORS.OTHER} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div style={{ ...s.grid3, marginTop: 16 }}>
                {trendData.map((entry, i) => (
                  <div key={i} style={{ ...s.card, display: "flex", alignItems: "center", gap: 14 }}>
                    <div style={{
                      width: 40, height: 40, borderRadius: 10, flexShrink: 0,
                      background: `${EVENT_COLORS[entry.name] || "#64748b"}22`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      border: `1px solid ${EVENT_COLORS[entry.name] || "#64748b"}44`
                    }}>
                      <span style={{ fontSize: 18, fontWeight: 800, color: EVENT_COLORS[entry.name] || "#64748b", fontFamily: "monospace" }}>
                        {entry.count}
                      </span>
                    </div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{entry.name}</div>
                      <div style={{ fontSize: 11, color: "#475569", marginTop: 2 }}>events tracked</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* NOTIFICATIONS */}
          {activeSection === "notifications" && (
            <div>
              <div style={s.statsRow}>
                <StatCard label="Total" value={notifications.length} color="#8b5cf6" />
                <StatCard label="Unread" value={unreadCount} color="#ef4444" />
                <StatCard label="Read" value={notifications.length - unreadCount} color="#10b981" />
              </div>
              {notifications.length === 0 ? <EmptyState msg="No notifications" /> : (
                <div style={s.grid2}>
                  {notifications.map((n, i) => (
                    <div key={i} style={{ ...s.card, borderLeft: `3px solid ${n.is_read ? "#334155" : "#06b6d4"}` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div style={{ fontSize: 13, fontWeight: 700, color: "#e2e8f0", lineHeight: 1.4, flex: 1, paddingRight: 12 }}>
                          {n.title}
                        </div>
                        <div style={{
                          flexShrink: 0, fontSize: 11, fontWeight: 600, padding: "3px 10px",
                          borderRadius: 99, whiteSpace: "nowrap",
                          background: n.is_read ? "#1e293b" : "#06b6d418",
                          color: n.is_read ? "#475569" : "#06b6d4",
                          border: `1px solid ${n.is_read ? "#334155" : "#06b6d444"}`
                        }}>
                          {n.is_read ? "Read" : "Unread"}
                        </div>
                      </div>
                      <div style={{ marginTop: 10, display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontSize: 11, color: "#475569" }}>Watchlist:</span>
                        <span style={{
                          fontSize: 11, fontWeight: 600, color: "#8b5cf6",
                          background: "#8b5cf618", padding: "2px 8px", borderRadius: 6
                        }}>
                          {n.keyword}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* WATCHLIST */}
          {activeSection === "watchlist" && (
            <div>
              <div style={s.card}>
                <div style={s.cardHeader}>Add to Watchlist</div>
                <div style={s.cardSub}>Track keywords across market events and alerts</div>
                <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
                  <input
                    type="text"
                    value={newKeyword}
                    onChange={e => setNewKeyword(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && addWatchlist()}
                    placeholder="e.g. Tesla, RBI, Gold..."
                    style={s.input}
                  />
                  <button onClick={addWatchlist} style={s.btnPrimary}>
                    + Add Keyword
                  </button>
                </div>
              </div>

              <div style={{ marginTop: 20 }}>
                <div style={{ fontSize: 12, color: "#475569", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 12 }}>
                  {watchlists.length} keyword{watchlists.length !== 1 ? "s" : ""} tracked
                </div>
                {watchlists.length === 0 ? <EmptyState msg="No keywords in your watchlist yet" /> : (
                  <div style={s.grid3}>
                    {watchlists.map(item => (
                      <div key={item.id} style={s.watchCard}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <div style={{
                            width: 36, height: 36, borderRadius: 8, background: "#06b6d418",
                            display: "flex", alignItems: "center", justifyContent: "center",
                            fontSize: 15, fontWeight: 700, color: "#06b6d4", flexShrink: 0
                          }}>
                            {item.keyword[0].toUpperCase()}
                          </div>
                          <span style={{ fontSize: 14, fontWeight: 600, color: "#e2e8f0" }}>{item.keyword}</span>
                        </div>
                        <button onClick={() => deleteWatchlist(item.id)} style={s.btnDelete}>
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ASK AI */}
          {activeSection === "ask" && (
            <div>
              <div style={s.card}>
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: 10, background: "linear-gradient(135deg,#06b6d4,#8b5cf6)",
                    display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20
                  }}>🤖</div>
                  <div>
                    <div style={s.cardHeader}>Ask MarketBeacon AI</div>
                    <div style={s.cardSub}>Powered by real-time market intelligence</div>
                  </div>
                </div>
                <div style={{ marginTop: 20 }}>
                  <textarea
                    rows={3}
                    value={question}
                    onChange={e => setQuestion(e.target.value)}
                    placeholder="Ask anything about the markets... e.g. 'What's driving commodity prices today?'"
                    style={{ ...s.input, resize: "vertical", lineHeight: 1.6 }}
                  />
                  <button
                    onClick={askMarketBeacon}
                    disabled={loading}
                    style={{ ...s.btnPrimary, marginTop: 12, opacity: loading ? 0.6 : 1 }}
                  >
                    {loading ? (
                      <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={s.spinner} /> Analyzing markets...
                      </span>
                    ) : "Ask MarketBeacon →"}
                  </button>
                </div>
              </div>

              {answer && (
                <div style={{ ...s.card, marginTop: 16, borderLeft: "3px solid #06b6d4" }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: "#06b6d4", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 12 }}>
                    AI Response
                  </div>
                  <div style={{ fontSize: 15, color: "#cbd5e1", lineHeight: 1.75 }}>{answer}</div>
                </div>
              )}

              <div style={{ ...s.grid3, marginTop: 16 }}>
                {["What are today's biggest market movers?", "Summarize recent IPO activity", "How is the commodity market trending?"].map((q, i) => (
                  <button key={i} onClick={() => setQuestion(q)} style={s.suggestionBtn}>
                    <span style={{ fontSize: 13, color: "#94a3b8" }}>"{q}"</span>
                  </button>
                ))}
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div style={{
      flex: 1, background: "#111827", border: "1px solid #1e293b",
      borderRadius: 12, padding: "18px 22px",
      borderTop: `3px solid ${color}`
    }}>
      <div style={{ fontSize: 32, fontWeight: 800, color, fontFamily: "monospace", lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 12, color: "#64748b", marginTop: 6, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>
    </div>
  );
}

function EmptyState({ msg }) {
  return (
    <div style={{
      textAlign: "center", padding: "60px 20px",
      color: "#334155", fontSize: 15, border: "1px dashed #1e293b",
      borderRadius: 12
    }}>
      <div style={{ fontSize: 36, marginBottom: 12 }}>📭</div>
      {msg}
    </div>
  );
}

const styles = {
  root: {
    display: "flex", minHeight: "100vh",
    background: "#0a0f1e", fontFamily: "'Inter', 'Segoe UI', sans-serif",
    color: "#e2e8f0",
  },
  sidebar: {
    background: "#0d1424", borderRight: "1px solid #1e293b",
    display: "flex", flexDirection: "column",
    position: "sticky", top: 0, height: "100vh",
    overflowX: "hidden", flexShrink: 0,
  },
  logoRow: {
    display: "flex", alignItems: "center", gap: 12,
    padding: "20px 16px", cursor: "pointer",
    borderBottom: "1px solid #1e293b",
  },
  logoIcon: {
    width: 36, height: 36, borderRadius: 9, flexShrink: 0,
    background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
    display: "flex", alignItems: "center", justifyContent: "center",
    fontSize: 12, fontWeight: 800, color: "#fff", letterSpacing: "0.05em",
  },
  logoText: { fontSize: 15, fontWeight: 700, color: "#f1f5f9", whiteSpace: "nowrap" },
  navBtn: {
    width: "100%", display: "flex", alignItems: "center",
    padding: "11px 20px", border: "none", cursor: "pointer",
    transition: "all 0.15s", textAlign: "left",
  },
  badge: {
    display: "inline-flex", alignItems: "center", justifyContent: "center",
    marginLeft: 8, minWidth: 18, height: 18, borderRadius: 99,
    background: "#ef4444", color: "#fff", fontSize: 10, fontWeight: 700, padding: "0 5px",
  },
  sidebarFooter: {
    padding: "16px 20px", borderTop: "1px solid #1e293b",
  },
  main: { flex: 1, display: "flex", flexDirection: "column", minWidth: 0 },
  topbar: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "20px 32px", borderBottom: "1px solid #1e293b",
    background: "#0d1424", position: "sticky", top: 0, zIndex: 10,
  },
  pageTitle: { fontSize: 20, fontWeight: 700, color: "#f1f5f9" },
  pageSubtitle: { fontSize: 12, color: "#475569", marginTop: 2 },
  topbarRight: { display: "flex", alignItems: "center", gap: 8 },
  statusDot: {
    width: 8, height: 8, borderRadius: "50%", background: "#10b981",
    boxShadow: "0 0 8px #10b981",
    animation: "pulse 2s infinite",
  },
  content: { padding: "28px 32px", flex: 1, maxWidth: 1200 },
  statsRow: { display: "flex", gap: 16, marginBottom: 20 },
  card: {
    background: "#111827", border: "1px solid #1e293b",
    borderRadius: 14, padding: "22px 24px",
  },
  cardHeader: { fontSize: 16, fontWeight: 700, color: "#e2e8f0" },
  cardSub: { fontSize: 13, color: "#475569", marginTop: 3 },
  grid3: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 14 },
  grid2: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 14 },
  summaryCard: {
    background: "#111827", border: "1px solid #1e293b",
    borderRadius: 14, padding: "18px 22px",
    transition: "border-color 0.2s",
  },
  summaryTitle: { fontSize: 14, fontWeight: 600, color: "#e2e8f0", lineHeight: 1.5 },
  alertCard: {
    background: "#111827", border: "1px solid #1e293b",
    borderRadius: 14, padding: "20px",
    transition: "transform 0.15s, border-color 0.15s",
  },
  alertTitle: {
    fontSize: 14, fontWeight: 600, color: "#e2e8f0",
    lineHeight: 1.5, marginTop: 14,
  },
  watchCard: {
    background: "#111827", border: "1px solid #1e293b",
    borderRadius: 12, padding: "14px 16px",
    display: "flex", justifyContent: "space-between", alignItems: "center",
    transition: "border-color 0.15s",
  },
  input: {
    width: "100%", background: "#0a0f1e", border: "1px solid #1e293b",
    borderRadius: 10, padding: "12px 16px", color: "#e2e8f0",
    fontSize: 14, outline: "none", boxSizing: "border-box",
    fontFamily: "inherit",
  },
  btnPrimary: {
    background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
    color: "#fff", border: "none", borderRadius: 10,
    padding: "12px 22px", fontSize: 14, fontWeight: 600,
    cursor: "pointer", whiteSpace: "nowrap",
    display: "flex", alignItems: "center", gap: 8,
  },
  btnDelete: {
    background: "#ef444418", color: "#ef4444",
    border: "1px solid #ef444433", borderRadius: 8,
    padding: "6px 10px", fontSize: 12, fontWeight: 600, cursor: "pointer",
    flexShrink: 0,
  },
  suggestionBtn: {
    background: "#111827", border: "1px solid #1e293b",
    borderRadius: 10, padding: "14px 16px", cursor: "pointer",
    textAlign: "left", transition: "border-color 0.15s",
    width: "100%",
  },
  spinner: {
    display: "inline-block", width: 14, height: 14,
    border: "2px solid #ffffff44", borderTop: "2px solid #fff",
    borderRadius: "50%", animation: "spin 0.7s linear infinite",
  },
};
