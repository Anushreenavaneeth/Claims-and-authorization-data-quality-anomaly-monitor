import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Key, CheckCircle, Loader2, AlertCircle, ShieldCheck } from "lucide-react";
import { verifyInviteToken, setPasswordWithToken } from "../services/api";

export function SetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const navigate = useNavigate();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Token verification state
  const [verifying, setVerifying] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [workerName, setWorkerName] = useState("");
  const [workerEmail, setWorkerEmail] = useState("");
  const [tokenError, setTokenError] = useState("");

  useEffect(() => {
    if (!token) {
      setVerifying(false);
      setTokenError("No invitation token provided. Please use the link from your invitation email.");
      return;
    }

    verifyInviteToken(token)
      .then((res) => {
        if (res.valid) {
          setTokenValid(true);
          setWorkerName(res.name || "");
          setWorkerEmail(res.email || "");
        } else {
          setTokenError(res.message || "Invalid or expired invitation token.");
        }
      })
      .catch(() => {
        setTokenError("Could not verify invitation token. Please try again or contact your administrator.");
      })
      .finally(() => setVerifying(false));
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await setPasswordWithToken(token, password);
      // Save auth token and user — they're now logged in
      localStorage.setItem("access_token", res.access_token);
      localStorage.setItem("auth_user", JSON.stringify(res.user));
      setSuccess(true);
      setTimeout(() => navigate("/"), 2500);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || "Failed to set password. The token may have expired.";
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50/30 to-slate-100 p-4">
      <div className="w-full max-w-md">

        {/* Brand Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-[11px] font-mono font-semibold mb-3">
            <ShieldCheck className="w-3.5 h-3.5" />
            AegisCare Insurance · Secure Account Setup
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Set Your Password</h1>
          <p className="text-xs text-slate-500 mt-1">
            Complete your operator account activation
          </p>
        </div>

        <div className="rounded-2xl bg-white border border-slate-200 shadow-lg p-8 space-y-5">

          {/* Loading / Verifying Token */}
          {verifying && (
            <div className="flex flex-col items-center justify-center py-8 gap-3">
              <Loader2 className="w-7 h-7 text-blue-600 animate-spin" />
              <p className="text-sm text-slate-500 font-mono">Verifying invitation token…</p>
            </div>
          )}

          {/* Token Invalid */}
          {!verifying && !tokenValid && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Invalid Invitation Link</p>
                  <p className="text-xs mt-1 text-red-700">{tokenError}</p>
                </div>
              </div>
              <button
                onClick={() => navigate("/login")}
                className="w-full py-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium transition-colors"
              >
                Go to Login
              </button>
            </div>
          )}

          {/* Token Valid — Show Success */}
          {!verifying && tokenValid && success && (
            <div className="flex flex-col items-center py-6 gap-3">
              <div className="w-14 h-14 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center">
                <CheckCircle className="w-7 h-7 text-emerald-600" />
              </div>
              <div className="text-center">
                <p className="text-base font-bold text-slate-900">Account Activated!</p>
                <p className="text-xs text-slate-500 mt-1">
                  Welcome, {workerName}. Redirecting to dashboard…
                </p>
              </div>
            </div>
          )}

          {/* Token Valid — Show Form */}
          {!verifying && tokenValid && !success && (
            <>
              {/* Worker Info Card */}
              <div className="p-3.5 rounded-xl bg-blue-50/70 border border-blue-200/80 space-y-1.5">
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-500 font-mono">Operator:</span>
                  <span className="font-semibold text-slate-800">{workerName}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-500 font-mono">Email:</span>
                  <span className="font-medium text-slate-700">{workerEmail}</span>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs font-mono flex items-center gap-2">
                    <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                    {error}
                  </div>
                )}

                <div>
                  <label className="block text-[11px] font-mono text-slate-500 uppercase tracking-widest mb-1.5 font-medium">
                    New Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Minimum 8 characters"
                    className="w-full px-4 py-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-800 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-mono text-slate-500 uppercase tracking-widest mb-1.5 font-medium">
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter password"
                    className="w-full px-4 py-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-800 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all"
                  />
                </div>
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition-colors disabled:opacity-50 flex items-center justify-center gap-2 shadow-sm"
                >
                  {submitting ? (
                    <><Loader2 className="w-4 h-4 animate-spin" />Activating Account…</>
                  ) : (
                    <><Key className="w-4 h-4" />Set Password & Activate</>
                  )}
                </button>
              </form>
            </>
          )}
        </div>

        <p className="text-center text-[11px] text-slate-400 mt-4 font-mono">
          Healthcare Data Quality & Anomaly Operations Platform
        </p>
      </div>
    </div>
  );
}

export default SetPassword;
