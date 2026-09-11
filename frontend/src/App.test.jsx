import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { routes } from "./App";

vi.mock("./api/client", () => ({
  listFilms: vi.fn().mockResolvedValue({ data: [] }),
  getFrame: vi.fn(),
  getFrameAnalysis: vi.fn(),
  resolveMediaUrl: (value) => value,
}));

function renderRoute(path) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  return render(<RouterProvider router={router} />);
}

test("renders direct library route with navigation", async () => {
  renderRoute("/library");
  expect(screen.getByRole("link", { name: /library/i })).toHaveAttribute("aria-current", "page");
  expect(await screen.findByText(/no films have been scraped yet/i)).toBeInTheDocument();
});

test("renders roadmap and not-found routes", () => {
  const { unmount } = renderRoute("/analyze");
  expect(screen.getByRole("heading", { name: "Analyze Shot" })).toBeInTheDocument();
  unmount();
  renderRoute("/missing");
  expect(screen.getByText("Page not found")).toBeInTheDocument();
});
