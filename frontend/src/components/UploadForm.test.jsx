import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getDatasetStatus, uploadDataset } from "../api/datasets";
import UploadForm from "./UploadForm";

vi.mock("../api/datasets", () => ({
  uploadDataset: vi.fn(),
  getDatasetStatus: vi.fn(),
}));

const csvFile = () => new File(["ORDERNUMBER,SALES\n1,2\n"], "sales.csv", { type: "text/csv" });

function renderForm(props = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <UploadForm {...props} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return userEvent.setup();
}

describe("UploadForm", () => {
  beforeEach(() => vi.resetAllMocks());

  it("uploads the file, polls processing status, then shows success", async () => {
    vi.mocked(uploadDataset).mockResolvedValue({ dataset_id: 7, status: "processing" });
    vi.mocked(getDatasetStatus).mockResolvedValue({ id: 7, status: "completed", progress: 100, error_message: null });
    const onUploadFinished = vi.fn();

    const user = renderForm({ onUploadFinished });
    const file = csvFile();
    await user.upload(screen.getByLabelText("CSV file"), file);
    await user.click(screen.getByRole("button", { name: "Upload" }));

    expect(await screen.findByRole("status")).toHaveTextContent("File processed successfully");
    expect(uploadDataset).toHaveBeenCalledWith(file, expect.any(Object));
    expect(screen.getByRole("link", { name: /view dataset/i })).toHaveAttribute("href", "/datasets/7");
    expect(onUploadFinished).toHaveBeenCalledWith(7);
  });

  it("shows the server's validation error", async () => {
    vi.mocked(uploadDataset).mockRejectedValue({
      response: { status: 400, data: { detail: "Missing required columns: SALES" } },
    });

    const user = renderForm();
    await user.upload(screen.getByLabelText("CSV file"), csvFile());
    await user.click(screen.getByRole("button", { name: "Upload" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Missing required columns: SALES");
  });
});
