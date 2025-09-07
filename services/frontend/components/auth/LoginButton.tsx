import { signIn } from "@/auth"

export function Login() {
    return (
        <form
            action={async () => {
                "use server"
                await signIn("github", { redirectTo: "/" })
            }}
        >
            <button type="submit" className="text-white hover:text-gray-300 px-4 py-2 rounded transition-colors">
                Login
            </button>
        </form>
    )
}