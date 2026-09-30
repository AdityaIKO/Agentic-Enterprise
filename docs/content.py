"""Single source of truth for report + slides (Bahasa Indonesia). Numbers come from outputs/*.json."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "outputs/results.json").read_text())
W = json.loads((ROOT / "outputs/worked_example.json").read_text())

NAMA = "[Isi nama Anda]"          # <- ganti sebelum dikumpulkan
NIM = "[Isi NIM]"
REPO = "https://github.com/AdityaIKO/Agentic-Enterprise"
TITLE = "MALQS: Multi-Agent Lead Qualification & Scoring System"
COURSE = "Agentic Enterprise - Magister AI | Tugas 1 - Laporan Progres"
tier = R["tier_conversion_test"]
pct = lambda x: f"{100 * x:.1f}%"

ROLES = [
    ("Product owner & analis bisnis", "Merumuskan masalah, memilih topik, menentukan KPI (AUC, lift, konversi per tier)."),
    ("Data engineer", "Membuat generator data sintetis, pembersihan data (dedup, imputasi)."),
    ("ML engineer", "Merancang fitur, implementasi Logistic Regression (numpy), evaluasi & baseline."),
    ("Agent architect", "Merancang 5 agen + orchestrator, blackboard, feedback loop, diagram sistem."),
    ("Dokumentasi & presentasi", "Menyusun laporan PDF, PPT, dan repositori GitHub."),
]
ROLE_NOTE = ("Catatan: pekerjaan ini dikerjakan individu (mahasiswa bergabung terlambat), sehingga seluruh peran di atas dipegang "
             "satu orang. Claude Code digunakan sebagai asisten penulisan kode dan dokumen; seluruh keputusan desain, hasil, "
             "dan klaim ditinjau oleh penulis.")

PROBLEM = [
    "Tim sales B2B menerima ratusan hingga ribuan lead per bulan dari web form, webinar, e-mail, dan daftar dingin (cold list). "
    "Kapasitas sales terbatas, sehingga lead yang paling siap membeli sering terlambat ditindaklanjuti, sementara waktu terbuang untuk lead yang tidak akan pernah konversi.",
    "Kesulitan utama: (1) data kotor - duplikat dan nilai kosong; (2) kecocokan dengan Ideal Customer Profile (ICP) sulit dinilai manual; "
    "(3) sinyal minat tersebar (perilaku web, isi pesan, sumber lead); (4) skoring manual berbasis poin tidak belajar dari hasil won/lost.",
    "Tujuan: membangun sistem multi-agen yang membersihkan, memperkaya, menilai, dan merekomendasikan tindakan untuk setiap lead, "
    "yaitu skor 0-100 (probabilitas konversi) dan kategori hot / warm / cold, sehingga sales fokus pada lead dengan peluang tertinggi.",
    "Pilihan topik: agen 'Lead Qualification Agent' (#33) dan 'Lead Scoring Agent' (#37) pada tab spesifikasi, digabung dengan "
    "Lead Enrichment (#14) dan ICP Finder (#11). Topik ini belum diambil kelompok 1-6 (yang mengambil complaint handling, procurement, AI outsourcing, trading Bitcoin, customer service, dan software developer agent).",
]

DATA_NOTE = ("Data CRM nyata bersifat rahasia, sehingga dipakai data sintetis (seed=42, 2.060 baris mentah termasuk 60 duplikat sengaja; "
             "8% nilai kosong pada employees & title_level). Label 'converted' dibangkitkan dari fungsi logit tersembunyi yang tidak dilihat agen. "
             "Angka hasil karenanya BUKAN bukti performa di dunia nyata; ini bukti bahwa pipeline bekerja dan dapat dibandingkan dengan baseline.")

SAMPLE_TABLE = [
    ["Lead", "pricing_views", "demo", "days_since", "icp_fit"],
    ["A", "3", "1", "5", f"{W['cosine_icp']['A']:.3f}"],
    ["B", "0", "0", "60", f"{W['cosine_icp']['B']:.3f}"],
    ["C", "1", "0", "20", f"{W['cosine_icp']['C']:.3f}"],
]
CALC_TABLE = [["Lead", "z = b + w.x", "p = sigma(z)", "Skor", "Tier"]] + [
    [k, f"{v['z']}", f"{v['p']}", str(v['score']), v['tier']] for k, v in W["scoring"].items()]

FORMULAS = [
    ("cosine", r"$\cos(\mathbf{a},\mathbf{b})=\dfrac{\mathbf{a}\cdot\mathbf{b}}{\|\mathbf{a}\|\,\|\mathbf{b}\|}$",
     "a, b = vektor lead & centroid ICP (atau vektor teks); a.b = dot product; ||.|| = norma Euclid. Dipakai untuk icp_fit, text_intent, dan deteksi duplikat (trigram karakter). Rentang -1..1."),
    ("tfidf", r"$\mathrm{tfidf}(t,d)=\mathrm{tf}(t,d)\cdot\left(\ln\dfrac{1+N}{1+\mathrm{df}(t)}+1\right)$",
     "t = term; d = dokumen (pesan lead); tf = frekuensi term di d; N = jumlah dokumen; df(t) = jumlah dokumen berisi t (varian smooth scikit-learn)."),
    ("zscore", r"$\tilde{x}_j=\dfrac{x_j-\mu_j}{\sigma_j}$",
     "x_j = fitur ke-j; mu_j, sigma_j = rata-rata & simpangan baku dari data latih (dihitung hanya pada train agar tidak bocor)."),
    ("logit", r"$z=b+\mathbf{w}^{\top}\tilde{\mathbf{x}},\qquad p=\sigma(z)=\dfrac{1}{1+e^{-z}}$",
     "b = bias; w = vektor bobot; x~ = fitur terstandarisasi; z = log-odds; sigma = fungsi sigmoid; p = probabilitas lead konversi."),
    ("loss", r"$\mathcal{L}(\mathbf{w},b)=-\dfrac{1}{n}\sum_{i=1}^{n}\left[y_i\ln p_i+(1-y_i)\ln(1-p_i)\right]+\dfrac{\lambda}{2}\|\mathbf{w}\|^2$",
     "n = jumlah lead latih; y_i in {0,1} = won/lost; p_i = prediksi; lambda = kekuatan regularisasi L2 (0,01)."),
    ("grad", r"$\nabla_{\mathbf{w}}\mathcal{L}=\dfrac{1}{n}X^{\top}(\mathbf{p}-\mathbf{y})+\lambda\mathbf{w},\qquad \mathbf{w}\leftarrow\mathbf{w}-\eta\,\nabla_{\mathbf{w}}\mathcal{L}$",
     "X = matriks fitur (n x d); p, y = vektor prediksi & label; eta = learning rate (0,3); 1.500 iterasi gradient descent."),
    ("score", r"$\mathrm{score}=\mathrm{round}(100\,p)$@@$\mathrm{hot}:\ p\geq 0.5;\ \ \mathrm{warm}:\ 0.2\leq p<0.5;\ \ \mathrm{cold}:\ p<0.2$",
     "Skor 0-100 adalah probabilitas terkalibrasi (bukan poin sembarang). Ambang 0,5 dan 0,2 disesuaikan dengan base rate konversi ~19%."),
    ("metrics", r"$\mathrm{AUC}=P(s^{+}>s^{-})$@@$\mathrm{Prec}=\dfrac{TP}{TP+FP},\ \ \mathrm{Rec}=\dfrac{TP}{TP+FN},$@@$\mathrm{Lift}@k=\dfrac{\mathrm{konversi\ top\ k}}{\mathrm{konversi\ rata\ rata}}$",
     "s+ / s- = skor lead yang konversi / tidak; TP, FP, FN = true positive, false positive, false negative; k = 10% lead teratas."),
]

WORKED_TEXT = [
    "Langkah 1 - icp_fit (cosine). Centroid pelanggan won: mu = [0,5; 0,3; 0,1; 0,4; 0,5] (logistics, manufacturing, retail, size_z, title/3). "
    "Lead A = [1, 0, 0, 0,5, 0,67]: A.mu = 0,5+0,2+0,335 = 1,035; ||A|| = 1,303; ||mu|| = 0,872 -> cos = 1,035/(1,303 x 0,872) = "
    f"{W['cosine_icp']['A']:.3f}.",
    "Langkah 2 - skoring dengan bobot ilustrasi w = [0,9; 1,2; -0,02; 2,0], b = -3,0. Lead A: z = -3 + 0,9(3) + 1,2(1) - 0,02(5) + 2,0(0,911) = "
    f"{W['scoring']['A']['z']} -> p = 1/(1+e^-{W['scoring']['A']['z']}) = {W['scoring']['A']['p']} -> skor {W['scoring']['A']['score']} (hot).",
    f"Langkah 3 - umpan balik. Jika A benar-benar konversi (y=1): loss = -ln({W['scoring']['A']['p']}) = {W['logloss_A_if_y1']}; gradien bobot = (p - y) x = {W['grad_w']}; "
    f"dengan eta = 0,1 bobot menjadi {W['w_new']} (bobot pricing_views & demo naik, days_since menjadi kurang negatif).",
]

RELATED_PROBLEM = [
    ("González-Flores, L., Rubiano-Moreno, J., Sosa-Gómez, G. (2025). The relevance of lead prioritization: a B2B lead scoring model based on machine learning. Frontiers in Artificial Intelligence. DOI 10.3389/frai.2025.1554325.",
     "Studi kasus perusahaan software B2B (data lead Jan 2020 - Apr 2024); membandingkan 16 algoritma klasifikasi dan melaporkan Gradient Boosting paling unggul.",
     "https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1554325/full"),
    ("Wu, M., Andreev, P., Benyoucef, M. (2024). The state of lead scoring models and their impact on sales performance. Information Technology and Management, 25(1). DOI 10.1007/s10799-023-00388-w.",
     "Tinjauan pustaka sistematis 44 studi: model tradisional (berbasis pengalaman) vs prediktif (ML), dengan 14 metrik dampak ke kinerja penjualan.",
     "https://link.springer.com/article/10.1007/s10799-023-00388-w"),
    ("D'Haen, J., Van den Poel, D. (2013). Model-supported business-to-business prospect prediction based on an iterative customer acquisition framework. Industrial Marketing Management, 42(4), 544-551.",
     "Kerangka akuisisi pelanggan iteratif untuk memprediksi prospek B2B; dasar pendekatan 'prospect prediction' yang dipakai riset skoring berikutnya.",
     ""),
]
RELATED_AGENT = [
    ("Huang, K.-H., Prabhakar, A., Thorat, O., et al. (2025). CRMArena-Pro: Holistic Assessment of LLM Agents Across Diverse Business Scenarios and Interactions. arXiv:2505.18878 (Salesforce AI Research).",
     "Benchmark 22 tugas CRM (termasuk lead qualification). Agen LLM terbaik hanya ~58% sukses satu-giliran dan ~35% multi-giliran -> perlu komponen deterministik/ML & guardrail.",
     "https://arxiv.org/abs/2505.18878"),
    ("Dhanyamraju, H. R., Raghav, L., Lee, A. (2026). Autonomous Event-Driven Multi-Agent Orchestration for Enterprise AI at Scale. arXiv:2606.20058.",
     "Orkestrasi multi-agen event-driven untuk enrichment, pra-kualifikasi, dan penilaian kesiapan lead; dilaporkan mengurangi kerja manual ~70%.",
     "https://arxiv.org/abs/2606.20058"),
    ("Wu, Q., Bansal, G., Zhang, J., et al. (2023). AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. arXiv:2308.08155 (Microsoft Research).",
     "Kerangka multi-agen dengan agen tersepesialisasi yang saling berkomunikasi; dasar pola orchestrator + agen peran khusus.",
     "https://arxiv.org/abs/2308.08155"),
]
CITE_NOTE = ("Verifikasi: metadata dua makalah pertama tiap daftar dicek lewat pencarian web pada sesi pengerjaan; D'Haen & Van den Poel (2013) dan AutoGen "
             "ditulis dari pengetahuan penulis dan belum dibuka ulang - mohon dicek sebelum dikumpulkan.")

WHY_MAS = [
    ("Tugas heterogen", "Dedup/imputasi, kemiripan ICP, NLP teks, klasifikasi, dan aturan tindakan memakai teknik berbeda; satu agen monolit akan sulit diuji dan dirawat."),
    ("Modularitas & ablation", "Tiap agen dapat diganti/diuji terpisah (mis. ganti Logistic Regression dengan XGBoost tanpa menyentuh agen lain)."),
    ("Pemisahan tanggung jawab", "Agen deterministik (Enrichment, Action-rule) terpisah dari agen probabilistik (Scoring) sehingga audit & guardrail jelas - relevan dengan temuan CRMArena-Pro."),
    ("Skala & paralel", "Intent dan ICP-Fit tidak saling bergantung, dapat berjalan paralel per batch lead; orchestrator mengatur urutan dan retry."),
    ("Feedback loop", "Orchestrator memantau AUC pada hasil won/lost dan memicu retrain - perilaku agentik (memantau lingkungan, menyesuaikan diri)."),
]
WHY_NOT_SINGLE = ("Single agent cukup untuk fungsi sempit (mis. hanya menghitung skor). Namun alur 'lead mentah -> tindakan sales' melibatkan beberapa kompetensi dan "
                  "sumber data, jadi dipilih sistem multi-agen (kategori 'Multiple AI Agents' pada Dimensi 1, dengan elemen Agentic pada feedback loop).")

AGENTS = [
    ("Enrichment Agent", "Lead mentah (nama, perusahaan, atribut)", "Blocking key + TF-IDF trigram karakter, cosine similarity >= 0,60; imputasi median per industri", "Lead bersih tanpa duplikat, nilai lengkap", "Klasik ML / NLP (bukan DL)"),
    ("ICP-Fit Agent", "Lead bersih + histori won", "Vektor fitur (one-hot industri, ukuran, jabatan); centroid pelanggan won (dari data latih saja)", "icp_fit in [-1,1]", "Similarity search (unsupervised)"),
    ("Intent Agent", "Pesan lead, sumber, perilaku web", "TF-IDF uni+bigram vs prototipe 'niat beli'; skor sumber; log ukuran", "text_intent, source_score, fitur turunan", "NLP klasik (TF-IDF)"),
    ("Scoring Agent", "Matriks 10 fitur + label historis", "Standardisasi, Logistic Regression L2 (gradient descent), pemetaan skor & tier", "p_convert, skor 0-100, tier", "Supervised ML"),
    ("Action Agent", "Tier + sinyal (demo, pricing views)", "Tabel aturan next-best-action; hook opsional LLM untuk draf e-mail", "Rekomendasi tindakan + draf e-mail (opsional)", "Rule-based (+ LLM opsional)"),
    ("Orchestrator", "Semua keluaran agen, hasil won/lost baru", "Penjadwal urutan, blackboard (State), monitor drift AUC, trigger retrain, log", "Alur end-to-end & jejak audit", "Kontrol / orkestrasi"),
]
AGENT_HDR = ["Agen", "Input / percept", "Komponen internal", "Output", "Metode"]

METHOD = [
    "Sistem ini memakai kombinasi AI klasik + ML supervised, bukan Deep Learning. Alasan: (1) data tabular berukuran ~2 ribu baris - pada data tabular kecil, model linier/tree biasanya setara atau lebih baik daripada DL; "
    "(2) skor harus dapat dijelaskan ke tim sales (bobot per fitur pada gambar bobot), penting untuk kepercayaan dan audit; (3) biaya komputasi rendah, berjalan di CPU dalam detik.",
    f"Verifikasi implementasi: model numpy buatan sendiri menghasilkan AUC {R['auc_agent_model']:.3f} vs LogisticRegression scikit-learn {R['auc_sklearn_check']:.3f} pada data uji yang sama.",
    "DL/LLM ditempatkan hanya di tempat yang tepat: penulisan draf e-mail (Action Agent, opsional) dan pengayaan teks bila data pesan bertambah (mis. embedding BERT menggantikan TF-IDF). "
    "Rencana tahap berikut: bandingkan dengan Gradient Boosting/XGBoost (sesuai temuan González-Flores et al., 2025).",
]

RESULTS_ROWS = [
    ["Metrik (data uji, n=%d)" % R["n_test"], "Agen (LogReg)", "Baseline poin manual"],
    ["AUC", f"{R['auc_agent_model']:.3f}", f"{R['auc_manual_points_baseline']:.3f}"],
    ["Lift@10% teratas", f"{R['lift_top10pct']:.2f}x", f"{R['lift_top10pct_baseline']:.2f}x"],
    ["Precision / Recall @ p>=0,5", f"{R['at_0.5']['precision']:.2f} / {R['at_0.5']['recall']:.2f}", "-"],
    ["Precision / Recall @ p>=0,3", f"{R['at_0.3']['precision']:.2f} / {R['at_0.3']['recall']:.2f}", "-"],
    ["Konversi hot / warm / cold", f"{pct(tier['mean']['hot'])} / {pct(tier['mean']['warm'])} / {pct(tier['mean']['cold'])}", "-"],
]
RESULT_TEXT = [
    f"Pipeline membersihkan {R['n_raw']} -> {R['n_clean']} lead (61 duplikat dibuang untuk 60 duplikat yang disisipkan; {R['log'][0].split('imputed ')[1]}).",
    f"Lead 'hot' berkonversi {pct(tier['mean']['hot'])} vs {pct(tier['mean']['cold'])} untuk 'cold' (rata-rata {pct(R['base_rate'])}) - tier memisahkan peluang dengan jelas.",
    "Keterbatasan: data sintetis; recall pada ambang 0,5 rendah (0,38) sehingga ambang perlu disesuaikan dengan kapasitas sales; belum ada uji pada data nyata, dan belum diuji drift.",
]
NEXT = ["Tugas berikutnya: integrasi LLM untuk draf e-mail, perbandingan XGBoost, simulasi drift & retrain otomatis, dashboard ringkas.",
        "Bila memungkinkan: uji pada dataset lead publik agar hasil tidak bergantung pada data sintetis."]
