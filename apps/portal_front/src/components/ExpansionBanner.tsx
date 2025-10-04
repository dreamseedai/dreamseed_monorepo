import React, { useState } from 'react';

export default function ExpansionBanner() {
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [email, setEmail] = useState('');

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      // TODO: 실제 뉴스레터 구독 API 호출
      setIsSubscribed(true);
      setTimeout(() => setIsSubscribed(false), 3000);
    }
  };

  return (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-xl p-6 mb-8">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="text-lg font-semibold text-purple-900 mb-2">
            <span className="text-purple-600">🚀</span> More Subjects Coming Soon!
          </h4>
          <p className="text-purple-800 mb-4">
            We're working hard to add English, Social Studies, Languages, and Arts. 
            Be the first to know when new subjects are available!
          </p>
          
          {!isSubscribed ? (
            <form onSubmit={handleSubscribe} className="flex gap-2 max-w-md">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="flex-1 border border-purple-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                required
              />
              <button
                type="submit"
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Notify Me
              </button>
            </form>
          ) : (
            <div className="text-green-600 font-medium">
              ✅ Thank you! We'll notify you when new subjects are available.
            </div>
          )}
        </div>
        
        <div className="ml-6 text-right">
          <div className="text-sm text-purple-600 font-medium mb-2">Coming Soon:</div>
          <div className="space-y-1 text-sm text-purple-700">
            <div>📖 English Language Arts</div>
            <div>🌍 Social Studies</div>
            <div>🈴 Foreign Languages</div>
            <div>🎨 Visual & Performing Arts</div>
          </div>
        </div>
      </div>
    </div>
  );
}
