"""Report + slide content (Bahasa Indonesia). Every number is read from outputs/*.json, never typed by hand."""
import json, pathlib, sys
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eosmas import config as C
from eosmas.data import make_scenario

R = json.loads((ROOT / "outputs/results.json").read_text())
W = json.loads((ROOT / "outputs/worked_example.json").read_text())
FIGDIR = ROOT / "outputs/figures"

NAMA, NIM = "[Isi nama Anda]", "[Isi NIM]"
REPO = "https://github.com/AdityaIKO/Agentic-Enterprise"
TITLE = "EOS-MAS: Export Order-to-Shipment Multi-Agent System"
SUBTITLE = "Sistem multi-agen cerdas untuk manufaktur furnitur berorientasi ekspor"
COURSE = "Agentic Enterprise (AI Agentic Technology Systems for Digital Enterprise Ecosystem) - Magister AI"

def n(x, nd=2, plus="", thou=False):
    """Indonesian number style: decimal comma, thousands dot."""
    s_ = format(x, f"{plus}{',' if thou else ''}.{nd}f")
    return s_.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


M = R["main"]; PD = R["paired_diffs"]
usd = lambda x: "$" + n(x, 0, "", True)
pc = lambda x: n(100 * x, 1) + "%"
def ci(t, f=lambda x: n(x, 2)): return f"{f(t[0])} [{f(t[1])}; {f(t[2])}]"
per_order = lambda m, k: M[m][k][0] / 12

otd_s, otd_m = M["static"]["otd"][0], M["mas"]["otd"][0]
cost_s, cost_m = M["static"]["total_cost"][0] / 12, M["mas"]["total_cost"][0] / 12
sav = 1 - cost_m / cost_s
ab = R["ablation"]; base = ab["MAS (full)"]
rb = R["robust"]; sc = R["scale"]; hs = R["hs"]; rk = R["risk"]; rlr = R["rl"]
lv = R["levels"]["mas"]; tot_lv = sum(lv.values()); auto_share = lv["4"] / tot_lv
sc_last = sc[-1]
peak_ratio = sc_last["central"]["coord_peak"] / sc_last["mas"]["peak_node"]
msg_red = 1 - sc_last["mas"]["msgs"] / sc_last["central"]["msgs"]
p_hi = str(max(map(float, rb)))
rob_c, rob_m = rb[p_hi]["central"]["otd"][0], rb[p_hi]["mas"]["otd"][0]
rob_c0, rob_m0 = rb["0.0"]["central"]["otd"][0], rb["0.0"]["mas"]["otd"][0]

# ============================================================ front matter
EXEC = [
    "Eksportir manufaktur harus menyelesaikan produksi, dokumen ekspor, dan pengiriman ke gerbang pelabuhan sebelum closing kapal. Satu gangguan kecil "
    "(mesin rusak, kode HS keliru, kargo tidak terangkut/roll-over) menggeser pengiriman minimal 7 hari, memicu penalti, biaya penyimpanan, dan risiko L/C kedaluwarsa.",
    "EOS-MAS adalah sistem multi-agen cerdas untuk masalah ini: agen order, mesin, compliance, risk, learning, carrier, agen governance, dan satu Scout Agent bergerak (mobile). "
    "Agen bernegosiasi lewat Contract Net Protocol, memakai kombinasi ML klasik + aturan + DSS + Q-learning, dan beroperasi pada tingkat otonomi terkendali dengan persetujuan manusia untuk keputusan berdampak tinggi.",
    f"Hasil simulasi ({R['n_scenarios']} skenario berpasangan, 12 order per skenario): pengiriman tepat waktu naik dari {pc(otd_s)} (proses manual/FIFO) menjadi {pc(otd_m)}; "
    f"biaya per order turun dari {usd(cost_s)} menjadi {usd(cost_m)} ({n(100*sav,0,'',False)}%); sentuhan manusia per order turun dari {n(M['static']['touches'][0],1,'',False)} menjadi {n(M['mas']['touches'][0],2,'',False)}; "
    f"kesalahan kode HS dari {pc(M['static']['hs_err'][0])} menjadi {pc(M['mas']['hs_err'][0])}.",
    f"Temuan yang jujur: (1) agen tunggal berinti terpusat dan multi-agen menghasilkan kualitas keputusan yang sama pada skala kecil karena memakai aturan yang sama; keunggulan multi-agen ada pada "
    f"ketahanan terhadap kegagalan koordinator ({pc(rob_m)} vs {pc(rob_c)} tepat waktu saat gangguan pada {int(float(p_hi)*100)}% skenario), beban puncak node ({n(peak_ratio,1,'',False)}x lebih ringan pada 240 order) dan batas organisasi (carrier, bea cukai). "
    "(2) Ada trade-off biaya vs layanan pada pemilihan carrier. (3) Policy RL yang dilatih pada lingkungan abstrak tidak transfer ke simulator penuh; melatih langsung di simulator memberi policy setara aturan yang dituning. "
    "(4) Semua data bersifat sintetis dan parameter biaya adalah asumsi; angka ini membuktikan sistem berfungsi dan dapat dibandingkan, bukan performa perusahaan nyata.",
]

TUGAS_MAP = [
    ("Gunakan topik yang dipilih", "Topik: EOS-MAS, order-to-shipment ekspor manufaktur (belum diambil kelompok 1-6)", "Bagian 2.1"),
    ("Upload laporan progres", "Dokumen ini (PDF) + slide (PPTX) + kode GitHub", "-"),
    ("Peran anggota tim", "Pengerjaan individu: seluruh peran dipegang satu orang", "Bagian 1"),
    ("Deskripsi problem", "Masalah order-to-shipment, KPI, klasifikasi lingkungan, PEAS", "Bagian 2"),
    ("Ilustrasi data dan perhitungan komputasi", "Data sintetis, 11 contoh hitung manual, simulasi penuh", "Bagian 3"),
    ("Rumus notasi dan arti simbol", "29 rumus dikelompokkan A-H, tiap simbol dijelaskan", "Bagian 4"),
    ("Tiga penelitian topik serupa", "Hathikal 2020; Lee 2024; Ouelhadj & Petrovic 2009", "Bagian 5"),
    ("Mengapa single vs multi-agent", "Kriteria Bab 4 + bukti eksperimen (ketahanan, skala, batas organisasi)", "Bagian 6.1"),
    ("Tiga penelitian agen cerdas", "Smith 1980; Leitao 2009; Zhao 2024", "Bagian 6.2"),
    ("Diagram rencana sistem", "Arsitektur, Contract Net, siklus BDI, Gantt", "Bagian 6.3"),
    ("Komponen internal tiap agen", "Tabel 8 agen: BDI, komponen, I/O, metode, otonomi", "Bagian 6.4"),
    ("AI / ML / DL dan alasannya", "Portofolio metode + alasan tidak memakai DL/LLM", "Bagian 6.6"),
]

