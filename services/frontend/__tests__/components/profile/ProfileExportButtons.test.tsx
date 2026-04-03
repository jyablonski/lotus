import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ProfileExportButtons } from "@/components/profile/ProfileExportButtons";
import {
  exportJournalsAsCsv,
  exportJournalsAsMarkdown,
} from "@/actions/journals";

jest.mock("@/actions/journals", () => ({
  exportJournalsAsCsv: jest.fn(),
  exportJournalsAsMarkdown: jest.fn(),
}));

jest.mock("lucide-react", () => ({
  FileDown: () => <svg data-testid="icon-file-down" />,
  FileText: () => <svg data-testid="icon-file-text" />,
}));

const mockCsv = exportJournalsAsCsv as jest.Mock;
const mockMd = exportJournalsAsMarkdown as jest.Mock;

describe("ProfileExportButtons", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.URL.createObjectURL = jest.fn(() => "blob:fake-url");
    global.URL.revokeObjectURL = jest.fn();
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

  it("triggers CSV download on success", async () => {
    mockCsv.mockResolvedValue({
      content: "id,text\n1,hello",
      filename: "journals.csv",
      mimeType: "text/csv;charset=utf-8",
    });

    const clickSpy = jest.spyOn(HTMLAnchorElement.prototype, "click");
    render(<ProfileExportButtons />);
    fireEvent.click(screen.getByRole("button", { name: /Export CSV/i }));

    await waitFor(() => expect(mockCsv).toHaveBeenCalledTimes(1));
    expect(URL.createObjectURL).toHaveBeenCalled();
    expect(clickSpy).toHaveBeenCalled();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:fake-url");
  });

  it("triggers Markdown download on success", async () => {
    mockMd.mockResolvedValue({
      content: "# Journal",
      filename: "journals.md",
      mimeType: "text/markdown;charset=utf-8",
    });

    const clickSpy = jest.spyOn(HTMLAnchorElement.prototype, "click");
    render(<ProfileExportButtons />);
    fireEvent.click(screen.getByRole("button", { name: /Export Markdown/i }));

    await waitFor(() => expect(mockMd).toHaveBeenCalledTimes(1));
    expect(clickSpy).toHaveBeenCalled();
  });

  it("shows error message when action returns an error", async () => {
    mockCsv.mockResolvedValue({ error: "Unauthorized" });

    render(<ProfileExportButtons />);
    fireEvent.click(screen.getByRole("button", { name: /Export CSV/i }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent("Unauthorized"),
    );
  });

  it("disables buttons while a request is in flight", async () => {
    let resolve: (v: unknown) => void;
    mockCsv.mockReturnValue(new Promise((r) => (resolve = r)));

    render(<ProfileExportButtons />);
    fireEvent.click(screen.getByRole("button", { name: /Export CSV/i }));

    const buttons = screen.getAllByRole("button", { name: /Preparing/i });
    expect(buttons).toHaveLength(2);
    buttons.forEach((btn) => expect(btn).toBeDisabled());

    resolve!({ content: "", filename: "x.csv", mimeType: "text/csv" });
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: /Export CSV/i }),
      ).not.toBeDisabled(),
    );
  });
});
