/** Badge showing how many seats an event has left; red once it is full. */
import { Badge } from "@/components/ui/badge"

export function SeatsBadge({ seatsLeft, capacity }: { seatsLeft: number; capacity: number }) {
  if (seatsLeft <= 0) return <Badge variant="destructive">Full</Badge>
  return (
    <Badge variant="secondary">
      {seatsLeft} of {capacity} seats left
    </Badge>
  )
}
