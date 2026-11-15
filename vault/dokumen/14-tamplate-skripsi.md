---
tipe: dokumen_resmi
id: 16
judul: "Tamplate Skripsi"
berkas_asli: "data/dokumen_raw/14_TEMPLATE_SKRIPSI.docx.pdf"
url_asli: "https://api.ifuntanhub.dev/assets/ca033349-e142-416f-afde-42efdfcd0062"
format: "PDF"
ukuran_byte: 450923
tanggal_upload: "2026-06-04"
sumber: "https://api.ifuntanhub.dev/assets/ca033349-e142-416f-afde-42efdfcd0062"
---

# Tamplate Skripsi

> **Informasi Berkas Resmi:**
> - **Format Asli:** PDF (450,923 bytes)
> - **Tautan Unduh Berkas Asli (Raw):** [TEMPLATE SKRIPSI.docx.pdf](https://api.ifuntanhub.dev/assets/ca033349-e142-416f-afde-42efdfcd0062)
> - **Tanggal Terbit:** 2026-06-04

---

# **JUDUL SKRIPSI HARUS DITULIS MENGGUNAKAN HURUF KAPITAL JENIS TIMES NEW ROMAN UKURAN 14 PT DICETAK TEBAL** 

## **SKRIPSI** 

Program Studi Teknik .......................... Jurusan Teknik .................. 

Oleh: **<u>FULAN</u>** 

NIM D....................... 



**FAKULTAS TEKNIK UNIVERSITAS TANJUNGPURA PONTIANAK 2022** 

## **HALAMAN PERNYATAAN** 

Yang bertanda tangan di bawah ini: 

Nama : Kiki P. Utomo NIM : D11193042 

menyatakan bahwa dalam SKRIPSI yang berjudul “xxxxxxxxxxx xxxxx” tidak terdapat karya yang pernah diajukan untuk memperoleh gelar sarjana di suatu perguruan tinggi manapun. Sepanjang pengetahuan Saya, tidak terdapat karya atau pendapat yang pernah ditulis atau diterbitkan oleh orang lain, kecuali yang secara tertulis diacu dalam naskah ini dan disebutkan dalam Daftar Rujukan. 

Demikian pernyataan ini dibuat dengan sebenar-benarnya. Saya sanggup menerima konsekuensi akademis dan hukum di kemudian hari apabila pernyataan yang dibuat ini tidak benar. 

Pontianak, 20 Mei 2022 

( _tanda tangan_ ) 

Kiki Prio Utomo NIM D11193042 

1 

**KOP FAKULTAS TEKNIK** 

## **HALAMAN PENGESAHAN** 

PENULISAN SKRIPSI UNTUK PROGRAM SARJANA FAKULTAS TEKNIK UNIVERSITAS TANJUNGPURA PONTIANAK 

Jurusan Teknik Sipil 

Program Studi Sarjana Teknik Sipil 

Oleh: 

Fulan NIM. D11193042 

Telah dipertahankan di depan Penguji Skripsi pada tanggal 20 Juli 2022 dan diterima sebagai salah satu persyaratan untuk memperoleh gelar sarjana 

Susunan Penguji Skripsi 

Dosen Pembimbing Utama : Prof. Dr.-Ing. Pulan Cemerlang NIP. Dosen Pembimbing Kedua  : Prof. Dr. Eng. Cantik Rupawan NIP. Dosen Penguji Utama : Ir. Cahaya Cemerlang, M.Sc, Ph.D NIP. Dosen Penguji Kedua : Ir. Sinar Mentari, M.Eng, Ph.D NIP. 

Pontianak, 20 Juli 2022 Dekan, 

Pembimbing Utama 

Prof. Dr.-Ing. Ir. Gagah Perkasa, M. Eng Prof. Dr.-Ing. Pulan Cemerlang NIP. NIP. 

2 

## **HALAMAN PERSEMBAHAN** 

Skripsi ini didedikasikan kepada kedua orang tuaku Mr. X dan Mrs. Y dan saudara-saudaraku Brown, Black, dan Yellow. Apa yang mereka telah berikan melebihi daripada apa yang pernah aku inginkan. 

Dari titisan ilmu-Mu kupersembahkan goresan tanganku bagi ilmu pengetahuan 

Indonesia 

3 

## **PRAKATA** 

Puji syukur kehadirat Allah SWT atas kehendak-Nya maka penelitian dan penulisan skripsi dengan judul “Teknik Pengamanan Perangkat Lunak Komersil dari Pembajakan Menggunakan Identitas Komputer dan _Short Message Service_ (SMS)” ini dapat diselesaikan dengan baik. 

Penelitian ini menjelaskan tentang skema proteksi perangkat lunak dari upaya-upaya pembajakan atau penggunaan perangkat lunak secara _illegal_ . Dengan memanfaatkan identitas yang ada pada komputer dapat dibangkitkan kode kombinasi yang unik sehingga perangkat lunak hanya dapat berfungsi pada komputer yang telah melakukan aktivasi atau registrasi. Proses aktivasi atau registrasi dilakukan secara _online_ dengan memanfaatkan layanan _short message service_ . 

Secara khusus penulis menyampaikan terima kasih yang sebesar-besarnya kepada Dr. Opal Blazer dan Dr. Edo Riza sebagai pembimbing utama dan pembimbing pendamping yang telah memberikan bimbingan, masukan, dan diskusi yang intensif khususnya tentang model proteksi perangkat lunak yang digunakan. Terima kasih disampaikan pula kepada CV. Minoritas Kreatif yang telah menyediakan peralatan yang diperlukan dalam penelitian, Pemerintah Kota Pontianak yang telah membantu biaya penelitian, Fulan, S.T., M.T. dan Fulanah, S.T. yang membantu pengujian perangkat lunak sehingga layak digunakan. 

Penulis berharap penelitian ini dapat bermanfaat dalam upaya mencegah praktik pembajakan atau setidaknya memperlambat upaya pembajakan sehingga tidak merugikan pihak _developer_ atau distributor perangkat lunak tersebut. Penulis mengharapkan masukan yang konstruktif agar dapat menyempurnakan penelitian ini. 

Pontianak, 20 Mei 2022 

Penulis, 

iv 

## **ABSTRAK** 

Seperti yang telah diketahui dengan baik bahwa fenomena _undershoot_ tidak dapat dihindari untuk _plants_ yang memiliki _real unstable zeros._ Karena itu, jika ada _plant_ yang memiliki _real unstable zeros_ , bentuk tanggapan tangga dari masukan acuan ke keluaran sistem pada sistem kendali umpan balik pasti menghasilkan _undershoot_ , tanpa tergantung pada pemilihan pengendalinya. Penelitian ini diawali dengan menginvestigasi teori fenomena _undershoot_ yang diakibatkan adanya _unstable zeros_ pada _plant_ yang harus dikendalikan. Kemudian mengajukan metode-metode untuk mengurangi _undershoot_ pada _plant_ yang memiliki _unstable zeros_ . Idenya adalah berdasarkan pada disain _linear quadratic regulator_ (LQR) yang memodifikasi indeks unjuk kerja dengan _exponential time decay rate_ yang menggunakan faktor pembobot. Berdasarkan hasil simulasi diperlihatkan bahwa _weighted optimal_ LQR dapat mengurangi _undershoot_ jika dibandingkan dengan penggunaan LQR yang standar. Metode berikutnya untuk mengurangi _undershoot_ adalah dengan menggunakan disain kendali digital. Idenya adalah dengan mengkombinasikan bentuk diskrit dari _weighted optimal_ LQR dan disain pengendali waktu diskrit dengan _piecewise constant hold_ (PCH). Penggunaan PCH ini dapat mengubah masukan kendali antar sampel sehingga _undershoot_ menjadi berkurang. Hasil simulasinya juga kembali menyimpulkan bahwa penggunaan faktor pembobot adalah efektif dan metode PCH lebih baik dari metode sebelumnya. Metode-metode baru yang diajukan ini kemudian diuji pada sistem dinamik dengan faktor pembobot yang berbeda-beda sehingga akan menghasilkan kuantitas _undershoot_ yang bervariasi pula. Hasil simulasi yang terjadi membuktikan keakuratan semua metode tersebut. 

Kata kunci: _undershoot_ , _linear quadratic regulator_ , kendali digital, _piecewise constant hold_ 

v 

## **ABSTRACT** 

It is well known that undershoot phenomena are inevitable for plants having real unstable zeros. Therefore, if the plant has real unstable zeros, the step response from the reference input to the system output in the feedback control system must exhibit undershoot, regardless of the choice of stabilizing controller. In this research, we first investigate the undershoot phenomena caused by unstable zeros of the plant to be controlled theoretically. We then propose methods of reducing the undershoot amount for a plant with unstable zeros. The idea based on the linear quadratic regulator (LQR) design is to use a modified performance index with an exponential time decay rate using a weighting factor. We can first confirm from simulation results that the weighted optimal LQR can reduce undershoot in comparison with the standard LQR case. The next method to reducing the undershoot amount is by using digital control design. Our idea here is a combination of the discrete version of the weighted optimal LQR and a discrete-time controller design with PCH (Piecewise Constant Hold). By using PCH we can change the inter-sample control input so as to reduce the undershoot amount. We can see from simulation results that the introduction of weighting factor is again effective. And, confirm that the PCH method is better than the previously method. We also have evaluated the quantity of undershoot caused our proposed methods by using some distinct weighting factor values for one typical dynamical examples. We can confirm the effectiveness off all method by simulations. 

Keyword: undershoot, digital control, piecewise constant hold 

vi 

## **DAFTAR ISI** 

|HALAMAN PERNYATAAN.................................................................................................................... i|
|---|
|HALAMAN PENGESAHAN...................................................................................................................ii|
|HALAMAN PERSEMBAHAN.............................................................................................................. iii|
|PRAKATA................................................................................................................................................iv|
|ABSTRAK................................................................................................................................................ 5|
|ABSTRACT..............................................................................................................................................6|
|DAFTAR ISI............................................................................................................................................. 7|
|DAFTAR GAMBAR.................................................................................................................................9|
|DAFTAR TABEL....................................................................................................................................10|
|DAFTAR KODE PROGRAM................................................................................................................ 11|
|DAFTAR LAMPIRAN........................................................................................................................... 12|
|GLOSARIUM...........................................................................................................................................1|
|BAB I PENDAHULUAN.........................................................................................................................2|
|1.1<br>Latar Belakang.........................................................................................................................2|
|1.2<br>Perumusan Masalah.................................................................................................................2|
|1.3<br>Tujuan dan Sasaran Penelitian.................................................................................................2|
|1.4<br>Pembatasan Masalah................................................................................................................2|
|1.5<br>Sistematika Penulisan..............................................................................................................2|
|BAB II TINJAUAN PUSTAKA...............................................................................................................3|
|2.1 Xxxxxx............................................................................................................................................3|
|2.2.1 Xxx Xxxxx Xxxxx...................................................................................................................3|
|2.1.2 Xxx Xxxxx Xxxxx...................................................................................................................3|
|2.1.3 Xxx Xxxxx Xxxxx...................................................................................................................3|
|2.2 Xxxx Xxxxxx Xxxxxx.................................................................................................................... 4|
|**Gambar 2.1**<br>Xxxxx xxxxx xxxxxx.................................................................................................4|
|**Tabel 2.1**<br>Xxxxx Xxxxxxxx Xxxxxx Xxxxxx Xxxxx Xxxxxx xx Xxxxxx Xxxxxx..................... 4|
|2.3 Xxxx Xxxxxx Xxxxxx.................................................................................................................... 5|
|2.4 Xxxx Xxxxxx Xxxxxx.................................................................................................................... 5|
|2.5 Xxxx Xxxxxx Xxxxxx.................................................................................................................... 5|
|BAB III METODOLOGI PENELITIAN..................................................................................................6|
|3.1 Xxxxxx............................................................................................................................................6|
|3.2 Xxxxxx............................................................................................................................................6|
|3.3 Xxxxxx............................................................................................................................................6|
|3.4 Xxxxxx............................................................................................................................................6|
|3.5 Xxxxxx............................................................................................................................................6|



vii 

|BAB IV HASI|L DAN PEMBAHASAN.................................................................................................. 7|
|---|---|
|4.1 Xxxxx...|...........................................................................................................................................7|
|4.2 Xxxxx...|...........................................................................................................................................7|
|4.2.1 Xxx|xx.......................................................................................................................................7|
|4.2.2 Xxx|xx.......................................................................................................................................7|
|4.3 Xxxxx...|...........................................................................................................................................7|
|4.3.1 Xxx|xx.......................................................................................................................................7|
|4.3.2 Xxx|xx.......................................................................................................................................7|
|BAB V PENU|TUP....................................................................................................................................8|
|5.1 Kesimpu|lan......................................................................................................................................8|
|5.2 Saran....|............................................................................................................................................8|
|DAFTAR RUJ|UKAN................................................................................................................................9|
|Lampiran A|Xxxxxxx xxxxxx............................................................................................................A|
|Lampiran B|Xxxxx Xxxxxx...............................................................................................................B|
|Lampiran C|Xxxxx Xxxxxx...............................................................................................................C|
|Lampiran D|Xxxxx Xxxxx.................................................................................................................D|
|Lampiran E|Xxxxx Xxxxxx............................................................................................................... E|
|Lampiran F|Xxxxxx Xxxxxx............................................................................................................. F|
|Lampiran G|Xxxx Xxxxxx.................................................................................................................G|
|Lampiran H|Xxxx Xxxxxx.................................................................................................................H|
|Lampiran I|Xxxxx Xxxxxx................................................................................................................ I|
|Lampiran J|Xxxxx Xxxxxx................................................................................................................ J|
|Lampiran K|Xxxxxx Xxxxxx.............................................................................................................K|
|Lampiran L|Xxxxx Xxxxxx............................................................................................................... L|
|Lampiran M|Xxxxxx Xxxxxx............................................................................................................ M|
|Lampiran N|Xxxxxx Xxxxxx.............................................................................................................N|
|Lampiran O|Xxxxxx Xxxxxx.............................................................................................................O|
|Lampiran P|Xxxxxx Xxxxxx............................................................................................................16|



vii 

## **DAFTAR GAMBAR** 

|Gambar 2.1   Xxxx|5|
|---|---|
|Gambar 2.2   Xxxx|8|
|Gambar 3.1   Xxxx|20|
|Gambar 3.2   Xxxx|31|



viii 

## **DAFTAR TABEL** 

|Tabel 2.1   Xxxx|5|
|---|---|
|Tabel 2.2   Xxxx|8|
|Tabel 3.1   Xxxx|20|
|Tabel 3.2   Xxxx|31|



ix 

## **DAFTAR KODE PROGRAM** 

|Kode Program 2.1|Xxxx|5|
|---|---|---|
|Kode Program 2.2|Xxxx|10|
|Kode Program 3.1|Xxxx|22|
|Kode Program 3.2|Xxxx|24|



x 

## **DAFTAR LAMPIRAN** 

|LAMPIRAN A   Xxxx|A-1|
|---|---|
|LAMPIRAN B   Xxxx|B-1|
|LAMPIRAN C   Xxxx|C-1|
|LAMPIRAN D   Xxxx|D-1|



xi 

## **GLOSARIUM** 

otomasi pengendalian suatu proses secara otomatis sistem interkoneksi elemen-elemen dan peralatan-epralatan untuk suatu tujuan yang diinginkan Σ jumlah 

xii 

## **BAB I PENDAHULUAN** 

**1.1 Latar Belakang 1.2 Perumusan Masalah 1.3 Tujuan dan Sasaran Penelitian 1.4 Pembatasan Masalah 1.5 Sistematika Penulisan** 

1 

## **BAB II TINJAUAN PUSTAKA** 

## **2.1 Xxxxxx** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## 2.2.1 Xxx Xxxxx Xxxxx 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## 2.1.2 Xxx Xxxxx Xxxxx 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

_2.1.2.1 Xxx Xxxxx Xxxxx_ 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## 2.1.3 Xxx Xxxxx Xxxxx 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx xxxx. 

## **2.2 Xxxx Xxxxxx Xxxxxx** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx xxxx.Xxxxx xxxx xxxx (lihat Tabel 2.1) xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx 



2 

xxxxxx xxxx xxxx (lihat Gambar 2.1). Xxxx xxxxx xxxxxxx xxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxxxxxx xxxxxx. 

**Tabel 2.1** Xxxxx Xxxxxxxx Xxxxxx Xxxxxx Xxxxx Xxxxxx xx Xxxxxx Xxxxxx 

|No.<br>Nama|Uraian|
|---|---|



Xxxx xxx xxx xxxxxx xxxxx xxxxxxx xxxxxx xxx xxx xxxxxx xxx xxx 

xxxxxx xxx xxxx 



<!-- Start of picture text -->
N variant =  w 1 X 1 +  w 2 X 2 +  w 3 X 3 + …+  wnXn (2.1)<br><!-- End of picture text -->

Xxxx xxx xxx xxxxxx xxxxx xxxxxxx Persamaan (2.1) xxxxxx xxx xxx xxxxxx xxx xxx xxxxxx xxx xxx xxx xxxx xxxxxx. Xxxx xxx xxxx. 

**Kode program 2.1.** Koneksi PHP dengan MySQL 



## **2.3 Xxxx Xxxxxx Xxxxxx** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## **2.4 Xxxx Xxxxxx Xxxxxx** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

3 

## **2.5 Xxxx Xxxxxx Xxxxxx** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

4 

## **BAB III METODOLOGI PENELITIAN** 

## **3.1 Xxxxxx** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## **3.2 Xxxxxx** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## **3.3 Xxxxxx** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## **3.4 Xxxxxx** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## **3.5 Xxxxxx** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

4 

## **BAB IV HASIL DAN PEMBAHASAN** 

## **4.1 Xxxxx** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## **4.2 Xxxxx** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## 4.2.1 Xxxxx 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## 4.2.2 Xxxxx 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## **4.3 Xxxxx** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## 4.3.1 Xxxxx 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## 4.3.2 Xxxxx 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

5 

## **BAB V PENUTUP** 

## **5.1 Kesimpulan** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

## **5.2 Saran** 

Xxxxx xxxx xxxx xxxxx xxxx xxx xxx xxx xxx xxx xxx xxx xxxxxx xxxx 

xxxx. 

6 

## **DAFTAR RUJUKAN** 

7 

# **Lampiran A Xxxxxxx xxxxxx** 

1 

# **Lampiran B Xxxxx Xxxxxx** 

2 

# **Lampiran C Xxxxx Xxxxxx** 

3 

**Lampiran D Xxxxx Xxxxx** 

4 

# **Lampiran E Xxxxx Xxxxxx** 

5 

# **Lampiran F Xxxxxx Xxxxxx** 

6 

# **Lampiran G Xxxx Xxxxxx** 

7 

# **Lampiran H Xxxx Xxxxxx** 

8 

# **Lampiran I Xxxxx Xxxxxx** 

9 

# **Lampiran J Xxxxx Xxxxxx** 

10 

# **Lampiran K Xxxxxx Xxxxxx** 

11 

# **Lampiran L Xxxxx Xxxxxx** 

12 

**Lampiran M Xxxxxx Xxxxxx** 

13 

# **Lampiran N Xxxxxx Xxxxxx** 

14 

# **Lampiran O Xxxxxx Xxxxxx** 

15 

# **Lampiran P Xxxxxx Xxxxxx** 

Sub Tabel() ' ' Makro1 Makro ' Buat judul tabel ' Selection.InsertRowsAbove 1 Selection.Cells.Merge With Selection.Cells .Borders(wdBorderLeft).LineStyle = wdLineStyleNone .Borders(wdBorderRight).LineStyle = wdLineStyleNone .Borders(wdBorderTop).LineStyle = wdLineStyleNone With .Borders(wdBorderBottom) .LineStyle = wdLineStyleSingle .LineWidth = wdLineWidth075pt .Color = wdColorAutomatic End With .Borders(wdBorderDiagonalDown).LineStyle = wdLineStyleNone .Borders(wdBorderDiagonalUp).LineStyle = wdLineStyleNone .Borders.Shadow = False End With With Options .DefaultBorderLineStyle = wdLineStyleSingle .DefaultBorderLineWidth = wdLineWidth050pt .DefaultBorderColor = wdColorAutomatic End With Selection.Font.Size = 12 With Selection.ParagraphFormat .LeftIndent = CentimetersToPoints(-0.2) .RightIndent = CentimetersToPoints(-0.2) .SpaceBefore = 0 .SpaceBeforeAuto = False .SpaceAfter = 0 .SpaceAfterAuto = False .LineSpacingRule = wdLineSpaceSingle .Alignment = wdAlignParagraphLeft .WidowControl = False .KeepWithNext = False .KeepTogether = False .PageBreakBefore = False .NoLineNumber = False .Hyphenation = True .FirstLineIndent = CentimetersToPoints(0) .OutlineLevel = wdOutlineLevel6 .CharacterUnitLeftIndent = 0 .CharacterUnitRightIndent = 0 .CharacterUnitFirstLineIndent = 0 

8 

.LineUnitBefore = 0 .LineUnitAfter = 0 .MirrorIndents = False .TextboxTightWrap = wdTightNone .CollapsedByDefault = False .ReadingOrder = wdReadingOrderLtr End With Selection.Font.Bold = wdToggle Selection.Font.BoldBi = wdToggle Selection.TypeText Text:="Tabel a.b" Selection.Font.Bold = wdToggle Selection.Font.BoldBi = wdToggle Selection.TypeText Text:=vbTab Selection.ParagraphFormat.TabStops.Add Position:=CentimetersToPoints(2#) _ , Alignment:=wdAlignTabLeft, Leader:=wdTabLeaderSpaces Selection.TypeText Text:="Xxxx Xxx" Selection.Style = ActiveDocument.Styles("Tabel") 'CommandBars("Apply Styles").Visible = False 

8
