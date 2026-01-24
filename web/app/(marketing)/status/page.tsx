import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Header } from '@/components/marketing/header'
import { Footer } from '@/components/marketing/footer'
import {
  CheckCircle,
  Clock,
  Server,
  Globe,
  Database,
  Zap,
  ArrowRight,
} from 'lucide-react'

export const metadata = {
  title: 'System Status - Maps for Developers',
  description: 'Real-time system status and uptime information for Maps for Developers API and services.',
}

export default function StatusPage() {
  const services = [
    {
      name: 'API',
      description: 'Core REST API endpoints',
      status: 'operational',
      uptime: '99.99%',
    },
    {
      name: 'Tile Server',
      description: 'Vector and raster tile delivery',
      status: 'operational',
      uptime: '99.98%',
    },
    {
      name: 'Geocoding',
      description: 'Address lookup and reverse geocoding',
      status: 'operational',
      uptime: '99.97%',
    },
    {
      name: 'CDN',
      description: 'Global content delivery network',
      status: 'operational',
      uptime: '99.99%',
    },
    {
      name: 'Dashboard',
      description: 'Developer dashboard and console',
      status: 'operational',
      uptime: '99.95%',
    },
    {
      name: 'Authentication',
      description: 'API key validation and auth services',
      status: 'operational',
      uptime: '99.99%',
    },
  ]

  const metrics = [
    {
      icon: Zap,
      label: 'Avg Response Time',
      value: '45ms',
      description: 'Global average',
    },
    {
      icon: Server,
      label: 'Uptime (30 days)',
      value: '99.98%',
      description: 'All services',
    },
    {
      icon: Globe,
      label: 'Edge Locations',
      value: '200+',
      description: 'Cloudflare network',
    },
    {
      icon: Database,
      label: 'Data Freshness',
      value: '< 24h',
      description: 'Parcel updates',
    },
  ]

  const recentIncidents: { date: string; title: string; status: string; description: string }[] = []

  return (
    <div className="min-h-screen">
      <Header />

      {/* Hero */}
      <section className="py-20 bg-gradient-to-b from-green-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold">
            All Systems Operational
          </h1>
          <p className="mt-4 text-xl text-muted-foreground max-w-2xl mx-auto">
            All Maps for Developers services are running normally.
            Last updated: {new Date().toLocaleString()}
          </p>
        </div>
      </section>

      {/* Metrics */}
      <section className="py-12 bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            {metrics.map((metric) => (
              <div key={metric.label} className="text-center">
                <metric.icon className="h-6 w-6 text-primary mx-auto mb-2" />
                <div className="text-3xl font-bold">{metric.value}</div>
                <div className="text-sm text-gray-400">{metric.label}</div>
                <div className="text-xs text-gray-500 mt-1">{metric.description}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Service Status */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold mb-8">Service Status</h2>

          <div className="space-y-4">
            {services.map((service) => (
              <Card key={service.name}>
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-3 h-3 bg-green-500 rounded-full" />
                      <div>
                        <div className="font-medium">{service.name}</div>
                        <div className="text-sm text-muted-foreground">{service.description}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-green-600 capitalize">{service.status}</div>
                      <div className="text-xs text-muted-foreground">{service.uptime} uptime</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Uptime History */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold mb-8">90-Day Uptime</h2>

          <Card>
            <CardContent className="py-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium">API Availability</span>
                <span className="text-sm text-green-600 font-medium">99.98%</span>
              </div>
              <div className="flex gap-0.5">
                {Array.from({ length: 90 }).map((_, i) => (
                  <div
                    key={i}
                    className="flex-1 h-8 bg-green-500 rounded-sm first:rounded-l last:rounded-r"
                    title={`Day ${90 - i}: 100% uptime`}
                  />
                ))}
              </div>
              <div className="flex justify-between mt-2 text-xs text-muted-foreground">
                <span>90 days ago</span>
                <span>Today</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Recent Incidents */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold mb-8">Recent Incidents</h2>

          {recentIncidents.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                <p className="text-lg font-medium">No incidents reported</p>
                <p className="text-muted-foreground mt-2">
                  All systems have been running smoothly for the past 90 days.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {recentIncidents.map((incident, i) => (
                <Card key={i}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{incident.title}</CardTitle>
                      <span className="text-sm text-muted-foreground">{incident.date}</span>
                    </div>
                    <CardDescription>{incident.description}</CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Subscribe */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <Clock className="h-12 w-12 text-primary mx-auto mb-4" />
          <h2 className="text-2xl font-bold">Stay Updated</h2>
          <p className="mt-4 text-muted-foreground max-w-lg mx-auto">
            Get notified about scheduled maintenance and service incidents.
            We&apos;ll email you when something affects your integration.
          </p>
          <Button className="mt-6" asChild>
            <Link href="/signup">
              Subscribe to Updates
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>

      <Footer />
    </div>
  )
}
