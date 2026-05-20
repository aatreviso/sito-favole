# Favole per Dormire — Note di sessione

## 👤 PROFILO UTENTE — leggi PRIMA di tutto

L'utente **non sa programmare**. Non legge il codice, non capisce diff, non sa cosa fa `git rebase` o `npm install`. Lavora su **Windows con PowerShell**. È la stessa persona di Conquizzone (vedi repo `aatreviso/food-war`, CLAUDE.md).

**Regole per ogni risposta dell'agente**:
- Quando devi farlo eseguire qualcosa, **dai i comandi PowerShell pronti da copia-incolla**, non spiegazioni astratte tipo "fai un git pull poi merge"
- Spiega in **italiano semplice** cosa fa ogni blocco di comandi (1 riga, niente gergo)
- Se serve una scelta, presenta opzioni numerate ("opzione 1, opzione 2"), non chiedere "vuoi rebase o merge?"
- Mai dire "apri il file X e cambia Y": se serve modificare un file lo facciamo noi via tool e poi gli diamo il comando per pullare
- Mai dire "pusha tu" senza dargli il comando esatto
- Risultati attesi: dopo aver eseguito il blocco copia-incollato, l'utente deve sapere se è andata bene o male (output da cercare, "se vedi X allora ok, se vedi Y dimmelo")
- L'utente ha Android Studio + Java JBR già installati per build AAB (stesso setup di Conquizzone), keystore di Conquizzone in `C:\Users\aless\Documents\conquizzone-upload.jks` (NON usare per Favole — servirà un keystore NUOVO `favoleperdormire-upload.jks`)

**Sintomi che indicano che NON stai seguendo questa regola**: l'utente risponde "boh, dimmi tu cosa fare", "non capisco", "spiegami passo passo", "scrivi in aramaico". Se succede, riformula in comandi pronti.

## 🎯 Cos'è questo progetto

Trasformare il sito **www.favoleperdormire.it** (WordPress) in un ecosistema multipiattaforma a **costo 0€** che monetizzi meglio dell'attuale.

- **Modello di riferimento**: Conquizzone (`aatreviso/food-war`). Architettura simile: sito web come "source of truth", app Android Capacitor che lo carica via WebView, AdMob bridge nativo per gli ads in-app.
- **PRINCIPIO GUIDA — l'app è un guscio, NON un clone**: il sito WordPress è il prodotto completo e include già funzionalità che funzionano benissimo (es. **filtro favole**, ricerca, categorie, layout lettura). L'app NON deve ricreare nulla di tutto questo: carica il sito in WebView e basta. Si aggiungono SOLO le funzioni che il sito non può dare nativamente (TTS, offline, timer nanna) + il bridge AdMob. Stessa identica filosofia di Conquizzone.
- **Repo GitHub Favole** (questo): `aatreviso/sito-favole`. Sarà la "casa" del guscio Capacitor + script di automazione (pipeline audio/video). NON contiene il sito WordPress (quello vive su SupportHost).
- **Branch sandbox agente**: `claude/website-to-playstore-app-OBjJn`. Push a `main` dal sandbox potrebbe essere bloccato 403 (come in Conquizzone): in quel caso pushare sul branch agente e dare all'utente il comando di merge.

## 📊 Stato attuale del sito

- **Sito**: WordPress su SupportHost (hosting dedicato italiano)
- **Traffico**: ~12.000 utenti attivi/mese, ~96.000 visualizzazioni/mese
- **Revenue attuale**: ~30€/mese con EvolutionGroup (eCPM ~0,4€, **disastroso**)
- **Causa eCPM basso**: 3 fattori sommati
  1. EvolutionGroup è un re-seller (si prende fetta grossa prima di passare a noi)
  2. Pool ristretto di compratori in asta (solo i network selezionati da loro)
  3. Probabile flag "kids/family" sull'audience → inserzionisti adulti tagliati fuori
