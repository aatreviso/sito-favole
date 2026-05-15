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
