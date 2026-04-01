import React, { useEffect, useState} from "react";

const emptyProfile = {
    major: "",
    year: "",
    personalization_notes: "",
};

export default function ProfileSettings({ userId }) {
    const [profile, setProfile] = useState(emptyProfile);
    const [isSaving, setIsSaving] = useState(false);
    const [status, setStatus] = useState("");

    useEffect(() => {
        const loadProfile = async () => {
            try {
                const response = await fetch(
                    `${process.env.REACT_APP_API_BASE}/profile?user_id=${encodeURIComponent(userId)}`
                );
                const data = await response.json();

                if (data.ok && data.profile) {
                    setProfile({
                        major: data.profile.major || "",
                        year: data.profile.year || "",
                        personalization_notes: data.profile.personalization_notes || "",
                    });
                }
            } catch (err) {
                console.error("Failed to load profile:", err);
                setStatus("Could not load profile.");
            }
        };

        if (userId) {
            loadProfile();
        }
    }, [userId]);

    const updateField = (field, value) => {
        setProfile((prev) => ({
            ...prev,
            [field]: value,
        }));
    };

    const handleSave = async () => {
        setIsSaving(true);
        setStatus("");

        try {
            const response = await fetch(`${process.env.REACT_APP_API_BASE}/profile`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_id: userId,
                    ...profile,
                }),
            });

            const data = await response.json();
            if (data.ok) {
                setStatus("Profile saved.");
            } else {
                setStatus("Failed to save profile.");
            }
        } catch (err) {
            console.error("Failed to save profile.", err);
            setStatus("Failed to save profile.");
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="min-h-screen bg-dark-gray text-white p-8">
            <div className="max-w-3xl mx-auto bg-gray-900 rounded-xl p-6 border border-gray-700">
                <h1 className="text-2xl font-bold mb-2">ProfileSettings</h1>
                <p className="text-gray-400 mb-6">
                    These settings help personalized GopherGPT responses.
                </p>

                <div className="grid gap-4">
                    <div>
                        <label className="block mb-1 text-sm text-gray-300">Major</label>
                        <input 
                            value={profile.major} 
                            onChange={(e) => updateField("major", e.target.value)} 
                            className="w-full p-3 rounded bg-gray-800 border border-gray-700"
                        />
                    </div>

                    <div>
                        <label className="block mb-1 text-sm text-gray-300">Year</label>
                        <input 
                            value={profile.year}
                            onChange={(e) => updateField("year", e.target.value)}
                            placeholder="Freshman, Sophomore, Junior, Senior..."
                            className="w-full p-3 rounded bg-gray-800 border border-gray-700"
                        />
                    </div>

                    <div>
                        <label className="block mb-1 text-sm text-gray-300">
                            Personalization Notes
                        </label>
                        <textarea 
                            value={profile.personalization_notes}
                            onChange={(e) => updateField("personalization_notes", e.target.value)}
                            rows={5}
                            className="w-full p-3 rounded bg-gray-800 border border-gray-700"
                            placeholder="Example: explain things simply, prioritize course-related answers, keep responses concise..."
                        />
                    </div>
                </div>

                <div className="mt-6 flex items-center gap-4">
                    <button 
                        onClick={handleSave}
                        disabled={isSaving}
                        className="px-5 py-2 rounded bg-gold text-maroon font-semigold disabled:opacity-50"
                    >
                        {isSaving ? "Saving..." : "Save Profile"}
                    </button>

                    {status && <span className="text-sm text-gray-300">{status}</span>}
                </div>

            </div>
        </div>
    );
}
