import { render, screen, waitFor } from "@testing-library/react";
import { CsgodoubleGame } from "@/components/profile/CsgodoubleGame";

describe("CsgodoubleGame", () => {
  const mockFetch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = mockFetch;
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          nextRollAt: Date.now() + 45_000,
          history: [7, 14, 3],
        }),
    });
  });

  it("shows Loading… initially", () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));
    render(<CsgodoubleGame />);
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("after state loads, shows countdown and balance", async () => {
    render(<CsgodoubleGame />);
    await waitFor(() => {
      expect(screen.getByText(/Rolling in/)).toBeInTheDocument();
    });
    expect(screen.getByText("Balance")).toBeInTheDocument();
    expect(screen.getByText("$100")).toBeInTheDocument();
  });

  it("fetches state from STATE_API on mount", async () => {
    render(<CsgodoubleGame />);
    await waitFor(() => {
      expect(screen.getByText(/Rolling in/)).toBeInTheDocument();
    });
    expect(mockFetch).toHaveBeenCalledWith("/api/v1/csgodouble/state");
  });

  it("renders betting zone buttons", async () => {
    render(<CsgodoubleGame />);
    await waitFor(() => {
      expect(screen.getByText(/Rolling in/)).toBeInTheDocument();
    });
    expect(screen.getByText("1 to 7")).toBeInTheDocument();
    expect(screen.getByText("8 to 14")).toBeInTheDocument();
    expect(screen.getByText("14x")).toBeInTheDocument();
  });

  it("renders 10 history slots with placeholders and server history", async () => {
    render(<CsgodoubleGame />);
    await waitFor(() => {
      expect(screen.getByText(/Rolling in/)).toBeInTheDocument();
    });
    const placeholders = screen.getAllByText("—");
    expect(placeholders.length).toBe(7);
  });

  it("shows bet controls: Clear, Last, +1, +10, +100, +1000, 1/2, x2, Max", async () => {
    render(<CsgodoubleGame />);
    await waitFor(() => {
      expect(screen.getByText(/Rolling in/)).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Clear" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Last" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "+1" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "+10" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "+100" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "+1000" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "1/2" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "x2" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Max" })).toBeInTheDocument();
  });

  it("shows Total placed this round", async () => {
    render(<CsgodoubleGame />);
    await waitFor(() => {
      expect(screen.getByText(/Rolling in/)).toBeInTheDocument();
    });
    expect(screen.getByText(/Total placed this round/)).toBeInTheDocument();
  });
});
