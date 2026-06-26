import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/\-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export default function Settings() {
  const {
    user,
    updateProfile,
    updatePreferences,
    updatePassword,
    deleteAccount,
    logout
  } = useAuth();

  const [activeTab, setActiveTab] = useState("profile");
  
  // Profile Form States
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [timezone, setTimezone] = useState(user?.timezone || "UTC");
  const [preferredMarket, setPreferredMarket] = useState(user?.preferred_market || "US");
  const [profilePicture, setProfilePicture] = useState(user?.profile_picture || "");
  const [profileMessage, setProfileMessage] = useState("");

  // Security Form States
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [securityMessage, setSecurityMessage] = useState("");
  const [securityError, setSecurityError] = useState("");

  // Preferences Form States
  const [theme, setTheme] = useState(user?.preferences?.theme || "dark");
  const [language, setLanguage] = useState(user?.preferences?.language || "en");
  const [defaultAiModel, setDefaultAiModel] = useState(user?.preferences?.default_ai_model || "llama-3.3-70b-versatile");
  const [marketRegion, setMarketRegion] = useState(user?.preferences?.market_region || "US");
  const [notificationsEnabled, setNotificationsEnabled] = useState(user?.preferences?.notifications_enabled !== false);
  const [emailNotifications, setEmailNotifications] = useState(user?.preferences?.email_notifications !== false);
  const [dashboardLayout, setDashboardLayout] = useState(user?.preferences?.dashboard_layout || "default");
  const [dailyBriefTime, setDailyBriefTime] = useState(user?.preferences?.daily_brief_time || "08:00");
  
  // New Expanded preferences
  const [pushNotifications, setPushNotifications] = useState(user?.preferences?.push_notifications !== false);
  const [morningBrief, setMorningBrief] = useState(user?.preferences?.morning_brief !== false);
  const [eveningSummary, setEveningSummary] = useState(user?.preferences?.evening_summary !== false);
  const [smartAlerts, setSmartAlerts] = useState(user?.preferences?.smart_alerts !== false);
  const [watchlistAlerts, setWatchlistAlerts] = useState(user?.preferences?.watchlist_alerts !== false);
  const [portfolioAlerts, setPortfolioAlerts] = useState(user?.preferences?.portfolio_alerts !== false);
  const [weeklyDigest, setWeeklyDigest] = useState(user?.preferences?.weekly_digest !== false);
  const [quietHoursEnabled, setQuietHoursEnabled] = useState(user?.preferences?.quiet_hours_enabled === true);
  const [quietHoursStart, setQuietHoursStart] = useState(user?.preferences?.quiet_hours_start || "22:00");
  const [quietHoursEnd, setQuietHoursEnd] = useState(user?.preferences?.quiet_hours_end || "08:00");
  const [prefTimezone, setPrefTimezone] = useState(user?.preferences?.timezone || "UTC");
  
  const [prefMessage, setPrefMessage] = useState("");

  // Danger Zone
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setProfileMessage("");
    try {
      await updateProfile({
        full_name: fullName,
        timezone,
        preferred_market: preferredMarket,
        profile_picture: profilePicture
      });
      setProfileMessage("Profile updated successfully!");
      setTimeout(() => setProfileMessage(""), 3000);
    } catch (err) {
      setProfileMessage("Error updating profile: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleUpdateSecurity = async (e) => {
    e.preventDefault();
    setSecurityMessage("");
    setSecurityError("");
    if (newPassword.length < 8) {
      setSecurityError("New password must be at least 8 characters long.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setSecurityError("New passwords do not match.");
      return;
    }
    try {
      await updatePassword({
        old_password: oldPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
      });
      setSecurityMessage("Password updated successfully!");
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setTimeout(() => setSecurityMessage(""), 3000);
    } catch (err) {
      setSecurityError(err.response?.data?.detail || "Failed to update password. Check old password.");
    }
  };

  const handleUpdatePreferences = async (e) => {
    e.preventDefault();
    setPrefMessage("");
    try {
      await updatePreferences({
        theme,
        language,
        default_ai_model: defaultAiModel,
        market_region: marketRegion,
        notifications_enabled: notificationsEnabled,
        email_notifications: emailNotifications,
        dashboard_layout: dashboardLayout,
        daily_brief_time: dailyBriefTime,
        push_notifications: pushNotifications,
        morning_brief: morningBrief,
        evening_summary: eveningSummary,
        smart_alerts: smartAlerts,
        watchlist_alerts: watchlistAlerts,
        portfolio_alerts: portfolioAlerts,
        weekly_digest: weeklyDigest,
        quiet_hours_enabled: quietHoursEnabled,
        quiet_hours_start: quietHoursStart,
        quiet_hours_end: quietHoursEnd,
        timezone: prefTimezone
      });
      setPrefMessage("Preferences saved successfully!");
      setTimeout(() => setPrefMessage(""), 3000);
    } catch (err) {
      setPrefMessage("Error saving preferences: " + err.message);
    }
  };

  const handlePushToggle = async (checked) => {
    setPushNotifications(checked);
    if (checked) {
      try {
        if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
          alert("Browser Push Notifications are not supported in this browser.");
          setPushNotifications(false);
          return;
        }

        const permission = await Notification.requestPermission();
        if (permission !== "granted") {
          alert("Permission for browser notifications was denied.");
          setPushNotifications(false);
          return;
        }

        const registration = await navigator.serviceWorker.ready;
        let subscription = await registration.pushManager.getSubscription();
        
        if (!subscription) {
          // Standard public VAPID key
          const vapidPublicKey = "BDp_k9sL_V8oD4p3o39WGdyb3FY3miM1xjKhA2wGcGFXpZSUrAm"; 
          subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
          });
        }

        await api.post("/api/notifications/push-subscribe", subscription);
        setPrefMessage("Browser push notifications registered successfully!");
        setTimeout(() => setPrefMessage(""), 3000);
      } catch (err) {
        console.error("Failed to register browser push:", err);
        setPrefMessage("Failed to register push subscription.");
        setPushNotifications(false);
      }
    } else {
      try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        if (subscription) {
          await subscription.unsubscribe();
          await api.post("/api/notifications/push-unsubscribe", { endpoint: subscription.endpoint });
          setPrefMessage("Browser push notifications disabled.");
          setTimeout(() => setPrefMessage(""), 3000);
        }
      } catch (err) {
        console.error("Failed to unsubscribe:", err);
      }
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText.toLowerCase() === "delete my account") {
      try {
        await deleteAccount();
      } catch (err) {
        alert("Failed to delete account: " + err.message);
      }
    } else {
      alert("Confirmation phrase does not match.");
    }
  };

  return (
    <div className="settings-page-container">
      <div className="settings-sidebar">
        <h2 className="sidebar-heading">Settings</h2>
        <button className={`settings-tab-btn ${activeTab === "profile" ? "active" : ""}`} onClick={() => setActiveTab("profile")}>
          👤 Profile Settings
        </button>
        <button className={`settings-tab-btn ${activeTab === "security" ? "active" : ""}`} onClick={() => setActiveTab("security")}>
          🔒 Security & Password
        </button>
        <button className={`settings-tab-btn ${activeTab === "preferences" ? "active" : ""}`} onClick={() => setActiveTab("preferences")}>
          🎨 Appearance & AI
        </button>
        <button className={`settings-tab-btn tab-danger ${activeTab === "danger" ? "active" : ""}`} onClick={() => setActiveTab("danger")}>
          ⚠️ Danger Zone
        </button>
      </div>

      <div className="settings-content-panel glass-panel">
        {activeTab === "profile" && (
          <form onSubmit={handleUpdateProfile} className="settings-form">
            <h3>Profile Settings</h3>
            <p className="form-subheading">Update your user details and preferences.</p>
            
            {profileMessage && <div className="settings-alert success">{profileMessage}</div>}

            <div className="form-group">
              <label>Full Name</label>
              <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
            </div>

            <div className="form-group">
              <label>Email Address (Unchangeable)</label>
              <input type="email" value={user?.email || ""} disabled style={{ cursor: "not-allowed", opacity: 0.6 }} />
            </div>

            <div className="form-group">
              <label>Timezone</label>
              <select value={timezone} onChange={(e) => setTimezone(e.target.value)}>
                <option value="UTC">UTC (Universal Coordinated Time)</option>
                <option value="IST">IST (Indian Standard Time)</option>
                <option value="EST">EST (Eastern Standard Time)</option>
                <option value="PST">PST (Pacific Standard Time)</option>
                <option value="GMT">GMT (Greenwich Mean Time)</option>
              </select>
            </div>

            <div className="form-group">
              <label>Preferred Market Region</label>
              <select value={preferredMarket} onChange={(e) => setPreferredMarket(e.target.value)}>
                <option value="US">United States (Wall Street)</option>
                <option value="India">India (NSE/BSE)</option>
                <option value="Crypto">Cryptocurrency</option>
                <option value="Global">Global Macro</option>
              </select>
            </div>

            <div className="form-group">
              <label>Avatar / Profile Image URL</label>
              <input type="url" placeholder="https://example.com/avatar.jpg" value={profilePicture} onChange={(e) => setProfilePicture(e.target.value)} />
            </div>

            <button type="submit" className="btn-primary">Save Profile</button>
          </form>
        )}

        {activeTab === "security" && (
          <form onSubmit={handleUpdateSecurity} className="settings-form">
            <h3>Security & Password</h3>
            <p className="form-subheading">Update your password to keep your account secure.</p>
            
            {securityMessage && <div className="settings-alert success">{securityMessage}</div>}
            {securityError && <div className="settings-alert error">{securityError}</div>}

            <div className="form-group">
              <label>Old Password</label>
              <input type="password" placeholder="••••••••" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} required />
            </div>

            <div className="form-group">
              <label>New Password (min 8 characters)</label>
              <input type="password" placeholder="••••••••" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
            </div>

            <div className="form-group">
              <label>Confirm New Password</label>
              <input type="password" placeholder="••••••••" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
            </div>

            <button type="submit" className="btn-primary">Update Password</button>
          </form>
        )}

        {activeTab === "preferences" && (
          <form onSubmit={handleUpdatePreferences} className="settings-form">
            <h3>Appearance & AI Customization</h3>
            <p className="form-subheading">Personalize your terminal layouts and model parameters.</p>

            {prefMessage && <div className="settings-alert success">{prefMessage}</div>}

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1.5rem", marginBottom: "2rem" }}>
              <div>
                <h4 style={{ margin: "0 0 1rem 0", color: "#00f2fe", fontSize: "14px", textTransform: "uppercase" }}>Core Settings</h4>
                <div className="form-group">
                  <label>Default AI Model</label>
                  <select value={defaultAiModel} onChange={(e) => setDefaultAiModel(e.target.value)}>
                    <option value="llama-3.3-70b-versatile">Llama 3.3 70B Versatile (Default)</option>
                    <option value="mixtral-8x7b-32768">Mixtral 8x7B (High-Speed)</option>
                    <option value="deepseek-r1-distill-llama-70b">DeepSeek R1 (Deep Reasoner)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Theme</label>
                  <select value={theme} onChange={(e) => setTheme(e.target.value)}>
                    <option value="dark">Dark Theme (Bloomberg Premium)</option>
                    <option value="glass">Glassmorphic Glow</option>
                    <option value="black">Amoled Black</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Daily Brief Time (24h Format)</label>
                  <input type="time" value={dailyBriefTime} onChange={(e) => setDailyBriefTime(e.target.value)} />
                </div>
                
                <div className="form-group">
                  <label>Timezone</label>
                  <select value={prefTimezone} onChange={(e) => setPrefTimezone(e.target.value)}>
                    <option value="UTC">UTC (Universal Coordinated Time)</option>
                    <option value="IST">IST (Indian Standard Time)</option>
                    <option value="EST">EST (Eastern Standard Time)</option>
                    <option value="PST">PST (Pacific Standard Time)</option>
                    <option value="GMT">GMT (Greenwich Mean Time)</option>
                  </select>
                </div>
              </div>

              <div>
                <h4 style={{ margin: "0 0 1rem 0", color: "#00f2fe", fontSize: "14px", textTransform: "uppercase" }}>Notification Channels</h4>
                <div className="checkbox-setting-row" style={{ marginBottom: "1rem" }}>
                  <label className="checkbox-container">
                    <input type="checkbox" checked={notificationsEnabled} onChange={(e) => setNotificationsEnabled(e.target.checked)} />
                    <span className="checkmark"></span>
                    Master Notifications Enable
                  </label>
                </div>

                <div className="checkbox-setting-row" style={{ marginBottom: "1rem" }}>
                  <label className="checkbox-container">
                    <input type="checkbox" checked={emailNotifications} onChange={(e) => setEmailNotifications(e.target.checked)} />
                    <span className="checkmark"></span>
                    Enable Email Alerts
                  </label>
                </div>

                <div className="checkbox-setting-row" style={{ marginBottom: "1rem" }}>
                  <label className="checkbox-container">
                    <input type="checkbox" checked={pushNotifications} onChange={(e) => handlePushToggle(e.target.checked)} />
                    <span className="checkmark"></span>
                    Enable Browser Push Notifications
                  </label>
                </div>

                <h4 style={{ margin: "1.5rem 0 1rem 0", color: "#00f2fe", fontSize: "14px", textTransform: "uppercase" }}>Alert Subscriptions</h4>
                <div style={{ display: "grid", gap: "0.75rem" }}>
                  <label className="checkbox-container" style={{ fontSize: "13px" }}>
                    <input type="checkbox" checked={morningBrief} onChange={(e) => setMorningBrief(e.target.checked)} />
                    <span className="checkmark"></span>
                    Daily Morning Brief
                  </label>
                  <label className="checkbox-container" style={{ fontSize: "13px" }}>
                    <input type="checkbox" checked={eveningSummary} onChange={(e) => setEveningSummary(e.target.checked)} />
                    <span className="checkmark"></span>
                    Evening Market Summary
                  </label>
                  <label className="checkbox-container" style={{ fontSize: "13px" }}>
                    <input type="checkbox" checked={smartAlerts} onChange={(e) => setSmartAlerts(e.target.checked)} />
                    <span className="checkmark"></span>
                    Smart Alerts Inbound
                  </label>
                  <label className="checkbox-container" style={{ fontSize: "13px" }}>
                    <input type="checkbox" checked={watchlistAlerts} onChange={(e) => setWatchlistAlerts(e.target.checked)} />
                    <span className="checkmark"></span>
                    Watchlist Updates
                  </label>
                  <label className="checkbox-container" style={{ fontSize: "13px" }}>
                    <input type="checkbox" checked={portfolioAlerts} onChange={(e) => setPortfolioAlerts(e.target.checked)} />
                    <span className="checkmark"></span>
                    Portfolio Risk Alerts
                  </label>
                  <label className="checkbox-container" style={{ fontSize: "13px" }}>
                    <input type="checkbox" checked={weeklyDigest} onChange={(e) => setWeeklyDigest(e.target.checked)} />
                    <span className="checkmark"></span>
                    Weekly Research Digest
                  </label>
                </div>
              </div>
            </div>

            <div style={{ borderTop: "1px solid #1f2937", paddingTop: "1.5rem", marginBottom: "1.5rem" }}>
              <h4 style={{ margin: "0 0 1rem 0", color: "#00f2fe", fontSize: "14px", textTransform: "uppercase" }}>Quiet Hours</h4>
              <div className="checkbox-setting-row" style={{ marginBottom: "1rem" }}>
                <label className="checkbox-container">
                  <input type="checkbox" checked={quietHoursEnabled} onChange={(e) => setQuietHoursEnabled(e.target.checked)} />
                  <span className="checkmark"></span>
                  Enable Quiet Hours (Suppresses alerts during these times)
                </label>
              </div>

              {quietHoursEnabled && (
                <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label>Start Time</label>
                    <input type="time" value={quietHoursStart} onChange={(e) => setQuietHoursStart(e.target.value)} style={{ padding: "8px" }} />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label>End Time</label>
                    <input type="time" value={quietHoursEnd} onChange={(e) => setQuietHoursEnd(e.target.value)} style={{ padding: "8px" }} />
                  </div>
                </div>
              )}
            </div>

            <button type="submit" className="btn-primary" style={{ marginTop: "1rem" }}>Save Preferences</button>
          </form>
        )}

        {activeTab === "danger" && (
          <div className="settings-danger-zone">
            <h3>Danger Zone</h3>
            <p className="form-subheading text-danger">Actions here can lead to permanent loss of your conversations and indexed research files.</p>

            <div className="danger-panel glass-panel border-danger">
              <h4>Delete Account Permanently</h4>
              <p>Once you delete your account, there is no going back. All watchlists, documents, and chat logs will be wiped from our server.</p>
              
              <button className="btn-danger" onClick={() => setShowDeleteModal(true)}>
                Delete Account
              </button>
            </div>

            {showDeleteModal && (
              <div className="modal-backdrop">
                <div className="modal-card glass-panel border-danger">
                  <h3>Are you absolutely sure?</h3>
                  <p>This action cannot be undone. Please type <strong>delete my account</strong> to confirm deletion.</p>
                  
                  <input type="text" placeholder="delete my account" value={deleteConfirmText} onChange={(e) => setDeleteConfirmText(e.target.value)} className="input-danger-confirm" />

                  <div className="modal-actions" style={{ marginTop: "1.5rem" }}>
                    <button className="btn-secondary" onClick={() => { setShowDeleteModal(false); setDeleteConfirmText(""); }}>
                      Cancel
                    </button>
                    <button className="btn-danger" onClick={handleDeleteAccount}>
                      Delete Permanently
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
