// app/profile/page.tsx
import { auth } from "@/auth";
import { ProfilePageClient } from "@/components/profile/ProfilePageClient";

export default async function ProfilePage() {
    const session = await auth();

    if (!session) {
        return (
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
                <h1 className="text-2xl font-bold text-gray-900 mb-4">Not authenticated</h1>
                <p className="text-gray-600">Please sign in to view your profile.</p>
            </div>
        );
    }

    const name = session.user?.name ?? "Unknown User";
    const email = session.user?.email ?? "No Email Provided";
    const image = session.user?.image ?? null; // Add this line
    const signUpDate = session.user?.createdAt ?? new Date().toISOString();

    return (
        <ProfilePageClient
            name={name}
            email={email}
            image={image} // Pass image to client component
            signupDate={signUpDate}
        />
    );
}