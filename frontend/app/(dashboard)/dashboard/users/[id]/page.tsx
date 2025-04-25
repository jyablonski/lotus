import React from "react";

// If you're not using `await` on `params`, just destructure and use it directly
export default async function Page({ params }: {
  params: Promise<{
    id: string
  }>
}) {
  // You do NOT need `await` on `params`, because it's already resolved
  const { id } = await params;

  return <div>User Profile: {id}</div>;
}
