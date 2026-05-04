import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "The rules of using Vaktram.",
};

export default function TermsPage() {
  return (
    <main className="bg-white py-20">
      <article className="container-tight prose prose-slate max-w-3xl">
        <p className="eyebrow">Legal</p>
        <h1 className="display mt-4 text-4xl sm:text-5xl">Terms of Service</h1>
        <p className="mt-3 text-sm text-slate-500">Last updated: 2026-05-04</p>

        <Section title="1. Acceptance">
          By creating an account or using Vaktram, you agree to these Terms.
          If you're using Vaktram on behalf of an organisation, you confirm
          you have authority to bind that organisation.
        </Section>

        <Section title="2. Your account">
          You're responsible for all activity under your account. Keep your
          password secure and notify us immediately of any unauthorised use.
        </Section>

        <Section title="3. Acceptable use">
          <ul>
            <li>
              Don't record meetings without legal consent under the
              applicable jurisdiction.
            </li>
            <li>
              Don't use Vaktram to facilitate harassment, surveillance
              without consent, or any illegal activity.
            </li>
            <li>
              Don't reverse-engineer, scrape, or interfere with the platform
              beyond the normal use of our APIs.
            </li>
          </ul>
        </Section>

        <Section title="4. Bring your own model">
          You bring an LLM API key. You're responsible for fees charged by
          your provider, and for compliance with their terms. We pass your
          requests through; we do not bill or proxy your usage.
        </Section>

        <Section title="5. Plans and payment">
          Free plans are subject to monthly meeting caps. Paid plans renew
          monthly or annually. We bill in advance; refunds are pro-rated for
          downgrades during a billing cycle.
        </Section>

        <Section title="6. Termination">
          You can cancel any time from Settings → Billing. We may suspend
          accounts that breach these Terms; we'll provide notice and a chance
          to remedy when reasonable.
        </Section>

        <Section title="7. Warranty disclaimer">
          The service is provided "as is" without warranty of any kind. AI
          outputs may be incorrect — always verify important decisions
          against the underlying transcript.
        </Section>

        <Section title="8. Liability">
          To the maximum extent permitted by law, our total liability for any
          claim related to the service is limited to the fees you paid us in
          the 12 months preceding the claim.
        </Section>

        <Section title="9. Governing law">
          These Terms are governed by the laws of India. Disputes are
          resolved in the courts of Bengaluru.
        </Section>

        <Section title="10. Contact">
          Questions: legal@vaktram.com.
        </Section>
      </article>
    </main>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-10">
      <h2 className="text-xl font-semibold tracking-tight text-slate-900">
        {title}
      </h2>
      <div className="mt-3 space-y-3 text-[15px] leading-relaxed text-slate-700 [&_a]:text-slate-900 [&_li]:my-1 [&_ul]:ml-5 [&_ul]:list-disc">
        {children}
      </div>
    </section>
  );
}
