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
  const [runningConfigId, setRunningConfigId] = useState<number | null>(null);

  useEffect(() => { fetchConfigs(); }, []);
  useEffect(() => { if (activeConfigId) fetchOpportunities(activeConfigId); }, [activeConfigId]);

  const fetchConfigs = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/configs/");
      const data = await res.json();
      setConfigs(data);
    } catch (err) { console.error("Failed to fetch configs:", err); }
  };

  const handleAddConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch("http://127.0.0.1:8000/api/configs/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        search_term: searchTerm, 
        min_profit_percentage: minProfitPct, 
        min_profit_flat: minProfitFlat, 
        is_active: true 
      })
    });
    setSearchTerm("");
    fetchConfigs();
  };

  const handleDeleteConfig = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering the row click
    if (!confirm("Are you sure you want to delete this target?")) return;
    
    try {
      await fetch(`http://127.0.0.1:8000/api/configs/${id}`, { method: "DELETE" });
      fetchConfigs();
      
      // Clear the opportunities view if we delete the currently active config
      if (activeConfigId === id) {
        setActiveConfigId(null);
        setOpportunities([]);
      }
    } catch (err) { console.error("Failed to delete config:", err); }
  };

  const fetchOpportunities = async (id: number) => {
    setLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/configs/${id}/opportunities`);
      const data = await res.json();
      setOpportunities(data.data || []);
    } catch (err) { console.error(err); }
    setLoading(false);
  };

  const handleRunSingleCheck = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setRunningConfigId(id);
    setActiveConfigId(id);
    await fetch(`http://127.0.0.1:8000/api/configs/${id}/run`, { method: "POST" });
    setTimeout(() => setRunningConfigId(null), 2000);
  };

  return (
    <main className="min-h-screen bg-gray-900 p-8 text-gray-100">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700">
          <h1 className="text-3xl font-extrabold text-white">eBay Arbitrage Engine</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column */}
          <div className="col-span-1 space-y-8">
            <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700">
              <h2 className="text-lg font-bold mb-4 text-gray-200 border-b border-gray-600 pb-2">New Search Target</h2>
              <form onSubmit={handleAddConfig} className="space-y-4">
                
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Search Term</label>
                  <input 
                    type="text" 
                    placeholder="e.g. Nintendo Switch OLED" 
                    value={searchTerm} 
                    onChange={(e) => setSearchTerm(e.target.value)} 
                    className="w-full bg-gray-700 border border-gray-600 text-white p-2 rounded focus:ring focus:ring-blue-500 focus:outline-none" 
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">Min Profit (%)</label>
                    <input 
                      type="number" 
                      value={minProfitPct} 
                      onChange={(e) => setMinProfitPct(Number(e.target.value))} 
                      className="w-full bg-gray-700 border border-gray-600 text-white p-2 rounded focus:ring focus:ring-blue-500 focus:outline-none" 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">Min Profit (£)</label>
                    <input 
                      type="number" 
                      value={minProfitFlat} 
                      onChange={(e) => setMinProfitFlat(Number(e.target.value))} 
                      className="w-full bg-gray-700 border border-gray-600 text-white p-2 rounded focus:ring focus:ring-blue-500 focus:outline-none" 
                    />
                  </div>
                </div>
                <button className="w-full bg-blue-600 text-white p-2 rounded font-bold hover:bg-blue-700 transition-colors mt-2">
                  Save Target
                </button>
              </form>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700">
              <h2 className="text-lg font-bold mb-4 text-gray-200 border-b border-gray-600 pb-2">Your Targets</h2>
              <ul className="space-y-2">
                {configs.map((c) => (
                  <li 
                    key={c.id} 
                    className={`flex justify-between items-center p-3 border rounded cursor-pointer transition-colors ${
                      activeConfigId === c.id 
                        ? 'border-blue-500 bg-gray-700' 
                        : 'border-gray-600 hover:bg-gray-700'
                    }`} 
                    onClick={() => setActiveConfigId(c.id)}
                  >
                    <span className="font-medium text-gray-200">{c.search_term}</span>
                    <div className="flex gap-2">
                      <button 
                        onClick={(e) => handleRunSingleCheck(c.id, e)} 
                        className="text-blue-300 text-xs font-bold bg-blue-900/50 px-2 py-1 rounded hover:bg-blue-800/60 transition-colors"
                      >
                        {runningConfigId === c.id ? "Running..." : "▶ Run"}
                      </button>
                      <button 
                        onClick={(e) => handleDeleteConfig(c.id, e)} 
                        className="text-red-300 text-xs font-bold bg-red-900/50 px-2 py-1 rounded hover:bg-red-800/60 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </li>
                ))}
                {configs.length === 0 && (
                  <p className="text-sm text-gray-400 italic">No targets saved yet.</p>
                )}
              </ul>
            </div>
          </div>

          {/* Right Column */}
          <div className="col-span-2 bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700">
            <h2 className="text-lg font-bold mb-4 text-gray-200 border-b border-gray-600 pb-2">
              Opportunities {activeConfigId && `- ID: ${activeConfigId}`}
            </h2>
            
            {loading ? (
              <p className="text-gray-400">Loading opportunities...</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="text-sm border-b border-gray-600 text-gray-400">
                      <th className="p-3 font-semibold">Item</th>
                      <th className="p-3 font-semibold">Price</th>
                      <th className="p-3 font-semibold">Profit</th>
                      <th className="p-3 font-semibold">Link</th>
                    </tr>
                  </thead>
                  <tbody>
                    {opportunities.length > 0 ? (
                      opportunities.map((opp) => (
                        <tr key={opp.id} className="border-b border-gray-700 text-sm hover:bg-gray-750 transition-colors">
                          <td className="p-3 font-medium text-gray-200">{opp.fb_title}</td>
                          <td className="p-3 text-gray-300">£{opp.fb_price.toFixed(2)}</td>
                          <td className="p-3 font-bold text-green-400">£{opp.calculated_profit.toFixed(2)}</td>
                          <td className="p-3">
                            <a href={opp.fb_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 underline">
                              View
                            </a>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="p-4 text-center text-gray-500 italic">
                          No opportunities found for this target.
                        </td>
                      </tr>
                    )}
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