# Modellazione dati del prototipo EuniGraph basata su OpenAIRE Beginner’s Kit

## Scopo del documento

Questo documento descrive la modellazione dati scelta per il prototipo **EuniGraph**, con particolare attenzione alla compatibilità con il **Beginner’s Kit** di OpenAIRE e con il modello concettuale dell’OpenAIRE Graph.

La definizione relazionale concreta implementata nel repository è documentata in [data-model.md](data-model.md).

L’obiettivo non è copiare 1:1 lo schema OpenAIRE nel database applicativo, ma progettare un **database PostgreSQL canonico** capace di:

- accogliere i dati reali del Beginner’s Kit
- mantenere la provenance del dato importato
- supportare ingestione incrementale da più sorgenti
- costruire il grafo di coautorialità
- collegare i record strutturati agli embedding memorizzati in Qdrant
- rimanere estendibile verso fonti e funzionalità future

## Perché il Beginner’s Kit è il riferimento iniziale giusto

Per il prototipo, il **Beginner’s Kit** è il dataset reale più adatto da usare come riferimento iniziale per tre motivi:

1. è un sottoinsieme reale dell’OpenAIRE Graph costruito apposta per esplorazione e sperimentazione
2. contiene **research products**, **organizations**, **data sources**, **projects**, **communities** e soprattutto **relationships**, cioè i collegamenti espliciti tra entità
3. include un notebook che mostra già un flusso di analisi reale sui dati tramite Spark

La documentazione OpenAIRE specifica che il Beginner’s Kit comprende:
- un sottoinsieme del grafo con i research products pubblicati tra **2024-06-01** e **2024-12-31**
- tutte le entità collegate a tali prodotti
- le rispettive relazioni
- un notebook Jupyter di esempio per l’analisi del dataset. citeturn762016view0turn464609view3

## Cosa emerge dal notebook del Beginner’s Kit

Dall’analisi del notebook allegato emerge che il Beginner’s Kit viene caricato come insieme di dataset separati, coerenti con il modello OpenAIRE:

- `publication`
- `dataset`
- `software`
- `other`
- `datasource`
- `organization`
- `project`
- `community`
- `relation`

Nel notebook, queste collezioni vengono lette con schemi distinti e poi esposte come tabelle temporanee Spark. Questo conferma che, anche nel sottoinsieme Beginner’s Kit, OpenAIRE mantiene una separazione netta tra:
- entità principali
- relazioni del grafo
- metadati descrittivi delle entità

Il notebook mostra anche query reali su:
- relazioni aggregate per semantica
- publishing venues
- citazioni
- soggetti/subjects
- progetti per organizzazione
- prodotti di ricerca per organizzazione

Questa osservazione è importante perché indica che il nostro database deve essere progettato per:
- importare entità eterogenee
- mantenere relazioni esplicite
- supportare query analitiche e aggregazioni
- non perdere il collegamento con la struttura originale della sorgente

## Il modello OpenAIRE da rispettare concettualmente

L’OpenAIRE Graph è modellato come grafo di **entità** e **relazioni**. Le entità principali sono:
- research products
- data sources
- organizations
- projects
- communities
- persons. citeturn464609view0

Per il perimetro MVP di EuniGraph, le componenti più rilevanti sono:

- **Research products**: nel nostro caso interessano soprattutto le `publication`, ma il Beginner’s Kit include anche `data`, `software` e `other` come sottotipi di `ResearchProduct` citeturn464609view1
- **Organizations**: rappresentano università, enti di ricerca, istituzioni e altre unità organizzative coinvolte nel grafo citeturn464609view0
- **Data sources**: servono a mantenere la tracciabilità della provenienza e sono una parte esplicita del modello OpenAIRE citeturn762016view3
- **Relationships**: OpenAIRE usa un oggetto relazione distinto, con `source`, `target`, `reltype`, `provenance`, `validated` e `validationDate`, cioè un vero edge tipizzato del grafo citeturn762016view2

## Principio di modellazione scelto

La decisione principale è la seguente:

**PostgreSQL non replicherà in modo speculare il dump OpenAIRE.**
Sarà invece progettato come **schema canonico applicativo** guidato dai dati OpenAIRE.

Questo significa che distinguiamo due livelli:

### 1. Livello sorgente
Conserva:
- identificativi originali
- payload raw
- provenienza
- metadati tecnici della raccolta

### 2. Livello canonico
Rappresenta:
- pubblicazioni
- ricercatori
- organizzazioni
- affiliazioni
- authorship
- collegamenti a embedding
- collegamenti organizzativi rilevanti per analytics e visualizzazione

Questa scelta evita due problemi:
- dipendere troppo dalla forma attuale dei payload OpenAIRE
- perdere dettagli utili per debug, reprocessing e audit

## Decisioni progettuali già assunte

Nel processo di progettazione sono state fissate le seguenti decisioni:

- chiavi primarie: **UUID**
- gestione degli identificativi esterni aggiuntivi: **sì**, tramite tabella dedicata
- tabella esplicita `publication_organization`: **sì**
- `topic` come entità forte nel MVP: **no**
- affiliazioni con dimensione temporale semplice: **sì**

Queste decisioni sono coerenti con l’uso reale del Beginner’s Kit e con gli obiettivi del prototipo.

## Strategia generale del database PostgreSQL

Il database PostgreSQL del prototipo deve essere in grado di:

1. importare i research products del Beginner’s Kit, in particolare le pubblicazioni
2. salvare l’autorship mantenendo l’ordine degli autori
3. salvare organizzazioni e relazioni con le pubblicazioni
4. mantenere provenance e payload raw della sorgente
5. essere interrogabile per:
   - pubblicazioni per autore
   - pubblicazioni per organizzazione
   - archi di coautorialità
   - metadati di publication utili per dashboard
   - collegamento tra publication ed embedding vettoriale

## Modellazione proposta

### 1. `data_source`

Rappresenta la sorgente logica da cui arrivano i dati.

Nel caso del Beginner’s Kit, la sorgente iniziale sarà OpenAIRE.

Campi principali:
- `id` UUID
- `name`
- `source_type`
- `base_url`
- `description`
- `is_active`
- `created_at`
- `updated_at`

### Motivazione
OpenAIRE tratta i data source come entità di primo livello e sottolinea l’importanza di mantenere la provenance dei metadati raccolti. citeturn762016view3

---

### 2. `ingestion_run`

Traccia ogni processo di importazione.

Campi principali:
- `id` UUID
- `data_source_id`
- `status`
- `started_at`
- `completed_at`
- `triggered_by`
- `notes`
- `raw_config`

### Motivazione
Serve per:
- distinguere diversi caricamenti del Beginner’s Kit
- rendere ripetibile il processo di ingestione
- facilitare debug e reprocessing

---

### 3. `source_record`

Conserva la traccia del record originale importato.

Campi principali:
- `id` UUID
- `data_source_id`
- `ingestion_run_id`
- `entity_type`
- `source_identifier`
- `source_version`
- `checksum`
- `raw_payload` JSONB
- `ingested_at`

Vincolo importante:
- unique su `(data_source_id, entity_type, source_identifier)`

### Motivazione
Questa tabella è centrale. OpenAIRE mette forte enfasi sulla provenance e sulla possibilità di ricostruire il dato a partire dalla sorgente originale. citeturn762016view3

È anche la tabella che rende il database “pronto ad accogliere” il Beginner’s Kit senza forzare ogni dettaglio del payload dentro il modello canonico.

---

### 4. `organization`

Rappresenta università, enti, dipartimenti o altre strutture organizzative.

Campi principali:
- `id` UUID
- `name`
- `normalized_name`
- `organization_type`
- `country_code`
- `city`
- `website`
- `parent_organization_id`
- `ror_id`
- `openaire_id`
- `created_at`
- `updated_at`

### Motivazione
OpenAIRE modella le organizzazioni come entità del grafo. Inoltre, il layer delle relazioni include anche relazioni organizzazione-organizzazione come `IsChildOf / IsParentOf`, quindi è utile predisporre una gerarchia interna anche nello schema canonico. citeturn287019view1

La scelta di una sola tabella `organization`, invece di tabelle separate `university`, `department`, `institute`, mantiene il modello semplice e flessibile.

---

### 5. `researcher`

Rappresenta la persona canonica del sistema applicativo.

Campi principali:
- `id` UUID
- `full_name`
- `given_name`
- `family_name`
- `normalized_name`
- `display_name`
- `orcid`
- `email`
- `profile_url`
- `primary_organization_id`
- `created_at`
- `updated_at`

