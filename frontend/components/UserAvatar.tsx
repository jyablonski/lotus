import { auth } from "../auth"
import Image from 'next/image'
import Link from "next/link";


export default async function UserAvatar() {
    const session = await auth()

    if (!session?.user?.image) return null;

    return (
        <div>
            <Link href={`/profile`}>
                <Image src={session.user.image} width="50" height="50" alt="User Avatar" />
            </Link>
        </div>
    )
}