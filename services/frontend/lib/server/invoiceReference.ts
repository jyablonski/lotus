import "server-only";

import { auth } from "@/auth";
import { BACKEND_URL } from "@/lib/config";
import { backendHeaders } from "@/lib/server/backendHeaders";
import { canAccessAdminRoutes } from "@/lib/server/admin";
import type { InvoiceServiceDefinitions } from "@/types/generated";
import type {
  InvoiceClientOption,
  InvoicePaymentOption,
  InvoiceReferenceData,
  InvoiceSenderOption,
} from "@/types/invoice";

type Defs = InvoiceServiceDefinitions;

function normalizeSender(
  row: Defs["invoiceInvoiceSenderRecord"] | undefined,
): InvoiceSenderOption {
  return {
    id: row?.id ?? "",
    name: row?.name ?? "",
    addressLine1: row?.addressLine1 ?? "",
    addressLine2: row?.addressLine2 ?? "",
    email: row?.email ?? "",
  };
}

function normalizeClient(
  row: Defs["invoiceInvoiceClientRecord"] | undefined,
): InvoiceClientOption {
  return {
    id: row?.id ?? "",
    name: row?.name ?? "",
    addressLine1: row?.addressLine1 ?? "",
    addressLine2: row?.addressLine2 ?? "",
    attention: row?.attention ?? "",
  };
}

function normalizePayment(
  row: Defs["invoiceInvoicePaymentRecord"] | undefined,
): InvoicePaymentOption {
  return {
    id: row?.id ?? "",
    checkPayableTo: row?.checkPayableTo ?? "",
    achAccountNumber: row?.achAccountNumber ?? "",
    achRoutingNumber: row?.achRoutingNumber ?? "",
  };
}

/** Loads saved senders / clients / payment rows for the invoice form (admin-only). */
export async function fetchInvoiceReferenceData(): Promise<InvoiceReferenceData | null> {
  const session = await auth();
  if (
    !session?.user?.id ||
    !(await canAccessAdminRoutes(session.user.email, session.user.role))
  ) {
    return null;
  }

  const params = new URLSearchParams({ user_id: session.user.id });
  const response = await fetch(
    `${BACKEND_URL}/v1/admin/invoices/reference-data?${params.toString()}`,
    {
      method: "GET",
      headers: backendHeaders(),
      cache: "no-store",
    },
  );

  if (!response.ok) {
    console.error(
      "Invoice reference data error:",
      response.status,
      await response.text(),
    );
    return null;
  }

  const raw =
    (await response.json()) as Defs["invoiceGetInvoiceReferenceDataResponse"] & {
      payment_profiles?: Defs["invoiceInvoicePaymentRecord"][];
    };

  const payments = raw.paymentProfiles ?? raw.payment_profiles;

  return {
    senders: (raw.senders ?? []).map(normalizeSender),
    clients: (raw.clients ?? []).map(normalizeClient),
    paymentProfiles: (payments ?? []).map(normalizePayment),
  };
}
