import { useState, useEffect, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { api } from "@/api/client";
import { useAuthStore } from "@/store/useAuthStore";

export default function LoginPage() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  async function handleGoogleLogin(credentialResponse: any) {
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.post("/auth/google", {
        id_token: credentialResponse.credential,
      });
      setTokens(data.access_token, data.refresh_token, data.user);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Google login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!googleClientId) return;

    let attempts = 0;
    const interval = setInterval(() => {
      const google = (window as any).google;
      if (google) {
        clearInterval(interval);
        google.accounts.id.initialize({
          client_id: googleClientId,
          callback: handleGoogleLogin,
        });
        google.accounts.id.renderButton(
          document.getElementById("google-signin-btn"),
          {
            theme: "outline",
            size: "large",
            width: 350,
            text: "continue_with",
            shape: "rectangular",
          }
        );
      } else {
        attempts++;
        if (attempts > 30) {
          clearInterval(interval);
        }
      }
    }, 100);

    return () => clearInterval(interval);
  }, [googleClientId]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.post("/auth/login", { email, password });
      setTokens(data.access_token, data.refresh_token, data.user);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Log in to keep building on your flowcharts."
      footer={
        <>
          Don't have an account?{" "}
          <Link to="/signup" className="text-violet-400 hover:text-violet-300">
            Sign up
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
            {error}
          </div>
        )}
        <div>
          <label className="mb-1.5 block text-xs text-paper-500">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input-field"
            placeholder="you@example.com"
          />
        </div>
        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <label className="text-xs text-paper-500">Password</label>
            <Link to="/forgot-password" className="text-xs text-violet-400 hover:text-violet-300">
              Forgot password?
            </Link>
          </div>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-field"
            placeholder="••••••••"
          />
        </div>
        <button type="submit" disabled={loading} className="btn-primary mt-1 w-full">
          {loading && <Loader2 size={16} className="animate-spin" />}
          Log in
        </button>
      </form>

      <div className="my-5 flex items-center gap-3">
        <div className="h-px flex-1 bg-white/10" />
        <span className="text-xs text-paper-500">or</span>
        <div className="h-px flex-1 bg-white/10" />
      </div>

      {googleClientId ? (
        <div className="flex justify-center w-full">
          <div id="google-signin-btn"></div>
        </div>
      ) : (
        <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 px-3 py-2.5 text-xs text-yellow-300 text-center">
          Configure <strong>VITE_GOOGLE_CLIENT_ID</strong> in <code>frontend/.env</code> to enable Google Sign-In.
        </div>
      )}
    </AuthLayout>
  );
}
