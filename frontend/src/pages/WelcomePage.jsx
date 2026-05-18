import { Link } from 'react-router-dom';
import {
  ArrowRightIcon,
  ArrowRightOnRectangleIcon,
  ChatBubbleLeftRightIcon,
  CameraIcon,
  ChartBarIcon,
  BellAlertIcon,
  SparklesIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import brandConfig from '../config/brand';

/**
 * WelcomePage — shown to first-time visitors who have NOT registered with
 * the WhatsApp bot yet. Showcases the product flow and pushes them to the
 * waiting-list survey.
 */
export default function WelcomePage() {
  const flowSteps = [
    {
      icon: ChatBubbleLeftRightIcon,
      title: 'Text or snap on WhatsApp',
      body: 'Hantar mesej atau gambar resit terus dari WhatsApp — tiada app baru untuk download.',
    },
    {
      icon: SparklesIcon,
      title: 'AI extracts the details',
      body: 'AI kami baca resit, kenal pasti vendor, kategori, dan amaun secara automatik.',
    },
    {
      icon: ChartBarIcon,
      title: 'Live cash flow dashboard',
      body: 'Lihat kesihatan tunai bisnes anda dalam masa nyata — di mana-mana sahaja.',
    },
    {
      icon: BellAlertIcon,
      title: 'Smart reminders',
      body: 'Reminder auto untuk hutang customer & ramalan cash flow 30 hari ke depan.',
    },
  ];

  const benefits = [
    'Tiada lagi key-in manual — snap je resit',
    'Faham CCC (Cash Conversion Cycle) tanpa pening kepala',
    'Skor kesihatan tunai bisnes dalam satu nombor',
    'Summary mingguan terus ke WhatsApp anda',
  ];

  return (
    <div className="min-h-screen bg-slate-950 relative overflow-hidden">
      {/* Nav */}
      <nav className="absolute top-0 left-0 right-0 z-20 bg-slate-900/50 backdrop-blur-md border-b border-slate-800">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <img
              src={brandConfig.logo.path}
              alt={brandConfig.logo.alt}
              className="h-10 object-contain drop-shadow-[0_0_10px_rgba(45,212,191,0.2)]"
            />
          </div>
          <Link
            to="/login"
            className="flex items-center gap-2 px-4 py-2 text-slate-300 hover:text-teal-400 hover:bg-teal-500/10 rounded-lg transition"
          >
            <ArrowRightOnRectangleIcon className="w-4.5 h-4.5" />
            <span>Sudah daftar? Login</span>
          </Link>
        </div>
      </nav>

      {/* Background glow */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Hero */}
      <section className="container mx-auto px-4 pt-32 pb-16 relative z-10">
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 mb-6 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-300 text-sm">
            <SparklesIcon className="w-4 h-4" />
            Pre-launch · Waiting list dibuka
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 tracking-tight">
            Aliran tunai bisnes anda,<br />
            <span className="text-teal-400">terus di WhatsApp.</span>
          </h1>
          <p className="text-lg md:text-xl text-slate-300 mb-10 max-w-2xl mx-auto">
            FLOW ialah AI Assistant yang track jualan, belian, dan hutang bisnes anda
            secara automatik. Cukup hantar mesej atau snap resit — kami uruskan
            selebihnya.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/waitlist"
              className="inline-flex items-center justify-center gap-2 bg-teal-500 text-slate-950 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-teal-400 transition-all duration-200 shadow-lg shadow-teal-500/25"
            >
              Sertai Waiting List <ArrowRightIcon className="w-5 h-5" />
            </Link>
            <a
              href="#how-it-works"
              className="inline-flex items-center justify-center gap-2 bg-slate-800/60 text-slate-200 px-8 py-4 rounded-lg text-lg font-medium hover:bg-slate-800 border border-slate-700 transition"
            >
              Tengok cara ia berfungsi
            </a>
          </div>
          <p className="mt-4 text-sm text-slate-500">
            Jawab survey pendek (~2 minit). Kami akan hubungi anda bila slot dibuka.
          </p>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="bg-slate-900/50 backdrop-blur-md py-20 relative z-10">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-3">
              Bagaimana FLOW berfungsi
            </h2>
            <p className="text-slate-400">Empat langkah. Tiada training, tiada setup yang menyusahkan.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {flowSteps.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.title}
                  className="relative bg-slate-900/80 border border-slate-800 rounded-2xl p-6 hover:border-teal-500/40 transition"
                >
                  <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-teal-500 text-slate-950 font-bold flex items-center justify-center">
                    {idx + 1}
                  </div>
                  <Icon className="w-10 h-10 text-teal-400 mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">{step.title}</h3>
                  <p className="text-sm text-slate-400">{step.body}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Showcase mock chat */}
      <section className="py-20 relative z-10">
        <div className="container mx-auto px-4 max-w-5xl grid md:grid-cols-2 gap-10 items-center">
          <div>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Macam ber-chat dengan kawan.
            </h2>
            <p className="text-slate-300 mb-6">
              Hantar je apa yang anda buat hari ini. FLOW akan kategorikan, simpan, dan
              update dashboard anda secara automatik.
            </p>
            <ul className="space-y-3">
              {benefits.map((b) => (
                <li key={b} className="flex items-start gap-3 text-slate-200">
                  <CheckCircleIcon className="w-5 h-5 text-teal-400 mt-0.5 shrink-0" />
                  <span>{b}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Mock WhatsApp chat */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-2xl shadow-teal-500/5">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-800 mb-3">
              <div className="w-9 h-9 rounded-full bg-teal-500/20 flex items-center justify-center">
                <SparklesIcon className="w-5 h-5 text-teal-400" />
              </div>
              <div>
                <p className="text-white text-sm font-semibold">FLOW Assistant</p>
                <p className="text-xs text-teal-400">online</p>
              </div>
            </div>
            <div className="space-y-2">
              <div className="ml-auto max-w-[80%] bg-teal-500/15 text-slate-100 text-sm rounded-2xl rounded-tr-sm px-4 py-2">
                Jual nasi lemak RM250 pagi ni, bayar cash
              </div>
              <div className="max-w-[85%] bg-slate-800 text-slate-100 text-sm rounded-2xl rounded-tl-sm px-4 py-2">
                ✅ Direkodkan: <b>Sales · RM250</b> · Tunai · F&amp;B<br />
                <span className="text-slate-400">Jumlah sales hari ni: RM480</span>
              </div>
              <div className="ml-auto max-w-[80%] bg-teal-500/15 text-slate-100 text-sm rounded-2xl rounded-tr-sm px-4 py-2">
                <span className="inline-flex items-center gap-1">
                  <CameraIcon className="w-4 h-4" /> [Resit beli bahan mentah]
                </span>
              </div>
              <div className="max-w-[85%] bg-slate-800 text-slate-100 text-sm rounded-2xl rounded-tl-sm px-4 py-2">
                ✅ Direkodkan: <b>Purchase · RM87.40</b> · Pasar Borong KL · Inventori
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 relative z-10">
        <div className="container mx-auto px-4 max-w-3xl text-center">
          <div className="bg-linear-to-br from-teal-500/10 to-indigo-500/10 border border-teal-500/30 rounded-3xl p-10">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-3">
              Jadi 'First User' FLOW.
            </h2>
            <p className="text-slate-300 mb-8">
              Tempat terhad. Jawab survey pendek untuk dapatkan akses awal & harga early-bird.
            </p>
            <Link
              to="/waitlist"
              className="inline-flex items-center gap-2 bg-teal-500 text-slate-950 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-teal-400 transition shadow-lg shadow-teal-500/25"
            >
              Mula Survey & Daftar <ArrowRightIcon className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-800 py-8 text-center text-sm text-slate-500 relative z-10">
        © {new Date().getFullYear()} {brandConfig.name}.{' '}
        <Link to="/privacy-policy" className="hover:text-teal-400">
          Privacy Policy
        </Link>
      </footer>
    </div>
  );
}
