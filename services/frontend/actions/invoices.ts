"use server";

import { auth } from "@/auth";
import { BACKEND_URL } from "@/lib/config";
import { canAccessAdminRoutes } from "@/lib/server/admin";
import { backendHeaders } from "@/lib/server/backendHeaders";
import type { InvoiceServiceDefinitions } from "@/types/generated";
import type { InvoicePayloadInput } from "@/types/invoice";

export type { InvoicePayloadInput } from "@/types/invoice";

/** Persists an invoice via the Go backend (admin-only; backend enforces Admin role). */
export async function saveInvoice(
  input: InvoicePayloadInput,
): Promise<{ success: boolean; error?: string; invoiceId?: string }> {
  const session = await auth();
  if (
    !session?.user?.id ||
    !(await canAccessAdminRoutes(session.user.email, session.user.role))
  ) {
    return { success: false, error: "Unauthorized" };
  }

  try {
    const response = await fetch(`${BACKEND_URL}/v1/admin/invoices`, {
      method: "POST",
      headers: {
        ...backendHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        userId: session.user.id,
        invoice: input,
      } satisfies InvoiceServiceDefinitions["invoiceCreateInvoiceRequest"]),
    });

    if (!response.ok) {
      const text = await response.text();
      console.error("Create invoice failed:", response.status, text);
      return {
        success: false,
        error: text || `Request failed (${response.status})`,
      };
    }

    const data =
      (await response.json()) as InvoiceServiceDefinitions["invoiceCreateInvoiceResponse"];
    const invoiceId = data.invoiceId;
    return { success: true, invoiceId };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    console.error("Failed to save invoice:", message);
    return { success: false, error: message };
  }
}

/** Renders a PDF via the Go backend (admin-only). Returns base64 PDF bytes. */
export async function renderInvoicePdf(input: InvoicePayloadInput): Promise<{
  success: boolean;
  error?: string;
  pdfBase64?: string;
  filename?: string;
}> {
  const session = await auth();
  if (
    !session?.user?.id ||
    !(await canAccessAdminRoutes(session.user.email, session.user.role))
  ) {
    return { success: false, error: "Unauthorized" };
  }

  try {
    const response = await fetch(`${BACKEND_URL}/v1/admin/invoices/pdf`, {
      method: "POST",
      headers: {
        ...backendHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        userId: session.user.id,
        invoice: input,
      } satisfies InvoiceServiceDefinitions["invoiceRenderInvoicePdfRequest"]),
    });

    if (!response.ok) {
      const text = await response.text();
      console.error("Render invoice PDF failed:", response.status, text);
      return {
        success: false,
        error: text || `Request failed (${response.status})`,
      };
    }

    const data =
      (await response.json()) as InvoiceServiceDefinitions["invoiceRenderInvoicePdfResponse"];

    const pdfB64 = data.pdfBytes;
    if (!pdfB64) {
      return { success: false, error: "Empty PDF response" };
    }

    return {
      success: true,
      pdfBase64: pdfB64,
      filename: data.filename ?? "invoice.pdf",
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    console.error("Failed to render invoice PDF:", message);
    return { success: false, error: message };
  }
}
