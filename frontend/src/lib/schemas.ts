/**
 * Zod form schemas that mirror the backend's Pydantic rules.
 *
 * They only give instant feedback in the browser; the API still validates
 * everything and its 422 message is shown if something slips through.
 */
import { format } from "date-fns"
import { z } from "zod"

/** Today's date as YYYY-MM-DD in the user's time zone. */
export const todayIso = (): string => format(new Date(), "yyyy-MM-dd")

export const loginSchema = z.object({
  email: z.email("Enter a valid email"),
  password: z.string().min(1, "Enter your password"),
})
export type LoginValues = z.infer<typeof loginSchema>

// Mirrors UserCreate: full_name 1-100 after trimming, password 8-128.
export const registerSchema = z.object({
  email: z.email("Enter a valid email"),
  full_name: z.string().trim().min(1, "Enter your name").max(100, "At most 100 characters"),
  password: z.string().min(8, "At least 8 characters").max(128, "At most 128 characters"),
})
export type RegisterValues = z.infer<typeof registerSchema>

// Mirrors EventCreate / EventUpdate field rules.
const eventFields = z.object({
  title: z.string().trim().min(1, "Enter a title").max(200, "At most 200 characters"),
  description: z.string().trim().max(2000, "At most 2000 characters"),
  // <input type="date"> gives YYYY-MM-DD, which compares correctly as a string.
  event_date: z.string().min(1, "Pick a date"),
  location: z.string().trim().min(1, "Enter a location").max(200, "At most 200 characters"),
  max_capacity: z
    .number({ error: "Enter a number" })
    .int("Whole numbers only")
    .min(1, "At least 1")
    .max(10000, "At most 10000"),
})

/** Editing an event: the API allows any date, so no past-date check. */
export const eventUpdateSchema = eventFields
export type EventFormValues = z.infer<typeof eventFields>

/** Creating an event: like the API, the date cannot be in the past. */
export const eventCreateSchema = eventFields.refine(
  (values) => values.event_date >= todayIso(),
  { message: "Date cannot be in the past", path: ["event_date"] },
)
