import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'Maps for Developers - The Maps API Built for Developers',
    template: '%s | Maps for Developers',
  },
  description: 'The most developer-friendly maps API. 150M+ property parcels, 17M+ POIs, 3D terrain, satellite imagery, and offline support. No surprise bills, zero egress fees.',
  keywords: ['maps api', 'developer maps', 'property parcels', 'google maps alternative', 'mapbox alternative', 'offline maps'],
  authors: [{ name: 'Maps for Developers' }],
  creator: 'Maps for Developers',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://www.mapsfordevelopers.com',
    siteName: 'Maps for Developers',
    title: 'Maps for Developers - The Maps API Built for Developers',
    description: 'The most developer-friendly maps API. 150M+ property parcels, 17M+ POIs, 3D terrain, satellite imagery, and offline support.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Maps for Developers',
    description: 'The most developer-friendly maps API for modern applications.',
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
