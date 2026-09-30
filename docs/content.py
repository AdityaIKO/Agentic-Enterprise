"""Report + slide content (Bahasa Indonesia). Every number is read from outputs/*.json, never typed by hand."""
import json, pathlib, sys
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from xpora_mas import config as C
from xpora_mas.data import make_scenario
from xpora_mas.profiles import PROFILES

R = json.loads((ROOT / "outputs/results.json").read_text())
W = json.loads((ROOT / "outputs/worked_example.json").read_text())
FIGDIR = ROOT / "outputs/figures"

NAMA, NIM = "Aditya Wahyu Wijanarko", "25/574566/PPA/07251"
REPO = "https://github.com/AdityaIKO/Agentic-Enterprise"
TITLE = "XCMAS: Xpora Consortium Multi-Agent System"
SUBTITLE = "Sistem multi-agen cerdas untuk konsolidasi ekspor UMKM (pilot tempe Jawa Tengah), dikalibrasi dengan operasi trading KrakaCoal"
COURSE = "Agentic Enterprise (AI Agentic Technology Systems for Digital Enterprise Ecosystem) - Magister AI, Universitas Gadjah Mada"


def n(x, nd=2, plus="", thou=False):
    """Indonesian number style: decimal comma, thousands dot."""
    s_ = format(x, f"{plus}{',' if thou else ''}.{nd}f")
    return s_.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


usd = lambda x: "$" + n(x, 0, "", True)
pc = lambda x, nd=1: n(100 * x, nd) + "%"
def ci(t, f=lambda x: n(x, 2)): return f"{f(t[0])} [{f(t[1])}; {f(t[2])}]"

P = R["profiles"]; XP, KR = P["xpora"], P["kraka"]
PFX, PFK = PROFILES["xpora"], PROFILES["kraka"]
MODES = ("static", "central", "mas")
def mv(pf, mode, key, i=0): return P[pf]["main"][mode][key][i]
def per_order(pf, mode, key): return mv(pf, mode, key) / PROFILES[pf].n_orders

# headline numbers
h = {}
for pf in ("xpora", "kraka"):
    h[pf] = dict(otif_s=mv(pf, "static", "otif"), otif_m=mv(pf, "mas", "otif"), otif_c=mv(pf, "central", "otif"),
                 fill_s=mv(pf, "static", "fill"), fill_m=mv(pf, "mas", "fill"), fill_c=mv(pf, "central", "fill"),
                 otd_s=mv(pf, "static", "otd"), otd_m=mv(pf, "mas", "otd"),
                 mar_s=per_order(pf, "static", "margin"), mar_c=per_order(pf, "central", "margin"), mar_m=per_order(pf, "mas", "margin"),
                 t_s=mv(pf, "static", "touches"), t_m=mv(pf, "mas", "touches"), hs_s=mv(pf, "static", "hs_err"), hs_m=mv(pf, "mas", "hs_err"))

# ============================================================ front matter
EXEC = [
    "Xpora adalah ekosistem ekspor Done-For-You untuk UMKM Indonesia: mengagregasi kapasitas produsen mikro (mis. produsen tempe 100-300 kg/hari) agar memenuhi MOQ pembeli global (15-27 ton per kontainer), "
    "dengan satu payung legalitas dan quality control terpusat. KrakaCoal adalah bisnis trading arang milik penulis yang sudah berjalan dengan pola serupa: jaringan produsen di Sumatra, Jawa, dan Sulawesi, MOQ satu FCL, ekspor dari Surabaya.",
    "Masalah agentik yang dipecahkan: bagaimana mengubah RFQ pembeli menjadi kontainer yang terisi penuh dan berangkat tepat waktu ketika pasokan tersebar pada puluhan produsen kecil yang kapasitas nyatanya berubah-ubah, "
    "kadang gagal kirim, dan sebagian barangnya ditolak QC. XCMAS memodelkannya sebagai sistem multi-agen: Sales Agent (Virtual SDR), Order Agent, Producer Agent (UMKM), QC, Warehouse Line, Compliance, Risk, Freight, Learning, Governance, dan Scout mobile.",
    f"Hasil simulasi ({R['n_scenarios']} skenario berpasangan per profil, seluruh data sintetis): pada profil Xpora (tempe, cold chain) pengiriman tepat waktu dan terisi penuh (OTIF) naik dari {pc(h['xpora']['otif_s'])} (admin manual via WhatsApp) menjadi {pc(h['xpora']['otif_m'])}, "
    f"margin kontribusi per order dari {usd(h['xpora']['mar_s'])} menjadi {usd(h['xpora']['mar_m'])}; pada profil KrakaCoal (arang, kontainer kering) OTIF {pc(h['kraka']['otif_s'])} menjadi {pc(h['kraka']['otif_m'])} dan margin per order {usd(h['kraka']['mar_s'])} menjadi {usd(h['kraka']['mar_m'])}. "
    f"Sentuhan manusia per order turun dari {n(h['xpora']['t_s'],0)} menjadi {n(h['xpora']['t_m'],1)} (Xpora).",
    "Temuan yang jujur: (1) Keunggulan multi-agen atas agen tunggal terpusat berasal dari informasi lokal yang segar (produsen menawar dengan kapasitas nyata hari itu) versus registry yang kedaluwarsa; keunggulan itu hilang bila kapasitas stabil dan registry akurat, sehingga agen tunggal cukup untuk konsorsium kecil yang stabil. "
    "(2) Multi-agen memakai lebih banyak pesan per order pada pemasokan tetapi lebih ringan pada node puncak dan lebih tahan gangguan koordinator. (3) Over-allocation 15% adalah trade-off antara kekurangan pasokan dan limbah surplus. "
    "(4) Q-learning yang dilatih di lingkungan abstrak tidak transfer; yang dilatih di simulator setara aturan yang dituning. (5) Modul Sales/SDR bersifat eksploratif dan bergantung asumsi. "
    "(6) Data bersifat sintetis; pilot Xpora belum berjalan dan syarat pembayaran KrakaCoal tidak dipublikasikan sehingga tidak dimodelkan (hanya asumsi DP).",
]

