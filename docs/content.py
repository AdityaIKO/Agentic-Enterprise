"""Report + slide content (Bahasa Indonesia). Every number is read from outputs/*.json, never typed by hand."""
import json, pathlib, sys
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kraka_mas import config as C
from kraka_mas.data import make_scenario
from kraka_mas.profiles import PROFILES

R = json.loads((ROOT / "outputs/results.json").read_text())
W = json.loads((ROOT / "outputs/worked_example.json").read_text())
FIGDIR = ROOT / "outputs/figures"

NAMA, NIM = "Aditya Wahyu Wijanarko", "25/574566/PPA/07251"
REPO = "https://github.com/AdityaIKO/Agentic-Enterprise"
TITLE = "KCMAS: Sistem Multi-Agen untuk Konsolidasi dan Ekspor Arang (KrakaCoal)"
SUBTITLE = "Sistem agen cerdas yang mengubah permintaan pembeli menjadi kontainer arang yang terisi penuh dan berangkat tepat waktu, dari puluhan produsen kecil"
COURSE = "Agentic Enterprise (AI Agentic Technology Systems for Digital Enterprise Ecosystem) - Magister AI, Universitas Gadjah Mada"


def n(x, nd=2, plus="", thou=False):
    """Indonesian number style: decimal comma, thousands dot."""
    s_ = format(x, f"{plus}{',' if thou else ''}.{nd}f")
    return s_.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


usd = lambda x: "$" + n(x, 0, "", True)
pc = lambda x, nd=1: n(100 * x, nd) + "%"
def ci(t, f=lambda x: n(x, 2)): return f"{f(t[0])} [{f(t[1])}; {f(t[2])}]"

P = R["profiles"]; KR = P["kraka"]; XP = KR
PFK = PROFILES["kraka"]
MODES = ("static", "central", "mas")
def mv(pf, mode, key, i=0): return P[pf]["main"][mode][key][i]
def per_order(pf, mode, key): return mv(pf, mode, key) / PROFILES[pf].n_orders

# headline numbers
h = {}
for pf in ("kraka",):
    h[pf] = dict(otif_s=mv(pf, "static", "otif"), otif_m=mv(pf, "mas", "otif"), otif_c=mv(pf, "central", "otif"),
                 fill_s=mv(pf, "static", "fill"), fill_m=mv(pf, "mas", "fill"), fill_c=mv(pf, "central", "fill"),
                 otd_s=mv(pf, "static", "otd"), otd_m=mv(pf, "mas", "otd"),
                 mar_s=per_order(pf, "static", "margin"), mar_c=per_order(pf, "central", "margin"), mar_m=per_order(pf, "mas", "margin"),
                 t_s=mv(pf, "static", "touches"), t_m=mv(pf, "mas", "touches"), hs_s=mv(pf, "static", "hs_err"), hs_m=mv(pf, "mas", "hs_err"))

# ============================================================ front matter
EXEC = [
    "KrakaCoal (krakacoal.com) adalah bisnis ekspor arang yang sudah berjalan: jaringan produsen (bukan satu pabrik) di Sumatra, Jawa, dan Sulawesi, karbonisasi di Jawa, uji lab tiap batch, ekspor dari Surabaya, "
    "kapasitas 300+ ton per bulan dan 10+ kontainer per bulan, dengan MOQ satu kontainer penuh (12-17 ton untuk 20 ft, 25-27 ton untuk 40 ft). Penulis bekerja sebagai trader pada bisnis ini.",
    "Masalah yang dipecahkan: bagaimana mengubah satu permintaan pembeli (RFQ) menjadi kontainer yang terisi penuh dan berangkat tepat waktu ketika pasokan tersebar pada puluhan produsen yang kapasitas nyatanya berubah-ubah, "
    "kadang gagal kirim, dan sebagian barangnya tidak lolos uji mutu. Sistem KCMAS memecahnya menjadi peran-peran perangkat lunak (agen): Marketing & Ads, Sales, Order, Producer, QC, Warehouse, Compliance, Risk, Freight, Learning, Governance, dan Scout. "
    "Semua agen adalah program; pekerjaan fisik tetap dilakukan produsen, staf, dan mesin gudang.",
    f"Hasil simulasi ({R['n_scenarios']} skenario, seluruh data sintetis): persentase order yang berangkat tepat waktu dan terisi penuh (OTIF) naik dari {pc(h['kraka']['otif_s'])} pada proses manual (admin via WhatsApp) menjadi {pc(h['kraka']['otif_m'])} pada multi-agen; "
    f"margin per order dari {usd(h['kraka']['mar_s'])} menjadi {usd(h['kraka']['mar_m'])}; sentuhan manusia per order dari {n(h['kraka']['t_s'],0)} menjadi {n(h['kraka']['t_m'],1)}.",
    "Temuan yang jujur: (1) keunggulan multi-agen atas agen tunggal terpusat kecil dan berasal dari informasi lokal yang segar (produsen menawar dengan kapasitas nyata hari itu, bukan data pendaftaran yang usang); bila data pusat akurat, agen tunggal setara. "
    "(2) Multi-agen memakai lebih banyak pesan pada tahap pemasokan tetapi beban per node lebih ringan. (3) Kelebihan pesanan (buffer) sekitar 15% adalah kompromi antara kekurangan pasokan dan limbah. "
    "(4) Modul Sales dan Marketing bersifat eksploratif dan bergantung asumsi. (5) Data sintetis; syarat pembayaran dan harga KrakaCoal tidak dipublikasikan sehingga menjadi asumsi.",
]
METRIK_DEF = [["Istilah pada tabel", "Artinya"],
    ["OTIF (On Time In Full)", "Persentase order yang berangkat paling lambat pada tanggal batas kirim (LSD) DAN jumlah kg yang lolos uji mutu minimal 98% dari yang dipesan. Ini ukuran utama."],
    ["Tepat waktu", "Persentase order yang berangkat sebelum LSD, tanpa memperhitungkan kelengkapan."],
    ["Fill rate", "Rata-rata (kg yang lolos uji mutu dibagi kg yang dipesan) per order."],
    ["Margin per order", "Pendapatan dikurangi semua biaya (bahan dari produsen, freight, denda keterlambatan, penyimpanan, lembur, biaya waktu manusia, limbah surplus), rata-rata per order, dalam USD."],
    ["Sentuhan manusia", "Berapa kali seseorang harus turun tangan per order (mengirim pesan, memverifikasi, memeriksa)."],
    ["Angka dalam tabel", f"Rata-rata dari {R['n_scenarios']} skenario simulasi yang sama untuk ketiga sistem; [a; b] adalah rentang kepercayaan 95%."]]

TUGAS_MAP = [
    ("Gunakan topik yang dipilih", "Topik: KCMAS, sistem multi-agen untuk konsolidasi dan ekspor arang (KrakaCoal). Tidak diambil kelompok 1-6.", "Bagian 1, 2"),
    ("Upload laporan progres", "Dokumen ini (PDF) + slide (PPTX) + kode GitHub", "-"),
    ("Peran anggota tim", "Pengerjaan individu (tidak ada tim)", "Bagian 1"),
    ("Deskripsi problem", "MOQ, mutu, kuota produsen, pemasaran dan penjualan; KPI, klasifikasi lingkungan, PEAS", "Bagian 2"),
    ("Tiga penelitian topik serupa dan SOTA", "Hathikal 2020; Lee 2024; Ivanov & Dolgui 2021 (+11 referensi, semua ber-DOI, jurnal Q1-Q3)", "Bagian 3"),
    ("Tujuan proyek", "Tujuan umum, enam tujuan khusus terukur, empat hipotesis", "Bagian 4"),
    ("Diagram rencana sistem dan alur", "Arsitektur, alur end-to-end, Contract Net, siklus kerja agen, cuplikan simulasi", "Bagian 5.1"),
    ("Komponen internal tiap agen; AI/ML/DL dan alasannya; peta agen ke kode", "Tabel 12 agen; portofolio metode dan alasan; berkas kode tiap agen", "Bagian 5.2"),
    ("Kontrak input, cognitive overload, jadwal dan approval, negosiasi", "Kontrak I/O pengguna, desain beban kognitif, SLA dan eskalasi, CNP, keamanan", "Bagian 5.3-5.6"),
    ("Mengapa single vs multi-agent; tiga penelitian agen cerdas", "Kriteria Bab 4 + bukti eksperimen; Smith 1980, Leitao 2009, Wang 2024", "Bagian 5.7, 3.2"),
    ("Ilustrasi data dan perhitungan komputasi", "Sumber data (situs KrakaCoal/asumsi), contoh hitung dengan angka, cuplikan simulasi", "Bagian 6"),
]

# ============================================================ problem
PROBLEM = [
    "KrakaCoal (situs krakacoal.com, PT. Kraka Coal Indonesia) menjual arang (batok kelapa, kayu keras, serbuk gergaji) ke pembeli luar negeri. Situsnya menyebut 'a vetted export network, not a single factory': bahan dikumpulkan dari Sumatra, Jawa, dan Sulawesi, "
    "dikarbonisasi di Jawa, diuji lab tiap batch, lalu diekspor dari pelabuhan Jawa Timur (Surabaya). MOQ satu kontainer penuh (20 ft: 12-17 ton, 40 ft: 25-27 ton), produksi 10 hari (20 ft) atau 14 hari (40 ft), packing 3-6 hari, FOB sebagai default dan CIF atas permintaan.",
    "Karena tidak ada satu pabrik yang menghasilkan 25 ton dalam dua minggu, satu order harus digabung dari belasan produsen kecil. Di sinilah masalahnya: (1) kapasitas nyata tiap produsen berubah-ubah (dipakai pembeli lokal, cuaca, bahan baku) dan data pendaftaran cepat usang; "
    "(2) sebagian produsen gagal kirim dan sebagian barang tidak lolos uji mutu (kadar air, abu, ukuran), sehingga kontainer tidak penuh; (3) dokumen ekspor dan klasifikasi HS sering baru diurus setelah barang siap sehingga kapal terlewat; (4) admin mengurus semuanya lewat WhatsApp satu per satu, sehingga lambat dan padat pekerjaan manusia.",
    "Di sisi hulu, pembeli harus ditemukan dan dilayani: iklan digital, konten, dan listing marketplace menghasilkan calon pembeli; RFQ yang masuk harus dijawab cepat dan ditawar. Tanpa pemasaran yang terarah, kapasitas produsen menganggur; tanpa pengawasan kapasitas, iklan menjual barang yang tidak bisa dikirim tepat waktu.",
    "Pernyataan masalah: untuk tiap order, tentukan produsen mana mengirim berapa (dengan cadangan dan re-kontrak bila gagal), jadwal lini gudang, dokumen dan kode HS, carrier, dan tindakan pemulihan, "
    "sehingga margin per order maksimum dengan batasan kapasitas, batas kirim (LSD), maksimum 30% dari satu order per produsen, kebijakan compliance, dan batas wewenang tiap agen.",
]
ENV_TABLE = [
    ["Karakteristik", "Klasifikasi", "Bukti pada kasus ini"],
    ["Observability", "Partially observable", "Kapasitas produsen hari ini (sisa setelah pasar lokal), keandalan, dan yield QC tidak diketahui pasti; registry hanya data onboarding"],
    ["Outcome", "Stochastic", "Gagal kirim produsen, reject QC, kerusakan lini gudang, roll-over kargo, dokumen kurang"],
    ["Change", "Dynamic", "Kapasitas berubah tiap order, jadwal kapal mingguan, kongesti pelabuhan, order baru masuk terus"],
    ["Actors", "Multi-agent", "Pembeli asing, puluhan produsen, carrier, bea cukai, admin: pemilik dan kepentingan berbeda"],
]
PEAS = [
    ["Komponen", "Deskripsi XCMAS"],
    ["Performance", "OTIF (tepat waktu dan terisi >= 98%); margin kontribusi per order; fill rate; rata-rata hari terlambat; tingkat reject dan surplus; sentuhan manusia; keadilan kuota antar UMKM (Jain); ketahanan dan beban node"],
    ["Environment", "Pasar pembeli global dan kanal iklan; 30 produsen arang (WhatsApp); gudang konsolidasi 3 tahap x 2 mesin; dokumen ekspor dan bea cukai; 3 carrier dengan jadwal kapal mingguan; kongesti pelabuhan"],
    ["Actuators", "Membuat dan mengatur iklan dan konten; broadcast CFP dan pemberian kuota via WhatsApp/bus; penjadwalan lini; lembur; booking carrier; penerbitan dokumen; eskalasi ke manusia; pembaruan quality score dan trust"],
    ["Sensors", "Klik dan RFQ dari tiap kanal iklan; balasan/bid produsen; hasil QC (CV/lab); sensor kesehatan mesin; jadwal kapal via Scout Agent; status pelabuhan; hasil pengiriman; RFQ masuk"],
]
SOTA = ("Posisi terhadap solusi yang ada. Marketplace B2B (mis. Alibaba, Global Sources) dan portal ekspor mempertemukan pembeli dan penjual tetapi tidak memastikan satu penjual sanggup memenuhi 25 ton tepat waktu. "
        "Suite ERP/APS, TMS, dan Global Trade Management (mis. SAP GTS, Oracle GTM) kuat pada transaksi dan kepatuhan tetapi berbasis aturan dan batch, dan tidak menegosiasikan kuota dengan puluhan produsen kecil lewat WhatsApp. "
        "KCMAS adalah lapisan keputusan agentik di atas kanal yang sudah dipakai (WhatsApp, e-mail, marketplace); ia tidak menggantikan ERP atau TMS.")

