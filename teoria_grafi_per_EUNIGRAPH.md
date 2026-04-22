# Teoria dei grafi essenziale per EuniGraph

## Definizione di grafo
Un **grafo** è una struttura composta da un insieme di **nodi** e da un insieme di **archi** che collegano coppie di nodi. In termini semplici, un grafo serve a rappresentare entità e relazioni tra entità.

### Significato nel progetto
In EuniGraph:
- nel **grafo di coautorialità**, le entità sono i ricercatori e le relazioni sono le co-firme di pubblicazioni
- nel **grafo semantico**, le entità sono le pubblicazioni e le relazioni sono le vicinanze tra embedding o score di similarità

---

#### Significato di Embedding 
_Un **embedding** è una rappresentazione numerica di un contenuto, per esempio di un testo, sotto forma di vettore. L’idea è trasformare un contenuto testuale in una forma matematica che permetta di confrontarlo con altri contenuti: testi semanticamente simili avranno embedding vicini nello spazio vettoriale. In EuniGraph, gli embedding servono per confrontare le pubblicazioni in base al loro contenuto e costruire il **grafo semantico**, in cui articoli simili vengono collegati tra loro._

---


## Nodi
I **nodi** sono i vertici del grafo, cioè gli oggetti che vogliamo rappresentare.

### Significato nel progetto
- nel **grafo di coautorialità**, un nodo corrisponde a un **autore / researcher**
- nel **grafo semantico**, un nodo corrisponde a una **publication**



## Archi
Gli **archi** sono i collegamenti tra nodi.

### Significato nel progetto
- nel **grafo di coautorialità**, un arco collega due ricercatori che hanno scritto almeno una pubblicazione insieme
- nel **grafo semantico**, un arco collega due pubblicazioni che risultano semanticamente vicine secondo il sistema di embedding / similarità

## Grafo direzionato e non direzionato
Un grafo può essere:

- **direzionato**, se gli archi hanno una direzione
- **non direzionato**, se gli archi non hanno direzione

Nelle librerie di analisi di rete questa distinzione è fondamentale perché molte metriche dipendono dal fatto che un arco sia orientato o meno.

### Significato nel progetto
Per EuniGraph, in prima approssimazione:

- il **grafo di coautorialità** è naturalmente **non direzionato**, perché la collaborazione tra A e B vale in entrambi i sensi
- anche il **grafo semantico** è normalmente trattato come **non direzionato** se la similarità tra due articoli viene resa simmetrica nel layer finale

## Peso degli archi
Un arco può avere un **peso**, cioè un valore numerico che misura l’intensità della relazione.

### Significato nel progetto
Nel progetto il peso degli archi ha un significato molto concreto:

- nel **grafo di coautorialità**, il peso rappresenta il **numero di pubblicazioni condivise** tra due autori
- nel **grafo semantico**, il peso rappresenta lo **score di similarità** tra due pubblicazioni

Il peso è importante perché molte metriche possono essere calcolate sia in versione non pesata sia in versione pesata.

## Degree
Il **degree** di un nodo è il numero di archi incidenti su quel nodo. In un grafo non pesato indica quindi con quanti altri nodi quel nodo è direttamente collegato.

### Significato nel progetto
Nel **grafo di coautorialità**, il degree di un autore indica con quanti coautori distinti ha collaborato.

Interpretazione utile:
- degree alto = ricercatore con molte collaborazioni dirette
- degree basso = ricercatore più periferico o specializzato in pochi legami

Nel **grafo semantico**, il degree di una publication indica con quante altre pubblicazioni è direttamente collegata nel layer di similarità.

Interpretazione utile:
- degree alto = articolo semanticamente vicino a molti altri
- degree basso = articolo più isolato o specialistico

## Betweenness
La **betweenness centrality** misura quanto spesso un nodo si trova lungo i cammini minimi tra altre coppie di nodi. In altre parole, misura quanto un nodo faccia da ponte nella rete. 

### Significato nel progetto
Nel **grafo di coautorialità**, una betweenness alta può indicare:
- ricercatori che collegano gruppi diversi
- autori ponte tra università o cluster di ricerca distinti
- figure che facilitano la circolazione della collaborazione nella rete

Nel **grafo semantico**, una betweenness alta può indicare:
- pubblicazioni che collegano temi diversi
- articoli “ponte” tra aree di ricerca affini ma non coincidenti
- lavori interdisciplinari o trasversali

