import React from 'react';

const GITHUB_BASE = 'https://github.com/dreamseedai/dreamseed_monorepo/blob/staging/attempt-view-lock-v1/shared/irt/docs';

export default function IrtDocsPage() {
  const links = [
    { file: 'README.md', title: 'Docs Index / 문서 인덱스' },
    { file: '01_IMPLEMENTATION_REPORT.md', title: '01 Implementation Report' },
    { file: '02_CALIBRATION_METHODS_COMPARISON.md', title: '02 Calibration Methods Comparison' },
    { file: '03_DRIFT_DETECTION_GUIDE.md', title: '03 Drift Detection Guide' },
    { file: '04_API_INTEGRATION_GUIDE.md', title: '04 API Integration Guide' },
    { file: '05_FRONTEND_INTEGRATION_GUIDE.md', title: '05 Frontend Integration Guide' },
    { file: '06_DEPLOYMENT_GUIDE.md', title: '06 Deployment Guide' },
    { file: '07_TROUBLESHOOTING_GUIDE.md', title: '07 Troubleshooting Guide' },
    { file: 'THRESHOLDS_AND_DIF.md', title: 'Thresholds and DIF' },
  ];

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-4">IRT Documentation</h1>
      <p className="text-gray-600 mb-6">
        Links open the GitHub view of the documents (staging branch).
      </p>

      <div className="grid md:grid-cols-2 gap-4">
        {links.map((l) => (
          <a
            key={l.file}
            href={`${GITHUB_BASE}/${l.file}`}
            target="_blank"
            rel="noreferrer"
            className="block border rounded p-4 hover:bg-gray-50"
          >
            <div className="font-semibold">{l.title}</div>
            <div className="text-sm text-blue-600 break-all">{`${GITHUB_BASE}/${l.file}`}</div>
          </a>
        ))}
      </div>
    </div>
  );
}
