import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { api } from "@/api/client";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      return;
    }
    api
      .post("/auth/verify-email", { token })
      .then(() => setStatus("success"))
      .catch(() => setStatus("error"));
  }, [token]);

  return (
    <AuthLayout title="Email verification" subtitle="">
      <div className="flex flex-col items-center gap-3 py-4 text-center">
        {status === "loading" && <Loader2 size={32} className="animate-spin text-violet-400" />}
        {status === "success" && (
          <>
            <CheckCircle2 size={32} className="text-mint-400" />
            <p className="text-sm text-paper-300">Your email has been verified.</p>
          </>
        )}
        {status === "error" && (
          <>
            <XCircle size={32} className="text-red-400" />
            <p className="text-sm text-paper-300">This verification link is invalid or expired.</p>
          </>
        )}
        <Link to="/dashboard" className="mt-2 text-sm text-violet-400 hover:text-violet-300">
          Go to dashboard
        </Link>
      </div>
    </AuthLayout>
  );
}
