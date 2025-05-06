import { signIn } from "@/auth"

export function Login() {
    return (
        <form
            action={async () => {
                "use server"
                await signIn("github", { redirectTo: "/" })
            }}
        >
            <button type="submit" className="navbar-link-button">Login</button>
        </form>
    )
}