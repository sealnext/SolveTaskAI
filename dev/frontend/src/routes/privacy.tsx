import React from 'react';
import { createFileRoute, Link } from '@tanstack/react-router';
import { ThemeToggle } from '@/components/theme-toggle';

export const Route = createFileRoute('/privacy')({
	component: Privacy,
});

function Privacy() {
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
          <h1 className="text-3xl font-bold mb-6">Privacy Policy</h1>

          <p className="text-muted-foreground mb-6">Last updated: {new Date().toLocaleDateString()}</p>

          <div className="space-y-6 text-sm">
            <section>
              <h2 className="text-xl font-semibold mb-3">1. Introduction</h2>
              <p>
                Welcome to SEALNEXT. This Privacy Policy explains how SEALNEXT SRL (&ldquo;Company&rdquo;, &ldquo;we&rdquo;, &ldquo;us&rdquo;, or &ldquo;our&rdquo;), a company registered in Romania, collects, uses, processes, and protects your personal information when you use our AI agent for ticketing systems (&ldquo;Service&rdquo;). By accessing or using our Service, you agree to the collection and use of information in accordance with this policy. If you do not agree with any part of this policy, you may not access or use the Service.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">2. Data Controller Information</h2>
              <p>
                SEALNEXT SRL, a company registered in Romania, acts as the data controller for the personal information collected through our Service. If you have any questions about this Privacy Policy or our data practices, please contact us at:
              </p>
              <p className="mt-2">
                Email: support@sealnext.com
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">3. Information We Collect</h2>
              <p>
                We collect several types of information for various purposes to provide and improve our Service to you:
              </p>
              <h3 className="text-lg font-medium mt-3 mb-2">3.1 Information You Provide Directly</h3>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li><strong>Account Information:</strong> When you register for our Service, we collect information such as your name, email address, and company name.</li>
                <li><strong>API Keys:</strong> To provide our core functionality, you provide API keys for ticketing systems such as Jira and Microsoft Azure DevOps Boards. These keys allow us to fetch, process, and analyze your ticketing data.</li>
                <li><strong>Communications:</strong> If you contact us directly, we may receive additional information about you, such as your name, email address, the contents of your message, and any other information you choose to provide.</li>
              </ul>

              <h3 className="text-lg font-medium mt-3 mb-2">3.2 Information We Collect Automatically</h3>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li><strong>Usage Data:</strong> We collect information on how the Service is accessed and used. This may include information such as your computer&apos;s Internet Protocol address, browser type, browser version, the pages of our Service that you visit, the time and date of your visit, the time spent on those pages, and other diagnostic data.</li>
                <li><strong>Cookies:</strong> We use cookies to maintain session information. A cookie is a small piece of data stored on your device. We use only essential authentication cookies necessary to provide our Service.</li>
              </ul>

              <h3 className="text-lg font-medium mt-3 mb-2">3.3 Information From Ticketing Systems</h3>
              <p>
                Using the API keys you provide, we collect and process data from your ticketing systems, which may include:
              </p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li>Ticket titles, descriptions, and comments</li>
                <li>Ticket statuses, priorities, and types</li>
                <li>User assignments and contributor information</li>
                <li>Project and workflow metadata</li>
                <li>Time tracking and due date information</li>
                <li>Attachment references (but not the actual files)</li>
                <li>Historical changes and updates to tickets</li>
              </ul>
              <p className="mt-2">
                This data is collected solely for the purpose of providing the SEALNEXT Service and enabling the AI agent to understand, respond to queries about, and potentially take actions within your ticketing system upon your request.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">4. Legal Basis for Processing</h2>
              <p>
                We process your personal data on the following legal grounds:
              </p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li><strong>Performance of a Contract:</strong> Processing is necessary for the performance of our contract with you to provide the SEALNEXT Service.</li>
                <li><strong>Legitimate Interests:</strong> Processing is necessary for our legitimate interests, such as to improve and develop our Service, protect the security of our Service, and for our marketing activities, provided that these interests are not overridden by your rights and freedoms.</li>
                <li><strong>Consent:</strong> In some cases, we process your data based on your consent, such as for certain marketing communications. You can withdraw your consent at any time.</li>
                <li><strong>Legal Obligation:</strong> Processing may be necessary to comply with a legal obligation to which we are subject.</li>
              </ul>
              <p className="mt-2">
                For EU citizens, our processing of personal data is in compliance with the General Data Protection Regulation (GDPR).
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">5. How We Use Your Information</h2>
              <p>
                We use the collected data for various purposes:
              </p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li>To provide, maintain, and improve our Service</li>
                <li>To process your account registration and manage your account</li>
                <li>To enable the AI agent to access and process your ticketing data</li>
                <li>To allow you to interact with the AI agent via natural language to perform actions and retrieve information from your ticketing systems</li>
                <li>To notify you about changes to our Service</li>
                <li>To provide customer support</li>
                <li>To gather analysis or valuable information so that we can improve our Service</li>
                <li>To monitor usage of our Service</li>
                <li>To detect, prevent, and address technical issues</li>
                <li>To send you marketing communications about our current and future products and services (you may opt out at any time)</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">6. Third-Party Service Providers</h2>
              <p>
                We may employ third-party companies and individuals to facilitate our Service (&ldquo;Service Providers&rdquo;), provide the Service on our behalf, or assist us in analyzing how our Service is used. These third parties include:
              </p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li><strong>AI and Machine Learning Services:</strong> We use services such as OpenAI and Google Gemini for RAG (Retrieval-Augmented Generation) embeddings vectors and large language model processing. Your ticketing data may be processed by these services to generate responses and perform actions, but we do not use this data to train these models for other purposes.</li>
                <li><strong>Hosting and Infrastructure Providers:</strong> To host and deliver our Service.</li>
                <li><strong>Analytics Providers:</strong> To help us understand how our Service is used.</li>
                <li><strong>Payment Processors:</strong> To process payments for subscription services, if applicable.</li>
              </ul>
              <p className="mt-2">
                These third parties have access to your personal data only to perform these tasks on our behalf and are contractually obligated not to disclose or use it for any other purpose. However, we cannot guarantee the same level of data protection once your information is shared with these third parties, and they may have their own privacy policies and practices.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">7. Data Retention</h2>
              <p>
                We will retain your personal data only for as long as is necessary for the purposes set out in this Privacy Policy. We will retain and use your personal data to the extent necessary to comply with our legal obligations, resolve disputes, and enforce our legal agreements and policies.
              </p>
              <p className="mt-2">
                Specifically regarding ticketing data fetched via API keys:
              </p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li>Data fetched from your ticketing systems is primarily processed in real-time to provide the Service.</li>
                <li>We may cache certain data to improve performance and provide a better user experience.</li>
                <li>Conversation history with the AI agent (which may contain references to your ticketing data) is retained to provide context for future interactions.</li>
                <li>You can request deletion of your conversation history at any time by contacting support@sealnext.com.</li>
              </ul>
              <p className="mt-2">
                We will also retain usage data for internal analysis purposes. Usage data is generally retained for a shorter period, except when this data is used to strengthen the security or to improve the functionality of our Service, or we are legally obligated to retain this data for longer time periods.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">8. Data Security</h2>
              <p>
                The security of your data is important to us. We implement appropriate technical and organizational measures to protect your personal information, including:
              </p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li>Encryption of data in transit and at rest</li>
                <li>Secure handling of API keys and access tokens</li>
                <li>Regular security assessments and updates</li>
                <li>Access controls and authentication mechanisms</li>
                <li>Staff training on data security practices</li>
              </ul>
              <p className="mt-2">
                However, no method of transmission over the Internet or method of electronic storage is 100% secure. While we strive to use commercially acceptable means to protect your personal information, we cannot guarantee its absolute security. You acknowledge that you provide your data, including API keys, at your own risk. The Company is not liable for any breaches of security or unauthorized access to your data, regardless of our adherence to reasonable security standards.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">9. Your Data Protection Rights Under GDPR</h2>
              <p>
                If you are a resident of the European Economic Area (EEA), you have certain data protection rights under the General Data Protection Regulation (GDPR). We aim to take reasonable steps to allow you to correct, amend, delete, or limit the use of your personal data.
              </p>
              <p className="mt-2">
                You have the following data protection rights:
              </p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li><strong>The right to access:</strong> You have the right to request copies of your personal data.</li>
                <li><strong>The right to rectification:</strong> You have the right to request that we correct any information you believe is inaccurate or complete information you believe is incomplete.</li>
                <li><strong>The right to erasure (right to be forgotten):</strong> You have the right to request that we erase your personal data, under certain conditions. To exercise this right, please email us at support@sealnext.com.</li>
                <li><strong>The right to restrict processing:</strong> You have the right to request that we restrict the processing of your personal data, under certain conditions.</li>
                <li><strong>The right to object to processing:</strong> You have the right to object to our processing of your personal data, under certain conditions.</li>
                <li><strong>The right to data portability:</strong> You have the right to request that we transfer the data that we have collected to another organization, or directly to you, under certain conditions.</li>
              </ul>
              <p className="mt-2">
                If you wish to exercise any of these rights, please contact us at support@sealnext.com. We will respond to your request within 30 days. We may need to verify your identity before responding to your request.
              </p>
              <p className="mt-2">
                Please note that these rights may be limited in some circumstances, for example, if fulfilling your request would reveal personal data about another person, or if you ask us to delete information which we are required by law to keep or have compelling legitimate interests in keeping. If you have unresolved concerns, you have the right to complain to a data protection authority in the country where you live, where you work, or where you feel your rights have been infringed.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">10. Cookies Policy</h2>
              <p>
                We use only essential cookies necessary for authentication and maintaining your session while using our Service. These cookies are required for the proper functioning of our Service and cannot be declined if you wish to use the Service.
              </p>
              <p className="mt-2">
                Our authentication cookies store session information to keep you logged in during your visit and across visits if you choose to remain logged in. These cookies do not track your activity across other websites and are used solely for the purpose of providing the core functionality of our Service.
              </p>
              <p className="mt-2">
                You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent. However, if you do not accept cookies, you may not be able to use some portions of our Service.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">11. International Data Transfers</h2>
              <p>
                Your information, including personal data, may be transferred to and maintained on computers located outside of your state, province, country, or other governmental jurisdiction where the data protection laws may differ from those of your jurisdiction.
              </p>
              <p className="mt-2">
                If you are located outside Romania and choose to provide information to us, please note that we transfer the data, including personal data, to Romania and process it there. Additionally, we may transfer your data to third-party service providers located in other countries, including:
              </p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li>United States (for certain AI and cloud service providers)</li>
                <li>European Union member states</li>
                <li>Other countries where our service providers may operate</li>
              </ul>
              <p className="mt-2">
                Your consent to this Privacy Policy followed by your submission of such information represents your agreement to these transfers. For transfers from the EEA to countries not considered adequate by the European Commission, we have put in place appropriate safeguards, such as Standard Contractual Clauses approved by the European Commission, to protect your personal data.
              </p>
              <p className="mt-2">
                SEALNEXT will take all the steps reasonably necessary to ensure that your data is treated securely and in accordance with this Privacy Policy, and no transfer of your personal data will take place to an organization or a country unless there are adequate controls in place, including the security of your data and other personal information.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">12. Children&apos;s Privacy</h2>
              <p>
                Our Service does not address anyone under the age of 18 (&ldquo;Children&rdquo;). We do not knowingly collect personally identifiable information from anyone under the age of 18. If you are a parent or guardian and you are aware that your child has provided us with personal data, please contact us. If we become aware that we have collected personal data from children without verification of parental consent, we take steps to remove that information from our servers.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">13. International Compliance</h2>
              <p>
                We strive to comply with privacy laws in various jurisdictions, including but not limited to:
              </p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li><strong>European Union:</strong> General Data Protection Regulation (GDPR)</li>
                <li><strong>United States:</strong> California Consumer Privacy Act (CCPA) and applicable state laws</li>
                <li><strong>Canada:</strong> Personal Information Protection and Electronic Documents Act (PIPEDA)</li>
                <li><strong>Australia:</strong> Australian Privacy Principles (APPs) under the Privacy Act 1988</li>
              </ul>
              <p className="mt-2">
                Users in these jurisdictions may have specific rights regarding their personal data as defined by these regulations. Users in other jurisdictions acknowledge that by using the Service, they do so at their own risk and are responsible for compliance with local laws.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">14. Changes to This Privacy Policy</h2>
              <p>
                We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the &quot;Last updated&quot; date at the top of this Privacy Policy.
              </p>
              <p className="mt-2">
                For significant changes, we will make reasonable efforts to provide notification through our Service or via email prior to the changes becoming effective. However, you are advised to review this Privacy Policy periodically for any changes. Changes to this Privacy Policy are effective when they are posted on this page. Your continued use of the Service after we post any modifications to the Privacy Policy will constitute your acknowledgment of the modifications and your consent to abide and be bound by the modified Privacy Policy.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">15. Disclaimer of Liability</h2>
              <p>
                By using our Service, you agree that SEALNEXT SRL shall not be liable for any damages arising from the use of the Service or from the disclosure of information through the use of the Service. The Company is not liable for the security of your personal data during transmission or after receipt by third-party services. You acknowledge that you provide your information at your own risk and that the Company is not liable for any security breaches or unauthorized access to your data.
              </p>
              <p className="mt-2">
                Furthermore, you agree that you will not hold the Company liable for any damages resulting from the use of information obtained through the Service, including but not limited to any decisions made or actions taken based on such information.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">16. Consent</h2>
              <p>
                By using our Service, you consent to our Privacy Policy and agree to its terms. If you do not agree to this Privacy Policy, please do not use our Service. Your continued use of the Service following the posting of changes to this policy will be deemed your acceptance of those changes.
              </p>
              <p className="mt-2">
                You acknowledge that by providing your API keys and allowing access to your ticketing systems, you are giving explicit consent for us to process the data contained within those systems for the purposes described in this Privacy Policy.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">17. Contact Us</h2>
              <p>
                If you have any questions about this Privacy Policy, please contact us at support@sealnext.com.
              </p>
            </section>
          </div>

          <div className="mt-10 pt-6 border-t border-muted">
            <p className="text-sm text-muted-foreground">
              By using SEALNEXT, you acknowledge that you have read, understood, and agree to be bound by this Privacy Policy.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
