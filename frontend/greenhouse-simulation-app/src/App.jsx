import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import Simulation from './pages/Simulation'
import Data from './pages/Data'
import Navbar from './components/NavBar'

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/simulation" element={<Simulation />} />
        <Route path="/data" element={<Data />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App