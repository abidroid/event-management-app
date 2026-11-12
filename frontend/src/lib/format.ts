/** Small display helpers shared by several pages. */
import { format, parseISO } from "date-fns"

/** Show an API date ("2026-12-15") as "Tue 15 Dec 2026". */
export function formatDate(isoDate: string): string {
  // parseISO reads a plain date as local midnight, so the day never shifts by time zone.
  return format(parseISO(isoDate), "EEE d MMM yyyy")
}

/** Show an API timestamp as "15 Dec 2026, 09:30" in the user's time zone. */
export function formatDateTime(isoDateTime: string): string {
  return format(parseISO(isoDateTime), "d MMM yyyy, HH:mm")
}