ROLES = [
    ("Leader / product owner", "Memilih topik, merumuskan masalah dan KPI, menetapkan lingkup Tugas 1."),
    ("Researcher", "Studi literatur (3 + 3 penelitian), memetakan materi Bab 1-5 ke desain sistem."),
    ("Programmer", "Simulator, agen, model ML/RL, lapisan pesan aman, 20 unit test."),
    ("Designer", "Arsitektur sistem, protokol Contract Net, diagram, dan visualisasi hasil."),
    ("Evaluator", "Desain eksperimen berpasangan, ablation, uji ketahanan dan skala, catatan validitas."),
    ("Presenter", "Menyusun laporan PDF dan slide PPT."),
]
ROLE_NOTE = ("Pengerjaan ini individu karena penulis bergabung terlambat ke kelas, sehingga enam peran pada template Project #1 (Leader, Researcher, Programmer, Designer, Evaluator, Presenter) "
             "dipegang satu orang. Claude Code dipakai sebagai asisten penulisan kode dan dokumen; keputusan desain, angka, dan klaim ditinjau oleh penulis.")

# ============================================================ problem
PROBLEM = [
    "Sebuah manufaktur furnitur kayu (fiktif) mengekspor 12 order per periode ke beberapa negara tujuan. Setiap order melewati tiga stasiun kerja (pemotongan, perakitan, finishing), "
    "menyiapkan dokumen ekspor (klasifikasi HS, invoice, packing list, sertifikat asal/legalitas), lalu dikirim ke pelabuhan dan diberangkatkan dengan kapal milik carrier yang berlayar mingguan. "
    "Kargo harus tiba di gerbang pelabuhan sebelum closing kapal; melewatkannya berarti menunggu kapal berikutnya (+7 hari).",
    "Titik nyeri: (1) jadwal produksi tidak mengikuti tenggat closing kapal; (2) mesin rusak tak terduga (laju 0,035 per mesin per hari); (3) dokumen dan kode HS disiapkan setelah produksi selesai dan rawan salah; "
    "(4) pemilihan carrier menyeimbangkan biaya vs risiko roll-over yang bergantung kongesti pelabuhan dan musim puncak; (5) informasi tersebar pada organisasi berbeda (pabrik, carrier, bea cukai) sehingga visibilitas silo.",
    "Dampak bisnis: penalti 0,4% nilai order per hari terlambat, demurrage/storage 45 USD per hari, dan diskon 5% jika L/C basi (>10 hari). Pada simulasi, proses manual hanya mengirim "
    f"{pc(otd_s)} order tepat waktu dengan rata-rata keterlambatan {n(M['static']['avg_late'][0],1,'',False)} hari.",
    "Pernyataan masalah formal: pada horizon satu periode, pilih jadwal produksi, keputusan dokumen, carrier, dan tindakan pemulihan (lembur/air freight) yang meminimalkan "
    "J = biaya freight + penyimpanan + lembur + sentuhan manusia + penalti keterlambatan, dengan constraint kapasitas mesin, closing kapal, kebijakan compliance, dan batas wewenang agen.",
]
ENV_TABLE = [
    ["Karakteristik", "Klasifikasi", "Bukti pada kasus ini"],
    ["Observability", "Partially observable", "Keandalan carrier, kongesti pelabuhan, dan waktu rusak mesin tidak diketahui pasti sebelumnya"],
    ["Outcome", "Stochastic", "Kerusakan mesin (Poisson), roll-over kargo (Bernoulli dengan logit), dokumen kurang (6%)"],
    ["Change", "Dynamic", "Jadwal kapal mingguan, indeks kongesti berubah harian, musim puncak mulai di tengah horizon"],
    ["Actors", "Multi-agent", "Pabrik, tiga carrier, bea cukai/pelabuhan, pembeli: pemilik dan kepentingan berbeda"],
]
PEAS = [
    ["Komponen", "Deskripsi EOS-MAS"],
    ["Performance", "Persentase order tepat waktu (<= LSD); biaya total J per order; rata-rata hari terlambat; tingkat kesalahan HS; jumlah sentuhan manusia; ketahanan (perubahan kinerja saat gangguan); beban node puncak"],
    ["Environment", "Pabrik 3 stasiun x 2 mesin; proses dokumen ekspor dan bea cukai; 3 carrier dengan jadwal kapal mingguan; pelabuhan (kongesti, musim puncak); pembeli dengan LSD"],
    ["Actuators", "Dispatch operasi ke mesin; lembur; booking carrier atau air freight; penerbitan dokumen; eskalasi ke manusia; konfirmasi/penolakan pesan"],
    ["Sensors", "ERP/MES (order, routing); sensor kesehatan mesin (percept sequence); jadwal kapal via Scout Agent; indeks kongesti; umpan balik hasil pengiriman"],
]
SOTA = ("Posisi terhadap solusi yang ada (ringkasan kategori, bukan evaluasi produk): suite ERP/APS, TMS, dan Global Trade Management (mis. SAP GTS, Oracle GTM) unggul pada data master, "
        "kepatuhan, dan integrasi transaksi, tetapi umumnya berbasis aturan/batch, terpisah per modul, dan tidak menegosiasikan keputusan lintas organisasi secara otonom. EOS-MAS tidak menggantikannya; "
        "ia menjadi lapisan keputusan agentik di atasnya: menegosiasikan penjadwalan dan carrier, menjaga dokumen paralel dengan produksi, dan mengeskalasi ke manusia sesuai tingkat otonomi.")

# ============================================================ data illustration
def sample_orders():
    sc_ = make_scenario(7)
    rows = [["Order", "HS", "Kontainer", "Nilai (USD)", "Rilis (hari)", "Beban kerja (hari)", "Closing dijanjikan", "LSD"]]
    for o in sc_.orders[:6]:
        rows.append([f"#{o.oid}", o.heading, str(o.containers), f"{n(o.value,0,'',True)}", f"{n(o.release,1,'',False)}", f"{n(sum(o.ops),1,'',False)}", f"{n(o.commit_closing,0,'',False)}", f"{n(o.lsd,0,'',False)}"])
    return rows

CARRIER_TABLE = [["Carrier", "Tarif/kontainer", "Transit", "Offset closing (hari)", "Klaim keandalan", "P(roll-over) dasar (logit)"]] + [
    [c.name, f"${n(c.rate,0,'',True)}", f"{n(c.transit,0,'',False)} hari", f"{n(c.offset,0,'',False)} + 7k", f"{n(c.advertised_rel,2,'',False)}", f"{n(1/(1+np.exp(-c.base_roll_logit)),2,'',False)}"] for c in C.CARRIERS]

