import { auth } from "@/auth"
import { ProfileCard } from "@/components/profile-card"

export default async function Page() {
    const session = await auth()
    if (!session) return <div>Not authenticated</div>

    return (
        <div className="flex justify-center items-center min-h-screen bg-gray-50">
            <ProfileCard
                name={session.user.name}
                email={session.user.email}
                signupDate={session.expires}
            />
        </div>
    )
}
