"use client";

import { useState, useEffect } from "react";
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
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { createClient } from "@/lib/supabase/client";
import { Loader2, Mail } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [loadingGoogle, setLoadingGoogle] = useState(false);
  const [loadingMicrosoft, setLoadingMicrosoft] = useState(false);
  const [loadingMagicLink, setLoadingMagicLink] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const router = useRouter();
  const { toast } = useToast();
  const supabase = createClient();

  useEffect(() => {
    const checkSession = async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (session) {
        router.replace("/dashboard");
      }
    };
    checkSession();
  }, [router, supabase.auth]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlError = params.get("error");
    if (urlError === "auth_callback_failed") {
      setError("Authentication failed. Please try again.");
    }
  }, []);

  const handleGoogleLogin = async () => {
    setError(null);
    setLoadingGoogle(true);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${window.location.origin}/callback`,
        },
      });
      if (error) {
        setError(error.message);
        setLoadingGoogle(false);
      }
    } catch {
      setError("An unexpected error occurred. Please try again.");
      setLoadingGoogle(false);
    }
  };

  const handleMicrosoftLogin = async () => {
    setError(null);
    setLoadingMicrosoft(true);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: "azure",
        options: {
          redirectTo: `${window.location.origin}/callback`,
        },
      });
      if (error) {
        setError(error.message);
        setLoadingMicrosoft(false);
      }
    } catch {
      setError("An unexpected error occurred. Please try again.");
      setLoadingMicrosoft(false);
    }
  };

  const handleMagicLink = async () => {
    if (!email.trim()) {
      setError("Please enter your email address.");
      return;
    }

    setError(null);
    setLoadingMagicLink(true);
    try {
      const { error } = await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: {
          emailRedirectTo: `${window.location.origin}/callback`,
        },
      });
      if (error) {
        setError(error.message);
      } else {
        toast({
          title: "Magic link sent!",
          description: "Check your email for the sign-in link.",
        });
        setEmail("");
      }
    } catch {
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setLoadingMagicLink(false);
    }
  };

  const isAnyLoading = loadingGoogle || loadingMicrosoft || loadingMagicLink;

  return (
    <Card className="w-full border-slate-200/80 shadow-xl shadow-slate-900/[0.04]">
      <CardHeader className="text-center pb-4">
        <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-base">
          V
        </div>
        <CardTitle className="text-xl font-bold">Sign in to Vaktram</CardTitle>
        <CardDescription className="text-sm">
          Choose your preferred sign-in method.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 px-6">
        {error && (
          <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <Button
          variant="outline"
          className="w-full h-11 rounded-lg border-slate-200 hover:bg-slate-50 hover:border-slate-300"
          onClick={handleGoogleLogin}
          disabled={isAnyLoading}
        >
          {loadingGoogle ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
          )}
          Continue with Google
        </Button>

        <Button
          variant="outline"
          className="w-full h-11 rounded-lg border-slate-200 hover:bg-slate-50 hover:border-slate-300"
          onClick={handleMicrosoftLogin}
          disabled={isAnyLoading}
        >
          {loadingMicrosoft ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M11.4 24H0V12.6h11.4V24zM24 24H12.6V12.6H24V24zM11.4 11.4H0V0h11.4v11.4zM24 11.4H12.6V0H24v11.4z" />
            </svg>
          )}
          Continue with Microsoft
        </Button>

        <div className="relative py-1">
          <div className="absolute inset-0 flex items-center">
            <Separator className="w-full" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-card px-2 text-muted-foreground">
              Or with email
            </span>
          </div>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="email" className="text-sm">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@company.com"
            className="h-11 rounded-lg"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleMagicLink();
            }}
            disabled={isAnyLoading}
          />
        </div>
        <Button
          className="w-full h-11 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground"
          onClick={handleMagicLink}
          disabled={isAnyLoading}
        >
          {loadingMagicLink ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Mail className="mr-2 h-4 w-4" />
          )}
          Send magic link
        </Button>

        <p className="text-center">
          <Link
            href="/forgot-password"
            className="text-xs text-muted-foreground hover:text-primary transition-colors"
          >
            Forgot your password?
          </Link>
        </p>
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