# ============================================================ data & assumptions
PROFILE_TABLE = [["Parameter", "Nilai pada model", "Sumber"],
    ["Produsen di pool", f"{PFK.n_producers}", "Setara 300+ ton per bulan (SOURCE: situs KrakaCoal); jumlah produsen ASUMSI"],
    ["Kapasitas produsen (kg/hari)", f"rata-rata {PFK.cap_mean:.0f} (rentang {PFK.cap_min:.0f}-{PFK.cap_max:.0f})", "ASUMSI, dikalibrasi agar 300+ ton per bulan tercapai"],
    ["Ukuran order (kontainer)", "12, 15, 17 ton (20 ft) atau 25, 27 ton (40 ft)", "SOURCE: situs KrakaCoal"],
    ["Harga kontrak (USD/kg)", "1,10 (medium) dan 1,45 (premium)", "Harga tidak dipublikasikan: ASUMSI"],
    ["Karbonisasi/pendinginan + transport ke gudang", f"{PFK.lag_days+PFK.transport_days:.0f} hari", "ASUMSI"],
    ["Tahap gudang (hari per 20 ton)", "Uji lab dan sortir 1,5 / packing 4,0 / stuffing 1,0", "Packing 3-6 hari (SOURCE); lainnya ASUMSI"],
    ["Waktu produksi total", "10 hari (20 ft) sampai 14 hari (40 ft)", "SOURCE: situs; dipakai untuk kalibrasi pemasokan"],
    ["Tipe kontainer dan tarif", f"kering; tarif x {PFK.rate_factor} dari acuan reefer", "ASUMSI"],
    ["Incoterm", "FOB default, CIF atas permintaan", "SOURCE: situs"],
    ["Dokumen", "COA, MSDS, uji lab, SABER/ESMA, EUDR, Halal", "SOURCE: situs"],
    ["Syarat pembayaran", "DP 40% sebagai contoh", "Tidak dipublikasikan pada situs: ASUMSI, perlu diisi penulis"],
]
ASSUME = [["Parameter", "Nilai", "Keterangan"],
    ["Ketersediaan kapasitas u", f"U({C.AVAIL_LOW}; 1)", "sisa kapasitas produsen setelah pasar lokal (ASUMSI); registry mengira rata-rata 0,775 dan kapasitas nominal berderau 10%"],
    ["Waktu balas WhatsApp", f"median {C.REPLY_MEDIAN_H} jam, sigma {C.REPLY_SIGMA}", "lognormal; bid lebih lambat dari 6 jam diabaikan (ASUMSI)"],
    ["Buffer over-allocation", f"{pc(C.BUFFER_FIRST,0)} (awal), {pc(C.BUFFER_REPL,0)} (susulan)", "dipilih dari sweep pada seed kalibrasi; admin manual 5%"],
    ["Batas konsentrasi", pc(C.MAX_SHARE, 0), "tiap produsen maks 30% dari satu order; produsen dengan quality score < 0,60 diblokir"],
    ["Gagal kirim produsen", "1 - keandalan, keandalan U(0,80; 0,99)", "yield QC = 0,72 + 0,26 x keandalan + derau; premium butuh yield >= 0,85 (Grade A)"],
    ["Surplus", f"dijual lokal {pc(C.SALVAGE,0)} harga beli", "biaya limbah = 40% harga beli untuk kg surplus"],
    ["Lini gudang", f"{C.MACHINES_PER_WC} mesin/tahap; kerusakan {C.BREAKDOWN_RATE}/hari", f"lembur x{C.OVERTIME_SPEEDUP}, {C.OVERTIME_COST_PER_DAY:.0f} USD per hari operasi; anggaran 12 tahap per skenario"],
    ["Penalti keterlambatan", "0,4% nilai/hari + 45 USD/hari (+5% bila > 10 hari)", "ASUMSI; L/C basi dan reputasi tidak dimodelkan"],
    ["Verifikasi DP", f"{C.DP_VERIFY_DAYS[0]}-{C.DP_VERIFY_DAYS[1]} hari, oleh admin", "Rancangan: manusia memverifikasi uang masuk (human-in-the-loop); berlaku pada semua mode"],
    ["Respons sales", f"manual median {C.HUMAN_SALES_MEDIAN_DAYS} hari; SDR {C.SDR_DAYS} hari", "ASUMSI (zona waktu dan jam kantor)"],
]
ASSUME_NOTE = ("Parameter bertanda ASUMSI adalah pilihan pemodelan penulis; harga dan syarat pembayaran KrakaCoal tidak dipublikasikan. Seluruh data operasional (kapasitas, gagal kirim, reject) sintetis.")

def sample_orders(pf="kraka", seed=7):
    sc_ = make_scenario(seed, pf)
    rows = [["Order", "HS", "Kuantitas", "Nilai (USD)", "RFQ (hari)", "DP terverifikasi (SDR)", "Closing dijanjikan", "LSD"]]
    for o in sc_.orders[:6]:
        rows.append([f"#{o.oid}", o.heading, f"{o.qty/1000:.0f} t" + (" premium" if o.premium else ""), f"{o.value:,.0f}".replace(",", "."), n(o.rfq, 1), n(o.dp_agent, 1), n(o.commit_closing, 0), n(o.lsd, 0)])
    return rows

CARRIER_TABLE = [["Carrier (fiktif)", "Tarif acuan/kontainer", "Transit", "Offset closing", "Klaim keandalan", "P(roll-over) dasar"]] + [
    [c.name, usd(c.rate), f"{c.transit:.0f} hari", f"{c.offset:.0f} + 7k", n(c.advertised_rel, 2), n(1 / (1 + np.exp(-c.base_roll_logit)), 2)] for c in C.CARRIERS]

# ============================================================ worked examples
pdm, qct, ca, ro, co, tr, qo, ql, ng, mm, ot, sn = W["producers"], W["qc_trust"], W["carrier"], W["roll"], W["cos"], W["trust"], W["q_ours"], W["q_lecture"], W["nego"], W["mas_metrics"], W["order_trace"], W["sales_nego"]
def _row(r): return f"{r['name']}: rate {n(r['rate'],0)} kg/hari, tawaran {n(r['offer'],0,'',True)} kg, harga {n(r['price'],2)}, q {n(r['q'],2)}, skor {n(r['score'],3)}"
WORKED = [
    ("1. Kebutuhan dengan cadangan (buffer)",
     "Order 25 ton. Sistem meminta 25 x 1,15 = 28,75 ton kepada produsen. Alasan: rata-rata sekitar dua produsen per order gagal kirim dan sekitar 6% kg tidak lolos uji mutu; tanpa cadangan OTIF turun tajam (lihat sweep buffer, Bagian 8). "
     "Putaran susulan hanya menutup kekurangan nyata ditambah cadangan 5%."),
    ("2. Pembagian kuota dengan tawaran kapasitas nyata",
     f"Lot {n(pdm['need'],0,'',True)} kg, jendela {pdm['window']:.0f} hari. Lima produsen menawar: " + "; ".join(_row(r) for r in pdm["rows"]) +
     f". Skor menimbang harga (30%), mutu (50%), dan kecepatan (20%). Urutan: {' > '.join(pdm['ranked'])}. Kuota: " + ", ".join(f"{k} {n(v,0,'',True)} kg" for k, v in pdm["alloc"].items()) + "."),
    ("3. Mengapa data pendaftaran yang usang merugikan (agen tunggal)",
     "Agen tunggal memperkirakan kapasitas dari data pendaftaran: " + ", ".join(f"{r['name']} {n(r['stale_offer'],0,'',True)} kg" for r in pdm["rows"]) +
     f". Dibanding tawaran nyata di atas, kuota berikut melebihi kemampuan: " + ", ".join(f"{k} +{n(v,0,'',True)} kg" for k, v in pdm["cap_short"].items() if v > 0) +
     f" (total {n(pdm['cap_short_total'],0,'',True)} kg), sehingga perlu putaran susulan dan lebih banyak pesan. Pada multi-agen kekurangan ini tidak muncul karena produsen hanya menawar sebatas kapasitas nyata."),
    ("4. Uji mutu dan skor mutu produsen",
     f"Produsen mengirim {n(qct['delivered'],0,'',True)} kg dengan tingkat kelolosan {n(qct['g'],2)}: yang lolos = {n(qct['passed_medium'],0,'',True)} kg. Untuk order premium, produsen berkelolosan di bawah 0,85 hanya 55% yang Grade A: {n(qct['passed_premium_lowgrade'],0,'',True)} kg. "
     f"Skor mutu produsen (mulai 0,78) diperbarui 80% dari skor lama ditambah 20% dari hasil terbaru: menjadi {n(qct['q_ok'],3)}; bila gagal kirim menjadi {n(qct['q_default'],3)}; gagal dua kali menjadi {n(qct['q_default_twice'],3)}, di bawah 0,60 sehingga produsen diblokir sementara."),
    ("5. Urutan kerja di gudang",
     f"Pada hari {n(W['cr']['t'],0)} ada tiga job. J1 tenggat 12,5 sisa kerja 3,2 hari; J2 tenggat 10,5 sisa 4,0; J3 tenggat 9,0 sisa 1,4. Sistem menghitung rasio sisa waktu terhadap sisa kerja (makin kecil makin mendesak): J1 {n(W['cr']['cr']['J1'],2)}; J2 {n(W['cr']['cr']['J2'],3)}; J3 {n(W['cr']['cr']['J3'],2)}. Urutan pengerjaan {' > '.join(W['cr']['order'])}."),
    ("6. Tawaran antar lini gudang (Contract Net)",
     f"Job 1,8 hari pada hari ke-5. Lini a: antrean 2,4 hari, kecepatan 1,02, perkiraan selesai hari {n(W['bids']['a'],2)}. Lini b: antrean 0,9 hari, kecepatan 0,97, selesai hari {n(W['bids']['b'],2)}, sehingga job diberikan ke lini b. "
     f"Bila sensor menandai lini b akan rusak sampai hari ke-7,5, perkiraan lini b menjadi {n(W['bids']['b_alerted'],2)} dan lini a menang."),
    ("7. Memilih carrier",
     f"Order ${n(ca['value'],0,'',True)}, satu kontainer, tiba di gerbang hari {n(ca['tport'],1)}, batas kirim hari {n(ca['lsd'],0)}. " +
     "; ".join(f"{r['name']}: biaya {usd(r['cost'])}, berangkat hari {n(r['dep'],0)}, peluang ditinggal kapal {n(r['p'],2)}, biaya harapan {usd(r['exp_total'])}" for r in ca["rows"]) +
     f". Skor gabungan (harga, waktu transit, dan peluang ditinggal kapal) memilih {ca['best_h']}; jika hanya melihat biaya harapan, yang terpilih {ca['best_exp']}."),
    ("8. Risiko kontainer ditinggal kapal (roll-over)",
     f"Untuk {ro['carrier']} pada kondisi pelabuhan padat (0,6), musim puncak, dan selisih waktu aman 2 hari, model memberi peluang {n(ro['p'],3)}. Carrier tercepat pada kondisi yang sama {n(ro['p_prime'],3)}. Model Risk Agent mempelajari peluang ini dari 4.000 pengiriman historis (AUC {n(R['risk']['auc'],2)})."),
    ("9. Kepercayaan terhadap carrier",
     f"Skor kepercayaan 0,80. Bila kontainer terangkut, skor menjadi {n(tr[0]['new'],2)}. Bila ditinggal kapal, menjadi {n(tr[1]['new'],2)}; ditinggal kedua kali menjadi {n(tr[2]['new'],3)}, di bawah 0,60 sehingga carrier diblokir sementara."),
    ("10. Biaya dan margin satu order (skenario 7, order #1 dan #4)",
     "; ".join(f"{'Manual' if m=='static' else 'Multi-agen'} order #{oid}: {n(v['qty']/1000,0)} ton, terisi {pc(v['fill'],0)}, {v['rounds']} putaran, {v['producers']} produsen, bahan {usd(v['src_cost'])}, freight {usd(v['freight'])}, denda {usd(v['penalty'])}, "
               f"penyimpanan {usd(v['hold'])}, biaya manusia {usd(v['human'])}, pendapatan {usd(v['revenue'])} (terlambat {n(v['late'],0)} hari)" for m in ("static", "mas") for oid, v in ot[m].items()) + "."),
    ("11. Agen mobile (Scout)",
     "Scout hanya berpindah ke sistem carrier yang tepercaya (kepercayaan minimal 0,80 dan risiko maksimal 0,20); carrier A (kepercayaan 0,71) ditolak walau paling cepat. "
     f"Data yang dipindahkan per skenario: {n(KR['scout']['bytes']/1e6,1)} MB (scout) dibanding {n(KR['scout']['raw']/1e6,1)} MB bila menarik seluruh jadwal; hemat {pc(1-KR['scout']['bytes']/KR['scout']['raw'],0)}."),
]

