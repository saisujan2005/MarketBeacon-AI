import { useEffect, useState } from "react";
import api from "./services/api";

function App() {
  const [alerts, setAlerts] = useState([]);

  const [summary, setSummary] = useState([]);

  const [trends, setTrends] = useState({});

  const [notifications, setNotifications] = useState([]);

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const [watchlists, setWatchlists] = useState([]);
  const [newKeyword, setNewKeyword] = useState("");

  useEffect(() => {

  api.get("/alerts")
    .then((response) => {
      setAlerts(response.data);
    });

  api.get("/market-summary")
    .then((response) => {
      setSummary(response.data.summary || []);
    });

  api.get("/trends")
    .then((response) => {
      setTrends(response.data);
    });

  api.get("/notifications")
    .then((response) => {
      setNotifications(response.data);
    });

  api.get("/watchlists")
  .then((response) => {
    setWatchlists(response.data);
  })
  .catch((error) => {
    console.error(error);
  });  

}, []);


  const askMarketBeacon = async () => {

  if (!question.trim()) return;

  setLoading(true);

  try {

    const response = await api.post("/ask", {
      question: question
    });

    setAnswer(response.data.answer);

  } catch (error) {

    console.error(error);

  }

  setLoading(false);
};  

  const addWatchlist = async () => {

  if (!newKeyword.trim()) return;

  try {

    await api.post("/watchlists", {
      keyword: newKeyword
    });

    const response = await api.get("/watchlists");

    setWatchlists(response.data);

    setNewKeyword("");

  } catch (error) {

    console.error(error);

  }
};


const deleteWatchlist = async (id) => {

  try {

    await api.delete(`/watchlists/${id}`);

    const response = await api.get("/watchlists");

    setWatchlists(response.data);

  } catch (error) {

    console.error(error);

  }
};

  return (
  <div className="min-h-screen bg-slate-100 p-8">

    <h1 className="text-5xl font-bold text-center mb-10">
      MarketBeacon AI
    </h1>

    {/* Market Summary */}

<div className="bg-white rounded-xl shadow-lg p-6 mb-8">

  <h2 className="text-2xl font-bold mb-4">
    📰 Today's Market Summary
  </h2>

  {summary.length === 0 ? (
    <p>No summary available</p>
  ) : (
    <div className="space-y-4">

      {summary.map((item, index) => (
        <div
          key={index}
          className="border-l-4 border-blue-500 pl-4 py-2"
        >
          <div className="font-semibold">
            {item.title}
          </div>

          <div className="text-sm text-gray-500 mt-1">
            {item.event_type} • Importance: {item.importance_score}
          </div>
        </div>
      ))}

    </div>
  )}

</div>

    {/* Alerts */}

    <h2 className="text-2xl font-semibold mb-6">
      🚨 Market Alerts
    </h2>

    {alerts.length === 0 ? (
      <p>No alerts found</p>
    ) : (
      <div className="grid md:grid-cols-3 gap-6">

        {alerts.map((alert, index) => (
          <div
            key={index}
            className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition"
          >

            <h3 className="font-bold text-lg mb-4">
              {alert.title}
            </h3>

            <div className="mb-2">
              <span className="font-semibold">
                Event Type:
              </span>{" "}
              {alert.event_type}
            </div>

            <div>
              <span className="font-semibold">
                Importance:
              </span>{" "}
              {alert.importance_score}
            </div>



           

          </div>
        ))}

      </div>
    )}

    {/*market trends */}

    <div className="mt-10">

  <h2 className="text-2xl font-semibold mb-6">
    📊 Market Trends
  </h2>

  <div className="grid md:grid-cols-3 gap-6">

    {Object.entries(trends).map(([key, value]) => (
      <div
        key={key}
        className="bg-white rounded-xl shadow-lg p-6"
      >
        <h3 className="font-bold text-lg">
          {key}
        </h3>

        <p className="text-3xl font-bold mt-2">
          {value}
        </p>
      </div>
    ))}

        </div>

      </div>

    <div className="mt-10">

  <h2 className="text-2xl font-semibold mb-6">
    🔔 Notifications
  </h2>

  {notifications.length === 0 ? (
    <p>No notifications found</p>
  ) : (
    <div className="grid md:grid-cols-2 gap-6">

      {notifications.map((notification, index) => (
        <div
          key={index}
          className="bg-white rounded-xl shadow-lg p-6"
        >

          <h3 className="font-bold text-lg mb-2">
            {notification.title}
          </h3>

          <p className="text-sm text-gray-500">
            Watchlist: {notification.keyword}
          </p>

          <p className="mt-2">
            Status: {notification.is_read ? "✅ Read" : "🔴 Unread"}
          </p>

        </div>
      ))}

    </div>
  )}

</div>

    <div className="mt-10 bg-white rounded-xl shadow-lg p-6">

  <h2 className="text-2xl font-bold mb-4">
    ⭐ Watchlists
  </h2>

  <div className="flex gap-4 mb-6">

    <input
      type="text"
      value={newKeyword}
      onChange={(e) => setNewKeyword(e.target.value)}
      placeholder="Add keyword..."
      className="border rounded-lg p-3 flex-1"
    />

    <button
      onClick={addWatchlist}
      className="bg-green-600 text-white px-4 py-2 rounded-lg"
    >
      Add
    </button>

  </div>

  <div className="grid md:grid-cols-3 gap-4">

    {watchlists.map((item) => (

      <div
        key={item.id}
        className="bg-slate-100 rounded-lg p-4 flex justify-between items-center"
      >

        <span className="font-semibold">
          {item.keyword}
        </span>

        <button
          onClick={() => deleteWatchlist(item.id)}
          className="bg-red-500 text-white px-3 py-1 rounded"
        >
          Delete
        </button>

      </div>

    ))}

  </div>

</div>

    <div className="mt-10 bg-white rounded-xl shadow-lg p-6">

  <h2 className="text-2xl font-bold mb-4">
    🤖 Ask MarketBeacon
  </h2>

  <input
    type="text"
    value={question}
    onChange={(e) => setQuestion(e.target.value)}
    placeholder="Ask about markets..."
    className="w-full border rounded-lg p-3 mb-4"
  />

  <button
    onClick={askMarketBeacon}
    className="bg-blue-600 text-white px-6 py-2 rounded-lg"
  >
    Ask
  </button>

  {loading && (
    <p className="mt-4">
      Thinking...
    </p>
  )}

  {answer && (
    <div className="mt-4 p-4 bg-slate-100 rounded-lg">
      {answer}
    </div>
  )}

</div>

     

  </div>
  )}

export default App;