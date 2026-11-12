/**
 * Register / cancel mutations, shared by the Register button and the
 * registrations table so both refresh the same data afterwards.
 */
import { useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import * as api from "@/lib/api"

/** Refetch everything that shows an event's seat numbers or attendees. */
function refreshEvent(queryClient: QueryClient, eventId: number) {
  queryClient.invalidateQueries({ queryKey: ["event", eventId] })
  queryClient.invalidateQueries({ queryKey: ["registrations", eventId] })
  queryClient.invalidateQueries({ queryKey: ["events"] })
}

/** Register the logged-in user for an event. 404/409 errors are toasted globally. */
export function useRegisterForEvent(eventId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => api.registerForEvent(eventId),
    onSuccess: () => {
      refreshEvent(queryClient, eventId)
      toast.success("You are registered")
    },
  })
}

/** Cancel one of the logged-in user's registrations for an event. */
export function useCancelRegistration(eventId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (registrationId: number) => api.cancelRegistration(registrationId),
    onSuccess: () => {
      refreshEvent(queryClient, eventId)
      toast.success("Registration cancelled")
    },
  })
}