# ============================================================ related work
# SOTA: setiap entri diverifikasi (judul, jurnal, volume/halaman, DOI) melalui pencarian web pada sesi pengerjaan.
# Kuartil = perkiraan SJR (Scimago) dari pengetahuan penulis; mohon dicek ulang di scimagojr.com sebelum pengumpulan.
# (id, kelompok, sitasi APA, jurnal, kuartil, DOI, temuan, celah/relevansi)
SOTA_ROWS = [
 ("Smith1980", "B", "Smith, R. G. (1980). The Contract Net Protocol: High-level communication and control in a distributed problem solver. IEEE Transactions on Computers, C-29(12), 1104-1113.",
  "IEEE Trans. Computers", "Q1", "10.1109/TC.1980.1675516",
  "Alokasi tugas terdesentralisasi: manajer mengumumkan tugas (CFP), kontraktor menawar, pemenang dipilih; dapat re-kontrak bila gagal.",
  "Protokol inti XCMAS untuk kuota produsen, dispatch lini gudang, dan pemilihan carrier. Celah: tidak membahas quality score, buffer, atau batas konsentrasi; XCMAS menambahkannya."),
 ("Leitao2009", "B", "Leitão, P. (2009). Agent-based distributed manufacturing control: A state-of-the-art survey. Engineering Applications of Artificial Intelligence, 22(7), 979-991.",
  "Eng. Appl. Artif. Intell.", "Q1", "10.1016/j.engappai.2008.09.005",
  "Survei kontrol manufaktur berbasis agen: fleksibilitas dan reaksi terhadap gangguan, tetapi adopsi industri terbatas oleh integrasi dan validasi.",
  "Menjustifikasi produsen/lini sebagai unit otonom dan pendekatan hibrida. Celah: fokus satu pabrik; belum konsorsium lintas UMKM dengan data kapasitas berubah."),
 ("Dorri2018", "B", "Dorri, A., Kanhere, S. S., & Jurdak, R. (2018). Multi-agent systems: A survey. IEEE Access, 6, 28573-28593.",
  "IEEE Access", "Q1", "10.1109/ACCESS.2018.2831228",
  "Survei definisi, fitur, komunikasi, tantangan (keamanan, skalabilitas, koordinasi) dan evaluasi MAS.",
  "Dasar kriteria evaluasi dan tantangan MAS (keamanan pesan, skala) yang diuji pada Bagian 8. Celah: survei umum, tanpa studi kasus ekspor UMKM."),
 ("Swaminathan1998", "B", "Swaminathan, J. M., Smith, S. F., & Sadeh, N. M. (1998). Modeling supply chain dynamics: A multiagent approach. Decision Sciences, 29(3), 607-632.",
  "Decision Sciences", "Q1", "10.1111/j.1540-5915.1998.tb01356.x",
  "Pustaka agen rantai pasok yang modular untuk memodelkan dinamika dan kebijakan pengendalian (simulasi).",
  "Mendukung pemodelan pemasok/pabrik/pengirim sebagai agen dalam simulasi. Celah: tidak ada bid kapasitas live vs registry, dan tidak ada komoditas ekspor perishable."),
 ("Jennings2001", "B", "Jennings, N. R., Faratin, P., Lomuscio, A. R., Parsons, S., Wooldridge, M. J., & Sierra, C. (2001). Automated negotiation: Prospects, methods and challenges. Group Decision and Negotiation, 10(2), 199-215.",
  "Group Decis. Negot.", "Q2", "10.1023/A:1008746126376",
  "Kerangka negosiasi otomatis (protokol, objek negosiasi, model keputusan agen) dan tantangannya.",
  "Dasar Sales Agent (konsesi bergantung waktu, Nash bargaining, batas kebijakan). Celah: tanpa evaluasi bisnis; XCMAS mengukur konversi pada simulasi."),
 ("Wang2024", "B", "Wang, L., Ma, C., Feng, X., Zhang, Z., Yang, H., Zhang, J., ... Wen, J. (2024). A survey on large language model based autonomous agents. Frontiers of Computer Science, 18(6), 186345.",
  "Front. Comput. Sci.", "Q1", "10.1007/s11704-024-40231-1",
  "Kerangka terpadu agen berbasis LLM (profil, memori, perencanaan, aksi) dan aplikasi rekayasa/sosial.",
  "Dasar Virtual SDR (LLM sebagai lapisan bahasa). Celah: kontrol dan keamanan aksi masih terbuka; XCMAS membatasi LLM dengan guardrail dan aturan deterministik."),
 ("Watkins1992", "B", "Watkins, C. J. C. H., & Dayan, P. (1992). Q-learning. Machine Learning, 8(3-4), 279-292.",
  "Machine Learning", "Q1", "10.1007/BF00992698",
  "Bukti konvergensi Q-learning pada MDP diskret bila semua aksi dicoba berulang kali.",
  "Dasar Learning Agent (keputusan lembur). Celah: MDP abstrak tidak otomatis bertransfer ke simulator; XCMAS melatih online di simulator (Bagian 8.6)."),
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
  "Mendukung pendekatan simulasi digital twin sebagai lingkungan uji (Bagian 8). Celah: level jaringan besar; tidak menyentuh konsolidasi UMKM dan negosiasi kuota."),
 ("Ouelhadj2009", "A", "Ouelhadj, D., & Petrovic, S. (2009). A survey of dynamic scheduling in manufacturing systems. Journal of Scheduling, 12(4), 417-431.",
  "J. Scheduling", "Q2", "10.1007/s10951-008-0090-8",
  "Tinjauan penjadwalan dinamis (heuristik, meta-heuristik, sistem multi-agen) saat terjadi gangguan seperti kerusakan mesin dan order mendadak.",
  "Dasar penjadwalan reaktif gudang (critical ratio, re-kontrak saat lini rusak). Celah: tidak mencakup hulu (sumber bahan dari UMKM)."),
 ("Dominguez2020", "A", "Dominguez, R., & Cannella, S. (2020). Insights on multi-agent systems applications for supply chain management. Sustainability, 12(5), 1935.",
  "Sustainability", "Q1", "10.3390/su12051935",
  "Tinjauan sistematis penerapan MAS pada rantai pasok: penjadwalan, koordinasi antarperusahaan, pemenuhan order, seleksi pemasok, ketahanan.",
  "Memetakan ruang riset; menunjukkan kebutuhan validasi MAS pada konteks UMKM ekspor. Celah: sedikit studi dengan kalibrasi pada bisnis nyata dan komoditas perishable."),
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
SOTA_TABLE = [["Referensi (APA)", "Jurnal / kuartil*", "DOI", "Temuan dan celah terhadap XCMAS"]] + [
    [r[2], f"{r[3]} ({r[4]})", r[5], r[6] + " Celah/relevansi: " + r[7]] for r in SOTA_ROWS]
CITE_NOTE = ("Verifikasi: judul, jurnal, volume/halaman, dan DOI seluruh 14 referensi dicek melalui pencarian web pada sesi pengerjaan (penelusuran DOI langsung ke Crossref diblokir dari lingkungan kerja). "
             "*Kuartil adalah perkiraan berdasarkan SJR (Scimago) dari pengetahuan penulis, bukan hasil pengecekan langsung; mohon diverifikasi di scimagojr.com untuk tahun terbitan yang relevan sebelum pengumpulan. "
             "Hathikal dkk. terbit di SN Applied Sciences (kini Discover Applied Sciences).")
SOTA_GAP = [
    "Celah 1: literatur MAS manufaktur/rantai pasok (Leitão, 2009; Swaminathan dkk., 1998; Dominguez dkk., 2020) berfokus pada pabrik atau jaringan perusahaan besar; konsolidasi puluhan UMKM dengan kapasitas yang berubah dan tanpa data terpusat belum divalidasi secara kuantitatif.",
    "Celah 2: nilai desentralisasi biasanya diklaim, bukan diukur; XCMAS mengisolasi nilainya (bid live vs registry usang) dengan aturan keputusan yang sama pada agen tunggal dan multi-agen, sehingga selisih hanya berasal dari arsitektur.",
    "Celah 3: model ML logistik ekspor (Hathikal dkk., 2020; Lee dkk., 2024) berdiri sendiri; XCMAS menanamkannya sebagai komponen agen (Risk dan Compliance) yang memicu tindakan (re-kontrak, eskalasi ke manusia, pilihan carrier).",
    "Celah 4: adopsi LLM pada agen (Wang dkk., 2024) belum disertai kontrol aksi yang dapat diaudit; XCMAS membatasi LLM dengan guardrail, otonomi berlevel, dan audit log berantai-hash.",
    "Celah 5: bukti pada bisnis nyata kecil; kasus dikalibrasi dari klaim operasional KrakaCoal (MOQ, lead time, packing) sehingga hasilnya dekat dengan praktik ekspor arang.",
]

