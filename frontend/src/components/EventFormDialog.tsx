/**
 * Dialog with the event form, used both to create a new event and to edit one.
 *
 * Pass `event` to edit it; leave it out to create a new event.
 */
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import * as api from "@/lib/api"
import { eventCreateSchema, eventUpdateSchema, todayIso, type EventFormValues } from "@/lib/schemas"

interface EventFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** The event to edit; undefined means "create a new event". */
  event?: api.Event
}

/** Starting form values: the event's current values, or empty for a new one. */
function toFormValues(event?: api.Event): EventFormValues {
  return {
    title: event?.title ?? "",
    description: event?.description ?? "",
    event_date: event?.event_date ?? "",
    location: event?.location ?? "",
    max_capacity: event?.max_capacity ?? 50,
  }
}

export function EventFormDialog({ open, onOpenChange, event }: EventFormDialogProps) {
  const isEdit = event !== undefined
  const queryClient = useQueryClient()
  const form = useForm<EventFormValues>({
    resolver: zodResolver(isEdit ? eventUpdateSchema : eventCreateSchema),
    defaultValues: toFormValues(event),
  })
  const { errors } = form.formState

  // Refill the form each time the dialog opens, so it never shows stale input.
  useEffect(() => {
    if (open) form.reset(toFormValues(event))
  }, [open, event, form])

  const mutation = useMutation({
    mutationFn: (values: EventFormValues) => {
      // The API stores "no description" as null, not an empty string.
      const body = { ...values, description: values.description || null }
      return isEdit ? api.updateEvent(event.id, body) : api.createEvent(body)
    },
    onSuccess: (saved) => {
      queryClient.invalidateQueries({ queryKey: ["events"] })
      queryClient.invalidateQueries({ queryKey: ["event", saved.id] })
      toast.success(isEdit ? "Event updated" : "Event created")
      onOpenChange(false)
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit event" : "New event"}</DialogTitle>
          <DialogDescription>
            {isEdit ? "Change the details and save." : "Fill in the details of the event."}
          </DialogDescription>
        </DialogHeader>
        <form id="event-form" onSubmit={form.handleSubmit((values) => mutation.mutate(values))} noValidate>
          <FieldGroup>
            <Field data-invalid={!!errors.title}>
              <FieldLabel htmlFor="title">Title</FieldLabel>
              <Input id="title" {...form.register("title")} />
              <FieldError errors={[errors.title]} />
            </Field>
            <Field data-invalid={!!errors.description}>
              <FieldLabel htmlFor="description">Description (optional)</FieldLabel>
              <Textarea id="description" rows={3} {...form.register("description")} />
              <FieldError errors={[errors.description]} />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field data-invalid={!!errors.event_date}>
                <FieldLabel htmlFor="event_date">Date</FieldLabel>
                <Input
                  id="event_date"
                  type="date"
                  min={isEdit ? undefined : todayIso()}
                  {...form.register("event_date")}
                />
                <FieldError errors={[errors.event_date]} />
              </Field>
              <Field data-invalid={!!errors.max_capacity}>
                <FieldLabel htmlFor="max_capacity">Capacity</FieldLabel>
                <Input
                  id="max_capacity"
                  type="number"
                  min={1}
                  max={10000}
                  {...form.register("max_capacity", { valueAsNumber: true })}
                />
                <FieldError errors={[errors.max_capacity]} />
              </Field>
            </div>
            <Field data-invalid={!!errors.location}>
              <FieldLabel htmlFor="location">Location</FieldLabel>
              <Input id="location" {...form.register("location")} />
              <FieldError errors={[errors.location]} />
            </Field>
          </FieldGroup>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button type="submit" form="event-form" disabled={mutation.isPending}>
            {mutation.isPending ? "Saving..." : isEdit ? "Save changes" : "Create event"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
