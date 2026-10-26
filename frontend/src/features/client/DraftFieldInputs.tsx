import type { Product } from "../../api/types";
import { Field } from "../../components/Field";
import { MoneyInput } from "../../components/MoneyInput";
import { formatAmount } from "../../shared/money";
import { COMPANY_FORMS, FIELD_LABELS, type DraftFormValues, type EditableField, type FieldErrors } from "./draftForm";
import { amountStep } from "./policy";

interface Props {
  fields: readonly EditableField[];
  values: DraftFormValues;
  errors: FieldErrors;
  product: Product | undefined;
  disabled?: boolean;
  onChange: <K extends EditableField>(field: K, value: DraftFormValues[K]) => void;
  onFormatError: (field: EditableField, invalid: boolean) => void;
}

const MONEY_HINTS: Partial<Record<EditableField, string>> = {
  monthly_revenue: "Средняя выручка бизнеса за месяц.",
  monthly_operating_costs: "Расходы без платежей по кредитам.",
  declared_monthly_debt_payments: "Если действующих кредитов нет, укажите 0: пустое поле не считается нулём.",
};

/** Поля черновика по одному списку: используются и в черновике, и в уточнении. */
export function DraftFieldInputs({ fields, values, errors, product, disabled, onChange, onFormatError }: Props) {
  return (
    <>
      {fields.map((field) => {
        if (field === "term_months") {
          return (
            <fieldset key={field} className={`field${errors.term_months ? " field-invalid" : ""}`} disabled={disabled}>
              <legend className="field-label">{FIELD_LABELS.term_months}</legend>
              <div className="choice-group" role="radiogroup" aria-describedby={errors.term_months ? "term-error" : undefined}>
                {(product?.term_months ?? []).map((months) => (
                  <label key={months} className="choice">
                    <input
                      type="radio"
                      name="term_months"
                      value={months}
                      checked={values.term_months === months}
                      onChange={() => onChange("term_months", months)}
                    />
                    <span>{months} мес.</span>
                  </label>
                ))}
              </div>
              {errors.term_months ? (
                <p className="field-error" id="term-error">
                  {errors.term_months}
                </p>
              ) : null}
            </fieldset>
          );
        }

        if (field === "company_form") {
          return (
            <Field key={field} label={FIELD_LABELS.company_form} error={errors.company_form} required>
              {(control) => (
                <select
                  {...control}
                  className="select"
                  disabled={disabled}
                  value={values.company_form ?? ""}
                  onChange={(event) => onChange("company_form", event.target.value || null)}
                >
                  <option value="">Не выбрано</option>
                  {COMPANY_FORMS.map((form) => (
                    <option key={form.value} value={form.value}>
                      {form.label}
                    </option>
                  ))}
                </select>
              )}
            </Field>
          );
        }

        const hint =
          field === "requested_amount" && product
            ? `От ${formatAmount(product.amount_min)} до ${formatAmount(product.amount_max)}, шаг ${formatAmount(amountStep(product.code))}.`
            : MONEY_HINTS[field];
        return (
          <Field key={field} label={FIELD_LABELS[field]} hint={hint} error={errors[field]} required>
            {(control) => (
              <MoneyInput
                {...control}
                name={field}
                disabled={disabled}
                value={values[field]}
                onChange={(value) => onChange(field, value)}
                onInvalidChange={(invalid) => onFormatError(field, invalid)}
              />
            )}
          </Field>
        );
      })}
    </>
  );
}