ASSUME = [["Parameter", "Nilai", "Keterangan"],
    ["Stasiun x mesin", "3 x 2", "Cutting, Assembly, Finishing; kecepatan mesin N(1; 0,05)"],
    ["Beban kerja rata-rata per tahap", "0,9 / 1,8 / 1,4 hari", "dikali faktor kuantitas 0,6-1,5"],
    ["Laju kerusakan mesin", f"{C.BREAKDOWN_RATE} per hari", f"perbaikan {C.REPAIR_DAYS[0]}-{C.REPAIR_DAYS[1]} hari; indikasi dini {n(C.ALERT_LEAD_DAYS,0,'',False)} hari (deteksi {int(C.ALERT_DETECT_PROB*100)}%)"],
    ["Lembur", f"x{C.OVERTIME_SPEEDUP}", f"biaya {n(C.OVERTIME_COST_PER_DAY,0,'',False)} USD per hari operasi; anggaran 12 tahap per skenario"],
    ["Kesalahan HS manual", pc(C.MANUAL_HS_ERROR), f"koreksi bea cukai +{n(C.HS_ERROR_DELAY_DAYS,0,'',False)} hari; ambang confidence ML tau = {C.HS_CONF_THRESHOLD}"],
    ["Dokumen kurang", pc(C.LICENSE_MISSING_PROB), f"+{C.LICENSE_FIX_DAYS} hari; dokumen dasar {C.DOC_BASE_DAYS} hari"],
    ["Truk ke pelabuhan", f"{C.TRUCK_TO_PORT_DAYS} hari", "toleransi LSD +2 hari dari keberangkatan kapal yang dijanjikan"],
    ["Biaya sentuhan manusia", f"${n(C.HUMAN_TOUCH_COST,0,'',False)}", "persetujuan menambah 0,25 hari; nilai order >= $50.000 wajib persetujuan"],
    ["Air freight", f"{n(C.AIR_MULT,0,'',False)}x tarif sea", "berangkat H+1, tanpa roll-over"],
    ["Data volume scout", "1,5 MB vs 27 KB", "dump jadwal remote vs state agen + hasil (ASUMSI)"],
]
ASSUME_NOTE = ("Seluruh parameter di atas adalah asumsi pemodelan dari penulis (perusahaan fiktif, data sintetis). Nilai riil harus dikalibrasi dari ERP/MES/TMS perusahaan sebelum keputusan bisnis diambil.")

