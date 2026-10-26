import { useEffect, useState } from "react";
import type { Money } from "../api/types";
import { moneyToInput, parseMoneyInput } from "../shared/money";
import type { FieldControlProps } from "./Field";

interface MoneyInputProps extends FieldControlProps {
  value: Money | null;
  /** null — поле пустое или формат неверен (см. onInvalidChange). Missing ≠ 0. */
  onChange: (value: Money | null) => void;
  onInvalidChange?: (invalid: boolean) => void;
  disabled?: boolean;
  name?: string;
}

/** Денежный ввод: строка "1234.56" наружу, группировка разрядов при выходе из поля. */
export function MoneyInput({ value, onChange, onInvalidChange, disabled, name, ...control }: MoneyInputProps) {
  const [text, setText] = useState(() => moneyToInput(value));
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    if (!focused) setText(moneyToInput(value));
  }, [value, focused]);

  function handleChange(raw: string) {
    setText(raw);
    if (raw.trim() === "") {
      onInvalidChange?.(false);
      onChange(null);
      return;
    }
    const parsed = parseMoneyInput(raw);
    onInvalidChange?.(parsed === null);
    onChange(parsed);
  }

  return (
    <div className="money-input">
      <input
        {...control}
        name={name}
        className="input num"
        type="text"
        inputMode="decimal"
        autoComplete="off"
        spellCheck={false}
        value={text}
        disabled={disabled}
        onFocus={() => setFocused(true)}
        onBlur={() => {
          setFocused(false);
          const parsed = parseMoneyInput(text);
          if (parsed) setText(moneyToInput(parsed));
        }}
        onChange={(event) => handleChange(event.target.value)}
      />
      <span className="money-input-suffix" aria-hidden="true">
        ₽
      </span>
    </div>
  );
}
