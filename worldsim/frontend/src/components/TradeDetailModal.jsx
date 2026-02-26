import React, { useEffect } from 'react';

// ─── Constants ────────────────────────────────────────────────────────────

const REGION_COLORS = {
  aquaria:   "#3b82f6",  // blue
  agrovia:   "#22c55e",  // green
  petrozon:  "#f97316",  // orange
  urbanex:   "#ef4444",  // red
  terranova: "#a855f7"   // purple
};

const SHORT_LABELS = {
  aquaria:   "Brazil",
  agrovia:   "India",
  petrozon:  "Gulf States",
  urbanex:   "China",
  terranova: "Africa"
};

const RESOURCE_ICONS = {
  water:  "💧",
  food:   "🌾",
  energy: "⚡",
  land:   "🏔️"
};

// ─── AnimationStyles - injected at runtime ────────────────────────────────

const animationStyles = `
@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: scale(0.92) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.trade-modal-box {
  animation: modalFadeIn 0.2s ease-out;
  scrollbar-width: thin;
  scrollbar-color: rgba(99, 102, 241, 0.3) transparent;
}

.trade-modal-box::-webkit-scrollbar {
  width: 6px;
}

.trade-modal-box::-webkit-scrollbar-track {
  background: transparent;
}

.trade-modal-box::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.3);
  border-radius: 3px;
}

.trade-modal-box::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.5);
}
`;

// Inject styles on component load
if (typeof document !== 'undefined') {
  const styleEl = document.createElement('style');
  styleEl.textContent = animationStyles;
  document.head.appendChild(styleEl);
}

// ─── Helper Functions ─────────────────────────────────────────────────────

function getRegionColor(regionId) {
  return REGION_COLORS[regionId?.toLowerCase()] || "#94a3b8";
}

function getShortLabel(regionId) {
  return SHORT_LABELS[regionId?.toLowerCase()] || regionId;
}

function getResourceChangeDisplay(before, after) {
  const change = after - before;
  if (change === 0) return null;
  
  const changeText = change > 0 ? `+${change.toFixed(2)}` : `${change.toFixed(2)}`;
  const changeColor = change > 0 ? '#22c55e' : '#ef4444';
  
  return { changeText, changeColor, change };
}

function ResourceChangeRow({ resource, before, after }) {
  const display = getResourceChangeDisplay(before, after);
  if (!display) return null;
  
  const { changeText, changeColor } = display;
  
  return (
    <div className="text-xs text-slate-300 py-1.5 flex justify-between items-center">
      <span>
        <span className="mr-1.5">{RESOURCE_ICONS[resource] || "•"}</span>
        {resource.charAt(0).toUpperCase() + resource.slice(1)}
      </span>
      <span className="font-mono text-slate-500">
        {before.toFixed(1)} → {after.toFixed(1)}
      </span>
      <span className="font-mono font-semibold ml-2" style={{ color: changeColor }}>
        {changeText}
      </span>
    </div>
  );
}

function getRejectionReason(outcome, trade) {
  const reasons = {
    "trade_rejected_low_trust": (
      <>
        <p className="text-sm text-slate-300 mb-1">Trust too low between these regions.</p>
        <p className="text-xs text-slate-400">
          Minimum trust of 20 required. Current trust: {trade.trust_before?.sender_toward_receiver || "N/A"}%
        </p>
      </>
    ),
    "trade_rejected_no_surplus": (
      <p className="text-sm text-slate-300">
        Receiver has no surplus to offer. Required resource quantity unavailable.
      </p>
    ),
    "trade_skipped_no_surplus": (
      <p className="text-sm text-slate-300">
        Sender has nothing to trade. All resources below surplus threshold.
      </p>
    ),
    "trade_skipped_no_deficit": (
      <p className="text-sm text-slate-300">
        Sender has no resource deficit. No trade was necessary this cycle.
      </p>
    ),
    "trade_skipped_no_capacity": (
      <p className="text-sm text-slate-300">
        Urbanex manufacturing capacity depleted. Recovering +1 per cycle.
      </p>
    ),
  };
  return reasons[outcome] || <p className="text-sm text-slate-300">Trade could not proceed.</p>;
}

// ─── Component ────────────────────────────────────────────────────────────