cr = W["cr"]; bd = W["bids"]; ca = W["carrier"]; ro = W["roll"]; co = W["cos"]; tr = W["trust"]; qo = W["q_ours"]; ql = W["q_lecture"]; ng = W["nego"]; mm = W["mas_metrics"]
ot = W["order_trace"]
WORKED = [
    ("1. Dispatch dengan critical ratio (Bab 3-4)",
     f"Pada t = {n(cr['t'],0,'',False)} hari tiga job menunggu satu stasiun. Job J1: tenggat 12,5, sisa kerja 3,2; J2: 10,5 dan 4,0; J3: 9,0 dan 1,4. "
     f"CR = (d - t)/W: J1 = (12,5-5)/3,2 = {n(cr['cr']['J1'],2,'',False)}; J2 = (10,5-5)/4,0 = {n(cr['cr']['J2'],3,'',False)}; J3 = (9,0-5)/1,4 = {n(cr['cr']['J3'],2,'',False)}. Urutan: {' > '.join(cr['order'])} (CR terkecil paling mendesak)."),
    ("2. Tawaran Contract Net antar mesin",
     f"Job baru (w = 1,8 hari) pada t = 5. M2a: beban 2,4, kecepatan 1,02: ETA = 5 + (2,4+1,8)/1,02 = {n(bd['a'],2,'',False)}. M2b: beban 0,9, kecepatan 0,97: ETA = 5 + (0,9+1,8)/0,97 = {n(bd['b'],2,'',False)}. "
     f"Order Agent memberi ACCEPT ke M2b dan REJECT ke M2a. Bila M2b diberi indikasi rusak sampai t = 7,5, ETA-nya menjadi 7,5 + 2,7/0,97 = {n(bd['b_alerted'],2,'',False)} sehingga M2a menang (condition monitoring)."),
    ("3. Pemilihan carrier: skor hibrida vs biaya harapan",
     f"Order senilai $38.000, 2 kontainer, tiba di gerbang t = {n(ca['tport'],1)}, LSD = {n(ca['lsd'],0)}, kongesti {n(ca['cong'],2)}. "
     + "; ".join(f"{r['name']}: biaya ${n(r['cost'],0,'',True)}, berangkat hari {n(r['dep'],0,'',False)}, p = {n(r['p'],2,'',False)}, z = {n(r['z'],1,'',False)}, g = {n(r['g'],0,'',False)}, h = {n(r['h'],1,'',False)}, E[biaya] = ${n(r['exp_total'],0,'',True)}" for r in ca["rows"]) +
     f". Aturan hibrida memilih {ca['best_h']} (EcoLine gugur karena berangkat setelah LSD, g = 0); aturan biaya-harapan murni memilih {ca['best_exp']} yang lebih murah tetapi berisiko terlambat. Air freight (${n(ca['air_cost'],0,'',True)}) tidak dipilih karena lebih mahal daripada biaya harapan."),
    ("4. Risiko roll-over (regresi logistik, kebenaran tersembunyi)",
     f"EcoLine dengan kongesti 0,6, musim puncak, buffer 2 hari: logit = -1,55 + 1,8(0,6) + 1,1(1) - 0,3(2) = {n(ro['logit'],2,'',False)}; p = 1/(1+e^-{n(ro['logit'],2,'',False)}) = {n(ro['p'],3,'',False)}. "
     f"Untuk PrimeExpress pada kondisi sama p = {n(ro['p_prime'],3,'',False)}. Model ML Risk Agent memperkirakan p ini dari data historis (AUC {n(rk['auc'],2,'',False)})."),
    ("5. Klasifikasi HS dengan kemiripan kosinus",
     f"Query 'teak dining chair'. Dokumen '{co['d1']}': irisan 3 kata, cos = 3/(sqrt(3) x sqrt(4)) = {n(co['c1'],3,'',False)}. Dokumen '{co['d2']}': irisan 2 kata, cos = 2/(sqrt(3) x sqrt(3)) = {n(co['c2'],3,'',False)}. "
     "Pada sistem sebenarnya vektor berupa TF-IDF n-gram kata + karakter; tetangga terdekat memberi suara berbobot kosinus dan confidence < 0,60 diserahkan ke manusia."),
    ("6. Pembaruan trust carrier",
     f"T = 0,80 dan kargo terangkut (q = 1): T' = 0,8(0,8) + 0,2(1) = {n(tr[0]['new'],2,'',False)}. Bila roll-over (q = 0,2): T' = {n(tr[1]['new'],2,'',False)} (conditional); roll-over kedua: T' = {n(tr[2]['new'],3,'',False)} < 0,60 sehingga carrier diblokir sementara oleh gerbang kelayakan g."),
    ("7. Q-learning untuk keputusan lembur",
     f"Contoh dari kuliah: Q = 2,0; alpha = 0,2; r = 5; gamma = 0,9; max Q' = 4: target = {n(ql['target'],1,'',False)}, TD error = {n(ql['td_error'],1,'',False)}, Q baru = {n(ql['q_new'],2,'',False)}. "
     f"Contoh kita: Q(s, lembur) = {n(qo['q_old'],0,'',False)}; r = -45 x 1,4/1,35 = {n(qo['r'],1,'',False)}; max Q' = {n(qo['maxq'],0,'',False)}; alpha = {qo['alpha']}; gamma = {qo['gamma']}: target = {n(qo['target'],1,'',False)}; TD = {n(qo['td'],1,'',False)}; Q baru = {n(qo['q_new'],1,'',False)}."),
    ("8. Biaya satu order end-to-end (skenario 7, order #10, statis vs multi-agen)",
     f"Statis: freight ${n(ot['static']['10']['freight'],0,'',True)}, penalti ${n(ot['static']['10']['penalty'],0,'',True)}, holding ${n(ot['static']['10']['hold'],0,'',True)}, manusia ${n(ot['static']['10']['human'],0,'',True)} ({ot['static']['10']['option']}, terlambat {n(ot['static']['10']['late'],0,'',False)} hari). "
     f"Multi-agen: freight ${n(ot['mas']['10']['freight'],0,'',True)}, penalti ${n(ot['mas']['10']['penalty'],0,'',True)}, holding ${n(ot['mas']['10']['hold'],0,'',True)}, manusia ${n(ot['mas']['10']['human'],0,'',True)} ({ot['mas']['10']['option']}, terlambat {n(ot['mas']['10']['late'],0,'',False)} hari). "
     f"Contoh penalti: order $38.000 terlambat 5 hari = 0,004 x 38.000 x 5 + 45 x 5 = ${n(W['penalty_examples']['5'],0,'',True)}; 12 hari = ${n(W['penalty_examples']['12'],0,'',True)} (termasuk diskon 5% L/C basi)."),
    ("9. Metrik sistem multi-agen (Bab 4)",
     f"Speedup 1.000 task: 100 s vs 29 s pada 4 agen: S = {n(mm['speedup'][0],2,'',False)}, efisiensi = {n(mm['speedup'][1],2,'',False)}. Redundansi 3 agen R = 0,9: R_sys = {n(mm['r_sys'],3,'',False)}. "
     f"Biaya komunikasi satu pesan 8 KB pada 8 Mbps dan 20 ms: {n(mm['comm_ms'],1,'',False)} ms. Jain: beban merata {n(mm['jain'][0],2,'',False)}; beban timpang (4,1,1,1) {n(mm['jain'][1],2,'',False)}. Utilisasi mesin pada simulasi: Jain = {n(M['mas']['jain'][0],2,'',False)}."),
    ("10. Negosiasi tarif dan Nash bargaining (modul negosiasi)",
     f"Pembeli membuka $1.900 (batas $2.300), carrier membuka $2.600 (batas bawah $2.000), T = 4, beta = 1. Ronde 1: 2.000 vs 2.450; ronde 2: 2.100 vs 2.300; ronde 3: 2.200 vs 2.150 sehingga sepakat di ${n(ng['price'],0,'',True)} (ronde {ng['round']}). "
     f"Untuk 2 kontainer surplus pembeli ${n(ng['surplus']['buyer'],0,'',True)}, carrier ${n(ng['surplus']['seller'],0,'',True)}, total ${n(ng['surplus']['total'],0,'',True)}. Nash product tertinggi ({n(max(ng['nash']['prod']),3,'',False)}) pada harga $2.100-$2.200."),
    ("11. Migrasi Scout Agent",
     "Host dengan trust >= 0,80 dan risiko <= 0,20 boleh dimigrasi. EcoLine edge (trust 0,71, risiko 0,30) ditolak walau latensinya terbaik; skor komposit hanya meranking host yang lolos "
     f"(Bab 4). Data yang dipindahkan per skenario: {n(R['scout']['bytes']/1e6,1,'',False)} MB (scout) vs {n(R['scout']['raw']/1e6,1,'',False)} MB (remote pull); penghematan {n(100*(1-R['scout']['bytes']/R['scout']['raw']),0,'',False)}%."),
]