- **Età target lettori reali**: **ADULTI** (genitori che leggono ai figli). Questo è cruciale: l'app NON va pubblicata come *Designed for Families*, va in categoria Books/Entertainment target 18+, così possiamo monetizzare a prezzo pieno con interstitial e ads personalizzati.
- **Contenuto sul sito oggi**: solo testo, nessun audio né video.

## 💰 Strategia di monetizzazione (DECISA con utente, 15 maggio 2026)

Mix di entrate atteso a regime (~6 mesi):

| Voce | Stima conservativa | Note |
|---|---|---|
| Sito con Ezoic (era 30€) | 150-270€/mese | Switch da EvolutionGroup |
| Banner AdMob in-app | 800-1.000€/mese | $1,2-2 eCPM adulti IT |
| Interstitial tra favole | 400-600€/mese | 1 ogni 4 favole, mai forzato |
| Rewarded "audio premium" | 100-200€/mese | 5% adoption |
| Subscription Favole Plus | 400-1.000€/mese | €2,99/mese, 1-3% conv |
| YouTube Ads (canale video) | Variabile, cresce nel tempo | 2-5€ CPM IT, lungo termine |
| Affiliate Amazon libri | 100-300€/mese | Classici → libri reali |
| **Totale stimato** | **2.000-3.500€/mese** | Vs 30€ attuali |

## 🗺️ Roadmap (3 fasi)

### Fase 1 — Sito web: sostituire EvolutionGroup (settimana 1)
- Migrare ads da EvolutionGroup → **Ezoic** (decisione provvisoria, AdSense come piano B)
- Setup Ezoic in modalità **conservativa** all'inizio: bassa densità ads (2 banner per pagina max), modulo "Leap" attivo per velocità sito
- Cambiare configurazione audience: NON kids/family → adulti
- Riscrivere copy homepage WP per posizionarsi come "portale per genitori"
- **Risultato atteso**: da 30€ → 150-270€/mese in 30 giorni

### Fase 2 — App Android Capacitor (settimane 2-4)
- Package: `it.favoleperdormire.app`
- Architettura: Capacitor 8, WebView carica `favoleperdormire.it`
- **L'app è un GUSCIO, non un clone**: tutta la UI (homepage, filtro favole, categorie, lettura) viene dal sito WordPress. NON riscrivere componenti in HTML/JS app-side. Le uniche cose app-side sono i 3 plugin nativi + il bridge AdMob.
- Plugin nativi obbligatori (servono a non farsi rifiutare da Google Play come "minimum functionality"):
  - **TTS**: `@capacitor-community/text-to-speech` — voce nativa Android italiana
  - **Preferiti offline**: cache IndexedDB tramite service worker
  - **Timer nanna**: auto-spegnimento schermo dopo N minuti
- Bridge JS AdMob nativo (replicare pattern Conquizzone: `window.NativeAdMob.showBanner/showInterstitial/showRewardedAd`)
- Categoria Play Store: **Books & Reference** (NON Family)
- Target audience: 18+ (genitori)
- Privacy policy GDPR adulti (NO COPPA)
- Build AAB sul PC Windows utente, stesso workflow di Conquizzone (`gradlew.bat bundleRelease`)
- Keystore NUOVO: `favoleperdormire-upload.jks` (NON il keystore di Conquizzone)

### Fase 3 — Pipeline audio + video YouTube (parallela o successiva)
**Idea**: generare automaticamente da ogni favola testuale → MP3 narrato + MP4 video, pubblicare su sito/app/YouTube/podcast.

Pipeline tecnica:
1. Script Python o Node legge le favole dal DB WordPress (API REST WP)
2. Per ogni favola → chiamata Google Cloud TTS (voce WaveNet IT premium, FREE TIER 4M char/mese — il catalogo intero rientra probabilmente nel free)
3. Salva MP3 sul server SupportHost
4. Genera MP4 con FFmpeg: audio MP3 + immagine fissa (cover o slideshow di 4-5 illustrazioni)
5. Upload automatico a YouTube tramite YouTube Data API (canale "Favole per dormire")
6. Embed video YouTube sotto il testo della favola sul sito
7. (Opzionale fase 3.5) Stesso MP3 → feed RSS podcast → Spotify/Apple Podcasts gratis

