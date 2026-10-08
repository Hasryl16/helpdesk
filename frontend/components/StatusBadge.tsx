import type { Status } from "@/lib/types";

const COLORS: Record<Status, string> = {
  open: "bg-blue-100 text-blue-800",
  in_progress: "bg-yellow-100 text-yellow-800",
  resolved: "bg-green-100 text-green-800",
  closed: "bg-gray-200 text-gray-700",
};

export default function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${COLORS[status]}`}>{status.replace("_", " ")}</span>
  );
}
