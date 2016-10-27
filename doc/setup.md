# Setup Guide

## Get the code

To download source code you need Git SCM and you are expected to be familiar
with typing command from the command line.

From the terminal type following to download the code and enter inside the root
project folder:

```bash
git clone https://github.com/pubtransit/transit.git
cd transit
```

## Build transit feeds and the Web page

### Edit site.yaml

Before starting building the feeds you have to edit [site.yaml](site.yaml)
configuration file to specify which feeds to download and deploy on the Web page.
The YAML file allows you to specify the location of public
[GTFS](https://developers.google.com/transit/gtfs/)
[Zip](https://en.wikipedia.org/wiki/Zip_(file_format)) files to download.
As the site at the moment supports only static data (non-real time
pre-scheduled scheduled trips), only the URL of one Zip file is required.
The YAML file comes pre-configured like the Web site is. You can edit it by
making sure you keep its schema as show like here:

```yaml
feed:

- name: ch  # Entry group for Switzerland
   url: http://gtfs.geops.ch/dl
   feeds:
     - name: bus
       path: gtfs_bus.zip  # path relative to the URL of the same group

     - name: train
       path: gtfs_train.zip

     - name: tram
       path: gtfs_tram.zip

     - name: ferries
       path: gtfs_ferry.zip

     - name: gondola
       path: gtfs_gondola.zip  

 - name: dk  # Entry group for Denmark
   feeds:

     - name: rejseplanen
       url: http://labs.rejseplanen.dk/files/GTFS/GTFS.zip  # absolute path
```

AS you can see every entry (like ch/bus, ch/train, ...) is specified under a
named group. Together above configuration specifies following feed archive
would be used to produce feed data inside related folder like here:

| Target feed directory     | Source feed URL |
| ---------------           | ------------- |
| build/feed/ch/bus         | http://gtfs.geops.ch/dl/gtfs_bus.zip |
| build/feed/ch/train       | http://gtfs.geops.ch/dl/gtfs_train.zip |
|   . . .                   |   . . . |
| build/feed/dk/rejseplanen | http://labs.rejseplanen.dk/files/GTFS/GTFS.zip |

### Install Build scripts dependencies

To download and build feed files you need following tools:
 - [WGet](https://www.gnu.org/software/wget/) used to download files;
 - [GNU/Make](https://www.gnu.org/software/make/) used to launch compilation
   scripts;
 - [Python2.7](https://www.python.org/download/releases/2.7/) because build
   scripts are written in Python;
 - [PIP](https://pip.pypa.io/en/stable/installing/) used to download build
   scripts dependences.

Python build scripts dependencies can be installed as follow:
```bash
pip install --user -r /path/to/requirements.txt
```
or if you want to install them as super user please type following:
```bash
sudo pip install -r /path/to/requirements.txt
```
Please be prepared that in some cases dependencies compilation could
fail because some project dependency could require C language tools chain to
compile its native code part.

### Build transit feed files and the HTML page

Once build dependencies are installed to start building be sure you have a fast
Internet connection and type following:
```bash
make
```

## Deploing web page to your server 

To host the Web site it requires a
[vanilla](https://en.wikipedia.org/wiki/Vanilla_software) installation of Apache
without requiring to run any appliance. The transit data store is hosted on the
Web site as a structure of binary compressed files made accessible to the Web
browser by the HTTP server. The Web browser has to download the files
containing required informations on demand and cache them for next use.

The deploy scripts expect you to provide a ready to use running Ubuntu Server
16.04 LTS. If you are not sure and you what to check what deployment scripts
does please have a look to the [Ansible configuration file](provision.yaml).
To understand listed operations and modify them you can read
[Ansible documentation](http://docs.ansible.com/).

To specify the direction of the Web server(s) edit Ansible
[hosts](provision/hosts) configuration file.

### Prepare administrator machine

On the administrator machine you have to install Ansible before deploying
typing following:
```bash
pip install ansible --user
```
or if you wont to install Ansible for all users:
```bash
sudo pip install ansible
```

### Prepare Web site target machine

On the target server you have to install Python to allow Ansible to configure
it.
```bash
ssh ubuntu@target-server-address -c 'sudo apt-get update && sudo apt-get install -y python-minimal'
```

### Run deployment scripts
```bash
make deploy
```
