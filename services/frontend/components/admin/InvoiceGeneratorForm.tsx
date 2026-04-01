"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { renderInvoicePdf, saveInvoice } from "@/actions/invoices";
import type {
  InvoicePayloadInput,
  InvoiceReferenceData,
} from "@/types/invoice";

interface LineItem {
  description: string;
  hours: number;
  rate: number;
  amount: number;
}

interface InvoiceData {
  sender: {
    name: string;
    addressLine1: string;
    addressLine2: string;
    email: string;
  };
  client: {
    name: string;
    addressLine1: string;
    addressLine2: string;
    attention: string;
  };
  payment: {
    checkPayableTo: string;
    achAccountNumber: string;
    achRoutingNumber: string;
  };
  invoice: {
    number: string;
    date: string;
    dueDate: string;
    terms: string;
  };
  lineItems: LineItem[];
}

const TERMS_OPTIONS = [
  "Net 15",
  "Net 30",
  "Net 45",
  "Net 60",
  "Due on Receipt",
];

function emptyLineItem(): LineItem {
  return { description: "", hours: 0, rate: 0, amount: 0 };
}

function todayISO(): string {
  return new Date().toISOString().split("T")[0];
}

function addDays(dateStr: string, days: number): string {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + days);
  return d.toISOString().split("T")[0];
}

