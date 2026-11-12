/** Entry point: wires up data fetching, routing, login state and toasts. */
import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { BrowserRouter } from "react-router-dom"
import { toast } from "sonner"

import App from "@/App"
import { Toaster } from "@/components/ui/sonner"
import { AuthProvider } from "@/context/AuthContext"
import { ApiError } from "@/lib/api"
import "@/index.css"

/** Show any failed request's message (the API's `detail`) in a toast. */
function showError(error: Error) {
  toast.error(error.message)
}

const queryClient = new QueryClient({
  // One place that turns every API error into a toast, for reads and writes.
  queryCache: new QueryCache({ onError: showError }),
  mutationCache: new MutationCache({ onError: showError }),
  defaultOptions: {
    queries: {
      // Retrying a 4xx (404, 401, 422) cannot succeed, so only retry server or network errors.
      retry: (failureCount, error) =>
        !(error instanceof ApiError && error.status >= 400 && error.status < 500) &&
        failureCount < 2,
      refetchOnWindowFocus: false,
    },
  },
})

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <App />
          <Toaster theme="light" position="top-right" richColors />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
