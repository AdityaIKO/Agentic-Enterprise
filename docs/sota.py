"""Verified SOTA references (14, all with DOI).  Verified through web search during the work session; quartile = estimate, check on scimagojr.com."""
# SOTA: setiap entri diverifikasi (judul, jurnal, volume/halaman, DOI) melalui pencarian web pada sesi pengerjaan.
# Kuartil = perkiraan SJR (Scimago) dari pengetahuan penulis; mohon dicek ulang di scimagojr.com sebelum pengumpulan.
# (id, kelompok, sitasi APA, jurnal, kuartil, DOI, temuan, celah/relevansi)
SOTA_ROWS = [
 ("Smith1980", "B", "Smith, R. G. (1980). The Contract Net Protocol: High-level communication and control in a distributed problem solver. IEEE Transactions on Computers, C-29(12), 1104-1113.",
  "IEEE Trans. Computers", "Q1", "10.1109/TC.1980.1675516",
  "Alokasi tugas terdesentralisasi: manajer mengumumkan tugas (CFP), kontraktor menawar, pemenang dipilih; dapat re-kontrak bila gagal.",
  "Dasar permintaan konfirmasi dan penawaran antara Procurement Agent dan pemasok utama atau cadangan, serta pemilihan carrier. Celah: tidak membahas lantai harga, persetujuan manusia, atau serangan injeksi; KCMAS menambahkannya."),
 ("Leitao2009", "B", "Leitão, P. (2009). Agent-based distributed manufacturing control: A state-of-the-art survey. Engineering Applications of Artificial Intelligence, 22(7), 979-991.",
  "Eng. Appl. Artif. Intell.", "Q1", "10.1016/j.engappai.2008.09.005",
  "Survei kontrol manufaktur berbasis agen: fleksibilitas dan reaksi terhadap gangguan, tetapi adopsi industri terbatas oleh integrasi dan validasi.",
  "Menjustifikasi peran-peran terpisah dan pendekatan hibrida. Celah: fokus satu pabrik; belum trader yang mengoordinasikan pemasok luar dengan kapasitas dan keandalan berubah."),
 ("Dorri2018", "B", "Dorri, A., Kanhere, S. S., & Jurdak, R. (2018). Multi-agent systems: A survey. IEEE Access, 6, 28573-28593.",
  "IEEE Access", "Q1", "10.1109/ACCESS.2018.2831228",
  "Survei definisi, fitur, komunikasi, tantangan (keamanan, skalabilitas, koordinasi) dan evaluasi MAS.",
  "Dasar kriteria evaluasi dan tantangan MAS (keamanan pesan, skala) yang diuji pada Bagian 8. Celah: survei umum, tanpa studi kasus ekspor UMKM."),
 ("Swaminathan1998", "B", "Swaminathan, J. M., Smith, S. F., & Sadeh, N. M. (1998). Modeling supply chain dynamics: A multiagent approach. Decision Sciences, 29(3), 607-632.",
  "Decision Sciences", "Q1", "10.1111/j.1540-5915.1998.tb01356.x",
  "Pustaka agen rantai pasok yang modular untuk memodelkan dinamika dan kebijakan pengendalian (simulasi).",
  "Mendukung pemodelan pemasok/pabrik/pengirim sebagai agen dalam simulasi. Celah: tidak membahas trader komoditas dengan markup, negosiasi terbatas, dan risiko injeksi pada masukan teks."),
 ("Jennings2001", "B", "Jennings, N. R., Faratin, P., Lomuscio, A. R., Parsons, S., Wooldridge, M. J., & Sierra, C. (2001). Automated negotiation: Prospects, methods and challenges. Group Decision and Negotiation, 10(2), 199-215.",
  "Group Decis. Negot.", "Q2", "10.1023/A:1008746126376",
  "Kerangka negosiasi otomatis (protokol, objek negosiasi, model keputusan agen) dan tantangannya.",
  "Dasar Quote & negotiation agent (tangga konsesi terbatas di bawah batas kebijakan). Celah: tanpa evaluasi bisnis; KCMAS mengukur win rate dan margin pada simulasi."),
 ("Wang2024", "B", "Wang, L., Ma, C., Feng, X., Zhang, Z., Yang, H., Zhang, J., ... Wen, J. (2024). A survey on large language model based autonomous agents. Frontiers of Computer Science, 18(6), 186345.",
  "Front. Comput. Sci.", "Q1", "10.1007/s11704-024-40231-1",
  "Kerangka terpadu agen berbasis LLM (profil, memori, perencanaan, aksi) dan aplikasi rekayasa/sosial.",
  "Dasar lapisan LLM opsional (hanya menulis ulang teks). Celah: kontrol dan keamanan aksi masih terbuka; KCMAS membatasi LLM dengan guardrail, angka dan klaim tetap berasal dari agen."),
 ("Russo2018", "B", "Russo, D. J., Van Roy, B., Kazerouni, A., Osband, I., & Wen, Z. (2018). A tutorial on Thompson sampling. Foundations and Trends in Machine Learning, 11(1), 1-96.",
  "Found. Trends Mach. Learn.", "Q1", "10.1561/2200000070",
  "Tutorial Thompson sampling: memilih aksi secara berurutan dengan menyeimbangkan eksploitasi dan eksplorasi, dengan contoh bandit dan aplikasi daring.",
  "Dasar Marketing & Ads Agent (pembagian anggaran iklan antar kanal). Celah: tutorial metode, bukan studi ekspor UMKM; laju kanal KrakaCoal belum diukur."),
 ("Nash1950", "B", "Nash, J. F. (1950). The bargaining problem. Econometrica, 18(2), 155-162.",
  "Econometrica", "Q1", "10.2307/1907266",
  "Solusi tawar-menawar yang memaksimalkan hasil kali surplus kedua pihak (aksioma Nash).",
  "Titik referensi harga sepakat pada negosiasi penjual-pembeli."),
 ("Hathikal2020", "A", "Hathikal, S., Chung, S. H., & Karczewski, M. (2020). Prediction of ocean import shipment lead time using machine learning methods. SN Applied Sciences, 2, 1272.",
  "SN Appl. Sci.", "Q2", "10.1007/s42452-020-2951-5",
  "Memprediksi lead time pengiriman laut dengan regresi logistik, pohon keputusan, SVM, Naive Bayes, k-NN untuk shipper, carrier, forwarder, consignee.",
  "Mendukung model klasik/explainable untuk risiko pengiriman (Risk Agent: regresi logistik roll-over). Celah: prediksi tunggal, tidak terhubung ke keputusan kontrak dan re-kontrak."),
 ("Lee2024", "A", "Lee, E., Kim, S., Kim, S., Jung, S., Kim, H., & Cha, M. (2024). Explainable product classification for customs. ACM Transactions on Intelligent Systems and Technology, 15(2), Art. 25.",
  "ACM Trans. Intell. Syst. Technol.", "Q1", "10.1145/3635158",
  "Model XAI untuk membantu petugas bea cukai menetapkan subheading HS (top-3 akurasi 93,9% pada 925 subheading sulit) dengan penjelasan yang dapat dibaca.",
  "Dasar Compliance Agent (klasifikasi teks HS dengan confidence dan eskalasi). Celah: alat bantu petugas bea cukai, bukan bagian dari alur ekspor UMKM yang otomatis."),
 ("Ivanov2021", "A", "Ivanov, D., & Dolgui, A. (2021). A digital supply chain twin for managing the disruption risks and resilience in the era of Industry 4.0. Production Planning & Control, 32(9), 775-788.",
  "Prod. Plan. Control", "Q1", "10.1080/09537287.2020.1768450",
  "Konsep digital supply chain twin: model komputasi yang merepresentasikan keadaan jaringan waktu-nyata untuk mengelola gangguan dan ketahanan.",
  "Mendukung pendekatan simulasi digital twin sebagai lingkungan uji (Bagian 8). Celah: level jaringan besar; tidak menyentuh trader UMKM dan negosiasi harga terbatas."),
 ("Ouelhadj2009", "A", "Ouelhadj, D., & Petrovic, S. (2009). A survey of dynamic scheduling in manufacturing systems. Journal of Scheduling, 12(4), 417-431.",
  "J. Scheduling", "Q2", "10.1007/s10951-008-0090-8",
  "Tinjauan penjadwalan dinamis (heuristik, meta-heuristik, sistem multi-agen) saat terjadi gangguan seperti kerusakan mesin dan order mendadak.",
  "Dasar pemulihan reaktif saat pemasok gagal (penjadwalan ulang, pemasok cadangan). Celah: tidak membahas trader yang tidak memiliki pabrik."),
 ("Dominguez2020", "A", "Dominguez, R., & Cannella, S. (2020). Insights on multi-agent systems applications for supply chain management. Sustainability, 12(5), 1935.",
  "Sustainability", "Q1", "10.3390/su12051935",
  "Tinjauan sistematis penerapan MAS pada rantai pasok: penjadwalan, koordinasi antarperusahaan, pemenuhan order, seleksi pemasok, ketahanan.",
  "Memetakan ruang riset; menunjukkan kebutuhan validasi MAS pada konteks UMKM ekspor. Celah: sedikit studi dengan kalibrasi pada bisnis nyata."),
 ("Pergelova2019", "A", "Pergelova, A., Manolova, T., Simeonova-Ganeva, R., & Yordanova, D. (2019). Democratizing entrepreneurship? Digital technologies and the internationalization of female-led SMEs. Journal of Small Business Management, 57(1), 14-39.",
  "J. Small Bus. Manage.", "Q1", "10.1111/jsbm.12494",
  "Kapabilitas digital meningkatkan internasionalisasi (ekspor) UMKM di pasar berkembang.",
  "Motivasi bisnis: teknologi digital (termasuk pemasaran digital) menurunkan hambatan ekspor UMKM. Celah: studi survei; tidak menawarkan mekanisme koordinasi operasional."),
]
SOTA_BY = {r[0]: r for r in SOTA_ROWS}
def doi_url(d): return "https://doi.org/" + d
def sota_rel(ids): return [(SOTA_BY[i][2] + " doi:" + SOTA_BY[i][5], SOTA_BY[i][6], SOTA_BY[i][7], doi_url(SOTA_BY[i][5])) for i in ids]
# Tugas 1 meminta tiga penelitian serupa (topik) dan tiga penelitian agen cerdas
RELATED_PROBLEM = sota_rel(["Hathikal2020", "Lee2024", "Ivanov2021"])
RELATED_AGENT = sota_rel(["Smith1980", "Leitao2009", "Wang2024"])
SOTA_TABLE = [["Referensi (APA)", "Jurnal / kuartil*", "DOI", "Temuan dan celah terhadap KCMAS"]] + [
    [r[2], f"{r[3]} ({r[4]})", r[5], r[6] + " Celah/relevansi: " + r[7]] for r in SOTA_ROWS]
