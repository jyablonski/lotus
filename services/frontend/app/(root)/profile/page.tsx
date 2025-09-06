import { auth } from "@/auth";
import { ProfilePageClient } from "@/components/profile/ProfilePageClient";

export default async function ProfilePage() {
    const session = await auth();

    if (!session) {
        return (
            <div className="page-container">
                <div className="content-container text-center">
                    <h1 className="heading-2 mb-4">Not authenticated</h1>
                    <p className="text-muted-dark">Please sign in to view your profile.</p>
                </div>
            </div>
        );
    }

    const name = session.user?.name ?? "Unknown User";
    const email = session.user?.email ?? "No Email Provided";
    const image = session.user?.image ?? null;
    const signUpDate = session.user?.createdAt ?? new Date().toISOString();

    return (
        <ProfilePageClient
            name={name}
            email={email}
            image={image}
            signupDate={signUpDate}
        />
    );
}