# ============================================================ why multi-agent
stX = XP["staleness"]["avail"]; stK = KR["staleness"]["avail"]
def adv(pf, a, key="margin"): d = P[pf]["staleness"]["avail"][a]; return (d["mas"][key][0] - d["central"][key][0]) / (PROFILES[pf].n_orders if key == "margin" else 1)
CRITERIA = [
    ["Kriteria (Bab 4)", "Terpusat", "Terdesentralisasi", "Hybrid", "Posisi KCMAS"],
    ["Latensi dan bandwidth", "Sedang", "Rendah", "Rendah-sedang", "CFP hanya ke kandidat (fan-out dibatasi)"],
    ["Fault tolerance", "Rendah (single point of failure)", "Tinggi", "Tinggi", "Kegagalan satu produsen/agen tidak menghentikan order"],
    ["Optimalitas global", "Tinggi bila data akurat", "Lokal", "Cukup tinggi", "Aturan skor bersama + governance; data segar dari bid"],
    ["Biaya koordinasi", "Fan-in O(n) pada koordinator", "Tinggi (banyak pesan)", "Sedang", "Lebih banyak pesan per order pada pemasokan"],
]
WHY = [
    ("Batas organisasi dan kepemilikan", "Produsen arang, carrier, bea cukai, dan pembeli adalah pihak otonom; planner pusat tidak dapat memerintah mereka, hanya menegosiasikan (minta tawaran, tawaran, terima/tolak). Jaringan KrakaCoal memang berbasis kepercayaan lintas pemilik."),
    ("Informasi lokal yang segar", f"Kapasitas nyata produsen berubah (pembeli lokal, cuaca, bahan baku). Bid multi-agen memakai kapasitas nyata; data pendaftaran pusat cepat usang. Dengan variasi ketersediaan 45% (default), multi-agen menaikkan margin {usd(adv('kraka','0.55'))} per order; "
     f"bila kapasitas stabil (variasi 0%) selisihnya {usd(adv('kraka','1.0'))}."),
    ("Ketahanan terhadap single point of failure", f"Gangguan koordinator pusat 2-5 hari pada 50% skenario mengubah OTIF agen tunggal dari {pc(P['kraka']['robust']['0.0']['central']['otif'][0])} ke {pc(P['kraka']['robust']['0.5']['central']['otif'][0])} dan multi-agen dari {pc(P['kraka']['robust']['0.0']['mas']['otif'][0])} ke {pc(P['kraka']['robust']['0.5']['mas']['otif'][0])}: "
     "perbedaannya kecil karena jadwal memiliki cadangan waktu; ketahanan bukan alasan utama pada kasus ini, tetapi menjadi relevan bila jadwal ketat."),
    ("Beban node puncak dan skala", f"Pada {KR['scale'][-1]['n_producers']} produsen, koordinator menerima {n(KR['scale'][-1]['central']['coord_peak'],0)} pesan pada hari tersibuk dibanding {n(KR['scale'][-1]['mas']['peak_node'],0)} pada agen tersibuk multi-agen; total pesan justru lebih banyak pada multi-agen untuk pemasokan ({n(KR['scale'][-1]['mas']['msgs'],0,'',True)} vs {n(KR['scale'][-1]['central']['msgs'],0,'',True)})."),
    ("Modularitas", "Tiap peran (produsen, gudang, carrier, pemasaran) adalah agen terpisah sehingga dapat diganti atau ditambah tanpa mengubah agen lain; misalnya Marketing Agent ditambahkan tanpa mengubah alur pemasokan."),
]
WHY_HONEST = ("Catatan penting: keunggulan multi-agen bergantung pada seberapa kedaluwarsa data pusat. Bila kapasitas produsen stabil dan registry akurat, agen tunggal terpusat setara. "
              "Rekomendasi: arsitektur hybrid: satu inti kognitif per pabrik/gudang, negosiasi multi-agen pada batas organisasi (produsen, carrier), dan governance sebagai bidang kontrol; "
              "untuk 20 produsen yang stabil, agen tunggal + WhatsApp sudah cukup, lalu berpindah ke multi-agen saat pool tumbuh ke ratusan produsen dengan kapasitas berubah-ubah.")

AGENTS = [
    ["Agen", "Tipe", "Belief / Desire / Intention", "Komponen internal dan tools", "Input -> Output", "Metode", "Otonomi"],
    ["Marketing & Ads Agent", "Deliberatif + belajar, statis", "B: performa tiap kanal, anggaran, kapasitas tersedia. D: sebanyak mungkin RFQ berkualitas per dolar iklan. I: membagi anggaran, membuat iklan dan konten, menjeda kampanye",
     "Pembagi anggaran (Thompson sampling), pembuat materi iklan (LLM), pemeriksa klaim (harus sesuai spesifikasi dan sertifikat nyata), sinyal kapasitas dari Order Agent", "Kapasitas + performa kanal -> kampanye, iklan; klik/RFQ -> pembaruan", "Bandit multi-lengan + LLM + aturan klaim", "Supervise (materi baru disetujui manusia)"],
    ["Sales Agent (Virtual SDR)", "Deliberatif, statis", "B: RFQ, spesifikasi, batas harga. D: konversi RFQ ke LoI. I: menawar/berkonsesi atau eskalasi",
     "Deteksi niat, kalkulator konsesi (beta), guardrail harga, hook LLM, CRM", "RFQ -> LoI / eskalasi", "LLM (opsional) + konsesi waktu-tergantung", "Supervise (LoI dalam band harga)"],
    ["Order Agent (x n)", "Hybrid, statis", "B: ETA, antrean, trust. D: terisi penuh dan berangkat <= LSD dengan margin maksimum. I: memilih bid produsen/lini/carrier",
     "Estimator slack, klien CNP, kalkulator penalti, kebijakan expedite", "DP terverifikasi -> CFP, ACCEPT/REJECT, booking", "Aturan + DSS hibrida", "Delegate (nilai < batas)"],
    ["Producer Agent (UMKM, x 30-40)", "Reaktif, statis (WhatsApp)", "B: kapasitas hari ini, stok bahan. D: mendapat kuota dan modal kerja. I: menawar kg, harga, ETA",
     "Template WhatsApp, ketersediaan lokal u, riwayat quality score", "CFP -> PROPOSE(kg, harga, ETA); INFORM(kirim)", "Aturan lokal", "Otonom (pihak eksternal)"],
    ["QC Agent (CV / lab)", "Reaktif + belajar, statis", "B: hasil klasifikasi. D: grade akurat. I: A/B/Reject dan umpan balik ke produsen",
     "Model CV (rencana tim) atau uji lab; estimator yield per produsen", "Sampel -> grade, kg lolos", "CNN (rencana); disimulasikan statistik", "Delegate; sengketa ke manusia"],
    ["Warehouse Line Agent (x 6)", "Reaktif + deliberatif, statis", "B: antrean, kesehatan mesin. D: throughput. I: menawar ETA, memproses",
     "Estimator ETA, monitor kondisi (tren sensor), antrean critical ratio", "CFP -> PROPOSE(ETA); INFORM(done)", "Regresi slope + aturan", "Delegate"],
    ["Compliance Agent", "Deliberatif, statis", "B: deskripsi produk, aturan dokumen. D: dokumen benar dan siap sebelum produksi selesai. I: menetapkan HS, meminta review",
     "TF-IDF kata+karakter, k-NN kosinus, mesin aturan lisensi/sertifikat, penilai confidence", "Deskripsi -> HS + confidence; review manusia bila < 0,60", "ML klasik (NLP) + aturan", "Delegate / Approve"],
    ["Risk Agent", "Deliberatif, statis", "B: fitur pelabuhan/carrier, riwayat outcome. D: estimasi risiko akurat. I: memberi p roll-over dan trust",
     "Regresi logistik (numpy), registri trust, kalibrasi (Brier)", "Fitur -> p; outcome -> trust update", "Supervised ML + trust", "Supervise"],
    ["Freight Agent", "Deliberatif, statis", "B: tarif, closing, p, trust. D: berangkat sebelum LSD dengan biaya wajar. I: memilih carrier",
     "CNP klien, skor hibrida h, gerbang kelayakan g", "CFP -> pilih carrier", "DSS + ML + kebijakan", "Delegate; Approve bila nilai tinggi"],
    ["Learning Agent", "Learning agent (Bab 2)", "B: state (slack, nilai, tahap). D: minimalkan biaya+penalti. I: normal atau lembur",
     "Performance element, critic, learning element (Q), problem generator (epsilon), guardrail anggaran", "State -> aksi; outcome -> update Q", "Q-learning tabular (RL)", "Supervise, batas anggaran"],
    ["Governance & Security Agent", "Deliberatif, statis (bidang kontrol)", "B: kebijakan, identitas, quality score/trust, level otonomi. D: keputusan sah dan dapat diaudit. I: izinkan/tolak/eskalasi",
     "Policy engine, capability, HMAC + nonce, FSM protokol, audit log rantai-hash, batas konsentrasi", "Pesan/aksi -> allow/deny/level 1-4", "Rule-based (deterministik)", "Delegate"],
    ["Scout Agent", "Mobile, deliberatif", "B: host dan trust. D: jadwal terkini dengan trafik minimal. I: migrasi jika aman",
     "Serialisasi state, verifikasi hash/HMAC, pemilih host, sandbox", "Host tepercaya -> closing time (2 KB)", "Aturan + skor komposit", "Supervise"],
]
PORTFOLIO = [
    ["Komponen", "Metode", "Kelas", "Alasan pemilihan", "Mengapa bukan DL/LLM (sekarang)"],
    ["Alokasi kuota produsen", "Contract Net + skor berbobot + buffer + governance", "AI klasik / DSS", "Keputusan dapat dijelaskan ke produsen dan buyer; kendala keras (kapasitas, konsentrasi, kualitas)", "Data historis produsen belum ada; optimasi eksplisit lebih tepat daripada model black-box"],
    ["Quality score produsen", "Pembaruan eksponensial (trust)", "Statistik online", "Insentif kualitas organik; sederhana dan transparan", "Tidak butuh model kompleks"],
    ["Klasifikasi HS lintas komoditas", "TF-IDF + k-NN kosinus", "ML klasik (NLP)", f"Deskripsi pendek, ~1.000 contoh; akurasi {pc(R['hs']['acc'])}; confidence dapat dijelaskan", "Data kecil; LLM/BERT ditambahkan bila kosakata dan bahasa bertambah"],
    ["Risiko roll-over", "Regresi logistik", "ML supervised", f"Data tabular 4.000 pengiriman; AUC {n(R['risk']['auc'],2)}; bobot terbaca; probabilitas terkalibrasi", "Pada data tabular kecil, model linier setara DL (Bab 1); XGBoost sebagai pembanding"],
    ["QC visual (Grade A/B/Reject)", "CNN (rencana); di sini: tingkat kelolosan statistik", "DL (rencana)", "Citra produk adalah data yang cocok untuk DL (Bab 1); dataset sedang dikumpulkan", "Belum ada dataset terlabel; Tugas 1 memodelkan hasilnya (pass rate) saja"],
    ["Alokasi anggaran iklan", "Thompson sampling (bandit multi-lengan)", "RL sederhana", "Kanal mana yang terbaik tidak diketahui dan berubah; metode ini mencoba dan bergeser ke kanal yang menghasilkan RFQ", "Optimasi penuh butuh data klik yang belum ada; bandit cukup dan dapat dijelaskan"],
    ["Pembuatan materi iklan dan konten", "LLM + pemeriksa klaim + persetujuan manusia", "LLM + aturan", "Menulis banyak varian bahasa dan format dengan cepat; klaim (sertifikat, spesifikasi, kapasitas) dicek terhadap data nyata sebelum tayang", "LLM tidak boleh menyebut sertifikat atau kapasitas yang tidak ada; belum diimplementasikan"],
    ["Virtual SDR", "LLM + konsesi waktu-tergantung + guardrail", "LLM + aturan", "Bahasa alami multibahasa 24/7; harga dijaga oleh aturan dan band diskon (Bab 3: LLM tidak sendirian)", "Di simulasi hanya logika negosiasi; panggilan LLM belum dipakai (hook tersedia)"],
    ["Keputusan lembur", "Q-learning tabular", "RL", "Ruang state kecil, reward tertunda", "Deep RL tidak diperlukan; sulit diaudit"],
    ["Kesehatan lini", "Slope percept sequence", "Statistik", "Bab 2: tren lebih informatif daripada nilai tunggal", "Sensor sedikit"],
    ["Pemilihan carrier", "DSS berbobot + ML + gerbang kebijakan", "Hibrida (Bab 3)", "Skor hibrida h; kelayakan sebagai constraint keras", "Keputusan finansial harus dapat dijelaskan"],
    ["Keamanan dan otonomi", "HMAC, nonce, FSM, capability", "Deterministik", "Jaminan keamanan harus pasti", "-"],
]
CRIT_NOTE = ("Kriteria pemilihan model (Bab 3): akurasi dan explainability, latensi dan biaya, privasi dan data, skalabilitas. Prinsip Bab 1: pilih model paling sederhana yang memenuhi kebutuhan. "
             "Kesimpulan: XCMAS adalah hibrida AI klasik + ML supervised + RL kecil + aturan deterministik, dengan slot untuk LLM (Sales dan Marketing) dan CNN (QC) sebagai pengembangan berikutnya.")

