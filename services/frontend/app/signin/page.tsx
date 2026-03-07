import { auth, signIn } from "@/auth";
import { redirect } from "next/navigation";
import Link from "next/link";
import { Heart, Github, Mail } from "lucide-react";
import { ROUTES } from "@/lib/routes";

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ callbackUrl?: string; error?: string }>;
}) {
  const session = await auth();
  if (session?.user) {
    redirect(ROUTES.home);
  }

  const params = await searchParams;
  const callbackUrl = params.callbackUrl ?? ROUTES.home;
  const error = params.error;

  return (
    <div className="page-container min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link
            href={ROUTES.home}
            className="inline-flex items-center justify-center w-16 h-16 bg-lotus-gradient rounded-2xl mb-4 shadow-lg"
          >
            <Heart className="w-8 h-8 text-white" />
          </Link>
          <h1 className="heading-2">Welcome to Lotus</h1>
          <p className="text-muted-dark mt-2">Sign in to start journaling</p>
        </div>

        <div className="card p-8">
          {/* Error message */}
          {error && (
            <div className="alert-error mb-6">
              {error === "OAuthAccountNotLinked"
                ? "This email is already associated with another sign-in method."
                : "Something went wrong. Please try again."}
            </div>
          )}

          {/* Magic link form */}
          <form
            action={async (formData: FormData) => {
              "use server";
              const email = formData.get("email") as string;
              await signIn("resend", { email, redirectTo: callbackUrl });
            }}
          >
            <label htmlFor="email" className="label">
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              placeholder="you@example.com"
              className="input-primary w-full mb-4"
              autoComplete="email"
              autoFocus
            />
            <button
              type="submit"
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              <Mail className="w-4 h-4" />
              Sign in with Email
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-dark-600" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="bg-dark-800 px-3 text-dark-400">
                or continue with
              </span>
            </div>
          </div>

          {/* GitHub OAuth */}
          <form
            action={async () => {
              "use server";
              await signIn("github", { redirectTo: callbackUrl });
            }}
          >
            <button
              type="submit"
              className="btn-secondary w-full flex items-center justify-center gap-2"
            >
              <Github className="w-4 h-4" />
              Sign in with GitHub
            </button>
          </form>
        </div>

        {/* Back link */}
        <p className="text-center mt-6">
          <Link href={ROUTES.home} className="link-lotus text-sm">
            Back to home
          </Link>
        </p>
      </div>
    </div>
  );
}
