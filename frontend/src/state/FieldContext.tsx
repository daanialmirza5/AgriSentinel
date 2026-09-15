import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";
import { api } from "../api/client";
import { FieldT } from "../types";

interface FieldContextValue {
  fields: FieldT[];
  selectedFieldId: string | null;
  selectedField: FieldT | null;
  setSelectedFieldId: (id: string) => void;
  refreshFields: () => Promise<void>;
  loading: boolean;
}

const FieldContext = createContext<FieldContextValue | undefined>(undefined);

export function FieldProvider({ children }: { children: ReactNode }) {
  const [fields, setFields] = useState<FieldT[]>([]);
  const [selectedFieldId, setSelectedFieldId] = useState<string | null>(() => localStorage.getItem("agrisentinel_field_id"));
  const [loading, setLoading] = useState(true);

  const refreshFields = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.get<FieldT[]>("/fields");
      setFields(data);
      setSelectedFieldId((prev) => {
        if (prev && data.some((f) => f.id === prev)) return prev;
        return data[0]?.id ?? null;
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshFields();
  }, [refreshFields]);

  useEffect(() => {
    if (selectedFieldId) localStorage.setItem("agrisentinel_field_id", selectedFieldId);
  }, [selectedFieldId]);

  const selectedField = fields.find((f) => f.id === selectedFieldId) ?? null;

  return (
    <FieldContext.Provider value={{ fields, selectedFieldId, selectedField, setSelectedFieldId, refreshFields, loading }}>
      {children}
    </FieldContext.Provider>
  );
}

export function useFieldContext() {
  const ctx = useContext(FieldContext);
  if (!ctx) throw new Error("useFieldContext must be used within FieldProvider");
  return ctx;
}
