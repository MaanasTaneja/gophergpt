import React, { useEffect, useState } from "react";

const YEAR_OPTIONS = ["Freshman", "Sophomore", "Junior", "Senior", "Graduate", "PhD", "Other"];

const emptyProfile = { major: "", year: "", personalization_notes: "" };

export default function ProfileSettings({ userId, onClose }) {
  const [profile, setProfile] = useState(emptyProfile);
  const [isSaving, setIsSaving] = useState(false);
  const [status, setStatus] = useState("");

  useEffect(() => {
    if (!userId) return;
    fetch(`${process.env.REACT_APP_API_BASE}/profile?user_id=${encodeURIComponent(userId)}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.ok && data.profile) {
          setProfile({
            major: data.profile.major || "",
            year: data.profile.year || "",
            personalization_notes: data.profile.personalization_notes || "",
          });
        }
      })
      .catch(() => setStatus("Could not load profile."));
  }, [userId]);

  const update = (field, value) => setProfile((p) => ({ ...p, [field]: value }));

  const handleSave = async () => {
    if (!userId) { setStatus("No user ID found."); return; }
    setIsSaving(true);
    setStatus("");
    try {
      const res = await fetch(`${process.env.REACT_APP_API_BASE}/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, ...profile }),
      });
      const data = await res.json();
      setStatus(data.ok ? "Saved." : "Failed to save.");
    } catch {
      setStatus("Failed to save.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen relative overflow-y-auto">
      {/* Faded background logo */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <img
          src="/minnesota-m-logo.png"
          alt=""
          className="w-[500px] h-[500px] object-contain opacity-10"
        />
      </div>

      <div className="relative z-10 max-w-2xl mx-auto w-full px-6 pt-10 pb-10">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white mb-1">Profile</h1>
            <p className="text-gray-400 text-sm">
              GopherGPT uses this to personalize responses to you.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-white text-2xl leading-none mt-1 px-1"
            aria-label="Close"
          >
            &times;
          </button>
        </div>

        <div className="space-y-5">
          {/* Major */}
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Major</label>
            <input
              value={profile.major}
              onChange={(e) => update("major", e.target.value)}
              placeholder="e.g. Computer Science"
              className="w-full px-4 py-3 rounded-xl bg-[#1a1a1a] border border-gray-700 text-white placeholder-gray-600 focus:outline-none focus:border-gold/60 transition"
            />
          </div>

          {/* Year */}
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Year</label>
            <div className="flex flex-wrap gap-2">
              {YEAR_OPTIONS.map((y) => (
                <button
                  key={y}
                  onClick={() => update("year", profile.year === y ? "" : y)}
                  className={`px-4 py-2 rounded-full text-sm border transition ${
                    profile.year === y
                      ? "bg-gold text-[#1a0810] border-gold font-semibold"
                      : "border-gray-700 text-gray-400 hover:border-gold/50 hover:text-white"
                  }`}
                >
                  {y}
                </button>
              ))}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">
              Personalization Notes
            </label>
            <textarea
              value={profile.personalization_notes}
              onChange={(e) => update("personalization_notes", e.target.value)}
              rows={5}
              placeholder="e.g. I'm pre-med, keep course suggestions relevant to med school prep. Explain things simply."
              className="w-full px-4 py-3 rounded-xl bg-[#1a1a1a] border border-gray-700 text-white placeholder-gray-600 focus:outline-none focus:border-gold/60 transition resize-none"
            />
          </div>
        </div>

        {/* Save */}
        <div className="mt-6 flex items-center gap-4">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-6 py-2.5 rounded-xl bg-gold text-[#1a0810] font-semibold text-sm disabled:opacity-50 hover:brightness-110 transition"
          >
            {isSaving ? "Saving..." : "Save Profile"}
          </button>
          {status && (
            <span className={`text-sm ${status === "Saved." ? "text-green-400" : "text-red-400"}`}>
              {status}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