Costi: 0€ (TTS in free tier, FFmpeg gratis, YouTube/Spotify gratis).

Tempi sviluppo: 2-3 giorni.

### Fase 4 — Subscription Favole Plus (opzionale, dopo che l'app è in produzione)
- €2,99/mese o €19,99/anno
- Vantaggi: zero ads + voce premium + favole esclusive + temi notturni
- Implementazione: Google Play Billing + paywall + backend verifica receipt
- Backend leggero: Cloudflare Workers free tier o estensione del backend Conquizzone su Railway
- **Decisione finale lanciare/non lanciare**: rimandata, dopo aver visto i numeri reali di app + ads. Utente ok in linea di principio (fiscalità chiara, stesso flusso Google → P.IVA Torpal degli AdMob di Conquizzone).

## 🎁 Monetizzazione app: modello 3-tier (definito 18 maggio 2026)

Decisione architetturale dopo brainstorming con utente.

### Tier 1 — Free senza rewarded (entry level)
- Tutte le favole testuali leggibili
- Banner AdMob in basso (non in pagina lettura)
- 1 interstitial ogni N favole completate (mai durante TTS)
- TTS solo con voce nativa Android (gratis ma robotica)

### Tier 2 — Free con Rewarded (sblocchi temporanei opt-in)

| Sblocco | Cosa ottiene | Durata | Frequency cap |
|---|---|---|---|
| Voce Gufetto (ElevenLabs) | Audio premium narrato dalla voce brand | 1 ora | max 2-3/giorno |
| Timer nanna esteso | Riproduzione consecutiva favole narrate | 1 ora (vs 15 min default) | 1/giorno |
| Favola speciale della settimana | Contenuto esclusivo settimanale rotante | tutta la settimana | 1/settimana |
| 3 favole offline (anche audio) | Bonus iniziale per "tasting" della funzione | permanente | 1 sola volta |

UX rewarded:
- Countdown chiaro durante lo sblocco ("✨ Voce attiva: 47 min rimanenti")
- Reminder a 5 minuti dalla scadenza con offerta "guarda altro video per +1 ora"
- Mai forzati, sempre triggered dall'utente

### Tier 3 — Favole Plus (subscription, €2,99/mese o €19,99/anno)

| Feature | Free | Free + Rewarded | Plus |
|---|---|---|---|
| Lettura favole testuali | ✅ | ✅ | ✅ |
| Voce Gufetto (ElevenLabs) | ❌ | 1h temp | **Sempre attiva** |
| Timer nanna | 15 min | 1h temp | **2 ore** |
| Riordino playlist timer (drag&drop) | ❌ | ❌ | **Sì** |
| Banner / Interstitial | ✅ visti | ✅ visti | **Niente** |
| Musica di sottofondo (4 tracce) | ❌ | ❌ | **Sì, selezionabile** |
| Download offline favole + audio | 3 slot | 3 slot | **Illimitato** |
| Favola speciale settimanale | Rewarded | Rewarded | **Sempre sbloccata** |

Trial gratuito: 7 giorni (Google Play standard, aumenta conv 30-50%).

### Considerazioni implementative aperte
- **Timer "narrate consecutivamente"**: ordine default da definire. Probabilmente: ultima riprodotta + favole stessa categoria. Plus permette drag&drop manuale.
- **Musica sottofondo**: 4 tracce royalty-free (Pixabay/FreePD) curate ad hoc: "ninna nanna pianoforte", "foresta notturna", "mare calmo", "pioggia leggera". Volume dinamico via FFmpeg sidechain compress (25-30% sotto voce, 60% nelle pause).
- **Offline storage**: ~5-10MB per favola (testo + audio). 3 offline gratis = ~30MB, illimitato Plus = anche se scarica tutte le 75 favole sono <800MB, gestibile.
- **Frequency cap rewarded**: max 3 rewarded/sessione utente, max 5/giorno. Sopra → mostra messaggio "torna domani per più sblocchi" (no nag).