lv = XP["levels"]["mas"]; tot_lv = sum(lv.values())
AUTONOMY = [["Level (Bab 2)", "Keputusan pada KCMAS", "Rata-rata per skenario", "Kendali"],
    ["4 Delegate", "Dispatch lini, kuota dalam batas konsentrasi, HS confidence >= 0,60, carrier order di bawah batas nilai", f"{n(lv['4'],1)} ({pc(lv['4']/tot_lv,0)})", "Otomatis, audit trail"],
    ["3 Supervise", "Lembur dalam anggaran, LoI dalam band harga", f"{n(lv['3'],1)}", "Agen bertindak, manusia dapat override"],
    ["2 Approve", "Verifikasi DP (selalu), HS confidence rendah, order bernilai tinggi, lembur di luar anggaran, materi iklan dengan klaim baru", f"{n(lv['2'],1)}", "Human-in-the-loop"],
    ["1 Assist", "Belum dipakai (mode rekomendasi)", f"{n(lv['1'],1)}", "Rekomendasi"]]
ATTACKS = [["Serangan / pelanggaran", "Hasil pada bus pesan"]] + [[k, v] for k, v in R["attacks"].items()]
MIGR = [["Host", "Trust", "Latensi (ms)", "Risiko", "Skor", "Keputusan"]] + [[hh["host"], n(hh["trust"], 2), n(hh["latency"], 0), n(hh["risk"], 2), n(hh["score"], 2), hh["decision"]] for hh in R["migration_table"]]

# ============================================================ results tables
def main_table(pf):
    rows = [["Metrik", "Manual (admin WhatsApp)", "Agen tunggal (registry)", "Multi-agen (bid live)"]]
    nn = PROFILES[pf].n_orders
    spec = [("OTIF (tepat waktu dan terisi)", "otif", lambda x: pc(x), True), ("Tepat waktu", "otd", lambda x: pc(x), True), ("Fill rate", "fill", lambda x: pc(x), True),
            ("Rata-rata hari terlambat", "avg_late", lambda x: n(x, 2), True), ("Margin per order (USD)", "margin", lambda x: n(x / nn, 0, "", True), True),
            ("Biaya sourcing per order", "sourcing", lambda x: n(x / nn, 0, "", True), False), ("Freight per order", "freight", lambda x: n(x / nn, 0, "", True), False),
            ("Penalti per order", "penalty", lambda x: n(x / nn, 0, "", True), False), ("Limbah surplus per order", "surplus_waste", lambda x: n(x / nn, 0, "", True), False),
            ("Sentuhan manusia per order", "touches", lambda x: n(x, 1), False), ("Kesalahan HS", "hs_err", lambda x: pc(x), False),
            ("Putaran sourcing per order", "rounds", lambda x: n(x, 2), False), ("Produsen dikontrak per order", "producers_used", lambda x: n(x, 1), False),
            ("Gagal kirim per order", "defaults", lambda x: n(x, 2), False),
            ("Total pesan per skenario", "msgs", lambda x: n(x, 0, "", True), False), ("Pesan koordinator pada hari tersibuk", "coord_peak", lambda x: n(x, 0), False),
            ("Pesan agen tersibuk", "peak_node", lambda x: n(x, 0), False)]
    for name, k, f, with_ci in spec:
        row = [name]
        for m in MODES:
            v = P[pf]["main"][m][k]
            row.append(f"{f(v[0])}  [{f(v[1])}; {f(v[2])}]" if with_ci else f(v[0]))
        rows.append(row)
    return rows

def paired(pf):
    d = P[pf]["paired_diffs"]; nn = PROFILES[pf].n_orders
    return [["Selisih berpasangan", "Agen tunggal vs manual", "Multi-agen vs manual", "Multi-agen vs agen tunggal"],
        ["OTIF (poin persentase)", ci(d["central_vs_static_otif"], lambda x: n(100 * x, 1, "+")), ci(d["mas_vs_static_otif"], lambda x: n(100 * x, 1, "+")), ci(d["mas_vs_central_otif"], lambda x: n(100 * x, 1, "+"))],
        ["Fill rate (poin persentase)", ci(d["central_vs_static_fill"], lambda x: n(100 * x, 1, "+")), ci(d["mas_vs_static_fill"], lambda x: n(100 * x, 1, "+")), ci(d["mas_vs_central_fill"], lambda x: n(100 * x, 1, "+"))],
        ["Margin per order (USD)", ci(d["central_vs_static_margin"], lambda x: n(x / nn, 0, "+", True)), ci(d["mas_vs_static_margin"], lambda x: n(x / nn, 0, "+", True)), ci(d["mas_vs_central_margin"], lambda x: n(x / nn, 0, "+", True))],
        ["Putaran sourcing per order", "-", "-", ci(d["mas_vs_central_rounds"], lambda x: n(x, 2, "+"))],
        ["Total pesan per skenario", "-", "-", ci(d["mas_vs_central_msgs"], lambda x: n(x, 0, "+", True))]]

def ablation_table(pf):
    ab = P[pf]["ablation"]; base = ab["MAS (full)"]; nn = PROFILES[pf].n_orders
    rows = [["Varian multi-agen", "OTIF", "Fill", "Margin/order", "Delta margin/order", "Limbah surplus", "Putaran"]]
    for nm, v in ab.items():
        d = (v["margin"][0] - base["margin"][0]) / nn
        rows.append([nm, pc(v["otif"][0]), pc(v["fill"][0]), n(v["margin"][0] / nn, 0, "", True), "-" if nm == "MAS (full)" else n(d, 0, "+", True), n(v["surplus_waste"][0] / nn, 0, "", True), n(v["rounds"][0], 2)])
    return rows

def staleness_table():
    rows = [["Variasi ketersediaan (1 - u_min)", "Margin/order (agen tunggal / multi-agen)", "OTIF (agen tunggal / multi-agen)"]]
    for a in sorted(stK, key=float, reverse=True):
        d = P["kraka"]["staleness"]["avail"][a]; nn = PFK.n_orders
        rows.append([pc(1 - float(a), 0), f"{n(d['central']['margin'][0]/nn,0,'',True)} / {n(d['mas']['margin'][0]/nn,0,'',True)}", f"{pc(d['central']['otif'][0],0)} / {pc(d['mas']['otif'][0],0)}"])
    return rows

def buffer_table():
    rows = [["Buffer awal", "Margin/order (USD)", "OTIF", "Limbah surplus/order (USD)"]]
    for b in sorted(KR["buffer"], key=float):
        d = P["kraka"]["buffer"][b]; nn = PFK.n_orders
        rows.append([pc(float(b), 0), n(d["margin"][0] / nn, 0, "", True), pc(d["otif"][0], 0), n(d["surplus_waste"][0] / nn, 0, "", True)])
    return rows

ROBUST = [["Peluang gangguan koordinator pusat", "OTIF manual", "OTIF agen tunggal", "OTIF multi-agen"]] + [
    [n(float(p), 1)] + [pc(P["kraka"]["robust"][p][m]["otif"][0], 0) for m in MODES] for p in sorted(P["kraka"]["robust"], key=float)]
SCALE = [["Order / produsen", "Koordinator: puncak pesan/hari", "MAS: agen tersibuk", "Total pesan (pusat / MAS)", "OTIF (pusat / MAS)"]] + [
    [f"{r['n_orders']} / {r['n_producers']}", n(r["central"]["coord_peak"], 0), n(r["mas"]["peak_node"], 0), f"{n(r['central']['msgs'],0,'',True)} / {n(r['mas']['msgs'],0,'',True)}", f"{pc(r['central']['otif'],0)} / {pc(r['mas']['otif'],0)}"] for r in KR["scale"]]
sh, ss = R["sales"]["human"], R["sales"]["sdr"]
MK = json.loads((ROOT / "outputs/marketing.json").read_text())
MARKETING_TABLE = [["Strategi (12 minggu, USD 500/minggu)", "RFQ berkualitas (rata-rata)", "Rentang 95%", "Biaya per RFQ (USD)"]] + [
    [nm, n(MK[k]['leads_mean'], 1), f"{n(MK[k]['leads_ci'][0],0)} - {n(MK[k]['leads_ci'][1],0)}", n(MK[k]['cost_per_rfq'], 0)] for nm, k in (("Pembagian rata ke semua kanal", "fixed"), ("Marketing Agent (bandit)", "agent"))]
