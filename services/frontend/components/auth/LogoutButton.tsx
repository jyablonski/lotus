import { signOut } from "@/auth"

export function Logout() {
    return (
        <form
            action={async () => {
                "use server"
                await signOut()
            }}
        >
            <button type="submit" className="navbar-link-button">Logout</button>
        </form>
    )
}