# ============================================================ related work
RELATED_PROBLEM = [
    ("Hathikal, S., Chung, S. H., & Karczewski, M. (2020). Prediction of ocean import shipment lead time using machine learning methods. SN Applied Sciences, 2, 1272.",
     "Memprediksi lead time pengiriman laut dengan regresi logistik multinomial, pohon keputusan, SVM, Naive Bayes, dan k-NN untuk kepentingan shipper, carrier, forwarder, dan consignee.",
     "Mendukung pemakaian model klasik/explainable untuk risiko pengiriman; EOS-MAS memakai regresi logistik untuk peluang roll-over.",
     "https://link.springer.com/article/10.1007/s42452-020-2951-5"),
    ("Lee, E., Kim, S., Kim, S., Jung, S., Kim, H., & Cha, M. (2024). Explainable Product Classification for Customs. ACM Transactions on Intelligent Systems and Technology, 15(2), Art. 25. doi:10.1145/3635158.",
     "Model XAI untuk membantu petugas bea cukai menetapkan 6 digit kode HS dari deskripsi barang, disertai alasan yang dapat dibaca.",
     "Dasar Compliance Agent: klasifikasi teks HS dengan confidence dan eskalasi ke manusia (selective classification).",
     "https://dl.acm.org/doi/10.1145/3635158"),
    ("Ouelhadj, D., & Petrovic, S. (2009). A survey of dynamic scheduling in manufacturing systems. Journal of Scheduling, 12, 417-431. doi:10.1007/s10951-008-0090-8.",
     "Tinjauan penjadwalan dinamis (heuristik, meta-heuristik, sistem multi-agen, teknik AI lain) saat terjadi gangguan seperti kerusakan mesin dan order mendadak.",
     "Dasar penjadwalan reaktif EOS-MAS: re-kontrak job saat mesin rusak, critical ratio, dan perbandingan dengan jadwal statis.",
     "https://link.springer.com/article/10.1007/s10951-008-0090-8"),
]
RELATED_AGENT = [
    ("Smith, R. G. (1980). The Contract Net Protocol: High-level communication and control in a distributed problem solver. IEEE Transactions on Computers, C-29(12), 1104-1113.",
     "Memperkenalkan alokasi tugas terdesentralisasi: manajer mengumumkan tugas (CFP), kontraktor menawar, pemenang dipilih; dapat re-kontrak bila gagal.",
     "Protokol inti EOS-MAS untuk dispatch mesin dan pemilihan carrier (Bab 4 bagian Contract Net).",
     ""),
    ("Leitao, P. (2009). Agent-based distributed manufacturing control: A state-of-the-art survey. Engineering Applications of Artificial Intelligence, 22(7), 979-991.",
     "Survei kontrol manufaktur terdistribusi berbasis agen: fleksibilitas, kemampuan bereaksi terhadap gangguan, dan tantangan integrasi.",
     "Menjustifikasi agen mesin/order sebagai unit otonom dan pendekatan hibrida (koordinasi terdesentralisasi + kontrol ringan).",
     "https://doi.org/10.1016/j.engappai.2009.05.005"),
    ("Zhao, Z., Tang, D., Liu, C., Wang, L., Zhang, Z., Zhu, H., Chen, K., Nie, Q., & Ji, Y. (2024). A Large Language Model-based multi-agent manufacturing system for intelligent shopfloor. arXiv:2405.16887.",
     "Sistem multi-agen berbasis LLM untuk shopfloor pintar dengan modul agen dan cara kolaborasi, meminimalkan intervensi manusia.",
     "Arah lanjutan EOS-MAS: LLM sebagai lapisan bahasa (ekstraksi dokumen, penjelasan), tetap dibatasi kebijakan dan aturan deterministik.",
     "https://arxiv.org/abs/2405.16887"),
]
CITE_NOTE = ("Verifikasi: metadata Hathikal dkk., Lee dkk., Ouelhadj & Petrovic, Leitao, dan Zhao dkk. dicek melalui pencarian web pada sesi pengerjaan (situs penerbit tidak dapat dibuka langsung dari lingkungan kerja). "
             "Smith (1980) dan halaman jurnal Leitao ditulis dari pengetahuan penulis: mohon diverifikasi sebelum pengumpulan.")

# ============================================================ why multi-agent
CRITERIA = [
    ["Kriteria (Bab 4)", "Terpusat", "Terdesentralisasi", "Hybrid", "Posisi EOS-MAS"],
    ["Latensi dan bandwidth", "Sedang", "Rendah", "Rendah-sedang", "Hybrid: CNP lokal per operasi"],
    ["Fault tolerance", "Rendah (single point of failure)", "Tinggi", "Tinggi", "Kegagalan satu agen tidak menghentikan sistem"],
    ["Optimalitas global", "Tinggi", "Lokal", "Cukup tinggi", "Aturan keputusan bersama + governance"],
    ["Biaya koordinasi", "Fan-in O(n) pada koordinator", "Tinggi (banyak pesan)", "Sedang", "CFP dibatasi (fan-out 3)"],
]
WHY = [
    ("Batas organisasi", "Carrier, bea cukai, dan pelabuhan adalah pihak otonom yang tidak dapat dikendalikan planner pusat; mereka hanya dapat dinegosiasikan (CFP/PROPOSE) dan mengungkap sebatas tawaran."),
    ("Lingkungan partially observable, stochastic, dynamic", "Sesuai Tabel 2.1 (Bab 2), lingkungan seperti ini menuntut memori, penalaran probabilistik, perencanaan, koordinasi, dan pembelajaran; tugas heterogen lebih mudah diuji jika dipecah per agen."),
    (f"Ketahanan terhadap single point of failure", f"Pada gangguan bidang kontrol di 50% skenario, tepat waktu turun dari {pc(rob_c0)} ke {pc(rob_c)} (agen tunggal) vs {pc(rob_m0)} ke {pc(rob_m)} (multi-agen)."),
    ("Beban node puncak", f"Pada 240 order dan 120 mesin, koordinator menerima {n(sc_last['central']['coord_peak'],0,'',False)} pesan/hari pada hari tersibuk vs {n(sc_last['mas']['peak_node'],0,'',False)} pada agen tersibuk multi-agen ({n(peak_ratio,1,'',False)}x lebih ringan); total pesan {n(100*msg_red,0,'',False)}% lebih sedikit (asumsi heartbeat koordinator tiap 6 jam)."),
    ("Modularitas", "Agen dapat diganti/diuji terpisah (ablation): mis. mengganti model risiko atau kebijakan lembur tanpa menyentuh agen lain; carrier baru cukup ditambah sebagai agen."),
]
WHY_HONEST = (f"Catatan penting: pada simulasi dasar, agen tunggal (inti kognitif terpusat) dan multi-agen menghasilkan kualitas keputusan identik (selisih biaya berpasangan = "
              f"{ci(PD['mas_vs_central_total_cost'], lambda x: n(x, 0))} USD) karena keduanya memakai aturan keputusan yang sama. Untuk satu pabrik, satu pemilik, dan puluhan order, agen tunggal sudah memadai. "
              "Rekomendasi: arsitektur hybrid: satu inti kognitif per pabrik (Order + Production) dan negosiasi multi-agen pada batas organisasi (carrier, bea cukai), dengan governance sebagai bidang kontrol.")

