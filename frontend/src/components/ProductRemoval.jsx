import React, { useState } from 'react';

export default function ProductRemoval({ onBack }) {
  const [start, setStart] = useState(1);
  const [end, setEnd] = useState(5);
  const [parallel, setParallel] = useState(3);

  const handleSubmit = async () => {
  const payload = {
    profiles: {
      start: Number(start),
      end: Number(end)
    },
    parallel_browsers: Number(parallel)
  };

  try {
    const res = await fetch("http://localhost:8006/api/remove-products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    alert(data.status === "success" ? `✅ ${data.message}` : `❌ ${data.message}`);
  } catch (err) {
    alert("❌ Error: " + err.message);
  }
};

  return (
    <div className="min-h-screen bg-white">
      <div className="border-b-2 border-red-600 bg-red-600 text-white p-4">
        <button onClick={onBack} className="text-white hover:underline mb-2">← Back to Menu</button>
        <h1 className="text-2xl font-bold">🗑️ Product Removal</h1>
        <p className="text-sm text-gray-100">Clean cart for selected profiles</p>
      </div>

      <div className="max-w-4xl mx-auto p-6 space-y-6">
        {/* Warning Box */}
        <div className="border-2 border-red-600 bg-red-50 rounded p-6">
          <h3 className="font-bold text-xl mb-3 text-red-900">⚠️ This will:</h3>
          <div className="space-y-2 text-red-800">
            <p className="flex items-center gap-2">
              <span className="font-bold">•</span> Remove all applied coupons
            </p>
            <p className="flex items-center gap-2">
              <span className="font-bold">•</span> Save all products for later
            </p>
            <p className="flex items-center gap-2">
              <span className="font-bold">•</span> Clear cart completely
            </p>
          </div>
        </div>

        {/* Profile Range */}
        <div className="border-2 border-gray-900 rounded p-6">
          <h3 className="font-bold text-xl mb-4">Profile Range</h3>
          
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block font-bold mb-2">Start Profile</label>
              <input 
                type="number" 
                min="1" 
                max="20" 
                value={start} 
                onChange={(e) => setStart(Math.max(1, Math.min(20, parseInt(e.target.value) || 1)))}
                className="w-full border border-gray-900 rounded p-2" 
              />
            </div>
            
            <div>
              <label className="block font-bold mb-2">End Profile</label>
              <input 
                type="number" 
                min="1" 
                max="20" 
                value={end} 
                onChange={(e) => setEnd(Math.max(start, Math.min(20, parseInt(e.target.value) || 1)))}
                className="w-full border border-gray-900 rounded p-2" 
              />
            </div>

            <div>
              <label className="block font-bold mb-2">Parallel Browsers</label>
              <input 
                type="number" 
                min="1" 
                max="10" 
                value={parallel} 
                onChange={(e) => setParallel(Math.max(1, Math.min(10, parseInt(e.target.value) || 1)))}
                className="w-full border border-gray-900 rounded p-2" 
              />
            </div>
          </div>

          <div className="mt-4 p-3 bg-gray-100 rounded border border-gray-300">
            <p className="text-sm text-gray-700">
              <strong>Selected:</strong> {end - start + 1} profiles (Profile {start} to Profile {end})
            </p>
            <p className="text-sm text-gray-700 mt-1">
              <strong>Parallel:</strong> {parallel} browsers at a time
            </p>
          </div>
        </div>

        {/* Info Box */}
        <div className="border-2 border-blue-600 bg-blue-50 rounded p-4">
          <h4 className="font-bold mb-2">ℹ️ How it works:</h4>
          <ol className="space-y-1 text-sm text-gray-700">
            <li>1. Opens JioMart cart for each profile</li>
            <li>2. Removes any applied coupon codes</li>
            <li>3. Clicks "Save for Later" on all products</li>
            <li>4. Verifies cart is empty</li>
          </ol>
        </div>

        {/* Action Button */}
        <button 
          onClick={handleSubmit}
          className="w-full bg-red-600 text-white p-4 rounded text-xl font-bold hover:bg-red-700"
        >
          START REMOVAL
        </button>

        {/* Disclaimer */}
        <div className="text-center text-xs text-gray-500">
          <p>⚠️ This action cannot be undone. Products will be saved for later, not deleted.</p>
        </div>
      </div>
    </div>
  );
}