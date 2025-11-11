import { useState, useMemo } from "react";
import { JournalEntry } from "@/types/journal";
import {
  filterJournals,
  getUniqueMoodsFromJournals,
} from "@/lib/utils/journalFilters";

export function useJournalFilters(journals: JournalEntry[]) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedMood, setSelectedMood] = useState<string>("all");

  const filteredJournals = useMemo(() => {
    return filterJournals(journals, searchTerm, selectedMood);
  }, [journals, searchTerm, selectedMood]);

  const uniqueMoods = useMemo(() => {
    return getUniqueMoodsFromJournals(journals);
  }, [journals]);

  const clearFilters = () => {
    setSearchTerm("");
    setSelectedMood("all");
  };

  return {
    searchTerm,
    setSearchTerm,
    selectedMood,
    setSelectedMood,
    filteredJournals,
    uniqueMoods,
    clearFilters,
    hasActiveFilters: searchTerm.trim() !== "" || selectedMood !== "all",
  };
}