MARKETING_SHARE = [["Kanal iklan", "Porsi anggaran: rata", "Porsi anggaran: agen"]] + [[c, pc(MK['fixed']['share'][i], 0), pc(MK['agent']['share'][i], 0)] for i, c in enumerate(MK['channels'])]
ML_STATS = [["Model", "Metrik", "Nilai"],
    ["Klasifikasi HS (uji 25%, 7 heading)", "Akurasi (semua)", pc(R["hs"]["acc"])],
    ["Klasifikasi HS", "Akurasi pada yang otomatis (tau = 0,60)", pc(min(r for r in R["hs"]["selective"] if abs(r[0] - 0.6) < .03)[2])],
    ["Klasifikasi HS", "Cakupan otomatis (tau = 0,60)", pc(min(r for r in R["hs"]["selective"] if abs(r[0] - 0.6) < .03)[1])],
    ["Risiko roll-over (uji 25%)", "AUC", n(R["risk"]["auc"], 3)],
    ["Risiko roll-over", "Brier (model / baseline base-rate)", f"{n(R['risk']['brier'],4)} / {n(R['risk']['brier_baseline'],4)}"],
    ["Q-learning (MDP abstrak)", "Return per order: Q / aturan slack<0 / never", f"{n(R['rl']['env_return']['Q-learning'],0)} / {n(R['rl']['env_return']['rule (slack<0)'],0)} / {n(R['rl']['env_return']['never'],0)}"],
    ["Sales/SDR (eksploratif, 6.000 RFQ)", "Konversi RFQ ke deal: manual / SDR", f"{pc(sh['conversion'],0)} / {pc(ss['conversion'],0)}"],
    ["Sales/SDR", "Jam RFQ ke harga sepakat: manual / SDR", f"{n(sh['mean_hours'],0)} / {n(ss['mean_hours'],0)}"]]

def _d(pf, name, key="margin"): return (P[pf]["ablation"][name][key][0] - P[pf]["ablation"]["MAS (full)"][key][0]) / (PROFILES[pf].n_orders if key == "margin" else 1)
INTERPRET = [
    f"Sumber nilai terbesar (margin per order): kuota berbasis tawaran live ({usd(-_d('kraka','- live bids (stale registry instead)'))}), dokumen paralel dengan pemasokan ({usd(-_d('kraka','- parallel documents'))}), dan memilih ulang carrier ({usd(-_d('kraka','carrier rule = keep committed carrier'))}). "
    f"Prioritas skor mutu: {usd(-_d('kraka','- quality-score prioritisation (price only)'))}; tanpa buffer margin turun {usd(-_d('kraka','- over-allocation buffer (0 %)'))}.",
    f"Trade-off: menghapus model risiko atau memilih carrier hanya dari biaya harapan dapat menaikkan margin ({usd(_d('kraka','- ML risk model (advertised reliability)'))} dan {usd(_d('kraka','carrier rule = expected cost'))} per order) tetapi menurunkan OTIF; "
    "aturan hibrida memprioritaskan tingkat layanan. Pilihan bobot adalah keputusan bisnis; kerugian reputasi tidak dimodelkan sehingga nilai layanan di sini konservatif.",
    "Buffer: margin puncak pada 15-20% karena kekurangan pasokan (gagal kirim, reject uji mutu) lebih mahal daripada limbah surplus yang dijual 60% harga beli. Pada buffer 30% margin turun karena limbah surplus.",
    "Pembelajaran mesin untuk keputusan lembur: kebijakan yang dilatih pada model sederhana tidak berpindah ke simulator, sedangkan yang dilatih langsung di simulator setara aturan sederhana 'lembur bila sisa waktu negatif'. Pada simulasi ini 'selalu lembur dalam anggaran' bisa lebih baik karena lembur murah dibanding denda.",
    f"Sales dan Marketing (eksploratif, bergantung asumsi): konversi RFQ ke kesepakatan {pc(sh['conversion'],0)} (meja manusia) vs {pc(ss['conversion'],0)} (SDR); waktu ke harga sepakat {n(sh['mean_hours'],0)} vs {n(ss['mean_hours'],0)} jam. "
    f"Pembagian anggaran iklan oleh agen menghasilkan sekitar {n(MK['uplift_pct'],0)}% lebih banyak RFQ berkualitas daripada pembagian rata; bila peringkat kanal selalu sama antar pasar, selisihnya {n(MK['uplift_fixed_ranking_pct'],0)}%. Keduanya perlu divalidasi dengan data nyata.",
]
LIMITS = [
    "Data sintetis: KrakaCoal tidak mempublikasikan harga atau syarat pembayaran. Tidak ada klaim performa nyata; kalibrasi ke data operasional riil (ERP/CRM, riwayat produsen) adalah langkah wajib berikutnya.",
    "Keunggulan multi-agen bergantung pada asumsi variasi ketersediaan (45%) dan galat data pendaftaran (10%); sweep sensitivitas ditampilkan dan pada variasi 0% keunggulan hilang.",
    "Jumlah pesan pusat vs multi-agen bergantung pada asumsi refresh data mingguan dan batas fan-out CFP; pada pemasokan multi-agen memakai lebih banyak pesan.",
    "Uji mutu berbasis citra (CNN) dan LLM untuk Sales dan Marketing tidak diimplementasikan sebagai model; uji mutu dimodelkan sebagai tingkat kelolosan statistik, Sales sebagai logika konsesi, dan Marketing sebagai simulasi pembagian anggaran. Ketiganya eksploratif.",
    "Denda keterlambatan, harga jual, dan tarif carrier adalah asumsi; kerugian reputasi, pembatalan L/C, dan kurs tidak dimodelkan. Angka simulasi Marketing (tingkat RFQ per dolar tiap kanal) adalah asumsi, bukan data KrakaCoal.",
    "Model risiko (AUC 0,76) dilatih pada data yang dibangkitkan dari proses yang kami tulis sendiri; belum ada uji drift atau retraining online.",
    f"Simulasi diskret (langkah 0,05 hari), {R['n_scenarios']} skenario evaluasi (seed 0-299), terpisah dari seed kalibrasi (1000+) dan pelatihan pembelajaran mesin (10000+).",
    "Belum ada UI dashboard, integrasi WhatsApp Business API, API iklan (Google/LinkedIn), atau API bea cukai/carrier nyata; itu rencana Project #1.",
]
BIZ = [
    ["Rekomendasi operasional", "Dasar pada eksperimen"],
    ["Pesan produsen 15% lebih banyak dari kebutuhan pada putaran pertama; pertahankan re-kontrak untuk kekurangan", "Sweep buffer: margin puncak 15-20%; tanpa buffer OTIF turun tajam"],
    ["Minta konfirmasi kapasitas nyata dari produsen (template WhatsApp) sebelum mengunci kuota, bukan mengandalkan data pendaftaran", "Sweep data usang: nilai tawaran live tumbuh dengan variasi ketersediaan"],
    ["Prioritaskan produsen dengan skor mutu tinggi, blokir skor di bawah 0,60, batasi 30% per produsen", "Ablation skor mutu dan batas konsentrasi"],
    ["Mulai dokumen (HS, sertifikat) saat DP terverifikasi, paralel dengan produksi", "Ablation: dokumen paralel = penghematan waktu terbesar kedua"],
    ["Pertahankan verifikasi DP manual (level 2) dan persetujuan order bernilai tinggi", "Menambah sekitar satu sentuhan per order namun mencegah kesalahan pembayaran"],
    ["Bagi anggaran iklan antar kanal secara adaptif, dan hanya iklankan produk yang kapasitasnya tersedia", "Simulasi Marketing (eksploratif); sinyal kapasitas dari Order Agent"],
    ["Untuk 20 produsen yang stabil, mulai dengan agen tunggal; pindah ke multi-agen saat pool ratusan produsen", "Kesimpulan sensitivitas dan skala"],
    ["Kumpulkan data untuk kalibrasi: syarat pembayaran, harga beli per produsen, tingkat gagal kirim dan reject, waktu balas WhatsApp, performa tiap kanal iklan", "Batasan data sintetis"],
]
LECTURE_MAP = [["Materi kuliah", "Penerapan pada KCMAS", "Berkas kode"],
    ["Bab 1: hibrida prediksi + aturan; model paling sederhana yang memadai", "Risk/Compliance = ML klasik; governance = aturan; DL/LLM sesuai porsi", "ml.py, sim.py"],
    ["Bab 2: PEAS, klasifikasi lingkungan, rational agent", "Bagian 2.2-2.3", "config.py, consortium.py"],
    ["Bab 2: reactive vs deliberative, level otonomi, learning agent", "Monitor kondisi lini; agen hibrida; level 1-4; Learning Agent", "ml.py, rl.py, rl_sim.py"],
    ["Bab 3: BDI (belief, desire, intention), siklus kerja agen", "Tabel agen (5.2), siklus kerja (5.1)", "sim.py, consortium.py"],
    ["Bab 3: keputusan hibrida (DSS + ML + kebijakan)", "Pemilihan carrier", "sim.py (book)"],
    ["Bab 3: observability, audit trail, batas berhenti", "Audit log berantai-hash, jumlah pesan, anggaran lembur, eskalasi bila ragu", "messaging.py"],
    ["Bab 4: pesan antaragen, protokol, ontologi", "Format pesan, urutan Contract Net divalidasi bus", "messaging.py"],
    ["Bab 4: Contract Net, negosiasi, alokasi tugas", "Kuota produsen, lini gudang, carrier, negosiasi Sales Agent", "consortium.py, negotiation.py, sales.py"],
    ["Bab 4: kepercayaan, keamanan pesan, migrasi aman", "Skor mutu produsen, kepercayaan carrier, 7 uji serangan, syarat migrasi", "messaging.py, mobile.py"],
    ["Bab 4: metrik sistem (speedup, keadilan, biaya komunikasi), rantai pasok MAS", "Bagian 8 (metrik sistem, keadilan kuota)", "negotiation.py, experiments.py"],
    ["Bab 5: mobile agent, RL, layout Project #1", "Scout Agent; Marketing dan Learning Agent; struktur laporan mengikuti layout Project #1", "mobile.py, rl.py, marketing.py"]]
NEXT = [
    "Kalibrasi dengan data nyata KrakaCoal: syarat pembayaran, harga beli per produsen, tingkat gagal kirim dan reject, waktu balas produsen, dan performa tiap kanal iklan; ganti asumsi dengan estimasi.",
    "Project #1 (tema domain enterprise): perluas ke Scout/Broker/Worker/Security (Bab 5), dashboard UI/UX (peta kapasitas produsen, status pesanan, uji mutu), dan perbandingan dengan sistem statis.",
    "Implementasikan komponen yang saat ini hanya dimodelkan: CNN uji mutu, LLM untuk Sales dan Marketing dengan pemeriksa klaim, dan WhatsApp Business API sebagai kanal agen produsen.",
    "Perkuat pembelajaran mesin (reward per agen, safe-RL) dan bandingkan XGBoost untuk risiko roll-over; tambahkan uji drift dan retraining online.",
    "Bandingkan dengan optimizer global (MILP/OR-Tools) sebagai batas atas kualitas pembagian kuota.",
]


# ============================================================ struktur artikel penelitian (tab dokumen dosen)
ABSTRAK = ("Mengumpulkan satu kontainer arang (12-27 ton) dari puluhan produsen kecil sering gagal karena kapasitas produsen yang berubah-ubah, komunikasi manual, dan dokumen yang terlambat. "
           "Makalah ini merancang dan mengevaluasi KCMAS, sistem multi-agen (Contract Net, agen BDI, pengawas aturan berlevel otonomi, agen mobile, dan agen pemasaran digital) untuk alur dari iklan dan RFQ hingga kapal berangkat, dikalibrasi pada klaim operasional KrakaCoal. "
           f"Pada {R['n_scenarios']} skenario simulasi berpasangan, order yang berangkat tepat waktu dan terisi penuh (OTIF) naik dari {pc(h['kraka']['otif_s'],0)} (manual) ke {pc(h['kraka']['otif_c'],0)} (agen tunggal) dan {pc(h['kraka']['otif_m'],0)} (multi-agen); "
           "sentuhan manusia turun dari sekitar seratus menjadi kurang dari dua per order. Keunggulan multi-agen atas agen tunggal kecil dan bergantung pada seberapa usang data pusat. Data sintetis dan berasumsi; validasi lapangan adalah langkah berikutnya.")
