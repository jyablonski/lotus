import { signOut } from "@/auth"

export function Logout() {
    return (
        <form
            action={async () => {
                "use server"
                await signOut()
            }}
        >
            <button type="submit" className="navbar-logout-button">Logout</button>
        </form>
    )
}