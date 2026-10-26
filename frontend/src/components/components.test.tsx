import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import type { Money } from "../api/types";
import { ConfirmDialog } from "./ConfirmDialog";
import { Field } from "./Field";
import { MoneyInput } from "./MoneyInput";
import { StatusBadge } from "./StatusBadge";
import { Timeline } from "./Timeline";

describe("Field", () => {
  it("links label, hint and error to the control and states the error in text", () => {
    render(
      <Field label="Сумма" hint="От 100 000 ₽" error="Обязательное поле" required>
        {(control) => <input {...control} />}
      </Field>,
    );
    const input = screen.getByRole("textbox", { name: /Сумма/ });
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription(/Ошибка: Обязательное поле.*От 100 000/);
  });
});

function MoneyHarness({ onValue }: { onValue: (value: Money | null) => void }) {
  const [value, setValue] = useState<Money | null>(null);
  const [invalid, setInvalid] = useState(false);
  return (
    <Field label="Выручка" error={invalid ? "Введите сумму числом" : null}>
      {(control) => (
        <MoneyInput
          {...control}
          value={value}
          onInvalidChange={setInvalid}
          onChange={(next) => {
            setValue(next);
            onValue(next);
          }}
        />
      )}
    </Field>
  );
}

describe("MoneyInput", () => {
  it("emits money as a string and groups digits on blur", async () => {
    const onValue = vi.fn();
    render(<MoneyHarness onValue={onValue} />);
    const input = screen.getByRole("textbox", { name: "Выручка" });
    await userEvent.type(input, "600000");
    expect(onValue).toHaveBeenLastCalledWith("600000.00");
    await userEvent.tab();
    expect(input).toHaveValue("600 000");
  });

  it("keeps missing distinct from zero and flags bad input", async () => {
    const onValue = vi.fn();
    render(<MoneyHarness onValue={onValue} />);
    const input = screen.getByRole("textbox", { name: "Выручка" });
    await userEvent.type(input, "0");
    expect(onValue).toHaveBeenLastCalledWith("0.00");
    await userEvent.clear(input);
    expect(onValue).toHaveBeenLastCalledWith(null);
    await userEvent.type(input, "12x");
    expect(onValue).toHaveBeenLastCalledWith(null);
    expect(screen.getByText("Введите сумму числом")).toBeInTheDocument();
  });
});

describe("StatusBadge", () => {
  it("uses the client label from contracts/statuses.json", () => {
    render(<StatusBadge status="PROCESSING_ERROR" />);
    expect(screen.getByText("Проверка временно недоступна")).toHaveClass("badge-attention");
  });
});

describe("ConfirmDialog", () => {
  it("confirms and cancels without leaking to the other handler", async () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        open
        title="Отказать?"
        description="Решение нельзя отменить."
        confirmLabel="Отказать"
        tone="danger"
        onConfirm={onConfirm}
        onCancel={onCancel}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Отказать" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    await userEvent.click(screen.getByRole("button", { name: "Отмена" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("does not confirm while disabled or busy", async () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog open title="t" description="d" confirmLabel="Да" confirmDisabled onConfirm={onConfirm} onCancel={vi.fn()} />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Да" }));
    expect(onConfirm).not.toHaveBeenCalled();
  });
});

describe("Timeline", () => {
  it("shows the newest event first with readable labels", () => {
    render(
      <Timeline
        events={[
          { action: "SUBMIT", from_status: "DRAFT", to_status: "SUBMITTED", revision_no: 1, created_at: "2026-10-26T10:00:00Z" },
          { action: "FINISH_CHECKS", from_status: "CHECKING", to_status: "MANUAL_REVIEW", revision_no: 1, created_at: "2026-10-26T10:01:00Z" },
        ]}
      />,
    );
    const items = screen.getAllByRole("listitem");
    expect(items[0]).toHaveTextContent("Проверки завершены");
    expect(items[0]).toHaveTextContent("Заявка у специалиста");
    expect(items[1]).toHaveTextContent("Заявка отправлена");
  });
});
