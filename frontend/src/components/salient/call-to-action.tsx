import { Button } from './Button'
import { Container } from './Container'

export function CallToAction() {
    return (
        <section id="get-started-today" className="relative overflow-hidden bg-blue-600 py-32">
            <div className="absolute top-1/2 left-1/2 -translate-x-[50%] -translate-y-[50%]">
                <svg
                    viewBox="0 0 1024 1024"
                    className="h-[64rem] w-[64rem] [mask-image:radial-gradient(closest-side,white,transparent)]"
                    aria-hidden="true"
                >
                    <circle cx="512" cy="512" r="512" fill="url(#827591b1-ce8c-4110-b064-7cb85a0b1217)" fillOpacity="0.7" />
                    <defs>
                        <radialGradient id="827591b1-ce8c-4110-b064-7cb85a0b1217">
                            <stop stopColor="#7775D6" />
                            <stop offset="1" stopColor="#E935C1" />
                        </radialGradient>
                    </defs>
                </svg>
            </div>
            <Container className="relative">
                <div className="mx-auto max-w-lg text-center">
                    <h2 className="font-display text-3xl tracking-tight text-white sm:text-4xl">
                        Get started today
                    </h2>
                    <p className="mt-4 text-lg tracking-tight text-white">
                        It’s time to take control of your video marketing. Buy the software once and use it forever.
                    </p>
                    <Button href="/register" color="white" className="mt-10">
                        Get 6 months free
                    </Button>
                </div>
            </Container>
        </section>
    )
}
