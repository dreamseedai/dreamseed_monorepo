import React, { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

const BILLING_ENABLED = String(import.meta.env.VITE_BILLING_ENABLED || "false") === "true";

const PLANS = {
  free:  { name: "Free",    price: 0 },
  pro:   { name: "Pro",     price: 25 },
  premium_student: { name: "Premium (Student)", price: 99 },
  premium_family:  { name: "Premium (Family/School)", price: 199 },
} as const;

export default function CheckoutDummy() {
  const [sp] = useSearchParams();
  const navigate = useNavigate();
  const initial = (sp.get("plan") || "pro") as keyof typeof PLANS;
  const [plan, setPlan] = useState<keyof typeof PLANS>(initial);

  const total = useMemo(() => PLANS[plan].price, [plan]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-2xl font-bold">Checkout (Preview)</h1>
      <p className="mt-2 text-gray-600">
        This is a dummy page for testing before payment integration. No actual payment will be processed.
      </p>

      <div className="mt-6 rounded-2xl border p-4">
        <label className="block text-sm text-gray-600 mb-1">Select Plan</label>
        <select
          className="rounded-xl border-gray-300 focus:ring-2 focus:ring-gray-900"
          value={plan}
          onChange={e => setPlan(e.target.value as keyof typeof PLANS)}
        >
          <option value="pro">Pro — $25 /mo</option>
          <option value="premium_student">Premium (Student) — $99 /mo</option>
          <option value="premium_family">Premium (Family/School) — $199 /mo</option>
          <option value="free">Free — $0</option>
        </select>
      </div>

      <div className="mt-6 rounded-2xl border p-4">
        <h2 className="text-lg font-semibold">Order Summary</h2>
        <ul className="mt-2 text-sm text-gray-700 list-disc list-inside">
          <li>Plan: {PLANS[plan].name}</li>
          <li>Monthly fee: ${total}</li>
          <li>Tax/Discount: Not applied (Demo)</li>
        </ul>
        <div className="mt-4">
          <button
            className={`rounded-2xl px-4 py-2 text-sm font-semibold ${
              BILLING_ENABLED ? "bg-gray-900 text-white" : "bg-gray-200 text-gray-700 cursor-not-allowed"
            }`}
            disabled={!BILLING_ENABLED}
            onClick={() => alert("Demo: Payment module not connected yet.")}
          >
            {BILLING_ENABLED ? "Proceed to Payment (Demo)" : "Payment Preparation (Disabled)"}
          </button>
          <button
            className="ml-2 rounded-2xl px-4 py-2 text-sm font-semibold bg-white ring-1 ring-gray-300 hover:bg-gray-50"
            onClick={() => navigate("/")}
          >
            Go Back
          </button>
        </div>
        {!BILLING_ENABLED && (
          <p className="mt-2 text-xs text-gray-500">Enable by setting VITE_BILLING_ENABLED=true in .env</p>
        )}
      </div>
    </div>
  );
}


