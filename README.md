# ospf-remote-false-adjacency-attack

Code based on this [paper](theory.stanford.edu/~dabo/papers/ospf.pdf)

---
---
---

# Tools setup

## Mininet setup

- `git clone https://github.com/mininet/mininet`

- `cd mininet`

- `git checkout 2.3.0d4`

- `util/install.sh -a`

- `mn --test pingall`

- `mn --version`

---

## Quagga setup

- download quagga-1.2.4 from [here](http://download.savannah.gnu.org/releases/quagga/) in your `$HOME` and extract it

- `cd ~/quagga-1.2.4`

- `mkdir /var/run/quagga-1.2.4`

- `chown mininet:mininet /var/run/quagga-1.2.4`

- edit `configure` file, add `${quagga_statedir_prefix}/var/run/quagga-1.2.4` before all options in `QUAGGA_STATE_DIR` for loop 

- `./configure --enable-user=mininet --enable-group=mininet`

- `make`

---

## Contrib setup

- download [ospf.py](https://github.com/levigross/Scapy/blob/master/scapy/contrib/ospf.py)

- `mkdir /usr/lib/python2.7/dist-packages/scapy/contrib`

- `cp ospf.py /usr/lib/python2.7/dist-packages/scapy/contrib`

- `touch /usr/lib/python2.7/dist-packages/scapy/contrib/__init__.py`

---

---

---

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

L'attaccante dopo un numero ragionevole di DBD per rendere il router fantasma persistente nella RT del router vittima deve continuare a inviare più Hello packet

NB: l'attaccante non riceve mai i messaggi di risposta dal router vittima

Status: il pacchetto dell'attaccante remoto (src='10.0.3.66', dst='10.0.1.2') non viene elaborato dal router vittima R2

---

show routing table

`show ip ospf route`

show LSA database

`show ip ospf database`

show neighbors

`show ip ospf neighbor`

show configured ospf interfaces

`show ip ospf interface`

---

*TODO*:

- create a base class to init quagga

- check if ospf.py and bgp.py used are the latest version
