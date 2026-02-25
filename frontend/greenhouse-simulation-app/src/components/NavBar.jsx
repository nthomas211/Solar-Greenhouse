import { Link } from 'react-router-dom'
import './Navbar.css'

function Navbar() {
  return (
    <nav className="navbar">
      <span className="title">Greenhouse Simulator</span>

      <div className="nav-links">
        <Link className="options" to="/">Home</Link>
        <Link className="options" to="/simulation">Simulation</Link>
        <Link className="options" to="/data">Data</Link>
      </div>
    </nav>
  )
}

export default Navbar