CITE_NOTE = ("Verifikasi: judul, jurnal, volume/halaman, dan DOI seluruh 14 referensi dicek melalui pencarian web pada sesi pengerjaan (penelusuran DOI langsung ke Crossref diblokir dari lingkungan kerja). "
             "*Kuartil adalah perkiraan berdasarkan SJR (Scimago) dari pengetahuan penulis, bukan hasil pengecekan langsung; mohon diverifikasi di scimagojr.com untuk tahun terbitan yang relevan sebelum pengumpulan. "
             "Hathikal dkk. terbit di SN Applied Sciences (kini Discover Applied Sciences).")
SOTA_GAP = [
    "Celah 1: literatur MAS manufaktur/rantai pasok (Leitão, 2009; Swaminathan dkk., 1998; Dominguez dkk., 2020) berfokus pada pabrik atau jaringan perusahaan besar; konsolidasi puluhan UMKM dengan kapasitas yang berubah dan tanpa data terpusat belum divalidasi secara kuantitatif.",
    "Celah 2: nilai desentralisasi biasanya diklaim, bukan diukur; KCMAS mengisolasi nilainya (bid live vs registry usang) dengan aturan keputusan yang sama pada agen tunggal dan multi-agen, sehingga selisih hanya berasal dari arsitektur.",
    "Celah 3: model ML logistik ekspor (Hathikal dkk., 2020; Lee dkk., 2024) berdiri sendiri; KCMAS menanamkannya sebagai komponen agen (Risk dan Compliance) yang memicu tindakan (re-kontrak, eskalasi ke manusia, pilihan carrier).",
    "Celah 4: adopsi LLM pada agen (Wang dkk., 2024) belum disertai kontrol aksi yang dapat diaudit; KCMAS membatasi LLM dengan guardrail, otonomi berlevel, dan audit log berantai-hash.",
    "Celah 5: bukti pada bisnis nyata kecil; kasus dikalibrasi dari klaim operasional KrakaCoal (MOQ, lead time, packing) sehingga hasilnya dekat dengan praktik ekspor arang.",
]

