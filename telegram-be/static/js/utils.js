// static/js/utils.js
export function formatTime(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;

  if (diff < 60000) return "Just now";
  if (diff < 3600000) return Math.floor(diff / 60000) + "m ago";
  if (diff < 86400000) return Math.floor(diff / 3600000) + "h ago";
  return date.toLocaleDateString();
}

export function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

export function showToast(type, title, message) {
  // Simple Tailwind Toast implementation
  const toast = document.createElement("div");
  // Colors based on type
  const colors =
    type === "success"
      ? "border-l-4 border-green-500"
      : type === "error"
      ? "border-l-4 border-red-500"
      : "border-l-4 border-blue-500";

  toast.className = `fixed top-5 right-5 bg-white shadow-lg rounded-lg p-4 flex items-start gap-3 z-50 animate-slideIn ${colors}`;

  toast.innerHTML = `
        <div>
            <h4 class="font-bold text-gray-800 text-sm">${title}</h4>
            <p class="text-gray-600 text-xs mt-1">${message}</p>
        </div>
        <button class="text-gray-400 hover:text-gray-600" onclick="this.parentElement.remove()">×</button>
    `;

  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