### Motivazione
Nel Beginner’s Kit il notebook carica pubblicazioni e relazioni, ma non materializza direttamente una tabella persons nel sottoinsieme usato per le analisi locali. Tuttavia, nel data model OpenAIRE le **persons** sono entità di primo livello e gli autori compaiono già come array strutturato nei `ResearchProduct`, con campi come `fullName`, `rank`, `name`, `surname` e `pid`. citeturn464609view0turn762016view4

Per il nostro sistema, conviene quindi estrarre e canonicalizzare i ricercatori in una tabella dedicata.

---

### 6. `researcher_affiliation`

Traccia l’affiliazione del ricercatore verso un’organizzazione.

Campi principali:
- `id` UUID
- `researcher_id`
- `organization_id`
- `role_title`
- `start_date`
- `end_date`
- `is_primary`
- `source_record_id`
- `created_at`
- `updated_at`

### Motivazione
OpenAIRE distingue chiaramente il paese del data source dal paese delle affiliazioni degli autori, rimandando queste ultime al livello delle relazioni di affiliazione. Inoltre, il layer relazionale include il collegamento `hasAuthorInstitution / isAuthorInstitutionOf` tra `Result` e `Organization`. citeturn287019view1turn287019view4

Nel nostro schema, l’affiliazione viene modellata in forma semplice ma già pronta a essere storicizzata.

---

### 7. `publication`

Rappresenta la pubblicazione canonica.

Campi principali:
- `id` UUID
- `title`
- `normalized_title`
- `abstract`
- `publication_year`
- `publication_date`
- `doi`
- `openaire_id`
- `publication_type`
- `language_code`
- `journal_name`
- `venue_name`
- `publisher`
- `open_access`
- `source_url`
- `canonical_source_record_id`
- `created_at`
- `updated_at`

### Motivazione
Il `ResearchProduct` di OpenAIRE contiene campi come:
- `id`
- `type`
- `originalIds`
- `mainTitle`
- `authors`
- `dateOfCollection`
- `descriptions`
- `publicationDate`
- `publisher`
- `sources`
- `pids`. citeturn464609view1turn287019view4

Nel notebook del Beginner’s Kit, lo schema delle pubblicazioni usa campi top-level come:
- `id`
- `maintitle`
- `author`
- `publicationdate`
- `publisher`
- `pid`
- `subjects`
- `container`
- `description`
- `type`

Questo conferma che la tabella `publication` deve essere il centro del modello canonico.

### Nota progettuale
Per il prototipo:
- `journal_name` e `venue_name` restano denormalizzati
- `title` è la proiezione canonica di `mainTitle` / `maintitle`
- `abstract` deriva principalmente da `descriptions` / `description`
- `doi` va estratto da `pids` o dagli original identifiers quando disponibile

---

### 8. `publication_author`

Tabella ponte tra pubblicazioni e ricercatori.

Campi principali:
- `id` UUID
- `publication_id`
- `researcher_id`
- `author_position`
- `author_list_name`
- `is_corresponding`
- `source_record_id`
- `created_at`

Vincoli consigliati:
- unique su `(publication_id, researcher_id)`
- unique su `(publication_id, author_position)` se la qualità dei dati lo consente

### Motivazione
Gli autori in OpenAIRE sono un array strutturato del research product, con `rank` esplicito. Questo rende necessario preservare l’ordine autore. citeturn762016view4

Questa tabella è anche la base diretta per la costruzione del **grafo di coautorialità**.

---

### 9. `publication_organization`

Relazione esplicita tra pubblicazione e organizzazione.

Campi principali:
- `id` UUID
- `publication_id`
- `organization_id`
- `relation_type`
- `source_record_id`
- `created_at`

Vincolo consigliato:
- unique su `(publication_id, organization_id, relation_type)`

### Motivazione
Nel grafo OpenAIRE, il collegamento tra `Result` e `Organization` esiste esplicitamente come relazione tipizzata, ad esempio `hasAuthorInstitution / isAuthorInstitutionOf`. citeturn287019view1

Materializzare questa tabella nel modello canonico rende più semplici:
- le query per organizzazione
- le dashboard
- i conteggi di pubblicazioni per università
- la navigazione frontend

---

