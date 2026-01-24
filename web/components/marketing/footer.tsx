import Link from 'next/link'
import { MapPin } from 'lucide-react'

const footerLinks = {
  product: [
    { href: '/features', label: 'Features' },
    { href: '/pricing', label: 'Pricing' },
    { href: '/docs', label: 'Documentation' },
    { href: '/map', label: 'Live Map' },
    { href: '/quickstart', label: 'Quickstart' },
    { href: '/api-reference', label: 'API Reference' },
  ],
  resources: [
    { href: '/use-cases', label: 'Use Cases' },
    { href: '/status', label: 'Status' },
  ],
  compare: [
    { href: '/alternatives/google-maps', label: 'vs Google Maps' },
    { href: '/alternatives/mapbox', label: 'vs Mapbox' },
    { href: '/alternatives/here-maps', label: 'vs HERE Maps' },
    { href: '/alternatives/maptiler', label: 'vs MapTiler' },
  ],
  company: [
    { href: '/about', label: 'About' },
    { href: '/contact', label: 'Contact' },
    { href: '/privacy', label: 'Privacy' },
    { href: '/terms', label: 'Terms' },
  ],
}

export function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-400 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-5 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 text-white">
              <MapPin className="h-6 w-6" />
              <span className="font-bold">Maps for Developers</span>
            </div>
            <p className="mt-4 text-sm">
              Enterprise-grade geospatial data platform.
              Trusted by thousands of developers worldwide.
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="font-semibold text-white mb-4">Product</h4>
            <ul className="space-y-2 text-sm">
              {footerLinks.product.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="hover:text-white transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-semibold text-white mb-4">Resources</h4>
            <ul className="space-y-2 text-sm">
              {footerLinks.resources.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="hover:text-white transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Compare */}
          <div>
            <h4 className="font-semibold text-white mb-4">Compare</h4>
            <ul className="space-y-2 text-sm">
              {footerLinks.compare.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="hover:text-white transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="font-semibold text-white mb-4">Company</h4>
            <ul className="space-y-2 text-sm">
              {footerLinks.company.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="hover:text-white transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-gray-800 text-sm text-center">
          &copy; {new Date().getFullYear()} Maps for Developers. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
