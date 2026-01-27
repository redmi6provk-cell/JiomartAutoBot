import React, { useState } from 'react';
import { Zap, Users, Target, Sliders, Trash2 } from 'lucide-react';

// Import components
import Parallel from './components/Parallel';
import Sequential from './components/Sequential';
import SingleTest from './components/SingleTest';
import Custom from './components/Custom';
import ProductRemoval from './components/ProductRemoval';

export default function App() {
  const [activeMode, setActiveMode] = useState(null);

  const modes = [
    { id: 'parallel', label: 'PARALLEL', desc: 'All profiles together', icon: Zap },
    { id: 'sequential', label: 'SEQUENTIAL', desc: 'One by one', icon: Users },
    { id: 'single', label: 'SINGLE TEST', desc: 'Test with one profile', icon: Target },
    { id: 'custom', label: 'CUSTOM', desc: 'Select specific profiles', icon: Sliders },
  ];

  const renderComponent = () => {
    switch(activeMode) {
      case 'parallel': return <Parallel onBack={() => setActiveMode(null)} />;
      case 'sequential': return <Sequential onBack={() => setActiveMode(null)} />;
      case 'single': return <SingleTest onBack={() => setActiveMode(null)} />;
      case 'custom': return <Custom onBack={() => setActiveMode(null)} />;
      case 'removal': return <ProductRemoval onBack={() => setActiveMode(null)} />;
      default: return null;
    }
  };

  if (activeMode) {
    return renderComponent();
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="border-b-2 border-gray-900 bg-gray-900 text-white">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <h1 className="text-3xl font-bold">JioMart Automation</h1>
          <p className="text-gray-300 mt-1">Select Your Mode</p>
        </div>
      </div>

      {/* Menu */}
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="border-4 border-gray-900 rounded-lg p-8 bg-white">
          <h2 className="text-2xl font-bold mb-6 border-b-2 border-gray-900 pb-3">📋 MENU</h2>
          
          {/* Main Modes */}
          <div className="space-y-4 mb-8">
            {modes.map((mode, index) => (
              <button
                key={mode.id}
                onClick={() => setActiveMode(mode.id)}
                className="w-full p-4 border-2 border-gray-900 rounded hover:bg-gray-900 hover:text-white transition-all text-left group"
              >
                <div className="flex items-center gap-4">
                  <span className="text-2xl font-bold text-gray-400 group-hover:text-white">
                    {index + 1}.
                  </span>
                  <mode.icon className="w-6 h-6" />
                  <div>
                    <div className="font-bold text-lg">{mode.label}</div>
                    <div className="text-sm text-gray-600 group-hover:text-gray-300">{mode.desc}</div>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* Extra Feature */}
          <div className="border-t-2 border-gray-900 pt-6">
            <button
              onClick={() => setActiveMode('removal')}
              className="w-full p-4 border-2 border-red-600 bg-red-50 rounded hover:bg-red-600 hover:text-white transition-all"
            >
              <div className="flex items-center gap-4">
                <Trash2 className="w-6 h-6" />
                <div className="text-left">
                  <div className="font-bold text-lg">Remove Products</div>
                  <div className="text-sm">Clean cart for selected profiles</div>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}