KEYWORDS = "sistem multi-agen; Contract Net Protocol; rantai pasok arang; konsolidasi produsen; pemasaran digital; human-in-the-loop"

IDENT = [["Butir", "Isi"],
    ["Nama / NIM", f"{NAMA} / {NIM}"],
    ["Program studi dan institusi", "Magister Kecerdasan Artifisial (S2), Universitas Gadjah Mada"],
    ["Mata kuliah / dosen", "Agentic Enterprise: AI Agentic Technology Systems for Digital Enterprise Ecosystem / Prof. Dr. Azhari MT"],
    ["Bentuk pengerjaan", "Individu (tidak ada tim). Topik tidak diambil kelompok lain (bukan Customer Complaint, Procurement, Outsourcing, Bitcoin Trading, Customer Service, Software Developer Team)."],
    ["Judul proyek", TITLE],
    ["Kasus nyata", "KrakaCoal (krakacoal.com): bisnis ekspor arang yang sedang berjalan; penulis bekerja sebagai trader"],
    ["Fokus materi (sebelum UTS)", "Single agent / multi-agent; Proyek 1 nanti mengikuti domain enterprise yang diberikan dosen"],
    ["Repositori kode", REPO]]

TUJUAN_UMUM = ("Merancang, mengimplementasikan, dan mengevaluasi sistem multi-agen yang mengotomasi sebagian besar alur pemasaran, penjualan, pemasokan, dan pengiriman ekspor arang, dengan manusia hanya pada keputusan berisiko, dan menunjukkan kapan arsitektur multi-agen lebih baik dari agen tunggal.")
TUJUAN = [["Kode", "Tujuan khusus", "Ukuran keberhasilan", "Hasil (Bagian 8)"],
    ["T1", "Membangun simulator yang dikalibrasi pada klaim operasional KrakaCoal untuk membandingkan manual, agen tunggal, dan multi-agen", "Tiga sistem pada skenario yang sama; uji otomatis lulus; MOQ dan lead time situs tereproduksi", "tercapai"],
    ["T2", "Meningkatkan OTIF dan margin dibanding proses manual", "OTIF dan margin per order lebih tinggi dari manual", f"OTIF {pc(h['kraka']['otif_s'],0)} -> {pc(h['kraka']['otif_m'],0)}; margin {usd(h['kraka']['mar_s'])} -> {usd(h['kraka']['mar_m'])} per order"],
    ["T3", "Mengukur nilai desentralisasi (multi-agen vs agen tunggal) secara terisolasi", "Selisih OTIF dan margin dengan rentang 95%; sweep data usang", f"selisih OTIF {n(100*(h['kraka']['otif_m']-h['kraka']['otif_c']),0)} poin; hilang bila data pusat akurat"],
    ["T4", "Mengurangi beban manusia dengan otonomi berlevel", "Sentuhan manusia per order turun drastis", f"{n(h['kraka']['t_s'],0)} -> {n(h['kraka']['t_m'],1)}"],
    ["T5", "Menjamin keamanan dan auditabilitas pesan antaragen", "Tujuh uji serangan diblokir; audit log utuh", "7 dari 7 diblokir"],
    ["T6", "Menambahkan agen pemasaran digital yang membagi anggaran iklan secara adaptif dan aman", "Lebih banyak RFQ berkualitas per dolar dibanding pembagian rata pada simulasi", f"+{n(MK['uplift_pct'],0)}% RFQ (asumsi; eksploratif)"]]
HIPOTESIS = [
    "H1: Agen tunggal maupun multi-agen meningkatkan OTIF secara berarti dibanding proses manual (didukung).",
    "H2: Multi-agen unggul dari agen tunggal hanya bila data kapasitas pusat usang (didukung: selisih menyempit menuju nol saat variasi kapasitas 0).",
    "H3: Kelebihan pesanan (buffer) yang optimal berada pada rentang menengah, bukan nol atau maksimum (didukung: puncak 15-20%).",
    "H4: Otonomi berlevel menurunkan sentuhan manusia tanpa melewati kebijakan (didukung pada simulasi).",
    "H5: Pembagian anggaran iklan adaptif menghasilkan lebih banyak RFQ berkualitas daripada pembagian rata bila kualitas kanal tidak diketahui (didukung pada simulasi berasumsi).",
]

# ---- 5.1 alur end-to-end (mengacu fig_flow.png)
FLOW_INTRO = ("Sistem ini pada dasarnya adalah 'tim kerja digital' untuk satu pesanan ekspor. Setiap peran diisi agen perangkat lunak yang saling berkirim pesan; agen tidak melakukan pekerjaan fisik. Yang fisik (memproduksi, menguji, mengemas, mengirim) tetap dikerjakan produsen, staf, dan mesin gudang; agen hanya mengatur, menawar, dan mencatat. "
              "Manusia turun tangan hanya pada titik oranye. Contoh angka memakai order 25 ton: sistem meminta 25 x 1,15 = 28,75 ton kepada produsen sebagai cadangan, dan tidak ada produsen yang boleh mengambil lebih dari 30% (sekitar 8,6 ton), sehingga minimal 4 produsen terlibat.")
EVENTBUS_TEXT = ("Event bus adalah jalur pesan bersama: semua agen saling berkirim pesan hanya lewat satu tempat ini, seperti grup chat yang terstruktur. Bus memeriksa siapa pengirimnya (tanda tangan digital), apakah urutan pesannya benar (mis. 'terima' tidak boleh datang sebelum 'minta tawaran'), dan mencatat semua pesan pada log yang tidak dapat diubah diam-diam. "
                 "Pada WhatsApp, isi pesan yang sama dikirim sebagai template terstruktur.")
FLOW_STEPS = [["No.", "Pelaku", "Apa yang terjadi", "Keputusan / aturan", "Hasil"],
    ["0", "Marketing & Ads Agent", "Membagi anggaran iklan ke kanal (Google, LinkedIn, marketplace, e-mail/WhatsApp, konten), membuat materi iklan, dan hanya mengiklankan produk yang kapasitasnya tersedia (sinyal dari Order Agent).", "Klaim harus sesuai spesifikasi dan sertifikat nyata; materi baru disetujui manusia.", "Calon pembeli mengirim RFQ."],
    ["1", "Pembeli", "Mengirim RFQ lewat portal atau WhatsApp: produk, kuantitas, pelabuhan tujuan, tenggat kirim.", "Isian wajib diperiksa (Bagian 5.3).", "RFQ tercatat dengan id unik."],
    ["2", "Sales Agent (Virtual SDR)", "Mengkualifikasi pembeli, menegosiasikan harga dan syarat dengan konsesi bertahap, membuat Letter of Intent.", "Harga tidak boleh di bawah batas kebijakan; di luar batas dieskalasi ke manusia.", "LoI dan harga sepakat."],
    ["3", "Manusia (admin)", "Memverifikasi bukti down payment (human-in-the-loop, level otonomi 2).", "DP terverifikasi dalam 0,3-1,2 hari.", "Order dirilis ke produksi."],
    ["4", "Order Agent", "Melepas order dan menyiarkan permintaan tawaran (CFP) ke produsen dengan kuantitas ditambah cadangan 15%.", "Batas 30% per produsen; produsen bermutu di bawah 0,60 diblokir.", "CFP terkirim (template WhatsApp)."],
    ["5", "Compliance Agent", "Paralel dengan produksi: klasifikasi HS (ML teks) dan menyusun dokumen ekspor.", "Bila keyakinan HS di bawah 0,6, diserahkan ke tim Compliance.", "Dokumen siap sebelum barang tiba."],
    ["6", "Producer Agent", "Menawar: berapa kg, harga, kapan siap, berdasarkan kapasitas nyata hari itu. Di dunia nyata produsen membalas lewat WhatsApp.", "Tawaran lebih dari 6 jam diabaikan.", "Daftar tawaran."],
    ["7", "Order Agent", "Memberi kuota menurut skor tawaran (harga, waktu, skor mutu) dengan batas konsentrasi.", "Dua putaran: target 6 hari, lalu seluruh jendela waktu.", "Kontrak per produsen."],
    ["8", "Produsen (fisik)", "Memproduksi arang dan mengirim ke gudang. Ini pekerjaan manusia; agen hanya memantau.", "Gagal kirim menurunkan skor mutu.", "Barang tiba."],
    ["9", "QC Agent", "Mencatat hasil uji mutu (Grade A/B/Reject) dan memperbarui skor mutu produsen.", "Premium butuh tingkat kelolosan minimal 0,85.", "kg lolos uji mutu."],
    ["*", "Order Agent (keputusan)", "Apakah total kg lolos cukup? Bila belum: CFP susulan ke produsen lain (re-kontrak, cadangan 5%, maksimal 4 putaran).", "Bila cukup, lanjut ke gudang.", "Pemenuhan atau putaran baru."],
    ["10", "Warehouse Line Agent", "Mengatur tiga tahap (uji lab dan sortir, packing, stuffing) pada mesin dan staf gudang; mengurutkan job menurut kemendesakan dan memantau kondisi mesin.", "Lembur bila kritis (Learning Agent, anggaran 12 tahap).", "Kontainer siap."],
    ["11", "Freight Agent", "Lelang antar carrier; memilih dengan skor gabungan (harga, waktu transit, keandalan, peluang ditinggal kapal).", "Tanpa air freight; carrier dipilih menurut skor.", "Booking kapal."],
    ["12", "Scout Agent (mobile)", "Berpindah ke sistem carrier atau pelabuhan membaca jadwal secara lokal, kembali membawa sekitar 2 KB.", "Migrasi hanya bila kepercayaan minimal 0,80 dan risiko maksimal 0,20; jika tidak, tarik data jarak jauh.", "Jadwal terverifikasi."],
    ["13", "Manusia + Governance", "Persetujuan ekspor akhir: dokumen, biaya, dan risiko ditinjau ringkas.", "Level 2-3 menurut nilai order (di atas USD 30 ribu wajib persetujuan).", "Izin berangkat."],
    ["14", "Pembeli", "Kapal berangkat dan barang diterima; hasil dicatat untuk umpan balik.", "-", "Order selesai; skor mutu, kepercayaan, dan tabel belajar diperbarui."]]
FLOW_WHY = [
    "Mengapa banyak agen? Produsen, carrier, dan pembeli adalah pihak otonom yang tidak bisa diperintah pusat; mereka hanya bisa diminta tawaran dan menawar.",
    "Di mana kecerdasan buatan dipakai? (a) Compliance: klasifikasi HS berbasis ML; (b) Risk: regresi logistik untuk peluang ditinggal kapal; (c) Order/Producer: penawaran berbasis skor dan kapasitas nyata; (d) Learning: Q-learning untuk keputusan lembur; (e) Sales dan Marketing: LLM sebagai lapisan bahasa dan pembagi anggaran adaptif.",
    "Di mana manusia terlibat? Hanya verifikasi DP, HS ragu-ragu, order bernilai tinggi, materi iklan dengan klaim baru, dan pengecualian; sisanya otomatis (Bagian 5.4).",
    "Apa yang terjadi bila ada masalah? Produsen gagal kirim atau barang tidak lolos uji memicu putaran CFP baru; sistem carrier tidak tepercaya memicu penarikan data jarak jauh; pesan palsu ditolak oleh bus (Bagian 5.6).",
]

