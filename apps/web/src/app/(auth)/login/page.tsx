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
import { Loader2, LogIn } from "lucide-react";
import { login } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/stores/auth-store";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const router = useRouter();
  const { setTokens, setProfile } = useAuthStore();

  const handleLogin = async () => {
    setError(null);

    if (!email.trim()) {
      setError("Please enter your email address.");
      return;
    }
    if (!password) {
      setError("Please enter your password.");
      return;
    }

    setLoading(true);
    try {
      const result = await login({ email: email.trim(), password });
      setTokens(result.access_token, result.refresh_token);
      setProfile(result.user);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full border-slate-200/80 shadow-xl shadow-slate-900/[0.04]">
      <CardHeader className="text-center pb-4">
        <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-base">
          V
        </div>
        <CardTitle className="text-xl font-bold">Sign in to Vaktram</CardTitle>
        <CardDescription className="text-sm">
          Enter your credentials to continue.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 px-6">
        {error && (
          <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="email" className="text-sm">
            Email
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="you@company.com"
            className="h-11 rounded-lg"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="password" className="text-sm">
            Password
          </Label>
          <Input
            id="password"
            type="password"
            placeholder="Your password"
            className="h-11 rounded-lg"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleLogin();
            }}
            disabled={loading}
          />
        </div>
        <Button
          className="w-full h-11 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground"
          onClick={handleLogin}
          disabled={loading}
        >
          {loading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <LogIn className="mr-2 h-4 w-4" />
          )}
          Sign in
        </Button>
      </CardContent>
      <CardFooter className="justify-center pb-6">
        <p className="text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link
            href="/signup"
            className="font-medium text-primary hover:underline underline-offset-2"
          >
            Sign up
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
