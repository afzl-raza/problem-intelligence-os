import { Route, Routes } from 'react-router-dom'
import './App.css'
import { SiteHeader } from './components/SiteHeader'
import { CompanyPage } from './pages/CompanyPage'
import { DomainPage } from './pages/DomainPage'
import { DomainsPage } from './pages/DomainsPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { ProblemPage } from './pages/ProblemPage'
import { SearchPage } from './pages/SearchPage'

function App() {
  return (
    <div className="app">
      <SiteHeader />
      <main>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/domains" element={<DomainsPage />} />
          <Route path="/domains/:slug" element={<DomainPage />} />
          <Route path="/problems/:id" element={<ProblemPage />} />
          <Route path="/companies/:id" element={<CompanyPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
