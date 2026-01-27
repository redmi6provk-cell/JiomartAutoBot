import React, { useState } from 'react';

export default function SingleTest({ onBack }) {
  const [products, setProducts] = useState([{ url: '', name: '', qty: 1 }]);
  const [coupon, setCoupon] = useState('');
  const [reorder, setReorder] = useState(1);
  const [profileNum, setProfileNum] = useState(1);

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

 const handleSubmit = async () => {
  const payload = {
    mode: "single_test",
    products: products.filter(p => p.url && p.name),
    coupon_code: coupon,
    reorder_count: Number(reorder),
    profile: `Profile ${profileNum}`,  // ✅ Single profile
    headless: false
  };

  try {
    const res = await fetch("http://localhost:8006/api/start-automation", {
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
      <div className="border-b-2 border-gray-900 bg-gray-900 text-white p-4">
        <button onClick={onBack} className="text-white hover:underline mb-2">← Back to Menu</button>
        <h1 className="text-2xl font-bold">🎯 SINGLE TEST Mode</h1>
        <p className="text-sm text-gray-300">Test with one profile</p>
      </div>

      <div className="max-w-4xl mx-auto p-6 space-y-6">
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
        <div className="grid grid-cols-2 gap-4">
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
            <label className="block font-bold mb-2">Reorder Count (Max 5)</label>
            <input 
              type="number" 
              min="1" 
              max="5" 
              value={reorder} 
              onChange={(e) => setReorder(Math.min(5, e.target.value))}
              className="w-full border border-gray-900 rounded p-2" 
            />
          </div>
        </div>

        {/* Profile Selection */}
        <div className="border-2 border-gray-900 rounded p-4">
          <label className="block font-bold mb-2">Test Profile Number</label>
          <input 
            type="number" 
            min="1" 
            max="20" 
            value={profileNum} 
            onChange={(e) => setProfileNum(Math.max(1, Math.min(20, e.target.value)))}
            className="w-full border border-gray-900 rounded p-2" 
          />
          <p className="text-sm text-gray-600 mt-2">Testing with: Profile {profileNum}</p>
        </div>

        <div className="border-2 border-orange-600 bg-orange-50 rounded p-4">
          <p className="text-sm"><strong>Note:</strong> This mode is for testing. Only one profile will be used.</p>
        </div>

        <button 
          onClick={handleSubmit} 
          className="w-full bg-gray-900 text-white p-4 rounded text-xl font-bold hover:bg-gray-700"
        >
          START TEST
        </button>
      </div>
    </div>
  );
}