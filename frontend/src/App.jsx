import { useEffect, useState } from "react";
import api from "./services/api";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from "recharts";

import { useAuth } from "./context/AuthContext";
import LandingPage from "./components/LandingPage";
import { Login, Register, ForgotPassword } from "./components/AuthForms";
import Onboarding from "./components/Onboarding";
import Settings from "./components/Settings";
import Profile from "./components/Profile";


// ── Source metadata ───────────────────────────────────────────────────────────
const SOURCE_META = {
  ndtv_profit: { label: "NDTV Profit", flag: "🇮🇳", color: "#ef4444" },
  economic_times_markets: { label: "Economic Times", flag: "💰", color: "#f59e0b" },
  livemint_markets: { label: "Livemint", flag: "🇮🇳", color: "#06b6d4" },
  livemint_economy: { label: "Livemint Economy", flag: "🇮🇳", color: "#06b6d4" },
  hindu_business: { label: "Hindu BL", flag: "🇮🇳", color: "#10b981" },
  bloomberg_markets: { label: "Bloomberg", flag: "📈", color: "#f59e0b" },
  ft_markets: { label: "FT Markets", flag: "🌐", color: "#ef4444" },
  federal_reserve: { label: "Federal Reserve", flag: "🇺🇸", color: "#3b82f6" },
  cnbc_markets: { label: "CNBC", flag: "🇺🇸", color: "#6366f1" },
  wsj_markets: { label: "WSJ", flag: "🇺🇸", color: "#64748b" },
  marketwatch: { label: "MarketWatch", flag: "🇺🇸", color: "#10b981" },
  coindesk: { label: "CoinDesk", flag: "₿", color: "#f59e0b" },
  cointelegraph: { label: "CoinTelegraph", flag: "₿", color: "#8b5cf6" },
  gnews_indian_markets: { label: "Google: NSE/BSE", flag: "🇮🇳", color: "#06b6d4" },
  gnews_rbi: { label: "RBI", flag: "🇮🇳", color: "#10b981" },
  gnews_sebi: { label: "SEBI", flag: "🇮🇳", color: "#8b5cf6" },
  gnews_fed: { label: "Federal Reserve", flag: "🇺🇸", color: "#3b82f6" },
  gnews_wallstreet: { label: "Google: Wall St", flag: "🇺🇸", color: "#f59e0b" },
  gnews_crypto: { label: "Google: Crypto", flag: "₿", color: "#f59e0b" },
  gnews_commodities: { label: "Google: Commodities", flag: "🌐", color: "#10b981" },
  gnews_ipo: { label: "Google: IPO", flag: "🇮🇳", color: "#6366f1" },
  gnews_earnings: { label: "Google: Earnings", flag: "🌐", color: "#ef4444" },
  reuters: { label: "Reuters", flag: "📰", color: "#f97316" },
  motley_fool: { label: "The Motley Fool", flag: "🇺🇸", color: "#fbbf24" },
};

const getSource = (source_id) => {
  if (!source_id) return { label: "Unknown", flag: "🌐", color: "#64748b" };
  const lower = source_id.toLowerCase();
  
  if (lower === "rbi" || lower === "gnews_rbi") return { label: "RBI", flag: "🇮🇳", color: "#10b981" };
  if (lower === "federal reserve" || lower === "federal_reserve" || lower === "gnews_fed") return { label: "Federal Reserve", flag: "🇺🇸", color: "#3b82f6" };
  if (lower === "reuters") return { label: "Reuters", flag: "📰", color: "#f97316" };
  if (lower === "bloomberg" || lower === "bloomberg_markets") return { label: "Bloomberg", flag: "📈", color: "#f59e0b" };
  if (lower === "economic times" || lower === "economic_times" || lower === "economic_times_markets") return { label: "Economic Times", flag: "💰", color: "#fbbf24" };
  if (lower === "coindesk") return { label: "CoinDesk", flag: "₿", color: "#f59e0b" };

  if (SOURCE_META[source_id]) return SOURCE_META[source_id];
  
  const formattedLabel = source_id
    .split(/[_\-\s]+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
  return { label: formattedLabel, flag: "🌐", color: "#64748b" };
};


const formatTimestamp = (dateStr, now = new Date()) => {
  if (!dateStr) return { dateTimeStr: "Unknown", ageStr: "Unknown", diffMs: 0, parsedTime: null };
  
  let cleanStr = dateStr;
  if (typeof cleanStr === "string" && !cleanStr.endsWith("Z") && !cleanStr.includes("+") && !cleanStr.includes("-")) {
    cleanStr += "Z";
  }
  
  const d = new Date(cleanStr);
  if (isNaN(d.getTime())) return { dateTimeStr: "Unknown", ageStr: "Unknown", diffMs: 0, parsedTime: null };
  
  const day = d.getDate();
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const month = months[d.getMonth()];
  const year = d.getFullYear();
  
  let hours = d.getHours();
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12;
  hours = hours ? hours : 12;
  const timeStr = `${String(hours).padStart(2, '0')}:${minutes} ${ampm}`;
  
  const dateTimeStr = `${day} ${month} ${year}, ${timeStr}`;
  
  const diffMs = now.getTime() - d.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);
  
  let ageStr = "";
  if (diffSec < 60) {
    ageStr = "just now";
  } else if (diffMin < 60) {
    ageStr = `${diffMin} min ago`;
  } else if (diffHr < 24) {
    ageStr = `${diffHr}h ago`;
  } else {
    ageStr = `${diffDay} ${diffDay === 1 ? 'day' : 'days'} ago`;
  }
  
  return { dateTimeStr, ageStr, diffMs, parsedTime: d };
};

const formatAlertTimestamp = (dateStr) => {
  if (!dateStr) return { ageStr: "Unknown", tooltipStr: "Created: Unknown" };
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return { ageStr: "Unknown", tooltipStr: "Created: Unknown" };
  
  const diffMs = new Date().getTime() - d.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);
  
  let ageStr = "";
  if (diffSec < 60) {
    ageStr = "just now";
  } else if (diffMin < 60) {
    ageStr = `${diffMin} minute${diffMin === 1 ? '' : 's'} ago`;
  } else if (diffHr < 24) {
    ageStr = `${diffHr} hour${diffHr === 1 ? '' : 's'} ago`;
  } else {
    ageStr = `${diffDay} day${diffDay === 1 ? '' : 's'} ago`;
  }

  const day = String(d.getDate()).padStart(2, '0');
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const month = months[d.getMonth()];
  const year = d.getFullYear();
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const seconds = String(d.getSeconds()).padStart(2, '0');
  
  let tz = "IST";
  try {
    const parts = d.toLocaleDateString('en-US', { day: 'numeric', timeZoneName: 'short' }).split(' ');
    tz = parts[parts.length - 1];
  } catch (e) {
    // ignore
  }
  if (tz && (tz.includes('/') || !isNaN(tz))) {
    tz = "IST";
  }

  const tooltipStr = `Created: ${day} ${month} ${year} ${hours}:${minutes}:${seconds} ${tz}`;
  return { ageStr, tooltipStr };
};



// ── Nav items ─────────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { id: "summary", label: "News Intelligence", icon: "📰" },
  { id: "watchlist", label: "Watchlists", icon: "⭐" },
  { id: "portfolio", label: "Portfolio Intelligence", icon: "💼" },
  { id: "workspace", label: "AI Research Workspace", icon: "🧬" },
  { id: "heatmap", label: "Sector Heatmap", icon: "🔥" },
  { id: "timeline", label: "Event Timeline", icon: "⏳" },
  { id: "reports", label: "Research Reports", icon: "🔬" },
  { id: "alerts", label: "Smart Alerts", icon: "🚨" },
  { id: "notifications", label: "Notifications", icon: "🔔" },
  { id: "ask", label: "Ask AI", icon: "🤖" },
  { id: "research_library", label: "Research Library", icon: "📚" },
  { id: "evaluation_dashboard", label: "RAG Evaluation", icon: "📊" },
  { id: "profile", label: "Profile", icon: "👤" },
  { id: "settings", label: "Settings", icon: "⚙️" },
];

const EVENT_COLORS = {
  IPO: "#6366f1", REGULATION: "#f59e0b", MARKET_FLOW: "#06b6d4",
  COMMODITY: "#10b981", CORPORATE: "#8b5cf6", OTHER: "#64748b",
  MONETARY_POLICY: "#ef4444", GEOPOLITICAL: "#f97316",
  EARNINGS: "#84cc16", BANKING: "#0ea5e9", TECH: "#a78bfa",
  CRYPTO: "#fbbf24", REAL_ESTATE: "#34d399",
};

const IMPORTANCE_COLOR = (score) => {
  if (score >= 90) return "#ef4444";
  if (score >= 75) return "#f59e0b";
  return "#10b981";
};

const SENTIMENT_COLORS = {
  BULLISH: { text: "#10b981", bg: "#10b98118", border: "#10b98133" },
  BEARISH: { text: "#ef4444", bg: "#ef444418", border: "#ef444433" },
  NEUTRAL: { text: "#94a3b8", bg: "#1e293b", border: "#334155" },
};

const PREDICTION_COLORS = {
  UP: { text: "#10b981", icon: "▲" },
  DOWN: { text: "#ef4444", icon: "▼" },
  NEUTRAL: { text: "#94a3b8", icon: "⬘" },
};

export default function App() {
  const { user, loading: authLoading, logout } = useAuth();
  const [authState, setAuthState] = useState("landing"); // "landing", "login", "register", "forgot"
  
  const [onboarded, setOnboarded] = useState(() => {
    const cachedUser = localStorage.getItem("user");
    if (!cachedUser) return false;
    try {
      const u = JSON.parse(cachedUser);
      return localStorage.getItem(`onboarded_${u.id}`) === "true" || u.preferred_market !== "US";
    } catch (e) {
      return false;
    }
  });

  const [activeSection, setActiveSection] = useState("watchlist");
  const [alerts, setAlerts] = useState([]);
  const [allAlerts, setAllAlerts] = useState([]);
  const [selectedSeverity, setSelectedSeverity] = useState(null);
  const [selectedImportanceMin, setSelectedImportanceMin] = useState(null);
  const [selectedDirection, setSelectedDirection] = useState(null);
  const [selectedSource, setSelectedSource] = useState("all");
  const [selectedSort, setSelectedSort] = useState("latest");
  
  // Bulk alerts selection
  const [selectedAlertIds, setSelectedAlertIds] = useState([]);
  // Right Bloomberg analysis panel
  const [rightPanelContent, setRightPanelContent] = useState(null);
  const [rightPanelLoading, setRightPanelLoading] = useState(false);
  // Daily Brief
  const [dailyBriefContent, setDailyBriefContent] = useState(null);
  const [generatingBrief, setGeneratingBrief] = useState(false);
  // Toast
  const [toastMessage, setToastMessage] = useState(null);
  const [ragMetrics, setRagMetrics] = useState(null);
  const [ragMetricsLoading, setRagMetricsLoading] = useState(false);

  // Notification Filters State
  const [allNotifications, setAllNotifications] = useState([]);
  const [notifSeverity, setNotifSeverity] = useState(null);
  const [notifImportanceMin, setNotifImportanceMin] = useState(null);
  const [notifDirection, setNotifDirection] = useState(null);
  const [notifReadStatus, setNotifReadStatus] = useState("all");
  const [notifSource, setNotifSource] = useState("all");
  const [notifSort, setNotifSort] = useState("latest");
  const [notifDateRange, setNotifDateRange] = useState(null);

  // News Intelligence Filters State
  const [newsSource, setNewsSource] = useState("all");
  const [newsEventType, setNewsEventType] = useState("all");
  const [newsSeverity, setNewsSeverity] = useState(null);
  const [newsImportanceMin, setNewsImportanceMin] = useState(null);
  const [newsSector, setNewsSector] = useState("all");
  const [newsDateRange, setNewsDateRange] = useState(null);
  const [newsSort, setNewsSort] = useState("latest");
  const [newsSentiment, setNewsSentiment] = useState(null);

  // Copilot States
  const [chatSessions, setChatSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [deepResearchEnabled, setDeepResearchEnabled] = useState(false);

  // Company Research Dossier States (Phase D)
  const [activeCompanyResearch, setActiveCompanyResearch] = useState(null);
  const [companyResearchData, setCompanyResearchData] = useState(null);
  const [companyResearchLoading, setCompanyResearchLoading] = useState(false);
  const [companyResearchTab, setCompanyResearchTab] = useState("scorecard");
  const [researchLookupQuery, setResearchLookupQuery] = useState("");

  // Research Library States
  const [researchDocs, setResearchDocs] = useState([]);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadCompany, setUploadCompany] = useState("");
  const [uploadDocType, setUploadDocType] = useState("Report");
  const [uploadLoading, setUploadLoading] = useState(false);
  const [researchSearchQuery, setResearchSearchQuery] = useState("");
  const [researchSearchCompany, setResearchSearchCompany] = useState("all");
  const [researchSearchDocType, setResearchSearchDocType] = useState("all");
  const [researchSearchResults, setResearchSearchResults] = useState([]);
  const [researchSearchLoading, setResearchSearchLoading] = useState(false);
  const [indexingStats, setIndexingStats] = useState(null);
  const [selectedSourceText, setSelectedSourceText] = useState(null);
  const [selectedSourceTitle, setSelectedSourceTitle] = useState(null);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const [summary, setSummary] = useState([]);
  const [trends, setTrends] = useState({});
  const [notifications, setNotifications] = useState([]);
  const [notificationsError, setNotificationsError] = useState(false);
  const [selectedNotificationForSummary, setSelectedNotificationForSummary] = useState(null);
  const [now, setNow] = useState(new Date());


  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(timer);
  }, []);

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [watchlists, setWatchlists] = useState([]);
  const [newKeyword, setNewKeyword] = useState("");
  // Watchlist Intelligence States
  const [watchlistBrief, setWatchlistBrief] = useState(null);
  const [generatingWatchlistBrief, setGeneratingWatchlistBrief] = useState(false);
  const [analyzingCompanyId, setAnalyzingCompanyId] = useState(null);
  const [watchlistSearchQuery, setWatchlistSearchQuery] = useState("");
  const [watchlistSearchResults, setWatchlistSearchResults] = useState([]);
  const [watchlistSearchDropdownOpen, setWatchlistSearchDropdownOpen] = useState(false);
  const [selectedWhyMovingCompany, setSelectedWhyMovingCompany] = useState(null);
  // Market Intelligence Engine States
  const [marketHealth, setMarketHealth] = useState(null);
  const [upcomingEvents, setUpcomingEvents] = useState(null);
  const [sectorsIntel, setSectorsIntel] = useState([]);
  const [oppsRisks, setOppsRisks] = useState(null);
  const [commandBarOpen, setCommandBarOpen] = useState(false);
  const [commandSearchQuery, setCommandSearchQuery] = useState("");
  const [commandResults, setCommandResults] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(true);
  // AI Explain Engine States (Phase L)
  const [explainPanelOpen, setExplainPanelOpen] = useState(false);
  const [explainPanelLoading, setExplainPanelLoading] = useState(false);
  const [explainData, setExplainData] = useState(null);
  const [explainType, setExplainType] = useState("");
  const [explainTargetId, setExplainTargetId] = useState("");
  const [selectionState, setSelectionState] = useState({ text: "", x: 0, y: 0, visible: false });
  const [watchlistBriefTab, setWatchlistBriefTab] = useState("brief"); // "brief" | "story"
  const [marketStoryData, setMarketStoryData] = useState(null);
  const [fetchingStory, setFetchingStory] = useState(false);
  const [summaries, setSummaries] = useState({});
  const [summarizing, setSummarizing] = useState({});

  // Phase M: Portfolio Intelligence States
  const [portfolioData, setPortfolioData] = useState(null);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [portfolioError, setPortfolioError] = useState(null);
  const [portfolioReview, setPortfolioReview] = useState(null);
  const [portfolioReviewLoading, setPortfolioReviewLoading] = useState(false);
  const [portfolioBrief, setPortfolioBrief] = useState(null);
  const [portfolioBriefLoading, setPortfolioBriefLoading] = useState(false);
  const [portfolioActiveTab, setPortfolioActiveTab] = useState("holdings"); // "holdings" | "review" | "risk" | "compare"
  const [holdingTimelineOpen, setHoldingTimelineOpen] = useState(false);
  const [holdingTimelineCo, setHoldingTimelineCo] = useState("");
  const [holdingTimelineData, setHoldingTimelineData] = useState([]);
  const [holdingTimelineLoading, setHoldingTimelineLoading] = useState(false);
  const [portfolioCompareCo1, setPortfolioCompareCo1] = useState("");
  const [portfolioCompareCo2, setPortfolioCompareCo2] = useState("");
  const [portfolioCompareData, setPortfolioCompareData] = useState(null);
  const [portfolioCompareLoading, setPortfolioCompareLoading] = useState(false);
  const [portfolioAddModalOpen, setPortfolioAddModalOpen] = useState(false);
  const [portfolioAddForm, setPortfolioAddForm] = useState({
    company_name: "",
    exchange: "NSE",
    quantity: "",
    average_buy_price: "",
    notes: "",
    tags: []
  });

  // Phase N: AI Research Workspace States
  const [savedWorkspaces, setSavedWorkspaces] = useState([]);
  const [workspaceLoading, setWorkspaceLoading] = useState(false);
  const [currentWorkspace, setCurrentWorkspace] = useState(null); // active canvas data
  const [workspaceQuery, setWorkspaceQuery] = useState("");
  const [workspaceNotes, setWorkspaceNotes] = useState("");
  const [recentCompanies, setRecentCompanies] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("recent_companies") || '["HDFC Bank", "TCS", "Reliance Industries"]');
    } catch (e) {
      return ["HDFC Bank", "TCS", "Reliance Industries"];
    }
  });
  const [workspaceExportLoading, setWorkspaceExportLoading] = useState(false);



  const [selectedPostForSummary, setSelectedPostForSummary] = useState(null);
  const [postSummaryLoading, setPostSummaryLoading] = useState(false);
  const [postSummaryContent, setPostSummaryContent] = useState("");

  const handleFetchAISummary = async (post) => {
    setSelectedPostForSummary(post);
    setPostSummaryLoading(true);
    setPostSummaryContent("");
    try {
      const res = await api.post(`/posts/${post.id}/summarize`);
      setPostSummaryContent(res.data.summary);
    } catch (err) {
      setPostSummaryContent("Failed to generate AI Summary. Please try again.");
    } finally {
      setPostSummaryLoading(false);
    }
  };

  const handleReprocessAllPosts = async () => {
    try {
      await api.post("/admin/reprocess-posts");
      alert("Database reprocessing started in the background. Please wait 10 seconds and reload the page.");
    } catch (err) {
      alert("Failed to start reprocessing: " + err.message);
    }
  };

  // Phase M Portfolio Actions
  const fetchPortfolioData = async (force = false) => {
    setPortfolioLoading(true);
    setPortfolioError(null);
    try {
      const res = await api.get(`/portfolio${force ? "?force=true" : ""}`);
      setPortfolioData(res.data);
    } catch (err) {
      setPortfolioError(err.message || "Failed to load portfolio metrics.");
    } finally {
      setPortfolioLoading(false);
    }
  };

  const fetchPortfolioReview = async (force = false) => {
    setPortfolioReviewLoading(true);
    try {
      const res = await api.get(`/portfolio/review${force ? "?force=true" : ""}`);
      setPortfolioReview(res.data);
    } catch (err) {
      console.error("AI Review error", err);
    } finally {
      setPortfolioReviewLoading(false);
    }
  };

  const fetchPortfolioBrief = async (force = false) => {
    setPortfolioBriefLoading(true);
    try {
      const res = await api.get(`/portfolio/brief${force ? "?force=true" : ""}`);
      setPortfolioBrief(res.data);
    } catch (err) {
      console.error("AI Brief error", err);
    } finally {
      setPortfolioBriefLoading(false);
    }
  };

  const fetchHoldingTimeline = async (companyName) => {
    setHoldingTimelineLoading(true);
    setHoldingTimelineCo(companyName);
    setHoldingTimelineOpen(true);
    try {
      const res = await api.get(`/portfolio/timeline?company_name=${encodeURIComponent(companyName)}`);
      setHoldingTimelineData(res.data);
    } catch (err) {
      console.error("Timeline load error", err);
      setHoldingTimelineData([]);
    } finally {
      setHoldingTimelineLoading(false);
    }
  };

  const fetchPortfolioComparison = async () => {
    if (!portfolioCompareCo1 || !portfolioCompareCo2) {
      showToast("Please select two holdings to compare.");
      return;
    }
    setPortfolioCompareLoading(true);
    try {
      const res = await api.get(`/portfolio/compare?co1=${encodeURIComponent(portfolioCompareCo1)}&co2=${encodeURIComponent(portfolioCompareCo2)}`);
      setPortfolioCompareData(res.data);
    } catch (err) {
      console.error("Comparison load error", err);
      showToast("Failed to compile holdings comparison.");
    } finally {
      setPortfolioCompareLoading(false);
    }
  };

  const handleAddHolding = async (e) => {
    e.preventDefault();
    if (!portfolioAddForm.company_name || !portfolioAddForm.quantity || !portfolioAddForm.average_buy_price) {
      showToast("Please fill in company name, quantity, and buy price.");
      return;
    }
    try {
      await api.post("/portfolio/holding", {
        ...portfolioAddForm,
        quantity: parseFloat(portfolioAddForm.quantity),
        average_buy_price: parseFloat(portfolioAddForm.average_buy_price)
      });
      showToast("Holding added successfully.");
      fetchPortfolioData(true);
      fetchPortfolioReview(true);
      fetchPortfolioBrief(true);
      setPortfolioAddModalOpen(false);
      setPortfolioAddForm({
        company_name: "",
        exchange: "NSE",
        quantity: "",
        average_buy_price: "",
        notes: "",
        tags: []
      });
    } catch (err) {
      showToast("Failed to add holding: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteHolding = async (id) => {
    if (!window.confirm("Are you sure you want to remove this holding?")) return;
    try {
      await api.delete(`/portfolio/holding/${id}`);
      showToast("Holding removed successfully.");
      fetchPortfolioData(true);
      fetchPortfolioReview(true);
      fetchPortfolioBrief(true);
    } catch (err) {
      showToast("Failed to remove holding: " + err.message);
    }
  };

  // Phase N: AI Research Workspace Actions
  const fetchWorkspaces = async () => {
    try {
      const res = await api.get("/research/workspaces");
      setSavedWorkspaces(res.data || []);
    } catch (err) {
      console.error("Error fetching workspaces:", err);
    }
  };

  const handleAnalyzeWorkspace = async (q) => {
    if (!q || !q.trim()) {
      showToast("Please enter a research topic or query.");
      return;
    }
    setWorkspaceLoading(true);
    setWorkspaceQuery(q);
    try {
      const res = await api.post("/research/workspace/analyze", { query: q });
      
      const newWorkspace = {
        title: `Research: ${q}`,
        query: q,
        analysis_json: res.data,
        notes: "",
        is_favorite: false
      };
      
      setCurrentWorkspace(newWorkspace);
      setWorkspaceNotes("");

      // Update recent companies list
      let itemToTrack = res.data.primary_entity || q;
      if (itemToTrack) {
        setRecentCompanies(prev => {
          const filtered = prev.filter(c => c.toLowerCase() !== itemToTrack.toLowerCase());
          const updated = [itemToTrack, ...filtered].slice(0, 10);
          localStorage.setItem("recent_companies", JSON.stringify(updated));
          return updated;
        });
      }
      showToast("Research synthesis compiled successfully.");
    } catch (err) {
      console.error(err);
      showToast("Research compilation failed.");
    } finally {
      setWorkspaceLoading(false);
    }
  };

  const handleSaveWorkspace = async () => {
    if (!currentWorkspace) return;
    try {
      const payload = {
        title: currentWorkspace.title,
        query: currentWorkspace.query,
        analysis_json: currentWorkspace.analysis_json,
        notes: workspaceNotes,
        is_favorite: currentWorkspace.is_favorite
      };

      let savedObj;
      if (currentWorkspace.id) {
        const res = await api.put(`/research/workspace/${currentWorkspace.id}`, payload);
        savedObj = res.data;
      } else {
        const res = await api.post("/research/workspace", payload);
        savedObj = res.data;
      }
      
      setCurrentWorkspace(savedObj);
      showToast("Research workspace saved successfully.");
      fetchWorkspaces();
    } catch (err) {
      console.error(err);
      showToast("Failed to save research workspace.");
    }
  };

  const handleDeleteWorkspace = async (id) => {
    if (!window.confirm("Are you sure you want to delete this research workspace?")) return;
    try {
      await api.delete(`/research/workspace/${id}`);
      showToast("Workspace deleted successfully.");
      if (currentWorkspace?.id === id) {
        setCurrentWorkspace(null);
        setWorkspaceQuery("");
        setWorkspaceNotes("");
      }
      fetchWorkspaces();
    } catch (err) {
      console.error(err);
      showToast("Deletion failed.");
    }
  };

  const handleDuplicateWorkspace = async (id) => {
    try {
      await api.post(`/research/workspace/${id}/duplicate`);
      showToast("Workspace duplicated.");
      fetchWorkspaces();
    } catch (err) {
      console.error(err);
      showToast("Duplication failed.");
    }
  };

  const handleRenameWorkspace = async (id, newTitle) => {
    if (!newTitle || !newTitle.trim()) return;
    try {
      await api.put(`/research/workspace/${id}`, { title: newTitle });
      showToast("Workspace renamed.");
      if (currentWorkspace?.id === id) {
        setCurrentWorkspace(prev => ({ ...prev, title: newTitle }));
      }
      fetchWorkspaces();
    } catch (err) {
      console.error(err);
      showToast("Rename failed.");
    }
  };

  const handleFavoriteWorkspace = async (id, isFavorite) => {
    try {
      await api.put(`/research/workspace/${id}`, { is_favorite: isFavorite });
      showToast(isFavorite ? "Added to favorites" : "Removed from favorites");
      if (currentWorkspace?.id === id) {
        setCurrentWorkspace(prev => ({ ...prev, is_favorite: isFavorite }));
      }
      fetchWorkspaces();
    } catch (err) {
      console.error(err);
      showToast("Failed to update status.");
    }
  };

  const handleExportWorkspace = async () => {
    if (!currentWorkspace) return;
    setWorkspaceExportLoading(true);
    try {
      const payload = {
        title: currentWorkspace.title,
        query: currentWorkspace.query,
        summary: currentWorkspace.analysis_json?.summary,
        key_insights: currentWorkspace.analysis_json?.key_insights,
        risks: currentWorkspace.analysis_json?.risks,
        opportunities: currentWorkspace.analysis_json?.opportunities,
        notes: workspaceNotes,
        sources: currentWorkspace.analysis_json?.sources,
        timeline: currentWorkspace.analysis_json?.timeline
      };

      const res = await api.post("/research/workspace/export", payload);
      const markdown = res.data.markdown;

      const element = document.createElement("a");
      const file = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
      element.href = URL.createObjectURL(file);
      element.download = `${currentWorkspace.title.replace(/\s+/g, "_")}.md`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      showToast("Workspace exported successfully.");
    } catch (err) {
      console.error(err);
      showToast("Export failed.");
    } finally {
      setWorkspaceExportLoading(false);
    }
  };

  // ── AI Modules State ────────────────────────────────────────────────────────
  const [heatmapData, setHeatmapData] = useState([]);
  const [timelineEntities, setTimelineEntities] = useState([]);
  const [selectedTimelineEntity, setSelectedTimelineEntity] = useState("");
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [reportsList, setReportsList] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [reportSearch, setReportSearch] = useState("");
  const [generatingReport, setGeneratingReport] = useState(false);
  const [dailyBriefing, setDailyBriefing] = useState(null);
  const [briefingHistory, setBriefingHistory] = useState([]);
  const [watchlistNews, setWatchlistNews] = useState([]);
  const [generatingBriefing, setGeneratingBriefing] = useState(false);
  const [entitySearchQuery, setEntitySearchQuery] = useState("");
  const [timelineSummary, setTimelineSummary] = useState("");
  const [generatingTimelineSummary, setGeneratingTimelineSummary] = useState(false);

  const fetchHeatmap = () => {
    api.get("/sectors/heatmap").then(r => setHeatmapData(r.data)).catch(() => {});
  };

  const fetchTimelineEntities = () => {
    api.get("/timeline/entities").then(r => {
      setTimelineEntities(r.data);
      if (r.data.length > 0 && !selectedTimelineEntity) {
        setSelectedTimelineEntity(r.data[0].name);
      }
    }).catch(() => {});
  };

  const handleGenerateTimelineSummary = async () => {
    if (!selectedTimelineEntity) return;
    setGeneratingTimelineSummary(true);
    try {
      const res = await api.post(`/api/timeline/${selectedTimelineEntity}/summary`);
      setTimelineSummary(res.data.summary);
    } catch (err) {
      showToast("Failed to generate AI summary");
    } finally {
      setGeneratingTimelineSummary(false);
    }
  };

  const fetchReportsList = () => {
    api.get("/research-reports").then(r => setReportsList(r.data)).catch(() => {});
  };

  const fetchDailyBriefing = () => {
    api.get("/daily-briefing/latest").then(r => setDailyBriefing(r.data)).catch(() => {});
    api.get("/daily-briefing/history").then(r => setBriefingHistory(r.data)).catch(() => {});
  };

  const fetchWatchlistNews = () => {
    api.get("/watchlist/news").then(r => setWatchlistNews(r.data)).catch(() => {});
  };

  // Filter notifications in-memory (Feature 3)
  useEffect(() => {
    const filtered = allNotifications.filter(n => {
      if (notifSeverity === "CRITICAL" && !(n.importance_score >= 90)) return false;
      if (notifImportanceMin === 80 && !(n.importance_score >= 80)) return false;
      if (notifReadStatus === "unread" && n.is_read) return false;
      if (notifReadStatus === "read" && !n.is_read) return false;
      if (notifSource !== "all" && n.source !== notifSource) return false;
      if (notifDateRange) {
        const itemTime = new Date(n.posted_at || n.fetched_at || n.created_at).getTime();
        const diffMs = new Date().getTime() - itemTime;
        if (notifDateRange === "today" && diffMs > 24 * 3600 * 1000) return false;
        if (notifDateRange === "week" && diffMs > 7 * 24 * 3600 * 1000) return false;
        if (notifDateRange === "month" && diffMs > 30 * 24 * 3600 * 1000) return false;
      }
      return true;
    }).sort((a, b) => {
      const timeA = new Date(a.posted_at || a.fetched_at || a.created_at).getTime();
      const timeB = new Date(b.posted_at || b.fetched_at || b.created_at).getTime();
      
      if (notifSort === "oldest") {
        return timeA - timeB;
      } else if (notifSort === "importance") {
        return (b.importance_score || 0) - (a.importance_score || 0);
      } else if (notifSort === "confidence") {
        const confA = a.meta_info?.confidence || 0;
        const confB = b.meta_info?.confidence || 0;
        return confB - confA;
      } else {
        // latest
        return timeB - timeA;
      }
    });
    setNotifications(filtered);
  }, [allNotifications, notifSeverity, notifImportanceMin, notifDirection, notifReadStatus, notifSource, notifSort, notifDateRange]);

  // Handle single alert summarize (Feature 1)
  const handleAlertSummarize = async (alertId) => {
    setRightPanelContent({ type: "single" });
    setRightPanelLoading(true);
    try {
      const res = await api.post(`/alerts/${alertId}/summarize`);
      setRightPanelContent({
        type: "single",
        ...res.data
      });
      showToast("AI Summary Ready");
    } catch (err) {
      setRightPanelContent({
        type: "single",
        error: "Failed to generate AI Summary. Please try again."
      });
    } finally {
      setRightPanelLoading(false);
    }
  };

  // Handle bulk alerts summarize (Feature 2)
  const handleAlertsBulkSummarize = async () => {
    if (selectedAlertIds.length === 0) return;
    setRightPanelContent({ type: "bulk" });
    setRightPanelLoading(true);
    try {
      const res = await api.post("/alerts/summarize-bulk", { alert_ids: selectedAlertIds });
      setRightPanelContent({
        type: "bulk",
        summary: res.data.summary
      });
      showToast("AI Summary Ready");
    } catch (err) {
      setRightPanelContent({
        type: "bulk",
        error: "Failed to generate Bulk AI Summary. Please try again."
      });
    } finally {
      setRightPanelLoading(false);
    }
  };

  // Handle Daily Brief generate (Feature 6)
  const handleGenerateDailyBrief = async () => {
    setGeneratingBrief(true);
    try {
      const res = await api.post("/brief/generate");
      setDailyBriefContent(res.data.brief);
      showToast("AI Daily Brief Ready");
    } catch (err) {
      alert("Failed to generate Daily Brief: " + (err.response?.data?.error || err.message));
    } finally {
      setGeneratingBrief(false);
    }
  };


  const fetchNotifications = () => {
    setNotificationsError(false);
    api.get("/notifications")
      .then(r => {
        setAllNotifications(r.data);
        setNotifications(r.data);
      })
      .catch(() => setNotificationsError(true));
  };


  useEffect(() => {
    api.get("/alerts").then(r => { setAllAlerts(r.data); }).catch(() => { });
    api.get("/market-summary").then(r => setSummary(r.data.summary || [])).catch(() => { });
    api.get("/trends").then(r => setTrends(r.data)).catch(() => { });
    fetchNotifications();
    fetchWatchlists();
    fetchMarketIntelligenceData();
    api.post("/api/watchlist/brief").then(r => setWatchlistBrief(r.data)).catch(() => { });
    fetchChatSessions();
    fetchResearchDocs();
    fetchWorkspaces();

    fetchHeatmap();
    fetchTimelineEntities();
    fetchReportsList();
    fetchDailyBriefing();
    fetchWatchlistNews();
  }, []);

  useEffect(() => {
    // Automatically trigger initial analysis for watchlist items missing cached results
    watchlists.forEach(w => {
      if (!w.analysis_cache && w.id) {
        handleAnalyzeCompany(w.id, false);
      }
    });
  }, [watchlists]);

  useEffect(() => {
    if (selectedTimelineEntity) {
      setTimelineSummary("");
      api.get(`/timeline/${selectedTimelineEntity}`).then(r => setTimelineEvents(r.data)).catch(() => {});
    }
  }, [selectedTimelineEntity]);

  useEffect(() => {
    if (activeSection === "evaluation_dashboard") {
      fetchRAGMetrics();
    }
    if (activeSection === "portfolio") {
      fetchPortfolioData();
      fetchPortfolioReview();
      fetchPortfolioBrief();
    }
    if (activeSection === "workspace") {
      fetchWorkspaces();
    }
  }, [activeSection]);

  useEffect(() => {
    const fetchFilteredAlerts = async () => {
      try {
        const params = {};
        if (selectedSeverity) params.severity = selectedSeverity;
        if (selectedSource && selectedSource !== "all") params.source = selectedSource;
        if (selectedImportanceMin !== null && selectedImportanceMin !== undefined) {
          params.importance_min = selectedImportanceMin;
        }
        if (selectedDirection) params.direction = selectedDirection;
        params.sort = selectedSort;

        const res = await api.get("/alerts", { params });
        setAlerts(res.data);
      } catch (err) {
        console.error("Error fetching filtered alerts", err);
      }
    };
    fetchFilteredAlerts();
  }, [selectedSeverity, selectedSource, selectedImportanceMin, selectedDirection, selectedSort]);


  const fetchResearchDocs = async () => {
    try {
      const res = await api.get("/research/documents");
      setResearchDocs(res.data || []);
    } catch (err) {
      console.error("Error fetching research documents:", err);
    }
  };

  const handleUploadDocument = async (e) => {
    if (e) e.preventDefault();
    if (!uploadFile) {
      showToast("Please select a file to upload.");
      return;
    }
    setUploadLoading(true);
    setIndexingStats(null);
    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("company_name", uploadCompany);
    formData.append("document_type", uploadDocType);

    try {
      const res = await api.post("/research/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      showToast("File uploaded and indexed successfully!");
      setUploadFile(null);
      setUploadCompany("");
      setIndexingStats(res.data?.indexing_stats || null);
      
      const fileInput = document.getElementById("research-file-input");
      if (fileInput) fileInput.value = "";
      
      fetchResearchDocs();
    } catch (err) {
      console.error("Upload failed:", err);
      showToast(err.response?.data?.detail || "Upload and indexing failed.");
    } finally {
      setUploadLoading(false);
    }
  };

  const handleDeleteResearchDoc = async (id) => {
    if (!window.confirm("Are you sure you want to delete this document and all its indexed chunks?")) return;
    try {
      await api.delete(`/research/document/${id}`);
      showToast("Document deleted successfully.");
      fetchResearchDocs();
    } catch (err) {
      console.error("Failed to delete document:", err);
      showToast("Deletion failed.");
    }
  };

  const handleSearchResearchLibrary = async (e) => {
    if (e) e.preventDefault();
    if (!researchSearchQuery.trim()) {
      showToast("Please enter a search query.");
      return;
    }
    setResearchSearchLoading(true);
    try {
      const res = await api.post("/research/search", {
        query: researchSearchQuery,
        company_name: researchSearchCompany === "all" ? null : researchSearchCompany,
        document_type: researchSearchDocType === "all" ? null : researchSearchDocType
      });
      setResearchSearchResults(res.data || []);
    } catch (err) {
      console.error("Research search failed:", err);
      showToast("Search failed.");
    } finally {
      setResearchSearchLoading(false);
    }
  };


  const fetchChatSessions = async () => {
    try {
      const res = await api.get("/chat/sessions");
      setChatSessions(res.data || []);
    } catch (err) {
      console.error("Error fetching chat sessions:", err);
    }
  };

  const fetchCompanyResearch = async (companyName) => {
    if (!companyName) return;
    setCompanyResearchLoading(true);
    setActiveCompanyResearch(companyName);
    setCompanyResearchTab("scorecard");
    try {
      const res = await api.post("/api/research/dossier", { company_name: companyName });
      setCompanyResearchData(res.data);
    } catch (err) {
      console.error("Failed to fetch company research dossier:", err);
      showToast(`Failed to fetch dossier for ${companyName}`);
    } finally {
      setCompanyResearchLoading(false);
    }
  };

  const fetchRAGMetrics = async () => {
    setRagMetricsLoading(true);
    try {
      const res = await api.get("/api/research/metrics/aggregate");
      setRagMetrics(res.data);
    } catch (err) {
      console.error("Failed to fetch aggregated RAG metrics:", err);
      showToast("Failed to fetch RAG metrics dashboard data.");
    } finally {
      setRagMetricsLoading(false);
    }
  };

  const loadChatSession = async (sessionId) => {
    if (!sessionId) return;
    setCopilotLoading(true);
    try {
      const res = await api.get(`/chat/history/${sessionId}`);
      const msgs = res.data.messages || [];
      setChatMessages(msgs);
      setActiveSessionId(sessionId);

      // Auto-detect company from history to set active company research
      let detectedCo = null;
      for (const m of msgs) {
        if (m.role === "user") {
          const textLower = m.content.toLowerCase();
          for (const key of ["tcs", "hdfc", "reliance", "infosys", "nvidia", "tesla", "tata motors", "sbi"]) {
            if (textLower.includes(key)) {
              detectedCo = key;
              break;
            }
          }
        }
        if (detectedCo) break;
      }
      if (detectedCo) {
        const map = {
          tcs: "TCS",
          hdfc: "HDFC Bank",
          reliance: "Reliance Industries",
          infosys: "Infosys",
          nvidia: "Nvidia",
          tesla: "Tesla",
          "tata motors": "Tata Motors",
          sbi: "SBI"
        };
        fetchCompanyResearch(map[detectedCo] || detectedCo);
      } else {
        setActiveCompanyResearch(null);
        setCompanyResearchData(null);
      }
    } catch (err) {
      console.error("Error loading chat session:", err);
      showToast("Failed to load chat history.");
    } finally {
      setCopilotLoading(false);
    }
  };

  const startNewChat = () => {
    setActiveSessionId(null);
    setChatMessages([]);
    setActiveCompanyResearch(null);
    setCompanyResearchData(null);
  };

  const deleteChatSession = async (sessionId, e) => {
    if (e) e.stopPropagation();
    try {
      await api.delete(`/chat/session/${sessionId}`);
      showToast("Conversation deleted");
      fetchChatSessions();
      if (activeSessionId === sessionId) {
        startNewChat();
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
      showToast("Delete failed.");
    }
  };

  const sendCopilotMessage = async (text) => {
    if (!text || !text.trim() || copilotLoading) return;
    
    const userText = text.trim();
    setCopilotLoading(true);
    
    // Add user message to UI immediately
    const tempUserMsg = { id: String(Math.random()), role: "user", content: userText, created_at: new Date().toISOString() };
    setChatMessages(prev => [...prev, tempUserMsg]);
    setQuestion(""); // clear input box

    try {
      const res = await api.post("/chat/message", {
        session_id: activeSessionId,
        question: userText,
        deep_research: deepResearchEnabled
      });

      const { session_id, answer, sources, detected_company, suggested_followups, research_quality_badge, confidence_score } = res.data;
      
      if (!activeSessionId) {
        setActiveSessionId(session_id);
      }

      // Add assistant message to UI
      const tempAsstMsg = {
        id: String(Math.random()),
        role: "assistant",
        content: answer,
        sources: sources || [],
        detected_company: detected_company,
        suggested_followups: suggested_followups || [],
        research_quality_badge: research_quality_badge,
        confidence_score: confidence_score,
        created_at: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, tempAsstMsg]);
      showToast("Response generated");
      fetchChatSessions();

      if (detected_company) {
        fetchCompanyResearch(detected_company);
      }
    } catch (err) {
      console.error("Failed to send message:", err);
      const errorMsg = {
        id: String(Math.random()),
        role: "assistant",
        content: "Error: Failed to fetch response from MarketBeacon Copilot. Please check your backend connection.",
        created_at: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMsg]);
    } finally {
      setCopilotLoading(false);
    }
  };

  const handleAddCompanyToWatchlist = async (companyName) => {
    if (!companyName) return;
    try {
      await api.post("/watchlist/add", { keyword: companyName });
      api.get("/watchlists").then(r => setWatchlists(r.data));
      fetchWatchlistNews();
      showToast(`${companyName} added to Watchlist!`);
    } catch (err) {
      showToast("Failed to add to watchlist.");
    }
  };

  const handleRegenerateCopilot = () => {
    const userMsgs = chatMessages.filter(m => m.role === "user");
    if (userMsgs.length === 0) return;
    const lastUserText = userMsgs[userMsgs.length - 1].content;
    
    setChatMessages(prev => {
      const copy = [...prev];
      if (copy.length > 0 && copy[copy.length - 1].role === "assistant") {
        copy.pop();
      }
      return copy;
    });

    sendCopilotMessage(lastUserText);
  };

  const fetchMarketIntelligenceData = async () => {
    try {
      const [healthRes, eventsRes, oppsRisksRes, sectorsRes] = await Promise.all([
        api.get("/api/market-intelligence/health"),
        api.get("/api/market-intelligence/events"),
        api.get("/api/market-intelligence/opportunities-risks"),
        api.get("/api/market-intelligence/sectors")
      ]);
      setMarketHealth(healthRes.data);
      setUpcomingEvents(eventsRes.data);
      setOppsRisks(oppsRisksRes.data);
      setSectorsIntel(sectorsRes.data);
    } catch (err) {
      console.error("Failed to load Market Intelligence metrics:", err);
    }
  };

  const handleFetchExplanation = async (itemType, itemIdOrName, highlightedText = null) => {
    setExplainType(itemType);
    setExplainTargetId(itemIdOrName);
    setExplainPanelOpen(true);
    setExplainPanelLoading(true);
    setExplainData(null);
    try {
      const res = await api.post("/api/explain", {
        item_type: itemType,
        item_id: itemIdOrName,
        text: highlightedText
      });
      setExplainData(res.data);
    } catch (err) {
      console.error(err);
      setExplainData({
        error: "Failed to generate AI explanation. Please try again."
      });
    } finally {
      setExplainPanelLoading(false);
    }
  };

  const fetchMarketStory = async (force = false) => {
    setFetchingStory(true);
    try {
      const res = await api.get("/api/market-intelligence/story");
      setMarketStoryData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setFetchingStory(false);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setCommandBarOpen(prev => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    const handleMouseUp = (e) => {
      const selection = window.getSelection();
      const text = selection?.toString().trim();
      if (text && text.length > 8 && text.length < 500) {
        try {
          const range = selection.getRangeAt(0);
          const rect = range.getBoundingClientRect();
          setSelectionState({
            text: text,
            x: rect.left + window.scrollX,
            y: rect.top + window.scrollY - 38,
            visible: true
          });
        } catch (err) {}
      } else {
        if (e.target.id !== "floating-explain-btn") {
          setSelectionState(prev => ({ ...prev, visible: false }));
        }
      }
    };
    document.addEventListener("mouseup", handleMouseUp);
    return () => document.removeEventListener("mouseup", handleMouseUp);
  }, []);

  const fetchWatchlists = async () => {
    try {
      const res = await api.get("/api/watchlist");
      setWatchlists(res.data);
    } catch (err) {
      showToast("Failed to fetch watchlist");
    }
  };

  const addWatchlist = async () => {
    const kw = newKeyword.trim();
    if (!kw) return;
    try {
      await api.post("/api/watchlist", { keyword: kw });
      fetchWatchlists();
      setNewKeyword("");
      showToast(`${kw} added to watchlist`);
    } catch {
      showToast("Failed to add company");
    }
  };

  const deleteWatchlist = async (id) => {
    try {
      await api.delete(`/api/watchlist/${id}`);
      fetchWatchlists();
      showToast("Removed from watchlist");
    } catch {
      showToast("Failed to remove item");
    }
  };

  const handleGenerateWatchlistBrief = async () => {
    setGeneratingWatchlistBrief(true);
    try {
      const res = await api.post("/api/watchlist/brief");
      setWatchlistBrief(res.data);
      showToast("AI watchlist brief updated!");
    } catch (err) {
      showToast("Failed to generate brief");
    } finally {
      setGeneratingWatchlistBrief(false);
    }
  };

  const handleAnalyzeCompany = async (watchlistId, force = false) => {
    setAnalyzingCompanyId(watchlistId);
    try {
      await api.post("/api/watchlist/analyze", { watchlist_id: watchlistId, force });
      showToast(`${force ? "Regenerated" : "Loaded"} AI analysis`);
      fetchWatchlists();
    } catch (err) {
      showToast("Analysis failed");
    } finally {
      setAnalyzingCompanyId(null);
    }
  };

  const handleUpdateWatchlistItem = async (item, updates) => {
    try {
      await api.post("/api/watchlist", {
        keyword: item.keyword,
        company_name: item.company_name,
        exchange: item.exchange,
        favorite: updates.favorite !== undefined ? updates.favorite : item.favorite,
        priority: updates.priority !== undefined ? updates.priority : item.priority,
        notes: updates.notes !== undefined ? updates.notes : item.notes
      });
      fetchWatchlists();
      showToast("Updated watchlist settings");
    } catch (err) {
      showToast("Failed to update settings");
    }
  };

  const handleOpenDossier = (companyName) => {
    setActiveSection("ask");
    fetchCompanyResearch(companyName);
  };

  const markAsRead = async (id, currentStatus) => {
    if (currentStatus || !id) return;
    try {
      await api.patch(`/notifications/${id}/read`);
      setNotifications(notifications.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch { }
  };

  const summarizeNotification = async (id) => {
    if (!id) return;
    
    const notif = notifications.find(n => n.id === id);
    if (!notif) return;
    
    // If already cached in state, show immediately
    if (notif.summary) {
      setSelectedNotificationForSummary({
        ...notif,
        loading: false,
        summary: notif.summary,
        error: null
      });
      return;
    }
    
    // Open modal with loading state
    setSelectedNotificationForSummary({
      ...notif,
      loading: true,
      summary: null,
      error: null
    });
    
    try {
      const res = await api.post(`/notifications/${id}/summarize`);
      const summaryText = res.data.summary;
      
      setSelectedNotificationForSummary(prev => {
        if (prev && prev.id === id) {
          return {
            ...prev,
            loading: false,
            summary: summaryText,
            error: null
          };
        }
        return prev;
      });
      
      // Save locally to cache in state
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, summary: summaryText } : n));
    } catch (err) {
      const errMsg = err.response?.data?.detail || "Unable to generate summary. Please try again.";
      setSelectedNotificationForSummary(prev => {
        if (prev && prev.id === id) {
          return {
            ...prev,
            loading: false,
            summary: null,
            error: errMsg
          };
        }
        return prev;
      });
    }
  };


  const triggerReportGeneration = async () => {
    if (!reportSearch.trim()) return;
    setGeneratingReport(true);
    try {
      const res = await api.post("/research-reports/generate", { entity: reportSearch });
      setSelectedReport(res.data.report);
      fetchReportsList();
    } catch (err) {
      alert("Failed to generate research report. Check rate limits / server.");
    } finally {
      setGeneratingReport(false);
    }
  };

  const triggerBriefingRegenerate = async () => {
    setGeneratingBriefing(true);
    try {
      const res = await api.post("/daily-briefing/generate");
      setDailyBriefing(res.data);
      fetchDailyBriefing();
    } catch (err) {
      alert("Failed to generate briefing. Market intelligence temporarily unavailable.");
    } finally {
      setGeneratingBriefing(false);
    }
  };

  const selectPastReport = async (id) => {
    try {
      const res = await api.get(`/research-reports/${id}`);
      setSelectedReport(res.data);
    } catch (err) {}
  };

  const handleEntityClick = (name) => {
    setSelectedTimelineEntity(name);
    setActiveSection("timeline");
  };

  const filteredNews = summary.filter(item => {
    if (newsSource !== "all" && item.source_id !== newsSource) return false;
    if (newsEventType !== "all" && item.event_type !== newsEventType) return false;
    if (newsSeverity && item.impact_level !== newsSeverity) return false;
    if (newsImportanceMin !== null && !(item.importance_score >= newsImportanceMin)) return false;
    if (newsSector !== "all") {
       const sectorUpper = newsSector.toUpperCase();
       const inTitle = (item.title || "").toUpperCase().includes(sectorUpper);
       const inReasoning = (item.reasoning || "").toUpperCase().includes(sectorUpper);
       const inEventType = (item.event_type || "").toUpperCase().includes(sectorUpper);
       const inEntities = item.entities ? JSON.stringify(item.entities).toUpperCase().includes(sectorUpper) : false;
       if (!inTitle && !inReasoning && !inEventType && !inEntities) return false;
    }
    if (newsDateRange) {
      const postTime = new Date(item.posted_at || item.fetched_at).getTime();
      const diffMs = new Date().getTime() - postTime;
      if (newsDateRange === "today" && diffMs > 24 * 3600 * 1000) return false;
      if (newsDateRange === "week" && diffMs > 7 * 24 * 3600 * 1000) return false;
      if (newsDateRange === "month" && diffMs > 30 * 24 * 3600 * 1000) return false;
    }
    if (newsSentiment && (item.sentiment || "").toUpperCase() !== newsSentiment.toUpperCase()) return false;
    return true;
  }).sort((a, b) => {
    if (newsSort === "oldest") {
      const timeA = new Date(a.posted_at || a.fetched_at).getTime();
      const timeB = new Date(b.posted_at || b.fetched_at).getTime();
      return timeA - timeB;
    } else if (newsSort === "importance") {
      return (b.importance_score || 0) - (a.importance_score || 0);
    } else if (newsSort === "confidence") {
      return (b.confidence || 0) - (a.confidence || 0);
    } else {
      const timeA = new Date(a.posted_at || a.fetched_at).getTime();
      const timeB = new Date(b.posted_at || b.fetched_at).getTime();
      return timeB - timeA;
    }
  });

  const newsEventTypes = [...new Set(summary.map(item => item.event_type).filter(Boolean))];
  const newsSectors = ["Banking", "NBFC", "Telecom", "Metals", "Real Estate", "Tech", "Crypto"];

  const alertSources = [...new Set(allAlerts.map(a => a.source_id).filter(Boolean))];
  const unreadCount = notifications.filter(n => !n.is_read).length;


  const s = styles;

  if (authLoading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "100vh", background: "#060a13" }}>
        <span style={s.spinnerBig} />
        <span style={{ fontSize: 13, color: "#94a3b8", marginTop: 16, fontWeight: 500 }}>Initializing MarketBeacon AI...</span>
      </div>
    );
  }

  if (!user) {
    if (authState === "landing") {
      return <LandingPage onGetStarted={() => setAuthState("register")} onLogin={() => setAuthState("login")} />;
    }
    if (authState === "login") {
      return (
        <Login 
          onRegisterLink={() => setAuthState("register")} 
          onForgotPassword={() => setAuthState("forgot")} 
          onSuccess={() => { 
            setAuthState("landing"); 
            const cachedUser = localStorage.getItem("user");
            if (cachedUser) {
              const u = JSON.parse(cachedUser);
              setOnboarded(localStorage.getItem(`onboarded_${u.id}`) === "true" || u.preferred_market !== "US");
            }
          }} 
        />
      );
    }
    if (authState === "register") {
      return (
        <Register 
          onLoginLink={() => setAuthState("login")} 
          onSuccess={() => { 
            setAuthState("landing"); 
            setOnboarded(false); 
          }} 
        />
      );
    }
    if (authState === "forgot") {
      return <ForgotPassword onBackToLogin={() => setAuthState("login")} />;
    }
  }

  if (!onboarded) {
    return (
      <Onboarding 
        onComplete={() => {
          localStorage.setItem(`onboarded_${user.id}`, "true");
          setOnboarded(true);
        }} 
      />
    );
  }

  return (
    <div style={s.root}>
      {/* Sidebar */}
      <aside style={{ ...s.sidebar, width: sidebarOpen ? 240 : 64, transition: "width 0.25s ease" }}>
        <div style={s.logoRow} onClick={() => setSidebarOpen(v => !v)}>
          <div style={s.logoIcon}>MB</div>
          {sidebarOpen && <span style={s.logoText}>MarketBeacon AI</span>}
        </div>
        <nav style={{ flex: 1, paddingTop: 8 }}>
          {NAV_ITEMS.map(item => (
            <button key={item.id} onClick={() => setActiveSection(item.id)} style={{
              ...s.navBtn,
              background: activeSection === item.id ? "#06b6d418" : "transparent",
              borderLeft: activeSection === item.id ? "3px solid #06b6d4" : "3px solid transparent",
              color: activeSection === item.id ? "#06b6d4" : "#94a3b8",
            }}>
              <span style={{ fontSize: 18, minWidth: 24, textAlign: "center" }}>{item.icon}</span>
              {sidebarOpen && (
                <span style={{ marginLeft: 12, fontSize: 13, fontWeight: 500, whiteSpace: "nowrap" }}>
                  {item.label}
                  {item.id === "notifications" && unreadCount > 0 && (
                    <span style={s.badge}>{unreadCount}</span>
                  )}
                </span>
              )}
            </button>
          ))}
        </nav>
        <div style={{ ...s.sidebarFooter, display: "flex", flexDirection: "column", gap: 10 }}>
          {user && (
            <button
              onClick={() => logout()}
              style={{
                width: "100%",
                background: "rgba(239, 68, 68, 0.1)",
                color: "#ef4444",
                border: "1px solid rgba(239, 68, 68, 0.2)",
                borderRadius: 8,
                padding: "8px 12px",
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
                textAlign: "center",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 6,
                boxSizing: "border-box"
              }}
            >
              🚪 {sidebarOpen ? "Sign Out" : ""}
            </button>
          )}
          {sidebarOpen && <span style={{ fontSize: 10, color: "#475569" }}>Intelligence Platform v3.0</span>}
        </div>
      </aside>

      {/* Main Container */}
      <main style={{ ...s.main, display: "flex", flexDirection: "row", position: "relative" }}>
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
          {/* Topbar */}
          <div style={s.topbar}>
            <div>
              <div style={s.pageTitle}>
                {NAV_ITEMS.find(n => n.id === activeSection)?.icon}{" "}
                {NAV_ITEMS.find(n => n.id === activeSection)?.label}
              </div>
              <div style={{ ...s.pageSubtitle, color: "#06b6d4", fontWeight: 600 }}>
                {(() => {
                  const hr = new Date().getHours();
                  let greeting = "Good Morning";
                  if (hr >= 12 && hr < 17) greeting = "Good Afternoon";
                  else if (hr >= 17) greeting = "Good Evening";
                  return `${greeting}, ${user?.full_name || "Sujan"} | `;
                })()}
                <span style={{ color: "#475569", fontWeight: 500 }}>
                  {new Date().toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
                </span>
              </div>
            </div>
            <div style={s.topbarRight}>
              <button
                onClick={handleGenerateDailyBrief}
                disabled={generatingBrief}
                style={{
                  ...s.btnPrimary,
                  padding: "6px 12px",
                  fontSize: 11,
                  background: "linear-gradient(135deg, #a855f7, #6366f1)",
                  marginRight: 12
                }}
              >
                {generatingBrief ? "Compiling Brief..." : "📰 AI Market Brief"}
              </button>
              <button
                onClick={handleReprocessAllPosts}
                style={{
                  ...s.btnPrimary,
                  padding: "6px 12px",
                  fontSize: 11,
                  background: "linear-gradient(135deg, #10b981, #059669)",
                  marginRight: 12
                }}
              >
                🔄 Reprocess News
              </button>
              <div style={s.statusDot} />
              <span style={{ fontSize: 12, color: "#10b981", fontWeight: 600 }}>Active Local Engine</span>
            </div>
          </div>


        {/* Content Body */}
        <div style={s.content}>

          {/* NEWS INTELLIGENCE */}
          {activeSection === "summary" && (
            <div>
              <div style={s.statsRow}>
                <StatCard 
                  label="Total Articles" 
                  value={summary.length} 
                  color="#06b6d4" 
                  clickable={true}
                  active={!newsSentiment}
                  onClick={() => setNewsSentiment(null)}
                />
                <StatCard 
                  label="Bullish Sentiment" 
                  value={summary.filter(i => (i.sentiment || "").toUpperCase() === "BULLISH").length} 
                  color="#10b981" 
                  clickable={true}
                  active={newsSentiment === "BULLISH"}
                  onClick={() => setNewsSentiment(newsSentiment === "BULLISH" ? null : "BULLISH")}
                />
                <StatCard 
                  label="Bearish Sentiment" 
                  value={summary.filter(i => (i.sentiment || "").toUpperCase() === "BEARISH").length} 
                  color="#ef4444" 
                  clickable={true}
                  active={newsSentiment === "BEARISH"}
                  onClick={() => setNewsSentiment(newsSentiment === "BEARISH" ? null : "BEARISH")}
                />
                <StatCard 
                  label="Neutral Sentiment" 
                  value={summary.filter(i => {
                    const sentStr = (i.sentiment || "").toUpperCase();
                    return sentStr === "NEUTRAL" || sentStr === "";
                  }).length} 
                  color="#94a3b8" 
                  clickable={true}
                  active={newsSentiment === "NEUTRAL"}
                  onClick={() => setNewsSentiment(newsSentiment === "NEUTRAL" ? null : "NEUTRAL")}
                />
              </div>

              {/* Shared Filter Bar */}
              <FilterBar 
                sources={[...new Set(summary.map(item => item.source_id).filter(Boolean))]}
                selectedSource={newsSource}
                onSourceChange={setNewsSource}
                eventTypes={newsEventTypes}
                selectedEventType={newsEventType}
                onEventTypeChange={setNewsEventType}
                sectors={newsSectors}
                selectedSector={newsSector}
                onSectorChange={setNewsSector}
                severity={newsSeverity}
                selectedSeverity={newsSeverity}
                onSeverityChange={setNewsSeverity}
                importanceMin={newsImportanceMin}
                selectedImportanceMin={newsImportanceMin}
                onImportanceMinChange={setNewsImportanceMin}
                dateRange={newsDateRange}
                selectedDateRange={newsDateRange}
                onDateRangeChange={setNewsDateRange}
                sentiment={newsSentiment}
                selectedSentiment={newsSentiment}
                onSentimentChange={setNewsSentiment}
              />

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <ActiveFilterChips 
                  filters={{
                    source: newsSource,
                    eventType: newsEventType,
                    sector: newsSector,
                    severity: newsSeverity,
                    importanceMin: newsImportanceMin,
                    dateRange: newsDateRange,
                    sentiment: newsSentiment,
                    sort: newsSort
                  }}
                  onRemove={(key) => {
                    if (key === "source") setNewsSource("all");
                    if (key === "eventType") setNewsEventType("all");
                    if (key === "sector") setNewsSector("all");
                    if (key === "severity") setNewsSeverity(null);
                    if (key === "importanceMin") setNewsImportanceMin(null);
                    if (key === "dateRange") setNewsDateRange(null);
                    if (key === "sentiment") setNewsSentiment(null);
                    if (key === "sort") setNewsSort("latest");
                  }}
                />
                <SortDropdown value={newsSort} onChange={setNewsSort} />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {filteredNews.length === 0 ? (
                  <div style={{ textAlign: "center", padding: "60px 20px", color: "#475569", fontSize: 14, border: "1px dashed #1e293b", borderRadius: 12, background: "#0e1626" }}>
                    <div style={{ fontSize: 32, marginBottom: 12 }}>📭</div>
                    <div style={{ color: "#cbd5e1", fontWeight: 600, marginBottom: 6 }}>No articles match the selected filters.</div>
                    <div style={{ color: "#64748b", fontSize: 12, marginBottom: 16 }}>Try clearing filters or selecting another source.</div>
                    <button 
                      onClick={() => {
                        setNewsSource("all");
                        setNewsEventType("all");
                        setNewsSector("all");
                        setNewsSeverity(null);
                        setNewsImportanceMin(null);
                        setNewsDateRange(null);
                        setNewsSort("latest");
                      }} 
                      style={{ ...s.btnPrimary, margin: "0 auto" }}
                    >
                      Clear Filters
                    </button>
                  </div>
                ) : filteredNews.map((item, i) => {
                  const itemSentiment = (item?.sentiment || "").toUpperCase() || "NEUTRAL";
                  const sent = SENTIMENT_COLORS[itemSentiment] || SENTIMENT_COLORS.NEUTRAL;
                  const pred = PREDICTION_COLORS[item?.predicted_direction] || PREDICTION_COLORS.NEUTRAL;

                  return (
                    <div key={i} style={s.summaryCard}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 6 }}>
                            <SourceBadge source_id={item?.source_id} />
                            <EventBadge type={item?.event_type} />
                            <span style={{
                              fontSize: 10,
                              fontWeight: 700,
                              padding: "2px 8px",
                              borderRadius: 4,
                              color: sent.text,
                              backgroundColor: sent.bg,
                              border: `1px solid ${sent.border}`
                            }}>
                              {itemSentiment}
                              {item?.sentiment_confidence !== undefined && item?.sentiment_confidence !== null && (
                                ` (${Math.round(item.sentiment_confidence * 100)}%)`
                              )}
                            </span>
                            {item?.predicted_direction && (
                              <span style={{
                                fontSize: 10,
                                fontWeight: 700,
                                padding: "2px 8px",
                                borderRadius: 4,
                                color: pred.text,
                                backgroundColor: `${pred.text}10`,
                                border: `1px solid ${pred.text}33`
                              }}>
                                {pred.icon} Predict: {item?.predicted_direction} ({parseInt((item?.prediction_confidence || 0.5) * 100)}%)
                              </span>
                            )}
                          </div>
                          
                          <div style={s.summaryTitle}>
                            {item?.post_url ? (
                              <a href={item.post_url} target="_blank" rel="noreferrer" style={{ color: "#f1f5f9", textDecoration: "none" }}
                                 onMouseEnter={e => e.target.style.color = "#06b6d4"}
                                 onMouseLeave={e => e.target.style.color = "#f1f5f9"}>
                                {item?.title}
                              </a>
                            ) : item?.title}
                          </div>

                          {/* Published timestamp */}
                          {(() => {
                            const postTime = item?.posted_at || item?.fetched_at;
                            const { dateTimeStr, ageStr } = formatTimestamp(postTime);
                            return (
                              <div style={s.summaryMeta}>
                                <span><strong>Published:</strong> {dateTimeStr}</span>
                                <span> • </span>
                                <span><strong>Age:</strong> {ageStr}</span>
                              </div>
                            );
                          })()}

                          {item?.reasoning && (
                            <div style={s.reasoningBlock}>
                              <strong style={{ color: "#06b6d4" }}>Insight:</strong> {item?.reasoning}
                            </div>
                          )}

                          {item?.prediction_reasoning && (
                            <div style={{ ...s.reasoningBlock, borderLeftColor: "#a855f7", marginTop: 4 }}>
                              <strong style={{ color: "#a855f7" }}>Prediction:</strong> {item?.prediction_reasoning}
                            </div>
                          )}

                          {item?.entities && Object.values(item.entities).some(arr => arr && arr.length > 0) && (
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 10 }}>
                              <span style={{ fontSize: 10, color: "#475569", alignSelf: "center", fontWeight: "bold" }}>TAGS:</span>
                              {Object.entries(item.entities).flatMap(([cat, names]) => 
                                (names || []).map(name => (
                                  <span 
                                    key={`${cat}-${name}`} 
                                    onClick={() => handleEntityClick(name)}
                                    style={s.clickableEntityTag}
                                  >
                                    {name}
                                  </span>
                                ))
                              )}
                            </div>
                          )}

                          {/* AI Summary and Explain Buttons */}
                          <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
                            <button
                              onClick={() => handleFetchAISummary(item)}
                              style={s.btnSummaryAI}
                            >
                              ✨ AI Summary
                            </button>
                            <button
                              onClick={() => handleFetchExplanation("news", item.id)}
                              style={{ ...s.btnSummaryAI, background: "linear-gradient(135deg, #06b6d4, #3b82f6)" }}
                            >
                              ✨ Explain
                            </button>
                          </div>
                        </div>

                        <div style={{ textAlign: "right", flexShrink: 0 }}>
                          <div style={{ fontSize: 26, fontWeight: 800, color: IMPORTANCE_COLOR(item?.importance_score), fontFamily: "monospace", lineHeight: 1 }}>
                            {item?.importance_score}
                          </div>
                          <div style={{ fontSize: 9, color: "#475569", marginTop: 2, fontWeight: 700, letterSpacing: "0.05em" }}>IMPORTANCE</div>
                        </div>
                      </div>

                      {/* Debug Visibility Panel */}
                      {(() => {
                        const postTime = item?.posted_at || item?.fetched_at;
                        const { dateTimeStr, ageStr, diffMs, parsedTime } = formatTimestamp(postTime);
                        return (
                          <div style={{
                            marginTop: 12,
                            padding: "8px 12px",
                            background: "#121b2e",
                            border: "1px dashed #334155",
                            borderRadius: 8,
                            fontSize: 10,
                            fontFamily: "monospace",
                            color: "#94a3b8"
                          }}>
                            <div style={{ fontWeight: 800, color: "#cbd5e1", marginBottom: 4, letterSpacing: "0.05em" }}>[DEBUG PANEL]</div>
                            <div style={{ display: "grid", gridTemplateColumns: "150px 1fr", gap: "4px 12px" }}>
                              <div>Article Title:</div><div style={{ color: "#e2e8f0" }}>{item?.title}</div>
                              <div>Raw Sentiment:</div><div style={{ color: "#e2e8f0" }}>{item?.sentiment || "None"}</div>
                              <div>Normalized Sentiment:</div><div style={{ color: "#e2e8f0" }}>{(item?.sentiment || "").toUpperCase() || "None"}</div>
                              <div>Event Type:</div><div style={{ color: "#e2e8f0" }}>{item?.event_type || "None"}</div>
                              <div>Importance Score:</div><div style={{ color: "#e2e8f0" }}>{item?.importance_score || "None"}</div>
                              <div>Published Time (UTC):</div><div style={{ color: "#e2e8f0" }}>{postTime || "None"}</div>
                              <div>Current Time (Local):</div><div style={{ color: "#e2e8f0" }}>{new Date().toString()}</div>
                              <div>Published Time (Local):</div><div style={{ color: "#e2e8f0" }}>{parsedTime ? parsedTime.toString() : "None"}</div>
                              <div>Calculated Difference:</div><div style={{ color: "#e2e8f0" }}>{ageStr} ({Math.round(diffMs / 1000 / 60)} min difference)</div>
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* PERSONALIZED WATCHLISTS */}
          {activeSection === "watchlist" && (
            <div style={{ animation: "fadeIn 0.3s ease-out" }}>
              {/* Header Greeting */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                <div>
                  <h2 style={{ fontSize: 24, fontWeight: 800, color: "#f8fafc", margin: 0, letterSpacing: "-0.02em" }}>
                    Good Morning, {user?.full_name || user?.email?.split('@')[0] || "User"}
                  </h2>
                  <p style={{ fontSize: 13, color: "#64748b", margin: "4px 0 0 0" }}>
                    Today's Watchlist Intelligence • {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' })}
                  </p>
                </div>
                
                {/* Global Smart Search autocomplete */}
                <div style={{ position: "relative", width: 320 }}>
                  <div style={{ display: "flex", background: "#0e1626", border: "1px solid #121b2e", borderRadius: 8, padding: "2px 8px", alignItems: "center" }}>
                    <span style={{ marginRight: 8, color: "#475569" }}>🔍</span>
                    <input
                      id="watchlist-search-input"
                      type="text"
                      value={watchlistSearchQuery}
                      onChange={async (e) => {
                        const val = e.target.value;
                        setWatchlistSearchQuery(val);
                        if (val.trim().length > 1) {
                          try {
                            const res = await api.get("/api/watchlist/search", { params: { q: val } });
                            setWatchlistSearchResults(res.data);
                            setWatchlistSearchDropdownOpen(true);
                          } catch (err) {
                            console.error(err);
                          }
                        } else {
                          setWatchlistSearchResults([]);
                          setWatchlistSearchDropdownOpen(false);
                        }
                      }}
                      onFocus={() => {
                        if (watchlistSearchResults.length > 0) setWatchlistSearchDropdownOpen(true);
                      }}
                      placeholder="Search and add companies... (Ctrl+K for commands)"
                      style={{ background: "none", border: "none", color: "#f1f5f9", outline: "none", width: "100%", padding: "8px 0", fontSize: 13 }}
                    />
                    {watchlistSearchQuery && (
                      <button onClick={() => { setWatchlistSearchQuery(""); setWatchlistSearchResults([]); setWatchlistSearchDropdownOpen(false); }} style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 12 }}>
                        ✕
                      </button>
                    )}
                  </div>
                  
                  {/* Autocomplete Dropdown */}
                  {watchlistSearchDropdownOpen && watchlistSearchResults.length > 0 && (
                    <div style={{ position: "absolute", top: "100%", left: 0, right: 0, background: "#0a0f1d", border: "1px solid #121b2e", borderRadius: 8, marginTop: 4, zIndex: 1000, boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)", overflow: "hidden" }}>
                      {watchlistSearchResults.map((co, idx) => (
                        <div
                          key={idx}
                          onClick={async () => {
                            try {
                              await api.post("/api/watchlist", { keyword: co.name, company_name: co.name, exchange: co.exchange });
                              showToast(`${co.name} added to watchlist!`);
                              setWatchlistSearchQuery("");
                              setWatchlistSearchResults([]);
                              setWatchlistSearchDropdownOpen(false);
                              fetchWatchlists();
                            } catch (err) {
                              showToast("Failed to add company");
                            }
                          }}
                          style={{ padding: "10px 14px", borderBottom: idx < watchlistSearchResults.length - 1 ? "1px solid #121b2e" : "none", cursor: "pointer", fontSize: 13, color: "#cbd5e1", transition: "background 0.15s" }}
                          onMouseEnter={(e) => e.target.style.background = "#0e1626"}
                          onMouseLeave={(e) => e.target.style.background = "transparent"}
                        >
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <span style={{ fontWeight: 600, color: "#f1f5f9" }}>{co.name}</span>
                            <span style={{ fontSize: 10, color: "#06b6d4", background: "#06b6d418", padding: "2px 6px", borderRadius: 4, fontWeight: "bold" }}>{co.exchange}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* ── ROW 1: MARKET HEALTH & DAILY BRIEF ── */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1.8fr", gap: 20, marginBottom: 24 }}>
                
                {/* FEATURE 1: Market Health Dashboard */}
                <div style={{ ...s.card, background: "linear-gradient(135deg, #0b1528 0%, #060e20 100%)", border: "1px solid #1e3a8a25", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                  <div>
                    <h3 style={{ fontSize: 14, fontWeight: 700, color: "#cbd5e1", margin: "0 0 16px 0", display: "flex", alignItems: "center", gap: 8 }}>
                      📊 Market Health Dashboard
                    </h3>
                    {marketHealth ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                        <div style={{ display: "flex", alignItems: "center", justifyBox: "space-between", justifyContent: "space-between" }}>
                          <div>
                            <span style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", fontWeight: 700 }}>Health Index</span>
                            <div style={{ fontSize: 28, fontWeight: 800, color: "#06b6d4", fontFamily: "monospace", marginTop: 2 }}>
                              {marketHealth.market_health_score}<span style={{ fontSize: 13, color: "#475569" }}>/100</span>
                            </div>
                          </div>
                          <div style={{ textAlign: "right" }}>
                            <span style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", fontWeight: 700 }}>Mood & Risk</span>
                            <div style={{ marginTop: 4, display: "flex", gap: 6, justifyContent: "flex-end" }}>
                              <span style={{ fontSize: 10, fontWeight: 800, background: "#10b98115", color: "#10b981", padding: "2px 6px", borderRadius: 4 }}>
                                {marketHealth.market_mood}
                              </span>
                              <span style={{ fontSize: 10, fontWeight: 800, background: "#f59e0b15", color: "#f59e0b", padding: "2px 6px", borderRadius: 4 }}>
                                Risk: {marketHealth.risk_level}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Sector Sentiment indicator summary */}
                        <div style={{ background: "#05081199", border: "1px solid #121b2e", borderRadius: 8, padding: "10px 12px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px 14px", fontSize: 11 }}>
                          <div>
                            <span style={{ color: "#64748b" }}>🔥 Strongest Sector:</span>
                            <div style={{ fontWeight: 700, color: "#10b981", marginTop: 2 }}>{marketHealth.strongest_sector}</div>
                          </div>
                          <div>
                            <span style={{ color: "#64748b" }}>❄️ Weakest Sector:</span>
                            <div style={{ fontWeight: 700, color: "#ef4444", marginTop: 2 }}>{marketHealth.weakest_sector}</div>
                          </div>
                          <div>
                            <span style={{ color: "#64748b" }}>⚡ Most Active Sector:</span>
                            <div style={{ fontWeight: 700, color: "#cbd5e1", marginTop: 2 }}>{marketHealth.most_active_sector}</div>
                          </div>
                        </div>

                        {/* Micro events highlight */}
                        <div style={{ borderTop: "1px solid #121b2e", paddingTop: 10, fontSize: 11 }}>
                          <span style={{ color: "#64748b", display: "block", marginBottom: 2 }}>Highest Impact Catalyst Today:</span>
                          <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{marketHealth.highest_impact_event}</span>
                          <span style={{ color: "#06b6d4", fontSize: 10, display: "block", marginTop: 4 }}>⏰ Next event: {marketHealth.next_event}</span>
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                        <div style={{ height: 28, width: 80, background: "#1e293b", borderRadius: 4, animation: "pulse 1.5s infinite" }}></div>
                        <div style={{ height: 60, background: "#1e293b", borderRadius: 8, animation: "pulse 1.5s infinite" }}></div>
                      </div>
                    )}
                  </div>
                  <span style={{ fontSize: 9, color: "#475569", marginTop: 12, textAlign: "right" }}>Health cache refreshed every 15 min</span>
                </div>

                {/* FEATURE 10 & Feature 10 (Daily Market Story): Upgraded Daily AI Brief & Market Story */}
                <div style={{ ...s.card, background: "linear-gradient(135deg, #091220 0%, #060a13 100%)", border: "1px solid #1e293b", position: "relative" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #121b2e", paddingBottom: 12, marginBottom: 12 }}>
                    <div style={{ display: "flex", gap: 14 }}>
                      <button
                        onClick={() => setWatchlistBriefTab("brief")}
                        style={{
                          background: "none", border: "none", fontSize: 13, fontWeight: 800,
                          color: watchlistBriefTab === "brief" ? "#06b6d4" : "#64748b",
                          borderBottom: watchlistBriefTab === "brief" ? "2px solid #06b6d4" : "2px solid transparent",
                          paddingBottom: 4, cursor: "pointer"
                        }}
                      >
                        🌅 Portfolio Brief
                      </button>
                      <button
                        onClick={() => {
                          setWatchlistBriefTab("story");
                          if (!marketStoryData) {
                            fetchMarketStory();
                          }
                        }}
                        style={{
                          background: "none", border: "none", fontSize: 13, fontWeight: 800,
                          color: watchlistBriefTab === "story" ? "#06b6d4" : "#64748b",
                          borderBottom: watchlistBriefTab === "story" ? "2px solid #06b6d4" : "2px solid transparent",
                          paddingBottom: 4, cursor: "pointer"
                        }}
                      >
                        📖 Today's Market Story
                      </button>
                    </div>

                    {watchlistBriefTab === "brief" ? (
                      <button
                        onClick={handleGenerateWatchlistBrief}
                        disabled={generatingWatchlistBrief}
                        style={{
                          background: "linear-gradient(135deg, #06b6d4, #3b82f6)", color: "#fff", border: "none",
                          borderRadius: 6, padding: "5px 12px", fontSize: 11, fontWeight: 700, cursor: "pointer"
                        }}
                      >
                        {generatingWatchlistBrief ? "Compiling..." : "✨ Regenerate Brief"}
                      </button>
                    ) : (
                      <button
                        onClick={() => fetchMarketStory(true)}
                        disabled={fetchingStory}
                        style={{
                          background: "linear-gradient(135deg, #06b6d4, #3b82f6)", color: "#fff", border: "none",
                          borderRadius: 6, padding: "5px 12px", fontSize: 11, fontWeight: 700, cursor: "pointer"
                        }}
                      >
                        {fetchingStory ? "Compiling..." : "🔄 Refresh Story"}
                      </button>
                    )}
                  </div>

                  {watchlistBriefTab === "brief" ? (
                    generatingWatchlistBrief ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                        <div style={{ height: 16, width: "60%", background: "#1e293b", borderRadius: 4, animation: "pulse 1.5s infinite" }}></div>
                        <div style={{ height: 12, width: "95%", background: "#121b2e", borderRadius: 4, animation: "pulse 1.5s infinite" }}></div>
                        <div style={{ height: 12, width: "90%", background: "#121b2e", borderRadius: 4, animation: "pulse 1.5s infinite" }}></div>
                      </div>
                    ) : watchlistBrief ? (
                      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 20 }}>
                        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                          <div style={{ fontSize: 13, color: "#cbd5e1", lineHeight: 1.5 }}>
                            {watchlistBrief.market_summary}
                          </div>
                          <div style={{ display: "flex", gap: 8, fontSize: 11 }}>
                            <span style={{ color: "#64748b" }}>Overall Mood:</span>
                            <strong style={{ color: "#10b981" }}>{watchlistBrief.market_mood}</strong>
                          </div>
                          {/* Suggested actions list */}
                          <div>
                            <span style={{ fontSize: 9, fontWeight: 800, color: "#64748b", textTransform: "uppercase", display: "block", marginBottom: 4 }}>Suggested Actions</span>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                              {watchlistBrief.suggested_actions?.map((act, i) => (
                                <span key={i} style={{ fontSize: 10, color: "#06b6d4", background: "#06b6d412", padding: "2px 6px", borderRadius: 4, border: "1px solid #06b6d425" }}>
                                  {act}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Right panel: changes and risks */}
                        <div style={{ borderLeft: "1px solid #121b2e", paddingLeft: 20, display: "flex", flexDirection: "column", gap: 12 }}>
                          <div>
                            <span style={{ fontSize: 9, fontWeight: 800, color: "#64748b", textTransform: "uppercase", display: "block", marginBottom: 6 }}>Key Watchlist Changes</span>
                            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                              {watchlistBrief.watchlist_changes?.slice(0, 3).map((chg, i) => (
                                <div key={i} style={{ fontSize: 11, color: "#cbd5e1", display: "flex", alignItems: "flex-start", gap: 4 }}>
                                  <span>•</span> <span>{chg}</span>
                                </div>
                              ))}
                            </div>
                          </div>

                          <div style={{ display: "flex", gap: 8, fontSize: 11 }}>
                            <div>
                              <span style={{ fontSize: 9, fontWeight: 800, color: "#10b981", textTransform: "uppercase", display: "block", marginBottom: 2 }}>Opportunities</span>
                              {watchlistBrief.biggest_opportunities?.slice(0, 2).map((op, i) => (
                                <div key={i} style={{ fontSize: 10, color: "#cbd5e1" }}>{op.name}</div>
                              ))}
                            </div>
                            <div>
                              <span style={{ fontSize: 9, fontWeight: 800, color: "#ef4444", textTransform: "uppercase", display: "block", marginBottom: 2 }}>Risks</span>
                              {watchlistBrief.highest_risks?.slice(0, 2).map((rk, i) => (
                                <div key={i} style={{ fontSize: 10, color: "#cbd5e1" }}>{rk.name}</div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div style={{ padding: "16px 0", textAlign: "center", color: "#64748b", fontSize: 12 }}>
                        Briefing metrics are ready. Click compile or wait for background load.
                      </div>
                    )
                  ) : (
                    fetchingStory ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                        <div style={{ height: 16, width: "60%", background: "#1e293b", borderRadius: 4, animation: "pulse 1.5s infinite" }}></div>
                        <div style={{ height: 12, width: "95%", background: "#121b2e", borderRadius: 4, animation: "pulse 1.5s infinite" }}></div>
                        <div style={{ height: 12, width: "90%", background: "#121b2e", borderRadius: 4, animation: "pulse 1.5s infinite" }}></div>
                      </div>
                    ) : marketStoryData ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: 13, lineHeight: 1.5 }}>
                        <h4 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: "#f8fafc" }}>{marketStoryData.title}</h4>
                        <p style={{ margin: 0, color: "#cbd5e1" }}>{marketStoryData.narrative}</p>
                        
                        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 16, borderTop: "1px solid #121b2e", paddingTop: 10, fontSize: 11 }}>
                          <div>
                            <strong style={{ color: "#64748b", textTransform: "uppercase", fontSize: 9, display: "block", marginBottom: 4 }}>Sector Rotation</strong>
                            <span style={{ color: "#e2e8f0" }}>{marketStoryData.sector_rotation}</span>
                          </div>
                          <div>
                            <strong style={{ color: "#64748b", textTransform: "uppercase", fontSize: 9, display: "block", marginBottom: 4 }}>Watchlist Highlights</strong>
                            <span style={{ color: "#e2e8f0" }}>{marketStoryData.watchlist_highlights}</span>
                          </div>
                        </div>

                        <div style={{ borderTop: "1px solid #121b2e", paddingTop: 10, fontSize: 11, display: "flex", justifyContent: "space-between" }}>
                          <div>
                            <strong style={{ color: "#10b981" }}>🚀 Opportunity:</strong> {marketStoryData.opportunities}
                          </div>
                          <div>
                            <strong style={{ color: "#ef4444" }}>⚠️ Risk:</strong> {marketStoryData.risks}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div style={{ padding: "16px 0", textAlign: "center", color: "#64748b", fontSize: 12 }}>
                        Market story narrative is ready. Click load or wait for background.
                      </div>
                    )
                  )}
                </div>
              </div>

              {/* ── ROW 2: SECTOR INTELLIGENCE & UPCOMING EVENTS ── */}
              <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 20, marginBottom: 24 }}>
                
                {/* FEATURE 9: Sector Intelligence Widget */}
                <div style={s.card}>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: "#cbd5e1", margin: "0 0 12px 0" }}>
                    🔥 Sector Intelligence
                  </h3>
                  {sectorsIntel.length > 0 ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {sectorsIntel.map((sec, idx) => (
                        <div key={idx} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 10px", background: "#080c16", border: "1px solid #121b2e", borderRadius: 8 }}>
                          <div>
                            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                              <span style={{ fontSize: 12, fontWeight: 700, color: "#f1f5f9" }}>{sec.name}</span>
                              <span style={{
                                fontSize: 9, fontWeight: 800, color: sec.sentiment === "Positive" ? "#10b981" : sec.sentiment === "Negative" ? "#ef4444" : "#94a3b8",
                                background: sec.sentiment === "Positive" ? "#10b98115" : sec.sentiment === "Negative" ? "#ef444415" : "#1e293b",
                                padding: "1px 5px", borderRadius: 3
                              }}>{sec.sentiment}</span>
                            </div>
                            <span style={{ fontSize: 9, color: "#64748b" }}>Leads: {sec.companies_leading?.join(", ")}</span>
                          </div>
                          
                          <div style={{ display: "flex", gap: 14, fontSize: 11, fontFamily: "monospace", textAlign: "right" }}>
                            <div>
                              <span style={{ color: "#64748b", fontSize: 9 }}>NEWS</span>
                              <div style={{ color: "#cbd5e1" }}>{sec.news_count}</div>
                            </div>
                            <div>
                              <span style={{ color: "#64748b", fontSize: 9 }}>ALERTS</span>
                              <div style={{ color: "#ef4444" }}>{sec.alert_count}</div>
                            </div>
                            <div>
                              <span style={{ color: "#64748b", fontSize: 9 }}>TREND</span>
                              <div style={{ color: sec.trend === "Bullish" ? "#10b981" : sec.trend === "Bearish" ? "#ef4444" : "#cbd5e1" }}>{sec.trend}</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ height: 180, background: "#1e293b", borderRadius: 8, animation: "pulse 1.5s infinite" }}></div>
                  )}
                </div>

                {/* FEATURE 6: Upcoming Events Widget */}
                <div style={s.card}>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: "#cbd5e1", margin: "0 0 12px 0" }}>
                    📅 Upcoming Market Events
                  </h3>
                  {upcomingEvents ? (
                    <div style={{ maxHeight: 220, overflowY: "auto", display: "flex", flexDirection: "column", gap: 12 }}>
                      {/* Today's Events */}
                      {upcomingEvents.today?.length > 0 && (
                        <div>
                          <span style={{ fontSize: 9, fontWeight: 800, color: "#06b6d4", textTransform: "uppercase", display: "block", marginBottom: 6 }}>Today</span>
                          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                            {upcomingEvents.today.map((ev, i) => (
                              <div key={i}
                                onClick={() => handleFetchExplanation("event", ev.name)}
                                onMouseEnter={e => e.currentTarget.style.borderColor = "#06b6d444"}
                                onMouseLeave={e => e.currentTarget.style.borderColor = "transparent"}
                                style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 11, padding: "4px 8px", background: "#05081199", borderRadius: 4, cursor: "pointer", border: "1px solid transparent", transition: "border-color 0.15s" }}
                              >
                                <div>
                                  <strong style={{ color: "#e2e8f0" }}>{ev.name}</strong>
                                  <span style={{ color: "#64748b", marginLeft: 8 }}>{ev.time}</span>
                                </div>
                                <div style={{ display: "flex", gap: 6 }}>
                                  <span style={{ fontSize: 9, color: ev.impact === "High" ? "#ef4444" : "#f59e0b" }}>{ev.impact} Impact</span>
                                  <span style={{ fontSize: 9, color: "#94a3b8" }}>{ev.importance} Imp</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Tomorrow's Events */}
                      {upcomingEvents.tomorrow?.length > 0 && (
                        <div>
                          <span style={{ fontSize: 9, fontWeight: 800, color: "#f59e0b", textTransform: "uppercase", display: "block", marginBottom: 6 }}>Tomorrow</span>
                          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                            {upcomingEvents.tomorrow.map((ev, i) => (
                              <div key={i}
                                onClick={() => handleFetchExplanation("event", ev.name)}
                                onMouseEnter={e => e.currentTarget.style.borderColor = "#06b6d444"}
                                onMouseLeave={e => e.currentTarget.style.borderColor = "transparent"}
                                style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 11, padding: "4px 8px", background: "#05081199", borderRadius: 4, cursor: "pointer", border: "1px solid transparent", transition: "border-color 0.15s" }}
                              >
                                <div>
                                  <strong style={{ color: "#e2e8f0" }}>{ev.name}</strong>
                                  <span style={{ color: "#64748b", marginLeft: 8 }}>{ev.time}</span>
                                </div>
                                <div style={{ display: "flex", gap: 6 }}>
                                  <span style={{ fontSize: 9, color: ev.impact === "High" ? "#ef4444" : "#f59e0b" }}>{ev.impact} Impact</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* This Week Events */}
                      {upcomingEvents.this_week?.length > 0 && (
                        <div>
                          <span style={{ fontSize: 9, fontWeight: 800, color: "#94a3b8", textTransform: "uppercase", display: "block", marginBottom: 6 }}>This Week</span>
                          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                            {upcomingEvents.this_week.map((ev, i) => (
                              <div key={i}
                                onClick={() => handleFetchExplanation("event", ev.name)}
                                onMouseEnter={e => e.currentTarget.style.borderColor = "#06b6d444"}
                                onMouseLeave={e => e.currentTarget.style.borderColor = "transparent"}
                                style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 11, padding: "4px 8px", background: "#05081199", borderRadius: 4, cursor: "pointer", border: "1px solid transparent", transition: "border-color 0.15s" }}
                              >
                                <div>
                                  <strong style={{ color: "#e2e8f0" }}>{ev.name}</strong>
                                  <span style={{ color: "#64748b", marginLeft: 8 }}>{ev.time}</span>
                                </div>
                                <span style={{ fontSize: 9, color: ev.impact === "High" ? "#ef4444" : "#f59e0b" }}>{ev.impact} Impact</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{ height: 180, background: "#1e293b", borderRadius: 8, animation: "pulse 1.5s infinite" }}></div>
                  )}
                </div>
              </div>

              {/* ── ROW 3: TODAY'S OPPORTUNITIES & RISKS ── */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }}>
                
                {/* FEATURE 7: Opportunities Widget */}
                <div style={s.card}>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: "#10b981", margin: "0 0 12px 0" }}>
                    🚀 Today's Top Opportunities (Buy / Long catalyst)
                  </h3>
                  {oppsRisks ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {oppsRisks.opportunities?.map((op, i) => (
                        <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "#10b98106", border: "1px solid #10b98118", borderRadius: 8, fontSize: 12 }}>
                          <div>
                            <strong style={{ color: "#f8fafc" }}>{op.name}</strong>
                            <div style={{ fontSize: 10, color: "#94a3b8", marginTop: 2 }}>{op.reason}</div>
                          </div>
                          <span style={{ fontSize: 11, fontWeight: 800, color: "#10b981" }}>{op.confidence}% Conf</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ height: 150, background: "#1e293b", borderRadius: 8, animation: "pulse 1.5s infinite" }}></div>
                  )}
                </div>

                {/* FEATURE 8: Risks Widget */}
                <div style={s.card}>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: "#ef4444", margin: "0 0 12px 0" }}>
                    ⚠️ Today's Top Risks (Sell / Hedge catalyst)
                  </h3>
                  {oppsRisks ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {oppsRisks.risks?.map((rk, i) => (
                        <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "#ef444406", border: "1px solid #ef444418", borderRadius: 8, fontSize: 12 }}>
                          <div>
                            <strong style={{ color: "#f8fafc" }}>{rk.name}</strong>
                            <div style={{ fontSize: 10, color: "#94a3b8", marginTop: 2 }}>{rk.reason}</div>
                          </div>
                          <span style={{ fontSize: 11, fontWeight: 800, color: "#ef4444" }}>{rk.confidence}% Conf</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ height: 150, background: "#1e293b", borderRadius: 8, animation: "pulse 1.5s infinite" }}></div>
                  )}
                </div>
              </div>

              {/* ── MAIN WATCHLIST DASHBOARD LIST ── */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <h3 style={{ fontSize: 15, fontWeight: 700, color: "#e2e8f0", margin: 0 }}>
                    Watched Companies ({watchlists.length})
                  </h3>
                  
                  {/* Manual search addition for tags */}
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      type="text"
                      value={newKeyword}
                      onChange={e => setNewKeyword(e.target.value)}
                      onKeyDown={e => e.key === "Enter" && addWatchlist()}
                      placeholder="Add raw keyword..."
                      style={{ background: "#0e1626", border: "1px solid #121b2e", borderRadius: 6, padding: "4px 10px", color: "#e2e8f0", fontSize: 12, outline: "none", width: 180 }}
                    />
                    <button onClick={addWatchlist} style={{ ...s.btnPrimary, padding: "4px 10px", borderRadius: 6, fontSize: 12 }}>
                      + Add
                    </button>
                  </div>
                </div>

                {watchlists.length === 0 ? (
                  <div style={{ padding: "60px 20px", textAlign: "center", border: "1px dashed #1e293b", borderRadius: 16, background: "#0b0f19" }}>
                    <div style={{ fontSize: 40, marginBottom: 16 }}>⭐</div>
                    <h3 style={{ fontSize: 18, color: "#f8fafc", fontWeight: 700 }}>Your Watchlist is Empty</h3>
                    <p style={{ fontSize: 13, color: "#64748b", margin: "8px 0 20px 0", maxWidth: 400, marginLeft: "auto", marginRight: "auto" }}>
                      Start tracking companies that matter to you. Add your first company to receive AI-powered market intelligence every day.
                    </p>
                    <button onClick={() => document.getElementById("watchlist-search-input")?.focus()} style={s.btnPrimary}>
                      + Add Company
                    </button>
                  </div>
                ) : (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))", gap: 18 }}>
                    {watchlists.map((item) => {
                      const analysis = item.analysis_cache || {};
                      const isAnalyzing = analyzingCompanyId === item.id;
                      
                      // FEATURE 2: Attention Score mapping
                      const attentionScore = analysis.attention_score || 30;
                      const attentionStatus = analysis.attention_status || "Stable";
                      
                      let attnBadgeColor = "#10b981";
                      let attnBadgeBg = "#10b98115";
                      let attnBadgeText = "🟢 Stable";
                      let attnPulse = false;
                      
                      if (attentionScore >= 80) {
                        attnBadgeColor = "#ef4444";
                        attnBadgeBg = "#ef444420";
                        attnBadgeText = "🔥 Requires Immediate Attention";
                        attnPulse = true;
                      } else if (attentionScore >= 50) {
                        attnBadgeColor = "#f59e0b";
                        attnBadgeBg = "#f59e0b15";
                        attnBadgeText = "⚠️ Monitor Today";
                      }
                      
                      return (
                        <div
                          key={item.id}
                          style={{
                            ...s.card,
                            background: item.favorite ? "linear-gradient(135deg, #0e172a 0%, #0e1626 100%)" : "#0e1626",
                            border: item.favorite ? "1px solid #d9770633" : "1px solid #121b2e",
                            position: "relative",
                            display: "flex",
                            flexDirection: "column",
                            justifyContent: "space-between",
                            gap: 16,
                            transition: "all 0.2s ease-in-out"
                          }}
                        >
                          {/* Card Top: Logo, Name, Exchange, Favorite, Priority */}
                          <div>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                              <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                                <div style={{
                                  width: 36, height: 36, borderRadius: 8, background: "linear-gradient(135deg, #1e293b, #0f172a)",
                                  border: "1px solid #334155", display: "flex", alignItems: "center", justifyContent: "center",
                                  fontWeight: 800, fontSize: 14, color: "#06b6d4"
                                }}>
                                  {item.company_name?.charAt(0)}
                                </div>
                                <div>
                                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                    <h4 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: "#f8fafc" }}>{item.company_name}</h4>
                                    <span style={{ fontSize: 9, color: "#475569", background: "#1e293b", padding: "1px 4px", borderRadius: 3, fontWeight: "bold" }}>{item.exchange}</span>
                                  </div>
                                  <span style={{ fontSize: 10, color: "#64748b" }}>{item.sector} • {item.industry}</span>
                                </div>
                              </div>
                              
                              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                {/* Priority dropdown selector */}
                                <select
                                  value={item.priority || 3}
                                  onChange={(e) => handleUpdateWatchlistItem(item, { priority: parseInt(e.target.value) })}
                                  style={{
                                    background: "#111827", color: "#cbd5e1", border: "1px solid #1e293b",
                                    borderRadius: 4, padding: "2px 4px", fontSize: 10, outline: "none", cursor: "pointer"
                                  }}
                                  title="Priority"
                                >
                                  <option value={1}>P1</option>
                                  <option value={2}>P2</option>
                                  <option value={3}>P3</option>
                                  <option value={4}>P4</option>
                                  <option value={5}>P5</option>
                                </select>
                                
                                {/* Favorite button */}
                                <button
                                  onClick={() => handleUpdateWatchlistItem(item, { favorite: !item.favorite })}
                                  style={{ background: "none", border: "none", cursor: "pointer", fontSize: 15, padding: 0 }}
                                  title={item.favorite ? "Unmark Favorite" : "Mark Favorite"}
                                >
                                  {item.favorite ? "⭐" : "☆"}
                                </button>

                                {/* Delete button */}
                                <button
                                  onClick={() => deleteWatchlist(item.id)}
                                  style={{ background: "none", border: "none", cursor: "pointer", fontSize: 12, color: "#ef4444", padding: 0, marginLeft: 4 }}
                                  title="Remove from Watchlist"
                                >
                                  ✕
                                </button>
                              </div>
                            </div>

                            {/* Ratings & Score row */}
                            <div style={{ display: "flex", gap: 10, alignItems: "center", margin: "12px 0", flexWrap: "wrap" }}>
                              {analysis.watch_score !== undefined ? (
                                <div style={{ display: "inline-flex", background: "#06b6d412", border: "1px solid #06b6d425", borderRadius: 6, padding: "4px 8px", alignItems: "center", gap: 4 }}>
                                  <span style={{ fontSize: 9, color: "#06b6d4", fontWeight: 800, textTransform: "uppercase" }}>Watch Score</span>
                                  <span style={{ fontSize: 12, color: "#06b6d4", fontWeight: 800 }}>{analysis.watch_score}</span>
                                </div>
                              ) : (
                                <div style={{ height: 22, width: 75, background: "#1e293b", borderRadius: 6, animation: "pulse 1.5s infinite" }}></div>
                              )}

                              {analysis.rating ? (
                                <span style={{
                                  fontSize: 10, fontWeight: 800,
                                  color: analysis.rating.toLowerCase().includes("bullish") ? "#10b981" : analysis.rating.toLowerCase().includes("bearish") ? "#ef4444" : "#94a3b8",
                                  background: analysis.rating.toLowerCase().includes("bullish") ? "#10b98110" : analysis.rating.toLowerCase().includes("bearish") ? "#ef444410" : "#1e293b",
                                  padding: "4px 8px", borderRadius: 6, border: `1px solid ${analysis.rating.toLowerCase().includes("bullish") ? "#10b98122" : analysis.rating.toLowerCase().includes("bearish") ? "#ef444422" : "#334155"}`
                                }}>
                                  {analysis.rating.toLowerCase().includes("bullish") ? "🟢 " : analysis.rating.toLowerCase().includes("bearish") ? "🔴 " : "🟡 "}
                                  {analysis.rating}
                                </span>
                              ) : (
                                <div style={{ height: 22, width: 65, background: "#1e293b", borderRadius: 6, animation: "pulse 1.5s infinite" }}></div>
                              )}

                              {analysis.research_quality && (
                                <span style={{ fontSize: 9, color: "#8b5cf6", background: "#8b5cf612", border: "1px solid #8b5cf622", padding: "2px 6px", borderRadius: 4, fontWeight: 700 }}>
                                  🛡️ {analysis.research_quality}
                                </span>
                              )}
                            </div>

                            {/* FEATURE 2: Attention Score Badge */}
                            <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 10 }}>
                              <span style={{
                                fontSize: 10, fontWeight: 800, color: attnBadgeColor, background: attnBadgeBg,
                                padding: "4px 10px", borderRadius: 6, display: "inline-flex", alignItems: "center", gap: 6,
                                border: `1px solid ${attnBadgeColor}33`, animation: attnPulse ? "pulse 2s infinite" : "none"
                              }}>
                                {attnBadgeText}
                              </span>
                              <span style={{ fontSize: 11, fontFamily: "monospace", color: "#64748b" }}>
                                Score: <strong>{attentionScore}</strong>
                              </span>
                            </div>

                            {/* FEATURE 3: What Changed Since Yesterday Section */}
                            <div style={{ background: "#050811aa", border: "1px solid #121b2e", borderRadius: 8, padding: 10, minHeight: 90 }}>
                              <div style={{ fontSize: 10, fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.02em", marginBottom: 6 }}>
                                What Changed Since Yesterday
                              </div>
                              {isAnalyzing ? (
                                <div style={{ display: "flex", flexDirection: "column", gap: 6, padding: "4px 0" }}>
                                  <div style={{ height: 8, width: "90%", background: "#121b2e", borderRadius: 2, animation: "pulse 1.5s infinite" }}></div>
                                  <div style={{ height: 8, width: "80%", background: "#121b2e", borderRadius: 2, animation: "pulse 1.5s infinite" }}></div>
                                </div>
                              ) : analysis.whats_new && analysis.whats_new.length > 0 ? (
                                <ul style={{ margin: 0, paddingLeft: 12, fontSize: 11, color: "#cbd5e1", display: "flex", flexDirection: "column", gap: 4 }}>
                                  {analysis.whats_new.map((bullet, idx) => (
                                    <li key={idx} style={{ listStyleType: "square" }}>{bullet}</li>
                                  ))}
                                </ul>
                              ) : (
                                <p style={{ margin: "4px 0 0 0", fontSize: 11, color: "#475569", fontStyle: "italic" }}>
                                  No major changes registered. Click analyze to check latest updates.
                                </p>
                              )}
                            </div>
                          </div>

                          {/* Card Footer: Metadata (Counts, last updated), Buttons */}
                          <div style={{ borderTop: "1px solid #121b2e", paddingTop: 12, marginTop: 4 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10, fontSize: 10, color: "#64748b" }}>
                              <div style={{ display: "flex", gap: 8 }}>
                                <span>📰 News Today: <strong style={{ color: "#e2e8f0" }}>{analysis.news_count_today || 0}</strong></span>
                                <span>🚨 Alerts: <strong style={{ color: "#ef4444" }}>{analysis.alert_count_today || 0}</strong></span>
                              </div>
                              <span>Risk: <strong style={{ color: analysis.risk_level === "Low" ? "#10b981" : "#f59e0b" }}>{analysis.risk_level || "Low"}</strong></span>
                            </div>

                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                              <span style={{ fontSize: 10, color: "#475569" }}>
                                Updated: {item.last_analyzed_at ? formatTimestamp(item.last_analyzed_at).ageStr : "Never"}
                              </span>
                              
                              <div style={{ display: "flex", gap: 6 }}>
                                <button
                                  onClick={() => handleAnalyzeCompany(item.id, true)}
                                  disabled={isAnalyzing}
                                  style={{
                                    background: "#1e293b", color: "#e2e8f0", border: "1px solid #334155",
                                    borderRadius: 6, padding: "5px 10px", fontSize: 11, fontWeight: 600, cursor: "pointer",
                                    display: "flex", alignItems: "center", gap: 4
                                  }}
                                >
                                  {isAnalyzing ? (
                                    <span style={{ ...s.spinner, width: 8, height: 8 }}></span>
                                  ) : (
                                    "✨"
                                  )} Analyze
                                </button>
                                
                                <button
                                  onClick={() => handleOpenDossier(item.company_name)}
                                  style={{
                                    background: "#1e293b", color: "#e2e8f0", border: "1px solid #334155",
                                    borderRadius: 6, padding: "5px 10px", fontSize: 11, fontWeight: 600, cursor: "pointer"
                                  }}
                                >
                                  Dossier
                                </button>
                                
                                <button
                                  onClick={() => setSelectedWhyMovingCompany(item)}
                                  style={{
                                    background: "linear-gradient(135deg, #0284c7, #0369a1)", color: "#fff", border: "none",
                                    borderRadius: 6, padding: "5px 10px", fontSize: 11, fontWeight: 700, cursor: "pointer"
                                  }}
                                >
                                  Why Moving?
                                </button>
                                <button
                                  onClick={() => handleFetchExplanation("company", item.company_name)}
                                  style={{
                                    background: "linear-gradient(135deg, #a855f7, #6366f1)", color: "#fff", border: "none",
                                    borderRadius: 6, padding: "5px 10px", fontSize: 11, fontWeight: 700, cursor: "pointer"
                                  }}
                                >
                                  ✨ Explain
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* FEATURE 5: Upgraded "Why Is This Moving?" Modal Overlay */}
              {selectedWhyMovingCompany && (
                <div style={s.modalOverlay} onClick={() => setSelectedWhyMovingCompany(null)}>
                  <div style={{ ...s.modalContent, maxWidth: 650 }} onClick={e => e.stopPropagation()}>
                    <div style={s.modalHeader}>
                      <div>
                        <div style={s.modalTitleBadge}>✨ UPGRADED MARKET INTELLIGENCE INTEGRATION</div>
                        <h3 style={s.modalTitle}>Why is {selectedWhyMovingCompany.company_name} Moving?</h3>
                        <p style={{ margin: "2px 0 0 0", fontSize: 11, color: "#64748b" }}>
                          AI portfolio cognitive analysis matching recent events, regulatory context, and peer anomalies.
                        </p>
                      </div>
                      <button onClick={() => setSelectedWhyMovingCompany(null)} style={s.modalCloseBtn}>✕</button>
                    </div>

                    <div style={{ ...s.modalBody, maxHeight: "75vh" }}>
                      {selectedWhyMovingCompany.analysis_cache?.why_moving ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                          
                          {/* Segment 1: What happened */}
                          <div style={{ background: "#0e1626", border: "1px solid #121b2e", borderRadius: 8, padding: 14 }}>
                            <div style={{ fontSize: 10, fontWeight: 800, color: "#06b6d4", textTransform: "uppercase", marginBottom: 6 }}>What Happened?</div>
                            <div style={{ fontSize: 13, color: "#cbd5e1", lineHeight: 1.6 }}>
                              {selectedWhyMovingCompany.analysis_cache.why_moving.what_happened}
                            </div>
                          </div>

                          {/* Segment 2: Why it matters */}
                          <div>
                            <div style={{ fontSize: 10, fontWeight: 800, color: "#8b5cf6", textTransform: "uppercase", marginBottom: 6 }}>Why It Matters</div>
                            <div style={{ fontSize: 12, color: "#cbd5e1", lineHeight: 1.5 }}>
                              {selectedWhyMovingCompany.analysis_cache.why_moving.why_it_matters}
                            </div>
                          </div>

                          {/* Segment 3: Historical and peer impact */}
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                            <div style={{ background: "#111827", border: "1px solid #1f2937", borderRadius: 8, padding: 10 }}>
                              <span style={{ fontSize: 9, fontWeight: 800, color: "#94a3b8", textTransform: "uppercase", display: "block", marginBottom: 4 }}>Historical Similar Events</span>
                              <span style={{ fontSize: 11, color: "#94a3b8", lineHeight: 1.4 }}>
                                {selectedWhyMovingCompany.analysis_cache.why_moving.historical_similar_events}
                              </span>
                            </div>
                            <div style={{ background: "#111827", border: "1px solid #1f2937", borderRadius: 8, padding: 10 }}>
                              <span style={{ fontSize: 9, fontWeight: 800, color: "#94a3b8", textTransform: "uppercase", display: "block", marginBottom: 4 }}>Companies Also Affected</span>
                              <span style={{ fontSize: 11, color: "#cbd5e1", lineHeight: 1.4 }}>
                                {selectedWhyMovingCompany.analysis_cache.why_moving.companies_also_affected?.join(", ") || "None"}
                              </span>
                            </div>
                          </div>

                          {/* Segment 4: Potential Market Impact */}
                          <div style={{ background: "#1e3a8a10", border: "1px solid #1e3a8a30", borderRadius: 8, padding: 12 }}>
                            <span style={{ fontSize: 9, fontWeight: 800, color: "#3b82f6", textTransform: "uppercase", display: "block", marginBottom: 4 }}>Potential Market Impact</span>
                            <span style={{ fontSize: 12, color: "#cbd5e1", lineHeight: 1.4 }}>
                              {selectedWhyMovingCompany.analysis_cache.why_moving.potential_market_impact}
                            </span>
                          </div>

                          {/* FEATURE 4: Company Event Timeline */}
                          {selectedWhyMovingCompany.analysis_cache.timeline && selectedWhyMovingCompany.analysis_cache.timeline.length > 0 && (
                            <div>
                              <div style={{ fontSize: 10, fontWeight: 800, color: "#cbd5e1", textTransform: "uppercase", borderBottom: "1px solid #121b2e", paddingBottom: 6, marginBottom: 12 }}>
                                ⏳ Company Event Timeline (Past 7 Days)
                              </div>
                              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                                {selectedWhyMovingCompany.analysis_cache.timeline.map((ev, i) => (
                                  <div key={i} style={{ display: "flex", gap: 12, alignItems: "center", fontSize: 11 }}>
                                    <span style={{ color: "#06b6d4", fontFamily: "monospace", fontWeight: 700, width: 45 }}>{ev.date}</span>
                                    <span style={{
                                      fontSize: 9, padding: "1px 5px", borderRadius: 3, width: 50, textAlign: "center", fontWeight: "bold",
                                      background: ev.type === "alert" ? "#ef444415" : ev.type === "research" ? "#8b5cf615" : "#06b6d415",
                                      color: ev.type === "alert" ? "#ef4444" : ev.type === "research" ? "#8b5cf6" : "#06b6d4"
                                    }}>{ev.type.toUpperCase()}</span>
                                    <span style={{ color: "#cbd5e1", flex: 1 }}>{ev.event}</span>
                                    <span style={{ color: ev.impact === "Bullish" ? "#10b981" : ev.impact === "Bearish" ? "#ef4444" : "#94a3b8", fontWeight: 700 }}>
                                      {ev.impact}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Segment 5: Bull / Bear cases & Evidence */}
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                            <div style={{ background: "#10b98108", border: "1px solid #10b98115", borderRadius: 8, padding: 12 }}>
                              <span style={{ fontSize: 10, fontWeight: 800, color: "#10b981", textTransform: "uppercase", display: "block", marginBottom: 4 }}>📈 Bull Case</span>
                              <span style={{ fontSize: 12, color: "#cbd5e1", lineHeight: 1.4 }}>
                                {selectedWhyMovingCompany.analysis_cache.why_moving.bull_case}
                              </span>
                            </div>
                            <div style={{ background: "#ef444408", border: "1px solid #ef444415", borderRadius: 8, padding: 12 }}>
                              <span style={{ fontSize: 10, fontWeight: 800, color: "#ef4444", textTransform: "uppercase", display: "block", marginBottom: 4 }}>📉 Bear Case</span>
                              <span style={{ fontSize: 12, color: "#cbd5e1", lineHeight: 1.4 }}>
                                {selectedWhyMovingCompany.analysis_cache.why_moving.bear_case}
                              </span>
                            </div>
                          </div>

                          {/* Evidence citation block */}
                          <div style={{ background: "#05081199", border: "1px solid #121b2e", borderRadius: 8, padding: 12 }}>
                            <span style={{ fontSize: 9, fontWeight: 800, color: "#94a3b8", textTransform: "uppercase", display: "block", marginBottom: 4 }}>📌 Evidence & Citations</span>
                            <span style={{ fontSize: 11, color: "#cbd5e1", lineHeight: 1.4 }}>
                              {selectedWhyMovingCompany.analysis_cache.why_moving.evidence}
                            </span>
                          </div>

                          {/* Metadata: confidence, sources */}
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid #121b2e", paddingTop: 12, fontSize: 11, color: "#64748b" }}>
                            <span>AI Confidence: <strong style={{ color: "#cbd5e1" }}>{selectedWhyMovingCompany.analysis_cache.why_moving.confidence || selectedWhyMovingCompany.analysis_cache.confidence}%</strong></span>
                            <span>Sources: <strong style={{ color: "#cbd5e1" }}>{(selectedWhyMovingCompany.analysis_cache.why_moving.sources || []).join(", ")}</strong></span>
                          </div>

                        </div>
                      ) : (
                        <div style={{ padding: "30px 0", textAlign: "center" }}>
                          <span style={s.spinnerBig}></span>
                          <p style={{ marginTop: 12, fontSize: 12, color: "#64748b" }}>No cached intelligence found. Try triggering a card analysis first.</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* FEATURE 11: Global Command Bar (Ctrl + K) Modal */}
              {commandBarOpen && (
                <div style={s.modalOverlay} onClick={() => setCommandBarOpen(false)}>
                  <div style={{ ...s.modalContent, maxWidth: 550, borderRadius: 12 }} onClick={e => e.stopPropagation()}>
                    {/* Command bar input */}
                    <div style={{ padding: "14px 18px", borderBottom: "1px solid #121b2e", display: "flex", alignItems: "center" }}>
                      <span style={{ fontSize: 18, marginRight: 10, color: "#06b6d4" }}>⚡</span>
                      <input
                        autoFocus
                        type="text"
                        value={commandSearchQuery}
                        onChange={async (e) => {
                          const val = e.target.value;
                          setCommandSearchQuery(val);
                          // FEATURE 12: Grouped Smart Global Search
                          if (val.trim().length > 1) {
                            try {
                              const res = await api.get("/api/market-intelligence/search", { params: { q: val } });
                              setCommandResults(res.data);
                            } catch (err) {
                              console.error(err);
                            }
                          } else {
                            setCommandResults({});
                          }
                        }}
                        placeholder="Type a command or search (e.g. 'Analyze HDFC Bank', 'Open Watchlist')..."
                        style={{ background: "none", border: "none", color: "#f8fafc", outline: "none", width: "100%", fontSize: 14 }}
                      />
                      <span style={{ fontSize: 10, color: "#475569", background: "#111827", padding: "3px 6px", borderRadius: 4, fontStyle: "monospace" }}>ESC</span>
                    </div>

                    {/* Commands List & Grouped Search Results */}
                    <div style={{ maxHeight: 350, overflowY: "auto", padding: "8px 0" }}>
                      
                      {/* Grouped results from smart search if searching */}
                      {Object.keys(commandResults).length > 0 ? (
                        <div>
                          {Object.entries(commandResults).map(([groupName, items]) => (
                            <div key={groupName}>
                              <div style={{ padding: "6px 16px", fontSize: 10, fontWeight: 800, color: "#06b6d4", textTransform: "uppercase", background: "#0c152755" }}>
                                {groupName}
                              </div>
                              {items.map((item, idx) => (
                                <div
                                  key={idx}
                                  onClick={() => {
                                    setCommandBarOpen(false);
                                    setCommandSearchQuery("");
                                    setCommandResults({});
                                    
                                    if (groupName === "Watchlists") {
                                      setActiveSection("watchlist");
                                    } else if (groupName === "Saved Workspaces") {
                                      setActiveSection("workspace");
                                      setCurrentWorkspace({
                                        id: item.id,
                                        title: item.title,
                                        query: item.query_text,
                                        analysis_json: item.analysis_json,
                                        notes: item.notes,
                                        is_favorite: item.is_favorite
                                      });
                                      setWorkspaceQuery(item.query_text);
                                      setWorkspaceNotes(item.notes || "");
                                    } else if (groupName === "Portfolio Holdings") {
                                      setActiveSection("portfolio");
                                      setPortfolioActiveTab("holdings");
                                    } else if (groupName === "Research Documents") {
                                      setActiveSection("research_library");
                                    } else if (groupName === "Smart Alerts") {
                                      setActiveSection("alerts");
                                    } else if (groupName === "News Intelligence") {
                                      setActiveSection("summary");
                                    } else if (groupName === "AI Conversations") {
                                      setActiveSection("ask");
                                      loadChatSession(item.id);
                                    }
                                  }}
                                  style={{ padding: "8px 16px", cursor: "pointer", transition: "background 0.1s" }}
                                  onMouseEnter={e => e.target.style.background = "#0e1626"}
                                  onMouseLeave={e => e.target.style.background = "transparent"}
                                >
                                  <div style={{ fontSize: 12, fontWeight: 600, color: "#f1f5f9" }}>{item.title}</div>
                                  <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>{item.subtitle}</div>
                                </div>
                              ))}
                            </div>
                          ))}
                        </div>
                      ) : (
                        // Standard shortcut commands
                        <div>
                          <div style={{ padding: "6px 16px", fontSize: 10, fontWeight: 800, color: "#64748b", textTransform: "uppercase" }}>Quick Actions</div>
                          
                          {[
                            { name: "Analyze HDFC Bank", action: () => { handleOpenDossier("HDFC Bank"); } },
                            { name: "Analyze TCS", action: () => { handleOpenDossier("TCS"); } },
                            { name: "Analyze Nvidia", action: () => { handleOpenDossier("Nvidia"); } },
                            { name: "Compare TCS vs Infosys", action: () => { setActiveSection("ask"); setQuestion("Compare TCS and Infosys cloud earnings growth in detail."); } },
                            { name: "Generate Today's Brief", action: () => { handleGenerateWatchlistBrief(); } },
                            { name: "Search Research Library", action: () => { setActiveSection("research_library"); } },
                            { name: "Open Smart Alerts", action: () => { setActiveSection("alerts"); } },
                            { name: "Show RBI News", action: () => { setActiveSection("summary"); setNewsSource("rbi"); } },
                            { name: "Open Watchlist Dashboard", action: () => { setActiveSection("watchlist"); } },
                            { name: "Open Company Dossier", action: () => { setActiveSection("ask"); } }
                          ]
                          .filter(c => !commandSearchQuery || c.name.toLowerCase().includes(commandSearchQuery.toLowerCase()))
                          .map((cmd, idx) => (
                            <div
                              key={idx}
                              onClick={() => {
                                setCommandBarOpen(false);
                                setCommandSearchQuery("");
                                cmd.action();
                              }}
                              style={{ padding: "10px 16px", cursor: "pointer", fontSize: 12, color: "#cbd5e1", transition: "background 0.15s", display: "flex", justifyContent: "space-between", alignItems: "center" }}
                              onMouseEnter={e => e.target.style.background = "#0e1626"}
                              onMouseLeave={e => e.target.style.background = "transparent"}
                            >
                              <span>{cmd.name}</span>
                              <span style={{ fontSize: 9, color: "#475569", background: "#111827", padding: "1px 5px", borderRadius: 3 }}>Command</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* SECTOR HEATMAP */}
          {activeSection === "heatmap" && (
            <div>
              <div style={{ ...s.card, marginBottom: 20 }}>
                <div style={s.cardHeader}>Sector Sentiment & Impact Heatmap</div>
                <div style={s.cardSub}>Aggregated news metrics representing market momentum across key sectors.</div>
              </div>

              {heatmapData.length === 0 ? <EmptyState msg="Sector aggregates are loading..." /> : (
                <div style={s.grid3}>
                  {heatmapData.map((sect, i) => {
                    let bgGrad = "linear-gradient(135deg, #111827, #1e293b)";
                    let statusColor = "#94a3b8";
                    if (sect?.sentiment === "Bullish") {
                      bgGrad = "linear-gradient(135deg, #0f172a, #064e3b)";
                      statusColor = "#10b981";
                    } else if (sect?.sentiment === "Bearish") {
                      bgGrad = "linear-gradient(135deg, #0f172a, #7f1d1d)";
                      statusColor = "#ef4444";
                    }

                    return (
                      <div key={i} style={{ ...s.card, background: bgGrad, border: `1px solid ${statusColor}33` }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                          <div>
                            <div style={{ fontSize: 18, fontWeight: 800, color: "#f8fafc" }}>{sect?.sector}</div>
                            <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>{sect?.news_count} news items tracked</div>
                          </div>
                          <span style={{
                            fontSize: 10,
                            fontWeight: 800,
                            color: statusColor,
                            background: `${statusColor}18`,
                            padding: "4px 10px",
                            borderRadius: 6,
                            textTransform: "uppercase",
                            letterSpacing: "0.05em"
                          }}>
                            ● {sect?.sentiment || "Neutral"}
                          </span>
                        </div>

                        <div style={{ marginTop: 20 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#94a3b8", marginBottom: 4 }}>
                            <span>Avg Impact Score</span>
                            <span style={{ color: "#f8fafc", fontWeight: "bold" }}>{sect?.score || 50} / 100</span>
                          </div>
                          <div style={{ height: 4, backgroundColor: "#334155", borderRadius: 2, overflow: "hidden" }}>
                            <div style={{ height: "100%", width: `${sect?.score || 50}%`, backgroundColor: statusColor }} />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* EVENT TIMELINE */}
          {activeSection === "timeline" && (
            <div style={{ display: "grid", gridTemplateColumns: "240px 1fr", gap: 24 }}>
              {/* Sidebar Entities */}
              <div style={{ ...s.sidebarPanel, display: "flex", flexDirection: "column" }}>
                <h4 style={{ fontSize: 12, color: "#475569", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10, paddingLeft: 8 }}>Tracked Entities</h4>
                <div style={{ padding: "0 8px", marginBottom: 12 }}>
                  <input
                    type="text"
                    placeholder="Search entities..."
                    value={entitySearchQuery}
                    onChange={e => setEntitySearchQuery(e.target.value)}
                    style={{
                      width: "100%",
                      background: "#0f172a",
                      border: "1px solid #1e293b",
                      borderRadius: "6px",
                      padding: "8px 12px",
                      fontSize: "13px",
                      color: "#f8fafc",
                      outline: "none"
                    }}
                  />
                </div>
                <div style={{ flex: 1, overflowY: "auto" }}>
                  {timelineEntities.filter(ent => ent.name.toLowerCase().includes(entitySearchQuery.toLowerCase())).length === 0 ? (
                    <div style={{ fontSize: 12, color: "#475569", padding: 8 }}>No matching entities</div>
                  ) : (
                    timelineEntities
                      .filter(ent => ent.name.toLowerCase().includes(entitySearchQuery.toLowerCase()))
                      .map((ent, i) => (
                        <button key={i} onClick={() => setSelectedTimelineEntity(ent.name)} style={{
                          ...s.sidebarItemBtn,
                          backgroundColor: selectedTimelineEntity === ent.name ? "#06b6d415" : "transparent",
                          color: selectedTimelineEntity === ent.name ? "#06b6d4" : "#94a3b8",
                          borderLeft: selectedTimelineEntity === ent.name ? "2px solid #06b6d4" : "2px solid transparent"
                        }}>
                          <span style={{ flex: 1, textAlign: "left", fontSize: 13, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{ent?.name}</span>
                          <span style={{ fontSize: 9, color: "#475569", background: "#1e293b", padding: "2px 6px", borderRadius: 4, marginLeft: 4 }}>{ent?.type}</span>
                        </button>
                      ))
                  )}
                </div>
              </div>

              {/* Timeline Flow */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 12 }}>
                  <h3 style={{ fontSize: 16, color: "#cbd5e1", margin: 0 }}>Historical Timeline for: <span style={{ color: "#06b6d4" }}>{selectedTimelineEntity}</span></h3>
                  {selectedTimelineEntity && timelineEvents.length > 0 && (
                    <button
                      onClick={handleGenerateTimelineSummary}
                      disabled={generatingTimelineSummary}
                      style={{
                        ...s.btnPrimary,
                        padding: "6px 14px",
                        fontSize: "12px",
                        background: generatingTimelineSummary ? "#0891b250" : "#0891b2",
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        border: "none",
                        cursor: "pointer"
                      }}
                    >
                      <span>✨ {generatingTimelineSummary ? "Summarizing..." : "AI Timeline Summary"}</span>
                    </button>
                  )}
                </div>

                {timelineSummary && (
                  <div style={{
                    background: "linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(15, 23, 42, 0.4) 100%)",
                    border: "1px solid rgba(6, 182, 212, 0.2)",
                    borderRadius: "10px",
                    padding: "16px",
                    marginBottom: "24px",
                    boxShadow: "0 4px 20px -2px rgba(0,0,0,0.3)"
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "13px", fontWeight: "bold", color: "#06b6d4", marginBottom: "8px" }}>
                      <span>✨</span>
                      <span>AI EXECUTIVE BRIEFING</span>
                    </div>
                    <p style={{ fontSize: "13px", color: "#e2e8f0", lineHeight: "1.6", margin: 0 }}>
                      {timelineSummary}
                    </p>
                  </div>
                )}

                {timelineEvents.length === 0 ? <EmptyState msg="No timeline events indexed for this entity." /> : (
                  <div style={s.timelineContainer}>
                    {timelineEvents.map((evt, i) => (
                      <div key={i} style={s.timelineItem}>
                        <div style={s.timelineDot} />
                        <div style={s.timelineDate}>{new Date(evt.event_date).toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" })}</div>
                        <div style={s.timelineContentCard}>
                          <div style={{ fontSize: 14, fontWeight: 700, color: "#f1f5f9" }}>{evt?.event_title}</div>
                          {evt?.description && (
                            <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 6, lineHeight: 1.5 }}>
                              {evt?.description}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* MULTI-AGENT RESEARCH REPORT */}
          {activeSection === "reports" && (
            <div style={{ display: "grid", gridTemplateColumns: "240px 1fr", gap: 24 }}>
              {/* Sidebar Reports History */}
              <div style={s.sidebarPanel}>
                <h4 style={{ fontSize: 12, color: "#475569", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12, paddingLeft: 8 }}>Saved Reports</h4>
                {reportsList.length === 0 ? <div style={{ fontSize: 12, color: "#475569", padding: 8 }}>No reports generated</div> : reportsList.map((rep, i) => (
                  <button key={i} onClick={() => selectPastReport(rep.id)} style={{
                    ...s.sidebarItemBtn,
                    backgroundColor: selectedReport && selectedReport.id === rep.id ? "#06b6d415" : "transparent",
                    color: selectedReport && selectedReport.id === rep.id ? "#06b6d4" : "#94a3b8",
                  }}>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 2, width: "100%" }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{rep?.entity_name}</span>
                      <span style={{ fontSize: 9, color: "#475569" }}>
                        Rating: <span style={{ color: rep?.rating === "BUY" ? "#10b981" : rep?.rating === "SELL" ? "#ef4444" : "#94a3b8", fontWeight: "bold" }}>{rep?.rating || "NEUTRAL"}</span>
                      </span>
                    </div>
                  </button>
                ))}
              </div>

              {/* Main Report Panel */}
              <div>
                <div style={s.card}>
                  <div style={s.cardHeader}>Generate Investment Research Report</div>
                  <div style={s.cardSub}>Orchestrates News, Sentiment, Entity, Timeline, and Risk datasets to compile deep intelligence.</div>
                  <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
                    <input type="text" value={reportSearch} onChange={e => setReportSearch(e.target.value)} placeholder="Enter entity name (e.g. Reliance, RBI, TCS)" style={s.input} />
                    <button onClick={triggerReportGeneration} disabled={generatingReport} style={{ ...s.btnPrimary, minWidth: 150 }}>
                      {generatingReport ? "Running Agents..." : "Analyze Entity"}
                    </button>
                  </div>
                </div>

                {generatingReport && (
                  <div style={{ ...s.card, marginTop: 16, display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
                    <div style={s.spinnerBig} />
                    <div style={{ textAlign: "center" }}>
                      <div style={{ color: "#e2e8f0", fontWeight: "bold" }}>Running Multi-Agent Intelligence Network</div>
                      <div style={{ color: "#475569", fontSize: 12, marginTop: 4 }}>Synthesizing news history, mapping relationships, outlining risk variables, and generating final rating...</div>
                    </div>
                  </div>
                )}

                {selectedReport && !generatingReport && (
                  <div style={{ ...s.card, marginTop: 16 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #1e293b", paddingBottom: 16, marginBottom: 20 }}>
                      <div>
                        <h2 style={{ fontSize: 22, fontWeight: 800, color: "#f8fafc" }}>Research Report: {selectedReport?.entity_name}</h2>
                        <div style={{ fontSize: 11, color: "#475569", marginTop: 4 }}>Generated on {selectedReport?.created_at ? new Date(selectedReport.created_at).toLocaleDateString("en-IN", { dateStyle: "long" }) : "Unknown"}</div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <span style={{
                          fontSize: 14,
                          fontWeight: 800,
                          padding: "6px 16px",
                          borderRadius: 8,
                          color: selectedReport?.report_data?.overall_rating === "BUY" || selectedReport?.report_data?.overall_rating === "ACCUMULATE" ? "#10b981" : selectedReport?.report_data?.overall_rating === "SELL" ? "#ef4444" : "#94a3b8",
                          background: selectedReport?.report_data?.overall_rating === "BUY" || selectedReport?.report_data?.overall_rating === "ACCUMULATE" ? "#10b98115" : selectedReport?.report_data?.overall_rating === "SELL" ? "#ef444415" : "#1e293b",
                          border: `1px solid ${selectedReport?.report_data?.overall_rating === "BUY" || selectedReport?.report_data?.overall_rating === "ACCUMULATE" ? "#10b98133" : selectedReport?.report_data?.overall_rating === "SELL" ? "#ef444433" : "#334155"}`
                        }}>
                          RATING: {selectedReport?.report_data?.overall_rating || "NEUTRAL"}
                        </span>
                      </div>
                    </div>

                    {/* Executive Summary */}
                    <div style={{ marginBottom: 24 }}>
                      <h4 style={s.reportSectionHeader}>Executive Summary</h4>
                      <p style={{ fontSize: 14, color: "#cbd5e1", lineHeight: 1.7 }}>{selectedReport?.report_data?.executive_summary}</p>
                    </div>

                    {/* Sentiment Analysis */}
                    <div style={{ marginBottom: 24 }}>
                      <h4 style={s.reportSectionHeader}>Sentiment Analysis</h4>
                      <p style={{ fontSize: 14, color: "#cbd5e1", lineHeight: 1.7 }}>{selectedReport?.report_data?.sentiment_analysis}</p>
                    </div>

                    {/* Opportunities & Risks */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
                      <div style={{ background: "#10b98108", border: "1px solid #10b98122", borderRadius: 8, padding: 16 }}>
                        <h4 style={{ fontSize: 13, color: "#10b981", fontWeight: 700, marginBottom: 10 }}>Opportunities</h4>
                        <ul style={{ paddingLeft: 16, fontSize: 12, color: "#cbd5e1", margin: 0 }}>
                          {(selectedReport?.report_data?.opportunities || []).map((o, idx) => (
                            <li key={idx} style={{ marginBottom: 8, lineHeight: 1.5 }}>{o}</li>
                          ))}
                        </ul>
                      </div>
                      <div style={{ background: "#ef444408", border: "1px solid #ef444422", borderRadius: 8, padding: 16 }}>
                        <h4 style={{ fontSize: 13, color: "#ef4444", fontWeight: 700, marginBottom: 10 }}>Threat Vectors & Risks</h4>
                        <ul style={{ paddingLeft: 16, fontSize: 12, color: "#cbd5e1", margin: 0 }}>
                          {(selectedReport?.report_data?.risks || []).map((r, idx) => (
                            <li key={idx} style={{ marginBottom: 8, lineHeight: 1.5 }}>{r}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Timeline compilation */}
                    <div style={{ marginBottom: 24 }}>
                      <h4 style={s.reportSectionHeader}>Compiled Timeline Events</h4>
                      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                        {(selectedReport?.report_data?.historical_timeline || []).map((item, idx) => (
                          <div key={idx} style={{ fontSize: 13, color: "#cbd5e1", background: "#1e293b44", padding: "8px 12px", borderRadius: 6, borderLeft: "2px solid #06b6d4" }}>
                            {item}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* News narratives */}
                    <div>
                      <h4 style={s.reportSectionHeader}>Recent Headlines Narrative</h4>
                      <ul style={{ paddingLeft: 16, fontSize: 13, color: "#cbd5e1", margin: 0 }}>
                        {(selectedReport?.report_data?.recent_news || []).map((news, idx) => (
                          <li key={idx} style={{ marginBottom: 8, lineHeight: 1.5 }}>{news}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* SMART ALERTS */}
          {activeSection === "alerts" && (
            <div>
              {/* Clickable KPI Cards */}
              <div style={s.statsRow}>
                <StatCard 
                  label="High Impact Alerts" 
                  value={allAlerts.filter(a => a.importance_score >= 80).length} 
                  color="#ef4444"
                  clickable={true}
                  active={selectedImportanceMin === 80}
                  onClick={() => {
                    if (selectedImportanceMin === 80) {
                      setSelectedImportanceMin(null);
                    } else {
                      setSelectedImportanceMin(80);
                    }
                  }}
                />
                <StatCard 
                  label="Critical Risk (≥90)" 
                  value={allAlerts.filter(a => a.impact_level === "CRITICAL").length} 
                  color="#f59e0b"
                  clickable={true}
                  active={selectedSeverity === "CRITICAL"}
                  onClick={() => {
                    if (selectedSeverity === "CRITICAL") {
                      setSelectedSeverity(null);
                    } else {
                      setSelectedSeverity("CRITICAL");
                    }
                  }}
                />
                <StatCard 
                  label="Inbound Alerts" 
                  value={allAlerts.length} 
                  color="#06b6d4"
                  clickable={true}
                  active={selectedDirection === "INBOUND"}
                  onClick={() => {
                    if (selectedDirection === "INBOUND") {
                      setSelectedDirection(null);
                    } else {
                      setSelectedDirection("INBOUND");
                    }
                  }}
                />
              </div>

              {/* Shared Filter Bar */}
              <FilterBar 
                sources={alertSources}
                selectedSource={selectedSource}
                onSourceChange={setSelectedSource}
                severity={selectedSeverity}
                selectedSeverity={selectedSeverity}
                onSeverityChange={setSelectedSeverity}
                importanceMin={selectedImportanceMin}
                selectedImportanceMin={selectedImportanceMin}
                onImportanceMinChange={setSelectedImportanceMin}
                direction={selectedDirection}
                selectedDirection={selectedDirection}
                onDirectionChange={setSelectedDirection}
              />

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 12 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12, flex: 1, minWidth: 280 }}>
                  <ActiveFilterChips 
                    filters={{
                      source: selectedSource,
                      severity: selectedSeverity,
                      importanceMin: selectedImportanceMin,
                      direction: selectedDirection,
                      sort: selectedSort
                    }}
                    onRemove={(key) => {
                      if (key === "source") setSelectedSource("all");
                      if (key === "severity") setSelectedSeverity(null);
                      if (key === "importanceMin") setSelectedImportanceMin(null);
                      if (key === "direction") setSelectedDirection(null);
                      if (key === "sort") setSelectedSort("latest");
                    }}
                  />
                  
                  {/* Bulk Summarize Button */}
                  <button
                    onClick={handleAlertsBulkSummarize}
                    disabled={selectedAlertIds.length === 0}
                    style={{
                      ...s.btnPrimary,
                      opacity: selectedAlertIds.length === 0 ? 0.5 : 1,
                      cursor: selectedAlertIds.length === 0 ? "not-allowed" : "pointer",
                      padding: "8px 14px",
                      fontSize: 12,
                      background: "linear-gradient(135deg, #a855f7, #6366f1)"
                    }}
                  >
                    ✨ Summarize Selected ({selectedAlertIds.length})
                  </button>
                </div>
                
                <SortDropdown value={selectedSort} onChange={setSelectedSort} />
              </div>

              {/* Alert cards grid / Empty state */}
              {alerts.length === 0 ? (
                <div style={{ textAlign: "center", padding: "60px 20px", color: "#475569", fontSize: 14, border: "1px dashed #1e293b", borderRadius: 12, background: "#0e1626", width: "100%", boxSizing: "border-box" }}>
                  <div style={{ fontSize: 32, marginBottom: 12 }}>📭</div>
                  <div style={{ color: "#cbd5e1", fontWeight: 600, marginBottom: 6 }}>No alerts match the selected filters.</div>
                  <div style={{ color: "#64748b", fontSize: 12, marginBottom: 16 }}>Try clearing filters or selecting another source.</div>
                  <button 
                    onClick={() => {
                      setSelectedSeverity(null);
                      setSelectedImportanceMin(null);
                      setSelectedDirection(null);
                      setSelectedSource("all");
                      setSelectedSort("latest");
                      setSelectedAlertIds([]);
                    }} 
                    style={{ ...s.btnPrimary, margin: "0 auto" }}
                  >
                    Clear Filters
                  </button>
                </div>
              ) : (
                <div style={s.grid3}>
                  {alerts.map((alert, i) => {
                    const { ageStr, tooltipStr } = formatAlertTimestamp(alert.created_at);
                    const isSelected = selectedAlertIds.includes(alert.id);
                    return (
                      <div key={i} style={{
                        ...s.alertCard,
                        border: isSelected ? "1px solid #06b6d4" : "1px solid #121b2e",
                        boxShadow: isSelected ? "0 0 10px rgba(6, 182, 212, 0.15)" : "none",
                        transition: "all 0.2s ease"
                      }}>
                        {/* Alert Card Header Layout */}
                        <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 12 }}>
                          {/* Row 1: Checkbox, Event Type, Severity, Importance Score */}
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                              <input 
                                type="checkbox"
                                checked={isSelected}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSelectedAlertIds(prev => [...prev, alert.id]);
                                  } else {
                                    setSelectedAlertIds(prev => prev.filter(id => id !== alert.id));
                                  }
                                }}
                                style={{
                                  marginRight: 4,
                                  cursor: "pointer",
                                  accentColor: "#06b6d4",
                                  width: 14,
                                  height: 14
                                }}
                              />
                              <EventBadge type={alert?.event_type} />
                              <ImpactBadge level={alert?.impact_level} />
                            </div>
                            <div style={{
                              fontSize: 10, fontWeight: 700, fontFamily: "monospace",
                              color: IMPORTANCE_COLOR(alert?.importance_score),
                              background: `${IMPORTANCE_COLOR(alert?.importance_score)}18`,
                              padding: "2px 8px", borderRadius: 6
                            }}>
                              {alert?.importance_score}
                            </div>
                          </div>
                          {/* Row 2: Relative timestamp with hover tooltip */}
                          <div 
                            title={tooltipStr}
                            style={{ 
                              fontSize: 11, 
                              color: "#64748b", 
                              display: "flex", 
                              alignItems: "center", 
                              gap: 4,
                              fontWeight: 500
                            }}
                          >
                            🕒 {ageStr}
                          </div>
                        </div>

                        {/* Title & reasoning & footer */}
                        <div style={s.alertTitle}>
                          {alert?.post_url ? (
                            <a href={alert.post_url} target="_blank" rel="noreferrer" style={{ color: "#e2e8f0", textDecoration: "none" }}
                               onMouseEnter={e => e.target.style.color = "#ef4444"}
                               onMouseLeave={e => e.target.style.color = "#e2e8f0"}>
                              {alert?.title}
                            </a>
                          ) : alert?.title}
                        </div>
                        {alert?.reasoning && (
                          <div style={{ fontSize: 11, color: "#cbd5e1", marginTop: 10, lineHeight: 1.5, background: "#1e293b", padding: "8px 10px", borderRadius: 6, borderLeft: "2px solid #ef4444" }}>
                            {alert?.reasoning}
                          </div>
                        )}
                        
                        <div style={{ marginTop: 12, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                          <SourceBadge source_id={alert?.source_id} />
                          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                            <ConfidenceBadge score={alert?.confidence} />
                            <button
                              onClick={() => handleAlertSummarize(alert.id)}
                              style={{
                                ...s.btnSummaryAI,
                                padding: "4px 8px",
                                fontSize: 10,
                                background: "linear-gradient(135deg, #a855f7, #6366f1)"
                              }}
                            >
                              ✨ Summarize with AI
                            </button>
                            <button
                              onClick={() => handleFetchExplanation("alert", alert.id)}
                              style={{
                                ...s.btnSummaryAI,
                                padding: "4px 8px",
                                fontSize: 10,
                                background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
                                marginLeft: 4
                              }}
                            >
                              ✨ Explain Alert
                            </button>
                          </div>
                        </div>
                        <ImportanceBar score={alert?.importance_score} />
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}


          {/* IN-APP NOTIFICATIONS */}
          {activeSection === "notifications" && (
            <div>
              {/* Clickable KPI Cards */}
              <div style={s.statsRow}>
                <StatCard 
                  label="Critical (≥90)" 
                  value={allNotifications.filter(n => n.importance_score >= 90).length} 
                  color="#ef4444"
                  clickable={true}
                  active={notifSeverity === "CRITICAL"}
                  onClick={() => setNotifSeverity(notifSeverity === "CRITICAL" ? null : "CRITICAL")}
                />
                <StatCard 
                  label="High Impact (≥80)" 
                  value={allNotifications.filter(n => n.importance_score >= 80).length} 
                  color="#f59e0b"
                  clickable={true}
                  active={notifImportanceMin === 80}
                  onClick={() => setNotifImportanceMin(notifImportanceMin === 80 ? null : 80)}
                />
                <StatCard 
                  label="Inbound Alerts" 
                  value={allNotifications.length} 
                  color="#06b6d4"
                  clickable={true}
                  active={notifDirection === "INBOUND"}
                  onClick={() => setNotifDirection(notifDirection === "INBOUND" ? null : "INBOUND")}
                />
                <StatCard 
                  label="Unread" 
                  value={allNotifications.filter(n => !n.is_read).length} 
                  color="#a855f7"
                  clickable={true}
                  active={notifReadStatus === "unread"}
                  onClick={() => setNotifReadStatus(notifReadStatus === "unread" ? "all" : "unread")}
                />
                <StatCard 
                  label="Read" 
                  value={allNotifications.filter(n => n.is_read).length} 
                  color="#10b981"
                  clickable={true}
                  active={notifReadStatus === "read"}
                  onClick={() => setNotifReadStatus(notifReadStatus === "read" ? "all" : "read")}
                />
              </div>

              {/* Shared Filter Bar */}
              <FilterBar 
                sources={[...new Set(allNotifications.map(n => n.source).filter(Boolean))]}
                selectedSource={notifSource}
                onSourceChange={setNotifSource}
                severity={notifSeverity}
                selectedSeverity={notifSeverity}
                onSeverityChange={setNotifSeverity}
                importanceMin={notifImportanceMin}
                selectedImportanceMin={notifImportanceMin}
                onImportanceMinChange={setNotifImportanceMin}
                direction={notifDirection}
                selectedDirection={notifDirection}
                onDirectionChange={setNotifDirection}
                dateRange={notifDateRange}
                selectedDateRange={notifDateRange}
                onDateRangeChange={setNotifDateRange}
              />

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <ActiveFilterChips 
                  filters={{
                    source: notifSource,
                    severity: notifSeverity,
                    importanceMin: notifImportanceMin,
                    direction: notifDirection,
                    readStatus: notifReadStatus,
                    dateRange: notifDateRange,
                    sort: notifSort
                  }}
                  onRemove={(key) => {
                    if (key === "source") setNotifSource("all");
                    if (key === "severity") setNotifSeverity(null);
                    if (key === "importanceMin") setNotifImportanceMin(null);
                    if (key === "direction") setNotifDirection(null);
                    if (key === "readStatus") setNotifReadStatus("all");
                    if (key === "dateRange") setNotifDateRange(null);
                    if (key === "sort") setNotifSort("latest");
                  }}
                />
                <SortDropdown value={notifSort} onChange={setNotifSort} />
              </div>

              {notificationsError ? (
                <div style={{ ...s.card, color: "#ef4444", border: "1px solid #ef444433", background: "#ef444408", padding: 30, textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
                  <div style={{ fontSize: 32 }}>⚠️</div>
                  <div style={{ fontSize: 15, fontWeight: "bold" }}>Failed to load notifications.</div>
                  <div style={{ fontSize: 12, color: "#94a3b8" }}>Please check if the backend server is running and try again.</div>
                  <button onClick={fetchNotifications} style={{ ...s.btnPrimary, minWidth: 100, cursor: "pointer" }}>Retry</button>
                </div>
              ) : notifications.length === 0 ? (
                <div style={{ textAlign: "center", padding: "60px 20px", color: "#475569", fontSize: 14, border: "1px dashed #1e293b", borderRadius: 12, background: "#0e1626", width: "100%", boxSizing: "border-box" }}>
                  <div style={{ fontSize: 32, marginBottom: 12 }}>📭</div>
                  <div style={{ color: "#cbd5e1", fontWeight: 600, marginBottom: 6 }}>No notifications match the selected filters.</div>
                  <div style={{ color: "#64748b", fontSize: 12, marginBottom: 16 }}>Try clearing filters or selecting another source.</div>
                  <button 
                    onClick={() => {
                      setNotifSeverity(null);
                      setNotifImportanceMin(null);
                      setNotifDirection(null);
                      setNotifReadStatus("all");
                      setNotifSource("all");
                      setNotifDateRange(null);
                      setNotifSort("latest");
                    }} 
                    style={{ ...s.btnPrimary, margin: "0 auto" }}
                  >
                    Clear Filters
                  </button>
                </div>
              ) : (
                <div style={s.grid2}>
                  {notifications.map((n, i) => {
                    const timeInfo = formatTimestamp(n.posted_at || n.fetched_at, now);
                    const isSummaryLoadingForThis = selectedNotificationForSummary?.id === n.id && selectedNotificationForSummary?.loading;

                    return (
                      <div key={n.id || i} style={{ 
                        ...s.card, 
                        borderLeft: `3px solid ${n.is_read ? "#334155" : "#06b6d4"}`,
                        padding: "18px 20px",
                        display: "flex",
                        flexDirection: "column",
                        gap: 12
                      }}>
                        {/* Title */}
                        <div style={{ 
                          fontSize: 14, 
                          fontWeight: 700, 
                          color: n.is_read ? "#94a3b8" : "#f1f5f9", 
                          lineHeight: 1.4,
                          flex: 1
                        }}>
                          {n?.title}
                        </div>

                        {/* Published Time, Age, and Severity Badge */}
                        <div style={{ fontSize: 11, color: "#64748b", display: "flex", flexDirection: "column", gap: 3 }}>
                          <div>Published: <span style={{ color: "#cbd5e1" }}>{timeInfo.dateTimeStr}</span></div>
                          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                            <span>Age: <span style={{ color: "#cbd5e1" }}>{timeInfo.ageStr}</span></span>
                            {n.importance_score !== undefined && n.importance_score !== null && (
                              <ImportanceBadge score={n.importance_score} />
                            )}
                          </div>
                        </div>

                        {/* Metadata Tag Row */}
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center", marginTop: 4 }}>
                          {/* Watchlist keyword */}
                          <span style={{ 
                            fontSize: 10, 
                            fontWeight: 700, 
                            color: "#8b5cf6", 
                            background: "#8b5cf612", 
                            border: "1px solid #8b5cf622",
                            padding: "2px 8px", 
                            borderRadius: 4 
                          }}>
                            ⭐ {n?.keyword}
                          </span>

                          {/* Source badge */}
                          {n?.source && (
                            <SourceBadge source_id={n.source} />
                          )}

                          {/* Sentiment badge */}
                          {n?.sentiment && (
                            <SentimentBadge sentiment={n.sentiment} />
                          )}
                        </div>

                        {/* Actions Footer */}
                        <div style={{ 
                          display: "flex", 
                          justifyContent: "space-between", 
                          alignItems: "center", 
                          borderTop: "1px solid #1e293b", 
                          paddingTop: 12,
                          marginTop: 4,
                          flexWrap: "wrap",
                          gap: 12
                        }}>
                          {/* Article link */}
                          <div>
                            {n?.post_url ? (
                              <a 
                                href={n.post_url} 
                                target="_blank" 
                                rel="noopener noreferrer" 
                                style={{ 
                                  fontSize: 11, 
                                  color: "#06b6d4", 
                                  textDecoration: "none", 
                                  fontWeight: 600,
                                  display: "inline-flex",
                                  alignItems: "center",
                                  gap: 4
                                }}
                                onMouseEnter={e => e.target.style.textDecoration = "underline"}
                                onMouseLeave={e => e.target.style.textDecoration = "none"}
                              >
                                🔗 Open Original Article
                              </a>
                            ) : (
                              <span style={{ fontSize: 10, color: "#475569" }}>No link available</span>
                            )}
                          </div>

                          {/* Buttons */}
                          <div style={{ display: "flex", gap: 8 }}>
                            <button 
                              onClick={() => summarizeNotification(n.id)} 
                              disabled={isSummaryLoadingForThis || !n.id} 
                              style={{ 
                                fontSize: 11, 
                                fontWeight: 700,
                                color: "#a855f7", 
                                background: "none", 
                                border: "1px solid #a855f744", 
                                borderRadius: 6, 
                                padding: "5px 12px", 
                                cursor: (isSummaryLoadingForThis || !n.id) ? "default" : "pointer", 
                                opacity: (isSummaryLoadingForThis || !n.id) ? 0.6 : 1,
                                transition: "all 0.15s"
                              }}
                              onMouseEnter={e => { if (!isSummaryLoadingForThis && n.id) e.target.style.background = "#a855f710"; }}
                              onMouseLeave={e => { e.target.style.background = "none"; }}
                            >
                              {isSummaryLoadingForThis ? "Summarizing..." : "Summarize with AI 🤖"}
                            </button>

                            <button 
                              onClick={() => markAsRead(n.id, n.is_read)} 
                              disabled={n.is_read || !n.id}
                              style={{ 
                                fontSize: 11, 
                                fontWeight: 700, 
                                padding: "5px 12px", 
                                borderRadius: 6, 
                                background: n.is_read ? "#1e293b" : "#06b6d418", 
                                color: n.is_read ? "#475569" : "#06b6d4", 
                                border: `1px solid ${n.is_read ? "#334155" : "#06b6d444"}`, 
                                cursor: n.is_read ? "default" : "pointer",
                                transition: "all 0.15s"
                              }}
                              onMouseEnter={e => { if (!n.is_read && n.id) e.target.style.background = "#06b6d425"; }}
                              onMouseLeave={e => { if (!n.is_read && n.id) e.target.style.background = "#06b6d418"; }}
                            >
                              {n.is_read ? "Read" : "Mark as Read"}
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}


          {/* MARKETBEACON COPILOT */}
          {activeSection === "ask" && (
            <div style={{
              display: "grid",
              gridTemplateColumns: (activeCompanyResearch || companyResearchLoading) ? "220px 1fr 480px" : "240px 1fr",
              gap: 20,
              minHeight: "calc(100vh - 180px)",
              transition: "grid-template-columns 0.3s ease"
            }}>
              
              {/* Chat History Sidebar */}
              <div style={{
                background: "#0a0f1d",
                border: "1px solid #121b2e",
                borderRadius: 12,
                padding: "16px 12px",
                display: "flex",
                flexDirection: "column",
                gap: 12,
                height: "600px",
                overflowY: "auto"
              }}>
                <button 
                  onClick={startNewChat}
                  style={{
                    ...s.btnPrimary,
                    background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
                    justifyContent: "center",
                    padding: "8px 12px",
                    fontSize: 12
                  }}
                >
                  ➕ New Conversation
                </button>
                
                <h4 style={{ fontSize: 11, color: "#475569", textTransform: "uppercase", letterSpacing: "0.08em", margin: "12px 0 4px 4px", fontWeight: 700 }}>
                  Recent Conversations
                </h4>
                
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {chatSessions.length === 0 ? (
                    <span style={{ fontSize: 11, color: "#475569", padding: "8px" }}>No history yet</span>
                  ) : (
                    chatSessions.map(sessionItem => (
                      <div 
                        key={sessionItem.session_id}
                        onClick={() => loadChatSession(sessionItem.session_id)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          padding: "8px 12px",
                          borderRadius: 8,
                          background: activeSessionId === sessionItem.session_id ? "#06b6d412" : "transparent",
                          cursor: "pointer",
                          transition: "all 0.15s",
                          border: activeSessionId === sessionItem.session_id ? "1px solid #06b6d444" : "1px solid transparent"
                        }}
                        onMouseEnter={e => {
                          if (activeSessionId !== sessionItem.session_id) {
                            e.currentTarget.style.background = "#1e293b55";
                          }
                        }}
                        onMouseLeave={e => {
                          if (activeSessionId !== sessionItem.session_id) {
                            e.currentTarget.style.background = "transparent";
                          }
                        }}
                      >
                        <span style={{
                          fontSize: 12,
                          color: activeSessionId === sessionItem.session_id ? "#06b6d4" : "#94a3b8",
                          fontWeight: activeSessionId === sessionItem.session_id ? 600 : 500,
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          flex: 1,
                          marginRight: 8
                        }}>
                          💬 {sessionItem.title}
                        </span>
                        <button
                          onClick={(e) => deleteChatSession(sessionItem.session_id, e)}
                          style={{
                            background: "none",
                            border: "none",
                            color: "#ef4444",
                            cursor: "pointer",
                            fontSize: 11,
                            padding: 2,
                            opacity: 0.6
                          }}
                          onMouseEnter={e => e.currentTarget.style.opacity = 1}
                          onMouseLeave={e => e.currentTarget.style.opacity = 0.6}
                          title="Delete Session"
                        >
                          🗑️
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Main Chat Interface */}
              <div style={{
                background: "#0e1626",
                border: "1px solid #121b2e",
                borderRadius: 12,
                display: "flex",
                flexDirection: "column",
                height: "600px",
                overflow: "hidden"
              }}>
                
                {/* Header */}
                <div style={{
                  padding: "16px 20px",
                  borderBottom: "1px solid #121b2e",
                  background: "#0a0f1d",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between"
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontSize: 20 }}>🤖</span>
                    <div>
                      <h4 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: "#f8fafc" }}>
                        MarketBeacon Copilot
                      </h4>
                      <p style={{ margin: 0, fontSize: 10, color: "#64748b" }}>
                        Elite Financial RAG Assistant with Multi-Turn Memory
                      </p>
                    </div>
                  </div>
                  {activeSessionId && (
                    <button 
                      onClick={startNewChat}
                      style={{
                        background: "none",
                        border: "1px solid #334155",
                        borderRadius: 6,
                        color: "#94a3b8",
                        padding: "4px 10px",
                        fontSize: 11,
                        cursor: "pointer"
                      }}
                      onMouseEnter={e => e.currentTarget.style.borderColor = "#06b6d4"}
                      onMouseLeave={e => e.currentTarget.style.borderColor = "#334155"}
                    >
                      Clear Chat
                    </button>
                  )}
                </div>

                {/* Message Log */}
                <div style={{
                  flex: 1,
                  padding: 20,
                  overflowY: "auto",
                  display: "flex",
                  flexDirection: "column",
                  gap: 16
                }}>
                  {chatMessages.length === 0 ? (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", textAlign: "center", color: "#475569", padding: "40px 20px" }}>
                      <span style={{ fontSize: 44, marginBottom: 16 }}>💼</span>
                      <h4 style={{ color: "#cbd5e1", margin: "0 0 6px 0", fontSize: 15 }}>Welcome to MarketBeacon Copilot</h4>
                      <p style={{ maxWidth: 420, fontSize: 12, margin: 0, lineHeight: 1.6 }}>
                        Ask me deep financial questions, analyze company performance, or research sector catalysts. Examples:
                      </p>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", marginTop: 16, maxWidth: 460 }}>
                        {["Analyze HDFC Bank", "What are Tata Motors biggest growth risks?", "Summarize banking sector valuation and outlook"].map(ex => (
                          <button
                            key={ex}
                            onClick={() => sendCopilotMessage(ex)}
                            style={{
                              background: "#111827",
                              border: "1px solid #1e293b",
                              borderRadius: 8,
                              color: "#06b6d4",
                              padding: "6px 12px",
                              fontSize: 11,
                              cursor: "pointer",
                              transition: "all 0.1s"
                            }}
                            onMouseEnter={e => e.currentTarget.style.background = "#1e293b"}
                            onMouseLeave={e => e.currentTarget.style.background = "#111827"}
                          >
                            "{ex}"
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    chatMessages.map((msg, index) => {
                      const isUser = msg.role === "user";
                      return (
                        <div key={msg.id || index} style={{
                          display: "flex",
                          flexDirection: "column",
                          alignSelf: isUser ? "flex-end" : "flex-start",
                          maxWidth: "85%",
                          gap: 6
                        }}>
                           {/* Sender name & time */}
                           <div style={{ display: "flex", alignItems: "center", gap: 6, alignSelf: isUser ? "flex-end" : "flex-start" }}>
                             <span style={{
                               fontSize: 9,
                               color: "#64748b",
                               fontWeight: 700,
                               letterSpacing: "0.04em"
                             }}>
                               {isUser ? "YOU" : "COPILOT"}
                             </span>
                             {!isUser && msg.research_quality_badge && (
                               <span style={{
                                 fontSize: 8,
                                 fontWeight: 800,
                                 textTransform: "uppercase",
                                 padding: "1px 4px",
                                 borderRadius: 3,
                                 background: msg.research_quality_badge === "High Confidence" ? "rgba(16, 185, 129, 0.1)" : msg.research_quality_badge === "Medium Confidence" ? "rgba(245, 158, 11, 0.1)" : "rgba(239, 68, 68, 0.1)",
                                 border: msg.research_quality_badge === "High Confidence" ? "1px solid rgba(16, 185, 129, 0.3)" : msg.research_quality_badge === "Medium Confidence" ? "1px solid rgba(245, 158, 11, 0.3)" : "1px solid rgba(239, 68, 68, 0.3)",
                                 color: msg.research_quality_badge === "High Confidence" ? "#10b981" : msg.research_quality_badge === "Medium Confidence" ? "#f59e0b" : "#ef4444"
                               }}>
                                 {msg.research_quality_badge}
                               </span>
                             )}
                           </div>

                          {/* Message Bubble */}
                          <div style={{
                            background: isUser ? "linear-gradient(135deg, #1e1b4b, #312e81)" : "#111827",
                            border: isUser ? "1px solid #3730a3" : "1px solid #1e293b",
                            borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                            padding: "12px 16px",
                            color: "#f1f5f9",
                            fontSize: 13,
                            lineHeight: 1.6,
                            whiteSpace: "pre-line"
                          }}>
                            {msg.content}
                          </div>

                          {/* Actions / Add-ons for Copilot Responses */}
                          {!isUser && (
                            <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 4 }}>
                              
                              {/* Copy & Regenerate Actions row */}
                              <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                                <button
                                  onClick={() => {
                                    navigator.clipboard.writeText(msg.content);
                                    showToast("Copied to clipboard!");
                                  }}
                                  style={{
                                    background: "none",
                                    border: "none",
                                    color: "#64748b",
                                    fontSize: 10,
                                    fontWeight: 700,
                                    cursor: "pointer"
                                  }}
                                  onMouseEnter={e => e.currentTarget.style.color = "#06b6d4"}
                                  onMouseLeave={e => e.currentTarget.style.color = "#64748b"}
                                >
                                  📋 Copy Response
                                </button>
                                {index === chatMessages.length - 1 && (
                                  <button
                                    onClick={handleRegenerateCopilot}
                                    style={{
                                      background: "none",
                                      border: "none",
                                      color: "#64748b",
                                      fontSize: 10,
                                      fontWeight: 700,
                                      cursor: "pointer"
                                    }}
                                    onMouseEnter={e => e.currentTarget.style.color = "#06b6d4"}
                                    onMouseLeave={e => e.currentTarget.style.color = "#64748b"}
                                  >
                                    🔄 Regenerate
                                  </button>
                                )}
                              </div>

                              {/* Watchlist Integration */}
                              {msg.detected_company && (
                                <div style={{ alignSelf: "flex-start" }}>
                                  <button
                                    onClick={() => handleAddCompanyToWatchlist(msg.detected_company)}
                                    style={{
                                      background: "rgba(6, 182, 212, 0.1)",
                                      border: "1px solid rgba(6, 182, 212, 0.3)",
                                      borderRadius: 6,
                                      color: "#06b6d4",
                                      padding: "4px 10px",
                                      fontSize: 11,
                                      fontWeight: 700,
                                      cursor: "pointer",
                                      display: "inline-flex",
                                      alignItems: "center",
                                      gap: 4
                                    }}
                                    onMouseEnter={e => e.currentTarget.style.background = "rgba(6, 182, 212, 0.2)"}
                                    onMouseLeave={e => e.currentTarget.style.background = "rgba(6, 182, 212, 0.1)"}
                                  >
                                    ⭐ Follow {msg.detected_company} in Watchlist
                                  </button>
                                </div>
                              )}

                              {/* Source Citations panel */}
                              {msg.sources && msg.sources.length > 0 && (
                                <div style={{
                                  background: "#0a0f1d",
                                  border: "1px solid #121b2e",
                                  borderRadius: 8,
                                  padding: 10,
                                  alignSelf: "flex-start",
                                  width: "100%"
                                }}>
                                  <span style={{ fontSize: 9, fontWeight: 800, color: "#64748b", display: "block", marginBottom: 6, textTransform: "uppercase" }}>
                                    📚 Reference Sources Used
                                  </span>
                                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                                    {msg.sources.map((src, sIdx) => (
                                      <div key={sIdx} style={{ fontSize: 11, color: "#94a3b8", display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                                        <span style={{ color: "#64748b" }}>•</span>
                                        {src.url ? (
                                          <a href={src.url} target="_blank" rel="noreferrer" style={{ color: "#06b6d4", textDecoration: "none", fontWeight: 500 }}
                                             onMouseEnter={e => e.target.style.textDecoration = "underline"}
                                             onMouseLeave={e => e.target.style.textDecoration = "none"}>
                                            {src.title}
                                          </a>
                                        ) : (
                                          <span style={{ color: "#06b6d4", fontWeight: 500 }}>
                                            {src.title}
                                          </span>
                                        )}
                                        <span style={{ fontSize: 9, color: "#475569" }}>({src.source})</span>
                                        {src.source_tier_label && (
                                          <span style={{ 
                                            fontSize: 8, 
                                            fontWeight: 700, 
                                            padding: "1px 4px", 
                                            borderRadius: 3, 
                                            background: src.source_tier === 1 ? "rgba(16, 185, 129, 0.1)" : src.source_tier === 2 ? "rgba(6, 182, 212, 0.1)" : src.source_tier === 3 ? "rgba(245, 158, 11, 0.1)" : "rgba(239, 68, 68, 0.1)",
                                            border: src.source_tier === 1 ? "1px solid rgba(16, 185, 129, 0.3)" : src.source_tier === 2 ? "1px solid rgba(6, 182, 212, 0.3)" : src.source_tier === 3 ? "1px solid rgba(245, 158, 11, 0.3)" : "1px solid rgba(239, 68, 68, 0.3)",
                                            color: src.source_tier === 1 ? "#10b981" : src.source_tier === 2 ? "#06b6d4" : src.source_tier === 3 ? "#f59e0b" : "#ef4444"
                                          }}>
                                            {src.source_tier_label}
                                          </span>
                                        )}
                                        
                                        {src.text && (
                                          <button
                                            onClick={() => {
                                              setSelectedSourceTitle(src.title || src.source_file);
                                              setSelectedSourceText(src.text);
                                            }}
                                            style={{
                                              background: "rgba(6, 182, 212, 0.1)",
                                              border: "1px solid rgba(6, 182, 212, 0.3)",
                                              borderRadius: 4,
                                              padding: "1px 5px",
                                              fontSize: 9,
                                              color: "#06b6d4",
                                              cursor: "pointer"
                                            }}
                                            onMouseEnter={e => e.target.style.background = "rgba(6, 182, 212, 0.2)"}
                                            onMouseLeave={e => e.target.style.background = "rgba(6, 182, 212, 0.1)"}
                                          >
                                            View Evidence 📖
                                          </button>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Suggested Followups */}
                              {index === chatMessages.length - 1 && msg.suggested_followups && msg.suggested_followups.length > 0 && (
                                <div style={{ marginTop: 6 }}>
                                  <span style={{ fontSize: 10, color: "#64748b", fontWeight: "bold", display: "block", marginBottom: 6 }}>
                                    Suggested follow-up research questions:
                                  </span>
                                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                                    {msg.suggested_followups.map((qText, qIdx) => (
                                      <button
                                        key={qIdx}
                                        onClick={() => sendCopilotMessage(qText)}
                                        style={{
                                          background: "#0a0f1d",
                                          border: "1px solid #121b2e",
                                          color: "#94a3b8",
                                          borderRadius: 20,
                                          padding: "5px 12px",
                                          fontSize: 10,
                                          fontWeight: 600,
                                          cursor: "pointer",
                                          transition: "all 0.1s"
                                        }}
                                        onMouseEnter={e => {
                                          e.currentTarget.style.color = "#06b6d4";
                                          e.currentTarget.style.borderColor = "#06b6d455";
                                          e.currentTarget.style.background = "#06b6d405";
                                        }}
                                        onMouseLeave={e => {
                                          e.currentTarget.style.color = "#94a3b8";
                                          e.currentTarget.style.borderColor = "#121b2e";
                                          e.currentTarget.style.background = "#0a0f1d";
                                        }}
                                      >
                                        {qText} →
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              )}

                            </div>
                          )}
                        </div>
                      );
                    })
                  )}

                  {/* Typing Indicator */}
                  {copilotLoading && (
                    <div style={{
                      display: "flex",
                      flexDirection: "column",
                      alignSelf: "flex-start",
                      gap: 6
                    }}>
                      <span style={{ fontSize: 9, color: "#64748b", fontWeight: 700 }}>COPILOT</span>
                      <div style={{
                        background: "#111827",
                        border: "1px solid #1e293b",
                        borderRadius: "16px 16px 16px 4px",
                        padding: "12px 16px",
                        display: "flex",
                        alignItems: "center",
                        gap: 4
                      }}>
                        <span style={s.spinner} />
                        <span style={{ fontSize: 12, color: "#94a3b8" }}>Deep market research copilot is analyzing databases...</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer Input Area */}
                <div style={{
                  padding: "16px 20px",
                  borderTop: "1px solid #121b2e",
                  background: "#0a0f1d",
                  display: "flex",
                  flexDirection: "column",
                  gap: 12
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                      <input 
                        type="checkbox"
                        checked={deepResearchEnabled}
                        onChange={e => setDeepResearchEnabled(e.target.checked)}
                        style={{ accentColor: "#a855f7", cursor: "pointer" }}
                      />
                      <span style={{
                        fontSize: 11,
                        fontWeight: 700,
                        color: deepResearchEnabled ? "#a855f7" : "#64748b",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 4
                      }}>
                        ⚡ Deep Research Mode
                      </span>
                    </label>
                    <span style={{ fontSize: 10, color: "#475569" }}>
                      Press Enter to submit question
                    </span>
                  </div>

                  <div style={{ display: "flex", gap: 12 }}>
                    <textarea 
                      rows={1}
                      value={question} 
                      onChange={e => setQuestion(e.target.value)} 
                      onKeyDown={e => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          sendCopilotMessage(question);
                        }
                      }}
                      placeholder="Ask copilot about HDFC Bank, Tata Motors, or macro sector risks..." 
                      style={{ 
                        ...s.input, 
                        flex: 1, 
                        resize: "none", 
                        lineHeight: 1.4, 
                        background: "#050811",
                        borderColor: "#1e293b"
                      }} 
                    />
                    <button 
                      onClick={() => sendCopilotMessage(question)} 
                      disabled={copilotLoading || !question.trim()} 
                      style={{ 
                        ...s.btnPrimary, 
                        opacity: (copilotLoading || !question.trim()) ? 0.5 : 1,
                        cursor: (copilotLoading || !question.trim()) ? "default" : "pointer",
                        background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
                        padding: "0 20px"
                      }}
                    >
                      Send →
                    </button>
                  </div>
                </div>

              </div>

              {/* Right Column: Company Analysis Dashboard */}
              {(activeCompanyResearch || companyResearchLoading) && (
                <div style={{
                  background: "#0e1626",
                  border: "1px solid #121b2e",
                  borderRadius: 12,
                  display: "flex",
                  flexDirection: "column",
                  height: "600px",
                  overflow: "hidden"
                }}>
                  {/* Panel Header */}
                  <div style={{
                    padding: "14px 16px",
                    background: "#0a0f1d",
                    borderBottom: "1px solid #121b2e",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between"
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: 18 }}>📊</span>
                      <div>
                        <h4 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: "#f8fafc" }}>
                          {activeCompanyResearch ? `${activeCompanyResearch} Intelligence` : "Analyzing Company..."}
                        </h4>
                        {companyResearchData && (
                          <p style={{ margin: 0, fontSize: 9, color: "#64748b" }}>
                            {companyResearchData.sector || "Sector"} • {companyResearchData.industry || "Industry"}
                          </p>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setActiveCompanyResearch(null);
                        setCompanyResearchData(null);
                      }}
                      style={{
                        background: "none",
                        border: "none",
                        color: "#64748b",
                        cursor: "pointer",
                        fontSize: 14
                      }}
                      title="Close Analysis Panel"
                    >
                      ✕
                    </button>
                  </div>

                  {/* lookup search bar inside the panel */}
                  <div style={{
                    padding: "10px 16px",
                    background: "#080c16",
                    borderBottom: "1px solid #121b2e",
                    display: "flex",
                    gap: 8
                  }}>
                    <input
                      type="text"
                      placeholder="Lookup another company..."
                      value={researchLookupQuery}
                      onChange={e => setResearchLookupQuery(e.target.value)}
                      onKeyDown={e => {
                        if (e.key === "Enter" && researchLookupQuery.trim()) {
                          fetchCompanyResearch(researchLookupQuery.trim());
                          setResearchLookupQuery("");
                        }
                      }}
                      style={{
                        ...s.input,
                        padding: "4px 8px",
                        fontSize: 11,
                        background: "#050811",
                        borderColor: "#1e293b",
                        flex: 1
                      }}
                    />
                    <button
                      onClick={() => {
                        if (researchLookupQuery.trim()) {
                          fetchCompanyResearch(researchLookupQuery.trim());
                          setResearchLookupQuery("");
                        }
                      }}
                      style={{
                        ...s.btnPrimary,
                        padding: "4px 10px",
                        fontSize: 10,
                        background: "linear-gradient(135deg, #06b6d4, #3b82f6)"
                      }}
                    >
                      Go
                    </button>
                  </div>

                  {companyResearchLoading ? (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flex: 1, padding: 24, textAlign: "center" }}>
                      <span style={{ ...s.spinnerBig, marginBottom: 16 }} />
                      <h5 style={{ color: "#cbd5e1", margin: "0 0 6px 0", fontSize: 13 }}>Compiling Company Dossier</h5>
                      <p style={{ fontSize: 11, color: "#64748b", maxWidth: 280, margin: 0, lineHeight: 1.5 }}>
                        Analyzing research reports, news feeds, smart alerts, and peer groups to build scorecard & timeline...
                      </p>
                    </div>
                  ) : !companyResearchData ? (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flex: 1, padding: 24, textAlign: "center", color: "#64748b" }}>
                      <span style={{ fontSize: 32, marginBottom: 12 }}>🔍</span>
                      <p style={{ fontSize: 11, margin: 0 }}>No data compiled yet. Ask Copilot to analyze a company or search above.</p>
                    </div>
                  ) : (
                    <>
                      {/* Sub-navigation Tabs */}
                      <div style={{
                        display: "flex",
                        background: "#0a0f1d",
                        borderBottom: "1px solid #121b2e",
                        padding: "0 8px"
                      }}>
                        {[
                          { id: "scorecard", label: "📊 Scorecard" },
                          { id: "timeline", label: "📅 Timeline" },
                          { id: "peers", label: "⚖️ Peers" },
                          { id: "dossier", label: "📝 Dossier" }
                        ].map(t => (
                          <button
                            key={t.id}
                            onClick={() => setCompanyResearchTab(t.id)}
                            style={{
                              flex: 1,
                              background: "none",
                              border: "none",
                              borderBottom: companyResearchTab === t.id ? "2px solid #06b6d4" : "2px solid transparent",
                              color: companyResearchTab === t.id ? "#06b6d4" : "#64748b",
                              padding: "8px 0",
                              fontSize: 11,
                              fontWeight: 600,
                              cursor: "pointer",
                              transition: "all 0.15s"
                            }}
                          >
                            {t.label}
                          </button>
                        ))}
                      </div>

                      {/* Tab Content Container */}
                      <div style={{
                        flex: 1,
                        overflowY: "auto",
                        padding: 16,
                        display: "flex",
                        flexDirection: "column",
                        gap: 16,
                        boxSizing: "border-box"
                      }}>
                        
                        {/* Research Confidence Summary Banner */}
                        {(() => {
                          const conf = companyResearchData.confidence_score || 85;
                          let badge = companyResearchData.research_quality_badge;
                          if (!badge) {
                            if (conf >= 75) badge = "High Confidence";
                            else if (conf >= 40) badge = "Medium Confidence";
                            else badge = "Limited Evidence";
                          }

                          const badgeStyles = badge === "High Confidence"
                            ? { bg: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.3)", color: "#10b981" }
                            : badge === "Medium Confidence"
                            ? { bg: "rgba(245, 158, 11, 0.08)", border: "1px solid rgba(245, 158, 11, 0.3)", color: "#f59e0b" }
                            : { bg: "rgba(239, 68, 68, 0.08)", border: "1px solid rgba(239, 68, 68, 0.3)", color: "#ef4444" };

                          return (
                            <div style={{
                              background: "rgba(6, 182, 212, 0.04)",
                              border: "1px solid rgba(6, 182, 212, 0.15)",
                              borderRadius: 8,
                              padding: "10px 12px",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "space-between"
                            }}>
                              <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                                <span style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", fontWeight: 700, display: "block" }}>
                                  Research Confidence
                                </span>
                                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                  <span style={{ fontSize: 16, fontWeight: 800, color: "#06b6d4" }}>
                                    {conf}%
                                  </span>
                                  <span style={{ 
                                    fontSize: 8, 
                                    fontWeight: 800, 
                                    textTransform: "uppercase", 
                                    padding: "2px 6px", 
                                    borderRadius: 4, 
                                    background: badgeStyles.bg, 
                                    border: badgeStyles.border, 
                                    color: badgeStyles.color
                                  }}>
                                    {badge}
                                  </span>
                                </div>
                              </div>
                              <div style={{ textAlign: "right", fontSize: 9, color: "#94a3b8" }}>
                                <span style={{ display: "block" }}>✔ Multi-Source (Alerts + Reports)</span>
                                <span style={{ display: "block" }}>✔ Real-time Recency Checks</span>
                              </div>
                            </div>
                          );
                        })()}

                        {/* 1. SCORECARD TAB */}
                        {companyResearchTab === "scorecard" && (
                          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                            <h5 style={{ margin: "0 0 4px 0", fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                              Evidence-Backed Scorecard
                            </h5>
                            
                            {companyResearchData.scorecard ? (
                              Object.entries(companyResearchData.scorecard).map(([key, val]) => {
                                if (key === "overall") return null;
                                const score = val.score || 0;
                                const explanation = val.explanation || "";
                                const formattedKey = key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                                
                                return (
                                  <div key={key} style={{
                                    background: "#111827",
                                    border: "1px solid #1e293b",
                                    borderRadius: 8,
                                    padding: 10
                                  }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                                      <span style={{ fontSize: 12, fontWeight: 700, color: "#f1f5f9" }}>{formattedKey}</span>
                                      <span style={{ fontSize: 11, fontWeight: 800, color: "#06b6d4" }}>{score}/100</span>
                                    </div>
                                    {/* Progress bar background */}
                                    <div style={{ height: 6, background: "#1e293b", borderRadius: 3, overflow: "hidden", marginBottom: 8 }}>
                                      <div style={{ width: `${score}%`, height: "100%", background: "linear-gradient(90deg, #06b6d4, #3b82f6)", borderRadius: 3 }} />
                                    </div>
                                    {explanation && (
                                      <p style={{ fontSize: 10, color: "#94a3b8", margin: 0, lineHeight: 1.4 }}>
                                        <strong>Why:</strong> {explanation}
                                      </p>
                                    )}
                                  </div>
                                );
                              })
                            ) : (
                              <p style={{ fontSize: 11, color: "#64748b" }}>No scorecard available.</p>
                            )}

                            {companyResearchData.scorecard?.overall && (
                              <div style={{
                                marginTop: 8,
                                background: "linear-gradient(135deg, #1e1b4b, #111827)",
                                border: "1px solid #3730a3",
                                borderRadius: 8,
                                padding: 12,
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center"
                              }}>
                                <span style={{ fontSize: 12, fontWeight: 800, color: "#a855f7" }}>Composite Overall Score</span>
                                <span style={{ fontSize: 18, fontWeight: 900, color: "#a855f7" }}>
                                  {companyResearchData.scorecard.overall}/100
                                </span>
                              </div>
                            )}
                          </div>
                        )}

                        {/* 2. TIMELINE TAB */}
                        {companyResearchTab === "timeline" && (
                          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                            <h5 style={{ margin: "0 0 4px 0", fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                              Milestones & Guidance Timeline
                            </h5>
                            
                            {companyResearchData.timeline && companyResearchData.timeline.length > 0 ? (
                              <div style={{ display: "flex", flexDirection: "column", gap: 10, borderLeft: "2px solid #1e293b", paddingLeft: 12, marginLeft: 6 }}>
                                {companyResearchData.timeline.map((item, idx) => {
                                  const isBullish = item.impact?.toLowerCase() === "bullish";
                                  const isBearish = item.impact?.toLowerCase() === "bearish";
                                  const badgeColor = isBullish ? "#10b981" : isBearish ? "#ef4444" : "#94a3b8";
                                  const badgeBg = isBullish ? "rgba(16, 185, 129, 0.1)" : isBearish ? "rgba(239, 68, 68, 0.1)" : "rgba(148, 163, 184, 0.1)";

                                  return (
                                    <div key={idx} style={{ position: "relative" }}>
                                      {/* Timeline Node Dot */}
                                      <div style={{
                                        position: "absolute",
                                        left: -17,
                                        top: 4,
                                        width: 8,
                                        height: 8,
                                        borderRadius: "50%",
                                        background: badgeColor,
                                        border: "2px solid #0e1626"
                                      }} />
                                      
                                      <div style={{ fontSize: 10, color: "#64748b", fontWeight: 700, marginBottom: 2 }}>
                                        🕒 {item.date}
                                      </div>
                                      <div style={{ fontSize: 12, color: "#e2e8f0", lineHeight: 1.4, marginBottom: 4 }}>
                                        {item.event}
                                      </div>
                                      <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                                        <span style={{
                                          fontSize: 9,
                                          fontWeight: 700,
                                          color: badgeColor,
                                          background: badgeBg,
                                          padding: "1px 5px",
                                          borderRadius: 4
                                        }}>
                                          {item.impact}
                                        </span>
                                        {item.source && (
                                          <span style={{ fontSize: 9, color: "#475569" }}>
                                            Source: {item.source}
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            ) : (
                              <p style={{ fontSize: 11, color: "#64748b" }}>No events in timeline.</p>
                            )}
                          </div>
                        )}

                        {/* 3. PEER COMPARISON TAB */}
                        {companyResearchTab === "peers" && (
                          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                            <h5 style={{ margin: "0 0 4px 0", fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                              Dynamic Peer Comparison Table
                            </h5>
                            
                            {companyResearchData.peer_comparison && companyResearchData.peer_comparison.length > 0 ? (
                              <div style={{ overflowX: "auto", border: "1px solid #121b2e", borderRadius: 8 }}>
                                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, textAlign: "left" }}>
                                  <thead>
                                    <tr style={{ background: "#0a0f1d", borderBottom: "1px solid #121b2e" }}>
                                      <th style={{ padding: "8px 10px", color: "#64748b" }}>Company</th>
                                      <th style={{ padding: "8px 10px", color: "#64748b" }}>Mcap</th>
                                      <th style={{ padding: "8px 10px", color: "#64748b" }}>Revenue</th>
                                      <th style={{ padding: "8px 10px", color: "#64748b" }}>Profit</th>
                                      <th style={{ padding: "8px 10px", color: "#64748b" }}>ROE</th>
                                      <th style={{ padding: "8px 10px", color: "#64748b" }}>Debt</th>
                                      <th style={{ padding: "8px 10px", color: "#64748b" }}>Valuation</th>
                                      <th style={{ padding: "8px 10px", color: "#64748b" }}>Growth</th>
                                      <th style={{ padding: "8px 10px", color: "#64748b" }}>As Of</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {companyResearchData.peer_comparison.map((peer, idx) => {
                                      const isTarget = peer.company?.toLowerCase() === activeCompanyResearch?.toLowerCase();
                                      return (
                                        <tr key={idx} style={{
                                          borderBottom: "1px solid #121b2e",
                                          background: isTarget ? "rgba(6, 182, 212, 0.05)" : "transparent"
                                        }}>
                                          <td style={{ padding: "8px 10px", color: isTarget ? "#06b6d4" : "#cbd5e1", fontWeight: isTarget ? 700 : 500 }}>
                                            {peer.company}
                                          </td>
                                          <td style={{ padding: "8px 10px", color: "#e2e8f0" }}>{peer.market_cap}</td>
                                          <td style={{ padding: "8px 10px", color: "#e2e8f0" }}>{peer.revenue}</td>
                                          <td style={{ padding: "8px 10px", color: "#e2e8f0" }}>{peer.profit}</td>
                                          <td style={{ padding: "8px 10px", color: "#e2e8f0" }}>{peer.roe}</td>
                                          <td style={{ padding: "8px 10px", color: "#e2e8f0" }}>{peer.debt}</td>
                                          <td style={{ padding: "8px 10px", color: "#e2e8f0" }}>{peer.valuation_metrics}</td>
                                          <td style={{ padding: "8px 10px", color: "#e2e8f0" }}>{peer.growth_metrics}</td>
                                          <td style={{ padding: "8px 10px", color: "#64748b", fontSize: 10 }}>{peer.freshness_date || "Real-time"}</td>
                                        </tr>
                                      );
                                    })}
                                  </tbody>
                                </table>
                              </div>
                            ) : (
                              <p style={{ fontSize: 11, color: "#64748b" }}>No peer comparisons compiled.</p>
                            )}
                          </div>
                        )}

                        {/* 4. DOSSIER TEXT TAB */}
                        {companyResearchTab === "dossier" && (
                          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                            <h5 style={{ margin: "0 0 4px 0", fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                              Executive Dossier Details
                            </h5>
                            
                            {companyResearchData.dossier ? (
                              Object.entries(companyResearchData.dossier).map(([key, val]) => {
                                const formattedKey = key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                                
                                // Support both legacy string format and new structured format with citations
                                let sectionText = "";
                                let citations = [];
                                if (typeof val === "string") {
                                  sectionText = val;
                                } else if (val && typeof val === "object") {
                                  sectionText = val.text || "";
                                  citations = val.citations || [];
                                }

                                return (
                                  <div key={key} style={{
                                    background: "#111827",
                                    border: "1px solid #1e293b",
                                    borderRadius: 8,
                                    padding: 12
                                  }}>
                                    <span style={{ fontSize: 11, fontWeight: 800, color: "#06b6d4", display: "block", marginBottom: 6, textTransform: "uppercase" }}>
                                      {formattedKey}
                                    </span>
                                    <p style={{ fontSize: 11, color: "#cbd5e1", margin: "0 0 8px 0", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
                                      {sectionText}
                                    </p>

                                    {/* Render collapsible supporting evidence citations */}
                                    {citations && citations.length > 0 && (
                                      <div style={{ marginTop: 8, borderTop: "1px solid #1e293b", paddingTop: 8 }}>
                                        <span style={{ fontSize: 9, fontWeight: 800, color: "#64748b", display: "block", marginBottom: 4, textTransform: "uppercase" }}>
                                          Evidence & Citations
                                        </span>
                                        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                                          {citations.map((cit, cIdx) => (
                                            <div key={cIdx} style={{ 
                                              background: "#080c16", 
                                              border: "1px solid #121b2e", 
                                              borderRadius: 6, 
                                              padding: "6px 10px", 
                                              fontSize: 10 
                                            }}>
                                              <div style={{ display: "flex", justifyContent: "space-between", color: "#94a3b8", fontWeight: 600, flexWrap: "wrap", gap: 6 }}>
                                                <span>📄 {cit.document || "Source Document"}</span>
                                                <span style={{ fontSize: 9, color: "#64748b" }}>Date: {cit.date || "N/A"} | Source: {cit.source || "External"}</span>
                                              </div>
                                              {cit.evidence && (
                                                <details style={{ marginTop: 4 }}>
                                                  <summary style={{ fontSize: 9, color: "#06b6d4", cursor: "pointer", userSelect: "none" }}>
                                                    Inspect Supporting Evidence
                                                  </summary>
                                                  <div style={{ 
                                                    marginTop: 4, 
                                                    padding: 6, 
                                                    background: "#0f172a", 
                                                    borderRadius: 4, 
                                                    color: "#94a3b8", 
                                                    fontStyle: "italic",
                                                    fontSize: 10,
                                                    lineHeight: 1.4
                                                  }}>
                                                    "{cit.evidence}"
                                                  </div>
                                                </details>
                                              )}
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                );
                              })
                            ) : (
                              <p style={{ fontSize: 11, color: "#64748b" }}>No textual sections compiled.</p>
                            )}
                          </div>
                        )}

                      </div>
                    </>
                  )}
                </div>
              )}

            </div>
          )}

          {/* RESEARCH LIBRARY */}
          {activeSection === "research_library" && (
            <div style={{ display: "grid", gridTemplateColumns: "350px 1fr", gap: 24, minHeight: "calc(100vh - 180px)" }}>
              
              {/* Left Column: Upload Document */}
              <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                <div style={{ ...s.card, background: "#0a0f1d" }}>
                  <h4 style={{ ...s.cardHeader, borderBottom: "1px solid #121b2e", paddingBottom: 12, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                    📤 Ingest Research Document
                  </h4>
                  
                  <form onSubmit={handleUploadDocument} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    
                    {/* File Selection */}
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      <label style={{ fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Select File (PDF, DOCX, TXT)</label>
                      <div style={{
                        border: "2px dashed #1e293b",
                        borderRadius: 8,
                        padding: "24px 16px",
                        textAlign: "center",
                        cursor: "pointer",
                        background: uploadFile ? "rgba(6, 182, 212, 0.05)" : "#050811",
                        borderColor: uploadFile ? "#06b6d4" : "#1e293b",
                        transition: "all 0.15s",
                        position: "relative"
                      }}
                      onMouseEnter={e => { if (!uploadFile) e.currentTarget.style.borderColor = "#06b6d455"; }}
                      onMouseLeave={e => { if (!uploadFile) e.currentTarget.style.borderColor = "#1e293b"; }}
                      >
                        <input 
                          type="file"
                          id="research-file-input"
                          accept=".pdf,.docx,.txt"
                          onChange={e => setUploadFile(e.target.files[0])}
                          style={{
                            position: "absolute",
                            top: 0,
                            left: 0,
                            width: "100%",
                            height: "100%",
                            opacity: 0,
                            cursor: "pointer"
                          }}
                        />
                        <span style={{ fontSize: 24, display: "block", marginBottom: 8 }}>📄</span>
                        <span style={{ fontSize: 12, color: "#94a3b8", display: "block", fontWeight: 600 }}>
                          {uploadFile ? uploadFile.name : "Click or Drag file to upload"}
                        </span>
                        <span style={{ fontSize: 10, color: "#475569", marginTop: 4, display: "block" }}>
                          Max size 10MB
                        </span>
                      </div>
                    </div>

                    {/* Company Name */}
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      <label style={{ fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Tag Company Name (Optional)</label>
                      <input 
                        type="text" 
                        value={uploadCompany} 
                        onChange={e => setUploadCompany(e.target.value)} 
                        placeholder="e.g. TCS, HDFC Bank, Tesla"
                        style={s.input}
                      />
                    </div>

                    {/* Document Type */}
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      <label style={{ fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Document Type</label>
                      <select 
                        value={uploadDocType} 
                        onChange={e => setUploadDocType(e.target.value)} 
                        style={{ ...s.input, background: "#050811" }}
                      >
                        <option value="Report">Research Report</option>
                        <option value="Earnings Call">Earnings Call Transcript</option>
                        <option value="Investor Presentation">Investor Presentation</option>
                        <option value="Annual Report">Annual Report</option>
                      </select>
                    </div>

                    {/* Submit Button */}
                    <button 
                      type="submit" 
                      disabled={uploadLoading || !uploadFile}
                      style={{ 
                        ...s.btnPrimary,
                        justifyContent: "center",
                        width: "100%",
                        opacity: (uploadLoading || !uploadFile) ? 0.5 : 1,
                        cursor: (uploadLoading || !uploadFile) ? "default" : "pointer",
                        background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
                        padding: "12px"
                      }}
                    >
                      {uploadLoading ? (
                        <>
                          <span style={s.spinner} /> Ingesting & Embedding...
                        </>
                      ) : "Ingest & Index 🚀"}
                    </button>

                  </form>
                </div>

                {/* Indexing Stats Box */}
                {indexingStats && (
                  <div style={{
                    ...s.card,
                    background: "rgba(16, 185, 129, 0.05)",
                    border: "1px solid rgba(16, 185, 129, 0.2)",
                    boxShadow: "0 0 16px rgba(16, 185, 129, 0.03)"
                  }}>
                    <h5 style={{ margin: "0 0 10px 0", color: "#10b981", fontSize: 12, fontWeight: 700, textTransform: "uppercase", display: "flex", alignItems: "center", gap: 6 }}>
                      ✅ Last Indexing Stats
                    </h5>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12, color: "#94a3b8" }}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>File Size:</span>
                        <strong style={{ color: "#f1f5f9" }}>{(indexingStats.total_bytes / 1024).toFixed(1)} KB</strong>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>Extracted Chars:</span>
                        <strong style={{ color: "#f1f5f9" }}>{indexingStats.extracted_characters.toLocaleString()}</strong>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>Total Chunks:</span>
                        <strong style={{ color: "#06b6d4" }}>{indexingStats.total_chunks} chunks</strong>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Right Column: Files List & Vector Search */}
              <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                
                {/* Search / Ingested Files Card */}
                <div style={{ ...s.card, background: "#0e1626" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #121b2e", paddingBottom: 16, marginBottom: 16 }}>
                    <div>
                      <h4 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: "#f1f5f9" }}>
                        📚 Ingested Knowledge Base
                      </h4>
                      <p style={{ margin: 0, fontSize: 11, color: "#64748b", marginTop: 2 }}>
                        Manage uploaded reports, presentations, and documents.
                      </p>
                    </div>
                  </div>

                  {/* Document Grid / Table */}
                  <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                    {researchDocs.length === 0 ? (
                      <div style={{ textAlign: "center", padding: "40px 20px", color: "#475569", background: "#070c16", borderRadius: 8, border: "1px dashed #121b2e" }}>
                        <span style={{ fontSize: 32, display: "block", marginBottom: 8 }}>📭</span>
                        <span style={{ fontSize: 12, fontWeight: 600 }}>No documents ingested yet</span>
                        <p style={{ margin: "4px 0 0 0", fontSize: 11 }}>Upload your first research report in the left sidebar.</p>
                      </div>
                    ) : (
                      <div style={{ overflowX: "auto" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, textAlign: "left" }}>
                          <thead>
                            <tr style={{ borderBottom: "1px solid #121b2e", color: "#64748b" }}>
                              <th style={{ padding: "8px 12px", fontWeight: 700 }}>Title</th>
                              <th style={{ padding: "8px 12px", fontWeight: 700 }}>Company</th>
                              <th style={{ padding: "8px 12px", fontWeight: 700 }}>Doc Type</th>
                              <th style={{ padding: "8px 12px", fontWeight: 700 }}>Upload Date</th>
                              <th style={{ padding: "8px 12px", fontWeight: 700 }}>Chunks</th>
                              <th style={{ padding: "8px 12px", fontWeight: 700 }}>Status</th>
                              <th style={{ padding: "8px 12px", fontWeight: 700, textAlign: "center" }}>Action</th>
                            </tr>
                          </thead>
                          <tbody>
                            {researchDocs.map(doc => (
                              <tr key={doc.id} style={{ borderBottom: "1px solid #121b2e", transition: "background 0.1s" }} onMouseEnter={e => e.currentTarget.style.background = "#1e293b33"} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                                <td style={{ padding: "12px", color: "#cbd5e1", fontWeight: 600 }}>
                                  📝 {doc.title}
                                </td>
                                <td style={{ padding: "12px" }}>
                                  {doc.company_name ? (
                                    <span style={{ background: "rgba(6, 182, 212, 0.1)", border: "1px solid rgba(6, 182, 212, 0.3)", borderRadius: 4, padding: "2px 6px", color: "#06b6d4", fontSize: 10, fontWeight: 700 }}>
                                      {doc.company_name}
                                    </span>
                                  ) : (
                                    <span style={{ color: "#475569" }}>None</span>
                                  )}
                                </td>
                                <td style={{ padding: "12px", color: "#94a3b8" }}>
                                  {doc.document_type}
                                </td>
                                <td style={{ padding: "12px", color: "#64748b" }}>
                                  {new Date(doc.upload_date).toLocaleDateString("en-IN", { day: 'numeric', month: 'short', year: 'numeric' })}
                                </td>
                                <td style={{ padding: "12px", color: "#06b6d4", fontWeight: 700 }}>
                                  {doc.chunk_count}
                                </td>
                                <td style={{ padding: "12px" }}>
                                  <span style={{
                                    display: "inline-flex",
                                    alignItems: "center",
                                    gap: 4,
                                    fontSize: 10,
                                    fontWeight: 700,
                                    padding: "2px 8px",
                                    borderRadius: 12,
                                    background: doc.status === "Indexed" ? "#10b98115" : doc.status === "Processing" ? "#fbbf2415" : "#ef444415",
                                    color: doc.status === "Indexed" ? "#10b981" : doc.status === "Processing" ? "#fbbf24" : "#ef4444",
                                    border: `1px solid ${doc.status === "Indexed" ? "#10b98133" : doc.status === "Processing" ? "#fbbf2433" : "#ef444433"}`
                                  }}>
                                    {doc.status}
                                  </span>
                                </td>
                                <td style={{ padding: "12px", textAlign: "center" }}>
                                  <button 
                                    onClick={() => handleDeleteResearchDoc(doc.id)}
                                    style={s.btnDelete}
                                    title="Delete Document"
                                  >
                                    🗑️ Delete
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </div>

                {/* Vector Search Sandbox */}
                <div style={{ ...s.card, background: "#0e1626" }}>
                  <h4 style={{ ...s.cardHeader, borderBottom: "1px solid #121b2e", paddingBottom: 16, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                    🔍 Vector Search RAG Sandbox
                  </h4>
                  
                  <form onSubmit={handleSearchResearchLibrary} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                    <div style={{ display: "flex", gap: 12 }}>
                      <input 
                        type="text" 
                        value={researchSearchQuery} 
                        onChange={e => setResearchSearchQuery(e.target.value)} 
                        placeholder="Search semantic chunks (e.g. 'What is HDFC profit margin?' or 'EV vehicle sales target')..."
                        style={{ ...s.input, flex: 1 }}
                      />
                      <button 
                        type="submit" 
                        disabled={researchSearchLoading || !researchSearchQuery.trim()}
                        style={{ 
                          ...s.btnPrimary,
                          opacity: (researchSearchLoading || !researchSearchQuery.trim()) ? 0.5 : 1,
                          cursor: (researchSearchLoading || !researchSearchQuery.trim()) ? "default" : "pointer",
                          background: "linear-gradient(135deg, #a855f7, #6366f1)"
                        }}
                      >
                        {researchSearchLoading ? <span style={s.spinner} /> : "Search Chunks ⚡"}
                      </button>
                    </div>

                    <div style={{ display: "flex", gap: 16, fontSize: 11, color: "#64748b" }}>
                      <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        Filter Company:
                        <select 
                          value={researchSearchCompany} 
                          onChange={e => setResearchSearchCompany(e.target.value)} 
                          style={s.dropdownSelect}
                        >
                          <option value="all">All Companies</option>
                          {[...new Set(researchDocs.map(d => d.company_name).filter(Boolean))].map(c => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </label>
                      <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        Filter Doc Type:
                        <select 
                          value={researchSearchDocType} 
                          onChange={e => setResearchSearchDocType(e.target.value)} 
                          style={s.dropdownSelect}
                        >
                          <option value="all">All Doc Types</option>
                          <option value="Report">Research Report</option>
                          <option value="Earnings Call">Earnings Call</option>
                          <option value="Investor Presentation">Investor Presentation</option>
                          <option value="Annual Report">Annual Report</option>
                        </select>
                      </label>
                    </div>
                  </form>

                  {/* Search Results Display */}
                  {researchSearchResults.length > 0 && (
                    <div style={{ marginTop: 20, display: "flex", flexDirection: "column", gap: 12 }}>
                      <h5 style={{ margin: "0 0 4px 0", fontSize: 12, fontWeight: 700, color: "#94a3b8", textTransform: "uppercase" }}>
                        Search Matches ({researchSearchResults.length} chunks retrieved from Qdrant)
                      </h5>
                      <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: "400px", overflowY: "auto" }}>
                        {researchSearchResults.map((resItem, resIdx) => (
                          <div key={resIdx} style={{
                            background: "#070c16",
                            border: "1px solid #121b2e",
                            borderRadius: 8,
                            padding: 14,
                            display: "flex",
                            flexDirection: "column",
                            gap: 8
                          }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #121b2e", paddingBottom: 6, fontSize: 11 }}>
                              <span style={{ color: "#cbd5e1", fontWeight: 700 }}>
                                📄 {resItem.source_file} (Chunk {resItem.chunk_index})
                              </span>
                              <span style={{
                                background: "rgba(168, 85, 247, 0.1)",
                                border: "1px solid rgba(168, 85, 247, 0.3)",
                                borderRadius: 12,
                                padding: "2px 8px",
                                color: "#c084fc",
                                fontWeight: 700
                              }}>
                                🎯 Similarity: {(resItem.score * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div style={{ fontSize: 12, color: "#94a3b8", lineHeight: 1.5, whiteSpace: "pre-line" }}>
                              {resItem.text}
                            </div>
                            <div style={{ display: "flex", gap: 8, fontSize: 10 }}>
                              <span style={{ background: "#1e293b", color: "#94a3b8", padding: "2px 6px", borderRadius: 4 }}>
                                Type: {resItem.document_type}
                              </span>
                              {resItem.company_name && (
                                <span style={{ background: "#1e293b", color: "#06b6d4", padding: "2px 6px", borderRadius: 4 }}>
                                  Company: {resItem.company_name}
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {researchSearchLoading && (
                    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", padding: "40px 0" }}>
                      <span style={s.spinnerBig} />
                      <span style={{ fontSize: 13, color: "#94a3b8", marginLeft: 12 }}>Semantic index search is traversing vector space...</span>
                    </div>
                  )}

                  {!researchSearchLoading && researchSearchQuery.trim() && researchSearchResults.length === 0 && (
                    <div style={{ textAlign: "center", padding: "24px 0", color: "#475569", fontSize: 12 }}>
                      No semantic chunks matched your query. Check filters or try expanding your keywords.
                    </div>
                  )}
                </div>

              </div>

            </div>
          )}

          {/* RAG EVALUATION DASHBOARD */}
          {activeSection === "evaluation_dashboard" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              
              {/* Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: "#f8fafc" }}>
                    📊 RAG Retrieval Quality & Evaluation Dashboard
                  </h3>
                  <p style={{ margin: 0, fontSize: 11, color: "#64748b" }}>
                    Internal metrics tracking retrieval latency, confidence accuracy, citation coverage, and source reliability.
                  </p>
                </div>
                <button 
                  onClick={fetchRAGMetrics} 
                  disabled={ragMetricsLoading}
                  style={{
                    ...s.btnPrimary,
                    background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
                    fontSize: 11,
                    padding: "6px 14px",
                    cursor: "pointer"
                  }}
                >
                  {ragMetricsLoading ? "Refreshing..." : "🔄 Refresh Metrics"}
                </button>
              </div>

              {ragMetricsLoading && !ragMetrics ? (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "80px 0" }}>
                  <span style={s.spinnerBig} />
                  <span style={{ fontSize: 12, color: "#94a3b8", marginTop: 12 }}>Aggregating system logs and calculating quality scores...</span>
                </div>
              ) : !ragMetrics ? (
                <div style={{ ...s.card, padding: 24, textAlign: "center", color: "#64748b" }}>
                  No RAG metrics available. Run a query in MarketBeacon Copilot to generate metrics.
                </div>
              ) : (
                <>
                  {/* KPI Grid */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16 }}>
                    
                    {/* Latency */}
                    <div style={{ ...s.card, background: "#0a0f1d", padding: 16, display: "flex", flexDirection: "column", gap: 8 }}>
                      <span style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", fontWeight: 700 }}>
                        Avg Retrieval Latency
                      </span>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                        <span style={{ fontSize: 20, fontWeight: 800, color: ragMetrics.avg_latency < 500 ? "#10b981" : ragMetrics.avg_latency < 1000 ? "#f59e0b" : "#ef4444" }}>
                          {ragMetrics.avg_latency}
                        </span>
                        <span style={{ fontSize: 10, color: "#64748b" }}>ms</span>
                      </div>
                      <div style={{ height: 4, background: "#1e293b", borderRadius: 2, overflow: "hidden" }}>
                        <div style={{ 
                          width: `${Math.min(100, (ragMetrics.avg_latency / 1500) * 100)}%`, 
                          height: "100%", 
                          background: ragMetrics.avg_latency < 500 ? "#10b981" : ragMetrics.avg_latency < 1000 ? "#f59e0b" : "#ef4444" 
                        }} />
                      </div>
                      <span style={{ fontSize: 8, color: "#475569" }}>Target: &lt; 500ms (BM25 + Vector + Rerank)</span>
                    </div>

                    {/* Confidence */}
                    <div style={{ ...s.card, background: "#0a0f1d", padding: 16, display: "flex", flexDirection: "column", gap: 8 }}>
                      <span style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", fontWeight: 700 }}>
                        Avg Confidence Score
                      </span>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                        <span style={{ fontSize: 20, fontWeight: 800, color: "#06b6d4" }}>
                          {ragMetrics.avg_confidence}%
                        </span>
                      </div>
                      <div style={{ height: 4, background: "#1e293b", borderRadius: 2, overflow: "hidden" }}>
                        <div style={{ width: `${ragMetrics.avg_confidence}%`, height: "100%", background: "#06b6d4" }} />
                      </div>
                      <span style={{ fontSize: 8, color: "#475569" }}>
                        Quality Level: {ragMetrics.avg_confidence >= 75 ? "High Confidence" : ragMetrics.avg_confidence >= 40 ? "Medium Confidence" : "Limited Evidence"}
                      </span>
                    </div>

                    {/* Source Count */}
                    <div style={{ ...s.card, background: "#0a0f1d", padding: 16, display: "flex", flexDirection: "column", gap: 8 }}>
                      <span style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", fontWeight: 700 }}>
                        Avg Source Count
                      </span>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                        <span style={{ fontSize: 20, fontWeight: 800, color: "#cbd5e1" }}>
                          {ragMetrics.avg_source_count}
                        </span>
                        <span style={{ fontSize: 10, color: "#64748b" }}>docs</span>
                      </div>
                      <div style={{ height: 4, background: "#1e293b", borderRadius: 2, overflow: "hidden" }}>
                        <div style={{ width: `${(ragMetrics.avg_source_count / 10) * 100}%`, height: "100%", background: "#cbd5e1" }} />
                      </div>
                      <span style={{ fontSize: 8, color: "#475569" }}>Average chunks matched per RAG query</span>
                    </div>

                    {/* Citation Coverage */}
                    <div style={{ ...s.card, background: "#0a0f1d", padding: 16, display: "flex", flexDirection: "column", gap: 8 }}>
                      <span style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", fontWeight: 700 }}>
                        Citation Coverage
                      </span>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                        <span style={{ fontSize: 20, fontWeight: 800, color: "#a855f7" }}>
                          {Math.round(ragMetrics.avg_citation_coverage * 100)}%
                        </span>
                      </div>
                      <div style={{ height: 4, background: "#1e293b", borderRadius: 2, overflow: "hidden" }}>
                        <div style={{ width: `${ragMetrics.avg_citation_coverage * 100}%`, height: "100%", background: "#a855f7" }} />
                      </div>
                      <span style={{ fontSize: 8, color: "#475569" }}>Ratio of retrieved sources cited in responses</span>
                    </div>

                    {/* Retrieval Quality */}
                    <div style={{ ...s.card, background: "#0a0f1d", padding: 16, display: "flex", flexDirection: "column", gap: 8 }}>
                      <span style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", fontWeight: 700 }}>
                        Retrieval Quality (Similarity)
                      </span>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                        <span style={{ fontSize: 20, fontWeight: 800, color: "#10b981" }}>
                          {Math.round(ragMetrics.avg_retrieval_quality * 100)}%
                        </span>
                      </div>
                      <div style={{ height: 4, background: "#1e293b", borderRadius: 2, overflow: "hidden" }}>
                        <div style={{ width: `${ragMetrics.avg_retrieval_quality * 100}%`, height: "100%", background: "#10b981" }} />
                      </div>
                      <span style={{ fontSize: 8, color: "#475569" }}>Average cosine similarity of vector results</span>
                    </div>

                  </div>

                  {/* Recent Queries Table */}
                  <div style={{ ...s.card, background: "#0a0f1d", padding: 16, display: "flex", flexDirection: "column", gap: 12 }}>
                    <h4 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: "#f8fafc" }}>
                      📝 Recent Queries Evaluation Logs
                    </h4>
                    <div style={{ overflowX: "auto" }}>
                      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, textAlign: "left" }}>
                        <thead>
                          <tr style={{ background: "#080c16", borderBottom: "1px solid #121b2e" }}>
                            <th style={{ padding: "10px", color: "#64748b" }}>Query Text</th>
                            <th style={{ padding: "10px", color: "#64748b" }}>Latency</th>
                            <th style={{ padding: "10px", color: "#64748b" }}>Confidence</th>
                            <th style={{ padding: "10px", color: "#64748b" }}>Sources</th>
                            <th style={{ padding: "10px", color: "#64748b" }}>Citation Coverage</th>
                            <th style={{ padding: "10px", color: "#64748b" }}>Similarity Quality</th>
                            <th style={{ padding: "10px", color: "#64748b" }}>Logged At</th>
                          </tr>
                        </thead>
                        <tbody>
                          {ragMetrics.recent_queries && ragMetrics.recent_queries.length > 0 ? (
                            ragMetrics.recent_queries.map((q, idx) => (
                              <tr key={idx} style={{ borderBottom: "1px solid #121b2e" }}>
                                <td style={{ padding: "10px", color: "#f1f5f9", maxWidth: "250px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={q.query}>
                                  {q.query}
                                </td>
                                <td style={{ padding: "10px", color: q.latency < 500 ? "#10b981" : q.latency < 1000 ? "#f59e0b" : "#ef4444", fontWeight: 600 }}>
                                  {q.latency} ms
                                </td>
                                <td style={{ padding: "10px", color: "#cbd5e1" }}>
                                  <span style={{ 
                                    fontSize: 9, 
                                    fontWeight: 700, 
                                    padding: "2px 6px", 
                                    borderRadius: 4,
                                    background: q.confidence >= 75 ? "rgba(16, 185, 129, 0.1)" : q.confidence >= 40 ? "rgba(245, 158, 11, 0.1)" : "rgba(239, 68, 68, 0.1)",
                                    color: q.confidence >= 75 ? "#10b981" : q.confidence >= 40 ? "#f59e0b" : "#ef4444"
                                  }}>
                                    {q.confidence}%
                                  </span>
                                </td>
                                <td style={{ padding: "10px", color: "#e2e8f0" }}>{q.source_count} chunks</td>
                                <td style={{ padding: "10px", color: "#a855f7", fontWeight: 600 }}>{Math.round(q.citation_coverage * 100)}%</td>
                                <td style={{ padding: "10px", color: "#10b981", fontWeight: 600 }}>{Math.round(q.retrieval_quality * 100)}%</td>
                                <td style={{ padding: "10px", color: "#64748b" }}>{new Date(q.logged_at).toLocaleTimeString()}</td>
                              </tr>
                            ))
                          ) : (
                            <tr>
                              <td colSpan={7} style={{ padding: "20px", textAlign: "center", color: "#475569" }}>
                                No recent evaluation records found.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* PORTFOLIO INTELLIGENCE PAGE */}
          {activeSection === "portfolio" && (
            <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 24, animation: "fadeIn 0.25s ease-out" }}>
              
              {/* Header Overview Card */}
              {portfolioLoading && !portfolioData ? (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "100px 0", gap: 12 }}>
                  <div style={s.spinnerBig} />
                  <div style={{ color: "#94a3b8", fontSize: 13 }}>Loading portfolio intelligence details...</div>
                </div>
              ) : (
                <>
                  <div style={{
                    background: "linear-gradient(135deg, #0b1329, #050811)",
                    border: "1px solid #1e293b",
                    borderRadius: 16,
                    padding: 24,
                    boxShadow: "0 10px 30px -10px rgba(0,0,0,0.7)",
                    display: "flex",
                    flexWrap: "wrap",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 20
                  }}>
                    {/* Left: Net Worth & Stats */}
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: "#64748b", letterSpacing: "0.1em", textTransform: "uppercase" }}>
                        Portfolio Valuation
                      </span>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
                        <span style={{ fontSize: 32, fontWeight: 800, color: "#f8fafc", fontFamily: "monospace" }}>
                          ₹{(portfolioData?.portfolio_value || 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                        
                        {/* Daily Change Badge */}
                        <span style={{
                          fontSize: 14,
                          fontWeight: 700,
                          color: (portfolioData?.today_change_val || 0) >= 0 ? "#10b981" : "#ef4444",
                          display: "flex",
                          alignItems: "center",
                          gap: 4
                        }}>
                          {(portfolioData?.today_change_val || 0) >= 0 ? "▲" : "▼"}{" "}
                          ₹{Math.abs(portfolioData?.today_change_val || 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}{" "}
                          ({(portfolioData?.today_change_pct || 0).toFixed(2)}%)
                        </span>
                      </div>
                      
                      {/* Sub stats */}
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 20, fontSize: 12, color: "#94a3b8", marginTop: 8 }}>
                        <div>Equity Assets: <span style={{ color: "#cbd5e1", fontWeight: 600 }}>₹{(portfolioData?.equity_value || 0).toLocaleString("en-IN")}</span></div>
                        <div style={{ width: 1, height: 14, background: "#1e293b" }} />
                        <div>Cash Allocation: <span style={{ color: "#cbd5e1", fontWeight: 600 }}>₹{(portfolioData?.cash_value || 0).toLocaleString("en-IN")}</span></div>
                        <div style={{ width: 1, height: 14, background: "#1e293b" }} />
                        <div>Largest Holding: <span style={{ color: "#cbd5e1", fontWeight: 600 }}>{portfolioData?.largest_holding || "None"}</span></div>
                        <div style={{ width: 1, height: 14, background: "#1e293b" }} />
                        <div>Mood: <span style={{
                          color: portfolioData?.mood === "Bullish" ? "#10b981" : portfolioData?.mood === "Bearish" ? "#ef4444" : "#94a3b8",
                          fontWeight: 700,
                          textTransform: "uppercase",
                          fontSize: 10,
                          background: portfolioData?.mood === "Bullish" ? "#10b98115" : portfolioData?.mood === "Bearish" ? "#ef444415" : "#1e293b",
                          padding: "2px 8px",
                          borderRadius: 4
                        }}>{portfolioData?.mood === "Bullish" ? "🐂 Bullish" : portfolioData?.mood === "Bearish" ? "🐻 Bearish" : "⚖️ Neutral"}</span></div>
                      </div>
                    </div>

                    {/* Right: Scores & Controls */}
                    <div style={{ display: "flex", alignItems: "center", gap: 24, flexWrap: "wrap" }}>
                      
                      {/* Health Score Badge */}
                      <div style={{
                        background: "#0d1b2a",
                        border: "1px solid #1b4965",
                        borderRadius: 12,
                        padding: "12px 18px",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        minWidth: 100
                      }}>
                        <span style={{ fontSize: 9, fontWeight: 700, color: "#62b6cb", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 4 }}>Health Score</span>
                        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          <span style={{
                            width: 10,
                            height: 10,
                            borderRadius: "50%",
                            background: portfolioData?.health_status === "Healthy" ? "#10b981" : portfolioData?.health_status === "Moderate Risk" ? "#eab308" : "#ef4444",
                            boxShadow: `0 0 10px ${portfolioData?.health_status === "Healthy" ? "#10b981" : portfolioData?.health_status === "Moderate Risk" ? "#eab308" : "#ef4444"}`
                          }} />
                          <span style={{ fontSize: 22, fontWeight: 800, color: "#f8fafc", fontFamily: "monospace" }}>{portfolioData?.health_score || 0}</span>
                        </div>
                        <span style={{ fontSize: 10, color: "#94a3b8", marginTop: 4, fontWeight: 600 }}>{portfolioData?.health_status || "Unknown"}</span>
                      </div>

                      {/* Diversification Score Badge */}
                      <div style={{
                        background: "#160f29",
                        border: "1px solid #3c1642",
                        borderRadius: 12,
                        padding: "12px 18px",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        minWidth: 100
                      }}>
                        <span style={{ fontSize: 9, fontWeight: 700, color: "#b58db6", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 4 }}>Diversification</span>
                        <span style={{ fontSize: 22, fontWeight: 800, color: "#f8fafc", fontFamily: "monospace" }}>{portfolioData?.diversification_score || 0}</span>
                        <span style={{ fontSize: 10, color: "#94a3b8", marginTop: 4, fontWeight: 600 }}>
                          {portfolioData?.diversification_score >= 80 ? "Well Diversified" : portfolioData?.diversification_score >= 50 ? "Moderate" : "Concentrated"}
                        </span>
                      </div>

                      {/* Action buttons */}
                      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                        <button onClick={() => { fetchPortfolioData(true); fetchPortfolioReview(true); fetchPortfolioBrief(true); }} style={s.btnPrimary}>
                          🔄 Refresh Calculations
                        </button>
                        <button onClick={() => setPortfolioAddModalOpen(true)} style={{
                          ...s.btnPrimary,
                          background: "linear-gradient(135deg, #10b981, #059669)",
                        }}>
                          ➕ Add New Holding
                        </button>
                      </div>

                    </div>
                  </div>

                  {/* Sector Allocation Banner */}
                  <div style={{
                    background: "#080c14",
                    border: "1px solid #121b2e",
                    borderRadius: 12,
                    padding: 16,
                    display: "flex",
                    flexDirection: "column",
                    gap: 8
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8", textTransform: "uppercase" }}>Sector Allocation Matrix</span>
                      {portfolioData?.sector_allocations?.some(sec => sec.sector !== "Cash" && sec.percentage > 40) && (
                        <span style={{ fontSize: 10, color: "#f59e0b", background: "#f59e0b12", padding: "2px 8px", borderRadius: 4, border: "1px solid #f59e0b33", fontWeight: 600 }}>
                          ⚠️ Concentration Warning: Sector exposure exceeds 40%
                        </span>
                      )}
                    </div>
                    <div style={{ display: "flex", height: 12, borderRadius: 6, overflow: "hidden", background: "#111827", border: "1px solid #1f2937" }}>
                      {portfolioData?.sector_allocations?.map((sec, idx) => {
                        const colors = ["#06b6d4", "#a855f7", "#10b981", "#fbbf24", "#ef4444", "#3b82f6", "#f97316", "#94a3b8"];
                        return (
                          <div key={sec.sector} style={{
                            width: `${sec.percentage}%`,
                            background: sec.sector === "Cash" ? "#64748b" : colors[idx % colors.length],
                            height: "100%",
                            transition: "all 0.3s ease"
                          }} title={`${sec.sector}: ${sec.percentage}%`} />
                        );
                      })}
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 12, fontSize: 10, color: "#64748b", marginTop: 4 }}>
                      {portfolioData?.sector_allocations?.map((sec, idx) => {
                        const colors = ["#06b6d4", "#a855f7", "#10b981", "#fbbf24", "#ef4444", "#3b82f6", "#f97316", "#94a3b8"];
                        return (
                          <div key={sec.sector} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                            <span style={{ width: 8, height: 8, borderRadius: "50%", background: sec.sector === "Cash" ? "#64748b" : colors[idx % colors.length] }} />
                            <span style={{ color: "#cbd5e1", fontWeight: 600 }}>{sec.sector}</span>
                            <span>({sec.percentage}%)</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Portfolio Navigation Tabs */}
                  <div style={{ display: "flex", borderBottom: "1px solid #121b2e", paddingBottom: 0, gap: 12, marginTop: 8 }}>
                    {[
                      { id: "holdings", label: "Holding Ledger", icon: "📋" },
                      { id: "review", label: "AI Portfolio Review & Brief", icon: "✨" },
                      { id: "risk", label: "Risk Center & Simulation", icon: "🛡️" },
                      { id: "compare", label: "Holding Comparison", icon: "⚖️" },
                    ].map(tab => (
                      <button
                        key={tab.id}
                        onClick={() => setPortfolioActiveTab(tab.id)}
                        style={{
                          background: "none",
                          border: "none",
                          borderBottom: portfolioActiveTab === tab.id ? "3px solid #06b6d4" : "3px solid transparent",
                          color: portfolioActiveTab === tab.id ? "#06b6d4" : "#64748b",
                          padding: "10px 16px",
                          fontSize: 13,
                          fontWeight: 700,
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                          display: "flex",
                          alignItems: "center",
                          gap: 6
                        }}
                      >
                        <span>{tab.icon}</span> {tab.label}
                      </button>
                    ))}
                  </div>

                  {/* TAB CONTENT: HOLDINGS */}
                  {portfolioActiveTab === "holdings" && (
                    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                      {portfolioData?.holdings?.length === 0 ? (
                        <div style={{
                          border: "1px dashed #1e293b",
                          borderRadius: 12,
                          padding: 48,
                          textAlign: "center",
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                          gap: 16
                        }}>
                          <span style={{ fontSize: 32 }}>💼</span>
                          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                            <h4 style={{ fontSize: 15, fontWeight: 700, color: "#f8fafc", margin: 0 }}>No holdings registered</h4>
                            <p style={{ fontSize: 12, color: "#64748b", margin: 0 }}>Your portfolio database is currently empty.</p>
                          </div>
                          <button onClick={() => setPortfolioAddModalOpen(true)} style={s.btnPrimary}>
                            ➕ Register First Holding
                          </button>
                        </div>
                      ) : (
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(330px, 1fr))", gap: 16 }}>
                          {portfolioData?.holdings?.map(item => {
                            const isLoss = item.gain_loss < 0;
                            return (
                              <div key={item.id} style={{
                                background: "#080c14",
                                border: "1px solid #121b2e",
                                borderRadius: 12,
                                padding: 18,
                                display: "flex",
                                flexDirection: "column",
                                gap: 14,
                                position: "relative",
                                transition: "all 0.2s ease",
                                cursor: "default"
                              }}>
                                {/* Card Header */}
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                                  <div>
                                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                      <h4 style={{ fontSize: 14, fontWeight: 700, color: "#f8fafc", margin: 0 }}>
                                        {item.company_name}
                                      </h4>
                                      <span style={{ fontSize: 8, background: "#1e293b", color: "#94a3b8", padding: "1px 4px", borderRadius: 3, fontWeight: 700 }}>
                                        {item.exchange || "NSE"}
                                      </span>
                                    </div>
                                    <span style={{ fontSize: 10, color: "#64748b" }}>
                                      Sector: {item.sector} | Industry: {item.industry}
                                    </span>
                                  </div>
                                  
                                  {/* Delete holding */}
                                  <button
                                    onClick={() => handleDeleteHolding(item.id)}
                                    style={{
                                      background: "none",
                                      border: "none",
                                      color: "#ef4444",
                                      cursor: "pointer",
                                      fontSize: 12,
                                      opacity: 0.6,
                                      padding: 4,
                                      transition: "opacity 0.1s"
                                    }}
                                    onMouseEnter={e => e.target.style.opacity = 1}
                                    onMouseLeave={e => e.target.style.opacity = 0.6}
                                    title="Delete holding"
                                  >
                                    🗑️
                                  </button>
                                </div>

                                {/* Ledger Metrics */}
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, background: "#0a0f1d", padding: 10, borderRadius: 8, border: "1px solid #111827" }}>
                                  <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                                    <span style={{ fontSize: 9, color: "#64748b" }}>Quantity</span>
                                    <span style={{ fontSize: 12, fontWeight: 600, color: "#cbd5e1", fontFamily: "monospace" }}>{item.quantity}</span>
                                  </div>
                                  <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                                    <span style={{ fontSize: 9, color: "#64748b" }}>Current Value</span>
                                    <span style={{ fontSize: 12, fontWeight: 700, color: "#f8fafc", fontFamily: "monospace" }}>
                                      ₹{item.value.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                                    </span>
                                  </div>
                                  <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                                    <span style={{ fontSize: 9, color: "#64748b" }}>Average Cost</span>
                                    <span style={{ fontSize: 12, fontWeight: 600, color: "#cbd5e1", fontFamily: "monospace" }}>
                                      ₹{item.average_buy_price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                                    </span>
                                  </div>
                                  <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                                    <span style={{ fontSize: 9, color: "#64748b" }}>Current Price</span>
                                    <span style={{ fontSize: 12, fontWeight: 600, color: "#cbd5e1", fontFamily: "monospace" }}>
                                      ₹{item.current_price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                                    </span>
                                  </div>
                                </div>

                                {/* Return & Daily Change */}
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 11 }}>
                                  <div>
                                    <span style={{ color: "#64748b" }}>Gain/Loss: </span>
                                    <span style={{ color: isLoss ? "#ef4444" : "#10b981", fontWeight: 700, fontFamily: "monospace" }}>
                                      {isLoss ? "" : "+"}{item.gain_loss >= 0 ? "₹" : "-₹"}{Math.abs(item.gain_loss).toLocaleString("en-IN", { maximumFractionDigits: 2 })}{" "}
                                      ({isLoss ? "" : "+"}{item.gain_loss_pct.toFixed(2)}%)
                                    </span>
                                  </div>
                                  <div>
                                    <span style={{ color: "#64748b" }}>Daily Change: </span>
                                    <span style={{ color: item.daily_change_pct >= 0 ? "#10b981" : "#ef4444", fontWeight: 700, fontFamily: "monospace" }}>
                                      {item.daily_change_pct >= 0 ? "+" : ""}{item.daily_change_pct.toFixed(2)}%
                                    </span>
                                  </div>
                                </div>

                                {/* Intelligence Flags */}
                                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, borderTop: "1px solid #121b2e", paddingTop: 10 }}>
                                  <span style={{
                                    fontSize: 8,
                                    fontWeight: 700,
                                    background: item.risk_level === "High" ? "#ef444415" : item.risk_level === "Medium" ? "#f59e0b15" : "#10b98115",
                                    color: item.risk_level === "High" ? "#ef4444" : item.risk_level === "Medium" ? "#f59e0b" : "#10b981",
                                    padding: "2px 6px",
                                    borderRadius: 4,
                                    border: `1px solid ${item.risk_level === "High" ? "#ef444433" : item.risk_level === "Medium" ? "#f59e0b33" : "#10b98133"}`
                                  }}>
                                    RISK: {item.risk_level}
                                  </span>

                                  <span style={{
                                    fontSize: 8,
                                    fontWeight: 700,
                                    background: "#0ea5e915",
                                    color: "#0ea5e9",
                                    padding: "2px 6px",
                                    borderRadius: 4,
                                    border: "1px solid #0ea5e933"
                                  }}>
                                    ATTN: {item.attention_score}
                                  </span>

                                  {item.has_research && (
                                    <span style={{
                                      fontSize: 8,
                                      fontWeight: 700,
                                      background: "#8b5cf615",
                                      color: "#8b5cf6",
                                      padding: "2px 6px",
                                      borderRadius: 4,
                                      border: "1px solid #8b5cf633"
                                    }}>
                                      ✓ RESEARCH COVERED
                                    </span>
                                  )}

                                  {item.news_count > 0 && (
                                    <span style={{
                                      fontSize: 8,
                                      fontWeight: 700,
                                      background: "#06b6d415",
                                      color: "#06b6d4",
                                      padding: "2px 6px",
                                      borderRadius: 4,
                                      border: "1px solid #06b6d433"
                                    }}>
                                      NEWS (7D): {item.news_count}
                                    </span>
                                  )}

                                  {item.critical_alerts > 0 && (
                                    <span style={{
                                      fontSize: 8,
                                      fontWeight: 700,
                                      background: "#ef444420",
                                      color: "#ef4444",
                                      padding: "2px 6px",
                                      borderRadius: 4,
                                      border: "1px solid #ef444450"
                                    }}>
                                      🚨 ALERTS: {item.critical_alerts}
                                    </span>
                                  )}
                                </div>

                                {item.notes && (
                                  <div style={{ fontSize: 10, color: "#cbd5e1", background: "#0a0f1d", padding: "6px 10px", borderRadius: 4, fontStyle: "italic" }}>
                                    Note: {item.notes}
                                  </div>
                                )}

                                {/* Action Buttons */}
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginTop: 4 }}>
                                  <button
                                    onClick={() => fetchCompanyResearch(item.company_name)}
                                    style={{
                                      background: "#1e293b",
                                      color: "#cbd5e1",
                                      border: "1px solid #334155",
                                      borderRadius: 6,
                                      padding: "6px 10px",
                                      fontSize: 11,
                                      fontWeight: 600,
                                      cursor: "pointer",
                                      transition: "all 0.15s ease"
                                    }}
                                    onMouseEnter={e => e.target.style.background = "#334155"}
                                    onMouseLeave={e => e.target.style.background = "#1e293b"}
                                  >
                                    📂 Open Dossier
                                  </button>
                                  
                                  <button
                                    onClick={() => handleFetchExplanation("company", item.company_name)}
                                    style={{
                                      background: "linear-gradient(135deg, #06b6d415, #3b82f615)",
                                      color: "#3b82f6",
                                      border: "1px solid #3b82f633",
                                      borderRadius: 6,
                                      padding: "6px 10px",
                                      fontSize: 11,
                                      fontWeight: 600,
                                      cursor: "pointer",
                                      transition: "all 0.15s ease"
                                    }}
                                    onMouseEnter={e => e.target.style.background = "#3b82f625"}
                                    onMouseLeave={e => e.target.style.background = "linear-gradient(135deg, #06b6d415, #3b82f615)"}
                                  >
                                    ✨ Explain Holding
                                  </button>

                                  <button
                                    onClick={() => fetchHoldingTimeline(item.company_name)}
                                    style={{
                                      background: "#1e293b",
                                      color: "#cbd5e1",
                                      border: "1px solid #334155",
                                      borderRadius: 6,
                                      padding: "6px 10px",
                                      fontSize: 11,
                                      fontWeight: 600,
                                      cursor: "pointer",
                                      transition: "all 0.15s ease"
                                    }}
                                    onMouseEnter={e => e.target.style.background = "#334155"}
                                    onMouseLeave={e => e.target.style.background = "#1e293b"}
                                  >
                                    ⏳ View Timeline
                                  </button>

                                  <button
                                    onClick={() => {
                                      handleFetchExplanation("text", item.company_name, `Why is ${item.company_name} stock moving today? Explain in light of recent volatility triggers, alerts and index flow indicators.`);
                                    }}
                                    style={{
                                      background: "#1e293b",
                                      color: "#cbd5e1",
                                      border: "1px solid #334155",
                                      borderRadius: 6,
                                      padding: "6px 10px",
                                      fontSize: 11,
                                      fontWeight: 600,
                                      cursor: "pointer",
                                      transition: "all 0.15s ease"
                                    }}
                                    onMouseEnter={e => e.target.style.background = "#334155"}
                                    onMouseLeave={e => e.target.style.background = "#1e293b"}
                                  >
                                    ❓ Why Moving?
                                  </button>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}

                  {/* TAB CONTENT: AI REVIEW & BRIEF */}
                  {portfolioActiveTab === "review" && (
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, alignItems: "start" }}>
                      
                      {/* Left: Today's Portfolio Daily Brief */}
                      <div style={{
                        background: "#080c14",
                        border: "1px solid #121b2e",
                        borderRadius: 12,
                        padding: 20,
                        display: "flex",
                        flexDirection: "column",
                        gap: 16
                      }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #121b2e", paddingBottom: 12 }}>
                          <h3 style={{ fontSize: 15, fontWeight: 700, color: "#f8fafc", margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
                            🌅 Today's Portfolio Brief
                          </h3>
                          <button onClick={() => fetchPortfolioBrief(true)} style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 12 }}>
                            🔄 Regenerate Brief
                          </button>
                        </div>

                        {portfolioBriefLoading ? (
                          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, padding: "40px 0" }}>
                            <div style={s.spinner} />
                            <span style={{ fontSize: 11, color: "#64748b" }}>Analyzing portfolio intelligence briefs...</span>
                          </div>
                        ) : portfolioBrief ? (
                          <div style={{ display: "flex", flexDirection: "column", gap: 14, fontSize: 12, lineHeight: 1.5 }}>
                            <div style={{ fontSize: 13, fontWeight: 700, color: "#cbd5e1" }}>
                              {portfolioBrief.title}
                            </div>
                            
                            <p style={{ color: "#cbd5e1", margin: 0 }}>
                              {portfolioBrief.narrative}
                            </p>

                            <div style={{ background: "#0a0f1d", border: "1px solid #111827", borderRadius: 8, padding: 12, display: "flex", flexDirection: "column", gap: 8 }}>
                              <div>
                                <span style={{ color: "#ef4444", fontWeight: 700, display: "block", marginBottom: 2 }}>⚠️ New Risks:</span>
                                <span style={{ color: "#94a3b8" }}>{portfolioBrief.new_risks}</span>
                              </div>
                              <div>
                                <span style={{ color: "#10b981", fontWeight: 700, display: "block", marginBottom: 2 }}>📈 Positive Developments:</span>
                                <span style={{ color: "#94a3b8" }}>{portfolioBrief.positive_developments}</span>
                              </div>
                              <div>
                                <span style={{ color: "#eab308", fontWeight: 700, display: "block", marginBottom: 2 }}>🔔 Critical Changes:</span>
                                <span style={{ color: "#94a3b8" }}>{portfolioBrief.critical_changes}</span>
                              </div>
                            </div>

                            {portfolioBrief.upcoming_events?.length > 0 && (
                              <div>
                                <span style={{ color: "#06b6d4", fontWeight: 700, display: "block", marginBottom: 4 }}>📅 Upcoming Events:</span>
                                <ul style={{ margin: 0, paddingLeft: 16, color: "#cbd5e1", display: "flex", flexDirection: "column", gap: 4 }}>
                                  {portfolioBrief.upcoming_events.map((ev, i) => <li key={i}>{ev}</li>)}
                                </ul>
                              </div>
                            )}

                            <div style={{ display: "flex", flexWrap: "wrap", gap: 16, borderTop: "1px solid #121b2e", paddingTop: 12 }}>
                              <div>
                                <span style={{ color: "#ef4444", fontSize: 10, fontWeight: 700, display: "block", marginBottom: 2 }}>REQUIRES ATTENTION</span>
                                <div style={{ display: "flex", gap: 6 }}>
                                  {portfolioBrief.require_attention?.map(c => (
                                    <span key={c} style={{ fontSize: 9, background: "#ef444415", border: "1px solid #ef444433", color: "#ef4444", padding: "2px 6px", borderRadius: 4, fontWeight: 600 }}>{c}</span>
                                  ))}
                                </div>
                              </div>
                              <div>
                                <span style={{ color: "#06b6d4", fontSize: 10, fontWeight: 700, display: "block", marginBottom: 2 }}>WATCH TOMORROW</span>
                                <div style={{ display: "flex", gap: 6 }}>
                                  {portfolioBrief.watch_tomorrow?.map(c => (
                                    <span key={c} style={{ fontSize: 9, background: "#06b6d415", border: "1px solid #06b6d433", color: "#06b6d4", padding: "2px 6px", borderRadius: 4, fontWeight: 600 }}>{c}</span>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div style={{ color: "#64748b", fontSize: 12, textAlign: "center" }}>No briefing data compiled.</div>
                        )}
                      </div>

                      {/* Right: AI Portfolio Review */}
                      <div style={{
                        background: "#080c14",
                        border: "1px solid #121b2e",
                        borderRadius: 12,
                        padding: 20,
                        display: "flex",
                        flexDirection: "column",
                        gap: 16
                      }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #121b2e", paddingBottom: 12 }}>
                          <h3 style={{ fontSize: 15, fontWeight: 700, color: "#f8fafc", margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
                            ✨ Review My Portfolio
                          </h3>
                          <button onClick={() => fetchPortfolioReview(true)} style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 12 }}>
                            🔄 Recalculate Report
                          </button>
                        </div>

                        {portfolioReviewLoading ? (
                          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, padding: "40px 0" }}>
                            <div style={s.spinner} />
                            <span style={{ fontSize: 11, color: "#64748b" }}>Generating AI Risk overview report...</span>
                          </div>
                        ) : portfolioReview ? (
                          <div style={{ display: "flex", flexDirection: "column", gap: 14, fontSize: 12, lineHeight: 1.5 }}>
                            <div>
                              <span style={{ color: "#64748b", fontSize: 10, fontWeight: 700, textTransform: "uppercase" }}>Strategic Overview</span>
                              <p style={{ color: "#cbd5e1", margin: "4px 0 0 0" }}>{portfolioReview.summary}</p>
                            </div>

                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                              <div style={{ background: "#10b9810b", border: "1px solid #10b9811c", padding: 10, borderRadius: 8 }}>
                                <span style={{ color: "#10b981", fontWeight: 700, display: "block", marginBottom: 4 }}>💪 Strongest Assets:</span>
                                {portfolioReview.strongest_holdings?.map(h => (
                                  <span key={h} style={{ fontSize: 9, background: "#10b98115", color: "#10b981", border: "1px solid #10b98133", padding: "1px 6px", borderRadius: 4, marginRight: 6 }}>{h}</span>
                                ))}
                              </div>
                              <div style={{ background: "#ef44440b", border: "1px solid #ef44441c", padding: 10, borderRadius: 8 }}>
                                <span style={{ color: "#ef4444", fontWeight: 700, display: "block", marginBottom: 4 }}>🥀 Weakest Assets:</span>
                                {portfolioReview.weakest_holdings?.map(h => (
                                  <span key={h} style={{ fontSize: 9, background: "#ef444415", color: "#ef4444", border: "1px solid #ef444433", padding: "1px 6px", borderRadius: 4, marginRight: 6 }}>{h}</span>
                                ))}
                              </div>
                            </div>

                            <div>
                              <span style={{ color: "#cbd5e1", fontWeight: 700, display: "block", marginBottom: 2 }}>⚠️ Biggest Risks:</span>
                              <span style={{ color: "#94a3b8" }}>{portfolioReview.biggest_risks}</span>
                            </div>

                            <div>
                              <span style={{ color: "#06b6d4", fontWeight: 700, display: "block", marginBottom: 2 }}>💡 Key Opportunities:</span>
                              <span style={{ color: "#94a3b8" }}>{portfolioReview.biggest_opportunities}</span>
                            </div>

                            <div>
                              <span style={{ color: "#b58db6", fontWeight: 700, display: "block", marginBottom: 2 }}>🌐 Diversification Insights:</span>
                              <span style={{ color: "#94a3b8" }}>{portfolioReview.diversification_comments}</span>
                            </div>

                            {portfolioReview.suggested_priorities?.length > 0 && (
                              <div>
                                <span style={{ color: "#6366f1", fontWeight: 700, display: "block", marginBottom: 4 }}>📋 Suggested Monitoring Priorities:</span>
                                <ul style={{ margin: 0, paddingLeft: 16, color: "#cbd5e1", display: "flex", flexDirection: "column", gap: 4 }}>
                                  {portfolioReview.suggested_priorities.map((p, i) => <li key={i}>{p}</li>)}
                                </ul>
                              </div>
                            )}

                            <blockquote style={{ margin: "8px 0 0 0", padding: "6px 12px", borderLeft: "2px solid #64748b", fontStyle: "italic", color: "#64748b", fontSize: 10 }}>
                              Disclaimer: MarketBeacon portfolio analysis is strictly observational. It provides risk-focused updates and alerts monitoring checkpoints, avoiding trade advice or recommendations.
                            </blockquote>
                          </div>
                        ) : (
                          <div style={{ color: "#64748b", fontSize: 12, textAlign: "center" }}>No review report generated.</div>
                        )}
                      </div>

                    </div>
                  )}

                  {/* TAB CONTENT: RISK CENTER & SIMULATION */}
                  {portfolioActiveTab === "risk" && (
                    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                      
                      {/* Risk Dashboard Stats */}
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
                        
                        <div style={{ background: "#080c14", border: "1px solid #121b2e", borderRadius: 12, padding: 18, display: "flex", flexDirection: "column", gap: 8 }}>
                          <span style={{ fontSize: 11, color: "#64748b", fontWeight: 700, textTransform: "uppercase" }}>Sector Allocation Focus</span>
                          <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 4 }}>
                            {portfolioData?.sector_allocations?.map(sec => (
                              <div key={sec.sector}>
                                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#cbd5e1", marginBottom: 2 }}>
                                  <span>{sec.sector}</span>
                                  <span>{sec.percentage}%</span>
                                </div>
                                <div style={{ height: 6, background: "#111827", borderRadius: 3, overflow: "hidden" }}>
                                  <div style={{ height: "100%", width: `${sec.percentage}%`, background: sec.percentage > 40 ? "#f59e0b" : "#06b6d4" }} />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        <div style={{ background: "#080c14", border: "1px solid #121b2e", borderRadius: 12, padding: 18, display: "flex", flexDirection: "column", gap: 8 }}>
                          <span style={{ fontSize: 11, color: "#64748b", fontWeight: 700, textTransform: "uppercase" }}>Single Stock Concentration</span>
                          <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 4 }}>
                            {portfolioData?.holdings?.map(h => {
                              const pct = portfolioData.portfolio_value > 0 ? (h.value / portfolioData.portfolio_value * 100) : 0;
                              return (
                                <div key={h.id}>
                                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#cbd5e1", marginBottom: 2 }}>
                                    <span>{h.company_name}</span>
                                    <span>{pct.toFixed(1)}%</span>
                                  </div>
                                  <div style={{ height: 6, background: "#111827", borderRadius: 3, overflow: "hidden" }}>
                                    <div style={{ height: "100%", width: `${pct}%`, background: pct > 30 ? "#ef4444" : "#10b981" }} />
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>

                        <div style={{ background: "#080c14", border: "1px solid #121b2e", borderRadius: 12, padding: 18, display: "flex", flexDirection: "column", gap: 8 }}>
                          <span style={{ fontSize: 11, color: "#64748b", fontWeight: 700, textTransform: "uppercase" }}>Research Confidence Gaps</span>
                          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 4 }}>
                            <div style={{ fontSize: 11, color: "#94a3b8" }}>
                              Institutional holdings without RAG research coverages represent risk gaps:
                            </div>
                            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                              {portfolioData?.holdings?.filter(h => !h.has_research).map(h => (
                                <div key={h.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#ef44440f", border: "1px solid #ef444422", padding: "6px 10px", borderRadius: 6 }}>
                                  <span style={{ fontSize: 11, color: "#ef4444", fontWeight: 600 }}>{h.company_name}</span>
                                  <button
                                    onClick={() => {
                                      setActiveSection("research_library");
                                      setUploadCompany(h.company_name);
                                    }}
                                    style={{
                                      background: "#ef444420",
                                      color: "#ef4444",
                                      border: "1px solid #ef444440",
                                      borderRadius: 4,
                                      fontSize: 9,
                                      fontWeight: 700,
                                      padding: "2px 6px",
                                      cursor: "pointer"
                                    }}
                                  >
                                    📁 Upload Doc
                                  </button>
                                </div>
                              ))}
                              {portfolioData?.holdings?.filter(h => !h.has_research).length === 0 && (
                                <div style={{ fontSize: 11, color: "#10b981", fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}>
                                  <span>✓ All holdings have active research reports mapped in library.</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>

                      </div>

                      {/* PORTFOLIO IMPACT ANALYSIS (Explain Engine Event Simulator) */}
                      <div style={{
                        background: "#080c14",
                        border: "1px solid #121b2e",
                        borderRadius: 12,
                        padding: 20,
                        display: "flex",
                        flexDirection: "column",
                        gap: 16
                      }}>
                        <div>
                          <h3 style={{ fontSize: 15, fontWeight: 700, color: "#f8fafc", margin: "0 0 4px 0" }}>🛡️ Macro Event Portfolio Impact Simulation</h3>
                          <p style={{ fontSize: 11, color: "#64748b", margin: 0 }}>Select or type a macro catalyst to simulate how index changes affect your current manual holdings via the AI Explain Engine.</p>
                        </div>

                        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                          <select
                            id="macro-simulator-select"
                            style={{
                              flex: 1,
                              background: "#050811",
                              border: "1px solid #121b2e",
                              borderRadius: 8,
                              padding: "10px 14px",
                              color: "#cbd5e1",
                              fontSize: 13,
                              outline: "none"
                            }}
                          >
                            <option value="RBI Policy Rate Decision Cut">RBI monetary policy cuts repo rates by 25 bps</option>
                            <option value="US Federal Reserve Rate Hike Cycle">US Fed raises target interest rates due to inflation spikes</option>
                            <option value="Nifty Technology Valuations Correction">Major earnings misses trigger technology index rotation sell-off</option>
                            <option value="Automobile Steel Import Custom Duties hike">Government raises import duties on auto steel alloys</option>
                            <option value="General Public Sector Banks recapitalization">Finance ministry announces ₹50,000 Cr PSU bank cash infusions</option>
                          </select>
                          
                          <button
                            onClick={() => {
                              const selectEl = document.getElementById("macro-simulator-select");
                              if (selectEl) {
                                handleFetchExplanation("event", selectEl.value);
                              }
                            }}
                            style={s.btnPrimary}
                          >
                            ⚔️ Simulate Portfolio Impact
                          </button>
                        </div>
                      </div>

                    </div>
                  )}

                  {/* TAB CONTENT: HOLDING COMPARISON */}
                  {portfolioActiveTab === "compare" && (
                    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                      
                      {/* Pickers */}
                      <div style={{
                        background: "#080c14",
                        border: "1px solid #121b2e",
                        borderRadius: 12,
                        padding: 16,
                        display: "flex",
                        flexWrap: "wrap",
                        alignItems: "center",
                        gap: 16
                      }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10, flex: 1, minWidth: 200 }}>
                          <span style={{ fontSize: 12, color: "#cbd5e1", fontWeight: 600 }}>Asset 1:</span>
                          <select
                            value={portfolioCompareCo1}
                            onChange={e => setPortfolioCompareCo1(e.target.value)}
                            style={{ flex: 1, background: "#050811", border: "1px solid #121b2e", borderRadius: 6, padding: "6px 10px", color: "#cbd5e1", fontSize: 12 }}
                          >
                            <option value="">-- Choose Asset 1 --</option>
                            {portfolioData?.holdings?.map(h => (
                              <option key={h.id} value={h.company_name}>{h.company_name}</option>
                            ))}
                          </select>
                        </div>

                        <span style={{ color: "#64748b", fontWeight: "bold" }}>VS</span>

                        <div style={{ display: "flex", alignItems: "center", gap: 10, flex: 1, minWidth: 200 }}>
                          <span style={{ fontSize: 12, color: "#cbd5e1", fontWeight: 600 }}>Asset 2:</span>
                          <select
                            value={portfolioCompareCo2}
                            onChange={e => setPortfolioCompareCo2(e.target.value)}
                            style={{ flex: 1, background: "#050811", border: "1px solid #121b2e", borderRadius: 6, padding: "6px 10px", color: "#cbd5e1", fontSize: 12 }}
                          >
                            <option value="">-- Choose Asset 2 --</option>
                            {portfolioData?.holdings?.map(h => (
                              <option key={h.id} value={h.company_name}>{h.company_name}</option>
                            ))}
                          </select>
                        </div>

                        <button onClick={fetchPortfolioComparison} style={s.btnPrimary}>
                          ⚖️ Compare Holdings
                        </button>
                      </div>

                      {/* Results */}
                      {portfolioCompareLoading ? (
                        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, padding: "60px 0" }}>
                          <div style={s.spinnerBig} />
                          <span style={{ fontSize: 12, color: "#64748b" }}>Analyzing assets relative metrics...</span>
                        </div>
                      ) : portfolioCompareData ? (
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                          
                          {/* Asset 1 Card */}
                          <div style={{ background: "#080c14", border: "1px solid #121b2e", borderRadius: 12, padding: 18, display: "flex", flexDirection: "column", gap: 14 }}>
                            <h3 style={{ fontSize: 16, fontWeight: 800, color: "#06b6d4", margin: 0, borderBottom: "1px solid #121b2e", paddingBottom: 10 }}>
                              {portfolioCompareData.company1.name}
                            </h3>
                            <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: 12 }}>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ color: "#64748b" }}>Market Cap:</span>
                                <span style={{ color: "#cbd5e1", fontWeight: 600 }}>{portfolioCompareData.company1.fundamentals?.market_cap || "N/A"}</span>
                              </div>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ color: "#64748b" }}>P/E Ratio:</span>
                                <span style={{ color: "#cbd5e1", fontWeight: 600 }}>{portfolioCompareData.company1.fundamentals?.pe_ratio || "N/A"}</span>
                              </div>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ color: "#64748b" }}>Debt to Equity:</span>
                                <span style={{ color: "#cbd5e1", fontWeight: 600 }}>{portfolioCompareData.company1.fundamentals?.debt_to_equity || "N/A"}</span>
                              </div>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ color: "#64748b" }}>Revenue Growth:</span>
                                <span style={{ color: "#cbd5e1", fontWeight: 600 }}>{portfolioCompareData.company1.fundamentals?.revenue_growth || "N/A"}</span>
                              </div>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ color: "#64748b" }}>7D Smart Alerts Triggered:</span>
                                <span style={{ color: "#cbd5e1", fontWeight: 600 }}>{portfolioCompareData.company1.stats?.alerts_7d}</span>
                              </div>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ color: "#64748b" }}>7D News Catalysts:</span>
                                <span style={{ color: "#cbd5e1", fontWeight: 600 }}>{portfolioCompareData.company1.stats?.news_7d}</span>
                              </div>
                            </div>
                            
                            {/* Miniature timeline */}
                            <div style={{ borderTop: "1px solid #121b2e", paddingTop: 10 }}>
                              <span style={{ fontSize: 10, color: "#64748b", fontWeight: 700, textTransform: "uppercase", display: "block", marginBottom: 6 }}>Recent Events</span>
                              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                                {portfolioCompareData.company1.timeline?.map((item, i) => (
                                  <div key={i} style={{ background: "#0a0f1d", padding: 8, borderRadius: 6, fontSize: 10, border: "1px solid #111827" }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                                      <span style={{ color: item.color, fontWeight: 700 }}>{item.type}</span>
                                      <span style={{ color: "#64748b" }}>{item.date}</span>
                                    </div>
                                    <div style={{ color: "#cbd5e1" }}>{item.title}</div>
                                  </div>
                                ))}
                                {portfolioCompareData.company1.timeline?.length === 0 && <span style={{ fontSize: 11, color: "#64748b" }}>No recent events recorded.</span>}
                              </div>
                            </div>
                          </div>

                          {/* Asset 2 Card */}
                          <div style={{ background: "#080c14", border: "1px solid #121b2e", borderRadius: 12, padding: 18, display: "flex", flexDirection: "column", gap: 14 }}>
                            <h3 style={{ fontSize: 16, fontWeight: 800, color: "#a855f7", margin: 0, borderBottom: "1px solid #121b2e", paddingBottom: 10 }}>
                              {portfolioCompareData.company2.name}
                            </h3>
                            <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: 12 }}>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ color: "#64748b" }}>Market Cap:</span>
                                <span style={{ color: "#cbd5e1", fontWeight: 600 }}>{portfolioCompareData.company2.fundamentals?.market_cap || "N/A"}</span>
                              </div>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ color: "#64748b" }}>P/E Ratio:</span>
                                <span style={{ color: "#cbd5e1", fontWeight: 600 }}>{portfolioCompareData.company2.fundamentals?.pe_ratio || "N/A"}</span>
                              </div>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ color: "#64748b" }}>Debt to Equity:</span>
                                <span style={{ color: "#cbd5e1", fontWeight: 600 }}>{portfolioCompareData.company2.fundamentals?.debt_to_equity || "N/A"}</span>
                              </div>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ color: "#64748b" }}>Revenue Growth:</span>
                                <span style={{ color: "#cbd5e1", fontWeight: 600 }}>{portfolioCompareData.company2.fundamentals?.revenue_growth || "N/A"}</span>
                              </div>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ color: "#64748b" }}>7D Smart Alerts Triggered:</span>
                                <span style={{ color: "#cbd5e1", fontWeight: 600 }}>{portfolioCompareData.company2.stats?.alerts_7d}</span>
                              </div>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ color: "#64748b" }}>7D News Catalysts:</span>
                                <span style={{ color: "#cbd5e1", fontWeight: 600 }}>{portfolioCompareData.company2.stats?.news_7d}</span>
                              </div>
                            </div>

                            {/* Miniature timeline */}
                            <div style={{ borderTop: "1px solid #121b2e", paddingTop: 10 }}>
                              <span style={{ fontSize: 10, color: "#64748b", fontWeight: 700, textTransform: "uppercase", display: "block", marginBottom: 6 }}>Recent Events</span>
                              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                                {portfolioCompareData.company2.timeline?.map((item, i) => (
                                  <div key={i} style={{ background: "#0a0f1d", padding: 8, borderRadius: 6, fontSize: 10, border: "1px solid #111827" }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                                      <span style={{ color: item.color, fontWeight: 700 }}>{item.type}</span>
                                      <span style={{ color: "#64748b" }}>{item.date}</span>
                                    </div>
                                    <div style={{ color: "#cbd5e1" }}>{item.title}</div>
                                  </div>
                                ))}
                                {portfolioCompareData.company2.timeline?.length === 0 && <span style={{ fontSize: 11, color: "#64748b" }}>No recent events recorded.</span>}
                              </div>
                            </div>
                          </div>

                        </div>
                      ) : (
                        <div style={{ color: "#64748b", fontSize: 12, textAlign: "center", padding: "40px 0" }}>
                          Select two holdings above and click Compare to evaluate.
                        </div>
                      )}
                    </div>
                  )}

                </>
              )}

            </div>
          )}

          {/* AI RESEARCH WORKSPACE */}
          {activeSection === "workspace" && (
            <div style={{
              display: "grid",
              gridTemplateColumns: "260px 1fr 320px",
              height: "calc(100vh - 70px)",
              background: "#050811",
              boxSizing: "border-box",
              overflow: "hidden",
              animation: "fadeIn 0.2s ease-out"
            }}>
              
              {/* LEFT SIDEBAR: Research History & Recent Tickers */}
              <div style={{
                background: "#080c14",
                borderRight: "1px solid #121b2e",
                display: "flex",
                flexDirection: "column",
                overflowY: "auto",
                padding: 16,
                boxSizing: "border-box",
                gap: 20
              }}>
                <div>
                  <h4 style={{ fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>
                    Recent Tickers
                  </h4>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {recentCompanies.map(co => (
                      <button
                        key={co}
                        onClick={() => handleAnalyzeWorkspace(co)}
                        style={{
                          background: "#111827",
                          border: "1px solid #1e293b",
                          borderRadius: 6,
                          padding: "4px 10px",
                          color: "#cbd5e1",
                          fontSize: 11,
                          cursor: "pointer",
                          transition: "all 0.15s ease"
                        }}
                        onMouseEnter={e => { e.target.style.borderColor = "#06b6d4"; e.target.style.color = "#06b6d4"; }}
                        onMouseLeave={e => { e.target.style.borderColor = "#1e293b"; e.target.style.color = "#cbd5e1"; }}
                      >
                        {co}
                      </button>
                    ))}
                    {recentCompanies.length === 0 && <span style={{ fontSize: 11, color: "#475569" }}>No recent tickers.</span>}
                  </div>
                </div>

                <div>
                  <h4 style={{ fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>
                    Saved Workspaces ({savedWorkspaces.length})
                  </h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {savedWorkspaces.map(ws => (
                      <div
                        key={ws.id}
                        onClick={() => {
                          setCurrentWorkspace(ws);
                          setWorkspaceQuery(ws.query);
                          setWorkspaceNotes(ws.notes || "");
                        }}
                        style={{
                          background: currentWorkspace?.id === ws.id ? "#06b6d412" : "#0e1626",
                          border: currentWorkspace?.id === ws.id ? "1px solid #06b6d444" : "1px solid #121b2e",
                          borderRadius: 8,
                          padding: 10,
                          cursor: "pointer",
                          transition: "all 0.2s ease",
                          display: "flex",
                          flexDirection: "column",
                          gap: 6
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontSize: 12, fontWeight: 600, color: ws.is_favorite ? "#f59e0b" : "#cbd5e1", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap", flex: 1 }}>
                            {ws.title}
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleFavoriteWorkspace(ws.id, !ws.is_favorite);
                            }}
                            style={{ background: "none", border: "none", color: ws.is_favorite ? "#f59e0b" : "#475569", cursor: "pointer", fontSize: 11 }}
                          >
                            ★
                          </button>
                        </div>
                        <span style={{ fontSize: 9, color: "#64748b", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                          Q: {ws.query}
                        </span>
                        
                        {/* Inline controls */}
                        <div style={{ display: "flex", justifyContent: "flex-end", gap: 6, borderTop: "1px solid #1e293b", paddingTop: 4, marginTop: 2 }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              const newT = window.prompt("Rename workspace title:", ws.title);
                              if (newT) handleRenameWorkspace(ws.id, newT);
                            }}
                            style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 9 }}
                            title="Rename"
                          >
                            ✏️
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDuplicateWorkspace(ws.id);
                            }}
                            style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 9 }}
                            title="Duplicate"
                          >
                            👯
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteWorkspace(ws.id);
                            }}
                            style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer", fontSize: 9 }}
                            title="Delete"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    ))}
                    {savedWorkspaces.length === 0 && (
                      <div style={{ fontSize: 11, color: "#475569", fontStyle: "italic", textAlign: "center", padding: "10px 0" }}>
                        No saved workspaces found.
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* CENTER: AI Research Canvas */}
              <div style={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                overflow: "hidden"
              }}>
                {/* Search bar header */}
                <div style={{
                  padding: "16px 24px",
                  background: "#080c14",
                  borderBottom: "1px solid #121b2e",
                  display: "flex",
                  gap: 12,
                  alignItems: "center"
                }}>
                  <span style={{ fontSize: 16 }}>🔬</span>
                  <input
                    type="text"
                    placeholder="Investigate any company, sector, comparison or macro topic (e.g. 'Compare TCS vs Infosys' or 'HDFC Bank')..."
                    value={workspaceQuery}
                    onChange={e => setWorkspaceQuery(e.target.value)}
                    onKeyDown={e => { if (e.key === "Enter") handleAnalyzeWorkspace(workspaceQuery); }}
                    style={{
                      flex: 1,
                      background: "#050811",
                      border: "1px solid #121b2e",
                      borderRadius: 8,
                      padding: "8px 12px",
                      color: "#f8fafc",
                      fontSize: 13,
                      outline: "none"
                    }}
                  />
                  <button
                    onClick={() => handleAnalyzeWorkspace(workspaceQuery)}
                    disabled={workspaceLoading}
                    style={{
                      ...s.btnPrimary,
                      padding: "8px 16px"
                    }}
                  >
                    {workspaceLoading ? <span style={s.spinner} /> : "Compile Canvas"}
                  </button>
                </div>

                {/* Canvas Body */}
                <div style={{ flex: 1, overflowY: "auto", padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
                  
                  {workspaceLoading && !currentWorkspace ? (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 12 }}>
                      <div style={s.spinnerBig} />
                      <span style={{ fontSize: 12, color: "#94a3b8" }}>Running vector search & synthesizing intelligence canvas report...</span>
                    </div>
                  ) : currentWorkspace ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 24, animation: "fadeIn 0.25s ease-out" }}>
                      
                      {/* Canvas Report Header Card */}
                      <div style={{
                        background: "linear-gradient(135deg, #0b1329, #050811)",
                        border: "1px solid #1e293b",
                        borderRadius: 12,
                        padding: 18,
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center"
                      }}>
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <h2 style={{ fontSize: 16, fontWeight: 800, color: "#f8fafc", margin: 0 }}>
                              {currentWorkspace.title}
                            </h2>
                            <span style={{
                              fontSize: 9,
                              fontWeight: 700,
                              background: "#06b6d415",
                              color: "#06b6d4",
                              border: "1px solid #06b6d433",
                              padding: "2px 8px",
                              borderRadius: 4,
                              textTransform: "uppercase"
                            }}>
                              MODE: {currentWorkspace.analysis_json?.mode || "General"}
                            </span>
                          </div>
                          <span style={{ fontSize: 11, color: "#64748b", marginTop: 4, display: "block" }}>
                            Trigger Catalyst: "{currentWorkspace.query}"
                          </span>
                        </div>

                        <div style={{ display: "flex", gap: 8 }}>
                          <button
                            onClick={() => {
                              const newT = window.prompt("Change workspace title:", currentWorkspace.title);
                              if (newT) setCurrentWorkspace(prev => ({ ...prev, title: newT }));
                            }}
                            style={{ background: "#111827", color: "#cbd5e1", border: "1px solid #1e293b", borderRadius: 6, padding: "6px 12px", fontSize: 11, fontWeight: 600, cursor: "pointer" }}
                          >
                            ✏️ Rename
                          </button>
                          
                          <button
                            onClick={() => {
                              const isFav = !currentWorkspace.is_favorite;
                              setCurrentWorkspace(prev => ({ ...prev, is_favorite: isFav }));
                              if (currentWorkspace.id) handleFavoriteWorkspace(currentWorkspace.id, isFav);
                            }}
                            style={{ background: "#111827", color: currentWorkspace.is_favorite ? "#f59e0b" : "#cbd5e1", border: "1px solid #1e293b", borderRadius: 6, padding: "6px 12px", fontSize: 11, fontWeight: 600, cursor: "pointer" }}
                          >
                            ★ {currentWorkspace.is_favorite ? "Favorited" : "Favorite"}
                          </button>

                          <button
                            onClick={handleSaveWorkspace}
                            style={{ ...s.btnPrimary, background: "linear-gradient(135deg, #10b981, #059669)", padding: "6px 12px" }}
                          >
                            💾 Save Workspace
                          </button>

                          <button
                            onClick={handleExportWorkspace}
                            disabled={workspaceExportLoading}
                            style={{ ...s.btnPrimary, background: "linear-gradient(135deg, #a855f7, #6366f1)", padding: "6px 12px" }}
                          >
                            {workspaceExportLoading ? <span style={s.spinner} /> : "📤 Export MD"}
                          </button>
                        </div>
                      </div>

                      {/* Portfolio & Watchlist Exposure Alerts */}
                      {(currentWorkspace.analysis_json?.portfolio_exposure?.in_portfolio || currentWorkspace.analysis_json?.watchlist_status?.in_watchlist) && (
                        <div style={{
                          background: "#0f172a",
                          border: "1px solid #1e293b",
                          borderRadius: 8,
                          padding: 12,
                          display: "flex",
                          flexWrap: "wrap",
                          gap: 16,
                          fontSize: 11
                        }}>
                          {currentWorkspace.analysis_json.portfolio_exposure?.in_portfolio && (
                            <div style={{ display: "flex", alignItems: "center", gap: 6, color: "#10b981" }}>
                              <span>💼 Mapped in Portfolio Holdings:</span>
                              <span style={{ fontWeight: 700 }}>
                                Qty {currentWorkspace.analysis_json.portfolio_exposure.quantity} | Val: ₹{currentWorkspace.analysis_json.portfolio_exposure.current_value.toLocaleString()} ({currentWorkspace.analysis_json.portfolio_exposure.gain_loss >= 0 ? "+" : ""}{currentWorkspace.analysis_json.portfolio_exposure.gain_loss_pct.toFixed(1)}%)
                              </span>
                            </div>
                          )}
                          {currentWorkspace.analysis_json.portfolio_exposure?.in_portfolio && currentWorkspace.analysis_json.watchlist_status?.in_watchlist && (
                            <div style={{ width: 1, height: 14, background: "#334155" }} />
                          )}
                          {currentWorkspace.analysis_json.watchlist_status?.in_watchlist && (
                            <div style={{ display: "flex", alignItems: "center", gap: 6, color: "#06b6d4" }}>
                              <span>⭐ Mapped in Watchlist:</span>
                              <span style={{ fontWeight: 700 }}>
                                Priority: {currentWorkspace.analysis_json.watchlist_status.priority} | Sector: {currentWorkspace.analysis_json.watchlist_status.sector}
                              </span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Canvas Section: Summary */}
                      <div style={{ background: "#080c14", border: "1px solid #121b2e", borderRadius: 12, padding: 20 }}>
                        <h3 style={{ fontSize: 13, fontWeight: 700, color: "#06b6d4", textTransform: "uppercase", borderBottom: "1px solid #121b2e", paddingBottom: 8, margin: "0 0 12px 0" }}>
                          1. Executive Summary
                        </h3>
                        <p style={{ fontSize: 12, lineHeight: 1.6, color: "#cbd5e1", margin: 0 }}>
                          {currentWorkspace.analysis_json?.summary}
                        </p>
                      </div>

                      {/* Canvas Section: Key Insights & Opportunities/Risks */}
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, alignItems: "start" }}>
                        
                        <div style={{ background: "#080c14", border: "1px solid #121b2e", borderRadius: 12, padding: 18 }}>
                          <h3 style={{ fontSize: 13, fontWeight: 700, color: "#06b6d4", textTransform: "uppercase", borderBottom: "1px solid #121b2e", paddingBottom: 8, margin: "0 0 12px 0" }}>
                            2. Key Insights
                          </h3>
                          <ul style={{ margin: 0, paddingLeft: 16, color: "#cbd5e1", fontSize: 12, display: "flex", flexDirection: "column", gap: 10 }}>
                            {currentWorkspace.analysis_json?.key_insights?.map((ins, i) => (
                              <li key={i}>{ins}</li>
                            ))}
                          </ul>
                        </div>

                        <div style={{ background: "#080c14", border: "1px solid #121b2e", borderRadius: 12, padding: 18, display: "flex", flexDirection: "column", gap: 12 }}>
                          <div>
                            <span style={{ color: "#ef4444", fontSize: 11, fontWeight: 700, textTransform: "uppercase" }}>⚠️ Risks</span>
                            <ul style={{ margin: "6px 0 0 0", paddingLeft: 16, color: "#cbd5e1", fontSize: 12, display: "flex", flexDirection: "column", gap: 4 }}>
                              {currentWorkspace.analysis_json?.risks?.map((r, i) => <li key={i}>{r}</li>)}
                            </ul>
                          </div>
                          <div style={{ borderTop: "1px solid #121b2e", paddingTop: 10 }}>
                            <span style={{ color: "#10b981", fontSize: 11, fontWeight: 700, textTransform: "uppercase" }}>💡 Opportunities</span>
                            <ul style={{ margin: "6px 0 0 0", paddingLeft: 16, color: "#cbd5e1", fontSize: 12, display: "flex", flexDirection: "column", gap: 4 }}>
                              {currentWorkspace.analysis_json?.opportunities?.map((o, i) => <li key={i}>{o}</li>)}
                            </ul>
                          </div>
                        </div>

                      </div>

                      {/* Canvas Section: Comparison Grid (If Comparison Mode) */}
                      {currentWorkspace.analysis_json?.compare_data && (
                        <div style={{ background: "#080c14", border: "1px solid #121b2e", borderRadius: 12, padding: 20 }}>
                          <h3 style={{ fontSize: 13, fontWeight: 700, color: "#a855f7", textTransform: "uppercase", borderBottom: "1px solid #121b2e", paddingBottom: 8, margin: "0 0 16px 0" }}>
                            ⚖️ Peer Comparison Scorecard
                          </h3>
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                            {/* Asset 1 */}
                            <div style={{ background: "#0a0f1d", padding: 14, borderRadius: 8, border: "1px solid #121b2e" }}>
                              <h4 style={{ color: "#06b6d4", fontSize: 14, margin: "0 0 10px 0" }}>{currentWorkspace.analysis_json.compare_data.company1.name}</h4>
                              <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 11 }}>
                                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Market Cap:</span><strong>{currentWorkspace.analysis_json.compare_data.company1.fundamentals?.market_cap}</strong></div>
                                <div style={{ display: "flex", justifyContent: "space-between" }}><span>P/E Ratio:</span><strong>{currentWorkspace.analysis_json.compare_data.company1.fundamentals?.pe_ratio}</strong></div>
                                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Debt to Equity:</span><strong>{currentWorkspace.analysis_json.compare_data.company1.fundamentals?.debt_to_equity}</strong></div>
                                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Revenue Growth:</span><strong>{currentWorkspace.analysis_json.compare_data.company1.fundamentals?.revenue_growth}</strong></div>
                              </div>
                            </div>
                            {/* Asset 2 */}
                            <div style={{ background: "#0a0f1d", padding: 14, borderRadius: 8, border: "1px solid #121b2e" }}>
                              <h4 style={{ color: "#a855f7", fontSize: 14, margin: "0 0 10px 0" }}>{currentWorkspace.analysis_json.compare_data.company2.name}</h4>
                              <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 11 }}>
                                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Market Cap:</span><strong>{currentWorkspace.analysis_json.compare_data.company2.fundamentals?.market_cap}</strong></div>
                                <div style={{ display: "flex", justifyContent: "space-between" }}><span>P/E Ratio:</span><strong>{currentWorkspace.analysis_json.compare_data.company2.fundamentals?.pe_ratio}</strong></div>
                                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Debt to Equity:</span><strong>{currentWorkspace.analysis_json.compare_data.company2.fundamentals?.debt_to_equity}</strong></div>
                                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Revenue Growth:</span><strong>{currentWorkspace.analysis_json.compare_data.company2.fundamentals?.revenue_growth}</strong></div>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Canvas Section: Latest News & Alerts */}
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                        <div style={{ background: "#080c14", border: "1px solid #121b2e", borderRadius: 12, padding: 18 }}>
                          <span style={{ fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase", display: "block", marginBottom: 10 }}>Latest News Catalysts</span>
                          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                            {currentWorkspace.analysis_json?.news?.map((n, idx) => (
                              <div key={idx} style={{ background: "#0a0f1d", padding: 10, borderRadius: 6, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                <span style={{ fontSize: 11, color: "#cbd5e1", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap", flex: 1, marginRight: 8 }}>{n.title}</span>
                                <span style={{
                                  fontSize: 8,
                                  fontWeight: 700,
                                  background: n.sentiment === "Bullish" ? "#10b98115" : n.sentiment === "Bearish" ? "#ef444415" : "#1e293b",
                                  color: n.sentiment === "Bullish" ? "#10b981" : n.sentiment === "Bearish" ? "#ef4444" : "#94a3b8",
                                  padding: "2px 6px",
                                  borderRadius: 4
                                }}>{n.sentiment}</span>
                              </div>
                            ))}
                            {(!currentWorkspace.analysis_json?.news || currentWorkspace.analysis_json.news.length === 0) && (
                              <span style={{ fontSize: 11, color: "#475569" }}>No news match feeds found.</span>
                            )}
                          </div>
                        </div>

                        <div style={{ background: "#080c14", border: "1px solid #121b2e", borderRadius: 12, padding: 18 }}>
                          <span style={{ fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase", display: "block", marginBottom: 10 }}>Volatility Alerts</span>
                          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                            {currentWorkspace.analysis_json?.alerts?.map((a, idx) => (
                              <div key={idx} style={{ background: "#0a0f1d", padding: 10, borderRadius: 6, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                <span style={{ fontSize: 11, color: "#cbd5e1", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap", flex: 1, marginRight: 8 }}>{a.title}</span>
                                <span style={{
                                  fontSize: 8,
                                  fontWeight: 700,
                                  background: a.importance >= 80 ? "#ef444420" : "#fbbf2420",
                                  color: a.importance >= 80 ? "#ef4444" : "#fbbf24",
                                  border: `1px solid ${a.importance >= 80 ? "#ef444440" : "#fbbf2440"}`,
                                  padding: "1px 6px",
                                  borderRadius: 4
                                }}>Score: {a.importance}</span>
                              </div>
                            ))}
                            {(!currentWorkspace.analysis_json?.alerts || currentWorkspace.analysis_json.alerts.length === 0) && (
                              <span style={{ fontSize: 11, color: "#475569" }}>No alerts triggered recently.</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Canvas Section: Chronological Timeline */}
                      {currentWorkspace.analysis_json?.timeline?.length > 0 && (
                        <div style={{ background: "#080c14", border: "1px solid #121b2e", borderRadius: 12, padding: 20 }}>
                          <h3 style={{ fontSize: 13, fontWeight: 700, color: "#06b6d4", textTransform: "uppercase", borderBottom: "1px solid #121b2e", paddingBottom: 8, margin: "0 0 16px 0" }}>
                            3. Activity Timeline
                          </h3>
                          <div style={s.timelineContainer}>
                            {currentWorkspace.analysis_json.timeline.map((item, idx) => (
                              <div key={idx} style={s.timelineItem}>
                                <div style={{ ...s.timelineDot, background: item.color }} />
                                <div style={s.timelineDate}>{item.date}</div>
                                <div style={s.timelineContentCard}>
                                  <span style={{ fontSize: 8, background: `${item.color}15`, color: item.color, padding: "2px 6px", borderRadius: 4, textTransform: "uppercase", fontWeight: 700 }}>
                                    {item.type}
                                  </span>
                                  <h4 style={{ fontSize: 11, color: "#f8fafc", margin: "6px 0 0 0" }}>{item.title}</h4>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Canvas Section: Follow-Up Questions (Feature 8) */}
                      {currentWorkspace.analysis_json?.suggested_followups?.length > 0 && (
                        <div style={{
                          background: "#080c14",
                          border: "1px solid #121b2e",
                          borderRadius: 12,
                          padding: 16
                        }}>
                          <span style={{ fontSize: 10, fontWeight: 800, color: "#64748b", textTransform: "uppercase", display: "block", marginBottom: 10 }}>
                            Follow-Up Research Catalysts
                          </span>
                          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                            {currentWorkspace.analysis_json.suggested_followups.map((promptText, i) => (
                              <button
                                key={i}
                                onClick={() => handleAnalyzeWorkspace(promptText)}
                                style={{
                                  background: "#0a0f1d",
                                  border: "1px solid #1e293b",
                                  borderRadius: 8,
                                  padding: "8px 14px",
                                  color: "#cbd5e1",
                                  fontSize: 11,
                                  fontWeight: 600,
                                  cursor: "pointer",
                                  transition: "all 0.15s ease",
                                  textAlign: "left"
                                }}
                                onMouseEnter={e => { e.target.style.borderColor = "#06b6d4"; e.target.style.color = "#06b6d4"; }}
                                onMouseLeave={e => { e.target.style.borderColor = "#1e293b"; e.target.style.color = "#cbd5e1"; }}
                              >
                                {promptText} →
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                    </div>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 16 }}>
                      <span style={{ fontSize: 48 }}>🔬</span>
                      <div style={{ display: "flex", flexDirection: "column", gap: 6, textAlign: "center" }}>
                        <h3 style={{ fontSize: 16, fontWeight: 700, color: "#f8fafc", margin: 0 }}>AI Research Workspace Sandbox</h3>
                        <p style={{ fontSize: 12, color: "#64748b", margin: 0, maxWidth: 450 }}>
                          Type a company (e.g. HDFC Bank), sector, or macro topic catalyst above. 
                          The router will route the research mode and assemble an evidence-backed cognitive workspace automatically.
                        </p>
                      </div>
                    </div>
                  )}

                </div>
              </div>

              {/* RIGHT SIDEBAR: Sources, Notes, & Supporting Evidence */}
              <div style={{
                background: "#080c14",
                borderLeft: "1px solid #121b2e",
                display: "flex",
                flexDirection: "column",
                overflowY: "auto",
                padding: 16,
                boxSizing: "border-box",
                gap: 20
              }}>
                {/* Section: Notes */}
                <div>
                  <h4 style={{ fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>
                    Analyst Notes
                  </h4>
                  <textarea
                    rows={8}
                    placeholder="Type manual findings, audit observations or sector rotation strategies to link and search alongside this workspace..."
                    value={workspaceNotes}
                    onChange={e => setWorkspaceNotes(e.target.value)}
                    style={{
                      width: "100%",
                      background: "#050811",
                      border: "1px solid #121b2e",
                      borderRadius: 8,
                      padding: 10,
                      color: "#cbd5e1",
                      fontSize: 12,
                      resize: "none",
                      boxSizing: "border-box",
                      fontFamily: "inherit",
                      outline: "none"
                    }}
                  />
                  {currentWorkspace && (
                    <button
                      onClick={handleSaveWorkspace}
                      style={{
                        ...s.btnPrimary,
                        width: "100%",
                        padding: "6px 12px",
                        justifyContent: "center",
                        marginTop: 8,
                        fontSize: 11
                      }}
                    >
                      💾 Save Notes
                    </button>
                  )}
                </div>

                {/* Section: Sources List */}
                <div>
                  <h4 style={{ fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>
                    Evidence Sources Index
                  </h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {currentWorkspace?.analysis_json?.sources?.map((s, idx) => (
                      <div
                        key={idx}
                        onClick={() => {
                          if (s.doc_type === "Research Document" && s.source) {
                            setActiveSection("research_library");
                          } else {
                            showToast(`Source loaded: ${s.source}`);
                          }
                        }}
                        style={{
                          background: "#0e1626",
                          border: "1px solid #121b2e",
                          borderRadius: 8,
                          padding: 10,
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                          display: "flex",
                          flexDirection: "column",
                          gap: 4
                        }}
                        onMouseEnter={e => e.currentTarget.style.borderColor = "#06b6d4"}
                        onMouseLeave={e => e.currentTarget.style.borderColor = "#121b2e"}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontSize: 11, fontWeight: 700, color: "#f8fafc", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap", flex: 1 }}>
                            {s.source}
                          </span>
                          <span style={{ fontSize: 8, background: "#1f2937", color: "#94a3b8", padding: "1px 4px", borderRadius: 3 }}>
                            {s.confidence}
                          </span>
                        </div>
                        <span style={{ fontSize: 9, color: "#64748b" }}>
                          Type: {s.doc_type} | Tier: {s.tier}
                        </span>
                      </div>
                    ))}
                    {(!currentWorkspace?.analysis_json?.sources || currentWorkspace.analysis_json.sources.length === 0) && (
                      <div style={{ fontSize: 11, color: "#475569", fontStyle: "italic", textAlign: "center", padding: "10px 0" }}>
                        No sources compiled yet.
                      </div>
                    )}
                  </div>
                </div>

              </div>

            </div>
          )}

          {/* PROFILE PAGE */}
          {activeSection === "profile" && <Profile />}

          {/* SETTINGS PAGE */}
          {activeSection === "settings" && <Settings />}

        </div>
      </div>

      {/* Right Bloomberg Panel (Feature 1, 2) */}
        {rightPanelContent && (
          <div style={{
            width: 380,
            background: "#0a0f1d",
            borderLeft: "1px solid #121b2e",
            position: "sticky",
            top: 70,
            height: "calc(100vh - 70px)",
            overflowY: "auto",
            padding: 24,
            boxSizing: "border-box",
            flexShrink: 0,
            display: "flex",
            flexDirection: "column",
            gap: 16
          }}>
             {/* Header */}
             <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #1e293b", paddingBottom: 12 }}>
               <h3 style={{ fontSize: 13, fontWeight: 800, color: "#06b6d4", letterSpacing: "0.05em", margin: 0 }}>
                 {rightPanelContent.type === "bulk" ? "✨ BULK ALERT BRIEF" : "✨ AI ALERT ANALYSIS"}
               </h3>
               <button onClick={() => setRightPanelContent(null)} style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 16 }}>✕</button>
             </div>
             
             {rightPanelLoading ? (
               <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, padding: "40px 0" }}>
                 <div style={s.spinnerBig} />
                 <div style={{ fontSize: 12, color: "#64748b" }}>Generating AI Analysis...</div>
               </div>
             ) : rightPanelContent.error ? (
               <div style={{ color: "#ef4444", fontSize: 13, textAlign: "center" }}>
                 {rightPanelContent.error}
               </div>
             ) : (
               <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                 <div>
                   <h4 style={{ fontSize: 11, color: "#06b6d4", textTransform: "uppercase", margin: "0 0 6px 0", fontWeight: 700 }}>Executive Summary</h4>
                   <p style={{ fontSize: 13, color: "#cbd5e1", margin: 0, lineHeight: 1.5 }}>{rightPanelContent.summary}</p>
                 </div>
                 
                 <div>
                   <h4 style={{ fontSize: 11, color: "#06b6d4", textTransform: "uppercase", margin: "0 0 6px 0", fontWeight: 700 }}>Market Impact</h4>
                   <div style={{ fontSize: 13, color: "#cbd5e1", whiteSpace: "pre-line", lineHeight: 1.5 }}>
                     {rightPanelContent.market_impact}
                   </div>
                 </div>
 
                 <div>
                   <h4 style={{ fontSize: 11, color: "#06b6d4", textTransform: "uppercase", margin: "0 0 6px 0", fontWeight: 700 }}>Affected Sectors</h4>
                   <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                     {rightPanelContent.affected_sectors && rightPanelContent.affected_sectors.length > 0 ? (
                       rightPanelContent.affected_sectors.map(sec => (
                         <span key={sec} style={{ fontSize: 10, background: "#06b6d415", color: "#06b6d4", border: "1px solid #06b6d433", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
                           {sec}
                         </span>
                       ))
                     ) : (
                       <span style={{ fontSize: 11, color: "#475569" }}>None specified</span>
                     )}
                   </div>
                 </div>

                 {rightPanelContent.key_takeaways && (
                   <div>
                     <h4 style={{ fontSize: 11, color: "#06b6d4", textTransform: "uppercase", margin: "0 0 6px 0", fontWeight: 700 }}>Key Takeaways</h4>
                     <p style={{ fontSize: 13, color: "#cbd5e1", margin: 0, lineHeight: 1.5 }}>{rightPanelContent.key_takeaways}</p>
                   </div>
                 )}

                 {rightPanelContent.suggested_watchlist && rightPanelContent.suggested_watchlist.length > 0 && (
                   <div>
                     <h4 style={{ fontSize: 11, color: "#06b6d4", textTransform: "uppercase", margin: "0 0 6px 0", fontWeight: 700 }}>Suggested Watchlist</h4>

                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                       {rightPanelContent.suggested_watchlist.map(item => (
                         <span key={item} style={{ fontSize: 10, background: "#a855f715", color: "#a855f7", border: "1px solid #a855f733", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
                           {item}
                         </span>
                       ))}
                     </div>
                   </div>
                 )}


                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, borderTop: "1px solid #1e293b", paddingTop: 14 }}>
                   <div>
                     <h4 style={{ fontSize: 11, color: "#06b6d4", textTransform: "uppercase", margin: "0 0 4px 0", fontWeight: 700 }}>Outlook</h4>
                     <span style={{
                       fontSize: 11,
                       fontWeight: 800,
                       color: (rightPanelContent.outlook || "").toLowerCase().includes("bullish") ? "#10b981" : (rightPanelContent.outlook || "").toLowerCase().includes("bearish") ? "#ef4444" : "#94a3b8"
                     }}>
                       {rightPanelContent.outlook || "Neutral"}
                     </span>
                   </div>
                   
                   <div>
                     <h4 style={{ fontSize: 11, color: "#06b6d4", textTransform: "uppercase", margin: "0 0 4px 0", fontWeight: 700 }}>Confidence</h4>
                     <span style={{ fontSize: 11, fontWeight: 800, color: "#cbd5e1", fontFamily: "monospace" }}>
                       {rightPanelContent.confidence || 90}%
                      </span>
                    </div>
                  </div>
                </div>
              )
            }
          </div>
        )}

         {/* Explain Engine Right sliding panel (Feature 15) */}
         {explainPanelOpen && (
          <div style={{
            width: 420,
            background: "#0a0f1d",
            borderLeft: "1px solid #121b2e",
            position: "sticky",
            top: 70,
            height: "calc(100vh - 70px)",
            overflowY: "auto",
            padding: 24,
            boxSizing: "border-box",
            flexShrink: 0,
            display: "flex",
            flexDirection: "column",
            gap: 18,
            animation: "fadeIn 0.2s ease-out"
          }}>
             {/* Header */}
             <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", borderBottom: "1px solid #1e293b", paddingBottom: 12 }}>
               <div>
                 <span style={{
                   background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
                   color: "#fff", fontSize: 9, fontWeight: 800, padding: "2px 8px", borderRadius: 4, letterSpacing: "0.08em", display: "inline-block", marginBottom: 6
                 }}>
                   ✨ AI EXPLAIN: {explainType.toUpperCase()}
                 </span>
                 <h3 style={{ fontSize: 14, fontWeight: 700, color: "#f8fafc", margin: 0, lineHeight: 1.4 }}>
                   {explainType === "text" ? "Selected Text Analysis" : explainTargetId}
                 </h3>
               </div>
               <button onClick={() => setExplainPanelOpen(false)} style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 16, padding: 4 }}>✕</button>
             </div>

             {explainPanelLoading ? (
               <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, padding: "60px 0" }}>
                 <div style={s.spinnerBig} />
                 <div style={{ fontSize: 12, color: "#64748b" }}>Analyzing context data...</div>
               </div>
             ) : explainData?.error ? (
               <div style={{ color: "#ef4444", fontSize: 13, textAlign: "center", padding: "20px 0" }}>
                 {explainData.error}
               </div>
             ) : explainData ? (
               <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                 
                 {/* Feature 13: Explain Score */}
                 <div style={{ background: "#0c1222", border: "1px solid #1e293b", borderRadius: 10, padding: 12, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: 11 }}>
                   <div>
                     <span style={{ color: "#64748b" }}>🎯 Explanation Confidence:</span>
                     <div style={{ fontWeight: 800, color: "#06b6d4", fontSize: 13, marginTop: 2 }}>{explainData.explain_score?.confidence || explainData.confidence || 90}%</div>
                   </div>
                   <div>
                     <span style={{ color: "#64748b" }}>📚 Evidence Coverage:</span>
                     <div style={{ fontWeight: 800, color: "#a855f7", fontSize: 13, marginTop: 2 }}>{explainData.explain_score?.evidence_coverage || 85}%</div>
                   </div>
                   <div>
                     <span style={{ color: "#64748b" }}>🛡️ Source Quality:</span>
                     <div style={{ fontWeight: 800, color: "#10b981", fontSize: 11, marginTop: 2 }}>{explainData.explain_score?.source_quality || "High"} Confidence</div>
                   </div>
                   <div>
                     <span style={{ color: "#64748b" }}>⏰ Freshness Check:</span>
                     <div style={{ fontWeight: 800, color: "#f59e0b", fontSize: 11, marginTop: 2 }}>{explainData.explain_score?.freshness || "Today"}</div>
                   </div>
                 </div>

                 {/* Summary */}
                 <div>
                   <h4 style={{ fontSize: 11, color: "#06b6d4", textTransform: "uppercase", margin: "0 0 6px 0", fontWeight: 700 }}>Summary</h4>
                   <p style={{ fontSize: 13, color: "#cbd5e1", margin: 0, lineHeight: 1.6 }}>{explainData.summary}</p>
                 </div>

                 {/* Why It Matters */}
                 <div>
                   <h4 style={{ fontSize: 11, color: "#06b6d4", textTransform: "uppercase", margin: "0 0 6px 0", fontWeight: 700 }}>Why It Matters</h4>
                   <p style={{ fontSize: 13, color: "#cbd5e1", margin: 0, lineHeight: 1.6 }}>{explainData.why_it_matters}</p>
                 </div>

                 {/* Feature 6: AI Impact Map */}
                 <div style={{ background: "#0c1222", border: "1px solid #1e293b", borderRadius: 10, padding: 14 }}>
                   <h4 style={{ fontSize: 11, color: "#10b981", textTransform: "uppercase", margin: "0 0 10px 0", fontWeight: 700 }}>🗺️ AI Impact Map</h4>
                   
                   <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: 12 }}>
                     <div>
                       <span style={{ color: "#64748b", display: "block", marginBottom: 4 }}>📈 Who Benefits:</span>
                       <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                         {explainData.impact_map?.beneficiary_companies?.map(co => (
                           <span key={co} style={{ fontSize: 10, background: "#10b98115", color: "#10b981", border: "1px solid #10b98133", padding: "2px 6px", borderRadius: 4, fontWeight: 600 }}>{co}</span>
                         ))}
                       </div>
                     </div>

                     <div>
                       <span style={{ color: "#ef4444", display: "block", marginBottom: 4 }}>📉 Who Suffers:</span>
                       <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                         {explainData.impact_map?.affected_companies?.map(co => (
                           <span key={co} style={{ fontSize: 10, background: "#ef444415", color: "#ef4444", border: "1px solid #ef444433", padding: "2px 6px", borderRadius: 4, fontWeight: 600 }}>{co}</span>
                         ))}
                       </div>
                     </div>

                     <div>
                       <span style={{ color: "#94a3b8", display: "block", marginBottom: 4 }}>Affected Sectors:</span>
                       <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                         {explainData.impact_map?.affected_sectors?.map(sec => (
                           <span key={sec} style={{ fontSize: 10, background: "#33415520", color: "#94a3b8", border: "1px solid #334155", padding: "2px 6px", borderRadius: 4 }}>{sec}</span>
                         ))}
                       </div>
                     </div>

                     <div style={{ borderTop: "1px solid #1e293b", paddingTop: 8, fontSize: 11, color: "#cbd5e1" }}>
                       <strong>Supply Chain Impact:</strong> {explainData.impact_map?.supply_chain_impact}
                     </div>
                     <div style={{ fontSize: 11, color: "#cbd5e1" }}>
                       <strong>Overall Risk:</strong> <span style={{ color: explainData.impact_map?.risk_level === "High" ? "#ef4444" : "#10b981", fontWeight: "bold" }}>{explainData.impact_map?.risk_level}</span>
                     </div>
                   </div>
                 </div>

                 {/* Feature 5: Historical Context */}
                 <div>
                   <h4 style={{ fontSize: 11, color: "#06b6d4", textTransform: "uppercase", margin: "0 0 8px 0", fontWeight: 700 }}>📜 Historical Context</h4>
                   {explainData.historical_context?.events?.map((evt, idx) => (
                     <div key={idx} style={{ background: "#05081199", border: "1px solid #121b2e", borderRadius: 8, padding: 10, fontSize: 11, display: "flex", flexDirection: "column", gap: 4, marginBottom: 8 }}>
                       <div style={{ display: "flex", justifyContent: "space-between", color: "#94a3b8" }}>
                         <strong>{evt.event}</strong>
                         <span>{evt.date}</span>
                       </div>
                       <div style={{ color: "#cbd5e1" }}><strong>Reaction:</strong> {evt.market_reaction}</div>
                       <div style={{ color: "#cbd5e1" }}><strong>Performance:</strong> Banking {evt.banking_performance} | Nifty {evt.nifty_performance}</div>
                       <div style={{ color: "#06b6d4", fontStyle: "italic", marginTop: 2 }}>Lessons: {evt.lessons_learned}</div>
                     </div>
                   ))}
                 </div>

                 {/* Feature 11: Timeline View */}
                 <div>
                   <h4 style={{ fontSize: 11, color: "#cbd5e1", textTransform: "uppercase", margin: "0 0 10px 0", fontWeight: 700 }}>⏳ Explanation Evolution Timeline</h4>
                   <div style={{ display: "flex", flexDirection: "column", gap: 10, borderLeft: "2px solid #1e293b", paddingLeft: 12, marginLeft: 6 }}>
                     {explainData.timeline?.map((item, idx) => (
                       <div key={idx} style={{ position: "relative", fontSize: 11 }}>
                         <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#06b6d4", position: "absolute", left: -16, top: 4 }} />
                         <span style={{ color: "#06b6d4", fontWeight: "bold", display: "block" }}>{item.period}</span>
                         <span style={{ color: "#cbd5e1" }}>{item.description}</span>
                       </div>
                     ))}
                   </div>
                 </div>

                 {/* Feature 12: Source Transparency */}
                 <div>
                   <h4 style={{ fontSize: 11, color: "#06b6d4", textTransform: "uppercase", margin: "0 0 6px 0", fontWeight: 700 }}>🔍 Evidence used</h4>
                   <div style={{ fontSize: 11, color: "#cbd5e1", background: "#050811aa", border: "1px solid #121b2e", borderRadius: 8, padding: 10, fontStyle: "italic" }}>
                     "{explainData.evidence}"
                   </div>
                   <div style={{ display: "flex", gap: 8, fontSize: 10, color: "#64748b", marginTop: 6, flexWrap: "wrap" }}>
                     <span>Sources: <strong>{explainData.sources?.join(", ")}</strong></span>
                   </div>
                 </div>

                 {/* Details Bull/Bear */}
                 {explainData.details && (
                   <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, fontSize: 11 }}>
                     {explainData.details.bull_case && (
                       <div style={{ background: "#10b98108", border: "1px solid #10b98115", borderRadius: 6, padding: 8 }}>
                         <span style={{ color: "#10b981", fontWeight: "bold" }}>📈 Bull Case</span>
                         <div style={{ color: "#cbd5e1", marginTop: 2 }}>{explainData.details.bull_case}</div>
                       </div>
                     )}
                     {explainData.details.bear_case && (
                       <div style={{ background: "#ef444408", border: "1px solid #ef444415", borderRadius: 6, padding: 8 }}>
                         <span style={{ color: "#ef4444", fontWeight: "bold" }}>📉 Bear Case</span>
                         <div style={{ color: "#cbd5e1", marginTop: 2 }}>{explainData.details.bear_case}</div>
                       </div>
                     )}
                   </div>
                 )}

                 {/* Feature 7: Related Knowledge */}
                 {explainData.related_knowledge && (
                   <div style={{ borderTop: "1px solid #1e293b", paddingTop: 14 }}>
                     <h4 style={{ fontSize: 11, color: "#cbd5e1", textTransform: "uppercase", margin: "0 0 10px 0", fontWeight: 700 }}>📚 Related Knowledge</h4>
                     
                     <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 11 }}>
                       {explainData.related_knowledge.news?.map(nw => (
                         <div key={nw.id} onClick={() => handleFetchExplanation("news", nw.id)} style={{ cursor: "pointer", color: "#06b6d4" }} onMouseEnter={e => e.target.style.textDecoration = "underline"} onMouseLeave={e => e.target.style.textDecoration = "none"}>
                           📰 {nw.title}
                         </div>
                       ))}
                       {explainData.related_knowledge.alerts?.map(al => (
                         <div key={al.id} onClick={() => handleFetchExplanation("alert", al.id)} style={{ cursor: "pointer", color: "#ef4444" }} onMouseEnter={e => e.target.style.textDecoration = "underline"} onMouseLeave={e => e.target.style.textDecoration = "none"}>
                           🚨 {al.title}
                         </div>
                       ))}
                       {explainData.related_knowledge.reports?.map(rp => (
                         <div key={rp.id} onClick={() => { setActiveSection("research_library"); setExplainPanelOpen(false); }} style={{ cursor: "pointer", color: "#8b5cf6" }} onMouseEnter={e => e.target.style.textDecoration = "underline"} onMouseLeave={e => e.target.style.textDecoration = "none"}>
                           📖 {rp.title}
                         </div>
                       ))}
                       {explainData.related_knowledge.conversations?.map(cv => (
                         <div key={cv.id} onClick={() => { setActiveSection("ask"); loadChatSession(cv.id); setExplainPanelOpen(false); }} style={{ cursor: "pointer", color: "#eab308" }} onMouseEnter={e => e.target.style.textDecoration = "underline"} onMouseLeave={e => e.target.style.textDecoration = "none"}>
                           💬 AI Chat: {cv.title}
                         </div>
                       ))}
                     </div>
                   </div>
                 )}

                 {/* Feature 8: Ask Follow-up */}
                 {explainData.suggested_questions && (
                   <div style={{ borderTop: "1px solid #1e293b", paddingTop: 14 }}>
                     <h4 style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", margin: "0 0 8px 0", fontWeight: 700 }}>Suggested Follow-up Questions</h4>
                     <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                       {explainData.suggested_questions.map((q, idx) => (
                         <button
                           key={idx}
                           onClick={() => {
                             setActiveSection("ask");
                             setExplainPanelOpen(false);
                             setQuestion(q);
                             sendCopilotMessage(q);
                           }}
                           style={{
                             background: "#1e293b33",
                             color: "#06b6d4",
                             border: "1px solid #33415544",
                             borderRadius: 6,
                             padding: "6px 10px",
                             fontSize: 11,
                             cursor: "pointer",
                             textAlign: "left",
                             transition: "background 0.15s"
                           }}
                           onMouseEnter={e => e.target.style.background = "#1e293b99"}
                           onMouseLeave={e => e.target.style.background = "#1e293b33"}
                         >
                           {q}
                         </button>
                       ))}
                     </div>
                   </div>
                 )}

               </div>
             ) : null}
          </div>
        )}
      </main>

      {/* Feature 9 Floating Selection Button */}
      {selectionState.visible && (
        <button
          id="floating-explain-btn"
          onClick={() => {
            handleFetchExplanation("text", "", selectionState.text);
            setSelectionState(prev => ({ ...prev, visible: false }));
          }}
          style={{
            position: "absolute",
            left: selectionState.x,
            top: selectionState.y,
            zIndex: 99999,
            background: "linear-gradient(135deg, #a855f7, #6366f1)",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            padding: "5px 10px",
            fontSize: 11,
            fontWeight: "bold",
            cursor: "pointer",
            boxShadow: "0 4px 12px rgba(0,0,0,0.6)",
            display: "flex",
            alignItems: "center",
            gap: 4
          }}
        >
          ✨ Explain selection
        </button>
      )}


      {/* FEATURE 1: Add Holding Modal */}
      {portfolioAddModalOpen && (
        <div style={s.modalOverlay} onClick={() => setPortfolioAddModalOpen(false)}>
          <div style={{ ...s.modalContent, maxWidth: 500 }} onClick={e => e.stopPropagation()}>
            <div style={s.modalHeader}>
              <div>
                <span style={s.modalTitleBadge}>PORTFOLIO LEDGER REGISTRATION</span>
                <h3 style={s.modalTitle}>Register Manual Holding</h3>
              </div>
              <button style={s.modalCloseBtn} onClick={() => setPortfolioAddModalOpen(false)}>✕</button>
            </div>
            
            <form onSubmit={handleAddHolding}>
              <div style={{ ...s.modalBody, display: "flex", flexDirection: "column", gap: 16 }}>
                
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <label style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8" }}>Company Name *</label>
                  <input
                    required
                    type="text"
                    placeholder="e.g. HDFC Bank, TCS, Reliance Industries"
                    value={portfolioAddForm.company_name}
                    onChange={e => setPortfolioAddForm(prev => ({ ...prev, company_name: e.target.value }))}
                    style={s.input}
                  />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    <label style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8" }}>Exchange</label>
                    <select
                      value={portfolioAddForm.exchange}
                      onChange={e => setPortfolioAddForm(prev => ({ ...prev, exchange: e.target.value }))}
                      style={{
                        ...s.input,
                        background: "#050811",
                        height: 38
                      }}
                    >
                      <option value="NSE">NSE</option>
                      <option value="BSE">BSE</option>
                      <option value="NASDAQ">NASDAQ</option>
                      <option value="NYSE">NYSE</option>
                    </select>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    <label style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8" }}>Investment Date</label>
                    <input
                      type="date"
                      value={portfolioAddForm.investment_date || ""}
                      onChange={e => setPortfolioAddForm(prev => ({ ...prev, investment_date: e.target.value }))}
                      style={s.input}
                    />
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    <label style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8" }}>Quantity *</label>
                    <input
                      required
                      type="number"
                      step="any"
                      min="0.0001"
                      placeholder="e.g. 100"
                      value={portfolioAddForm.quantity}
                      onChange={e => setPortfolioAddForm(prev => ({ ...prev, quantity: e.target.value }))}
                      style={s.input}
                    />
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    <label style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8" }}>Average Buy Price *</label>
                    <input
                      required
                      type="number"
                      step="any"
                      min="0.01"
                      placeholder="e.g. 1650"
                      value={portfolioAddForm.average_buy_price}
                      onChange={e => setPortfolioAddForm(prev => ({ ...prev, average_buy_price: e.target.value }))}
                      style={s.input}
                    />
                  </div>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <label style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8" }}>Portfolio Tags (comma-separated)</label>
                  <input
                    type="text"
                    placeholder="e.g. core, long-term, banking"
                    onChange={e => setPortfolioAddForm(prev => ({
                      ...prev,
                      tags: e.target.value.split(",").map(t => t.trim()).filter(Boolean)
                    }))}
                    style={s.input}
                  />
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <label style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8" }}>Notes</label>
                  <textarea
                    rows={3}
                    placeholder="Enter manual analysis or trade rationale notes..."
                    value={portfolioAddForm.notes}
                    onChange={e => setPortfolioAddForm(prev => ({ ...prev, notes: e.target.value }))}
                    style={{ ...s.input, resize: "none" }}
                  />
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 12 }}>
                  <button
                    type="button"
                    onClick={() => setPortfolioAddModalOpen(false)}
                    style={{
                      background: "none",
                      border: "1px solid #1e293b",
                      color: "#94a3b8",
                      padding: "10px 18px",
                      borderRadius: 8,
                      fontSize: 13,
                      fontWeight: 600,
                      cursor: "pointer"
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    style={{
                      ...s.btnPrimary,
                      background: "linear-gradient(135deg, #10b981, #059669)"
                    }}
                  >
                    Save Holding
                  </button>
                </div>

              </div>
            </form>
          </div>
        </div>
      )}

      {/* FEATURE 7: Holding Timeline Modal */}
      {holdingTimelineOpen && (
        <div style={s.modalOverlay} onClick={() => setHoldingTimelineOpen(false)}>
          <div style={{ ...s.modalContent, maxWidth: 600 }} onClick={e => e.stopPropagation()}>
            <div style={s.modalHeader}>
              <div>
                <span style={s.modalTitleBadge}>CHRONOLOGICAL TIMELINE ACTIVITIES</span>
                <h3 style={s.modalTitle}>Holding History: {holdingTimelineCo}</h3>
              </div>
              <button style={s.modalCloseBtn} onClick={() => setHoldingTimelineOpen(false)}>✕</button>
            </div>
            
            <div style={{ ...s.modalBody, maxHeight: "60vh" }}>
              {holdingTimelineLoading ? (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, padding: "40px 0" }}>
                  <div style={s.spinnerBig} />
                  <span style={{ fontSize: 12, color: "#64748b" }}>Compiling timeline intelligence feeds...</span>
                </div>
              ) : holdingTimelineData.length === 0 ? (
                <div style={{ color: "#64748b", fontSize: 12, textAlign: "center", padding: "40px 0" }}>
                  No recent News, Smart Alerts, or Research Documents found for this holding.
                </div>
              ) : (
                <div style={s.timelineContainer}>
                  {holdingTimelineData.map((item, idx) => (
                    <div key={idx} style={s.timelineItem}>
                      <div style={{ ...s.timelineDot, background: item.color }} />
                      <div style={s.timelineDate}>{item.date}</div>
                      <div style={s.timelineContentCard}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                          <span style={{
                            background: `${item.color}15`,
                            color: item.color,
                            fontSize: 9,
                            fontWeight: 700,
                            padding: "2px 6px",
                            borderRadius: 4,
                            border: `1px solid ${item.color}33`,
                            textTransform: "uppercase"
                          }}>
                            {item.type}
                          </span>
                          <span style={{ fontSize: 8, color: "#64748b", fontWeight: 700 }}>
                            {item.badge}
                          </span>
                        </div>
                        <h4 style={{ fontSize: 12, fontWeight: 600, color: "#f1f5f9", margin: 0, lineHeight: 1.4 }}>
                          {item.title}
                        </h4>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}


      {/* AI Summary Bloomberg-style Modal */}
      {selectedPostForSummary && (
        <div style={s.modalOverlay} onClick={() => setSelectedPostForSummary(null)}>
          <div style={s.modalContent} onClick={e => e.stopPropagation()}>
            <div style={s.modalHeader}>
              <div>
                <span style={s.modalTitleBadge}>AI INTELLIGENCE REPORT</span>
                <h3 style={s.modalTitle}>{selectedPostForSummary.title}</h3>
              </div>
              <button style={s.modalCloseBtn} onClick={() => setSelectedPostForSummary(null)}>✕</button>
            </div>
            
            <div style={s.modalBody}>
              <div style={s.modalMetaGrid}>
                <div><strong>Source:</strong> <SourceBadge source_id={selectedPostForSummary.source_id} /></div>
                <div><strong>Published:</strong> {formatTimestamp(selectedPostForSummary.posted_at || selectedPostForSummary.fetched_at).dateTimeStr}</div>
                <div><strong>Sentiment:</strong> 
                  <span style={{
                    marginLeft: 6,
                    padding: "2px 8px",
                    borderRadius: 4,
                    fontWeight: "bold",
                    fontSize: 10,
                    color: (SENTIMENT_COLORS[(selectedPostForSummary.sentiment || "").toUpperCase()] || SENTIMENT_COLORS.NEUTRAL).text,
                    backgroundColor: (SENTIMENT_COLORS[(selectedPostForSummary.sentiment || "").toUpperCase()] || SENTIMENT_COLORS.NEUTRAL).bg,
                    border: `1px solid ${(SENTIMENT_COLORS[(selectedPostForSummary.sentiment || "").toUpperCase()] || SENTIMENT_COLORS.NEUTRAL).border}`
                  }}>
                    {(selectedPostForSummary.sentiment || "").toUpperCase() || "NEUTRAL"}
                    {selectedPostForSummary.sentiment_confidence !== undefined && selectedPostForSummary.sentiment_confidence !== null && (
                      ` (${Math.round(selectedPostForSummary.sentiment_confidence * 100)}%)`
                    )}
                  </span>
                </div>
                <div><strong>Importance Score:</strong> 
                  <span style={{
                    marginLeft: 6,
                    fontWeight: 800,
                    color: IMPORTANCE_COLOR(selectedPostForSummary.importance_score)
                  }}>
                    {selectedPostForSummary.importance_score} / 100
                  </span>
                </div>
                <div><strong>Predict Direction:</strong> 
                  {selectedPostForSummary.predicted_direction ? (
                    <span style={{
                      marginLeft: 6,
                      fontWeight: "bold",
                      color: (PREDICTION_COLORS[selectedPostForSummary.predicted_direction] || PREDICTION_COLORS.NEUTRAL).text
                    }}>
                      {(PREDICTION_COLORS[selectedPostForSummary.predicted_direction] || PREDICTION_COLORS.NEUTRAL).icon} {selectedPostForSummary.predicted_direction} 
                      {selectedPostForSummary.prediction_confidence !== undefined && (
                        ` (${Math.round(selectedPostForSummary.prediction_confidence * 100)}%)`
                      )}
                    </span>
                  ) : "None"}
                </div>
                <div><strong>Event Type:</strong> 
                  <span style={{
                    marginLeft: 6,
                    fontSize: 10,
                    padding: "2px 6px",
                    borderRadius: 4,
                    background: "#1e293b",
                    color: "#94a3b8"
                  }}>
                    {selectedPostForSummary.event_type || "OTHER"}
                  </span>
                </div>
              </div>

              {selectedPostForSummary.entities && Object.values(selectedPostForSummary.entities).some(arr => arr && arr.length > 0) && (
                <div style={{ marginTop: 12, borderBottom: "1px solid #1e293b", paddingBottom: 12 }}>
                  <strong>Related Tags: </strong>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 6 }}>
                    {Object.entries(selectedPostForSummary.entities).flatMap(([cat, names]) => 
                      (names || []).map(name => (
                        <span key={`${cat}-${name}`} style={s.clickableEntityTag}>{name}</span>
                      ))
                    )}
                  </div>
                </div>
              )}

              <div style={s.modalSummarySection}>
                <h4 style={s.modalSummaryTitle}>✨ Deep AI Analysis</h4>
                {postSummaryLoading ? (
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, padding: "20px 0" }}>
                    <div style={s.spinnerBig} />
                    <div style={{ fontSize: 12, color: "#64748b" }}>Querying Local AI Model...</div>
                  </div>
                ) : (
                  <div style={s.modalSummaryContent}>
                    {postSummaryContent ? (
                      postSummaryContent.split("\n\n").map((para, idx) => {
                        const lines = para.split("\n");
                        const titleLine = lines[0];
                        const isHeader = titleLine.endsWith(":") || titleLine.toLowerCase().startsWith("what happened") || titleLine.toLowerCase().startsWith("why it matters") || titleLine.toLowerCase().startsWith("market impact") || titleLine.toLowerCase().startsWith("key takeaway");
                        
                        if (isHeader) {
                          return (
                            <div key={idx} style={{ marginBottom: 16 }}>
                              <strong style={{ color: "#06b6d4", fontSize: 13, textTransform: "uppercase", letterSpacing: "0.05em", display: "block", marginBottom: 4 }}>
                                {titleLine}
                              </strong>
                              <div style={{ color: "#cbd5e1", fontSize: 13, lineHeight: 1.6, paddingLeft: 8, borderLeft: "2px solid #1e293b" }}>
                                {lines.slice(1).join("\n")}
                              </div>
                            </div>
                          );
                        }
                        
                        return (
                          <p key={idx} style={{ margin: "0 0 12px 0", color: "#cbd5e1", fontSize: 13, lineHeight: 1.6 }}>
                            {para}
                          </p>
                        );
                      })
                    ) : (
                      <div style={{ color: "#ef4444", fontSize: 12 }}>No summary text returned.</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Notification AI Summary Bloomberg-style Modal */}
      {selectedNotificationForSummary && (
        <div style={s.modalOverlay} onClick={() => setSelectedNotificationForSummary(null)}>
          <div style={s.modalContent} onClick={e => e.stopPropagation()}>
            <div style={s.modalHeader}>
              <div>
                <span style={s.modalTitleBadge}>NOTIFICATION AI ANALYSIS</span>
                <h3 style={s.modalTitle}>{selectedNotificationForSummary.title}</h3>
              </div>
              <button style={s.modalCloseBtn} onClick={() => setSelectedNotificationForSummary(null)}>✕</button>
            </div>
            
            <div style={s.modalBody}>
              <div style={s.modalMetaGrid}>
                <div><strong>Source:</strong> <SourceBadge source_id={selectedNotificationForSummary.source} /></div>
                <div><strong>Published:</strong> {formatTimestamp(selectedNotificationForSummary.posted_at || selectedNotificationForSummary.fetched_at, now).dateTimeStr}</div>
                <div><strong>Sentiment:</strong> <SentimentBadge sentiment={selectedNotificationForSummary.sentiment} /></div>
                <div><strong>Importance Score:</strong> 
                  <span style={{
                    marginLeft: 6,
                    fontWeight: 800,
                    color: IMPORTANCE_COLOR(selectedNotificationForSummary.importance_score)
                  }}>
                    {selectedNotificationForSummary.importance_score !== null ? `${selectedNotificationForSummary.importance_score} / 100` : "N/A"}
                  </span>
                </div>
                <div><strong>Event Type:</strong> 
                  <span style={{
                    marginLeft: 6,
                    fontSize: 10,
                    padding: "2px 6px",
                    borderRadius: 4,
                    background: "#1e293b",
                    color: "#94a3b8"
                  }}>
                    {selectedNotificationForSummary.event_type || "OTHER"}
                  </span>
                </div>
              </div>

              <div style={s.modalSummarySection}>
                <h4 style={s.modalSummaryTitle}>✨ Deep AI Analysis</h4>
                {selectedNotificationForSummary.loading ? (
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, padding: "20px 0" }}>
                    <div style={s.spinnerBig} />
                    <div style={{ fontSize: 13, color: "#94a3b8", fontWeight: "bold" }}>Generating AI Analysis...</div>
                    <div style={{ fontSize: 11, color: "#64748b" }}>Querying Local AI Model & updating database cache...</div>
                  </div>
                ) : selectedNotificationForSummary.error ? (
                  <div style={{ color: "#ef4444", fontSize: 13, padding: "20px 0", textAlign: "center", background: "#ef444408", border: "1px dashed #ef444433", borderRadius: 8, display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
                    <div style={{ fontSize: 24 }}>⚠️</div>
                    <div>{selectedNotificationForSummary.error}</div>
                    <button 
                      onClick={() => summarizeNotification(selectedNotificationForSummary.id)} 
                      style={{ ...s.btnPrimary, marginTop: 12, fontSize: 11, padding: "6px 14px", cursor: "pointer" }}
                    >
                      Retry
                    </button>
                  </div>
                ) : (
                  <div style={s.modalSummaryContent}>
                    {selectedNotificationForSummary.summary ? (
                      selectedNotificationForSummary.summary.split("\n\n").map((para, idx) => {
                        const lines = para.split("\n");
                        const titleLine = lines[0];
                        const isHeader = titleLine.endsWith(":") || 
                          titleLine.toLowerCase().startsWith("what happened") || 
                          titleLine.toLowerCase().startsWith("why it matters") || 
                          titleLine.toLowerCase().startsWith("market impact") || 
                          titleLine.toLowerCase().startsWith("trading implications") || 
                          titleLine.toLowerCase().startsWith("key takeaway") || 
                          titleLine.toLowerCase().startsWith("risk factors");
                        
                        if (isHeader) {
                          return (
                            <div key={idx} style={{ marginBottom: 16 }}>
                              <strong style={{ color: "#06b6d4", fontSize: 13, textTransform: "uppercase", letterSpacing: "0.05em", display: "block", marginBottom: 4 }}>
                                {titleLine}
                              </strong>
                              <div style={{ color: "#cbd5e1", fontSize: 13, lineHeight: 1.6, paddingLeft: 8, borderLeft: "2px solid #1e293b" }}>
                                {lines.slice(1).join("\n")}
                              </div>
                            </div>
                          );
                        }
                        
                        return (
                          <p key={idx} style={{ margin: "0 0 12px 0", color: "#cbd5e1", fontSize: 13, lineHeight: 1.6 }}>
                            {para}
                          </p>
                        );
                      })
                    ) : (
                      <div style={{ color: "#ef4444", fontSize: 12 }}>No summary text returned.</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Toast message rendering (Feature 8) */}
      {toastMessage && (
        <div style={{
          position: "fixed",
          bottom: 20,
          right: 20,
          background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
          color: "#fff",
          padding: "12px 24px",
          borderRadius: 8,
          boxShadow: "0 10px 15px -3px rgba(0,0,0,0.5)",
          zIndex: 99999,
          fontWeight: 600,
          fontSize: 13,
          animation: "fadeIn 0.2s ease-out"
        }}>
          {toastMessage}
        </div>
      )}

      {/* AI Daily Brief modal (Feature 6) */}
      {dailyBriefContent && (
        <div style={s.modalOverlay} onClick={() => setDailyBriefContent(null)}>
          <div style={{ ...s.modalContent, maxWidth: 650 }} onClick={e => e.stopPropagation()}>
            <div style={s.modalHeader}>
              <div>
                <span style={s.modalTitleBadge}>MARKETBEACON DAILY BRIEF</span>
                <h3 style={s.modalTitle}>Daily Executive Briefing</h3>
              </div>
              <button style={s.modalCloseBtn} onClick={() => setDailyBriefContent(null)}>✕</button>
            </div>
            <div style={{ ...s.modalBody, padding: "20px 24px", maxHeight: "70vh", overflowY: "auto" }}>
              <div style={{
                fontSize: 14,
                color: "#cbd5e1",
                whiteSpace: "pre-line",
                lineHeight: 1.7,
                fontFamily: "inherit"
              }}>
                {dailyBriefContent}
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Evidence Viewer modal (Phase C) */}
      {selectedSourceText && (
        <div style={s.modalOverlay} onClick={() => setSelectedSourceText(null)}>
          <div style={{ ...s.modalContent, maxWidth: 650 }} onClick={e => e.stopPropagation()}>
            <div style={s.modalHeader}>
              <div>
                <span style={s.modalTitleBadge}>📚 RAG SUPPORTING EVIDENCE</span>
                <h3 style={s.modalTitle}>{selectedSourceTitle}</h3>
              </div>
              <button style={s.modalCloseBtn} onClick={() => setSelectedSourceText(null)}>✕</button>
            </div>
            <div style={{ ...s.modalBody, padding: "24px", maxHeight: "65vh", overflowY: "auto" }}>
              <div style={{
                fontSize: 13,
                color: "#cbd5e1",
                whiteSpace: "pre-line",
                lineHeight: 1.6,
                fontFamily: "inherit",
                background: "#050811",
                border: "1px solid #1e293b",
                padding: "16px",
                borderRadius: 8
              }}>
                {selectedSourceText}
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

// ── Shared Filter & Navigation Components (Feature 5) ───────────────────────

function FilterBar({
  sources,
  selectedSource,
  onSourceChange,
  eventTypes,
  selectedEventType,
  onEventTypeChange,
  sectors,
  selectedSector,
  onSectorChange,
  dateRange,
  selectedDateRange,
  onDateRangeChange,
  importanceMin,
  selectedImportanceMin,
  onImportanceMinChange,
  severity,
  selectedSeverity,
  onSeverityChange,
  direction,
  selectedDirection,
  onDirectionChange,
  sentiment,
  selectedSentiment,
  onSentimentChange
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, background: "#0e1626", border: "1px solid #121b2e", borderRadius: 12, padding: 16, marginBottom: 20 }}>
      {/* Source Selector */}
      {sources && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: 11, color: "#475569", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Source:
          </span>
          <button onClick={() => onSourceChange("all")} style={{
            ...styles.filterBtn,
            background: selectedSource === "all" ? "#06b6d4" : "#111827",
            color: selectedSource === "all" ? "#fff" : "#94a3b8",
            border: selectedSource === "all" ? "1px solid #06b6d4" : "1px solid #1e293b",
          }}>
            All
          </button>
          {sources.map(src => {
            const meta = getSource(src);
            return (
              <button key={src} onClick={() => onSourceChange(src)} style={{
                ...styles.filterBtn,
                background: selectedSource === src ? `${meta.color}22` : "#111827",
                color: selectedSource === src ? meta.color : "#94a3b8",
                border: selectedSource === src ? `1px solid ${meta.color}` : "1px solid #1e293b",
              }}>
                {meta.flag} {meta.label}
              </button>
            );
          })}
        </div>
      )}

      {/* Secondary Dropdown Selectors */}
      {(eventTypes || sectors || dateRange || importanceMin !== undefined || severity !== undefined || direction !== undefined || sentiment !== undefined) && (
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center", borderTop: "1px solid #121b2e", paddingTop: 12 }}>
          {eventTypes && (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 11, color: "#475569", fontWeight: 700 }}>Event:</span>
              <select value={selectedEventType || "all"} onChange={e => onEventTypeChange(e.target.value)} style={styles.dropdownSelect}>
                <option value="all">All Events</option>
                {eventTypes.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          )}

          {sectors && (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 11, color: "#475569", fontWeight: 700 }}>Sector:</span>
              <select value={selectedSector || "all"} onChange={e => onSectorChange(e.target.value)} style={styles.dropdownSelect}>
                <option value="all">All Sectors</option>
                {sectors.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          )}

          {severity !== undefined && (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 11, color: "#475569", fontWeight: 700 }}>Severity:</span>
              <select value={selectedSeverity || "all"} onChange={e => onSeverityChange(e.target.value === "all" ? null : e.target.value)} style={styles.dropdownSelect}>
                <option value="all">All Severity</option>
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
          )}

          {importanceMin !== undefined && (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 11, color: "#475569", fontWeight: 700 }}>Min Score:</span>
              <select value={selectedImportanceMin || "all"} onChange={e => onImportanceMinChange(e.target.value === "all" ? null : parseInt(e.target.value))} style={styles.dropdownSelect}>
                <option value="all">All Scores</option>
                <option value="50">50+</option>
                <option value="75">75+</option>
                <option value="80">80+</option>
                <option value="90">90+</option>
              </select>
            </div>
          )}

          {dateRange !== undefined && (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 11, color: "#475569", fontWeight: 700 }}>Timeframe:</span>
              <select value={selectedDateRange || "all"} onChange={e => onDateRangeChange(e.target.value === "all" ? null : e.target.value)} style={styles.dropdownSelect}>
                <option value="all">All Time</option>
                <option value="today">Today</option>
                <option value="week">Past Week</option>
                <option value="month">Past Month</option>
              </select>
            </div>
          )}

          {direction !== undefined && (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 11, color: "#475569", fontWeight: 700 }}>Direction:</span>
              <select value={selectedDirection || "all"} onChange={e => onDirectionChange(e.target.value === "all" ? null : e.target.value)} style={styles.dropdownSelect}>
                <option value="all">All Directions</option>
                <option value="INBOUND">Inbound</option>
                <option value="OUTBOUND">Outbound</option>
              </select>
            </div>
          )}

          {sentiment !== undefined && (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 11, color: "#475569", fontWeight: 700 }}>Sentiment:</span>
              <select value={selectedSentiment || "all"} onChange={e => onSentimentChange(e.target.value === "all" ? null : e.target.value)} style={styles.dropdownSelect}>
                <option value="all">All Sentiments</option>
                <option value="BULLISH">Bullish</option>
                <option value="BEARISH">Bearish</option>
                <option value="NEUTRAL">Neutral</option>
              </select>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ActiveFilterChips({ filters, onRemove }) {
  const hasActive = Object.values(filters).some(v => v !== null && v !== undefined && v !== "all" && v !== "latest");
  if (!hasActive) return null;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", background: "#0e1626", padding: "10px 14px", borderRadius: 8, border: "1px solid #121b2e", flex: 1, marginRight: 12 }}>
      <span style={{ fontSize: 11, color: "#64748b", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
        Active Filters:
      </span>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {filters.severity && (
          <span style={styles.filterChip}>
            Severity: {filters.severity} <button onClick={() => onRemove("severity")} style={styles.filterChipClose}>×</button>
          </span>
        )}
        {filters.importanceMin && (
          <span style={styles.filterChip}>
            Min Importance: {filters.importanceMin} <button onClick={() => onRemove("importanceMin")} style={styles.filterChipClose}>×</button>
          </span>
        )}
        {filters.direction && (
          <span style={styles.filterChip}>
            Direction: {filters.direction} <button onClick={() => onRemove("direction")} style={styles.filterChipClose}>×</button>
          </span>
        )}
        {filters.source && filters.source !== "all" && (
          <span style={styles.filterChip}>
            Source: {getSource(filters.source).label} <button onClick={() => onRemove("source")} style={styles.filterChipClose}>×</button>
          </span>
        )}
        {filters.sort && filters.sort !== "latest" && (
          <span style={styles.filterChip}>
            Sort: {filters.sort === "oldest" ? "Oldest First" : filters.sort === "importance" ? "Highest Importance" : "Highest Confidence"} <button onClick={() => onRemove("sort")} style={styles.filterChipClose}>×</button>
          </span>
        )}
        {filters.eventType && filters.eventType !== "all" && (
          <span style={styles.filterChip}>
            Event: {filters.eventType} <button onClick={() => onRemove("eventType")} style={styles.filterChipClose}>×</button>
          </span>
        )}
        {filters.sector && filters.sector !== "all" && (
          <span style={styles.filterChip}>
            Sector: {filters.sector} <button onClick={() => onRemove("sector")} style={styles.filterChipClose}>×</button>
          </span>
        )}
        {filters.dateRange && (
          <span style={styles.filterChip}>
            Date: {filters.dateRange} <button onClick={() => onRemove("dateRange")} style={styles.filterChipClose}>×</button>
          </span>
        )}
        {filters.sentiment && filters.sentiment !== "all" && (
          <span style={styles.filterChip}>
            Sentiment: {filters.sentiment} <button onClick={() => onRemove("sentiment")} style={styles.filterChipClose}>×</button>
          </span>
        )}
        {filters.readStatus && filters.readStatus !== "all" && (
          <span style={styles.filterChip}>
            Status: {filters.readStatus === "unread" ? "Unread" : "Read"} <button onClick={() => onRemove("readStatus")} style={styles.filterChipClose}>×</button>
          </span>
        )}
      </div>
    </div>
  );
}

function SortDropdown({ value, onChange }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
      <span style={{ fontSize: 11, color: "#475569", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em" }}>
        Sort By:
      </span>
      <select 
        value={value} 
        onChange={e => onChange(e.target.value)} 
        style={styles.dropdownSelect}
      >
        <option value="latest">▼ Latest First</option>
        <option value="oldest">▼ Oldest First</option>
        <option value="importance">▼ Highest Importance</option>
        <option value="confidence">▼ Highest Confidence</option>
      </select>
    </div>
  );
}


// ── Secondary Layout Components ──────────────────────────────────────────────

function StatCard({ label, value, color, clickable, active, onClick }) {
  const cardStyle = {
    flex: 1,
    background: "#111827",
    border: active ? `1px solid ${color}` : "1px solid #1e293b",
    borderTop: active ? `3px solid ${color}` : `3px solid ${color}`,
    borderRadius: 12,
    padding: "18px 22px",
    cursor: clickable ? "pointer" : "default",
    boxShadow: active ? `0 0 15px ${color}33` : "none",
    transform: active ? "scale(1.02)" : "scale(1)",
    transition: "all 0.2s ease"
  };

  return (
    <div 
      style={cardStyle} 
      onClick={onClick}
      onMouseEnter={e => {
        if (clickable && !active) {
          e.currentTarget.style.transform = "scale(1.02)";
          e.currentTarget.style.boxShadow = `0 0 10px ${color}22`;
          e.currentTarget.style.borderColor = `${color}66`;
        }
      }}
      onMouseLeave={e => {
        if (clickable && !active) {
          e.currentTarget.style.transform = "scale(1)";
          e.currentTarget.style.boxShadow = "none";
          e.currentTarget.style.borderColor = "#1e293b";
        }
      }}
    >
      <div style={{ fontSize: 30, fontWeight: 800, color, fontFamily: "monospace", lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 11, color: active ? "#cbd5e1" : "#64748b", marginTop: 6, textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 700 }}>{label}</div>
    </div>
  );
}

function EmptyState({ msg }) {
  return (
    <div style={{ textAlign: "center", padding: "60px 20px", color: "#475569", fontSize: 14, border: "1px dashed #1e293b", borderRadius: 12 }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>📭</div>
      {msg}
    </div>
  );
}

function ImportanceBar({ score }) {
  const color = IMPORTANCE_COLOR(score);
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: 10, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>Importance</span>
        <span style={{ fontSize: 12, fontWeight: 700, color, fontFamily: "monospace" }}>{score}</span>
      </div>
      <div style={{ height: 4, background: "#1e293b", borderRadius: 99, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${score}%`, background: color, borderRadius: 99 }} />
      </div>
    </div>
  );
}

function EventBadge({ type }) {
  const color = EVENT_COLORS[type] || EVENT_COLORS.OTHER;
  return (
    <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 700, letterSpacing: "0.04em", color, background: `${color}18`, border: `1px solid ${color}33` }}>
      {type}
    </span>
  );
}

function SourceBadge({ source_id }) {
  const src = getSource(source_id);
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 700,
      color: src.color, background: `${src.color}15`,
      border: `1px solid ${src.color}22`,
    }}>
      {src.flag} {src.label}
    </span>
  );
}

function SentimentBadge({ sentiment }) {
  if (!sentiment) return null;
  const sUpper = sentiment.toUpperCase();
  const colors = SENTIMENT_COLORS[sUpper] || SENTIMENT_COLORS.NEUTRAL;
  return (
    <span style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 4,
      padding: "2px 8px",
      borderRadius: 4,
      fontSize: 10,
      fontWeight: 700,
      color: colors.text,
      background: colors.bg,
      border: `1px solid ${colors.border}`,
    }}>
      ● {sUpper}
    </span>
  );
}

function ImportanceBadge({ score }) {
  const numericScore = parseInt(score);
  if (isNaN(numericScore)) return null;
  
  let label = "Low";
  let color = "#10b981"; // green
  let emoji = "🟢";
  
  if (numericScore >= 90) {
    label = "Critical";
    color = "#ef4444"; // red
    emoji = "🔴";
  } else if (numericScore >= 75) {
    label = "High";
    color = "#f59e0b"; // orange
    emoji = "🟠";
  } else if (numericScore >= 50) {
    label = "Medium";
    color = "#eab308"; // yellow
    emoji = "🟡";
  }
  
  return (
    <span style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 4,
      padding: "2px 8px",
      borderRadius: 4,
      fontSize: 10,
      fontWeight: 700,
      color: color,
      background: `${color}15`,
      border: `1px solid ${color}33`,
    }}>
      {emoji} {label}
    </span>
  );
}


function ImpactBadge({ level }) {
  if (!level) return null;
  const colors = {
    LOW: "#64748b",
    MEDIUM: "#f59e0b",
    HIGH: "#ef4444",
    CRITICAL: "#991b1b"
  };
  const color = colors[level] || colors.LOW;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "2px 8px", borderRadius: 4, fontSize: 9, fontWeight: 800,
      color: color, background: `${color}15`, border: `1px solid ${color}33`,
      letterSpacing: "0.05em"
    }}>
      ⚡ {level}
    </span>
  );
}

function ConfidenceBadge({ score }) {
  if (score == null) return null;
  const displayScore = score > 1 ? score : parseInt(score * 100);
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "2px 6px", borderRadius: 4, fontSize: 9, fontWeight: 700,
      color: "#94a3b8", background: "#1e293b", border: "1px solid #334155"
    }}>
      🎯 {displayScore}% Conf
    </span>
  );
}

// ── Layout CSS-in-JS Styles ──────────────────────────────────────────────────

const styles = {
  root: { display: "flex", minHeight: "100vh", background: "#060a13", fontFamily: "'Inter', 'Segoe UI', sans-serif", color: "#e2e8f0" },
  sidebar: { background: "#0a0f1d", borderRight: "1px solid #121b2e", display: "flex", flexDirection: "column", position: "sticky", top: 0, height: "100vh", overflowX: "hidden", flexShrink: 0 },
  logoRow: { display: "flex", alignItems: "center", gap: 12, padding: "20px 16px", cursor: "pointer", borderBottom: "1px solid #121b2e" },
  logoIcon: { width: 32, height: 32, borderRadius: 8, flexShrink: 0, background: "linear-gradient(135deg, #06b6d4, #3b82f6)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 800, color: "#fff", letterSpacing: "0.05em" },
  logoText: { fontSize: 14, fontWeight: 700, color: "#f1f5f9", whiteSpace: "nowrap" },
  navBtn: { width: "100%", display: "flex", alignItems: "center", padding: "12px 20px", border: "none", cursor: "pointer", transition: "all 0.15s", textAlign: "left" },
  badge: { display: "inline-flex", alignItems: "center", justifyContent: "center", marginLeft: 8, minWidth: 18, height: 18, borderRadius: 99, background: "#ef4444", color: "#fff", fontSize: 9, fontWeight: 700, padding: "0 4px" },
  sidebarFooter: { padding: "16px 20px", borderTop: "1px solid #121b2e" },
  main: { flex: 1, display: "flex", flexDirection: "column", minWidth: 0 },
  topbar: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 32px", borderBottom: "1px solid #121b2e", background: "#0a0f1d", position: "sticky", top: 0, zIndex: 10 },
  pageTitle: { fontSize: 18, fontWeight: 700, color: "#f1f5f9" },
  pageSubtitle: { fontSize: 11, color: "#475569", marginTop: 2 },
  topbarRight: { display: "flex", alignItems: "center", gap: 8 },
  statusDot: { width: 8, height: 8, borderRadius: "50%", background: "#10b981", boxShadow: "0 0 8px #10b981" },
  content: { padding: "24px 32px", flex: 1, maxWidth: 1200 },
  statsRow: { display: "flex", gap: 16, marginBottom: 20 },
  card: { background: "#0e1626", border: "1px solid #121b2e", borderRadius: 12, padding: "20px 22px" },
  cardHeader: { fontSize: 15, fontWeight: 700, color: "#e2e8f0" },
  cardSub: { fontSize: 12, color: "#475569", marginTop: 4 },
  grid3: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 14 },
  grid2: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 14 },
  summaryCard: { background: "#0e1626", border: "1px solid #121b2e", borderRadius: 12, padding: "16px 20px" },
  summaryTitle: { fontSize: 14, fontWeight: 600, color: "#f1f5f9", lineHeight: 1.5, marginTop: 8 },
  summaryMeta: { fontSize: 11, color: "#64748b", display: "flex", gap: 6, marginTop: 4, marginBottom: 8 },
  reasoningBlock: { fontSize: 12, color: "#cbd5e1", marginTop: 8, lineHeight: 1.5, borderLeft: "2px solid #06b6d4", paddingLeft: 10, background: "#1e293b33", padding: "6px 10px", borderRadius: "0 6px 6px 0" },
  clickableEntityTag: { fontSize: 9, padding: "2px 6px", borderRadius: 4, background: "#1e293b", color: "#94a3b8", cursor: "pointer", border: "1px solid #334155", display: "inline-block" },
  alertCard: { background: "#0e1626", border: "1px solid #121b2e", borderRadius: 12, padding: "18px" },
  alertTitle: { fontSize: 13, fontWeight: 600, color: "#e2e8f0", lineHeight: 1.5, marginTop: 10 },
  input: { width: "100%", background: "#050811", border: "1px solid #121b2e", borderRadius: 8, padding: "10px 14px", color: "#e2e8f0", fontSize: 13, outline: "none", boxSizing: "border-box", fontFamily: "inherit" },
  btnPrimary: { background: "linear-gradient(135deg, #06b6d4, #3b82f6)", color: "#fff", border: "none", borderRadius: 8, padding: "10px 18px", fontSize: 13, fontWeight: 600, cursor: "pointer", whiteSpace: "nowrap", display: "flex", alignItems: "center", gap: 8 },
  btnDelete: { background: "#ef444415", color: "#ef4444", border: "1px solid #ef444433", borderRadius: 6, padding: "4px 8px", fontSize: 11, fontWeight: 600, cursor: "pointer" },
  filterBtn: { padding: "4px 10px", borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: "pointer", whiteSpace: "nowrap" },
  watchlistTagContainer: { display: "flex", alignItems: "center", gap: 6, background: "#06b6d412", border: "1px solid #06b6d433", borderRadius: 6, padding: "4px 10px", color: "#06b6d4", fontSize: 12, fontWeight: 600 },
  watchlistTagDelete: { background: "none", border: "none", color: "#ef4444", cursor: "pointer", fontWeight: "bold", marginLeft: 4, padding: 0 },
  sidebarPanel: { background: "#0a0f1d", border: "1px solid #121b2e", borderRadius: 12, padding: "12px 8px", display: "flex", flexDirection: "column", gap: 4 },
  sidebarItemBtn: { width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 12px", border: "none", cursor: "pointer", transition: "all 0.15s", background: "transparent", borderRadius: 6, color: "#cbd5e1" },
  timelineContainer: { display: "flex", flexDirection: "column", gap: 16, borderLeft: "2px solid #1e293b", paddingLeft: 16, position: "relative" },
  timelineItem: { display: "flex", flexDirection: "column", position: "relative", marginBottom: 8 },
  timelineDot: { width: 10, height: 10, borderRadius: "50%", background: "#06b6d4", position: "absolute", left: -22, top: 4, border: "2px solid #060a13" },
  timelineDate: { fontSize: 11, color: "#06b6d4", fontWeight: 700, marginBottom: 4 },
  timelineContentCard: { background: "#0e1626", border: "1px solid #121b2e", borderRadius: 8, padding: "12px 14px" },
  reportSectionHeader: { fontSize: 14, color: "#06b6d4", fontWeight: 700, borderBottom: "1px solid #1e293b", paddingBottom: 6, marginBottom: 10 },
  spinner: { display: "inline-block", width: 12, height: 12, border: "2px solid #ffffff44", borderTop: "2px solid #fff", borderRadius: "50%", animation: "spin 0.7s linear infinite" },
  spinnerBig: { display: "inline-block", width: 32, height: 32, border: "4px solid #06b6d422", borderTop: "4px solid #06b6d4", borderRadius: "50%", animation: "spin 0.8s linear infinite" },
  btnSummaryAI: { background: "linear-gradient(135deg, #a855f7, #6366f1)", color: "#fff", border: "none", borderRadius: 6, padding: "6px 12px", fontSize: 12, fontWeight: 600, cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 6, transition: "transform 0.1s ease" },
  modalOverlay: { position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(3, 7, 18, 0.85)", backdropFilter: "blur(4px)", display: "flex", alignItems: "center", justifyBox: "center", zIndex: 9999, justifyContent: "center" },
  modalContent: { background: "#0b0f19", border: "1px solid #1e293b", borderRadius: 16, width: "90%", maxWidth: 650, boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)", overflow: "hidden", animation: "fadeIn 0.2s ease-out" },
  modalHeader: { padding: "20px 24px", borderBottom: "1px solid #1e293b", display: "flex", justifyContent: "space-between", alignItems: "flex-start" },
  modalTitleBadge: { background: "linear-gradient(135deg, #a855f7, #6366f1)", color: "#fff", fontSize: 9, fontWeight: 800, padding: "2px 8px", borderRadius: 4, letterSpacing: "0.08em", display: "inline-block", marginBottom: 8 },
  modalTitle: { fontSize: 16, fontWeight: 700, color: "#f8fafc", margin: 0, lineHeight: 1.4 },
  modalCloseBtn: { background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 18, padding: 4, transition: "color 0.1s ease" },
  modalBody: { padding: "20px 24px 28px", maxHeight: "70vh", overflowY: "auto" },
  modalMetaGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px 16px", fontSize: 12, color: "#94a3b8", borderBottom: "1px solid #1e293b", paddingBottom: 16 },
  modalSummarySection: { marginTop: 20, background: "#0e1626", border: "1px solid #121b2e", borderRadius: 12, padding: 16 },
  modalSummaryTitle: { fontSize: 13, fontWeight: 700, color: "#cbd5e1", margin: "0 0 12px 0" },
  modalSummaryContent: { whiteSpace: "pre-line" },
  filterChip: { display: "inline-flex", alignItems: "center", gap: 6, background: "#06b6d418", border: "1px solid #06b6d444", borderRadius: 6, padding: "4px 8px", color: "#06b6d4", fontSize: 11, fontWeight: 600 },
  filterChipClose: { background: "none", border: "none", color: "#ef4444", cursor: "pointer", fontWeight: "bold", padding: 0, fontSize: 13, marginLeft: 2, display: "inline-flex", alignItems: "center", justifyContent: "center", lineHeight: 1 },
  dropdownSelect: { background: "#111827", color: "#cbd5e1", border: "1px solid #1e293b", borderRadius: 6, padding: "4px 8px", fontSize: 12, fontWeight: 500, outline: "none", cursor: "pointer" },
};