"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { createClient } from "@/lib/supabase/client";
import { Loader2, Lock, CheckCircle } from "lucide-react";

export default function ResetPasswordPage() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const router = useRouter();
  const { toast } = useToast();
  const supabase = createClient();

  const handleResetPassword = async () => {
    setError(null);

    if (!password) {
      setError("Please enter a new password.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const { error } = await supabase.auth.updateUser({ password });
      if (error) {
        setError(error.message);
      } else {
        setSuccess(true);
        toast({
          title: "Password updated!",
          description: "You can now sign in with your new password.",
        });
        setTimeout(() => router.push("/login"), 2000);
      }
    } catch {
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <Card className="w-full border-slate-200/80 shadow-xl shadow-slate-900/[0.04]">
        <CardHeader className="text-center">
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <CheckCircle className="h-5 w-5" />
          </div>
          <CardTitle className="text-xl font-bold">Password updated</CardTitle>
          <CardDescription className="mt-2">
            Your password has been reset. Redirecting you to sign in...
          </CardDescription>
        </CardHeader>
        <CardFooter className="justify-center pb-6">
          <Link
            href="/login"
            className="text-sm font-medium text-primary hover:underline underline-offset-2"
          >
            Sign in now
          </Link>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="w-full border-slate-200/80 shadow-xl shadow-slate-900/[0.04]">
      <CardHeader className="text-center pb-4">
        <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-base">
          V
        </div>
        <CardTitle className="text-xl font-bold">Set new password</CardTitle>
        <CardDescription className="text-sm">
          Enter your new password below.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 px-6">
        {error && (
          <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="password" className="text-sm">New password</Label>
          <Input
            id="password"
            type="password"
            placeholder="At least 6 characters"
            className="h-11 rounded-lg"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="confirmPassword" className="text-sm">Confirm password</Label>
          <Input
            id="confirmPassword"
            type="password"
            placeholder="Repeat your password"
            className="h-11 rounded-lg"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleResetPassword();
            }}
            disabled={loading}
          />
        </div>
        <Button
          className="w-full h-11 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground"
          onClick={handleResetPassword}
          disabled={loading}
        >
          {loading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Lock className="mr-2 h-4 w-4" />
          )}
          Reset password
        </Button>
      </CardContent>
      <CardFooter className="justify-center pb-6">
        <Link
          href="/login"
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          Back to sign in
        </Link>
      </CardFooter>
    </Card>
  );
}
