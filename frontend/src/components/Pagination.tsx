/**
 * Previous / Next buttons for a list paged with skip and limit.
 *
 * The API returns a plain list without a total count, so "Next" is enabled
 * only when the current page came back full (there may be more after it).
 */
import { ChevronLeft, ChevronRight } from "lucide-react"

import { Button } from "@/components/ui/button"

interface PaginationProps {
  skip: number
  limit: number
  /** Number of items on the current page. */
  itemCount: number
  onSkipChange: (skip: number) => void
}

export function Pagination({ skip, limit, itemCount, onSkipChange }: PaginationProps) {
  const page = Math.floor(skip / limit) + 1
  const hasPrevious = skip > 0
  const hasNext = itemCount === limit

  // Nothing to page through: hide the controls entirely.
  if (!hasPrevious && !hasNext) return null

  return (
    <div className="flex items-center justify-end gap-2">
      <span className="mr-2 text-sm text-muted-foreground">Page {page}</span>
      <Button
        variant="outline"
        size="sm"
        disabled={!hasPrevious}
        onClick={() => onSkipChange(Math.max(0, skip - limit))}
      >
        <ChevronLeft /> Previous
      </Button>
      <Button variant="outline" size="sm" disabled={!hasNext} onClick={() => onSkipChange(skip + limit)}>
        Next <ChevronRight />
      </Button>
    </div>
  )
}
