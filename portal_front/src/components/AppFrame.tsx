// portal_front/src/components/AppFrame.tsx
"use client";

import { useEffect, useRef } from "react";

type AppFrameProps = {
  src: string;
};

export function AppFrame({ src }: AppFrameProps) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);

  // 최초 로딩 시 토큰 전송
  useEffect(() => {
    const token =
      typeof window !== "undefined"
        ? window.localStorage.getItem("access_token")
        : null;

    if (!token) return;

    const sendToken = () => {
      if (iframeRef.current?.contentWindow) {
        iframeRef.current.contentWindow.postMessage(
          {
            type: "SET_TOKEN",
            token,
          },
          "*" // dev: *, prod: 정확한 origin
        );
      }
    };

    // iframe이 로드된 후 토큰 전달
    const iframe = iframeRef.current;
    if (iframe) {
      iframe.addEventListener("load", sendToken);
      // 이미 로드된 경우를 위해 즉시 한 번 실행
      if (iframe.contentWindow) {
        sendToken();
      }
    }

    return () => {
      if (iframe) {
        iframe.removeEventListener("load", sendToken);
      }
    };
  }, [src]);

  // localStorage access_token 변경시마다 재전송 (로그인/로그아웃)
  useEffect(() => {
    function handleStorage(e: StorageEvent) {
      if (e.key !== "access_token") return;
      if (!iframeRef.current?.contentWindow) return;

      iframeRef.current.contentWindow.postMessage(
        {
          type: "SET_TOKEN",
          token: e.newValue,
        },
        "*"
      );
    }

    if (typeof window !== "undefined") {
      window.addEventListener("storage", handleStorage);
    }
    return () => {
      if (typeof window !== "undefined") {
        window.removeEventListener("storage", handleStorage);
      }
    };
  }, []);

  return (
    <iframe
      ref={iframeRef}
      src={src}
      className="h-[calc(100vh-64px)] w-full border-0"
      title="Portal App Frame"
    />
  );
}
