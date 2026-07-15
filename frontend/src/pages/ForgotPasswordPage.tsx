import { useState, FormEvent } from "react";
import { Link } from "react-router-dom";
import { Loader2, MailCheck } from "lucide-react";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { api } from "@/api/client";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/auth/forgot-password", { email });
    } finally {
      setLoading(false);
      setSent(true);
    }
  }

  if (sent) {
    return (
      <AuthLayout title="Check your email" subtitle="">
        <div className="flex flex-col items-center gap-3 py-4 text-center">
          <MailCheck size={32} className="text-mint-400" />
          <p className="text-sm text-paper-300">
            If an account exists for <span className="text-paper-100">{email}</span>, we've sent a
            password reset link.
          </p>
          <Link to="/login" className="mt-2 text-sm text-violet-400 hover:text-violet-300">
            Back to log in
          </Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Reset your password"
      subtitle="Enter your email and we'll send you a reset link."
      footer={
        <Link to="/login" className="text-violet-400 hover:text-violet-300">
          Back to log in
        </Link>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
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
        <button type="submit" disabled={loading} className="btn-primary mt-1 w-full">
          {loading && <Loader2 size={16} className="animate-spin" />}
          Send reset link
        </button>
      </form>
    </AuthLayout>
  );
}
