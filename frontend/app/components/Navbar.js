'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navbar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const navItems = [
    { name: 'Overview', href: '/' },
    { name: 'Predictions & Forecasts', href: '/predictions' },
    { name: 'Event Timeline', href: '/events' },
    { name: 'Economic Indicators', href: '/analysis' },
    { name: 'Settings', href: '/settings' },
  ];

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  const closeMenu = () => {
    setIsOpen(false);
  };

  return (
    <header className="navbar">
      <div className="container navbar-inner">
        <Link href="/" className="navbar-logo" onClick={closeMenu}>
          <span>⚜</span> GoldSight
        </Link>
        
        <button 
          className={`hamburger ${isOpen ? 'open' : ''}`} 
          onClick={toggleMenu}
          aria-label="Toggle navigation menu"
          aria-expanded={isOpen}
        >
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
        </button>

        <nav className={`navbar-menu ${isOpen ? 'open' : ''}`}>
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`navbar-link ${isActive ? 'active' : ''}`}
                onClick={closeMenu}
              >
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}

