import React from "react";
import PlansCompareTable from "../components/PlansCompareTable";

export default function PlansCompare() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="text-2xl font-bold">Plan Comparison</h1>
      <p className="mt-2 text-gray-600">Compare the differences between Free / Pro / Premium plans at a glance.</p>
      <div className="mt-6">
        <PlansCompareTable />
      </div>
    </div>
  );
}


