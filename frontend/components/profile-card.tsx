interface ProfileCardProps {
    name?: string
    email?: string
    signupDate: string
}

export function ProfileCard({ name, email, signupDate }: ProfileCardProps) {
    return (
        <div className="bg-white shadow-lg rounded-2xl p-8 w-150">
            <div className="flex flex-col items-center">
                <h2 className="text-2xl font-bold mt-4">{name}</h2>
                <p className="text-gray-500">{email}</p>
                <div className="mt-6 text-center">
                    <p className="text-sm text-gray-400">Signed up on</p>
                    <p className="text-md font-medium">{new Date(signupDate).toLocaleDateString()}</p>
                </div>
            </div>
        </div>
    )
}
