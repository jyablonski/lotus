import { auth } from "@/auth"
import { ProfileCard } from "@/components/profile-card"

export default async function Page() {
    const session = await auth()
    if (!session) return <div>Not authenticated</div>

    const name = session.user?.name ?? "Unknown User"
    const email = session.user?.email ?? "No Email Provided"
    const signUpDate = session.user?.createdAt ?? "No Creation Date Provided"

    return (
        <div className="flex justify-center items-center min-h-screen bg-gray-50">
            <ProfileCard
                name={name}
                email={email}
                signupDate={signUpDate}
            />
        </div>
    )
}