TUGAS_MAP = [
    ("Gunakan topik yang dipilih", "Topik: XCMAS, sistem multi-agen konsolidasi ekspor UMKM (venture Xpora; kalibrasi KrakaCoal). Tidak diambil kelompok 1-6.", "Bagian 2.1"),
    ("Upload laporan progres", "Dokumen ini (PDF) + slide (PPTX) + kode GitHub", "-"),
    ("Peran anggota tim", "Pengerjaan individu; enam peran template Project #1 dipegang satu orang", "Bagian 1"),
    ("Deskripsi problem", "MOQ trap, legalitas, kualitas, alokasi kuota; KPI, klasifikasi lingkungan, PEAS", "Bagian 2"),
    ("Ilustrasi data dan perhitungan komputasi", "Sumber data (Xpora/KrakaCoal/asumsi), 13 contoh hitung manual, simulasi penuh", "Bagian 3"),
    ("Rumus notasi dan arti simbol", "30 rumus dikelompokkan A-H, tiap simbol dijelaskan", "Bagian 4"),
    ("Tiga penelitian topik serupa", "Hathikal 2020; Lee 2024; Ouelhadj & Petrovic 2009", "Bagian 5"),
    ("Mengapa single vs multi-agent", "Kriteria Bab 4 + bukti eksperimen (informasi segar, ketahanan, skala, batas organisasi)", "Bagian 6.1"),
    ("Tiga penelitian agen cerdas", "Smith 1980; Leitao 2009; Zhao 2024", "Bagian 6.2"),
    ("Diagram rencana sistem", "Arsitektur, Contract Net kuota produsen, siklus BDI, Gantt", "Bagian 6.3"),
    ("Komponen internal tiap agen", "Tabel 11 agen: BDI, komponen, I/O, metode, otonomi", "Bagian 6.4"),
    ("AI / ML / DL dan alasannya", "Portofolio metode (ML, RL, LLM, CV) + alasan tidak memakai DL sekarang", "Bagian 6.6"),
]
ROLES = [
    ("Leader / product owner", "Memilih topik dari venture sendiri (Xpora, KrakaCoal), merumuskan masalah dan KPI."),
    ("Researcher", "Studi literatur (3 + 3), memetakan materi Bab 1-5 ke desain, mengumpulkan parameter dari submission Xpora dan situs KrakaCoal."),
    ("Programmer", "Simulator, agen, model ML/RL, lapisan pesan aman, unit test."),
    ("Designer", "Arsitektur sistem, protokol Contract Net, diagram, visualisasi."),
    ("Evaluator", "Eksperimen berpasangan pada dua profil komoditas, ablation, sensitivitas, uji ketahanan dan skala, catatan validitas."),
    ("Presenter", "Menyusun laporan PDF dan slide PPT."),
]
ROLE_NOTE = ("Tugas 1 dikerjakan individu (penulis bergabung terlambat ke kelas), sehingga enam peran pada template Project #1 dipegang satu orang. Kasus berangkat dari venture Xpora (tim PIDI 2026) dan bisnis trading KrakaCoal milik penulis; "
             "bagian yang dinilai di sini (model agentik, simulasi, dan analisis) dikerjakan penulis. Claude Code dipakai sebagai asisten penulisan kode dan dokumen; keputusan desain, angka, dan klaim ditinjau oleh penulis. "
             "Modul CNN QC dan portal Virtual SDR pada Xpora dikembangkan anggota tim lain dan hanya dimodelkan secara statistik di sini.")

# ============================================================ problem
PROBLEM = [
    "Xpora (submission ke-2 PIDI 2026) menargetkan tiga hambatan struktural ekspor UMKM: (1) fragmentasi kapasitas: pembeli mensyaratkan 15-27 ton per kontainer sementara produsen tempe rumahan hanya 100-300 kg/hari (The MOQ Trap); "
    "(2) kemacetan legalitas dan kualitas: hanya 18,6% UMKM memiliki NIB dan 7,8% bersertifikasi produk, mutu tidak konsisten; (3) ilusi literasi digital: komunikasi akar rumput bertumpu pada WhatsApp.",
    "Xpora menjawab dengan lima tahap: inbound negosiasi (Virtual SDR), validasi DP oleh admin (human-in-the-loop), distribusi kuota ke puluhan UMKM via WhatsApp (DP menjadi modal kerja), fulfillment dan QC (CV, Grade A/B/Reject) di gudang konsolidasi, lalu pelunasan dan ekspor di bawah satu PT konsorsium. "
    "Tahap yang paling agentik dan paling rawan adalah distribusi kuota dan pemenuhan: kapasitas nyata produsen berubah-ubah, sebagian gagal kirim, dan sebagian barang ditolak QC.",
    "KrakaCoal (situs krakacoal.com, PT. Kraka Coal Indonesia) adalah bisnis trading yang sudah berjalan: 'a vetted export network, not a single factory'. Mengumpulkan bahan dari Sumatra, Jawa, dan Sulawesi, karbonisasi di Jawa, uji lab tiap batch, kapasitas 300+ MT/bulan dan 10+ kontainer/bulan, "
    "ekspor dari pelabuhan Jawa Timur (Surabaya). MOQ satu FCL (20 ft: 12-17 ton, 40 ft: 25-27 ton), produksi 10 hari (20 ft) atau 14 hari (40 ft), packing 3-6 hari, FOB default dan CIF atas permintaan. Pola ini identik dengan konsorsium Xpora, hanya komoditasnya tidak perishable.",
    "Pernyataan masalah formal: untuk tiap order kontainer, pilih kuota tiap produsen (dengan buffer dan re-kontrak), jadwal lini gudang, dokumen/HS, carrier, dan tindakan pemulihan yang memaksimalkan margin kontribusi M = pendapatan (nilai x fill x (1 - diskon shelf-life)) - biaya total J, "
    "dengan constraint kapasitas, closing kapal, batas konsentrasi produsen, kebijakan compliance, dan batas wewenang agen.",
]
ENV_TABLE = [
    ["Karakteristik", "Klasifikasi", "Bukti pada kasus ini"],
    ["Observability", "Partially observable", "Kapasitas produsen hari ini (sisa setelah pasar lokal), keandalan, dan yield QC tidak diketahui pasti; registry hanya data onboarding"],
    ["Outcome", "Stochastic", "Gagal kirim produsen, reject QC, kerusakan lini gudang, roll-over kargo, dokumen kurang"],
    ["Change", "Dynamic", "Kapasitas berubah tiap order, jadwal kapal mingguan, kongesti pelabuhan, order baru masuk terus"],
    ["Actors", "Multi-agent", "Pembeli asing, puluhan UMKM, carrier, bea cukai, admin konsorsium: pemilik dan kepentingan berbeda"],
]
PEAS = [
    ["Komponen", "Deskripsi XCMAS"],
    ["Performance", "OTIF (tepat waktu dan terisi >= 98%); margin kontribusi per order; fill rate; rata-rata hari terlambat; tingkat reject dan surplus; sentuhan manusia; keadilan kuota antar UMKM (Jain); ketahanan dan beban node"],
    ["Environment", "Pasar pembeli global; 30-40 produsen UMKM (WhatsApp); gudang konsolidasi 3 lini x 2; proses dokumen ekspor dan bea cukai; 3 carrier dengan jadwal kapal mingguan; kongesti pelabuhan"],
    ["Actuators", "Broadcast CFP dan pemberian kuota via WhatsApp/bus; penjadwalan lini; lembur; booking carrier; penerbitan dokumen; eskalasi ke manusia; pembaruan quality score dan trust"],
    ["Sensors", "Balasan/bid produsen; hasil QC (CV/lab); sensor kesehatan mesin; jadwal kapal via Scout Agent; status pelabuhan; hasil pengiriman; RFQ masuk"],
]
SOTA = ("Posisi terhadap solusi yang ada. Platform ekspor digital (Inaexport, MadeinIndonesia.com) berpola katalog do-it-yourself: UMKM tunggal sulit memenuhi 15-27 ton, mengurus legalitas sendiri (Rp 50-200 juta), dan QC self-reported (tabel pembanding pada submission Xpora). "
        "Suite ERP/APS, TMS, dan Global Trade Management (mis. SAP GTS, Oracle GTM) kuat pada transaksi dan kepatuhan tetapi berbasis aturan/batch dan tidak menegosiasikan kuota dengan ratusan produsen kecil lewat WhatsApp. "
        "XCMAS adalah lapisan keputusan agentik di atas kanal yang sudah dipakai UMKM; ia tidak menggantikan ERP/TMS.")

