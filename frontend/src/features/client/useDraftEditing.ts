import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo, useState } from "react";
import { api } from "../../api/endpoints";
import { isApiError } from "../../api/errors";
import { queryKeys } from "../../api/queryClient";
import type { ClientApplication } from "../../api/types";
import { useCommand } from "../../api/useCommand";
import {
  changedFields,
  EDITABLE_FIELDS,
  isDirty,
  serverFieldErrors,
  valuesFromDraft,
  type DraftFormValues,
  type EditableField,
  type FieldErrors,
} from "./draftForm";

/**
 * Локальное редактирование черновика с явным сохранением на сервер.
 * Индикатор показывает время успешного ответа сервера, а не локальное состояние.
 */
export function useDraftEditing(app: ClientApplication, allowedFields: readonly EditableField[] = EDITABLE_FIELDS) {
  const queryClient = useQueryClient();
  const saved = useMemo(() => valuesFromDraft(app.draft_fields), [app.draft_fields]);
  const [values, setValues] = useState<DraftFormValues>(saved);
  const [formatErrors, setFormatErrors] = useState<Partial<Record<EditableField, boolean>>>({});
  const [serverErrors, setServerErrors] = useState<FieldErrors>({});
  const [savedAt, setSavedAt] = useState<Date | null>(null);

  const dirty = isDirty(saved, values, allowedFields);
  const hasFormatErrors = Object.values(formatErrors).some(Boolean);

  const save = useCommand(
    (_: void) => api.saveDraft(app.id, app.version, changedFields(saved, values, allowedFields)),
    {
      onSuccess: (updated) => {
        queryClient.setQueryData(queryKeys.application(app.id), updated);
        setValues(valuesFromDraft(updated.draft_fields));
        setServerErrors({});
        setSavedAt(new Date());
      },
      onError: (error) => {
        if (isApiError(error) && error.kind === "validation") setServerErrors(serverFieldErrors(error.fieldErrors));
      },
    },
  );

  const setField = useCallback(<K extends EditableField>(field: K, value: DraftFormValues[K]) => {
    setValues((current) => ({ ...current, [field]: value }));
    setServerErrors((current) => ({ ...current, [field]: undefined }));
  }, []);

  const setFormatError = useCallback((field: EditableField, invalid: boolean) => {
    setFormatErrors((current) => (current[field] === invalid ? current : { ...current, [field]: invalid }));
  }, []);

  /** После 409: отбросить локальные правки и взять актуальную версию с сервера. */
  const reloadFromServer = useCallback(async () => {
    const fresh = await queryClient.fetchQuery({
      queryKey: queryKeys.application(app.id),
      queryFn: ({ signal }) => api.getApplication(app.id, { signal }),
      staleTime: 0,
    });
    setValues(valuesFromDraft(fresh.draft_fields));
    setFormatErrors({});
    setServerErrors({});
    save.reset();
  }, [app.id, queryClient, save]);

  const fieldErrors: FieldErrors = { ...serverErrors };
  for (const field of allowedFields) {
    if (formatErrors[field]) fieldErrors[field] = "Введите сумму цифрами, например 250 000 или 250 000,50";
  }

  return {
    values,
    saved,
    dirty,
    hasFormatErrors,
    fieldErrors,
    setServerErrors,
    savedAt,
    save,
    setField,
    setFormatError,
    reloadFromServer,
  };
}
