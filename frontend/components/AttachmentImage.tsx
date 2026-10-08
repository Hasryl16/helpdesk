"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";

/**
 * <img src> cannot send our Authorization header, so we download the image
 * with apiRequest and show it from a temporary blob: URL.
 */
export default function AttachmentImage({ ticketId, messageId }: { ticketId: number; messageId: number }) {
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let url = "";
    let cancelled = false;
    apiRequest(`/tickets/${ticketId}/attachments/${messageId}`)
      .then((res) => res.blob())
      .then((blob) => {
        if (cancelled) return;
        url = URL.createObjectURL(blob);
        setSrc(url);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [ticketId, messageId]);

  if (failed) return <p className="text-xs text-red-600">Image could not be loaded.</p>;
  if (!src) return <p className="text-xs text-gray-500">Loading image...</p>;
  // next/image is for optimizing remote files; a local blob: URL needs nothing from it.
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={src} alt="Attachment" className="mt-1 max-h-64 rounded" />;
}