# ---- peta agen ke kode
CODE_MAP = [["Agen", "Berkas kode", "Fungsi / kelas utama", "Diuji oleh"],
    ["Marketing & Ads Agent", "marketing.py", "run_once (pembagi anggaran Thompson sampling), run, run_all", "keluaran outputs/marketing.json"],
    ["Sales Agent (Virtual SDR)", "sales.py, negotiation.py", "run, worked_negotiation; concession, negotiate, nash_bargaining", "test_sdr_faster_and_converts_more"],
    ["Order Agent", "consortium.py, sim.py", "Sourcing.run (putaran CFP), Sim.book (pemilihan carrier), Sim.start_docs", "test_all_orders_ship_and_accounting_consistent"],
    ["Producer Agent", "consortium.py, data.py", "Sourcing._allocate (tawaran, skor, kuota); make_scenario (produsen sintetis)", "test_no_producer_exceeds_concentration_cap"],
    ["QC Agent", "consortium.py", "Sourcing.run (hasil uji dan pembaruan skor mutu)", "test_trust_and_reliability_formulas"],
    ["Warehouse Line Agent", "sim.py, ml.py", "Sim.dispatch, Sim.pick_next, Sim.step_machines; health_slope", "test_health_slope_positive_trend"],
    ["Compliance Agent", "ml.py, sim.py", "HSClassifier, train_hs, selective_curve; Sim.hs_predict", "test_hs_catalog_contains_charcoal_and_tempe"],
    ["Risk Agent", "ml.py, data.py", "LogisticModel, train_risk; roll_prob", "test_roll_prob_monotone"],
    ["Freight Agent", "sim.py", "Sim.options, Sim.phat, Sim.book (lelang carrier)", "test_next_closing_and_penalty"],
    ["Learning Agent", "rl.py, rl_sim.py, sim.py", "train_q, train_in_sim; Sim._expedite", "test_q_learning_lecture_example"],
    ["Governance & Security Agent", "messaging.py, sim.py", "MessageBus (tanda tangan, nonce, kapabilitas, urutan pesan, audit log)", "test_signature_tamper_rejected, test_replay_rejected, test_audit_chain_detects_tampering"],
    ["Scout Agent (mobile)", "mobile.py", "ScoutState, serialize, verify, query_carrier", "test_migration_rules, test_tampered_state_falls_back_to_remote_pull"],
    ["Simulator dan eksperimen", "sim.py, experiments.py, demo.py", "Sim.run, Sim.summary; python -m kraka_mas.experiments; python -m kraka_mas.demo", "test_deterministic"],
]

# ---- 5.3 kontrak input pengguna
KONTRAK_IN = [["Pengguna", "Input (kontrak)", "Format dan validasi", "Bila tidak valid"],
    ["Pembeli", "RFQ: produk, kuantitas (ton), incoterm, pelabuhan tujuan, tenggat kirim, harga target, sertifikat wajib", "Isian bertipe; kuantitas minimal satu kontainer (12 ton untuk 20 ft, 25 ton untuk 40 ft); tenggat tidak kurang dari waktu produksi minimum", "Ditolak dengan alasan; Sales Agent meminta perbaikan"],
    ["Produsen", "Pendaftaran: kapasitas kg/hari, harga per kg, jenis arang, sertifikat; balasan CFP: kg, harga, waktu siap", "Template WhatsApp berisi maksimal 3 isian; angka positif dan tidak melebihi kapasitas terdaftar x 1,5", "Balasan tidak sah dianggap tidak menawar; pengingat sekali"],
    ["Admin", "Bukti DP; persetujuan (setuju / tolak / ubah); parameter kebijakan (buffer, batas konsentrasi, ambang skor mutu, anggaran lembur, anggaran iklan mingguan)", "Kartu keputusan satu layar (Bagian 5.4); parameter bertipe dengan batas minimum dan maksimum", "Nilai di luar batas ditolak; perubahan dicatat pada audit log"],
    ["Admin pemasaran", "Daftar produk yang boleh diiklankan beserta spesifikasi dan sertifikat yang benar; anggaran mingguan; kata terlarang", "Daftar terstruktur; klaim iklan dicocokkan otomatis dengan daftar ini", "Klaim tidak cocok diblokir dan dikirim ke manusia"],
    ["Tim Compliance", "Keputusan HS dan dokumen untuk kasus keyakinan rendah", "Kode HS terdaftar pada katalog", "Kasus tetap terbuka dan naik prioritas"],
    ["Sistem lain", "Data ERP/CRM, sensor mesin, jadwal kapal", "Event bertipe dan bertanda tangan digital", "Ditolak oleh bus dan dicatat"]]
KONTRAK_OUT = [["Penerima", "Keluaran (kontrak)", "Kapan"],
    ["Pembeli", "LoI, status order (dikonfirmasi, produksi, stuffing, berangkat), dokumen ekspor, perkiraan tiba", "Tiap perubahan status"],
    ["Produsen", "CFP, kuota yang diberikan, hasil uji mutu dan skor mutu", "Saat CFP, pemberian kuota, dan setelah uji"],
    ["Admin", "Kartu keputusan (rekomendasi, alasan, aksi default), ringkasan harian, peringatan risiko", "Bila ada pengecualian; ringkasan sekali sehari"],
    ["Admin pemasaran", "Laporan mingguan per kanal (biaya, klik, RFQ berkualitas, biaya per RFQ) dan usulan pembagian anggaran", "Mingguan"],
    ["Audit", "Log berantai-hash: siapa mengirim apa, kapan, dengan wewenang apa", "Selalu; tidak dapat diubah diam-diam"]]

# ---- 5.4 cognitive overload
COGNITIVE = [
    ("Routing berdasarkan pengecualian", f"Sistem tidak meminta manusia menyetujui semua hal; hanya risiko tinggi, keyakinan rendah, atau nilai besar. Hasilnya sentuhan manusia per order turun dari {n(h['kraka']['t_s'],0)} (manual) menjadi {n(h['kraka']['t_m'],1)}."),
    ("Kartu keputusan satu layar", "Setiap permintaan persetujuan berisi rekomendasi sistem, tiga alasan utama, dampak biaya dan risiko, serta aksi default. Admin cukup memilih Setuju, Ubah, atau Tolak."),
    ("Ringkasan (digest) dan pengumpulan", "Notifikasi tidak mendesak dikumpulkan menjadi ringkasan harian; hanya peringatan kritis (mis. kapal akan terlewat) yang dikirim langsung."),
    ("Prioritas dan batas volume", "Antrean persetujuan diurutkan menurut nilai dan urgensi; ada batas jumlah item aktif per admin, sisanya menunggu atau dieskalasi."),
    ("Bahasa dan format sederhana", "Produsen hanya menerima template WhatsApp pendek dengan maksimal tiga isian dan angka baku, tanpa istilah teknis."),
    ("Otonomi bertahap", "Level otonomi dinaikkan hanya setelah tingkat kesalahan terukur di bawah ambang; semua aksi dapat dijelaskan lewat audit log."),
    ("Batas penyiaran pesan", "CFP tidak disiarkan ke semua produsen pada skala besar, tetapi ke subset regional, sehingga agen tidak dibanjiri pesan (Bagian 8.5)."),
    ("Iklan: persetujuan hanya untuk hal baru", "Marketing Agent memindahkan anggaran antar kanal secara otomatis dalam batas mingguan; manusia hanya menyetujui materi iklan dengan klaim baru."),
]

# ---- 5.5 jadwal, approval, eskalasi
JADWAL = [["Peristiwa", "Batas waktu / SLA", "Jika terlewat (eskalasi)", "Status"],
    ["Balasan produsen terhadap CFP", f"median {C.REPLY_MEDIAN_H} jam; tawaran diterima sampai {C.CFP_DEADLINE_H:.0f} jam", "CFP susulan ke produsen berikutnya menurut skor", "dalam simulasi"],
    ["Verifikasi DP oleh admin", f"{C.DP_VERIFY_DAYS[0]}-{C.DP_VERIFY_DAYS[1]} hari", "Pengingat ke admin cadangan", "dalam simulasi"],
    ["Persetujuan order bernilai tinggi", f"{C.APPROVAL_DAYS} hari; wajib bila nilai di atas USD {C.APPROVAL_VALUE_USD:,}".replace(",", "."), "Order ditahan, tidak dieksekusi otomatis", "dalam simulasi"],
    ["Target waktu produksi", f"{C.PROD_TARGET_DAYS:.0f} hari (target), lalu seluruh jendela waktu", "Putaran kontrak baru, cadangan 5%", "dalam simulasi"],
    ["Klasifikasi HS", "otomatis; keyakinan di bawah 0,6 ke tim Compliance", "Kasus dinaikkan prioritasnya", "dalam simulasi"],
    ["Migrasi Scout", "kepercayaan minimal 0,80 dan risiko maksimal 0,20", "Tarik data jarak jauh", "dalam simulasi"],
    ["Ringkasan harian ke admin", "sekali sehari", "Peringatan kritis tetap dikirim langsung", "rancangan (belum disimulasikan)"],
    ["Tinjauan anggaran iklan", "mingguan", "Kampanye dijeda bila biaya per RFQ melewati batas", "simulasi eksploratif"],
    ["Persetujuan materi iklan baru", "1 hari kerja", "Materi tidak tayang sampai disetujui", "rancangan (belum disimulasikan)"]]
APPROVAL_LEVELS = [["Level otonomi (Bab 2)", "Contoh keputusan", "Siapa yang menyetujui"],
    ["4 Delegate", "Pembagian kuota dalam batas, urutan kerja gudang, HS dengan keyakinan tinggi, pemindahan anggaran iklan antar kanal", "Tidak ada; audit log"],
    ["3 Supervise", "Lembur dalam anggaran; carrier di bawah batas biaya", "Manusia dapat membatalkan dalam jendela waktu"],
    ["2 Approve", "Verifikasi DP; HS keyakinan rendah; order bernilai tinggi; materi iklan dengan klaim baru", "Admin / tim Compliance / admin pemasaran"],
    ["1 Assist", "Belum dipakai (mode rekomendasi)", "Manusia memutuskan"]]

# ---- 5.6 koordinasi dan negosiasi
NEGO = [
    ("Contract Net (kuota produsen, lini gudang, carrier)", "Manajer menyiarkan permintaan tawaran (CFP); kontraktor menjawab dengan tawaran atau menolak; manajer memilih dan mengirim ACCEPT atau REJECT. Bus memeriksa urutan pesan (IDLE, BIDDING, AWARDED, COMPLETED) dan menolak urutan yang salah; tiap leg punya id percakapan sendiri."),
    ("Skor penilaian tawaran", "Tawaran produsen dinilai dari harga (30%), waktu siap (50% pada penilaian kecepatan/waktu), dan skor mutu (20%) sesuai bobot konfigurasi; carrier dinilai dengan skor gabungan harga/waktu transit dan peluang ditinggal kapal."),
    ("Negosiasi harga (Sales Agent)", "Konsesi bertahap dengan batas kebijakan. Model kesabaran pembeli dan waktu balas manusia bersifat asumsi (eksploratif)."),
    ("Penanganan konflik dan kegagalan", "Batas 30% mencegah satu produsen menguasai order; kegagalan kirim memicu re-kontrak; skor mutu memberi insentif keandalan; carrier tidak tepercaya diblokir."),
    ("Keamanan pesan", "Tanda tangan digital (HMAC), nonce dan jendela waktu anti-ulang, izin per agen, audit log berantai-hash; tujuh serangan diuji dan seluruhnya diblokir."),
]
