// portal_front/src/app/portal/tutor/page.tsx
"use client";

import { AppFrame } from "@/components/AppFrame";
import { PORTAL_APPS } from "@/config/portalApps";

export default function TutorPortalPage() {
  const app = PORTAL_APPS.find((a) => a.id === "tutor");
  if (!app) {
    return (
      <div className="py-10 text-sm text-red-600">
        Tutor 앱 구성이 되어 있지 않습니다.
      </div>
    );
  }

  return <AppFrame src={app.iframeSrc} />;
}
