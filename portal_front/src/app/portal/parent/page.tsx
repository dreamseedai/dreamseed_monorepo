// portal_front/src/app/portal/parent/page.tsx
"use client";

import { AppFrame } from "@/components/AppFrame";
import { PORTAL_APPS } from "@/config/portalApps";

export default function ParentPortalPage() {
  const app = PORTAL_APPS.find((a) => a.id === "parent");
  if (!app) {
    return (
      <div className="py-10 text-sm text-red-600">
        Parent 앱 구성이 되어 있지 않습니다.
      </div>
    );
  }

  return <AppFrame src={app.iframeSrc} />;
}
