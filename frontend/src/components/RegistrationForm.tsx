/**
 * Register / "Cancel my registration" controls for the logged-in user.
 *
 * There is no form body to fill in: the API registers whoever owns the token.
 * Register stays clickable even when the user is registered or the event is
 * full, because the API enforces those rules and its 409 message is toasted.
 */
import { CheckCircle2, UserPlus, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useCancelRegistration, useRegisterForEvent } from "@/hooks/useRegistrationActions"
import type { Registration } from "@/lib/api"

interface RegistrationFormProps {
  eventId: number
  /** The user's own registration, if it is on the loaded page of attendees. */
  myRegistration?: Registration
}

export function RegistrationForm({ eventId, myRegistration }: RegistrationFormProps) {
  const registerMutation = useRegisterForEvent(eventId)
  const cancelMutation = useCancelRegistration(eventId)

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Button onClick={() => registerMutation.mutate()} disabled={registerMutation.isPending}>
        <UserPlus /> {registerMutation.isPending ? "Registering..." : "Register"}
      </Button>
      {myRegistration && (
        <>
          <Button
            variant="outline"
            onClick={() => cancelMutation.mutate(myRegistration.id)}
            disabled={cancelMutation.isPending}
          >
            <X /> {cancelMutation.isPending ? "Cancelling..." : "Cancel my registration"}
          </Button>
          <span className="flex items-center gap-1 text-sm text-muted-foreground">
            <CheckCircle2 className="size-4 text-primary" /> You are registered
          </span>
        </>
      )}
    </div>
  )
}
