import React, { useState } from 'react';

export default function Custom({ onBack }) {
  const [products, setProducts] = useState([{ url: '', name: '', qty: 1 }]);
  const [coupon, setCoupon] = useState('');
  const [reorder, setReorder] = useState(1);
  const [selectedProfiles, setSelectedProfiles] = useState([1, 2, 3]);
  const [profileInput, setProfileInput] = useState('');
  const [parallel, setParallel] = useState(3);

  const allProfiles = Array.from({ length: 20 }, (_, i) => i + 1);

  const addProduct = () => {
    if (products.length < 20) {
      setProducts([...products, { url: '', name: '', qty: 1 }]);
    }
  };

  const removeProduct = (i) => {
    if (products.length > 1) {
      setProducts(products.filter((_, idx) => idx !== i));
    }
  };

  const updateProduct = (i, field, value) => {
    const newP = [...products];
    newP[i][field] = value;
    setProducts(newP);
  };

  const toggleProfile = (num) => {
    if (selectedProfiles.includes(num)) {
      setSelectedProfiles(selectedProfiles.filter(p => p !== num));
    } else {
      setSelectedProfiles([...selectedProfiles, num].sort((a, b) => a - b));
    }
  };

  const parseProfileInput = () => {
    try {
      const selected = [];
      const parts = profileInput.split(',');
      
      parts.forEach(part => {
        if (part.includes('-')) {
          const [start, end] = part.split('-').map(n => parseInt(n.trim()));
          for (let i = start; i <= end; i++) {
            if (i >= 1 && i <= 20 && !selected.includes(i)) {
              selected.push(i);
            }
          }
        } else {
          const num = parseInt(part.trim());
          if (num >= 1 && num <= 20 && !selected.includes(num)) {
            selected.push(num);
          }
        }
      });
      
      setSelectedProfiles(selected.sort((a, b) => a - b));
      setProfileInput('');
    } catch (e) {
      alert('Invalid input format!');
    }
  };

  const handleSubmit = async () => {
  const payload = {
    mode: 'custom',
    products: products.filter(p => p.url && p.name),
    coupon_code: coupon,
    reorder_count: parseInt(reorder),
    profiles: selectedProfiles.map(n => `Profile ${n}`), // ✅ Array of strings
    parallel_browsers: parseInt(parallel),
    headless: false
  };
  
  try {
    const response = await fetch('http://localhost:8006/api/start-automation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
      alert(`✅ ${data.message}`);
    } else {
      alert(`❌ Error: ${data.message}`);
    }
  } catch (error) {
    alert(`❌ Failed to connect: ${error.message}`);
  }
};

  return (
    <div className="min-h-screen bg-white">
      <div className="border-b-2 border-gray-900 bg-gray-900 text-white p-4">
        <button onClick={onBack} className="text-white hover:underline mb-2">← Back to Menu</button>
        <h1 className="text-2xl font-bold">⚙️ CUSTOM Mode</h1>
        <p className="text-sm text-gray-300">Select specific profiles</p>
      </div>

      <div className="max-w-4xl mx-auto p-6 space-y-6">
        {/* Profile Selection */}
        <div className="border-2 border-gray-900 rounded p-4">
          <h3 className="font-bold text-xl mb-4">Select Profiles ({selectedProfiles.length} selected)</h3>
          
          <div className="mb-4">
            <label className="block font-bold mb-2">Quick Input (e.g., 1,3,5,7-10)</label>
            <div className="flex gap-2">
              <input 
                value={profileInput}
                onChange={(e) => setProfileInput(e.target.value)}
                placeholder="1,3,5,7-10"
                className="flex-1 border border-gray-900 rounded p-2"
              />
              <button 
                onClick={parseProfileInput}
                className="border-2 border-gray-900 rounded px-4 hover:bg-gray-900 hover:text-white"
              >
                Add
              </button>
            </div>
          </div>

          <div className="grid grid-cols-10 gap-2">
            {allProfiles.map(num => (
              <button
                key={num}
                onClick={() => toggleProfile(num)}
                className={`p-2 border-2 rounded font-bold ${
                  selectedProfiles.includes(num)
                    ? 'bg-gray-900 text-white border-gray-900'
                    : 'border-gray-300 hover:border-gray-900'
                }`}
              >
                {num}
              </button>
            ))}
          </div>

          <div className="mt-4 flex gap-2">
            <button 
              onClick={() => setSelectedProfiles(allProfiles)}
              className="flex-1 border-2 border-gray-900 rounded p-2 hover:bg-gray-900 hover:text-white"
            >
              Select All
            </button>
            <button 
              onClick={() => setSelectedProfiles([])}
              className="flex-1 border-2 border-red-600 rounded p-2 hover:bg-red-600 hover:text-white"
            >
              Clear All
            </button>
          </div>
        </div>

        {/* Products */}
        <div className="border-2 border-gray-900 rounded p-4">
          <h3 className="font-bold text-xl mb-4">Products ({products.length}/20)</h3>
          {products.map((p, i) => (
            <div key={i} className="border border-gray-300 rounded p-3 mb-3 bg-gray-50">
              <div className="flex justify-between mb-2">
                <span className="font-bold">Product {i + 1}</span>
                {products.length > 1 && (
                  <button onClick={() => removeProduct(i)} className="text-red-600 font-bold">✕</button>
                )}
              </div>
              <input 
                placeholder="Product Name" 
                className="w-full border border-gray-900 rounded p-2 mb-2" 
                value={p.name} 
                onChange={(e) => updateProduct(i, 'name', e.target.value)} 
              />
              <input 
                placeholder="Product URL" 
                className="w-full border border-gray-900 rounded p-2 mb-2"
                value={p.url} 
                onChange={(e) => updateProduct(i, 'url', e.target.value)} 
              />
              <input 
                type="number" 
                placeholder="Quantity" 
                className="w-full border border-gray-900 rounded p-2"
                value={p.qty} 
                onChange={(e) => updateProduct(i, 'qty', e.target.value)} 
              />
            </div>
          ))}
          <button 
            onClick={addProduct} 
            disabled={products.length >= 20}
            className="w-full border-2 border-gray-900 rounded p-2 hover:bg-gray-900 hover:text-white disabled:opacity-50"
          >
            + Add Product
          </button>
        </div>

        {/* Settings */}
        <div className="grid grid-cols-3 gap-4">
          <div className="border-2 border-gray-900 rounded p-4">
            <label className="block font-bold mb-2">Coupon Code</label>
            <input 
              value={coupon} 
              onChange={(e) => setCoupon(e.target.value.toUpperCase())} 
              className="w-full border border-gray-900 rounded p-2" 
              placeholder="Optional" 
            />
          </div>
          <div className="border-2 border-gray-900 rounded p-4">
            <label className="block font-bold mb-2">Reorder Count</label>
            <input 
              type="number" 
              min="1" 
              max="5" 
              value={reorder} 
              onChange={(e) => setReorder(Math.min(5, e.target.value))}
              className="w-full border border-gray-900 rounded p-2" 
            />
          </div>
          <div className="border-2 border-gray-900 rounded p-4">
            <label className="block font-bold mb-2">Parallel Browsers</label>
            <input 
              type="number" 
              min="1" 
              max="10" 
              value={parallel} 
              onChange={(e) => setParallel(e.target.value)}
              className="w-full border border-gray-900 rounded p-2" 
            />
          </div>
        </div>

        <button 
          onClick={handleSubmit}
          disabled={selectedProfiles.length === 0}
          className="w-full bg-gray-900 text-white p-4 rounded text-xl font-bold hover:bg-gray-700 disabled:opacity-50"
        >
          START AUTOMATION
        </button>
      </div>
    </div>
  );
}