### Numeri attesi (rivisti, 10.000 MAU)
- Subscription Plus 2% conv = 200 × €2,99 × 0,85 (Google fee 15%) = **~€508/mese**
- Rewarded (9.800 non-paganti × 1,5 ad/giorno × $5 eCPM) = **~€600/mese**
- Banner + interstitial sui non-paganti = **~€700/mese**
- **Totale app: ~€1.800/mese** (in linea con stima iniziale di €1.500-2.500)

## 🔑 Account condivisi con Conquizzone

- **Play Console**: stesso account dev (Torpal di Alessandro Zaratin). $25 dev fee già pagati. Aggiungiamo Favole come nuova app sullo stesso account, costo aggiuntivo 0€.
- **AdMob**: stesso account `ca-app-pub-1355648809209212` (account condiviso, dichiarato in CLAUDE.md Conquizzone). Per Favole creeremo **nuovi ad unit ID** (banner, interstitial, rewarded) dentro lo stesso account.
- **P.IVA**: Torpal di Alessandro Zaratin, P.IVA IT05049650269, Via Bavaresco 11/2, 31038 Paese (TV). Email: aatreviso@gmail.com.
- **PC build**: stesso PC Windows dell'utente, stesso Android Studio in `C:\Program Files\Android\Android Studio\`, stesso Java JBR.

## 🆔 ID da creare quando serviranno (TODO)
- [ ] AdMob App ID per Favole: DA CREARE (dentro account `ca-app-pub-1355648809209212`)
- [ ] AdMob Banner ad unit ID: DA CREARE
- [ ] AdMob Interstitial ad unit ID: DA CREARE
- [ ] AdMob Rewarded ad unit ID: DA CREARE
- [ ] Keystore Android upload key: DA CREARE (`favoleperdormire-upload.jks`, salvarne SHA-1 in questo file)
- [ ] Google Cloud project per TTS API: DA CREARE (account Google esistente di Conquizzone)
- [ ] Canale YouTube "Favole per dormire": DA VERIFICARE se esiste già

## 🚫 Cosa NON serve (differenze importanti da Conquizzone)

Conquizzone ha **Railway + Postgres + Redis** perché è un gioco custom in Node.js: senza quel backend acceso 24/7 non funziona niente.

**Favole NON ha bisogno di niente di tutto questo**:
- Il "backend" è già WordPress, gira su SupportHost (CMS + database MySQL inclusi)
- L'app Capacitor parla direttamente col sito WordPress (su SupportHost) e con AdMob (server Google). Niente nostro server in mezzo.
- Pipeline audio/video (Fase 3): script batch eseguito sul **PC utente** o su **GitHub Actions free tier** (2000 min/mese). Genera i file e si spegne. NON serve server sempre acceso.
- Backend subscription (Fase 4, opzionale): plugin PHP dentro WordPress stesso (sfrutta SupportHost), oppure **Cloudflare Workers free tier** (100k req/giorno). **NON Railway**.

Cloudflare Free può eventualmente essere utile davanti a SupportHost come CDN per servire MP3 audio senza saturare banda hosting. Decisione da prendere in Fase 3.

## 🌐 Hosting e infrastruttura sito

- **Hosting WordPress**: SupportHost (italiano, dedicato). Da verificare:
  - [ ] Versione PHP supportata
  - [ ] Spazio disco residuo (servirà per ospitare MP3 generati, ~5-20MB per favola)
  - [ ] Banda mensile inclusa (gli MP3 servono download)
  - [ ] Accesso SSH/SFTP/cPanel?
- **DNS**: da verificare se è su Cloudflare o resta su SupportHost
- **CDN**: nessuno attivo per ora (Cloudflare Free sarebbe ideale per servire MP3 senza saturare banda hosting)
- **WordPress**: versione + tema + plugin installati → da catalogare in prima sessione di lavoro reale

