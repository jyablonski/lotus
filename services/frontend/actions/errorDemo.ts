"use server";

export interface ErrorDemoResult {
  success: boolean;
  error?: string;
}

/**
 * Demo action: does not persist anything. Waits 2s then "fails".
 * Logs the full error on the server and returns a user-friendly message to the client.
 */
export async function submitErrorDemo(
  _value: string,
): Promise<ErrorDemoResult> {
  await new Promise((resolve) => setTimeout(resolve, 2000));

  const fullError = new Error(
    `[error-demo] Simulated failure at ${new Date().toISOString()}. ` +
      "This is the full error logged on the server only.",
  );
  (fullError as Error & { code?: string }).code = "ERROR_DEMO_SIMULATED";

  console.error("[error-demo] Full error (server-only):", {
    message: fullError.message,
    code: (fullError as Error & { code?: string }).code,
    stack: fullError.stack,
  });

  return {
    success: false,
    error: "Something went wrong. Please try again.",
  };
}