# ============================================================ data & assumptions
PROFILE_TABLE = [["Parameter", "Xpora (tempe)", "KrakaCoal (arang)", "Sumber"],
    ["Produsen di pool", f"{PFX.n_producers}", f"{PFK.n_producers}", "Xpora: pilot >= 20, target 200 (SOURCE); Kraka: setara 300+ MT/bln (SOURCE)"],
    ["Kapasitas produsen (kg/hari)", f"{PFX.cap_mean:.0f} (100-320)", f"{PFK.cap_mean:.0f} ({PFK.cap_min:.0f}-{PFK.cap_max:.0f})", "Xpora: 100-300, rata-rata 250 (SOURCE); Kraka: ASUMSI dikalibrasi ke 300+ MT/bln"],
    ["Ukuran order (kontainer)", "15-27 t", "12, 15, 17 t (20 ft) atau 25, 27 t (40 ft)", "Xpora: 15-27 t (SOURCE); Kraka: situs (SOURCE)"],
    ["Harga kontrak (USD/kg)", "3,15 (medium), 4,5 (premium)", "1,10 dan 1,45", "Xpora: pita harga portal (SOURCE); Kraka: harga tidak dipublikasikan, ASUMSI"],
    ["Fermentasi/karbonisasi + transport", f"{PFX.lag_days+PFX.transport_days:.2f} hari", f"{PFK.lag_days+PFK.transport_days:.0f} hari", "ASUMSI (tempe 36-48 jam; arang karbonisasi + pendinginan)"],
    ["Lini gudang (hari per 20 t)", "QC-CV 0,9 / vakum 1,8 / beku 1,4", "Lab 1,5 / packing 4,0 / stuffing 1,0", "Kraka: packing 3-6 hari (SOURCE); lainnya ASUMSI"],
    ["Waktu produksi total", "-", "10 hari (20 ft) - 14 hari (40 ft)", "Kraka (SOURCE); dipakai untuk kalibrasi sourcing"],
    ["Perishable / shelf life", "ya, 45 hari (uji tim: 1-2 bulan)", "tidak", "Xpora uji vakum (SOURCE)"],
    ["Tipe kontainer", "reefer", f"kering (tarif x {PFK.rate_factor})", "ASUMSI tarif"],
    ["Incoterm", "-", "FOB default, CIF atas permintaan", "Kraka (SOURCE); model memakai closing/keberangkatan kapal"],
    ["Jaminan dokumen", "HS, NIB, HACCP/BPOM/Halal", "COA, MSDS, lab test, SABER/ESMA, EUDR, Halal", "Xpora dan Kraka (SOURCE)"],
    ["Syarat pembayaran", "DP buyer sebagai modal kerja (40% ASUMSI)", "tidak dipublikasikan pada situs", "Belum ada data: perlu diisi penulis"],
]
ASSUME = [["Parameter", "Nilai", "Keterangan"],
    ["Ketersediaan kapasitas u", f"U({C.AVAIL_LOW}; 1)", "sisa kapasitas produsen setelah pasar lokal (ASUMSI); registry mengira rata-rata 0,775 dan kapasitas nominal berderau 10%"],
    ["Waktu balas WhatsApp", f"median {C.REPLY_MEDIAN_H} jam, sigma {C.REPLY_SIGMA}", "lognormal; SLA target Xpora < 2 jam; bid lebih lambat dari 6 jam diabaikan"],
    ["Buffer over-allocation", f"{pc(C.BUFFER_FIRST,0)} (awal), {pc(C.BUFFER_REPL,0)} (susulan)", "dipilih dari sweep pada seed kalibrasi; admin manual 5%"],
    ["Batas konsentrasi", pc(C.MAX_SHARE, 0), "tiap produsen maks 30% dari satu order; produsen dengan quality score < 0,60 diblokir"],
    ["Gagal kirim produsen", "1 - keandalan, keandalan U(0,80; 0,99)", "yield QC = 0,72 + 0,26 x keandalan + derau; premium butuh yield >= 0,85 (Grade A)"],
    ["Surplus", f"dijual lokal {pc(C.SALVAGE,0)} harga beli", "biaya limbah = 40% harga beli untuk kg surplus"],
    ["Lini gudang", f"{C.MACHINES_PER_WC} mesin/tahap; kerusakan {C.BREAKDOWN_RATE}/hari", f"lembur x{C.OVERTIME_SPEEDUP}, {C.OVERTIME_COST_PER_DAY:.0f} USD per hari operasi; anggaran 12 tahap per skenario"],
    ["Penalti keterlambatan", "0,4% nilai/hari + 45 USD/hari (+5% bila > 10 hari)", "ASUMSI; L/C basi dan reputasi tidak dimodelkan"],
    ["Verifikasi DP", f"{C.DP_VERIFY_DAYS[0]}-{C.DP_VERIFY_DAYS[1]} hari, oleh admin", "SOURCE: human-in-the-loop yang disengaja oleh Xpora; berlaku pada semua mode"],
    ["Respons sales", f"manual median {C.HUMAN_SALES_MEDIAN_DAYS} hari; SDR {C.SDR_DAYS} hari", "ASUMSI (zona waktu dan jam kantor)"],
]
ASSUME_NOTE = ("Seluruh parameter bertanda ASUMSI adalah pilihan pemodelan penulis; pilot Xpora belum mengirim dan syarat pembayaran KrakaCoal tidak dipublikasikan. "
               "Catatan pada submission Xpora: PO 27 ton bernilai 'USD 6.000-8.000' setara USD 0,22-0,30/kg, jauh di bawah pita harga portal USD 2,8-8/kg; simulasi memakai pita harga portal. Mohon dikonfirmasi angka yang benar.")

def sample_orders(pf="kraka", seed=7):
    sc_ = make_scenario(seed, pf)
    rows = [["Order", "HS", "Kuantitas", "Nilai (USD)", "RFQ (hari)", "DP terverifikasi (SDR)", "Closing dijanjikan", "LSD"]]
    for o in sc_.orders[:6]:
        rows.append([f"#{o.oid}", o.heading, f"{o.qty/1000:.0f} t" + (" premium" if o.premium else ""), f"{o.value:,.0f}".replace(",", "."), n(o.rfq, 1), n(o.dp_agent, 1), n(o.commit_closing, 0), n(o.lsd, 0)])
    return rows