### 10. `external_identifier`

Contiene identificativi esterni addizionali per entità canoniche.

Campi principali:
- `id` UUID
- `entity_type`
- `entity_id`
- `identifier_type`
- `identifier_value`
- `is_primary`
- `source_record_id`
- `created_at`

Vincolo consigliato:
- unique su `(entity_type, identifier_type, identifier_value)`

### Motivazione
OpenAIRE usa sia `originalIds` sia `pids`, con molteplici schemi di identificazione. Questo rende utile una tabella generica capace di assorbire identificativi ulteriori senza dover cambiare continuamente il core schema. citeturn464609view1turn762016view3

---

### 11. `publication_embedding`

Collega la pubblicazione canonica all’embedding memorizzato in Qdrant.

Campi principali:
- `id` UUID
- `publication_id`
- `qdrant_collection`
- `qdrant_point_id`
- `embedding_model`
- `embedding_version`
- `content_hash`
- `created_at`
- `updated_at`

Vincolo consigliato:
- unique su `(publication_id, embedding_model, embedding_version)`

### Motivazione
Il database PostgreSQL rimane la fonte canonica dei metadati; Qdrant è il layer vettoriale. Serve quindi una tabella di collegamento stabile, che permetta:
- reindicizzazione
- versionamento dell’embedding
- sincronizzazione tra structured layer e vector layer

## Relazione tra schema OpenAIRE e schema PostgreSQL

Di seguito la logica di mapping principale.

### OpenAIRE `ResearchProduct` / Beginner’s Kit `publication`
Mappa su:
- `publication`
- `publication_author`
- `external_identifier`
- `source_record`

### OpenAIRE `Organization`
Mappa su:
- `organization`
- `external_identifier`
- `source_record`

### OpenAIRE `DataSource`
Mappa su:
- `data_source`
- `source_record`

### OpenAIRE `Relationship`
Mappa su:
- `publication_organization`
- `researcher_affiliation` in alcuni casi
- future tabelle di relazione dedicate quando serviranno
- `source_record` per mantenere traccia della relazione originaria

## Cosa non modelliamo ancora nel MVP

Per mantenere il prototipo focalizzato, alcune parti del modello OpenAIRE non vengono trasformate subito in entità forti PostgreSQL:

- `topic` come entità autonoma
- `project` come entità canonica del core MVP
- `community` come entità canonica del core MVP
- `venue` o `journal` come tabelle dedicate
- relazioni `Result-Result` come citazioni, versioning o relatedness persistite in PostgreSQL come grafo completo

### Motivazione
Queste informazioni possono essere:
- mantenute nel `raw_payload`
- trattate successivamente
- derivate al bisogno in pipeline analitiche o in ulteriori issue

La relazione semantica tra articoli, ad esempio, verrà gestita principalmente nel layer vettoriale e non come entità forte del database relazionale nella prima versione.

## Query applicative che il modello deve supportare

Lo schema proposto è pensato per supportare subito almeno queste query:

- tutte le pubblicazioni di un ricercatore
- tutti gli autori di una pubblicazione in ordine corretto
- tutte le pubblicazioni associate a una organizzazione/università
- costruzione degli archi di coautorialità
- recupero del payload originale e della provenance di un record
- ricerca di pubblicazioni per DOI o titolo normalizzato
- ricerca di ricercatori per nome o ORCID
- collegamento tra publication e embedding in Qdrant

## Motivazione finale della scelta

La modellazione proposta è un compromesso deliberato tra:
- **fedeltà al dato reale**
- **semplicità del prototipo**
- **estendibilità futura**

In particolare:
- è guidata dal Beginner’s Kit e dal modello OpenAIRE, quindi non nasce in astratto
- non replica brutalmente lo schema del grafo, quindi rimane adatta a un backend applicativo
- preserva provenance e raw payload, quindi riduce il rischio di perdere informazione
- è ottimizzata per i casi d’uso del prototipo: ingestione, coauthorship, filtro per organizzazione, API e collegamento al layer vettoriale

## Prossimo passo operativo

Dopo questo documento, il passo successivo è:

1. fissare il DDL PostgreSQL definitivo
2. definire vincoli e indici principali
3. generare la prima migrazione
4. documentare il mapping campo-per-campo dal Beginner’s Kit alle tabelle canoniche
