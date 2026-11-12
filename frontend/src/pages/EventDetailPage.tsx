/**
 * One event: its details, seats left, the Register / Cancel controls and the
 * paged list of registrations (attendees are only visible when logged in,
 * because the API requires a token for that list).
 */
import { useQuery } from "@tanstack/react-query"
import { ArrowLeft, CalendarDays, MapPin, Users } from "lucide-react"
import { useState } from "react"
import { Link, useParams } from "react-router-dom"

import { Pagination } from "@/components/Pagination"
import { RegistrationForm } from "@/components/RegistrationForm"
import { SeatsBadge } from "@/components/SeatsBadge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useAuth } from "@/context/AuthContext"
import { useCancelRegistration } from "@/hooks/useRegistrationActions"
import * as api from "@/lib/api"
import { formatDate, formatDateTime } from "@/lib/format"

const PAGE_SIZE = 10

export function EventDetailPage() {
  const eventId = Number(useParams().id)
  const { user, isLoggedIn } = useAuth()
  const [skip, setSkip] = useState(0)
  const cancelMutation = useCancelRegistration(eventId)

  const eventQuery = useQuery({
    queryKey: ["event", eventId],
    queryFn: () => api.getEvent(eventId),
  })
  const registrationsQuery = useQuery({
    queryKey: ["registrations", eventId, skip],
    queryFn: () => api.listRegistrations(eventId, skip, PAGE_SIZE),
    enabled: isLoggedIn && eventQuery.isSuccess,
  })
  const registrations = registrationsQuery.data ?? []
  // RegistrationRead has no user id, so the user's own row is found by email.
  const myRegistration = registrations.find((registration) => registration.user.email === user?.email)

  if (eventQuery.isPending) {
    return <div className="h-48 animate-pulse rounded-xl bg-muted" aria-label="Loading event" />
  }
  if (eventQuery.isError) {
    const notFound = eventQuery.error instanceof api.ApiError && eventQuery.error.status === 404
    return (
      <Card className="mx-auto max-w-md text-center">
        <CardHeader>
          <CardTitle>{notFound ? "Event not found" : "Could not load this event"}</CardTitle>
          <CardDescription>{eventQuery.error.message}</CardDescription>
        </CardHeader>
        <CardContent>
          <BackButton />
        </CardContent>
      </Card>
    )
  }

  const event = eventQuery.data

  return (
    <div className="space-y-6">
      <BackButton />

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-2">
            <CardTitle className="text-2xl">{event.title}</CardTitle>
            <SeatsBadge seatsLeft={event.seats_left} capacity={event.max_capacity} />
          </div>
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <CalendarDays className="size-4" /> {formatDate(event.event_date)}
            </span>
            <span className="flex items-center gap-1.5">
              <MapPin className="size-4" /> {event.location}
            </span>
            <span className="flex items-center gap-1.5">
              <Users className="size-4" /> {event.registered_count} registered
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <p className="whitespace-pre-line">{event.description || "No description."}</p>
          {isLoggedIn ? (
            <RegistrationForm eventId={event.id} myRegistration={myRegistration} />
          ) : (
            <p className="text-sm text-muted-foreground">
              <Link to="/login" className="text-primary underline-offset-4 hover:underline">
                Log in
              </Link>{" "}
              to register and to see who is coming.
            </p>
          )}
        </CardContent>
      </Card>

      {isLoggedIn && (
        <Card>
          <CardHeader>
            <CardTitle>Registrations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 px-0">
            {registrationsQuery.isPending ? (
              <div className="space-y-3 px-4">
                {Array.from({ length: 3 }, (_, index) => (
                  <div key={index} className="h-8 animate-pulse rounded-md bg-muted" />
                ))}
              </div>
            ) : registrations.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-muted-foreground">
                Nobody has registered yet.
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="pl-4">Name</TableHead>
                    <TableHead className="hidden sm:table-cell">Email</TableHead>
                    <TableHead className="hidden md:table-cell">Registered</TableHead>
                    <TableHead className="pr-4 text-right" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {registrations.map((registration) => (
                    <TableRow key={registration.id}>
                      <TableCell className="pl-4 font-medium">{registration.user.full_name}</TableCell>
                      <TableCell className="hidden sm:table-cell">{registration.user.email}</TableCell>
                      <TableCell className="hidden md:table-cell">
                        {formatDateTime(registration.registered_at)}
                      </TableCell>
                      <TableCell className="pr-4 text-right">
                        {/* The API only lets users cancel their own registration. */}
                        {registration.id === myRegistration?.id && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive"
                            disabled={cancelMutation.isPending}
                            onClick={() => cancelMutation.mutate(registration.id)}
                          >
                            Cancel
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
            <div className="px-4">
              <Pagination skip={skip} limit={PAGE_SIZE} itemCount={registrations.length} onSkipChange={setSkip} />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

/** Link back to the events list. */
function BackButton() {
  return (
    <Button variant="ghost" size="sm" asChild>
      <Link to="/">
        <ArrowLeft /> All events
      </Link>
    </Button>
  )
}