## 📋 TODO prossime sessioni (in ordine di priorità)

1. **Fase 1 — sito** (prima cosa, ROI immediato in 30 giorni):
   - [ ] Iscrizione Ezoic + integrazione (decidere se via DNS o via plugin WP)
   - [ ] Configurazione audience "adulti" in Ezoic
   - [ ] Cattura screenshot/log dell'attuale configurazione EvolutionGroup prima di toglierli (per confronto)
   - [ ] Disattivare EvolutionGroup
   - [ ] Misurare per 14 giorni, confrontare eCPM
2. **Fase 2 — app**:
   - [ ] Setup Capacitor base + WebView verso favoleperdormire.it
   - [ ] Plugin TTS + bridge JS
   - [ ] Plugin preferiti offline
   - [ ] Plugin AdMob (riusare pattern Conquizzone)
   - [ ] Generazione keystore + assets store listing
   - [ ] Upload internal testing Play Console
3. **Fase 3 — audio/video**:
   - [ ] Script TTS batch (Python o Node)
   - [ ] Script FFmpeg audio + immagine → MP4
   - [ ] Setup canale YouTube + API credentials
   - [ ] Upload automatico

## ❌ COSE DA NON FARE

- ❌ **NON pubblicare l'app come "Designed for Families"** → il pubblico è adulto, taggarla kids significa rinunciare al 60% del revenue ads
- ❌ **NON committare keystore, password o token nel repo pubblico** (CLAUDE.md di Conquizzone ha alcune password committed: per Favole **non replichiamo questo**, le password vivono solo nel password manager dell'utente)
- ❌ **NON tentare di scaricare Android SDK nel sandbox** (network bloccato per `dl.google.com`) → build sempre sul PC utente
- ❌ **NON pubblicare l'app come "shell webview pura"** senza almeno 2-3 funzioni native (TTS, offline, timer) → Google Play rifiuta
- ❌ **NON committare HTML statici nella root del repo** (lesson learned Conquizzone: Cloudflare Pages li espone pubblicamente)
- ❌ **NON installare plugin WordPress a casaccio** sul sito di produzione senza backup database

## 📝 Cronologia decisioni strategiche

- **15 maggio 2026**: prima sessione di strategia con utente. Definita roadmap 3 fasi. Confermato target ADULTI (no Families Policy). Confermato che riusiamo account Play Console + AdMob di Conquizzone. Confermato idea audio TTS generato una volta sola + video YouTube derivati. Subscription approvata in linea di principio, decisione finale rimandata post-lancio app. Memoria progetto creata.

- **18 maggio 2026**: prima sessione operativa Fase 3. Pipeline audio + video funzionante in produzione via GitHub Actions. Test reale completato su favola "La gatta Sofia". Dettagli sotto.

## 🎙️ Pipeline audio + video — STATO: FUNZIONANTE (18 maggio 2026)

Costruita e testata via GitHub Actions. Tutto pushato su `main`.

### Stack tecnico effettivo
- **TTS**: ElevenLabs API, modello `eleven_multilingual_v2`
- **Pricing**: PAYG ($0.10 / 1.000 caratteri Multilingual v2). Stima totale catalogo 75 favole: **~$27 una tantum** (~€25). Una favola media (2.000 char) costa ~$0.20.
- **API key**: configurata come GitHub Secret `ELEVENLABS_API_KEY` nel repo `aatreviso/sito-favole`.
- **Voice ID scelto dall'utente**: `3DPhHWXDY263XJ1d2EPN` (provvisorio, ne sta cercando altre alternative migliori — TODO sotto).
- **Voice settings finali** (dopo iterazioni):
  - `stability`: 0.40 (espressiva)
  - `similarity_boost`: 0.75
  - `style`: 0.45 (gioiosa, caratterizzata)
  - `speed`: 0.92 (8% più lenta della normale)
  - `use_speaker_boost`: true
- **Post-processing audio**: pitch shift -0.5 semitoni via ffmpeg (`asetrate + atempo`). Mantiene durata, riduce "roca".
- **Pause naturali**: tag SSML `<break time="0.6s"/>` pre-titolo, `<break time="1.0s"/>` post-titolo, `<break time="0.35s"/>` dopo ogni `. ! ?` nel testo storia, `<break time="1.0s"/>` finale.

### Struttura cartelle nel repo
```
sito-favole/
├── testi/                 # input: testo favola (slug.txt)
├── immagini/              # input: illustrazione quadrata (slug.png o .jpg)
├── audio/                 # output: MP3 narrazione (slug.mp3) + timestamps (slug.json)
├── video/                 # output: MP4 1080x1920 reel (slug.mp4)
├── assets/
│   ├── branding/          # logo.png (gufetto trasparente)
│   └── fonts/             # Pacifico-Regular.ttf, ComingSoon-Regular.ttf
├── tools/
│   └── genera_video.py    # script Python pipeline completa
└── .github/workflows/
    └── genera-video.yml   # workflow GitHub Actions
```

### Come lanciare un nuovo video
1. Caricare `testi/<slug>.txt` (testo favola) e `immagini/<slug>.png` (quadrata)
2. Andare su https://github.com/aatreviso/sito-favole/actions/workflows/genera-video.yml
3. "Run workflow" → input:
   - `favola`: slug del file (es. `la-gatta-sofia`)
   - `voice_id`: opzionale, default è `3DPhHWXDY263XJ1d2EPN`
   - `rigenera_audio`: checkbox. **False = cache** (riusa audio se presente, gratis). **True = rigenera** da API (costa crediti).
4. In ~3 minuti gli output sono committati su `main` e disponibili in `audio/` e `video/`.

### Layout video (9:16, 1080x1920)
- **Titolo in alto** (y=30-250): font Pacifico oro #ad9853, fino a 84px, shadow nera
- **Immagine quadrata** (y=290-1170, centrata orizzontalmente): 880x880 con angoli arrotondati 60px, ombra morbida dietro
- **Sottotitoli karaoke** (y=1210-1730): font Coming Soon bianco 84px, outline navy 5px, sincronizzati al millisecondo via ElevenLabs character timestamps. Rispettano confini di frase (chunk forzato dopo ogni `. ! ?`).
- **Footer** (y=1740-1920): logo gufetto 160px + "favoleperdormire.it" in oro
- **Sfondo**: gradiente notturno brand `#103f65 → #081e32` con stelline nelle zone libere

### Sistema cache audio (importante per non spendere crediti)
Lo script ha 3 modalità in ordine di preferenza:
1. **Cache completa**: se `audio/<slug>.mp3` + `audio/<slug>.json` (timestamps) esistono e `rigenera_audio=false` → riusa entrambi, sub karaoke perfetto, **ZERO API call**
2. **Cache parziale**: se solo `audio/<slug>.mp3` esiste (no JSON) → riusa audio, sub distribuiti uniformemente sulla durata reale, **ZERO API call**. Leggermente meno preciso sui timing ma costo zero.
3. **Fresh**: nessun file presente o `rigenera_audio=true` → chiamata ElevenLabs + salva tutto

### Pause naturali nella narrazione
Lo script inserisce automaticamente `<break time="0.35s"/>` dopo ogni `. ! ?` nel testo. Il parser ignora i tag SSML nei character timestamps (bug "<break time= 1>" trapelava nei sottotitoli, risolto).

## 🆔 ID e credenziali aggiornati al 18 maggio 2026

- [x] **ElevenLabs API key**: salvata come GitHub Secret `ELEVENLABS_API_KEY` nel repo. ⚠️ L'utente è stato avvisato di rigenerarla dato che era stata condivisa in chat per il setup iniziale.
- [x] **ElevenLabs voice ID**: `3DPhHWXDY263XJ1d2EPN` (provvisorio, utente sta cercando alternative migliori)
- [x] **Logo gufetto**: caricato in `assets/branding/logo.png` (PNG trasparente)
- [x] **Font branding**: Pacifico-Regular.ttf + ComingSoon-Regular.ttf in `assets/fonts/` (Google Fonts gratuiti, già nel repo)
- [x] **Colori brand**: blu navy `#103f65`, oro `#ad9853` (forniti dall'utente)
- [ ] AdMob App ID per Favole: DA CREARE (dentro account `ca-app-pub-1355648809209212`)
- [ ] AdMob Banner / Interstitial / Rewarded ad unit ID: DA CREARE
- [ ] Keystore Android upload key: DA CREARE (`favoleperdormire-upload.jks`, salvarne SHA-1 in questo file)

## 📋 TODO prossime sessioni (in ordine di priorità, aggiornato 18 maggio 2026)

### Prossima sessione immediata
1. **Voce alternativa ElevenLabs** (utente sta valutando): provare 2-3 voci candidate, generare lo stesso audio "La gatta Sofia" per A/B test sentito. Quando trovata, aggiornare `DEFAULT_VOICE` in `tools/genera_video.py`.
2. **Batch generazione del catalogo intero** (~75 favole):
   - Estrarre singole favole dai 5 ODT/DOCX (`/root/.claude/uploads/045d8f45-...`) → file `testi/<slug>.txt` uno per favola
   - Generare/raccogliere immagine quadrata per ogni favola → `immagini/<slug>.jpg`
   - Lanciare workflow per ognuna (o crearne uno "batch" che gira tutte in sequenza). Costo stimato: ~$25 una tantum totale.
   - Upload risultati su SupportHost via SFTP per servirli dal sito

### Fase 1 — Sito web (ROI immediato, ancora da fare)
- [ ] Iscrizione Ezoic + integrazione (decidere se via DNS o via plugin WP)
- [ ] Configurazione audience "adulti" in Ezoic
- [ ] Cattura screenshot/log dell'attuale configurazione EvolutionGroup prima di toglierli (per confronto)
- [ ] Disattivare EvolutionGroup
- [ ] Misurare per 14 giorni, confrontare eCPM
- [ ] Embeddare i video generati nelle pagine WordPress sotto il testo della favola

### Fase 2 — App Capacitor (dopo audio/video pronto)
- [ ] Setup Capacitor base + WebView verso favoleperdormire.it
- [ ] Plugin TTS + bridge JS
- [ ] Plugin preferiti offline
- [ ] Plugin AdMob (riusare pattern Conquizzone)
- [ ] Generazione keystore + assets store listing
- [ ] Upload internal testing Play Console

### Fase 3.5 — YouTube + Podcast (dopo batch generazione)
- [ ] Setup canale YouTube "Favole per Dormire" + API credentials
- [ ] Script di upload automatico dei MP4 a YouTube
- [ ] Setup feed RSS podcast → Spotify/Apple Podcasts

## 🔧 File chiave del repo (per future sessioni)

| File | Cosa fa |
|---|---|
| `tools/genera_video.py` | Pipeline completa: ElevenLabs → MP3 + timestamps → pitch shift → ASS sottotitoli → FFmpeg video MP4 |
| `.github/workflows/genera-video.yml` | Trigger manuale (workflow_dispatch) con input favola/voice/rigenera_audio |
| `testi/la-gatta-sofia.txt` | Testo di test usato durante setup pipeline |
| `immagini/la-gatta-sofia.jpg` | Immagine di test usata durante setup pipeline |
| `assets/branding/logo.png` | Logo Mr. Gufetto |
| `assets/fonts/Pacifico-Regular.ttf` | Font titolo |
| `assets/fonts/ComingSoon-Regular.ttf` | Font sottotitoli |
| `audio/la-gatta-sofia.mp3` | Output di esempio (modalità podcast) |
| `video/la-gatta-sofia.mp4` | Output di esempio (reel 9:16) |
