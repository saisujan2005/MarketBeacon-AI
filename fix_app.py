import os

def main():
    filepath = os.path.join("frontend", "src", "App.jsx")
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    start_anchor = "      {/* Right Bloomberg Panel (Feature 1, 2) */}"
    end_anchor = "         {/* Explain Engine Right sliding panel (Feature 15) */}"

    start_idx = content.find(start_anchor)
    if start_idx == -1:
        print(f"Error: Start anchor '{start_anchor}' not found.")
        return

    end_idx = content.find(end_anchor)
    if end_idx == -1:
        print(f"Error: End anchor '{end_anchor}' not found.")
        return

    # Keep start_anchor in place, replace the middle
    new_panel = """      {/* Right Bloomberg Panel (Feature 1, 2) */}
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
                 <div style={{
                   width: 24,
                   height: 24,
                   border: "2px solid #06b6d420",
                   borderTopColor: "#06b6d4",
                   borderRadius: "50%",
                   animation: "spin 0.8s linear infinite"
                 }} />
                 <div style={{ fontSize: 12, color: "#64748b" }}>Generating AI Analysis...</div>
               </div>
             ) : rightPanelContent.error ? (
               <div style={{ color: "#ef4444", fontSize: 13, textAlign: "center" }}>
                 {rightPanelContent.error}
               </div>
             ) : rightPanelContent.type === "bulk" ? (
               <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                 <div style={{ fontSize: 13, color: "#cbd5e1", whiteSpace: "pre-line", lineHeight: 1.6 }}>
                   {rightPanelContent.summary}
                 </div>
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
             )}
          </div>
        )}
\n"""

    # We replace from start_anchor to end_anchor
    updated_content = content[:start_idx] + new_panel + content[end_idx:]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("Successfully restored rightPanelContent block in App.jsx.")

if __name__ == "__main__":
    main()
