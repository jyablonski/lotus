import Link from "next/link";
import { Heart, Mail } from "lucide-react";

export default function VerifyRequestPage() {
  return (
    <div className="page-container min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center">
        {/* Logo */}
        <Link
          href="/"
          className="inline-flex items-center justify-center w-16 h-16 bg-lotus-gradient rounded-2xl mb-6 shadow-lg"
        >
          <Heart className="w-8 h-8 text-white" />
        </Link>

        <div className="card p-8">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-lotus-500/20 rounded-full mb-4">
            <Mail className="w-6 h-6 text-lotus-400" />
          </div>

          <h1 className="heading-2 mb-2">Check your email</h1>
          <p className="text-muted-dark mb-6">
            We sent you a sign-in link. Click the link in the email to continue.
          </p>

          <div className="text-sm text-dark-400 space-y-2">
            <p>The link will expire in 24 hours.</p>
            <p>
              Didn&apos;t receive it?{" "}
              <Link href="/signin" className="link-lotus">
                Try again
              </Link>
            </p>
          </div>
        </div>

        <p className="mt-6">
          <Link href="/" className="link-lotus text-sm">
            Back to home
          </Link>
        </p>
      </div>
    </div>
  );
}
