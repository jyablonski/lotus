import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { ProfileExportButtons } from "@/components/profile/ProfileExportButtons";
import { requestJournalExport, pollJournalExport } from "@/actions/journals";

jest.mock("@/actions/journals", () => ({
  requestJournalExport: jest.fn(),
  pollJournalExport: jest.fn(),
}));

jest.mock("lucide-react", () => ({
  FileDown: () => <svg data-testid="icon-file-down" />,
  FileText: () => <svg data-testid="icon-file-text" />,
}));

const mockRequest = requestJournalExport as jest.Mock;
const mockPoll = pollJournalExport as jest.Mock;

describe("ProfileExportButtons", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    global.URL.createObjectURL = jest.fn(() => "blob:fake-url");
    global.URL.revokeObjectURL = jest.fn();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders CSV and Markdown export buttons", () => {
    render(<ProfileExportButtons />);
    expect(
      screen.getByRole("button", { name: /Export CSV/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Export Markdown/i }),
    ).toBeInTheDocument();
  });

  it("triggers CSV download when poll returns complete", async () => {
    mockRequest.mockResolvedValue({ exportId: "test-export-id" });
    mockPoll.mockResolvedValue({
      status: "complete",
      content: "id,text\n1,hello",
      filename: "journals.csv",
      mimeType: "text/csv;charset=utf-8",
    });

    const clickSpy = jest.spyOn(HTMLAnchorElement.prototype, "click");
    render(<ProfileExportButtons />);
    fireEvent.click(screen.getByRole("button", { name: /Export CSV/i }));

    await waitFor(() => expect(mockRequest).toHaveBeenCalledWith("csv"));

    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    await waitFor(() =>
      expect(mockPoll).toHaveBeenCalledWith("test-export-id"),
    );
    expect(URL.createObjectURL).toHaveBeenCalled();
    expect(clickSpy).toHaveBeenCalled();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:fake-url");
  });

  it("triggers Markdown download when poll returns complete", async () => {
    mockRequest.mockResolvedValue({ exportId: "md-export-id" });
    mockPoll.mockResolvedValue({
      status: "complete",
      content: "# Journal",
      filename: "journals.md",
      mimeType: "text/markdown;charset=utf-8",
    });

    const clickSpy = jest.spyOn(HTMLAnchorElement.prototype, "click");
    render(<ProfileExportButtons />);
    fireEvent.click(screen.getByRole("button", { name: /Export Markdown/i }));

    await waitFor(() => expect(mockRequest).toHaveBeenCalledWith("markdown"));

    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    await waitFor(() => expect(clickSpy).toHaveBeenCalled());
  });

  it("shows error when requestJournalExport returns an error", async () => {
    mockRequest.mockResolvedValue({ error: "Unauthorized" });

    render(<ProfileExportButtons />);
    fireEvent.click(screen.getByRole("button", { name: /Export CSV/i }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent("Unauthorized"),
    );
  });

  it("shows error when poll returns failed status", async () => {
    mockRequest.mockResolvedValue({ exportId: "fail-id" });
    mockPoll.mockResolvedValue({ status: "failed" });

    render(<ProfileExportButtons />);
    fireEvent.click(screen.getByRole("button", { name: /Export CSV/i }));

    await waitFor(() => expect(mockRequest).toHaveBeenCalled());

    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Export failed. Please try again.",
      ),
    );
  });

  it("disables both buttons while a request is in progress", async () => {
    mockRequest.mockResolvedValue({ exportId: "in-flight-id" });
    mockPoll.mockResolvedValue({ status: "processing" });

    render(<ProfileExportButtons />);
    fireEvent.click(screen.getByRole("button", { name: /Export CSV/i }));

    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: /Preparing/i }),
      ).toBeInTheDocument(),
    );

    screen.getAllByRole("button").forEach((btn) => expect(btn).toBeDisabled());
  });
});