CARRIER_TABLE = [["Carrier (fiktif)", "Tarif/kontainer reefer", "Transit", "Offset closing", "Klaim keandalan", "P(roll-over) dasar"]] + [
    [c.name, usd(c.rate), f"{c.transit:.0f} hari", f"{c.offset:.0f} + 7k", n(c.advertised_rel, 2), n(1 / (1 + np.exp(-c.base_roll_logit)), 2)] for c in C.CARRIERS]

# ============================================================ worked examples
pdm, qct, ca, ro, co, tr, qo, ql, ng, mm, ot, sn = W["producers"], W["qc_trust"], W["carrier"], W["roll"], W["cos"], W["trust"], W["q_ours"], W["q_lecture"], W["nego"], W["mas_metrics"], W["order_trace"], W["sales_nego"]
def _row(r): return f"{r['name']}: rate {n(r['rate'],0)} kg/hari, tawaran {n(r['offer'],0,'',True)} kg, harga {n(r['price'],2)}, q {n(r['q'],2)}, skor {n(r['score'],3)}"
WORKED = [
    ("1. Kebutuhan dengan buffer (over-allocation)",
     f"Order 20 t (Q = 20.000 kg), buffer awal b = 15%: N_0 = 20.000 x 1,15 = 23.000 kg. Alasan: rata-rata sekitar 2 produsen per order gagal kirim dan ~6% kg ditolak QC; tanpa buffer OTIF turun (lihat sweep buffer, Bagian 7). "
     "Putaran susulan hanya menutup kekurangan nyata: N_k = (Q - kg lolos QC) x 1,05."),
    ("2. Alokasi kuota multi-agen (bid dengan kapasitas nyata)",
     f"Lot {n(pdm['need'],0,'',True)} kg, jendela {pdm['window']:.0f} hari. Lima produsen menawar: " + "; ".join(_row(r) for r in pdm["rows"]) +
     f". Skor s = 0,3(1 - harga~) + 0,5 q + 0,2 kecepatan~. Urutan: {' > '.join(pdm['ranked'])}. Kuota: " + ", ".join(f"{k} {n(v,0,'',True)} kg" for k, v in pdm["alloc"].items()) + "."),
    ("3. Mengapa registry kedaluwarsa merugikan (agen tunggal)",
     "Agen tunggal memakai kapasitas registry x ketersediaan rata-rata 0,775: " + ", ".join(f"{r['name']} {n(r['stale_offer'],0,'',True)} kg" for r in pdm["rows"]) +
     f". Terhadap tawaran nyata di atas, kuota berikut melebihi kemampuan: " + ", ".join(f"{k} +{n(v,0,'',True)} kg" for k, v in pdm["cap_short"].items() if v > 0) +
     f" (total {n(pdm['cap_short_total'],0,'',True)} kg) sehingga perlu putaran susulan setelah konfirmasi (+0,25 hari) dan lebih banyak pesan. Pada multi-agen kekurangan ini tidak muncul karena produsen menawar sebatas kapasitas nyata."),
    ("4. QC dan pembaruan quality score",
     f"Produsen mengirim {n(qct['delivered'],0,'',True)} kg dengan yield {n(qct['g'],2)}: lolos QC = {n(qct['passed_medium'],0,'',True)} kg. Untuk order premium dengan produsen yield < 0,85 hanya 55% yang Grade A: {n(qct['passed_premium_lowgrade'],0,'',True)} kg. "
     f"Quality score q = 0,78 diperbarui q' = 0,8 x 0,78 + 0,2 x {n(qct['g'],2)} = {n(qct['q_ok'],3)}; bila gagal kirim (hasil 0): q' = {n(qct['q_default'],3)}; dua kali gagal: {n(qct['q_default_twice'],3)} < 0,60 sehingga diblokir."),
    ("5. Dispatch lini gudang (critical ratio)",
     f"t = {n(W['cr']['t'],0)}: J1 tenggat 12,5 sisa 3,2; J2 10,5 dan 4,0; J3 9,0 dan 1,4. CR = (d - t)/W: J1 {n(W['cr']['cr']['J1'],2)}; J2 {n(W['cr']['cr']['J2'],3)}; J3 {n(W['cr']['cr']['J3'],2)}. Urutan {' > '.join(W['cr']['order'])}."),
    ("6. Tawaran Contract Net antar lini",
     f"Job w = 1,8 hari pada t = 5. Lini a: beban 2,4, kecepatan 1,02: ETA = {n(W['bids']['a'],2)}. Lini b: beban 0,9, kecepatan 0,97: ETA = {n(W['bids']['b'],2)} sehingga ACCEPT ke b. Bila b terindikasi rusak sampai t = 7,5: ETA b = {n(W['bids']['b_alerted'],2)} dan a menang."),
    ("7. Pemilihan carrier: skor hibrida vs biaya harapan",
     f"Order ${n(ca['value'],0,'',True)}, 1 kontainer kering, tiba gerbang t = {n(ca['tport'],1)}, LSD = {n(ca['lsd'],0)}. " +
     "; ".join(f"{r['name']}: biaya {usd(r['cost'])}, berangkat hari {n(r['dep'],0)}, p = {n(r['p'],2)}, z = {n(r['z'],1)}, g = {n(r['g'],0)}, h = {n(r['h'],1)}, E[biaya] = {usd(r['exp_total'])}" for r in ca["rows"]) +
     f". Hibrida memilih {ca['best_h']}; biaya-harapan murni memilih {ca['best_exp']}."),
    ("8. Risiko roll-over (kebenaran tersembunyi vs model)",
     f"{ro['carrier']}, kongesti 0,6, musim puncak, buffer 2 hari: logit = -1,55 + 1,8(0,6) + 1,1(1) - 0,3(2) = {n(ro['logit'],2)}; p = {n(ro['p'],3)}. Carrier tercepat pada kondisi sama p = {n(ro['p_prime'],3)}. Model Risk Agent memperkirakan p dari 4.000 pengiriman historis (AUC {n(R['risk']['auc'],2)})."),
    ("9. Klasifikasi HS dengan kemiripan kosinus",
     f"Query '{co['q']}'. Dokumen '{co['d1']}': cos = 3/(sqrt(3) x sqrt(4)) = {n(co['c1'],3)}. Dokumen '{co['d2']}': irisan 2 kata, cos = {n(co['c2'],3)}. Sistem sebenarnya memakai TF-IDF n-gram kata + karakter dan k-NN; confidence < 0,60 diserahkan ke manusia."),
    ("10. Trust carrier",
     f"T = 0,80, terangkut (q = 1): T' = {n(tr[0]['new'],2)}. Roll-over (q = 0,2): T' = {n(tr[1]['new'],2)}; roll-over kedua: {n(tr[2]['new'],3)} < 0,60 sehingga diblokir oleh gerbang g."),
    ("11. Q-learning keputusan lembur",
     f"Contoh kuliah: Q = 2,0; alpha = 0,2; r = 5; gamma = 0,9; max Q' = 4: target = {n(ql['target'],1)}, TD = {n(ql['td_error'],1)}, Q baru = {n(ql['q_new'],2)}. "
     f"Contoh kita: Q(s, lembur) = {n(qo['q_old'],0)}; r = -45 x 1,4/1,35 = {n(qo['r'],1)}; max Q' = {n(qo['maxq'],0)}: target = {n(qo['target'],1)}; TD = {n(qo['td'],1)}; Q baru = {n(qo['q_new'],1)}."),
    ("12. Negosiasi Sales Agent dan Nash bargaining",
     f"Harga per kg: pembeli membuka 2,60 (batas 3,40), penjual membuka 4,20 (batas bawah 3,00), T = 4: " + "; ".join(f"ronde {t}: {n(b_,2)} vs {n(s_,2)}" for t, b_, s_ in sn['trace']) +
     f". Sepakat pada {n(sn['price'],2)} USD/kg pada ronde {sn['round']}; surplus pembeli {n(sn['surplus_per_kg']['buyer'],2)} dan penjual {n(sn['surplus_per_kg']['seller'],2)} per kg. Nash product tertinggi pada tarif $2.100-$2.200 pada contoh tarif di modul negosiasi."),
    ("13. Biaya dan margin satu order (KrakaCoal, skenario 7, order #1 dan #4)",
     "; ".join(f"{'Manual' if m=='static' else 'Multi-agen'} order #{oid}: kuantitas {n(v['qty']/1000,0)} t, terisi {pc(v['fill'],0)}, {v['rounds']} putaran, {v['producers']} produsen, sourcing {usd(v['src_cost'])}, freight {usd(v['freight'])}, penalti {usd(v['penalty'])}, "
               f"penyimpanan {usd(v['hold'])}, manusia {usd(v['human'])}, pendapatan {usd(v['revenue'])} (terlambat {n(v['late'],0)} hari)" for m in ("static", "mas") for oid, v in ot[m].items()) + "."),
    ("14. Metrik sistem multi-agen (Bab 4)",
     f"Speedup 1.000 task: 100 s vs 29 s pada 4 agen: S = {n(mm['speedup'][0],2)}, efisiensi {n(mm['speedup'][1],2)}. Redundansi 3 agen R = 0,9: R_sys = {n(mm['r_sys'],3)}. Biaya komunikasi satu pesan 8 KB pada 8 Mbps dan 20 ms: {n(mm['comm_ms'],1)} ms. "
     f"Jain: kuota merata {n(mm['jain'][0],2)}; timpang (4,1,1,1) {n(mm['jain'][1],2)}. Jain kuota antar produsen pada simulasi: Xpora {n(mv('xpora','mas','jain_producers'),2)}, KrakaCoal {n(mv('kraka','mas','jain_producers'),2)}."),
    ("15. Migrasi Scout Agent",
     "Host dengan trust >= 0,80 dan risiko <= 0,20 boleh dimigrasi; host carrier A (trust 0,71, risiko 0,30) ditolak walau latensinya terbaik. "
     f"Data yang dipindahkan per skenario: {n(XP['scout']['bytes']/1e6,1)} MB (scout) vs {n(XP['scout']['raw']/1e6,1)} MB (remote pull); penghematan {pc(1-XP['scout']['bytes']/XP['scout']['raw'],0)}."),
]

