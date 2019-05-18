# ospf-remote-false-adjacency-attack

## Installazione VM

Scaricare la VM Mininet [http://www.scs.stanford.edu/~jvimal/mininet-sigcomm14/mininet-tutorial-vm-64bit.zip](http://www.scs.stanford.edu/~jvimal/mininet-sigcomm14/mininet-tutorial-vm-64bit.zip).  
Per accedere:

- username: mininet
- password: mininet

## Preparazione mininet

- `$ git clone https://github.com/mininet/mininet`

- `$ cd mininet`

- `$ git checkout 2.3.0d4`

- `$ ./util/install.sh -a`

- `$ mn --test pingall`

- `$ mn --version`

## Quagga preparation

Scaricare quagga-1.2.4 from [http://download.savannah.gnu.org/releases/quagga/](http://download.savannah.gnu.org/releases/quagga/) nella tua `$HOME` ed estrai il package

- `$ cd ~/quagga-1.2.4`

- `# chown mininet:mininet /var/run/quagga`

- modifica il file `configure`, aggiungendo `${quagga_statedir_prefix}/var/run/quagga` prima di tutte le opzioni del loop su `QUAGGA_STATE_DIR` 

- `$ ./configure --enable-user=mininet --enable-group=mininet`

- `$ make`

## Contrib setup

Scaricare [https://github.com/levigross/Scapy/blob/master/scapy/contrib/ospf.py](https://github.com/levigross/Scapy/blob/master/scapy/contrib/ospf.py)

- `$ mkdir /usr/lib/python2.7/dist-packages/scapy/contrib`

- `$ cp ospf.py /usr/lib/python2.7/dist-packages/scapy/contrib`

- `$ touch /usr/lib/python2.7/dist-packages/scapy/contrib/__init__.py`

---

## Descrizione dell'attacco

|attaccante||router vittima|
|-|:-:|-|
|| Hello(ID fantasma > ID vittima, neighbor=ID vittima) &rarr; ||
|| &larr; DBD(I, M, MS, SN=y) ||
|| DBD(I, M, MS, SN=x) &rarr; ||
|| &larr; DBD(M, SN=x) ||
|| DBD(M, MS, SN=x+1) &rarr; ||
|| &larr; DBD(M, SN=x+1) ||
||...||
|| DBD(MS, SN=x+N) &rarr; |||


L'attaccante invia DBD Message per rendere il router fantasma persistente nella RT del router vittima.
Dopo questa fase deve continuare a inviare Hello packet a intervalli regolari.

NB: l'attaccante non riceve mai i messaggi di risposta dal router vittima

---

## Utils

show routing table

`> show ip ospf route`

show LSA database

`> show ip ospf database`

show neighbors

`> show ip ospf neighbor`

show configured ospf interfaces

`> show ip ospf interface`