function downloadBase64Pdf(base64: string, filename: string) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  const blob = new Blob([bytes], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

interface InvoiceGeneratorFormProps {
  referenceData?: InvoiceReferenceData;
}

export function InvoiceGeneratorForm({
  referenceData,
}: InvoiceGeneratorFormProps) {
  const today = todayISO();

  const senders = referenceData?.senders ?? [];
  const clients = referenceData?.clients ?? [];
  const paymentProfiles = referenceData?.paymentProfiles ?? [];
  const hasPrefill =
    senders.length > 0 || clients.length > 0 || paymentProfiles.length > 0;

  const [senderPick, setSenderPick] = useState("");
  const [clientPick, setClientPick] = useState("");
  const [paymentPick, setPaymentPick] = useState("");

  const [sender, setSender] = useState({
    name: "",
    addressLine1: "",
    addressLine2: "",
    email: "",
  });
  const [client, setClient] = useState({
    name: "",
    addressLine1: "",
    addressLine2: "",
    attention: "",
  });
  const [payment, setPayment] = useState({
    checkPayableTo: "",
    achAccountNumber: "",
    achRoutingNumber: "",
  });
  const [invoice, setInvoice] = useState({
    number: "",
    date: today,
    dueDate: addDays(today, 30),
    terms: "Net 30",
  });
  const [lineItems, setLineItems] = useState<LineItem[]>([emptyLineItem()]);
  const [isSaving, setIsSaving] = useState(false);
  const [isPdfLoading, setIsPdfLoading] = useState(false);
  const [saveResult, setSaveResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  function updateLineItem(index: number, field: keyof LineItem, value: string) {
    setLineItems((prev) =>
      prev.map((item, i) => {
        if (i !== index) return item;
        const updated = { ...item };
        if (field === "description") {
          updated.description = value;
        } else {
          const num = parseFloat(value) || 0;
          updated[field] = num;
          if (field === "hours" || field === "rate") {
            const hours = field === "hours" ? num : updated.hours;
            const rate = field === "rate" ? num : updated.rate;
            updated.amount = Math.round(hours * rate * 100) / 100;
          }
        }
        return updated;
      }),
    );
  }

  function addLineItem() {
    setLineItems((prev) => [...prev, emptyLineItem()]);
  }

  function removeLineItem(index: number) {
    setLineItems((prev) => prev.filter((_, i) => i !== index));
  }

  function buildInvoiceData(): InvoiceData {
    return { sender, client, payment, invoice, lineItems };
  }

  function toPayload(): InvoicePayloadInput {
    const data = buildInvoiceData();
    return {
      sender: {
        name: data.sender.name,
        addressLine1: data.sender.addressLine1,
        addressLine2: data.sender.addressLine2,
        email: data.sender.email,
      },
      client: {
        name: data.client.name,
        addressLine1: data.client.addressLine1,
        addressLine2: data.client.addressLine2,
        attention: data.client.attention,
      },
      payment: {
        checkPayableTo: data.payment.checkPayableTo,
        achAccountNumber: data.payment.achAccountNumber,
        achRoutingNumber: data.payment.achRoutingNumber,
      },
      invoice: {
        number: data.invoice.number,
        date: data.invoice.date,
        dueDate: data.invoice.dueDate,
        terms: data.invoice.terms,
      },
      lineItems: data.lineItems.map((item) => ({
        description: item.description,
        hours: item.hours,
        rate: item.rate,
        amount: item.amount,
      })),
    };
  }

  async function handleDownloadPDF() {
    setIsPdfLoading(true);
    setSaveResult(null);
    const result = await renderInvoicePdf(toPayload());
    if (result.success && result.pdfBase64) {
      downloadBase64Pdf(
        result.pdfBase64,
        result.filename ?? `invoice-${invoice.number || "draft"}.pdf`,
      );
    } else {
      setSaveResult({
        success: false,
        message: result.error || "Failed to generate PDF",
      });
    }
    setIsPdfLoading(false);
  }

  async function handleSaveAndDownload() {
    setIsSaving(true);
    setSaveResult(null);

    const payload = toPayload();
    const result = await saveInvoice(payload);

    setSaveResult({
      success: result.success,
      message: result.success
        ? "Invoice saved to database"
        : result.error || "Failed to save",
    });

    if (result.success) {
      const pdf = await renderInvoicePdf(payload);
      if (pdf.success && pdf.pdfBase64) {
        downloadBase64Pdf(
          pdf.pdfBase64,
          pdf.filename ?? `invoice-${invoice.number || "draft"}.pdf`,
        );
      } else {
        setSaveResult({
          success: true,
          message:
            "Invoice saved, but PDF download failed: " +
            (pdf.error ?? "unknown error"),
        });
      }
    }

    setIsSaving(false);
  }

  const total = lineItems.reduce((sum, item) => sum + item.amount, 0);

  function onSenderSelectChange(value: string) {
    setSenderPick(value);
    if (!value) return;
    const row = senders.find((s) => s.id === value);
    if (row) {
      setSender({
        name: row.name,
        addressLine1: row.addressLine1,
        addressLine2: row.addressLine2,
        email: row.email,
      });
    }
  }

  function onClientSelectChange(value: string) {
    setClientPick(value);
    if (!value) return;
    const row = clients.find((c) => c.id === value);
    if (row) {
      setClient({
        name: row.name,
        addressLine1: row.addressLine1,
        addressLine2: row.addressLine2,
        attention: row.attention,
      });
    }
  }

  function onPaymentSelectChange(value: string) {
    setPaymentPick(value);
    if (!value) return;
    const row = paymentProfiles.find((p) => p.id === value);
    if (row) {
      setPayment({
        checkPayableTo: row.checkPayableTo,
        achAccountNumber: row.achAccountNumber,
        achRoutingNumber: row.achRoutingNumber,
      });
    }
  }

  return (
    <div className="flex flex-col lg:flex-row gap-8 items-start">
      <div className="flex-1 min-w-0 space-y-6 w-full">
        {/* Sender Info */}
        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-primary-dark mb-4">
              From (Sender)
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">Name</label>
                <input
                  type="text"
                  value={sender.name}
                  onChange={(e) => {
                    setSenderPick("");
                    setSender((p) => ({ ...p, name: e.target.value }));
                  }}
                  className="textarea-primary w-full"
                  placeholder="Jacob Yablonski"
                />
              </div>
              <div>
                <label className="label">Email</label>
                <input
                  type="email"
                  value={sender.email}
                  onChange={(e) => {
                    setSenderPick("");
                    setSender((p) => ({ ...p, email: e.target.value }));
                  }}
                  className="textarea-primary w-full"
                  placeholder="you@example.com"
                />
              </div>
              <div>
                <label className="label">Address Line 1</label>
                <input
                  type="text"
                  value={sender.addressLine1}
                  onChange={(e) => {
                    setSenderPick("");
                    setSender((p) => ({ ...p, addressLine1: e.target.value }));
                  }}
                  className="textarea-primary w-full"
                  placeholder="123 Main St"
                />
              </div>
              <div>
                <label className="label">Address Line 2</label>
                <input
                  type="text"
                  value={sender.addressLine2}
                  onChange={(e) => {
                    setSenderPick("");
                    setSender((p) => ({ ...p, addressLine2: e.target.value }));
                  }}
                  className="textarea-primary w-full"
                  placeholder="City, State ZIP"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Client Info */}
        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-primary-dark mb-4">
              To (Client)
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">Company Name</label>
                <input
                  type="text"
                  value={client.name}
                  onChange={(e) => {
                    setClientPick("");
                    setClient((p) => ({ ...p, name: e.target.value }));
                  }}
                  className="textarea-primary w-full"
                  placeholder="Example Company, Inc"
                />
              </div>
              <div>
                <label className="label">Attention</label>
                <input
                  type="text"
                  value={client.attention}
                  onChange={(e) => {
                    setClientPick("");
                    setClient((p) => ({ ...p, attention: e.target.value }));
                  }}
                  className="textarea-primary w-full"
                  placeholder="Jane Doe"
                />
              </div>
              <div>
                <label className="label">Address Line 1</label>
                <input
                  type="text"
                  value={client.addressLine1}
                  onChange={(e) => {
                    setClientPick("");
                    setClient((p) => ({ ...p, addressLine1: e.target.value }));
                  }}
                  className="textarea-primary w-full"
                  placeholder="456 Business Ave"
                />
              </div>
              <div>
                <label className="label">Address Line 2</label>
                <input
                  type="text"
                  value={client.addressLine2}
                  onChange={(e) => {
                    setClientPick("");
                    setClient((p) => ({ ...p, addressLine2: e.target.value }));
                  }}
                  className="textarea-primary w-full"
                  placeholder="City, State ZIP"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Payment Info */}
        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-primary-dark mb-4">
              Payment Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="label">Check Payable To</label>
                <input
                  type="text"
                  value={payment.checkPayableTo}
                  onChange={(e) => {
                    setPaymentPick("");
                    setPayment((p) => ({
                      ...p,
                      checkPayableTo: e.target.value,
                    }));
                  }}
                  className="textarea-primary w-full"
                  placeholder="Jacob Yablonski"
                />
              </div>
              <div>
                <label className="label">ACH Account Number</label>
                <input
                  type="text"
                  value={payment.achAccountNumber}
                  onChange={(e) => {
                    setPaymentPick("");
                    setPayment((p) => ({
                      ...p,
                      achAccountNumber: e.target.value,
                    }));
                  }}
                  className="textarea-primary w-full"
                  placeholder="554041411333"
                />
              </div>
              <div>
                <label className="label">ACH Routing Number</label>
                <input
                  type="text"
                  value={payment.achRoutingNumber}
                  onChange={(e) => {
                    setPaymentPick("");
                    setPayment((p) => ({
                      ...p,
                      achRoutingNumber: e.target.value,
                    }));
                  }}
                  className="textarea-primary w-full"
                  placeholder="323111555"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Invoice Details */}
        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-primary-dark mb-4">
              Invoice Details
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="label">Invoice Number</label>
                <input
                  type="text"
                  value={invoice.number}
                  onChange={(e) =>
                    setInvoice((p) => ({ ...p, number: e.target.value }))
                  }
                  className="textarea-primary w-full"
                  placeholder="001"
                />
              </div>
              <div>
                <label className="label">Date</label>
                <input
                  type="date"
                  value={invoice.date}
                  onChange={(e) =>
                    setInvoice((p) => ({ ...p, date: e.target.value }))
                  }
                  className="textarea-primary w-full"
                />
              </div>
              <div>
                <label className="label">Due Date</label>
                <input
                  type="date"
                  value={invoice.dueDate}
                  onChange={(e) =>
                    setInvoice((p) => ({ ...p, dueDate: e.target.value }))
                  }
                  className="textarea-primary w-full"
                />
              </div>
              <div>
                <label className="label">Terms</label>
                <select
                  value={invoice.terms}
                  onChange={(e) =>
                    setInvoice((p) => ({ ...p, terms: e.target.value }))
                  }
                  className="textarea-primary w-full"
                >
                  {TERMS_OPTIONS.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Line Items */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-primary-dark">
                Line Items
              </h2>
              <button
                type="button"
                onClick={addLineItem}
                className="btn-outline text-sm"
              >
                + Add Item
              </button>
            </div>

            <div className="space-y-4">
              {lineItems.map((item, index) => (
                <div
                  key={index}
                  className="border border-dark-600 rounded-lg p-4 space-y-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <label className="label">Description</label>
                      <textarea
                        value={item.description}
                        onChange={(e) =>
                          updateLineItem(index, "description", e.target.value)
                        }
                        className="textarea-primary w-full"
                        rows={3}
                        placeholder={
                          "Software Development Services\nForecasting Widget\nPeriod: February 2026"
                        }
                      />
                    </div>
                    {lineItems.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeLineItem(index)}
                        className="text-red-400 hover:text-red-300 text-sm mt-6"
                      >
                        Remove
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="label">Hours</label>
                      <input
                        type="number"
                        step="0.5"
                        min="0"
                        value={item.hours || ""}
                        onChange={(e) =>
                          updateLineItem(index, "hours", e.target.value)
                        }
                        className="textarea-primary w-full"
                        placeholder="30"
                      />
                    </div>
                    <div>
                      <label className="label">Rate ($/hr)</label>
                      <input
                        type="number"
                        step="1"
                        min="0"
                        value={item.rate || ""}
                        onChange={(e) =>
                          updateLineItem(index, "rate", e.target.value)
                        }
                        className="textarea-primary w-full"
                        placeholder="110"
                      />
                    </div>
                    <div>
                      <label className="label">Amount</label>
                      <input
                        type="number"
                        step="0.01"
                        value={item.amount || ""}
                        onChange={(e) =>
                          updateLineItem(index, "amount", e.target.value)
                        }
                        className="textarea-primary w-full bg-dark-800/50"
                        placeholder="3300.00"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Total */}
            <div className="mt-4 pt-4 border-t border-dark-600 flex justify-end">
              <div className="text-right">
                <span className="text-muted-dark text-sm">Total Due</span>
                <p className="text-2xl font-bold text-primary-dark">
                  ${total.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Save Result */}
        {saveResult && (
          <div
            className={
              saveResult.success
                ? "rounded-lg p-3 bg-emerald-900/30 border border-emerald-700 text-emerald-300 text-sm"
                : "alert-error"
            }
          >
            {saveResult.message}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4">
          <button
            type="button"
            onClick={handleDownloadPDF}
            disabled={isPdfLoading}
            className="btn-outline flex-1 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center justify-center gap-2"
          >
            {isPdfLoading ? (
              <>
                <span
                  className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
                  aria-hidden
                />
                Generating...
              </>
            ) : (
              "Download PDF Only"
            )}
          </button>
          <button
            type="button"
            onClick={handleSaveAndDownload}
            disabled={isSaving}
            className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center justify-center gap-2"
          >
            {isSaving ? (
              <>
                <span
                  className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
                  aria-hidden
                />
                Saving...
              </>
            ) : (
              "Save & Download PDF"
            )}
          </button>
        </div>
      </div>

      {hasPrefill && (
        <aside
          className="w-full lg:w-72 xl:w-80 shrink-0 lg:sticky lg:top-24 lg:self-start"
          aria-label="Quick fill from saved profiles"
        >
          <Card className="border-dark-600 shadow-lg shadow-black/20">
            <CardContent className="p-4 space-y-5">
              <div>
                <h3 className="text-sm font-semibold text-primary-dark">
                  Quick fill
                </h3>
                <p className="text-xs text-muted-dark mt-1 leading-relaxed">
                  Tap a saved profile to load it. Editing the form clears the
                  highlight.
                </p>
              </div>

              {senders.length > 0 && (
                <div>
                  <p className="label text-[11px] uppercase tracking-wide text-muted-dark mb-2">
                    Sender
                  </p>
                  <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
                    {senders.map((s) => {
                      const active = senderPick === String(s.id);
                      return (
                        <button
                          key={s.id}
                          type="button"
                          onClick={() => onSenderSelectChange(String(s.id))}
                          aria-pressed={active}
                          className={
                            active
                              ? "w-full text-left rounded-lg px-3 py-2 text-sm transition-colors bg-lotus-500/20 border border-lotus-500/40 text-lotus-100"
                              : "w-full text-left rounded-lg px-3 py-2 text-sm transition-colors bg-dark-800/60 hover:bg-dark-700 border border-dark-600 text-dark-100"
                          }
                        >
                          <span className="font-medium block truncate">
                            {s.name}
                          </span>
                          <span className="text-xs text-muted-dark truncate block">
                            {s.email}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {clients.length > 0 && (
                <div>
                  <p className="label text-[11px] uppercase tracking-wide text-muted-dark mb-2">
                    Client
                  </p>
                  <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
                    {clients.map((c) => {
                      const active = clientPick === String(c.id);
                      return (
                        <button
                          key={c.id}
                          type="button"
                          onClick={() => onClientSelectChange(String(c.id))}
                          aria-pressed={active}
                          className={
                            active
                              ? "w-full text-left rounded-lg px-3 py-2 text-sm transition-colors bg-lotus-500/20 border border-lotus-500/40 text-lotus-100"
                              : "w-full text-left rounded-lg px-3 py-2 text-sm transition-colors bg-dark-800/60 hover:bg-dark-700 border border-dark-600 text-dark-100"
                          }
                        >
                          <span className="font-medium block truncate">
                            {c.name}
                          </span>
                          {c.attention ? (
                            <span className="text-xs text-muted-dark truncate block">
                              Attn: {c.attention}
                            </span>
                          ) : null}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {paymentProfiles.length > 0 && (
                <div>
                  <p className="label text-[11px] uppercase tracking-wide text-muted-dark mb-2">
                    Payment
                  </p>
                  <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                    {paymentProfiles.map((p) => {
                      const active = paymentPick === String(p.id);
                      return (
                        <button
                          key={p.id}
                          type="button"
                          onClick={() => onPaymentSelectChange(String(p.id))}
                          aria-pressed={active}
                          className={
                            active
                              ? "w-full text-left rounded-lg px-3 py-2 text-sm transition-colors bg-lotus-500/20 border border-lotus-500/40 text-lotus-100"
                              : "w-full text-left rounded-lg px-3 py-2 text-sm transition-colors bg-dark-800/60 hover:bg-dark-700 border border-dark-600 text-dark-100"
                          }
                        >
                          <span className="font-medium block truncate">
                            {p.checkPayableTo}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </aside>
      )}
    </div>
  );
}