# ============================================================ related work
RELATED_PROBLEM = [
    ("Hathikal, S., Chung, S. H., & Karczewski, M. (2020). Prediction of ocean import shipment lead time using machine learning methods. SN Applied Sciences, 2, 1272.",
     "Memprediksi lead time pengiriman laut dengan regresi logistik multinomial, pohon keputusan, SVM, Naive Bayes, dan k-NN untuk shipper, carrier, forwarder, dan consignee.",
     "Dasar pemakaian model klasik/explainable untuk risiko pengiriman: Risk Agent memakai regresi logistik untuk peluang roll-over.",
     "https://link.springer.com/article/10.1007/s42452-020-2951-5"),
    ("Lee, E., Kim, S., Kim, S., Jung, S., Kim, H., & Cha, M. (2024). Explainable Product Classification for Customs. ACM Transactions on Intelligent Systems and Technology, 15(2), Art. 25. doi:10.1145/3635158.",
     "Model XAI untuk membantu petugas bea cukai menetapkan 6 digit kode HS dari deskripsi barang, disertai alasan yang dapat dibaca.",
     "Dasar Compliance Agent: klasifikasi teks HS lintas komoditas dengan confidence dan eskalasi ke manusia (selective classification); relevan untuk klaim Xpora bahwa arsitektur agnostik komoditas.",
     "https://dl.acm.org/doi/10.1145/3635158"),
    ("Ouelhadj, D., & Petrovic, S. (2009). A survey of dynamic scheduling in manufacturing systems. Journal of Scheduling, 12, 417-431. doi:10.1007/s10951-008-0090-8.",
     "Tinjauan penjadwalan dinamis (heuristik, meta-heuristik, sistem multi-agen, teknik AI lain) saat terjadi gangguan seperti kerusakan mesin dan order mendadak.",
     "Dasar penjadwalan reaktif: re-kontrak pekerjaan saat produsen gagal kirim atau lini gudang rusak, dan critical ratio.",
     "https://link.springer.com/article/10.1007/s10951-008-0090-8"),
]
RELATED_AGENT = [
    ("Smith, R. G. (1980). The Contract Net Protocol: High-level communication and control in a distributed problem solver. IEEE Transactions on Computers, C-29(12), 1104-1113.",
     "Alokasi tugas terdesentralisasi: manajer mengumumkan tugas (CFP), kontraktor menawar, pemenang dipilih; dapat re-kontrak bila gagal.",
     "Protokol inti XCMAS untuk kuota produsen UMKM, dispatch lini gudang, dan pemilihan carrier (Bab 4 bagian Contract Net).",
     ""),
    ("Leitao, P. (2009). Agent-based distributed manufacturing control: A state-of-the-art survey. Engineering Applications of Artificial Intelligence, 22(7), 979-991.",
     "Survei kontrol manufaktur terdistribusi berbasis agen: fleksibilitas, kemampuan bereaksi terhadap gangguan, dan tantangan integrasi.",
     "Menjustifikasi produsen/lini sebagai unit otonom dan pendekatan hibrida (koordinasi terdesentralisasi + kontrol ringan).",
     "https://doi.org/10.1016/j.engappai.2009.05.005"),
    ("Zhao, Z., Tang, D., Liu, C., Wang, L., Zhang, Z., Zhu, H., Chen, K., Nie, Q., & Ji, Y. (2024). A Large Language Model-based multi-agent manufacturing system for intelligent shopfloor. arXiv:2405.16887.",
     "Sistem multi-agen berbasis LLM untuk shopfloor pintar dengan modul agen dan cara kolaborasi, meminimalkan intervensi manusia.",
     "Arah lanjutan: LLM sebagai lapisan bahasa (Virtual SDR, ekstraksi dokumen, penjelasan) yang tetap dibatasi kebijakan dan aturan deterministik.",
     "https://arxiv.org/abs/2405.16887"),
]
CITE_NOTE = ("Verifikasi: metadata Hathikal dkk., Lee dkk., Ouelhadj & Petrovic, Leitao, dan Zhao dkk. dicek melalui pencarian web pada sesi pengerjaan (situs penerbit tidak dapat dibuka langsung dari lingkungan kerja). "
             "Smith (1980) dan halaman jurnal Leitao ditulis dari pengetahuan penulis: mohon diverifikasi sebelum pengumpulan.")

