import React from "react";

export default function PlansCompareTable() {
  const rows = [
    { feature: "Content Access", free: "Static content", pro: "Some personalized content", premium: "Personalized + unlimited generation" },
    { feature: "AI Usage", free: "Very limited", pro: "Monthly token limit", premium: "Unlimited" },
    { feature: "Personalization", free: "None", pro: "Profile/Diagnostics", premium: "Progress tracking & prediction" },
    { feature: "Dashboard", free: "None", pro: "Progress/Weaknesses", premium: "Advanced analytics/Weekly plans" },
    { feature: "Support", free: "Community/FAQ", pro: "Basic support", premium: "Priority support (+Family/School)" },
    { feature: "Monthly Fee", free: "$0", pro: "$25", premium: "$99 (Student) / $199 (Family/School)" },
  ];

  return (
    <div className="overflow-x-auto rounded-2xl border">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-semibold">Features</th>
            <th className="px-4 py-3 text-left font-semibold">Free</th>
            <th className="px-4 py-3 text-left font-semibold">Pro</th>
            <th className="px-4 py-3 text-left font-semibold">Premium</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.feature} className="border-t">
              <td className="px-4 py-3 font-medium">{r.feature}</td>
              <td className="px-4 py-3">{r.free}</td>
              <td className="px-4 py-3">{r.pro}</td>
              <td className="px-4 py-3">{r.premium}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


