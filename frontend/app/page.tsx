"use client";

import { useState, useEffect } from "react";

export default function Dashboard() {
  const [searchTerm, setSearchTerm] = useState("");
  const [minProfitPct, setMinProfitPct] = useState(20);
  const [minProfitFlat, setMinProfitFlat] = useState(15);
  
  const [configs, setConfigs] = useState<any[]>([]);
  const [activeConfigId, setActiveConfigId] = useState<number | null>(null); 
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch all configs on page load
  useEffect(() => {
    fetchConfigs();
  }, []);

  // Auto-fetch opportunities when a new config is selected
  useEffect(() => {
    if (activeConfigId) {
      fetchOpportunities(activeConfigId);
    }
  }, [activeConfigId]);

  const fetchConfigs = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/configs/");
      const data = await res.json();
      setConfigs(data);
    } catch (err) {
      console.error("Failed to fetch configs:", err);
    }
  };

  const handleAddConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch("http://127.0.0.1:8000/api/configs/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          search_term: searchTerm,
          min_profit_percentage: minProfitPct,
          min_profit_flat: minProfitFlat,
          is_active: true
        })
      });
      const data = await res.json();
      setSearchTerm(""); // Clear form
      fetchConfigs(); // Refresh the list
      setActiveConfigId(data.id); // Auto-select the new config
    } catch (err) {
      console.error(err);
      alert("Failed to add configuration.");
    }
  };

  const handleDeleteConfig = async (id: number) => {
    if (!confirm("Are you sure you want to delete this target?")) return;
    try {
      await fetch(`http://127.0.0.1:8000/api/configs/${id}`, { method: "DELETE" });
      if (activeConfigId === id) {
        setActiveConfigId(null);
        setOpportunities([]);
      }
      fetchConfigs(); // Refresh the list
    } catch (err) {
      console.error(err);
      alert("Failed to delete configuration.");
    }
  };

  const fetchOpportunities = async (id: number) => {
    setLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/configs/${id}/opportunities`);
      const data = await res.json();
      setOpportunities(data.data || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <main className="min-h-screen bg-gray-50 p-8 text-gray-900">
      <div className="max-w-6xl mx-auto space-y-8">
        <h1 className="text-3xl font-bold text-blue-600">Arbitrage Engine Dashboard</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column: Form & Saved Configs */}
          <div className="col-span-1 space-y-8">
            
            {/* Create Form */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h2 className="text-xl font-semibold mb-4">New Search Target</h2>
              <form onSubmit={handleAddConfig} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Search Term</label>
                  <input 
                    type="text" 
                    value={searchTerm} 
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full border p-2 rounded"
                    placeholder="e.g. MacBook Pro M2"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Min Profit %</label>
                    <input 
                      type="number" 
                      value={minProfitPct} 
                      onChange={(e) => setMinProfitPct(Number(e.target.value))}
                      className="w-full border p-2 rounded"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Min Profit ($)</label>
                    <input 
                      type="number" 
                      value={minProfitFlat} 
                      onChange={(e) => setMinProfitFlat(Number(e.target.value))}
                      className="w-full border p-2 rounded"
                    />
                  </div>
                </div>
                <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 font-medium transition-colors">
                  Save Target
                </button>
              </form>
            </div>

            {/* Saved Configurations List */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h2 className="text-xl font-semibold mb-4">Your Targets</h2>
              {configs.length === 0 ? (
                <p className="text-sm text-gray-500 italic">No targets saved yet.</p>
              ) : (
                <ul className="space-y-3">
                  {configs.map((config) => (
                    <li 
                      key={config.id} 
                      className={`flex justify-between items-center p-3 border rounded-lg cursor-pointer transition-colors ${activeConfigId === config.id ? 'bg-blue-50 border-blue-400' : 'hover:bg-gray-50'}`}
                    >
                      <div className="flex-1 overflow-hidden pr-4" onClick={() => setActiveConfigId(config.id)}>
                        <p className="font-medium truncate">{config.search_term}</p>
                        <p className="text-xs text-gray-500">Min: {config.min_profit_percentage}% | ${config.min_profit_flat}</p>
                      </div>
                      <button 
                        onClick={() => handleDeleteConfig(config.id)}
                        className="text-red-500 hover:text-red-700 text-sm font-semibold px-2"
                      >
                        Delete
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* Right Column: Opportunities Viewer */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 col-span-1 lg:col-span-2">
            <div className="flex justify-between items-center mb-6 border-b pb-4">
              <div>
                <h2 className="text-xl font-semibold">Found Opportunities</h2>
                {activeConfigId && (
                  <p className="text-sm text-gray-500 mt-1">
                    Viewing results for: <span className="font-medium text-blue-600">{configs.find(c => c.id === activeConfigId)?.search_term}</span>
                  </p>
                )}
              </div>
              <button 
                onClick={() => activeConfigId && fetchOpportunities(activeConfigId)}
                disabled={!activeConfigId || loading}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:bg-gray-300 font-medium transition-colors text-sm"
              >
                {loading ? "Loading..." : "Refresh Data"}
              </button>
            </div>

            {!activeConfigId ? (
              <div className="text-center text-gray-500 py-12 bg-gray-50 rounded border border-dashed">
                Select a target from the list to view its opportunities.
              </div>
            ) : opportunities.length === 0 ? (
              <div className="text-center text-gray-500 py-12 bg-gray-50 rounded border border-dashed">
                No opportunities found yet. Wait for the background worker to run!
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b bg-gray-50 text-sm">
                      <th className="py-3 px-4 rounded-tl-lg">Item</th>
                      <th className="py-3 px-4">FB Price</th>
                      <th className="py-3 px-4">eBay Value</th>
                      <th className="py-3 px-4 text-green-600">Net Profit</th>
                      <th className="py-3 px-4 rounded-tr-lg">Action</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm">
                    {opportunities.map((opp) => (
                      <tr key={opp.id} className="border-b hover:bg-gray-50">
                        <td className="py-4 px-4 font-medium max-w-[200px] truncate" title={opp.fb_title}>{opp.fb_title}</td>
                        <td className="py-4 px-4">${opp.fb_price.toFixed(2)}</td>
                        <td className="py-4 px-4">${opp.ebay_median_sold.toFixed(2)}</td>
                        <td className="py-4 px-4 font-bold text-green-600">${opp.calculated_profit.toFixed(2)}</td>
                        <td className="py-4 px-4">
                          <a 
                            href={opp.fb_url} 
                            target="_blank" 
                            rel="noreferrer"
                            className="bg-blue-100 text-blue-700 px-3 py-1.5 rounded-full hover:bg-blue-200 transition-colors font-medium text-xs whitespace-nowrap"
                          >
                            View Listing &rarr;
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}