import { Link, NavLink } from 'react-router-dom'

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link to="/" className="site-header__brand">
        Problem Intelligence OS
      </Link>
      <nav className="site-header__nav" aria-label="Main">
        <NavLink to="/" end>
          Search
        </NavLink>
        <NavLink to="/domains">Domains</NavLink>
      </nav>
    </header>
  )
}