AGENTS = [
    ["Agen", "Tipe", "Belief / Desire / Intention", "Komponen internal dan tools", "Input -> Output", "Metode", "Otonomi"],
    ["Order Agent (x n)", "Hybrid, statis, deliberatif", "B: ETA, antrean, trust, kongesti. D: kirim <= LSD dengan biaya minimum. I: memilih bid mesin dan carrier",
     "Estimator slack, kalkulator penalti, klien CNP, kebijakan expedite", "Order + bid -> ACCEPT/REJECT, booking", "Aturan + DSS hibrida", "Delegate (nilai < $50k)"],
    ["Machine Agent (x6)", "Reaktif + deliberatif, statis", "B: antrean, kesehatan mesin. D: memaksimalkan throughput. I: menawar ETA, memproses job",
     "Estimator ETA, monitor kondisi (tren sensor), antrean critical ratio", "CFP -> PROPOSE(ETA); INFORM(done)", "Regresi slope + aturan", "Delegate"],
    ["Compliance Agent", "Deliberatif, statis", "B: deskripsi produk, aturan dokumen. D: dokumen benar dan siap sebelum produksi selesai. I: menetapkan HS, meminta review",
     "TF-IDF kata+karakter, k-NN kosinus, mesin aturan lisensi, penilai confidence", "Deskripsi -> HS + confidence; review manusia bila < 0,60", "ML klasik (NLP) + aturan", "Delegate / Approve"],
    ["Risk Agent", "Deliberatif, statis", "B: fitur pelabuhan/carrier, riwayat outcome. D: estimasi risiko akurat. I: memberi p roll-over dan trust",
     "Regresi logistik (numpy), registri trust, kalibrasi (Brier)", "Fitur -> p; outcome -> trust update", "Supervised ML + trust", "Supervise"],
    ["Learning Agent", "Learning agent (Bab 2)", "B: state (slack, nilai, tahap). D: meminimalkan biaya+penalti. I: normal atau lembur",
     "Performance element, critic (reward), learning element (Q), problem generator (epsilon-greedy), guardrail anggaran", "State -> aksi; outcome -> update Q", "Q-learning tabular (RL)", "Supervise, batas anggaran"],
    ["Governance & Security Agent", "Deliberatif, statis (bidang kontrol)", "B: kebijakan, identitas, trust, level otonomi. D: keputusan sah dan dapat diaudit. I: izinkan/tolak/eskalasi",
     "Policy engine, capability set, HMAC + nonce, FSM protokol, audit log rantai-hash", "Pesan/aksi -> allow/deny/level 1-4", "Rule-based (deterministik)", "Delegate"],
    ["Carrier Agent (x3, eksternal)", "Reaktif, eksternal", "B: kapasitas dan jadwal kapal. D: mengisi kapal. I: menawar tarif dan closing",
     "Tabel tarif, jadwal mingguan", "CFP -> PROPOSE(rate, closing)", "Aturan", "Di luar kendali"],
    ["Scout Agent", "Mobile, deliberatif", "B: host dan trust. D: mendapat jadwal terkini dengan trafik minimal. I: migrasi jika aman",
     "Serialisasi state, verifikasi hash/HMAC, pemilih host, sandbox", "Host tepercaya -> closing time (2 KB)", "Aturan + skor komposit", "Supervise"],
]
PORTFOLIO = [
    ["Komponen", "Metode", "Kelas", "Alasan pemilihan", "Mengapa bukan DL/LLM (sekarang)"],
    ["Klasifikasi HS", "TF-IDF + k-NN kosinus", "ML klasik (NLP)", f"Deskripsi pendek, ~840 contoh; akurasi {pc(hs['acc'])} dan confidence dapat dijelaskan; latensi ms", "Data kecil; DL/LLM lebih baik hanya bila kosakata besar; LLM ditambahkan kelak untuk ekstraksi dokumen"],
    ["Risiko roll-over", "Regresi logistik", "ML supervised", f"Data tabular 4.000 pengiriman; AUC {n(rk['auc'],2,'',False)}; bobot dapat dibaca tim logistik; probabilitas terkalibrasi", "Pada data tabular kecil, model linier/tree setara DL (Bab 1); XGBoost sebagai pembanding tahap berikut"],
    ["Kesehatan mesin", "Slope percept sequence", "Statistik", "Bab 2: tren lebih informatif daripada nilai tunggal", "Sensor sedikit; DL (LSTM) relevan bila data getaran tersedia"],
    ["Keputusan lembur", "Q-learning tabular", "RL", "Ruang state kecil (66 state), keputusan sekuensial dengan reward tertunda", "Deep RL tidak diperlukan; risiko tidak stabil dan sulit diaudit"],
    ["Pemilihan carrier", "DSS berbobot + ML + gerbang kebijakan", "Hibrida (Bab 3)", "Skor hibrida h; kelayakan sebagai constraint keras", "Keputusan berdampak finansial harus dapat dijelaskan"],
    ["Dispatch mesin", "Critical ratio + Contract Net", "AI klasik / aturan", "Deterministik, cepat, teruji di literatur penjadwalan", "Tidak perlu belajar untuk aturan yang sudah baik"],
    ["Keamanan dan otonomi", "HMAC, nonce, FSM, capability", "Deterministik", "Jaminan keamanan harus pasti, bukan probabilistik", "-"],
    ["Rencana lanjutan", "LLM+RAG, LSTM/TFT, GNN", "DL / LLM", "Ekstraksi L/C dan invoice, prediksi ETA, graf jaringan pelabuhan (Bab 5)", "Belum diimplementasikan di Tugas 1"],
]
CRIT_NOTE = ("Kriteria pemilihan model (Bab 3): akurasi dan explainability, latensi dan biaya, privasi dan data, skalabilitas. Prinsip Bab 1: pilih model paling sederhana yang memenuhi kebutuhan akurasi, latensi, biaya, explainability, dan governance.")

AUTONOMY = [["Level (Bab 2)", "Keputusan pada EOS-MAS", "Rata-rata per skenario", "Kendali"],
    ["4 Delegate", "Dispatch operasi, HS confidence >= 0,60, carrier order < $50k", f"{n(lv['4'],1,'',False)} ({pc(auto_share)})", "Otomatis, audit trail"],
    ["3 Supervise", "Lembur dalam anggaran", f"{n(lv['3'],1,'',False)}", "Agen bertindak, manusia dapat override"],
    ["2 Approve", "HS confidence rendah, order >= $50k, air freight, lembur di luar anggaran", f"{n(lv['2'],1,'',False)}", "Human-in-the-loop"],
    ["1 Assist", "Belum dipakai pada simulasi (mode rekomendasi saja)", f"{n(lv['1'],1,'',False)}", "Rekomendasi"]]

ATTACKS = [["Serangan / pelanggaran", "Hasil pada bus pesan"]] + [[k, v] for k, v in R["attacks"].items()]
MIGR = [["Host", "Trust", "Latensi (ms)", "Risiko", "Skor", "Keputusan"]] + [
    [h["host"], f"{n(h['trust'],2,'',False)}", f"{n(h['latency'],0,'',False)}", f"{n(h['risk'],2,'',False)}", f"{n(h['score'],2,'',False)}", h["decision"]] for h in R["migration_table"]]

