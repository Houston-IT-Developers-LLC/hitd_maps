import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Header } from '@/components/marketing/header'
import { Footer } from '@/components/marketing/footer'
import {
  ArrowRight,
  Terminal,
  Code,
  Smartphone,
  Apple,
  Laptop,
  CheckCircle,
  Copy,
} from 'lucide-react'

export const metadata = {
  title: 'Quickstart - Maps for Developers',
  description: 'Get started with Maps for Developers in minutes. Installation guides and code examples for JavaScript, React, React Native, iOS, and Android.',
}

export default function QuickstartPage() {
  const platforms = [
    {
      icon: Code,
      name: 'JavaScript',
      description: 'Vanilla JS or any framework',
      install: 'npm install @mapsfordevelopers/js',
      code: `import { MapsForDevelopers } from '@mapsfordevelopers/js'

const map = new MapsForDevelopers({
  apiKey: 'YOUR_API_KEY',
  container: 'map',
  center: [-95.37, 29.76],
  zoom: 12,
  layers: ['parcels', 'pois']
})

// Add click handler for parcels
map.on('click', 'parcels', (e) => {
  const parcel = e.features[0]
  console.log('Owner:', parcel.properties.owner)
  console.log('Value:', parcel.properties.assessed_value)
})`,
    },
    {
      icon: Code,
      name: 'React',
      description: 'React 18+ with hooks',
      install: 'npm install @mapsfordevelopers/react',
      code: `import { Map, ParcelLayer, POILayer } from '@mapsfordevelopers/react'

export default function MyMap() {
  const handleParcelClick = (parcel) => {
    console.log('Selected:', parcel.properties)
  }

  return (
    <Map
      apiKey="YOUR_API_KEY"
      center={[-95.37, 29.76]}
      zoom={12}
    >
      <ParcelLayer onClick={handleParcelClick} />
      <POILayer categories={['restaurant', 'hospital']} />
    </Map>
  )
}`,
    },
    {
      icon: Smartphone,
      name: 'React Native',
      description: 'iOS and Android',
      install: 'npm install @mapsfordevelopers/react-native',
      code: `import { MapView, ParcelLayer } from '@mapsfordevelopers/react-native'

export default function App() {
  return (
    <MapView
      apiKey="YOUR_API_KEY"
      initialRegion={{
        latitude: 29.76,
        longitude: -95.37,
        zoom: 12,
      }}
    >
      <ParcelLayer
        onPress={(parcel) => {
          Alert.alert('Parcel', parcel.properties.address)
        }}
      />
    </MapView>
  )
}`,
    },
    {
      icon: Apple,
      name: 'iOS (Swift)',
      description: 'Swift Package Manager',
      install: '.package(url: "https://github.com/mapsfordevelopers/ios-sdk")',
      code: `import MapsForDevelopers

class MapViewController: UIViewController {
    var mapView: MFDMapView!

    override func viewDidLoad() {
        super.viewDidLoad()

        mapView = MFDMapView(frame: view.bounds)
        mapView.apiKey = "YOUR_API_KEY"
        mapView.setCenter(CLLocationCoordinate2D(
            latitude: 29.76,
            longitude: -95.37
        ), zoom: 12)

        mapView.addLayer(.parcels)
        mapView.delegate = self
        view.addSubview(mapView)
    }
}`,
    },
    {
      icon: Smartphone,
      name: 'Android (Kotlin)',
      description: 'Gradle dependency',
      install: 'implementation "com.mapsfordevelopers:android-sdk:1.0.0"',
      code: `class MapActivity : AppCompatActivity() {
    private lateinit var mapView: MFDMapView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        mapView = MFDMapView(this).apply {
            apiKey = "YOUR_API_KEY"
            setCenter(LatLng(29.76, -95.37), zoom = 12)
            addLayer(Layer.PARCELS)

            setOnParcelClickListener { parcel ->
                Toast.makeText(
                    context,
                    "Owner: \${parcel.owner}",
                    Toast.LENGTH_SHORT
                ).show()
            }
        }
        setContentView(mapView)
    }
}`,
    },
    {
      icon: Laptop,
      name: 'Flutter',
      description: 'Cross-platform',
      install: 'flutter pub add mapsfordevelopers',
      code: `import 'package:mapsfordevelopers/mapsfordevelopers.dart';

class MyMap extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MFDMap(
      apiKey: 'YOUR_API_KEY',
      initialCenter: LatLng(29.76, -95.37),
      initialZoom: 12,
      layers: [
        ParcelLayer(
          onTap: (parcel) {
            showDialog(
              context: context,
              builder: (_) => AlertDialog(
                title: Text(parcel.address),
                content: Text('Value: \$\${parcel.assessedValue}'),
              ),
            );
          },
        ),
      ],
    );
  }
}`,
    },
  ]

  const steps = [
    {
      step: 1,
      title: 'Create an account',
      description: 'Sign up for free and get your API key from the dashboard.',
    },
    {
      step: 2,
      title: 'Install the SDK',
      description: 'Add the SDK to your project using your package manager.',
    },
    {
      step: 3,
      title: 'Initialize the map',
      description: 'Create a map instance with your API key and configuration.',
    },
    {
      step: 4,
      title: 'Add data layers',
      description: 'Enable parcels, POIs, terrain, or satellite imagery.',
    },
  ]

  return (
    <div className="min-h-screen">
      <Header />

      {/* Hero */}
      <section className="py-20 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold">
            Quickstart Guide
          </h1>
          <p className="mt-4 text-xl text-muted-foreground max-w-2xl mx-auto">
            Get up and running in minutes. Native SDKs for every platform.
          </p>
          <Button size="lg" className="mt-8" asChild>
            <Link href="/signup">
              Get Your API Key
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </Button>
        </div>
      </section>

      {/* Steps */}
      <section className="py-16 bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            {steps.map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                  {item.step}
                </div>
                <h3 className="font-semibold text-lg mb-2">{item.title}</h3>
                <p className="text-gray-400 text-sm">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Platform SDKs */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold">Choose Your Platform</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Native SDKs with full TypeScript support and comprehensive documentation
            </p>
          </div>

          <div className="space-y-8">
            {platforms.map((platform) => (
              <Card key={platform.name} id={platform.name.toLowerCase().replace(' ', '-')}>
                <CardHeader>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                      <platform.icon className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <CardTitle>{platform.name}</CardTitle>
                      <CardDescription>{platform.description}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Install command */}
                    <div>
                      <div className="text-sm font-medium mb-2 flex items-center gap-2">
                        <Terminal className="h-4 w-4" />
                        Installation
                      </div>
                      <div className="bg-gray-100 rounded-lg p-3 font-mono text-sm flex items-center justify-between">
                        <code>{platform.install}</code>
                      </div>
                    </div>

                    {/* Code example */}
                    <div>
                      <div className="text-sm font-medium mb-2 flex items-center gap-2">
                        <Code className="h-4 w-4" />
                        Quick Example
                      </div>
                      <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                        <pre className="text-sm text-gray-300 font-mono">
                          <code>{platform.code}</code>
                        </pre>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features included */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold">All SDKs Include</h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="flex items-start gap-4">
              <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0" />
              <div>
                <h3 className="font-semibold">TypeScript Definitions</h3>
                <p className="text-muted-foreground text-sm mt-1">Full type safety and autocomplete support</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0" />
              <div>
                <h3 className="font-semibold">Offline Support</h3>
                <p className="text-muted-foreground text-sm mt-1">Download and cache tiles for offline use</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0" />
              <div>
                <h3 className="font-semibold">Custom Styling</h3>
                <p className="text-muted-foreground text-sm mt-1">Full control over map appearance</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0" />
              <div>
                <h3 className="font-semibold">Geocoding Built-in</h3>
                <p className="text-muted-foreground text-sm mt-1">Address search and reverse lookup</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0" />
              <div>
                <h3 className="font-semibold">Event Handling</h3>
                <p className="text-muted-foreground text-sm mt-1">Click, hover, and gesture callbacks</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0" />
              <div>
                <h3 className="font-semibold">Performance Optimized</h3>
                <p className="text-muted-foreground text-sm mt-1">Lazy loading and efficient rendering</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold">Start building today</h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Free tier includes 1,000 requests per day. No credit card required.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Button size="lg" asChild>
              <Link href="/signup">
                Create Free Account
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/api-reference">API Reference</Link>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
