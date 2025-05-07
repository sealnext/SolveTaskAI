import React from 'react';
import { Link } from 'react-router';
import { ThemeToggle } from '~/components/theme-toggle';

export function meta() {
  return [
    { title: "Terms of Service | SEALNEXT" },
    { name: "description", content: "Terms of Service for SEALNEXT" },
  ];
}

export default function Terms() {
  return (
    <div className="flex min-h-svh flex-col bg-muted p-6 md:p-10">
      <div className="absolute top-3 right-6">
        <ThemeToggle />
      </div>

      <div className="container mx-auto max-w-4xl">
        <div className="mb-8 flex justify-center items-center">
					<Link to="/login">
						<img
							src="https://cdn.sealnext.com/logo-full.svg"
							alt="SEALNEXT"
							className="h-10 pointer-events-none dark:invert"
						/>
					</Link>
        </div>

        <div className="bg-card p-8 rounded-lg shadow-sm">
          <h1 className="text-3xl font-bold mb-6">Terms of Service</h1>

          <p className="text-muted-foreground mb-6">Last updated: {new Date().toLocaleDateString()}</p>

          <div className="space-y-6 text-sm">
            <section>
              <h2 className="text-xl font-semibold mb-3">1. Agreement to Terms</h2>
              <p>
                Welcome to SEALNEXT. These Terms of Service (&ldquo;Terms&rdquo;) govern your access to and use of the SEALNEXT application and services (&ldquo;Service&rdquo;) provided by SEALNEXT SRL (&ldquo;Company&rdquo;, &ldquo;we&rdquo;, &ldquo;us&rdquo;, or &ldquo;our&rdquo;). By accessing or using our Service, you agree to be bound by these Terms. If you disagree with any part of the Terms, you may not access the Service.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">2. Description of Service</h2>
              <p>
                SEALNEXT is an AI agent for ticketing systems, currently supporting Jira. Our Service allows you to connect your Jira account by providing an API key, which enables us to fetch, process, and analyze your ticketing data to provide you with insights and answers to your queries.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">3. Account Registration and Terms</h2>
              <p>
                When you register for an account, you must provide accurate and complete information. You are responsible for maintaining the security of your account and API keys. The Company reserves the absolute right to terminate, suspend, or delete your account at any time, for any reason, without prior notice or explanation, and without any liability to you or any third party. You acknowledge and agree that the Company has no obligation to maintain or provide you with access to your account or data after termination.
              </p>
              <p className="mt-2">
                You expressly acknowledge and agree that your account and all related data are the exclusive property of the Company. The Company grants you a limited, revocable license to use the account and Service in accordance with these Terms. This license may be revoked at any time at the sole discretion of the Company.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">4. Data Collection and Use</h2>
              <p>
                By using our Service, you authorize us to collect, process, and store data from your connected ticketing system. This data is primarily used to provide you with the core functionality of the Service. We may also use your email address for marketing communications about our current and future products and services. You have the right to opt out of such communications at any time, although this does not affect our right to contact you regarding your account or changes to these Terms. For more detailed information about how we collect, use, and protect your data, please refer to our Privacy Policy.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">5. Third-Party Services</h2>
              <p>
                Our Service integrates with third-party applications and services, including but not limited to OpenAI and Google Gemini, for functionality such as RAG embeddings vectors and large language model processing. Your use of the Service constitutes consent to the sharing of certain data with these third-party services as necessary for the functioning of our Service. We are not responsible for the privacy practices or content of these third-party services, and your use of such services is at your own risk.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">6. Disclaimer of Warranties</h2>
              <p>
                The Service is provided &ldquo;as is&rdquo; and &ldquo;as available&rdquo; without warranties of any kind, either express or implied. To the fullest extent permissible under applicable law, the Company disclaims all warranties, express or implied, including but not limited to implied warranties of merchantability, fitness for a particular purpose, and non-infringement.
              </p>
              <p className="mt-2">
                The Company does not warrant that the Service will be uninterrupted or error-free, that defects will be corrected, or that the Service or the servers that make it available are free of viruses or other harmful components. The Company does not warrant or make any representations regarding the use or the results of the use of the Service in terms of their correctness, accuracy, reliability, or otherwise.
              </p>
              <p className="mt-2">
                The Company makes no guarantees regarding the availability or uptime of the Service. The Service may be temporarily or permanently unavailable for maintenance, updates, or for any other reason, at the sole discretion of the Company, without notice or liability to users. You acknowledge and agree that the Company has no obligation to maintain any particular level of uptime or availability for the Service.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">7. Limitation of Liability</h2>
              <p>
                To the maximum extent permitted by law, the Company shall not be liable for any indirect, incidental, special, consequential, or punitive damages, or any loss of profits or revenues, whether incurred directly or indirectly, or any loss of data, use, goodwill, or other intangible losses, resulting from:
              </p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li>Your access to or use of or inability to access or use the Service;</li>
                <li>Any conduct or content of any third party on the Service;</li>
                <li>Any content obtained from the Service;</li>
                <li>Unauthorized access, use, or alteration of your transmissions or content;</li>
                <li>Data breaches or security incidents, including those affecting your API keys or other confidential information;</li>
                <li>Any decision made or action taken by you in reliance on the output, recommendations, or suggestions provided by the Service;</li>
                <li>Any errors, mistakes, inaccuracies, or omissions in the Service.</li>
              </ul>
              <p className="mt-2">
                In no event shall the Company&apos;s total liability to you for all claims exceed the amount paid by you, if any, for accessing the Service during the twelve (12) months prior to such claim. The limitations in this section shall apply even if the Company has been advised of the possibility of such damages.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">8. Data Security</h2>
              <p>
                While we implement reasonable security measures to protect your data, we cannot guarantee its absolute security. You acknowledge that you provide your data, including API keys, at your own risk. The Company is not liable for any breaches of security or unauthorized access to your data, regardless of our adherence to reasonable security standards. You agree to indemnify and hold harmless the Company from any claims, damages, or expenses arising from the unauthorized use of your API keys or other credentials.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">9. User Data and GDPR Compliance</h2>
              <p>
                In accordance with the General Data Protection Regulation (&ldquo;GDPR&rdquo;) and other applicable data protection laws, you have certain rights regarding your personal data:
              </p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li>Right to access: You can request copies of your personal data.</li>
                <li>Right to rectification: You can request correction of inaccurate data.</li>
                <li>Right to erasure: You can request deletion of your personal data.</li>
                <li>Right to restrict processing: You can request the restriction of processing under certain conditions.</li>
                <li>Right to data portability: You can request transfer of your data to another controller.</li>
                <li>Right to object: You can object to the processing of your personal data.</li>
              </ul>
              <p className="mt-2">
                To exercise any of these rights, please contact us at support@sealnext.com. We will respond to your request within the timeframe required by applicable law. We may require additional verification of your identity before fulfilling certain requests. Please note that some information may be retained for legal or administrative purposes, or to comply with our legal obligations.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">10. International Users</h2>
              <p>
                If you access the Service from a region outside the European Union, you acknowledge and agree that your information may be processed in countries (including Romania) where laws regarding processing of personal information may be less stringent than the laws in your country. By providing your data, you consent to this transfer. Users in the United States acknowledge that we comply with applicable provisions of the California Consumer Privacy Act (CCPA) and other state laws. Users in Canada acknowledge that we adhere to the Personal Information Protection and Electronic Documents Act (PIPEDA) principles. Users in Australia acknowledge our compliance with the Australian Privacy Principles (APPs) under the Privacy Act 1988. Users in other jurisdictions acknowledge that by using the Service, they do so at their own risk and are responsible for compliance with local laws.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">11. Indemnification</h2>
              <p>
                You agree to defend, indemnify, and hold harmless the Company, its affiliates, licensors, and service providers, and its and their respective officers, directors, employees, contractors, agents, licensors, suppliers, successors, and assigns from and against any claims, liabilities, damages, judgments, awards, losses, costs, expenses, or fees (including reasonable attorneys&apos; fees) arising out of or relating to your violation of these Terms or your use of the Service, including, but not limited to, your submissions, any use of the Service&apos;s content, services, and products other than as expressly authorized in these Terms, or your use of any information obtained from the Service.
              </p>
              <p className="mt-2">
                By using the Service, you agree to release, discharge, and hold harmless the Company from any and all claims, demands, damages, liabilities, and causes of action related to your use of the Service, regardless of the form of action or legal theory under which such liability may be asserted. This waiver applies to the maximum extent permitted by applicable law in your jurisdiction.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">12. Arbitration and Class Action Waiver</h2>
              <p>
                Any dispute arising from these Terms or your use of the Service shall be resolved through binding arbitration, rather than in court, except that you may assert claims in small claims court if your claims qualify. The arbitration will be conducted by the Romanian Court of International Commercial Arbitration under its rules. The Company and you each waive the right to a trial by jury or to participate in a class action. This provision does not apply to EU consumers where prohibited by EU consumer protection law.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">13. Changes to Terms and Service</h2>
              <p>
                The Company reserves the right to modify or replace these Terms at any time at its sole discretion. It is your responsibility to review these Terms periodically for changes. Your continued use of the Service following the posting of any changes constitutes acceptance of those changes. If you do not agree to the new terms, you are no longer authorized to use the Service.
              </p>
              <p className="mt-2">
                Additionally, the Company reserves the right to modify, update, or discontinue, temporarily or permanently, the Service (or any part thereof) at any time without notice. The Company may release new features, functionality, or versions of the Service at any time without prior notification. You agree that the Company shall not be liable to you or to any third party for any modification, suspension, or discontinuance of the Service or any part thereof.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">14. Governing Law</h2>
              <p>
                These Terms shall be governed by and construed in accordance with the laws of Romania and, where applicable, the European Union, without regard to its conflict of law provisions. For EU consumers, this does not deprive you of the protection afforded by provisions that cannot be derogated from by agreement under the law of your country of residence. Any disputes arising under these Terms shall be subject to the exclusive jurisdiction of the courts located in Romania.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">15. Severability</h2>
              <p>
                If any provision of these Terms is held to be unenforceable or invalid, such provision will be changed and interpreted to accomplish the objectives of such provision to the greatest extent possible under applicable law and the remaining provisions will continue in full force and effect.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">16. Payment and Refund Policy</h2>
              <p>
                All fees and charges for paid services are non-refundable under any circumstances. By making a payment for the Service, you acknowledge and agree that the Company is not required to provide a refund for any reason, including but not limited to termination of your account, dissatisfaction with the Service, or any other reason. The Company may, at its sole discretion, offer refunds or credits in exceptional circumstances, but such actions shall not create an obligation to do so in the future.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">17. Complete Agreement</h2>
              <p>
                These Terms, together with the Privacy Policy and any other legal notices published by the Company, shall constitute the entire agreement between you and the Company concerning the Service. By using the Service, you unconditionally consent to all terms herein and affirm that you have read, understood, and agree to be bound by each provision of these Terms, even if any individual provision may be deemed unenforceable.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">18. Contact Information</h2>
              <p>
                If you have any questions about these Terms, please contact us at support@sealnext.com.
              </p>
            </section>
          </div>

          <div className="mt-10 pt-6 border-t border-muted">
            <p className="text-sm text-muted-foreground">
              By using SEALNEXT, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