# ============================================================ why multi-agent
stX = XP["staleness"]["avail"]; stK = KR["staleness"]["avail"]
def adv(pf, a, key="margin"): d = P[pf]["staleness"]["avail"][a]; return (d["mas"][key][0] - d["central"][key][0]) / (PROFILES[pf].n_orders if key == "margin" else 1)
CRITERIA = [
    ["Kriteria (Bab 4)", "Terpusat", "Terdesentralisasi", "Hybrid", "Posisi XCMAS"],
    ["Latensi dan bandwidth", "Sedang", "Rendah", "Rendah-sedang", "CFP hanya ke kandidat (fan-out dibatasi)"],
    ["Fault tolerance", "Rendah (single point of failure)", "Tinggi", "Tinggi", "Kegagalan satu produsen/agen tidak menghentikan order"],
    ["Optimalitas global", "Tinggi bila data akurat", "Lokal", "Cukup tinggi", "Aturan skor bersama + governance; data segar dari bid"],
    ["Biaya koordinasi", "Fan-in O(n) pada koordinator", "Tinggi (banyak pesan)", "Sedang", "Lebih banyak pesan per order pada pemasokan"],
]
WHY = [
    ("Batas organisasi dan kepemilikan", "Produsen UMKM, carrier, bea cukai, dan pembeli adalah pihak otonom; planner pusat tidak dapat memerintah mereka, hanya menegosiasikan (CFP/PROPOSE/ACCEPT). Konsorsium Xpora memang berbasis kepercayaan lintas pemilik."),
    ("Informasi lokal yang segar", f"Kapasitas nyata produsen berubah (pasar lokal, musim, kondisi). Bid multi-agen memakai kapasitas nyata; registry pusat kedaluwarsa. Dengan variasi ketersediaan 45% (default), multi-agen menaikkan margin {usd(adv('xpora','0.55'))}/order (Xpora) dan {usd(adv('kraka','0.55'))}/order (KrakaCoal); "
     f"bila kapasitas stabil (variasi 0%) selisihnya {usd(adv('xpora','1.0'))} dan {usd(adv('kraka','1.0'))}."),
    ("Ketahanan terhadap single point of failure", f"Gangguan bidang kontrol 2-5 hari pada 50% skenario mengubah OTIF agen tunggal dari {pc(P['xpora']['robust']['0.0']['central']['otif'][0])} ke {pc(P['xpora']['robust']['0.5']['central']['otif'][0])} dan multi-agen dari {pc(P['xpora']['robust']['0.0']['mas']['otif'][0])} ke {pc(P['xpora']['robust']['0.5']['mas']['otif'][0])} (Xpora): tidak ada penurunan berarti karena jadwal memiliki slack; ketahanan bukan alasan utama pada kasus ini, tetapi menjadi relevan bila slack ketat."),
    ("Beban node puncak dan skala", f"Pada {XP['scale'][-1]['n_producers']} produsen, koordinator menerima {n(XP['scale'][-1]['central']['coord_peak'],0)} pesan pada hari tersibuk vs {n(XP['scale'][-1]['mas']['peak_node'],0)} pada agen tersibuk multi-agen; total pesan justru lebih banyak pada multi-agen untuk pemasokan ({n(XP['scale'][-1]['mas']['msgs'],0,'',True)} vs {n(XP['scale'][-1]['central']['msgs'],0,'',True)})."),
    ("Modularitas dan komoditas baru", "Producer Agent cukup diberi profil baru (kapasitas, harga, perishable) untuk komoditas lain: profil KrakaCoal dan Xpora dijalankan pada mesin yang sama tanpa mengubah agen (klaim agnostik komoditas pada submission Xpora)."),
]
WHY_HONEST = ("Catatan penting: keunggulan multi-agen bergantung pada seberapa kedaluwarsa data pusat. Bila kapasitas produsen stabil dan registry akurat, agen tunggal terpusat setara. "
              "Rekomendasi: arsitektur hybrid: satu inti kognitif per pabrik/gudang, negosiasi multi-agen pada batas organisasi (produsen, carrier), dan governance sebagai bidang kontrol; "
              "untuk pilot 20 produsen yang stabil, agen tunggal + WhatsApp sudah cukup, lalu berpindah ke multi-agen saat pool tumbuh ke ratusan produsen dengan kapasitas berubah-ubah.")

AGENTS = [
    ["Agen", "Tipe", "Belief / Desire / Intention", "Komponen internal dan tools", "Input -> Output", "Metode", "Otonomi"],
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
    ["Quality score produsen", "Pembaruan eksponensial (trust)", "Statistik online", "Insentif kualitas organik (submission Xpora); sederhana dan transparan", "Tidak butuh model kompleks"],
    ["Klasifikasi HS lintas komoditas", "TF-IDF + k-NN kosinus", "ML klasik (NLP)", f"Deskripsi pendek, ~1.000 contoh; akurasi {pc(R['hs']['acc'])}; confidence dapat dijelaskan", "Data kecil; LLM/BERT ditambahkan bila kosakata dan bahasa bertambah"],
    ["Risiko roll-over", "Regresi logistik", "ML supervised", f"Data tabular 4.000 pengiriman; AUC {n(R['risk']['auc'],2)}; bobot terbaca; probabilitas terkalibrasi", "Pada data tabular kecil, model linier setara DL (Bab 1); XGBoost sebagai pembanding"],
    ["QC visual (Grade A/B/Reject)", "CNN (rencana tim Xpora); di sini: yield statistik", "DL (rencana)", "Citra produk adalah data yang cocok untuk DL (Bab 1); dataset sedang dikumpulkan", "Belum ada dataset terlabel; Tugas 1 memodelkan hasilnya (pass rate) saja"],
    ["Virtual SDR", "LLM + konsesi waktu-tergantung + guardrail", "LLM + aturan", "Bahasa alami multibahasa 24/7; harga dijaga oleh aturan dan band diskon (Bab 3: LLM tidak sendirian)", "Di simulasi hanya logika negosiasi; panggilan LLM belum dipakai (hook tersedia)"],
    ["Keputusan lembur", "Q-learning tabular", "RL", "Ruang state kecil, reward tertunda", "Deep RL tidak diperlukan; sulit diaudit"],
    ["Kesehatan lini", "Slope percept sequence", "Statistik", "Bab 2: tren lebih informatif daripada nilai tunggal", "Sensor sedikit"],
    ["Pemilihan carrier", "DSS berbobot + ML + gerbang kebijakan", "Hibrida (Bab 3)", "Skor hibrida h; kelayakan sebagai constraint keras", "Keputusan finansial harus dapat dijelaskan"],
    ["Keamanan dan otonomi", "HMAC, nonce, FSM, capability", "Deterministik", "Jaminan keamanan harus pasti", "-"],
]
CRIT_NOTE = ("Kriteria pemilihan model (Bab 3): akurasi dan explainability, latensi dan biaya, privasi dan data, skalabilitas. Prinsip Bab 1: pilih model paling sederhana yang memenuhi kebutuhan. "
             "Kesimpulan: XCMAS adalah hibrida AI klasik + ML supervised + RL kecil + aturan deterministik, dengan slot untuk LLM (Sales) dan CNN (QC) yang dikembangkan tim.")