Questa misura è particolarmente interessante per EUNICE perché può aiutare a individuare:
- collaborazioni tra atenei diversi
- nodi che favoriscono l’integrazione tra comunità di ricerca
- punti di connessione tra filoni scientifici diversi

## Strength
La **strength** di un nodo è il suo **weighted degree**, cioè la somma dei pesi degli archi incidenti.

### Significato nel progetto
Nel **grafo di coautorialità**, la strength di un autore può essere interpretata come la **forza complessiva delle sue collaborazioni**.

Esempio:
- un autore con pochi coautori ma molte pubblicazioni condivise con loro può avere degree moderato ma strength alta
- un autore con tanti coautori occasionali può avere degree alto ma strength non necessariamente altissima

Nel **grafo semantico**, la strength di una publication misura la **somma complessiva delle sue vicinanze semantiche** con altri articoli.

Interpretazione utile:
- strength alta = articolo molto ben connesso semanticamente
- strength bassa = articolo che ha pochi collegamenti forti o solo collegamenti deboli

## Differenza pratica tra degree e strength
Questa distinzione è molto importante nel progetto:

- **degree** conta **quanti** collegamenti esistono
- **strength** misura **quanto sono forti** quei collegamenti

### Nel grafo di coautorialità
- degree = quanti coautori distinti
- strength = quanto intensa è stata la collaborazione complessiva

### Nel grafo semantico
- degree = quanti articoli vicini
- strength = quanto forte è complessivamente la similarità con i vicini

## A cosa serve il grafo di coautorialità nel contesto EUNICE
L’analisi di reti di coautorialità è una tecnica consolidata per studiare la collaborazione scientifica. La letteratura mostra che le co-authorship networks sono utili per valutare collaborazioni, struttura della comunità scientifica, integrazione tra gruppi e opportunità di sviluppo di nuove connessioni. 
Nel contesto EUNICE, il grafo di coautorialità può essere utile per:

- vedere **chi collabora con chi**
- capire se esistono collaborazioni **intra-ateneo** o **inter-ateneo**
- identificare ricercatori **centrali**, **ponte** o **isolati**
- individuare cluster di ricerca già consolidati
- osservare quanto la rete EUNICE sia integrata o frammentata
- supportare strategie di cooperazione tra università dell’alleanza

In sintesi, il grafo di coautorialità serve a rappresentare la **struttura sociale e collaborativa** della ricerca in EUNICE.

## A cosa serve il grafo semantico nel contesto EUNICE
Il grafo semantico non guarda direttamente alle persone, ma ai **contenuti scientifici**.

Nel progetto, il grafo semantico permette di:
- collegare pubblicazioni che trattano temi simili
- far emergere filoni di ricerca anche quando non esiste ancora coautorialità diretta
- identificare cluster tematici
- trovare vicinanze tra lavori prodotti in università diverse
- suggerire potenziali aree di collaborazione futura

Nel contesto EUNICE, questo è utile perché permette di vedere non solo la collaborazione **già avvenuta**, ma anche la **prossimità scientifica potenziale** tra gruppi di ricerca.

### Lettura complementare dei due grafi
La combinazione dei due layer è molto potente:

- **coauthorship graph** = mostra la collaborazione reale già esistente
- **semantic graph** = mostra la vicinanza tematica tra lavori e linee di ricerca

## Come leggere i due grafi insieme
Nel progetto, l’uso combinato dei due grafi può supportare domande come:

- quali ricercatori collaborano già dentro EUNICE?
- quali università sono più connesse sul piano delle coautorialità?
- quali pubblicazioni sono semanticamente vicine anche se prodotte da gruppi non ancora collegati socialmente?
- esistono aree di ricerca comuni tra atenei che ancora non collaborano direttamente?
- quali autori o quali articoli funzionano da ponte tra cluster diversi?

## Sintesi finale
Nel contesto di EuniGraph:

- un **grafo** rappresenta entità e relazioni
- i **nodi** sono ricercatori o pubblicazioni
- gli **archi** rappresentano collaborazioni o similarità
- il **peso** misura l’intensità della relazione
- il **degree** misura quanti collegamenti diretti ha un nodo
- la **betweenness** misura quanto un nodo funge da ponte
- la **strength** misura la forza complessiva dei collegamenti pesati

Queste misure servono a trasformare un insieme di metadata e relazioni in una rappresentazione leggibile e analizzabile della ricerca EUNICE, sia dal punto di vista delle collaborazioni effettive sia dal punto di vista delle vicinanze tematiche.