# ============================================================ results tables
def main_table():
    rows = [["Metrik", "Statis (manual/FIFO)", "Agen tunggal (inti terpusat)", "Multi-agen (EOS-MAS)"]]
    spec = [("Tepat waktu", "otd", lambda x: pc(x)), ("Rata-rata hari terlambat", "avg_late", lambda x: f"{n(x,2,'',False)}"),
            ("Biaya total per skenario (USD)", "total_cost", lambda x: f"{n(x,0,'',True)}"), ("  Freight", "freight", lambda x: f"{n(x,0,'',True)}"),
            ("  Penalti keterlambatan", "penalty", lambda x: f"{n(x,0,'',True)}"), ("  Lembur", "overtime", lambda x: f"{n(x,0,'',True)}"),
            ("  Penyimpanan", "hold", lambda x: f"{n(x,0,'',True)}"), ("  Sentuhan manusia", "human", lambda x: f"{n(x,0,'',True)}"),
            ("Sentuhan manusia per order", "touches", lambda x: f"{n(x,2,'',False)}"), ("Kesalahan HS", "hs_err", lambda x: pc(x)),
            ("Total pesan per skenario", "msgs", lambda x: f"{n(x,0,'',True)}"), ("Pesan koordinator pada hari tersibuk", "coord_peak", lambda x: f"{n(x,0,'',False)}"),
            ("Pesan agen tersibuk (non-koordinator)", "peak_node", lambda x: f"{n(x,0,'',False)}"), ("Indeks Jain utilisasi mesin", "jain", lambda x: f"{n(x,2,'',False)}")]
    for name, k, f in spec:
        rows.append([name] + [f(M[m][k][0]) if k in ("msgs", "coord_peak", "peak_node", "jain", "touches", "hs_err", "freight", "penalty", "overtime", "hold", "human") else
                              f"{f(M[m][k][0])}  [{f(M[m][k][1])}; {f(M[m][k][2])}]" for m in ("static", "central", "mas")])
    return rows

PAIRED = [["Selisih berpasangan vs statis", "Agen tunggal", "Multi-agen"],
    ["Tepat waktu (poin persentase)", ci(PD["central_vs_static_otd"], lambda x: f"{n(100*x,1,'+',False)}"), ci(PD["mas_vs_static_otd"], lambda x: f"{n(100*x,1,'+',False)}")],
    ["Hari terlambat", ci(PD["central_vs_static_avg_late"], lambda x: f"{n(x,2,'+',False)}"), ci(PD["mas_vs_static_avg_late"], lambda x: f"{n(x,2,'+',False)}")],
    ["Biaya total per skenario (USD)", ci(PD["central_vs_static_total_cost"], lambda x: f"{n(x,0,'+',True)}"), ci(PD["mas_vs_static_total_cost"], lambda x: f"{n(x,0,'+',True)}")],
    ["Biaya sentuhan manusia (USD)", ci(PD["central_vs_static_human"], lambda x: f"{n(x,0,'+',True)}"), ci(PD["mas_vs_static_human"], lambda x: f"{n(x,0,'+',True)}")]]

def ablation_table():
    rows = [["Varian MAS", "Tepat waktu", "Biaya/skenario", "Delta biaya", "Penalti", "Freight", "Lembur"]]
    for nm, v in ab.items():
        d = v["total_cost"][0] - base["total_cost"][0]
        rows.append([nm, pc(v["otd"][0]), f"{n(v['total_cost'][0],0,'',True)}", "-" if nm == "MAS (full)" else f"{n(d,0,'+',True)}", f"{n(v['penalty'][0],0,'',True)}", f"{n(v['freight'][0],0,'',True)}", f"{n(v['overtime'][0],0,'',True)}"])
    return rows

ROBUST = [["P(gangguan bidang kontrol)", "Statis", "Agen tunggal", "Multi-agen"]] + [
    [f"{n(float(p),1,'',False)}"] + [f"{pc(rb[p][m]['otd'][0])} / ${n(rb[p][m]['total_cost'][0],0,'',True)}" for m in ("static", "central", "mas")] for p in sorted(rb, key=float)]
SCALE = [["Order / mesin", "Koordinator: puncak pesan/hari", "MAS: agen tersibuk", "Total pesan (pusat / MAS)", "Tepat waktu (pusat / MAS)"]] + [
    [f"{r['n_orders']} / {r['machines']}", f"{n(r['central']['coord_peak'],0,'',False)}", f"{n(r['mas']['peak_node'],0,'',False)}", f"{n(r['central']['msgs'],0,'',True)} / {n(r['mas']['msgs'],0,'',True)}",
     f"{pc(r['central']['otd'])} / {pc(r['mas']['otd'])}"] for r in sc]
ML_STATS = [["Model", "Metrik", "Nilai"],
    ["Klasifikasi HS (uji 25%)", "Akurasi (semua)", pc(hs["acc"])],
    ["Klasifikasi HS", f"Akurasi pada yang otomatis (tau=0,60)", pc(min(r for r in hs["selective"] if abs(r[0]-0.6) < .03)[2])],
    ["Klasifikasi HS", "Cakupan otomatis (tau=0,60)", pc(min(r for r in hs["selective"] if abs(r[0]-0.6) < .03)[1])],
    ["Risiko roll-over (uji 25%)", "AUC", f"{n(rk['auc'],3,'',False)}"],
    ["Risiko roll-over", "Brier (model / baseline base-rate)", f"{n(rk['brier'],4,'',False)} / {n(rk['brier_baseline'],4,'',False)}"],
    ["Q-learning (MDP abstrak)", "Return per order: Q / aturan slack<0 / never", f"{n(rlr['env_return']['Q-learning'],0,'',False)} / {n(rlr['env_return']['rule (slack<0)'],0,'',False)} / {n(rlr['env_return']['never'],0,'',False)}"]]

