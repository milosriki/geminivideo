import { Header } from '../components/salient/Header'
import { Hero } from '../components/salient/Hero'
import { PrimaryFeatures } from '../components/salient/primary-features'
import { SecondaryFeatures } from '../components/salient/secondary-features'
import { CallToAction } from '../components/salient/call-to-action'
import { Testimonials, Testimonial } from '../components/radiant/testimonials'
import { Pricing } from '../components/salient/Pricing'
import { Faqs } from '../components/salient/faqs'
import { Map } from '../components/radiant/map'

const faqs = [
    {
        question: 'Does TaxPal handle VAT?',
        answer:
            'Well no, but if you move your company offshore you can probably ignore it.',
    },
    {
        question: 'Can I pay for my subscription via purchase order?',
        answer: 'Absolutely, we are happy to take your money in all forms.',
    },
    {
        question: 'How do I apply for a job at TaxPal?',
        answer:
            'We only hire our customers, so subscribe for a minimum of 6 months and then let’s talk.',
    },
]

export default function LandingPage() {
    return (
        <div className="bg-white">
            <Header />
            <main>
                <Hero />
                <PrimaryFeatures />
                <SecondaryFeatures />
                <CallToAction />
                <div id="testimonials" className="scroll-mt-32">
                    <Testimonials>
                        <Testimonial author={{ name: 'Sheryl Berge', role: 'CEO at Lynch LLC', image: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80' }}>
                            TaxPal is so easy to use I can’t help but wonder if it’s really doing the things the government expects me to do.
                        </Testimonial>
                        <Testimonial author={{ name: 'Leland Kiehn', role: 'Founder of Kiehn and Sons', image: 'https://images.unsplash.com/photo-1519244703995-f4e0f30006d5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80' }}>
                            The best part about TaxPal is every time I pay my employees, my bank balance doesn’t go down like it used to. Looking forward to spending this extra cash when I figure out why my card is being declined.
                        </Testimonial>
                        <Testimonial author={{ name: 'Peter Renolds', role: 'Founder of West Inc', image: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80' }}>
                            I used to have to remit tax to the EU and with TaxPal I somehow don’t have to do that anymore. Nervous to travel there now though.
                        </Testimonial>
                    </Testimonials>
                </div>
                <div className="py-20 bg-slate-50">
                    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                        <div className="mx-auto max-w-2xl md:text-center mb-10">
                            <h2 className="font-display text-3xl tracking-tight text-slate-900 sm:text-4xl">
                                Global Reach
                            </h2>
                            <p className="mt-4 text-lg tracking-tight text-slate-700">
                                See where our clients are located.
                            </p>
                        </div>
                        <Map />
                    </div>
                </div>
                <div id="pricing" className="scroll-mt-32">
                    <Pricing />
                </div>
                <Faqs faqs={faqs} />
            </main>
            <footer className="bg-slate-50 py-16 text-center text-sm text-slate-500">
                <p>Copyright © {new Date().getFullYear()} TaxPal. All rights reserved.</p>
            </footer>
        </div>
    )
}