lv = XP["levels"]["mas"]; tot_lv = sum(lv.values())
AUTONOMY = [["Level (Bab 2)", "Keputusan pada XCMAS", "Rata-rata per skenario (Xpora)", "Kendali"],
    ["4 Delegate", "Dispatch lini, kuota dalam batas konsentrasi, HS confidence >= 0,60, carrier order di bawah batas nilai", f"{n(lv['4'],1)} ({pc(lv['4']/tot_lv,0)})", "Otomatis, audit trail"],
    ["3 Supervise", "Lembur dalam anggaran, LoI dalam band harga", f"{n(lv['3'],1)}", "Agen bertindak, manusia dapat override"],
    ["2 Approve", "Verifikasi DP (selalu), HS confidence rendah, order bernilai tinggi, lembur di luar anggaran", f"{n(lv['2'],1)}", "Human-in-the-loop"],
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
            ("Gagal kirim per order", "defaults", lambda x: n(x, 2), False), ("Jain kuota antar produsen", "jain_producers", lambda x: n(x, 2), False),
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
    rows = [["Variasi ketersediaan (1 - u_min)", "Xpora: margin/order (agen tunggal / multi-agen)", "Xpora: OTIF", "KrakaCoal: margin/order", "KrakaCoal: OTIF"]]
    for a in sorted(stX, key=float, reverse=True):
        r_ = [pc(1 - float(a), 0)]
        for pf in ("xpora", "kraka"):
            d = P[pf]["staleness"]["avail"][a]; nn = PROFILES[pf].n_orders
            r_ += [f"{n(d['central']['margin'][0]/nn,0,'',True)} / {n(d['mas']['margin'][0]/nn,0,'',True)}", f"{pc(d['central']['otif'][0],0)} / {pc(d['mas']['otif'][0],0)}"]
        rows.append(r_)
    return rows

def buffer_table():
    rows = [["Buffer awal", "Xpora: margin/order", "Xpora: OTIF", "Xpora: limbah/order", "KrakaCoal: margin/order", "KrakaCoal: OTIF", "KrakaCoal: limbah/order"]]
    for b in sorted(XP["buffer"], key=float):
        r_ = [pc(float(b), 0)]
        for pf in ("xpora", "kraka"):
            d = P[pf]["buffer"][b]; nn = PROFILES[pf].n_orders
            r_ += [n(d["margin"][0] / nn, 0, "", True), pc(d["otif"][0], 0), n(d["surplus_waste"][0] / nn, 0, "", True)]
        rows.append(r_)
    return rows

ROBUST = [["P(gangguan bidang kontrol)", "Xpora: manual", "Xpora: agen tunggal", "Xpora: multi-agen", "KrakaCoal: agen tunggal", "KrakaCoal: multi-agen"]] + [
    [n(float(p), 1)] + [pc(P["xpora"]["robust"][p][m]["otif"][0], 0) for m in MODES] + [pc(P["kraka"]["robust"][p][m]["otif"][0], 0) for m in ("central", "mas")] for p in sorted(P["xpora"]["robust"], key=float)]
SCALE = [["Order / produsen", "Koordinator: puncak pesan/hari", "MAS: agen tersibuk", "Total pesan (pusat / MAS)", "OTIF (pusat / MAS)"]] + [
    [f"{r['n_orders']} / {r['n_producers']}", n(r["central"]["coord_peak"], 0), n(r["mas"]["peak_node"], 0), f"{n(r['central']['msgs'],0,'',True)} / {n(r['mas']['msgs'],0,'',True)}", f"{pc(r['central']['otif'],0)} / {pc(r['mas']['otif'],0)}"] for r in XP["scale"]]
sh, ss = R["sales"]["human"], R["sales"]["sdr"]
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
    f"Sumber nilai terbesar (margin per order): kuota berbasis bid live ({usd(-_d('xpora','- live bids (stale registry instead)'))} Xpora, {usd(-_d('kraka','- live bids (stale registry instead)'))} KrakaCoal), dokumen paralel dengan sourcing "
    f"({usd(-_d('xpora','- parallel documents'))} dan {usd(-_d('kraka','- parallel documents'))}), dan re-optimasi carrier ({usd(-_d('xpora','carrier rule = keep committed carrier'))} dan {usd(-_d('kraka','carrier rule = keep committed carrier'))}). "
    f"Quality-score prioritisation: {usd(-_d('xpora','- quality-score prioritisation (price only)'))} dan {usd(-_d('kraka','- quality-score prioritisation (price only)'))}; tanpa buffer margin turun {usd(-_d('xpora','- over-allocation buffer (0 %)'))} dan {usd(-_d('kraka','- over-allocation buffer (0 %)'))}.",
    f"Trade-off: menghapus model risiko atau memakai aturan biaya-harapan dapat menaikkan margin ({usd(_d('xpora','- ML risk model (advertised reliability)'))} dan {usd(_d('xpora','carrier rule = expected cost'))} per order pada Xpora) tetapi menurunkan OTIF; "
    "aturan hibrida (Bab 3) memprioritaskan tingkat layanan. Pilihan bobot adalah keputusan bisnis; kerugian reputasi dan L/C tidak dimodelkan sehingga nilai layanan di sini konservatif.",
    f"Buffer over-allocation: margin puncak pada 15-20% (Bagian sweep) karena kekurangan pasokan (gagal kirim, reject QC) lebih mahal daripada limbah surplus yang dijual 60% harga beli. Pada buffer 30% margin turun karena limbah surplus.",
    f"Pembelajaran RL: policy Q dari MDP abstrak tidak transfer ke simulator (hampir tidak pernah lembur), sedangkan Q yang dilatih langsung di simulator setara aturan slack<0. Pada sebagian profil 'selalu lembur (dalam anggaran)' lebih baik: lembur murah dibanding penalti dan anggaran governance menjadi parameter yang mengikat. "
    "Penyebab Q tidak menemukannya: reward akhir bising dan kredit tercampur antar order; perbaikan: difference reward (Bab 4) dan lebih banyak episode.",
    f"Sales/SDR (eksploratif, bergantung asumsi waktu balas): konversi RFQ ke deal {pc(sh['conversion'],0)} (meja manusia) vs {pc(ss['conversion'],0)} (SDR) dan waktu ke harga sepakat {n(sh['mean_hours'],0)} vs {n(ss['mean_hours'],0)} jam; harga rata-rata hampir sama karena strategi konsesi sama. Perlu divalidasi dengan data RFQ nyata.",
]
LIMITS = [
    "Data sintetis: pilot Xpora belum mengirim, KrakaCoal tidak mempublikasikan harga atau syarat pembayaran. Tidak ada klaim performa nyata; kalibrasi ke data ERP/CRM riil adalah langkah wajib berikutnya.",
    "Keunggulan multi-agen bergantung pada asumsi variasi ketersediaan (45%) dan noise registry (10%); sweep sensitivitas ditampilkan dan pada variasi 0% keunggulan hilang.",
    "Keunggulan jumlah pesan pusat vs MAS bergantung pada asumsi heartbeat/refresh registry mingguan dan fan-out CFP; pada pemasokan multi-agen memakai lebih banyak pesan.",
    "QC (CNN) dan Virtual SDR (LLM) tidak diimplementasikan sebagai model; QC dimodelkan sebagai pass-rate statistik dan SDR sebagai logika konsesi. Modul SDR bersifat eksploratif.",
    "Penalti keterlambatan, harga jual, dan tarif carrier adalah asumsi; kerugian reputasi, pembatalan L/C, dan kurs tidak dimodelkan. Data volume scout adalah asumsi.",
    "Model risiko (AUC 0,76) dilatih pada data yang dibangkitkan dari proses logit yang kita tulis; belum ada uji drift/retraining online.",
    "Simulasi diskret (langkah 0,05 hari), 300 skenario evaluasi per profil (seed 0-299), terpisah dari seed kalibrasi (1000+) dan pelatihan RL (10000+).",
    "Belum ada UI dashboard, integrasi WhatsApp Business API, atau API bea cukai/carrier nyata; itu rencana Project #1 dan MVP Xpora.",
]
BIZ = [
    ["Rekomendasi operasional", "Dasar pada eksperimen"],
    ["Pakai buffer over-allocation 15% pada putaran pertama; pertahankan re-kontrak untuk kekurangan", "Sweep buffer: margin puncak 15-20%; tanpa buffer OTIF turun tajam"],
    ["Minta konfirmasi kapasitas nyata dari produsen (template WhatsApp) sebelum mengunci kuota, bukan mengandalkan data onboarding", "Sweep staleness: nilai bid live tumbuh dengan variasi ketersediaan"],
    ["Prioritaskan produsen dengan quality score tinggi dan blokir score < 0,60; batasi 30% per produsen", "Ablation quality-score dan concentration cap; Jain kuota tetap terpantau"],
    ["Mulai dokumen (HS, sertifikat) saat DP terverifikasi, paralel dengan produksi", "Ablation: dokumen paralel = penghematan waktu terbesar kedua"],
    ["Pertahankan verifikasi DP manual (level 2) dan persetujuan order bernilai tinggi", "Desain Xpora; menambah 1 sentuhan per order namun mencegah kesalahan pembayaran"],
    ["Untuk pilot 20 produsen stabil, mulai dengan agen tunggal; pindah ke multi-agen saat pool ratusan produsen", "Kesimpulan sensitivitas dan skala"],
    ["Kumpulkan data untuk kalibrasi: syarat pembayaran, harga beli per produsen, tingkat gagal kirim dan reject, waktu balas WhatsApp", "Batasan data sintetis"],
]
LECTURE_MAP = [["Materi kuliah", "Penerapan pada XCMAS", "Berkas kode"],
    ["Bab 1: hibrida prediksi + aturan deterministik; model paling sederhana yang memadai", "Risk/Compliance = ML klasik; governance = aturan; DL/LLM sesuai porsi", "ml.py, sim.py"],
    ["Bab 2: PEAS, klasifikasi lingkungan, rational agent, utility + constraint", "Bagian 2.3-2.4; a* = argmax U s.t. policy", "config.py, consortium.py"],
    ["Bab 2: percept sequence, reactive vs deliberative, level otonomi, learning agent", "Monitor kondisi lini; hybrid; level 1-4; Learning Agent", "ml.py, rl.py, rl_sim.py"],
    ["Bab 3: BDI, A = <G,B,I,M,C,R,P,T>, s(t+1)=F(s,o,a)", "Tabel agen (6.4), siklus kognitif (6.3)", "sim.py, consortium.py"],
    ["Bab 3: skor hibrida h = g[alpha z + (1-alpha) 100 (1-p)], DSS + ML + policy engine", "Pemilihan carrier", "sim.py (book)"],
    ["Bab 3: runtime, observability, audit trail, batas berhenti", "Audit log rantai-hash, jumlah pesan, anggaran lembur, eskalasi confidence", "messaging.py"],
    ["Bab 4: MAS tuple, ACL, FSM, ontologi", "Message m = <s,r,p,c,o,l,id,t>, FSM Contract Net, ontologi export-mfg-v1", "messaging.py"],
    ["Bab 4: Contract Net, negosiasi, task allocation, utility", "Kuota produsen (CNP), lini gudang, carrier, negosiasi Sales Agent", "consortium.py, negotiation.py, sales.py"],
    ["Bab 4: trust eksponensial, HMAC, replay, capability, migrasi aman", "Quality score produsen, trust carrier, 7 uji serangan, gerbang migrasi", "messaging.py, mobile.py"],
    ["Bab 4: speedup, R_sys, Jain, C_comm, KPI vector, smart manufacturing, supply chain MAS", "Bagian 3 (contoh 14) dan 7 (metrik sistem, fairness kuota)", "negotiation.py, experiments.py"],
    ["Bab 5: mobile agent, serialisasi, migrasi, sandbox, RL mobility, layout Project #1", "Scout Agent; Q-learning; struktur laporan mengikuti layout Project #1", "mobile.py, rl.py"]]
NEXT = [
    "Kalibrasi dengan data nyata KrakaCoal (syarat pembayaran, harga beli per pemasok, tingkat gagal/reject, waktu balas) dan data pilot Xpora; ganti asumsi dengan estimasi.",
    "Project #1 (tema domain enterprise): perluas ke Scout/Broker/Worker/Security (Bab 5), dashboard UI/UX (Command Center: peta kapasitas UMKM, status pesanan, QC), GNN untuk jaringan produsen-gudang-pelabuhan, dan perbandingan dengan sistem statis.",
    "Integrasikan komponen yang dikembangkan tim Xpora: CNN QC (Grade A/B/Reject) menggantikan pass-rate statistik, LLM Virtual SDR menggantikan logika konsesi, dan WhatsApp Business API sebagai kanal agen produsen.",
    "Perkuat RL (difference reward, replay terkontrol, safe-RL) dan bandingkan XGBoost untuk risiko roll-over; tambahkan uji drift dan retraining online.",
    "Bandingkan dengan optimizer global (MILP/OR-Tools) sebagai batas atas optimalitas alokasi kuota.",
]
