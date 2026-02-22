import { render, screen } from "@testing-library/react";
import UserAvatar from "@/components/UserAvatar";

jest.mock("../../../auth", () => ({
  auth: jest.fn(),
}));

jest.mock("next/image", () => {
  return ({ src, alt, ...props }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} {...props} />
  );
});

jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

import { auth } from "../../../auth";
const mockAuth = auth as jest.MockedFunction<typeof auth>;

describe("UserAvatar", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("returns null when no session", async () => {
    mockAuth.mockResolvedValue(null);
    const result = await UserAvatar();
    expect(result).toBeNull();
  });

  it("returns null when session has no user image", async () => {
    mockAuth.mockResolvedValue({
      user: { name: "Jane", email: "jane@example.com", image: undefined },
      expires: "2099-01-01",
    });
    const result = await UserAvatar();
    expect(result).toBeNull();
  });

  it("renders avatar image with link to profile", async () => {
    mockAuth.mockResolvedValue({
      user: {
        name: "Jane",
        email: "jane@example.com",
        image: "https://example.com/avatar.jpg",
      },
      expires: "2099-01-01",
    });
    const AvatarEl = await UserAvatar();
    render(AvatarEl!);
    const img = screen.getByAltText("User Avatar");
    expect(img).toHaveAttribute("src", "https://example.com/avatar.jpg");
    expect(img.closest("a")).toHaveAttribute("href", "/profile");
  });
});
