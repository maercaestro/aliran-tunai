import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  PaperAirplaneIcon,
} from '@heroicons/react/24/outline';
import survey from '../config/survey';
import brandConfig from '../config/brand';
import { buildApiUrl } from '../config/api';

/**
 * Multi-step waitlist survey. One section per step.
 * Submits to POST /api/waitlist.
 */
export default function WaitlistSurvey() {
  const navigate = useNavigate();
  const [stepIndex, setStepIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitted, setSubmitted] = useState(null); // { position }

  const sections = survey.sections;
  const totalSteps = sections.length;
  const currentSection = sections[stepIndex];
  const progress = Math.round(((stepIndex + 1) / totalSteps) * 100);

  // Filter questions by `showIf` conditional visibility.
  const visibleQuestions = useMemo(
    () => currentSection.questions.filter((q) => isVisible(q, answers)),
    [currentSection, answers]
  );

  function setAnswer(id, value) {
    setAnswers((a) => ({ ...a, [id]: value }));
    setErrors((e) => {
      if (!e[id]) return e;
      const { [id]: _, ...rest } = e;
      return rest;
    });
  }

  function validateCurrentStep() {
    const errs = {};
    for (const q of visibleQuestions) {
      const v = answers[q.id];
      if (q.required && (v === undefined || v === null || v === '')) {
        errs[q.id] = 'Soalan ini wajib diisi.';
        continue;
      }
      if (v === undefined || v === '') continue;
      if (q.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
        errs[q.id] = 'Format emel tidak sah.';
      } else if (q.type === 'phone' && !/^\+?[0-9]{7,15}$/.test(String(v).replace(/[\s-]/g, ''))) {
        errs[q.id] = 'Nombor WhatsApp tidak sah (contoh: 60123456789).';
      } else if (q.type === 'number') {
        const n = Number(v);
        if (Number.isNaN(n)) errs[q.id] = 'Sila masukkan nombor.';
        else if (q.min !== undefined && n < q.min) errs[q.id] = `Minimum ${q.min}.`;
        else if (q.max !== undefined && n > q.max) errs[q.id] = `Maksimum ${q.max}.`;
      }
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function next() {
    if (!validateCurrentStep()) return;
    setStepIndex((i) => Math.min(i + 1, totalSteps - 1));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function back() {
    setStepIndex((i) => Math.max(i - 1, 0));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function submit() {
    if (!validateCurrentStep()) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const res = await axios.post(buildApiUrl('/api/waitlist'), {
        survey_id: survey.id,
        answers,
      });
      // Mark as visited so the root router doesn't bounce them back here.
      localStorage.setItem('visited_before', 'true');
      setSubmitted({ position: res.data?.position ?? null });
    } catch (err) {
      const msg =
        err.response?.data?.error ||
        err.response?.data?.message ||
        'Penghantaran gagal. Sila cuba lagi sebentar.';
      setSubmitError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return <ThankYou position={submitted.position} navigate={navigate} />;
  }

  const isLastStep = stepIndex === totalSteps - 1;

  return (
    <div className="min-h-screen bg-slate-950 relative overflow-hidden">
      {/* Nav */}
      <nav className="absolute top-0 left-0 right-0 z-20 bg-slate-900/50 backdrop-blur-md border-b border-slate-800">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Link to="/welcome" className="flex items-center gap-2">
            <img
              src={brandConfig.logo.path}
              alt={brandConfig.logo.alt}
              className="h-10 object-contain"
            />
          </Link>
          <Link to="/login" className="text-sm text-slate-400 hover:text-teal-400">
            Sudah daftar?
          </Link>
        </div>
      </nav>

      <div className="absolute top-0 left-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="container mx-auto px-4 pt-28 pb-16 relative z-10 max-w-2xl">
        {/* Progress */}
        <div className="mb-6">
          <div className="flex justify-between text-xs text-slate-400 mb-2">
            <span>
              Langkah {stepIndex + 1} dari {totalSteps}
            </span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-teal-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Section header */}
        <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
          {currentSection.title}
        </h1>
        {currentSection.description && (
          <p className="text-slate-400 mb-8">{currentSection.description}</p>
        )}
        {!currentSection.description && <div className="mb-6" />}

        {/* Questions */}
        <div className="space-y-6">
          {visibleQuestions.map((q) => (
            <QuestionField
              key={q.id}
              question={q}
              value={answers[q.id]}
              onChange={(v) => setAnswer(q.id, v)}
              error={errors[q.id]}
            />
          ))}
        </div>

        {submitError && (
          <div className="mt-6 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
            {submitError}
          </div>
        )}

        {/* Nav buttons */}
        <div className="mt-10 flex items-center justify-between">
          <button
            type="button"
            onClick={back}
            disabled={stepIndex === 0 || submitting}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <ArrowLeftIcon className="w-4 h-4" /> Kembali
          </button>

          {isLastStep ? (
            <button
              type="button"
              onClick={submit}
              disabled={submitting}
              className="inline-flex items-center gap-2 bg-teal-500 text-slate-950 px-6 py-3 rounded-lg font-semibold hover:bg-teal-400 disabled:opacity-60 transition shadow-lg shadow-teal-500/25"
            >
              {submitting ? 'Menghantar...' : 'Hantar & Sertai Waiting List'}
              <PaperAirplaneIcon className="w-5 h-5" />
            </button>
          ) : (
            <button
              type="button"
              onClick={next}
              className="inline-flex items-center gap-2 bg-teal-500 text-slate-950 px-6 py-3 rounded-lg font-semibold hover:bg-teal-400 transition shadow-lg shadow-teal-500/25"
            >
              Seterusnya <ArrowRightIcon className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------- helpers ----------

function isVisible(q, answers) {
  if (!q.showIf) return true;
  return answers[q.showIf.question] === q.showIf.equals;
}

function QuestionField({ question, value, onChange, error }) {
  const baseInput =
    'w-full px-4 py-3 rounded-lg bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition';

  return (
    <div>
      <label className="block text-slate-100 font-medium mb-1">
        {question.label}
        {question.required && <span className="text-teal-400 ml-1">*</span>}
      </label>
      {question.help && (
        <p className="text-xs text-slate-400 mb-3">{question.help}</p>
      )}

      {question.type === 'single_choice' && (
        <div className="space-y-2 mt-2">
          {question.options.map((opt) => {
            const selected = value === opt.value;
            return (
              <label
                key={opt.value}
                className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition ${
                  selected
                    ? 'bg-teal-500/10 border-teal-500/60 text-white'
                    : 'bg-slate-900 border-slate-700 text-slate-200 hover:border-slate-600'
                }`}
              >
                <input
                  type="radio"
                  name={question.id}
                  value={opt.value}
                  checked={selected}
                  onChange={() => onChange(opt.value)}
                  className="mt-1 accent-teal-500"
                />
                <span className="text-sm">{opt.label}</span>
              </label>
            );
          })}
        </div>
      )}

      {(question.type === 'short_text' || question.type === 'email' || question.type === 'phone') && (
        <input
          type={question.type === 'email' ? 'email' : question.type === 'phone' ? 'tel' : 'text'}
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={question.placeholder}
          maxLength={question.maxLength}
          className={baseInput}
        />
      )}

      {question.type === 'long_text' && (
        <textarea
          rows={4}
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={question.placeholder}
          maxLength={question.maxLength}
          className={baseInput}
        />
      )}

      {question.type === 'number' && (
        <input
          type="number"
          inputMode="numeric"
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))}
          placeholder={question.placeholder}
          min={question.min}
          max={question.max}
          className={baseInput}
        />
      )}

      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
    </div>
  );
}

function ThankYou({ position, navigate }) {
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
      <div className="max-w-md text-center bg-slate-900/70 border border-teal-500/30 rounded-3xl p-10">
        <CheckCircleIcon className="w-16 h-16 text-teal-400 mx-auto mb-4" />
        <h1 className="text-3xl font-bold text-white mb-2">Terima kasih!</h1>
        <p className="text-slate-300 mb-2">
          Anda sudah berjaya daftar dalam waiting list FLOW.
        </p>
        {position && (
          <p className="text-teal-400 font-semibold mb-6">
            Kedudukan anda: #{position}
          </p>
        )}
        <p className="text-sm text-slate-400 mb-8">
          Kami akan hantar mesej di WhatsApp anda sebaik sahaja slot dibuka.
        </p>
        <button
          onClick={() => navigate('/welcome')}
          className="inline-flex items-center gap-2 bg-teal-500 text-slate-950 px-6 py-3 rounded-lg font-semibold hover:bg-teal-400 transition"
        >
          Kembali ke laman utama
        </button>
      </div>
    </div>
  );
}
