/**
 * Events list: search by title, filter by date, page through results and,
 * when logged in, create, edit and delete events.
 *
 * Filters live in the URL (?title=&date=&skip=) so a filtered page can be
 * reloaded or shared and the browser's Back button works.
 */
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { format, parseISO } from "date-fns"
import { CalendarIcon, CalendarX2, Pencil, Plus, Search, Trash2, X } from "lucide-react"
import { useEffect, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { toast } from "sonner"

import { ConfirmDeleteDialog } from "@/components/ConfirmDeleteDialog"
import { EventFormDialog } from "@/components/EventFormDialog"
import { Pagination } from "@/components/Pagination"
import { SeatsBadge } from "@/components/SeatsBadge"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useAuth } from "@/context/AuthContext"
import * as api from "@/lib/api"
import { formatDate } from "@/lib/format"

const PAGE_SIZE = 10

/** The dialog currently open on this page, if any. */
type DialogState =
  | { kind: "none" }
  | { kind: "create" }
  | { kind: "edit"; event: api.Event }
  | { kind: "delete"; event: api.Event }

export function EventsPage() {
  const { isLoggedIn } = useAuth()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const title = searchParams.get("title") ?? ""
  const date = searchParams.get("date") ?? ""
  const skip = Number(searchParams.get("skip") ?? 0)
  const [dialog, setDialog] = useState<DialogState>({ kind: "none" })
  const [titleInput, setTitleInput] = useState(title)

  /** Change some URL filters; any filter change goes back to the first page. */
  function updateParams(changes: Record<string, string>) {
    const next = new URLSearchParams(searchParams)
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value)
      else next.delete(key)
    }
    if (!("skip" in changes)) next.delete("skip")
    setSearchParams(next)
  }

  // Wait until typing pauses for 300 ms before searching, instead of
  // sending a request on every keystroke.
  useEffect(() => {
    const timer = setTimeout(() => {
      if (titleInput.trim() !== title) updateParams({ title: titleInput.trim() })
    }, 300)
    return () => clearTimeout(timer)
    // updateParams changes every render; only typing should restart the timer.
    // oxlint-disable-next-line react/exhaustive-deps
  }, [titleInput, title])

  const eventsQuery = useQuery({
    queryKey: ["events", { skip, title, date }],
    queryFn: () => api.listEvents({ skip, limit: PAGE_SIZE, title, date }),
    // Keep showing the current page while the next one loads, so the table doesn't flash.
    placeholderData: keepPreviousData,
  })
  const events = eventsQuery.data ?? []

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteEvent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events"] })
      toast.success("Event deleted")
      setDialog({ kind: "none" })
    },
  })

  const hasFilters = title !== "" || date !== ""

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Events</h1>
          <p className="text-sm text-muted-foreground">Upcoming Acme Corp events.</p>
        </div>
        {isLoggedIn && (
          <Button onClick={() => setDialog({ kind: "create" })}>
            <Plus /> New event
          </Button>
        )}
      </div>

      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by title"
            className="pl-8"
            value={titleInput}
            onChange={(event) => setTitleInput(event.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="flex-1 justify-start font-normal sm:w-48">
                <CalendarIcon />
                {date ? formatDate(date) : <span className="text-muted-foreground">Any date</span>}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="end">
              <Calendar
                mode="single"
                selected={date ? parseISO(date) : undefined}
                onSelect={(day) => updateParams({ date: day ? format(day, "yyyy-MM-dd") : "" })}
              />
            </PopoverContent>
          </Popover>
          {hasFilters && (
            <Button
              variant="ghost"
              onClick={() => {
                setTitleInput("")
                updateParams({ title: "", date: "" })
              }}
            >
              <X /> Clear
            </Button>
          )}
        </div>
      </div>

      <Card className="py-0">
        <CardContent className="px-0">
          {eventsQuery.isPending ? (
            <LoadingRows />
          ) : events.length === 0 ? (
            <EmptyState filtered={hasFilters} isLoggedIn={isLoggedIn} />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-4">Event</TableHead>
                  <TableHead className="hidden sm:table-cell">Date</TableHead>
                  <TableHead className="hidden md:table-cell">Location</TableHead>
                  <TableHead>Seats</TableHead>
                  {isLoggedIn && <TableHead className="pr-4 text-right">Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {events.map((event) => (
                  <TableRow key={event.id}>
                    <TableCell className="pl-4">
                      <Link to={`/events/${event.id}`} className="font-medium hover:text-primary hover:underline">
                        {event.title}
                      </Link>
                      {/* On small screens the date column is hidden, so show it here instead. */}
                      <div className="text-xs text-muted-foreground sm:hidden">{formatDate(event.event_date)}</div>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell">{formatDate(event.event_date)}</TableCell>
                    <TableCell className="hidden md:table-cell">{event.location}</TableCell>
                    <TableCell>
                      <SeatsBadge seatsLeft={event.seats_left} capacity={event.max_capacity} />
                    </TableCell>
                    {isLoggedIn && (
                      <TableCell className="pr-4 text-right">
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label={`Edit ${event.title}`}
                          onClick={() => setDialog({ kind: "edit", event })}
                        >
                          <Pencil />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label={`Delete ${event.title}`}
                          onClick={() => setDialog({ kind: "delete", event })}
                        >
                          <Trash2 className="text-destructive" />
                        </Button>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Pagination
        skip={skip}
        limit={PAGE_SIZE}
        itemCount={events.length}
        onSkipChange={(nextSkip) => updateParams({ skip: nextSkip ? String(nextSkip) : "" })}
      />

      {/* A new key per event remounts the form, so create and edit never share state. */}
      <EventFormDialog
        key={dialog.kind === "edit" ? dialog.event.id : "new"}
        open={dialog.kind === "create" || dialog.kind === "edit"}
        onOpenChange={(open) => !open && setDialog({ kind: "none" })}
        event={dialog.kind === "edit" ? dialog.event : undefined}
      />
      <ConfirmDeleteDialog
        open={dialog.kind === "delete"}
        onOpenChange={(open) => !open && setDialog({ kind: "none" })}
        title="Delete this event?"
        description={
          dialog.kind === "delete"
            ? `"${dialog.event.title}" and all its registrations will be removed. This cannot be undone.`
            : ""
        }
        isPending={deleteMutation.isPending}
        onConfirm={() => dialog.kind === "delete" && deleteMutation.mutate(dialog.event.id)}
      />
    </div>
  )
}

/** Grey placeholder rows shown while the first page loads. */
function LoadingRows() {
  return (
    <div className="space-y-3 p-4" aria-label="Loading events">
      {Array.from({ length: 5 }, (_, index) => (
        <div key={index} className="h-8 animate-pulse rounded-md bg-muted" />
      ))}
    </div>
  )
}

/** Message shown when there are no events to list. */
function EmptyState({ filtered, isLoggedIn }: { filtered: boolean; isLoggedIn: boolean }) {
  return (
    <div className="flex flex-col items-center gap-2 px-4 py-12 text-center">
      <CalendarX2 className="size-8 text-muted-foreground" />
      <p className="font-medium">{filtered ? "No events match your filters" : "No events yet"}</p>
      <p className="text-sm text-muted-foreground">
        {filtered
          ? "Try a different title or date."
          : isLoggedIn
            ? "Create the first one with New event."
            : "Log in to create the first one."}
      </p>
    </div>
  )
}
