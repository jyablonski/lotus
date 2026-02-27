import Link from "next/link";

export function Login() {
  return (
    <Link
      href="/signin"
      className="text-white hover:text-gray-300 px-4 py-2 rounded transition-colors"
    >
      Login
    </Link>
  );
}
