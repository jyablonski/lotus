import { renderHook, act, waitFor } from "@testing-library/react";
import { useCreateJournal } from "@/hooks/useCreateJournal";

// Mock the server action
const mockCreateJournal = jest.fn();
jest.mock("@/actions/journals", () => ({
  createJournal: (...args: unknown[]) => mockCreateJournal(...args),
}));

// Mock next/navigation (already partially done in jest.setup.js, but we need
// access to the mock router for assertions)
const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    back: jest.fn(),
  }),
  usePathname: jest.fn(() => "/"),
}));

describe("useCreateJournal", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test("initializes with default values", () => {
    const { result } = renderHook(() => useCreateJournal());

    expect(result.current.entry).toBe("");
    expect(result.current.mood).toBe(5);
    expect(result.current.isSubmitting).toBe(false);
    expect(result.current.success).toBe(false);
    expect(result.current.error).toBeNull();
  });

  test("updates entry and mood", () => {
    const { result } = renderHook(() => useCreateJournal());

    act(() => {
      result.current.setEntry("Hello world");
      result.current.setMood(7);
    });

    expect(result.current.entry).toBe("Hello world");
    expect(result.current.mood).toBe(7);
  });

  test("sets error when submitting empty entry", async () => {
    const { result } = renderHook(() => useCreateJournal());

    await act(async () => {
      await result.current.handleSubmit({
        preventDefault: jest.fn(),
      } as unknown as React.FormEvent);
    });

    expect(result.current.error).toBe(
      "Please write something in your journal entry.",
    );
    expect(mockCreateJournal).not.toHaveBeenCalled();
  });

  test("sets error when submitting whitespace-only entry", async () => {
    const { result } = renderHook(() => useCreateJournal());

    act(() => {
      result.current.setEntry("   ");
    });

    await act(async () => {
      await result.current.handleSubmit({
        preventDefault: jest.fn(),
      } as unknown as React.FormEvent);
    });

    expect(result.current.error).toBe(
      "Please write something in your journal entry.",
    );
  });

  test("calls createJournal with correct arguments on submit", async () => {
    mockCreateJournal.mockResolvedValue({ success: true, journalId: "123" });

    const { result } = renderHook(() => useCreateJournal());

    act(() => {
      result.current.setEntry("My journal entry");
      result.current.setMood(7);
    });

    await act(async () => {
      await result.current.handleSubmit({
        preventDefault: jest.fn(),
      } as unknown as React.FormEvent);
    });

    await waitFor(() => {
      expect(mockCreateJournal).toHaveBeenCalledWith({
        journalText: "My journal entry",
        moodScore: 7,
      });
    });
  });

  test("sets success on successful submission", async () => {
    mockCreateJournal.mockResolvedValue({ success: true, journalId: "123" });

    const { result } = renderHook(() => useCreateJournal());

    act(() => {
      result.current.setEntry("Test entry");
    });

    await act(async () => {
      await result.current.handleSubmit({
        preventDefault: jest.fn(),
      } as unknown as React.FormEvent);
    });

    await waitFor(() => {
      expect(result.current.success).toBe(true);
    });
  });

  test("sets error on failed submission", async () => {
    mockCreateJournal.mockResolvedValue({
      success: false,
      error: "Backend error",
    });

    const { result } = renderHook(() => useCreateJournal());

    act(() => {
      result.current.setEntry("Test entry");
    });

    await act(async () => {
      await result.current.handleSubmit({
        preventDefault: jest.fn(),
      } as unknown as React.FormEvent);
    });

    await waitFor(() => {
      expect(result.current.error).toBe("Backend error");
    });
  });

  test("sets generic error when submission throws", async () => {
    mockCreateJournal.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useCreateJournal());

    act(() => {
      result.current.setEntry("Test entry");
    });

    await act(async () => {
      await result.current.handleSubmit({
        preventDefault: jest.fn(),
      } as unknown as React.FormEvent);
    });

    await waitFor(() => {
      expect(result.current.error).toBe(
        "Something went wrong. Please try again.",
      );
    });
  });

  test("resetForm clears all state", async () => {
    const { result } = renderHook(() => useCreateJournal());

    act(() => {
      result.current.setEntry("Some text");
      result.current.setMood(8);
    });

    act(() => {
      result.current.resetForm();
    });

    expect(result.current.entry).toBe("");
    expect(result.current.mood).toBe(5);
    expect(result.current.success).toBe(false);
    expect(result.current.error).toBeNull();
  });

  test("clears previous error before new submission", async () => {
    mockCreateJournal.mockResolvedValue({ success: true, journalId: "1" });

    const { result } = renderHook(() => useCreateJournal());

    // First: trigger validation error
    await act(async () => {
      await result.current.handleSubmit({
        preventDefault: jest.fn(),
      } as unknown as React.FormEvent);
    });
    expect(result.current.error).toBeTruthy();

    // Second: submit with valid entry — error should be cleared
    act(() => {
      result.current.setEntry("Valid entry");
    });

    await act(async () => {
      await result.current.handleSubmit({
        preventDefault: jest.fn(),
      } as unknown as React.FormEvent);
    });

    await waitFor(() => {
      expect(result.current.error).toBeNull();
    });
  });
});
