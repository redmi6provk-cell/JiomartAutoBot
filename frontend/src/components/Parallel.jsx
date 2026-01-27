import React, { useState } from "react";

export default function Parallel({ onBack }) {
  const [products, setProducts] = useState([
    { name: "", url: "", qty: 1 },
  ]);

  const [coupon, setCoupon] = useState("");
  const [reorder, setReorder] = useState(1);
  const [start, setStart] = useState(1);
  const [end, setEnd] = useState(5);
  const [parallel, setParallel] = useState(3);
  const [loading, setLoading] = useState(false);

  /* ---------------- Products ---------------- */

  const addProduct = () => {
    if (products.length < 20) {
      setProducts([...products, { name: "", url: "", qty: 1 }]);
    }
  };

  const removeProduct = (index) => {
    if (products.length > 1) {
      setProducts(products.filter((_, i) => i !== index));
    }
  };

  const updateProduct = (index, field, value) => {
    const copy = [...products];
    copy[index][field] = value;
    setProducts(copy);
  };

  /* ---------------- Submit ---------------- */
const handleSubmit = async () => {
  // Generate profile list from range
  const profilesList = [];
  for (let i = Number(start); i <= Number(end); i++) {
    profilesList.push(`Profile ${i}`);
  }

  const payload = {
    mode: "parallel",
    products: products.filter(p => p.name && p.url),
    coupon_code: coupon,
    reorder_count: Number(reorder),
    profiles: profilesList,  // ✅ Array of strings
    parallel_browsers: Number(parallel),
    headless: false
  };

    if (payload.products.length === 0) {
      alert("❌ At least one product required");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(
        "http://localhost:8006/api/start-automation",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );

      const data = await res.json();

      if (data.status === "success") {
        alert("✅ " + data.message);
      } else {
        alert("❌ " + data.message);
      }
    } catch (err) {
      alert("❌ Backend not reachable");
    } finally {
      setLoading(false);
    }
  };

  /* ---------------- UI ---------------- */

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="bg-gray-900 text-white p-4 border-b-2 border-black">
        <button
          onClick={onBack}
          className="text-sm underline mb-2"
        >
          ← Back to Menu
        </button>
        <h1 className="text-2xl font-bold">🔥 PARALLEL MODE</h1>
        <p className="text-gray-300 text-sm">
          Run all profiles together
        </p>
      </div>

      <div className="max-w-4xl mx-auto p-6 space-y-6">

        {/* Products */}
        <div className="border-2 border-black rounded p-4">
          <h2 className="text-xl font-bold mb-4">
            Products ({products.length}/20)
          </h2>

          {products.map((p, i) => (
            <div
              key={i}
              className="border border-gray-400 rounded p-3 mb-3 bg-gray-50"
            >
              <div className="flex justify-between mb-2">
                <span className="font-bold">
                  Product {i + 1}
                </span>
                {products.length > 1 && (
                  <button
                    onClick={() => removeProduct(i)}
                    className="text-red-600 font-bold"
                  >
                    ✕
                  </button>
                )}
              </div>

              <input
                className="w-full border p-2 mb-2"
                placeholder="Product Name"
                value={p.name}
                onChange={(e) =>
                  updateProduct(i, "name", e.target.value)
                }
              />

              <input
                className="w-full border p-2 mb-2"
                placeholder="Product URL"
                value={p.url}
                onChange={(e) =>
                  updateProduct(i, "url", e.target.value)
                }
              />

              <input
                type="number"
                min="1"
                className="w-full border p-2"
                placeholder="Quantity"
                value={p.qty}
                onChange={(e) =>
                  updateProduct(i, "qty", e.target.value)
                }
              />
            </div>
          ))}

          <button
            onClick={addProduct}
            disabled={products.length >= 20}
            className="w-full border-2 border-black p-2 hover:bg-black hover:text-white disabled:opacity-40"
          >
            + Add Product
          </button>
        </div>

        {/* Settings */}
        <div className="grid grid-cols-2 gap-4">
          <div className="border-2 border-black rounded p-4">
            <label className="font-bold block mb-2">
              Coupon Code
            </label>
            <input
              className="w-full border p-2"
              placeholder="Optional"
              value={coupon}
              onChange={(e) =>
                setCoupon(e.target.value.toUpperCase())
              }
            />
          </div>

          <div className="border-2 border-black rounded p-4">
            <label className="font-bold block mb-2">
              Reorder Count (max 5)
            </label>
            <input
              type="number"
              min="1"
              max="5"
              className="w-full border p-2"
              value={reorder}
              onChange={(e) =>
                setReorder(Math.min(5, e.target.value))
              }
            />
          </div>
        </div>

        {/* Profiles */}
        <div className="grid grid-cols-3 gap-4">
          <div className="border-2 border-black rounded p-4">
            <label className="font-bold block mb-2">
              Start Profile
            </label>
            <input
              type="number"
              className="w-full border p-2"
              value={start}
              onChange={(e) => setStart(e.target.value)}
            />
          </div>

          <div className="border-2 border-black rounded p-4">
            <label className="font-bold block mb-2">
              End Profile
            </label>
            <input
              type="number"
              className="w-full border p-2"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
            />
          </div>

          <div className="border-2 border-black rounded p-4">
            <label className="font-bold block mb-2">
              Parallel Browsers
            </label>
            <input
              type="number"
              min="1"
              max="10"
              className="w-full border p-2"
              value={parallel}
              onChange={(e) => setParallel(e.target.value)}
            />
          </div>
        </div>

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full bg-black text-white p-4 text-xl font-bold rounded hover:bg-gray-800 disabled:opacity-50"
        >
          {loading ? "RUNNING..." : "START AUTOMATION"}
        </button>
      </div>
    </div>
  );
}
