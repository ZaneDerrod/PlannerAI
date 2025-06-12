/* ---------- src/pages/LandingPage.jsx ---------- */
import Button from "../components/Button"
import { useNavigate } from "react-router-dom"

export default function LandingPage() {
  const nav = useNavigate()
  return (
    <div className="flex h-screen w-screen items-center justify-center bg-gray-900">
      <div className="text-center space-y-6">
        <h1 className="text-4xl font-bold text-white">PlannerAI</h1>
        <p className="text-gray-300">Plan smarter. Build faster.</p>
        <Button onClick={() => nav("/home")}>Enter</Button>
      </div>
    </div>
  )
}