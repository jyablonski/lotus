import { auth } from "@/auth"
import { ProfileCard } from "@/components/ProfileCard"

export default async function Page() {
    const session = await auth()
    if (!session) return <div>Not authenticated</div>

    const name = session.user?.name ?? "Unknown User"
    const email = session.user?.email ?? "No Email Provided"
    const signUpDate = session.user?.createdAt ?? "No Creation Date Provided"

    return (
        <ProfileCard
            name={name}
            email={email}
            signupDate={signUpDate}
        />
    )
}
