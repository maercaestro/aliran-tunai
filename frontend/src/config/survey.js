// Survey schema for the FLOW waiting list.
// Mirrors the Google Form "Survey 'FLOW': Faham Betul-Betul Aliran Tunai anda".
// Edit questions here — the multi-step form and backend validation key off `id`.

const survey = {
  id: 'flow-waitlist-v1',
  title: "Survey 'FLOW': Faham Betul-Betul Aliran Tunai Anda",
  description:
    "Kami nak faham cabaran pengurusan tunai bisnes anda. Maklum balas jujur anda " +
    "sangat penting untuk kami siapkan AI FLOW yang betul-betul 'ngam'!",
  sections: [
    {
      id: 'section-1',
      title: 'Seksyen 1: Kesedaran & Pengurusan Tunai Semasa',
      questions: [
        {
          id: 'cash_sync_feeling',
          type: 'single_choice',
          required: true,
          label:
            "Pernah tak rasa sales macam lebat, tapi bila tengok baki bank, macam tak ada apa-apa?",
          help: "Duit masuk vs Duit Keluar tak 'sync'",
          options: [
            { value: 'never', label: 'Tak pernah (Semua di bawah kawalan)' },
            { value: 'sometimes', label: 'Kadang-kadang (Ada masa terkejut)' },
            { value: 'often', label: 'Kerap (Selalu tertanya-tanya ke mana duit pergi)' },
            { value: 'always', label: 'Selalu sangat (Ini masalah utama bisnes saya)' },
          ],
        },
        {
          id: 'ccc_tracking_method',
          type: 'single_choice',
          required: true,
          label:
            "Macam mana anda 'track' atau pantau Cash Conversion Cycle (CCC) perniagaan anda sekarang?",
          help:
            'CCC: Berapa lama masa yang diambil untuk tukarkan inventori/jualan jadi duit tunai di tangan',
          options: [
            { value: 'none', label: 'Tak tahu / Tak track langsung' },
            { value: 'spreadsheet', label: 'Guna Excel / Spreadsheet sendiri' },
            { value: 'software', label: 'Guna software perakaunan / ERP sedia ada' },
            { value: 'feeling', label: 'Main agak-agak je (Berdasarkan feeling / baki bank semasa)' },
            { value: 'bookkeeper', label: 'Bantuan Akauntan / Bookkeeper' },
            { value: 'all', label: 'Semua di atas' },
          ],
        },
      ],
    },
    {
      id: 'section-2',
      title: 'Seksyen 2: Pelaburan dalam Pengurusan Kewangan',
      questions: [
        {
          id: 'affordable_bookkeeper_salary',
          type: 'single_choice',
          required: true,
          label:
            'Jika perniagaan anda sudah di tahap memerlukan akauntan atau penjaga kunci kira-kira untuk memastikan akaun anda sentiasa dikemaskini, berapakah amaun gaji yang anda mampu bayar sebulan?',
          options: [
            { value: 'RM2200', label: 'A. RM2200' },
            { value: 'RM2500', label: 'B. RM2500' },
            { value: 'RM2800', label: 'C. RM2800' },
            { value: 'RM3000', label: 'D. RM3000' },
          ],
        },
      ],
    },
    {
      id: 'section-3',
      title: 'Seksyen 3: Feature & Harga FLOW',
      description:
        "FLOW ialah AI Assistant di WhatsApp. Anda hanya perlu 'text' atau 'snap' gambar resit " +
        'jualan/belanja, dan AI kami akan auto-track aliran tunai bisnes anda.',
      questions: [
        {
          id: 'most_useful_feature',
          type: 'single_choice',
          required: true,
          label:
            "Antara feature di bawah, yang mana PALING 'ngam' dan membantu bisnes anda?",
          options: [
            { value: 'ccc_score', label: 'Skor CCC (Nilai kesihatan tunai bisnes dalam satu nombor)' },
            { value: 'debt_reminder', label: 'Reminder auto untuk customer yang hutang (Elak lupa kutip)' },
            { value: 'snap_receipt', label: "Fungsi 'Snap Resit' (Auto-masuk data, tak perlu key-in)" },
            { value: 'cashflow_forecast', label: 'Ramalan cash flow 30 hari (Tahu awal bila nak ‘sesak’ duit)' },
            { value: 'weekly_summary', label: 'Summary mingguan terus kat WhatsApp (Ringkasan cepat)' },
          ],
        },
        // Van Westendorp Price Sensitivity Meter
        {
          id: 'price_too_expensive',
          type: 'number',
          required: true,
          label:
            "Apakah harga bulanan (RM) untuk FLOW yang anda rasa 'Mahal Sangat'?",
          help: 'Beyond budget, tak sanggup bayar.',
          min: 0,
          max: 10000,
          placeholder: 'cth: 200',
        },
        {
          id: 'price_too_cheap',
          type: 'number',
          required: true,
          label:
            "Apakah harga bulanan (RM) untuk FLOW yang anda rasa 'Murah Sangat'?",
          help: 'Sampai takut kualiti low / macam tak logik.',
          min: 0,
          max: 10000,
          placeholder: 'cth: 10',
        },
        {
          id: 'price_getting_expensive',
          type: 'number',
          required: true,
          label:
            "Apakah harga bulanan (RM) untuk FLOW yang anda rasa 'Mula Rasa Mahal'?",
          help: 'Titik di mana anda akan berfikir dua kali sebelum subscribe.',
          min: 0,
          max: 10000,
          placeholder: 'cth: 120',
        },
        {
          id: 'price_good_value',
          type: 'number',
          required: true,
          label:
            "Apakah harga bulanan (RM) untuk FLOW yang anda rasa 'Berbaloi'?",
          help: 'Nilai yang anda rasa adil dan sanggup bayar untuk semua feature.',
          min: 0,
          max: 10000,
          placeholder: 'cth: 50',
        },
      ],
    },
    {
      id: 'section-4',
      title: 'Seksyen 4: Latar Belakang Bisnes & Minat',
      questions: [
        {
          id: 'industry',
          type: 'single_choice',
          required: true,
          label: 'Apakah industri utama perniagaan anda?',
          options: [
            { value: 'fnb', label: 'Makanan & Minuman (F&B)' },
            { value: 'retail', label: 'Retail / Kedai Fizikal' },
            { value: 'ecommerce', label: 'E-Commerce / Online Business' },
            { value: 'services', label: 'Perkhidmatan (Consultancy, Agensi, Kontraktor)' },
            { value: 'manufacturing', label: 'Sektor Pembuatan (Manufacturing)' },
            { value: 'other', label: 'Lain-lain (Sila nyatakan di soalan seterusnya)' },
          ],
        },
        {
          id: 'industry_other',
          type: 'short_text',
          required: false,
          label: 'Jika "Lain-lain", sila nyatakan industri anda:',
          maxLength: 120,
          showIf: { question: 'industry', equals: 'other' },
        },
        {
          id: 'monthly_transactions',
          type: 'single_choice',
          required: true,
          label:
            'Secara purata, berapa banyak transaksi (jualan dan belian) yang bisnes anda handle dalam sebulan?',
          options: [
            { value: '1-50', label: '1 - 50 transaksi' },
            { value: '51-200', label: '51 - 200 transaksi' },
            { value: '201-500', label: '201 - 500 transaksi' },
            { value: '500+', label: 'Lebih 500 transaksi' },
          ],
        },
      ],
    },
    {
      id: 'section-5',
      title: "Seksyen 5: Daftar Sebagai 'First User'",
      description:
        "Jika anda berminat untuk menjadi 'First User' (orang terawal) yang mencuba FLOW, " +
        'sila tinggalkan maklumat anda di bawah.',
      questions: [
        {
          id: 'name',
          type: 'short_text',
          required: true,
          label: 'Nama anda',
          maxLength: 120,
          placeholder: 'cth: Ahmad Faiz',
        },
        {
          id: 'whatsapp',
          type: 'phone',
          required: true,
          label: 'Nombor WhatsApp',
          placeholder: 'cth: 60123456789',
          help: 'Sertakan kod negara (cth: 60 untuk Malaysia).',
        },
        {
          id: 'email',
          type: 'email',
          required: false,
          label: 'Emel (optional)',
          placeholder: 'nama@contoh.com',
        },
        {
          id: 'business_name',
          type: 'short_text',
          required: false,
          label: 'Nama perniagaan (optional)',
          maxLength: 120,
        },
      ],
    },
  ],
};

export default survey;
