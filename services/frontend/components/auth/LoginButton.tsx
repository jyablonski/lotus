import Link from "next/link";
import { ROUTES } from "@/lib/routes";

export function Login() {
  return (
    <Link
      href={ROUTES.signin}
      className="text-dark-50 hover:text-dark-200 px-4 py-2 rounded transition-colors"
    >
      Login
    </Link>
  );
}
