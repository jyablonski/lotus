import type { InvoiceServiceDefinitions } from "./generated";

/** Body `invoice` field for create / render-PDF (OpenAPI `invoiceInvoicePayload`). */
export type InvoicePayloadInput =
  InvoiceServiceDefinitions["invoiceInvoicePayload"];

export type InvoiceSenderOption = Required<
  Pick<
    InvoiceServiceDefinitions["invoiceInvoiceSenderRecord"],
    "id" | "name" | "addressLine1" | "addressLine2" | "email"
  >
>;

export type InvoiceClientOption = Required<
  Pick<
    InvoiceServiceDefinitions["invoiceInvoiceClientRecord"],
    "id" | "name" | "addressLine1" | "addressLine2" | "attention"
  >
>;

export type InvoicePaymentOption = Required<
  Pick<
    InvoiceServiceDefinitions["invoiceInvoicePaymentRecord"],
    "id" | "checkPayableTo" | "achAccountNumber" | "achRoutingNumber"
  >
>;

export interface InvoiceReferenceData {
  senders: InvoiceSenderOption[];
  clients: InvoiceClientOption[];
  paymentProfiles: InvoicePaymentOption[];
}
