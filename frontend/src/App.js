import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { SearchProvider } from './services/SearchContext';
import { CrawlerProvider } from './services/CrawlerContext';
import Header from './components/Header';
import SearchPage from './pages/SearchPage';
import DashboardPage from './pages/DashboardPage';
import './styles/App.css';

function App() {
  return (
    <SearchProvider>
      <CrawlerProvider>
        <Router>
          <div className="App">
            <Header />
            <main className="main-content">
              <Routes>
                <Route path="/" element={<SearchPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
              </Routes>
            </main>
          </div>
        </Router>
      </CrawlerProvider>
    </SearchProvider>
  );
}

export default App;
