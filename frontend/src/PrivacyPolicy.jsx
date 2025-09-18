import React from 'react';

const PrivacyPolicy = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-xl shadow-2xl p-8 md:p-12">
          <h1 className="text-4xl font-bold text-gray-800 text-center mb-4">Privacy Policy</h1>
          <div className="text-center text-gray-600 mb-8 bg-gray-50 p-4 rounded-lg italic">
            Last updated: September 18, 2025
          </div>
          
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b-2 border-blue-400 pb-2">
              1. Introduction
            </h2>
            <p className="text-gray-600 mb-4 leading-relaxed">
              Welcome to Aliran Tunai ("we," "our," or "us"). This Privacy Policy explains how we collect, 
              use, disclose, and safeguard your information when you use our financial tracking WhatsApp 
              bot service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b-2 border-blue-400 pb-2">
              2. Information We Collect
            </h2>
            <h3 className="text-xl font-medium text-gray-700 mt-6 mb-3">2.1 Information You Provide</h3>
            <ul className="list-disc ml-6 mb-4 space-y-2">
              <li className="text-gray-600">WhatsApp phone number</li>
              <li className="text-gray-600">Financial transaction data you share via messages</li>
              <li className="text-gray-600">Text messages and images you send to our bot</li>
              <li className="text-gray-600">Categories and descriptions of your expenses and income</li>
            </ul>
            
            <h3 className="text-xl font-medium text-gray-700 mt-6 mb-3">2.2 Information Automatically Collected</h3>
            <ul className="list-disc ml-6 mb-4 space-y-2">
              <li className="text-gray-600">Message timestamps</li>
              <li className="text-gray-600">Usage patterns and interaction data</li>
              <li className="text-gray-600">Technical information for service improvement</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b-2 border-blue-400 pb-2">
              3. How We Use Your Information
            </h2>
            <p className="text-gray-600 mb-4">We use your information to:</p>
            <ul className="list-disc ml-6 mb-4 space-y-2">
              <li className="text-gray-600">Process and categorize your financial transactions</li>
              <li className="text-gray-600">Generate financial summaries and insights</li>
              <li className="text-gray-600">Provide personalized financial advice</li>
              <li className="text-gray-600">Improve our AI-powered transaction processing</li>
              <li className="text-gray-600">Maintain and improve our services</li>
              <li className="text-gray-600">Comply with legal obligations</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b-2 border-blue-400 pb-2">
              4. Data Storage and Security
            </h2>
            <p className="text-gray-600 mb-4">
              Your data is stored securely in encrypted MongoDB databases. We implement industry-standard 
              security measures including:
            </p>
            <ul className="list-disc ml-6 mb-4 space-y-2">
              <li className="text-gray-600">End-to-end encryption for data transmission</li>
              <li className="text-gray-600">Secure database storage with access controls</li>
              <li className="text-gray-600">Regular security audits and updates</li>
              <li className="text-gray-600">Limited access to authorized personnel only</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b-2 border-blue-400 pb-2">
              5. Data Sharing and Disclosure
            </h2>
            <p className="text-gray-600 mb-4">We do not sell, trade, or otherwise transfer your personal information to third parties except:</p>
            <ul className="list-disc ml-6 mb-4 space-y-2">
              <li className="text-gray-600">With your explicit consent</li>
              <li className="text-gray-600">To comply with legal requirements</li>
              <li className="text-gray-600">To protect our rights and safety</li>
              <li className="text-gray-600">With trusted service providers who assist in our operations (under strict confidentiality agreements)</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b-2 border-blue-400 pb-2">
              6. Third-Party Services
            </h2>
            <p className="text-gray-600 mb-4">Our service integrates with:</p>
            <ul className="list-disc ml-6 mb-4 space-y-2">
              <li className="text-gray-600"><strong>WhatsApp Business API:</strong> For message processing</li>
              <li className="text-gray-600"><strong>OpenAI:</strong> For AI-powered transaction analysis (data is processed securely)</li>
              <li className="text-gray-600"><strong>MongoDB Atlas:</strong> For secure data storage</li>
            </ul>
            <p className="text-gray-600 mb-4">These services have their own privacy policies, and we encourage you to review them.</p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b-2 border-blue-400 pb-2">
              7. Data Retention
            </h2>
            <p className="text-gray-600 mb-4">
              We retain your information for as long as necessary to provide our services. You may request 
              deletion of your data at any time by sending "/delete" to our WhatsApp bot or contacting us directly.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b-2 border-blue-400 pb-2">
              8. Your Rights
            </h2>
            <p className="text-gray-600 mb-4">You have the right to:</p>
            <ul className="list-disc ml-6 mb-4 space-y-2">
              <li className="text-gray-600">Access your personal data</li>
              <li className="text-gray-600">Correct inaccurate information</li>
              <li className="text-gray-600">Delete your data (send "/delete" to our bot)</li>
              <li className="text-gray-600">Export your data</li>
              <li className="text-gray-600">Withdraw consent for data processing</li>
              <li className="text-gray-600">File a complaint with supervisory authorities</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b-2 border-blue-400 pb-2">
              9. Children's Privacy
            </h2>
            <p className="text-gray-600 mb-4">
              Our service is not intended for children under 13. We do not knowingly collect personal 
              information from children under 13. If we become aware of such data, we will delete it immediately.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b-2 border-blue-400 pb-2">
              10. International Data Transfers
            </h2>
            <p className="text-gray-600 mb-4">
              Your information may be transferred to and processed in countries other than your country of 
              residence. We ensure appropriate safeguards are in place for such transfers.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b-2 border-blue-400 pb-2">
              11. Changes to This Privacy Policy
            </h2>
            <p className="text-gray-600 mb-4">
              We may update this privacy policy from time to time. We will notify you of any material 
              changes by updating the "Last updated" date and, where appropriate, through our service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b-2 border-blue-400 pb-2">
              12. Contact Us
            </h2>
            <p className="text-gray-600 mb-4">If you have any questions about this Privacy Policy, please contact us:</p>
            <div className="bg-gray-50 p-6 rounded-lg border-l-4 border-blue-400">
              <p className="text-gray-700 font-medium mb-2"><strong>Email:</strong> privacy@alirantunai.com</p>
              <p className="text-gray-700 font-medium mb-2"><strong>WhatsApp:</strong> Send a message to our bot</p>
              <p className="text-gray-700 font-medium"><strong>Address:</strong> [Your business address]</p>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b-2 border-blue-400 pb-2">
              13. WhatsApp-Specific Terms
            </h2>
            <p className="text-gray-600 mb-4">By using our WhatsApp bot service:</p>
            <ul className="list-disc ml-6 mb-4 space-y-2">
              <li className="text-gray-600">You consent to receiving automated messages from our bot</li>
              <li className="text-gray-600">You can opt-out anytime by blocking our number or sending "STOP"</li>
              <li className="text-gray-600">We process messages according to WhatsApp's Business Policy</li>
              <li className="text-gray-600">Your WhatsApp account information is handled per WhatsApp's Privacy Policy</li>
            </ul>
          </section>

          <div className="mt-12 p-6 bg-gray-100 rounded-lg text-center">
            <p className="text-gray-600 text-sm italic">
              This privacy policy is designed to comply with GDPR, CCPA, and other applicable data 
              protection regulations. For jurisdiction-specific rights, please contact us.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;