export default function TradeDetailModal({ trade, onClose }) {
  // Keyboard support - close on Escape
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "unset";
    };
  }, []);

  if (!trade) return null;

  const isSuccess = trade.outcome === "trade_success";
  const senderLabel = trade.source_region ? trade.source_region.charAt(0).toUpperCase() + trade.source_region.slice(1) : "Unknown";
  const receiverLabel = trade.target_region ? trade.target_region.charAt(0).toUpperCase() + trade.target_region.slice(1) : "Unknown";
  const senderShort = getShortLabel(trade.source_region);
  const receiverShort = getShortLabel(trade.target_region);
  const senderColor = getRegionColor(trade.source_region);
  const receiverColor = getRegionColor(trade.target_region);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm"
      style={{
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
      }}
      onClick={onClose}
    >
      {/* Modal Box */}
      <div
        className="trade-modal-box relative w-full mx-4 p-7 rounded-2xl overflow-y-auto"
        style={{
          width: "480px",
          maxHeight: "85vh",
          backgroundColor: "#0f172a",
          border: "1px solid rgba(99, 102, 241, 0.3)",
          boxShadow: "0 25px 50px rgba(0, 0, 0, 0.8), 0 0 30px rgba(99, 102, 241, 0.15)"
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Row */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-xs font-semibold tracking-widest text-indigo-400 mb-1" style={{ textTransform: "uppercase" }}>
              Trade Event
            </p>
            <h2 className="text-xl font-bold text-white">Cycle {trade.cycle ?? "?"}</h2>
          </div>
          <button
            onClick={onClose}
            className="flex items-center justify-center w-8 h-8 rounded-full transition-colors"
            style={{
              backgroundColor: "rgba(255, 255, 255, 0.1)",
              color: "#e2e8f0"
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.2)"}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.1)"}
          >
            ✕
          </button>
        </div>

        {/* Outcome Badge */}
        <div
          className="w-full py-2.5 px-3.5 rounded-lg text-center font-semibold text-sm mb-5 border"
          style={
            isSuccess
              ? {
                  backgroundColor: "rgba(34, 197, 94, 0.15)",
                  borderColor: "rgba(34, 197, 94, 0.4)",
                  color: "#22c55e"
                }
              : {
                  backgroundColor: "rgba(239, 68, 68, 0.15)",
                  borderColor: "rgba(239, 68, 68, 0.4)",
                  color: "#ef4444"
                }
          }
        >
          {isSuccess ? "✓ Trade Successful" : "✗ Trade Rejected"}
        </div>

        {/* Participants Row */}
        <div className="flex items-center justify-between gap-3 mb-5 px-2">
          {/* Sender Box */}
          <div
            className="flex-1 text-center p-3 rounded-lg"
            style={{ backgroundColor: "rgba(255, 255, 255, 0.05)" }}
          >
            <div
              className="w-2 h-2 rounded-full mx-auto mb-2"
              style={{ backgroundColor: senderColor }}
            />
            <p className="text-sm font-bold text-white">{senderLabel}</p>
            <p className="text-xs text-slate-400 mt-0.5">{senderShort}</p>
          </div>

          {/* Arrow */}
          <div className="text-slate-500 font-bold">→</div>

          {/* Receiver Box */}
          <div
            className="flex-1 text-center p-3 rounded-lg"
            style={{ backgroundColor: "rgba(255, 255, 255, 0.05)" }}
          >
            <div
              className="w-2 h-2 rounded-full mx-auto mb-2"
              style={{ backgroundColor: receiverColor }}
            />
            <p className="text-sm font-bold text-white">{receiverLabel}</p>
            <p className="text-xs text-slate-400 mt-0.5">{receiverShort}</p>
          </div>
        </div>

        {/* Divider */}
        <div
          className="my-4"
          style={{ height: "1px", backgroundColor: "rgba(255, 255, 255, 0.08)" }}
        />

        {/* What Was Traded Section */}
        {isSuccess && (
          <div className="mb-5">
            <p className="text-xs text-slate-500 font-semibold mb-3 uppercase tracking-wider">
              What Was Traded
            </p>
            <div className="space-y-2 text-sm">
              {trade.is_manufacturing_trade ? (
                <>
                  <div className="flex items-center justify-between text-slate-300">
                    <span>🏭 Manufacturing Capacity</span>
                    <span className="font-mono text-red-400 font-semibold">-3</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span>
                      {RESOURCE_ICONS[trade.resource_traded] || "•"} {trade.resource_traded ? trade.resource_traded.charAt(0).toUpperCase() + trade.resource_traded.slice(1) : "Resource"}
                    </span>
                    <span className="font-mono text-green-400 font-semibold">+{trade.transfer_amount?.toFixed(1)}</span>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-center justify-between text-slate-300">
                    <span>
                      {RESOURCE_ICONS[trade.resource_offered] || "•"} {trade.resource_offered ? trade.resource_offered.charAt(0).toUpperCase() + trade.resource_offered.slice(1) : "Resource"} Sent
                    </span>
                    <span className="font-mono text-red-400 font-semibold">-{trade.transfer_amount?.toFixed(1)}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span>
                      {RESOURCE_ICONS[trade.resource_traded] || "•"} {trade.resource_traded ? trade.resource_traded.charAt(0).toUpperCase() + trade.resource_traded.slice(1) : "Resource"} Received
                    </span>
                    <span className="font-mono text-green-400 font-semibold">+{trade.transfer_amount?.toFixed(1)}</span>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Resource Changes Table */}
        {isSuccess && (
          <div className="mb-5">
            <p className="text-xs text-slate-500 font-semibold mb-3 uppercase tracking-wider">
              Resource Changes
            </p>
            <div className="grid grid-cols-2 gap-4">
              {/* Sender Changes */}
              <div className="text-xs">
                <p className="text-slate-400 font-semibold mb-2">{senderLabel}</p>
                <div className="space-y-1">
                  <ResourceChangeRow
                    resource="water"
                    before={trade.sender_before?.water || 0}
                    after={trade.sender_after?.water || 0}
                  />
                  <ResourceChangeRow
                    resource="food"
                    before={trade.sender_before?.food || 0}
                    after={trade.sender_after?.food || 0}
                  />
                  <ResourceChangeRow
                    resource="energy"
                    before={trade.sender_before?.energy || 0}
                    after={trade.sender_after?.energy || 0}
                  />
                  <ResourceChangeRow
                    resource="land"
                    before={trade.sender_before?.land || 0}
                    after={trade.sender_after?.land || 0}
                  />
                </div>
              </div>

              {/* Receiver Changes */}
              <div className="text-xs">
                <p className="text-slate-400 font-semibold mb-2">{receiverLabel}</p>
                <div className="space-y-1">
                  <ResourceChangeRow
                    resource="water"
                    before={trade.receiver_before?.water || 0}
                    after={trade.receiver_after?.water || 0}
                  />
                  <ResourceChangeRow
                    resource="food"
                    before={trade.receiver_before?.food || 0}
                    after={trade.receiver_after?.food || 0}
                  />
                  <ResourceChangeRow
                    resource="energy"
                    before={trade.receiver_before?.energy || 0}
                    after={trade.receiver_after?.energy || 0}
                  />
                  <ResourceChangeRow
                    resource="land"
                    before={trade.receiver_before?.land || 0}
                    after={trade.receiver_after?.land || 0}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Trust Impact Section */}
        <div className="mb-5">
          <p className="text-xs text-slate-500 font-semibold mb-3 uppercase tracking-wider">
            Trust Impact
          </p>
          <div className="space-y-3 text-sm">
            {/* Sender to Receiver */}
            <div>
              <p className="text-slate-300 font-mono mb-1.5">
                {senderLabel} → {receiverLabel}
              </p>
              <div className="flex items-center justify-between text-xs ml-2">
                <span className="text-slate-400">
                  {trade.trust_before?.sender_toward_receiver || "N/A"}% →{" "}
                  <span className="text-slate-300 font-semibold">
                    {trade.trust_after?.sender_toward_receiver || "N/A"}%
                  </span>
                </span>
                {isSuccess && (
                  <span
                    className="px-2 py-1 rounded font-semibold"
                    style={{ backgroundColor: "rgba(34, 197, 94, 0.2)", color: "#22c55e" }}
                  >
                    +{((trade.trust_after?.sender_toward_receiver || 50) - (trade.trust_before?.sender_toward_receiver || 50)).toFixed(0)}
                  </span>
                )}
              </div>
              {isSuccess && (
                <p className="text-xs text-green-400 mt-1.5 ml-2">✓ Alliance strengthening</p>
              )}
            </div>

            {/* Receiver to Sender (Success Only) */}
            {isSuccess && (
              <div>
                <p className="text-slate-300 font-mono mb-1.5">
                  {receiverLabel} → {senderLabel}
                </p>
                <div className="flex items-center justify-between text-xs ml-2">
                  <span className="text-slate-400">
                    {trade.trust_before?.receiver_toward_sender || "N/A"}% →{" "}
                    <span className="text-slate-300 font-semibold">
                      {trade.trust_after?.receiver_toward_sender || "N/A"}%
                    </span>
                  </span>
                  <span
                    className="px-2 py-1 rounded font-semibold"
                    style={{ backgroundColor: "rgba(34, 197, 94, 0.2)", color: "#22c55e" }}
                  >
                    +{((trade.trust_after?.receiver_toward_sender || 50) - (trade.trust_before?.receiver_toward_sender || 50)).toFixed(0)}
                  </span>
                </div>
              </div>
            )}

            {!isSuccess && (
              <div className="pt-2" style={{ borderTop: "1px solid rgba(239, 68, 68, 0.2)" }}>
                <p className="text-xs text-red-400">✗ Trust damaged</p>
              </div>
            )}
          </div>
        </div>

        {/* Rejection Reason Section */}
        {!isSuccess && (
          <div
            className="p-3 rounded-lg mb-5 border"
            style={{
              backgroundColor: "rgba(239, 68, 68, 0.08)",
              borderColor: "rgba(239, 68, 68, 0.2)"
            }}
          >
            <p className="text-xs font-bold text-red-400 mb-2 uppercase tracking-wider">
              ⚠️ Why Rejected
            </p>
            <div className="text-xs text-slate-300">
              {getRejectionReason(trade.outcome, trade)}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-xs text-slate-500 pt-4" style={{ borderTop: "1px solid rgba(255, 255, 255, 0.08)" }}>
          <p>WorldSim · 1 cycle ≈ 1 year · Click outside to close</p>
        </div>
      </div>
    </div>
  );
}