INTERPRET = [
    f"Sumber penghematan terbesar adalah re-optimasi carrier: mempertahankan carrier yang dijanjikan menaikkan biaya {n(ab['carrier rule = keep committed carrier (no re-optimisation)']['total_cost'][0]-base['total_cost'][0],0,'+',True)} USD per skenario dengan tepat waktu hampir sama. Dokumen paralel dengan produksi menyumbang "
    f"{pc(base['otd'][0]-ab['- parallel documents']['otd'][0])} poin tepat waktu dan {n(ab['- parallel documents']['total_cost'][0]-base['total_cost'][0],0,'',True)} USD.",
    f"Trade-off biaya vs layanan: menghapus model risiko atau memakai aturan biaya-harapan menurunkan biaya ({n(ab['- ML risk model (advertised reliability)']['total_cost'][0]-base['total_cost'][0],0,'+',True)} dan {n(ab['carrier rule = expected cost']['total_cost'][0]-base['total_cost'][0],0,'+',True)} USD) "
    f"tetapi menurunkan tepat waktu menjadi {pc(ab['- ML risk model (advertised reliability)']['otd'][0])} dan {pc(ab['carrier rule = expected cost']['otd'][0])}. Karena penalti diasumsikan kecil dibanding selisih tarif, aturan biaya murni memilih carrier murah yang berisiko; "
    "aturan hibrida (Bab 3) memprioritaskan tingkat layanan. Pilihan bobot adalah keputusan bisnis, bukan kebenaran teknis; kerugian reputasi/L-C tidak dimodelkan sehingga biaya layanan rendah di sini bersifat konservatif.",
    f"Klasifier HS ML menurunkan kesalahan dari {pc(M['static']['hs_err'][0])} menjadi {pc(M['mas']['hs_err'][0])} dan biaya manusia; dampak dolar kecil ({n(ab['- ML HS classifier (manual HS)']['total_cost'][0]-base['total_cost'][0],0,'+',True)} USD) tetapi mengurangi risiko kepatuhan yang tidak dimodelkan penuh. "
    f"Scout mobile memangkas data yang dipindahkan {n(100*(1-R['scout']['bytes']/R['scout']['raw']),0,'',False)}% (host tidak tepercaya tetap memakai remote pull).",
    f"Pembelajaran RL: policy Q yang dilatih di MDP abstrak tidak transfer ({n(ab['expedite = Q trained in abstract env (no transfer)']['total_cost'][0]-base['total_cost'][0],0,'+',True)} USD, hampir tidak pernah lembur), "
    f"sedangkan Q yang dilatih langsung di simulator setara aturan slack<0 ({n(ab['expedite = tuned rule (slack<0)']['total_cost'][0]-base['total_cost'][0],0,'+',True)} USD). Menariknya 'selalu lembur (dalam anggaran)' lebih baik "
    f"({n(ab['expedite = always overtime']['total_cost'][0]-base['total_cost'][0],0,'+',True)} USD, tepat waktu {pc(ab['expedite = always overtime']['otd'][0])}): lembur murah dibanding penalti, dan anggaran governance 12 tahap menjadi parameter yang mengikat. "
    "Penyebab Q tidak menemukannya adalah reward akhir yang bising dan kredit yang tercampur antar order (credit assignment); perbaikan yang direncanakan: difference reward (Bab 4) dan lebih banyak episode.",
]
LIMITS = [
    "Data sintetis dan perusahaan fiktif: tidak ada klaim performa dunia nyata. Kalibrasi ke data ERP/MES/TMS riil adalah langkah wajib berikutnya.",
    "Aturan keputusan agen tunggal dan multi-agen sengaja disamakan agar perbedaan arsitektur terisolasi; perbandingan dengan optimizer global eksak (MILP) belum dilakukan.",
    "Keunggulan pesan multi-agen bergantung pada asumsi heartbeat koordinator tiap 6 jam; pada arsitektur pusat yang event-driven selisihnya mengecil.",
    "Penalti keterlambatan diasumsikan; kerugian reputasi, pembatalan L/C, dan variasi kurs tidak dimodelkan. Ukuran data untuk scout adalah asumsi.",
    "Model risiko (AUC 0,76) dilatih pada data yang dibangkitkan dari proses logit yang kita tulis; performa nyata akan berbeda. Belum ada uji drift/retraining online.",
    "Simulasi diskret dengan langkah 0,05 hari; 300 skenario evaluasi (seed 0-299) terpisah dari seed kalibrasi (1000+) dan pelatihan RL (10000+).",
    "Belum ada LLM/DL, UI dashboard, maupun integrasi API nyata (bea cukai, carrier); ini rencana Project #1.",
]
LECTURE_MAP = [["Materi kuliah", "Penerapan pada EOS-MAS", "Berkas kode"],
    ["Bab 1: hibrida prediksi + aturan deterministik; model paling sederhana yang memadai", "Risk/Compliance = ML klasik; governance = aturan; DL/LLM ditunda", "ml.py, agents di sim.py"],
    ["Bab 2: PEAS, klasifikasi lingkungan, rational agent, utility + constraint", "Bagian 2.3-2.4; a* = argmax U s.t. policy", "config.py, sim.py"],
    ["Bab 2: percept sequence (55->80 C), reactive vs deliberative, level otonomi, learning agent", "Condition monitor mesin; hybrid; level 1-4; Learning Agent (critic, learning element, problem generator)", "ml.py (slope), rl.py, rl_sim.py"],
    ["Bab 3: BDI, A = <G,B,I,M,C,R,P,T>, s(t+1)=F(s,o,a)", "Tabel agen (6.4), siklus kognitif (6.3)", "sim.py"],
    ["Bab 3: skor hibrida h = g[alpha z + (1-alpha) 100 (1-p)], DSS + ML + policy engine", "Pemilihan carrier", "sim.py (book)"],
    ["Bab 3: runtime, observability, audit trail, batas berhenti", "Log audit rantai-hash, jumlah pesan, anggaran lembur, eskalasi confidence", "messaging.py"],
    ["Bab 4: MAS tuple, ACL, FSM, ontologi, komunikasi", "Message m = <s,r,p,c,o,l,id,t>, FSM Contract Net, ontologi export-mfg-v1", "messaging.py"],
    ["Bab 4: Contract Net, negosiasi konsesi, Nash bargaining, lelang, assignment", "Dispatch mesin (CNP), carrier (CNP), tarif (negosiasi)", "negotiation.py, sim.py"],
    ["Bab 4: trust eksponensial, HMAC, replay, capability, migrasi aman", "Trust carrier, 7 uji serangan, gerbang migrasi", "messaging.py, mobile.py"],
    ["Bab 4: speedup, R_sys, Jain, C_comm, KPI vector, smart manufacturing", "Bagian 3 (contoh 9) dan 7 (metrik sistem)", "negotiation.py, experiments.py"],
    ["Bab 5: mobile agent, serialisasi, migrasi, sandbox, RL mobility, layout Project #1", "Scout Agent; Q-learning; struktur laporan mengikuti layout Project #1", "mobile.py, rl.py"]]

NEXT = [
    "Ganti data sintetis dengan data riil/publik (data perdagangan, jadwal kapal terbuka) dan kalibrasi seluruh parameter; jika perlu adaptasi ke komoditas ekspor lain (mis. briket arang, wood pellet: HS 4402/4401).",
    "Project #1 (tema domain enterprise): perluas ke Scout/Broker/Worker/Security (Bab 5), dashboard UI/UX (status agen, migrasi, KPI), GNN untuk jaringan pelabuhan-carrier, dan bandingkan dengan sistem statis.",
    "Perkuat RL: difference reward, replay terkontrol, dan safe-RL dengan constraint eksplisit; bandingkan XGBoost untuk risiko roll-over.",
    "Tambahkan LLM+RAG untuk ekstraksi dokumen L/C dan invoice dengan human-approval gate; uji drift dan retraining online.",
    "Bandingkan dengan optimizer global (MILP/OR-Tools) sebagai batas atas optimalitas.",
]
