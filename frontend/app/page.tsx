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
    <main className="min-h-screen bg-gray-100 p-8 text-gray-900">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-300">
          <h1 className="text-3xl font-extrabold text-gray-900">eBay Arbitrage Engine</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column */}
          <div className="col-span-1 space-y-8">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-300">
              <h2 className="text-lg font-bold mb-4 text-gray-800 border-b pb-2">New Search Target</h2>
              <form onSubmit={handleAddConfig} className="space-y-4">
                <input type="text" placeholder="Search Term" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full border border-gray-300 p-2 rounded" />
                <div className="grid grid-cols-2 gap-4">
                  <input type="number" placeholder="Min %" value={minProfitPct} onChange={(e) => setMinProfitPct(Number(e.target.value))} className="border border-gray-300 p-2 rounded" />
                  <input type="number" placeholder="Min £" value={minProfitFlat} onChange={(e) => setMinProfitFlat(Number(e.target.value))} className="border border-gray-300 p-2 rounded" />
                </div>
                <button className="w-full bg-blue-600 text-white p-2 rounded font-bold hover:bg-blue-700">Save Target</button>
              </form>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-300">
              <h2 className="text-lg font-bold mb-4 text-gray-800 border-b pb-2">Your Targets</h2>
              <ul className="space-y-2">
                {configs.map((c) => (
                  <li key={c.id} className="flex justify-between items-center p-3 border border-gray-300 rounded hover:bg-gray-50 cursor-pointer" onClick={() => setActiveConfigId(c.id)}>
                    <span className="font-medium">{c.search_term}</span>
                    <button onClick={(e) => handleRunSingleCheck(c.id, e)} className="text-blue-600 text-sm font-bold bg-blue-50 px-2 py-1 rounded">
                      {runningConfigId === c.id ? "Running..." : "▶ Run"}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Right Column */}
          <div className="col-span-2 bg-white p-6 rounded-lg shadow-sm border border-gray-300">
            <h2 className="text-lg font-bold mb-4 text-gray-800 border-b pb-2">Opportunities</h2>
            <table className="w-full text-left">
              <thead>
                <tr className="text-sm border-b border-gray-200 bg-gray-50">
                  <th className="p-3">Item</th>
                  <th className="p-3">Price</th>
                  <th className="p-3">Profit</th>
                  <th className="p-3">Link</th>
                </tr>
              </thead>
              <tbody>
                {opportunities.map((opp) => (
                  <tr key={opp.id} className="border-b border-gray-100 text-sm hover:bg-gray-50">
                    <td className="p-3 font-medium">{opp.fb_title}</td>
                    <td className="p-3">£{opp.fb_price.toFixed(2)}</td>
                    <td className="p-3 font-bold text-green-600">£{opp.calculated_profit.toFixed(2)}</td>
                    <td className="p-3"><a href={opp.fb_url} target="_blank" className="text-blue-600 underline">View</a></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  );
}