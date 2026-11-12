/** URL routes: every page shares the same header layout. */
import { Route, Routes } from "react-router-dom"

import { Layout } from "@/components/Layout"
import { EventDetailPage } from "@/pages/EventDetailPage"
import { EventsPage } from "@/pages/EventsPage"
import { LoginPage } from "@/pages/LoginPage"
import { RegisterPage } from "@/pages/RegisterPage"

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<EventsPage />} />
        <Route path="events/:id" element={<EventDetailPage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
      </Route>
    </Routes>
  )
}
